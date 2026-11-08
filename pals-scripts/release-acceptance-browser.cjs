/* Real browser/API observer. Inputs and credentials remain in the controlled runner. */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { pathToFileURL } = require("node:url");

class Refusal extends Error {}
const need = (value, code) => { if (!value) throw new Refusal(code); };
const sha = value => crypto.createHash("sha256").update(value).digest("hex");
const norm = value => value.normalize("NFC").replace(/\s+/gu, " ").trim();
const stable = value => JSON.stringify(value, (_, item) => item && typeof item === "object" && !Array.isArray(item)
  ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);

function normalizeMath(source) {
  let out = "";
  for (let i = 0; i < source.length;) {
    if (source[i] === "`") {
      const width = source.slice(i).match(/^`+/u)[0].length;
      const end = source.indexOf("`".repeat(width), i + width);
      const next = end < 0 ? source.length : end + width;
      out += source.slice(i, next); i = next; continue;
    }
    const pair = source.startsWith("\\(", i) ? ["\\)", "$", "$"]
      : source.startsWith("\\[", i) ? ["\\]", "\n\n$$\n", "\n$$\n\n"] : null;
    if (pair && (i === 0 || source[i - 1] !== "\\")) {
      const end = source.indexOf(pair[0], i + 2);
      if (end >= 0) { out += pair[1] + source.slice(i + 2, end) + pair[2]; i = end + 2; continue; }
    }
    out += source[i++];
  }
  return out;
}

function semanticTokens(tokens) {
  const result = [];
  for (const token of tokens) {
    if (token.kind === "text" && result.at(-1)?.kind === "text") result.at(-1).value += token.value;
    else result.push({ ...token });
  }
  return result.map(token => ({ kind: token.kind, value: norm(token.value) })).filter(token => token.value);
}

function sourceSemantics(source, processor) {
  const tokens = [];
  function visit(node) {
    if (node.type === "math" || node.type === "inlineMath") tokens.push({ kind: "math", value: node.value });
    else if (["text", "code", "inlineCode"].includes(node.type)) tokens.push({ kind: "text", value: node.value });
    else {
      need(node.type !== "html" && node.type !== "image", "unsupported_acceptance_markup");
      if (["paragraph", "heading", "listItem", "break", "thematicBreak"].includes(node.type)) tokens.push({ kind: "text", value: " " });
      for (const child of node.children || []) visit(child);
      if (["paragraph", "heading", "listItem"].includes(node.type)) tokens.push({ kind: "text", value: " " });
    }
  }
  visit(processor.parse(normalizeMath(source)));
  return semanticTokens(tokens);
}

function validateAnswer(request, job, explanation, source, expected, activatedAt, processor) {
  need(request.id === expected.id && request.chat_id === expected.chat_id && request.status === "answered"
    && request.error_code === null && Date.parse(request.created_at) >= activatedAt, "fresh_terminal_request_required");
  need(request.generation_model === expected.generation_model
    && (request.generation_reasoning_effort ?? null) === expected.reasoning_effort
    && request.output_language === expected.output_language, "request_configuration_differs");
  const answer = request.answer;
  need(answer?.evidence_kind === "lean_verified" && typeof answer.text === "string" && answer.text.trim()
    && answer.verdict !== "refuted" && answer.lean?.source === "proof_job"
    && answer.lean.proof_job_id === request.formal_job_id, "lean_verified_answer_required");
  need(job.id === request.formal_job_id && job.chat_id === request.chat_id && job.state === "verified"
    && job.output_language === expected.output_language && Date.parse(job.created_at) >= activatedAt,
    "fresh_verified_job_required");
  need(source.job_id === job.id && source.chat_id === request.chat_id
    && typeof source.lean_code === "string" && source.lean_code.trim()
    && sha(source.lean_code) === answer.lean.lean_sha256, "verified_source_binding_differs");
  need(explanation.proof_job_id === job.id && explanation.state === "completed"
    && explanation.content && typeof explanation.content.conclusion === "string"
    && explanation.content.conclusion.trim(), "completed_conclusion_required");
  const content = explanation.content;
  need(typeof content.overview === "string" && Array.isArray(content.sections)
    && content.sections.every(section => typeof section.summary === "string"), "complete_explanation_required");
  const preceding = [content.overview, ...content.sections.map(section => section.summary)].map(s => s.trim()).filter(Boolean).join("\n\n");
  const projection = [preceding, content.conclusion.trim()].filter(Boolean).join("\n\n");
  need(norm(answer.text) === norm(projection), "stored_answer_dropped_explanation_content");
  const conclusion = sourceSemantics(content.conclusion, processor);
  const prior = sourceSemantics(preceding, processor);
  for (const text of expected.required_conclusion_text) {
    need(norm(content.conclusion).includes(norm(text)) && !norm(preceding).includes(norm(text)), "unique_conclusion_text_required");
  }
  for (const math of expected.required_conclusion_math) {
    need(conclusion.some(token => token.kind === "math" && token.value === norm(math))
      && !prior.some(token => token.kind === "math" && token.value === norm(math)), "unique_conclusion_math_required");
  }
  return { answer, expectedSemantics: sourceSemantics(answer.text, processor), conclusion };
}

// This function is serialized into the real page; it never substitutes DOM or API data.
function readRendered(root) {
  const tokens = [];
  const blocks = new Set(["P", "DIV", "SECTION", "LI", "UL", "OL", "PRE", "BLOCKQUOTE", "H1", "H2", "H3", "H4", "BR", "HR"]);
  function visit(node) {
    if (node.nodeType === Node.TEXT_NODE) { tokens.push({ kind: "text", value: node.textContent }); return; }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.classList.contains("learner-math-source")) {
      const next = node.nextElementSibling;
      const katex = next?.matches(".katex") ? next : next?.querySelector(".katex");
      if (!katex || katex.getBoundingClientRect().width <= 0) throw new Error("visible_math_missing");
      tokens.push({ kind: "math", value: node.textContent }); return;
    }
    if (node.matches(".katex, .katex-display, [aria-hidden='true']")) return;
    const style = getComputedStyle(node);
    if (style.display === "none" || style.visibility === "hidden") return;
    if (blocks.has(node.tagName)) tokens.push({ kind: "text", value: " " });
    for (const child of node.childNodes) visit(child);
    if (blocks.has(node.tagName)) tokens.push({ kind: "text", value: " " });
  }
  if (root.querySelector(".katex-error")) throw new Error("math_render_error");
  visit(root);
  return tokens;
}

async function observe(payload, trace) {
  const { contract: c, run_id: runId } = payload;
  const resolve = name => require.resolve(name, { paths: [c.web_root] });
  const { chromium } = require(resolve("playwright"));
  const [{ unified }, { default: remarkParse }, { default: remarkMath }] = await Promise.all(
    ["unified", "remark-parse", "remark-math"].map(name => import(pathToFileURL(resolve(name)).href)));
  const processor = unified().use(remarkParse).use(remarkMath);
  const sessionInfo = fs.lstatSync(payload.session_path);
  need(sessionInfo.isFile() && !sessionInfo.isSymbolicLink() && (sessionInfo.mode & 0o777) === 0o600,
    "private_session_required");
  const session = JSON.parse(fs.readFileSync(payload.session_path, "utf8"));
  need(session.schema_version === "pals.acceptance-session.v1" && session.origin === c.web_origin
    && session.session_storage && Object.entries(session.session_storage).every(([k, v]) => typeof k === "string" && typeof v === "string"),
    "session_origin_invalid");
  const browser = await chromium.launch({ headless: true });
  const closeForSignal = () => { void browser.close().finally(() => process.exit(143)); };
  process.once("SIGTERM", closeForSignal);
  try {
    const context = await browser.newContext({ serviceWorkers: "block" });
    await context.addInitScript(({ origin, entries }) => {
      if (location.origin === origin) for (const [key, value] of entries) sessionStorage.setItem(key, value);
    }, { origin: session.origin, entries: Object.entries(session.session_storage) });
    let attemptedWrites = 0, telemetryPosts = 0, authPosts = 0;
    await context.route("**/*", async route => {
      const request = route.request(), url = new URL(request.url());
      if (["GET", "HEAD", "OPTIONS"].includes(request.method())) await route.continue();
      else if (request.method() === "POST" && url.origin === c.api_origin && url.pathname === "/v1/product-events" && !url.search) {
        telemetryPosts++; await route.continue();
      } else if (request.method() === "POST" && c.auth_origin && url.origin === c.auth_origin && !url.search
        && ["/", "/oauth2/token"].includes(url.pathname)) { authPosts++; await route.continue(); }
      else { attemptedWrites++; await route.abort(); }
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30_000);
    const assets = new Map(), assetReads = [];
    let assetError = null;
    page.on("response", response => {
      const url = new URL(response.url());
      let assetPath;
      try { assetPath = decodeURIComponent(url.pathname); } catch { return; }
      if (url.origin === c.web_origin && /^\/_next\/static\/[A-Za-z0-9_./@()+\[\]-]+\.(js|css)$/u.test(assetPath) && !assetPath.includes("..")) {
        assetReads.push(response.body().then(bytes => {
          need(response.status() === 200 && bytes.length <= 2**23, "served_asset_read_failed");
          const prior = assets.get(assetPath), hash = sha(bytes);
          need(!prior || prior === hash, "served_asset_changed_during_capture");
          assets.set(assetPath, hash);
        }).catch(error => { assetError = error; }));
      }
    });
    let token = null;
    page.on("request", request => {
      if (new URL(request.url()).origin === c.api_origin) {
        const value = request.headers().authorization;
        if (value?.startsWith("Bearer ")) token = value;
      }
    });
    const url = `${c.web_origin}/chats/${c.request.chat_id}`;
    await page.goto(url, { waitUntil: "domcontentloaded" });
    const deadline = Date.now() + c.timeout_seconds * 1000;
    while (!token && Date.now() < deadline) await page.waitForTimeout(100);
    need(token, "authenticated_context_not_observed");
    async function get(endpoint) {
      const response = await context.request.get(c.api_origin + endpoint, { headers: { Authorization: token, "Cache-Control": "no-cache" }, maxRedirects: 0, timeout: 30_000 });
      trace.last_http_status = response.status();
      need(response.status() === 200, "required_api_read_failed");
      need(response.headers()["x-pals-release-manifest-sha256"] === c.manifest.sha256, "public_api_not_candidate");
      const bytes = await response.body();
      need(bytes.length <= 2**20, "api_response_unbounded");
      return JSON.parse(bytes.toString("utf8"));
    }
    const statuses = [];
    trace.status_transitions = statuses;
    let request;
    do {
      request = await get(`/v1/proof-requests/${c.request.id}`);
      need(["queued", "assessing", "verifying", "answered", "failed", "needs_input"].includes(request.status)
        && Number.isSafeInteger(request.revision), "request_response_invalid");
      if (statuses.at(-1)?.status !== request.status) statuses.push({ status: request.status, at: new Date().toISOString(), revision: request.revision });
      need(!["failed", "needs_input"].includes(request.status), "request_did_not_answer");
      if (request.status === "answered") break;
      need(["queued", "assessing", "verifying"].includes(request.status) && Date.now() < deadline, "terminal_answer_deadline_exceeded");
      await page.waitForTimeout(1000);
    } while (true);
    need(typeof request.formal_job_id === "string" && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$/u.test(request.formal_job_id), "formal_job_required");
    const jobPath = `/v1/proof-jobs/${encodeURIComponent(request.formal_job_id)}`;
    const [job, explanation, source] = await Promise.all([get(jobPath), get(jobPath + "/explanation"), get(jobPath + "/source")]);
    const { answer, expectedSemantics } = validateAnswer(request, job, explanation, source, c.request, Date.parse(payload.activated_at), processor);
    async function persisted() {
      const listing = await get(`/v1/chats/${c.request.chat_id}/proof-requests`);
      const matches = listing.items?.filter(item => item.id === c.request.id);
      need(matches?.length === 1 && matches[0].status === "answered" && stable(matches[0].answer) === stable(answer), "persisted_answer_differs");
      const direct = await get(`/v1/proof-requests/${c.request.id}`);
      need(direct.status === "answered" && stable(direct.answer) === stable(answer), "reread_answer_differs");
      return sha(stable(direct.answer));
    }
    async function rendered() {
      const node = page.locator(`[data-proof-request-id="${c.request.id}"] [data-proof-answer]`);
      await node.waitFor({ state: "visible", timeout: Math.min(30_000, Math.max(1, deadline - Date.now())) });
      need(await node.count() === 1, "unique_rendered_answer_required");
      const tokens = semanticTokens(await node.evaluate(readRendered));
      need(stable(tokens) === stable(expectedSemantics), "rendered_answer_differs_from_persisted_source");
      return sha(stable(tokens));
    }
    const saved = await persisted();
    const first = await rendered();
    await page.reload({ waitUntil: "domcontentloaded" });
    need(new URL(page.url()).origin === c.web_origin && new URL(page.url()).pathname === `/chats/${c.request.chat_id}`, "reload_did_not_restore_chat");
    const second = await rendered();
    need(await persisted() === saved && second === first, "reloaded_answer_differs");
    need(attemptedWrites === 0, "observer_attempted_mutation");
    await Promise.all(assetReads);
    need(!assetError, "served_asset_read_failed");
    return { run_id: runId, request_sha256: sha(c.request.id), chat_sha256: sha(c.request.chat_id),
      created_at: request.created_at, status_transitions: statuses, terminal_status: request.status,
      evidence_kind: answer.evidence_kind, answer_sha256: saved, conclusion_sha256: sha(explanation.content.conclusion),
      verified_lean_sha256: sha(source.lean_code), rendered_semantics_sha256: first,
      reloaded_semantics_sha256: second, observed_at: new Date().toISOString(), attempted_mutations: attemptedWrites,
      passive_telemetry_posts: telemetryPosts, authentication_posts: authPosts,
      web_assets: [...assets].map(([assetPath, hash]) => ({ path: assetPath, sha256: hash })) };
  } finally { process.off("SIGTERM", closeForSignal); await browser.close(); }
}

module.exports = { Refusal, norm, stable, normalizeMath, semanticTokens, sourceSemantics, validateAnswer, readRendered };
if (require.main === module) {
  let raw = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", chunk => { raw += chunk; if (raw.length > 2**20) process.exit(1); });
  process.stdin.on("end", async () => {
    const trace = {};
    try {
      const payload = JSON.parse(raw);
      trace.run_id = payload.run_id;
      trace.request_sha256 = sha(payload.contract.request.id);
      process.stdout.write(JSON.stringify(await observe(payload, trace)));
    } catch (error) {
      trace.observed_at = new Date().toISOString();
      process.stdout.write(JSON.stringify(trace));
      process.stderr.write(error instanceof Refusal ? error.message : "browser_dependency_or_execution_failed");
      process.exitCode = 1;
    }
  });
}
