"use strict";
// Approved local guest journey: one UI submission, actual API polling, visible answer and reload.
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const { pathToFileURL } = require("node:url");
const { norm, stable, sourceSemantics, semanticTokens, readRendered } = require("./release-acceptance-browser.cjs");
const sha = v => crypto.createHash("sha256").update(v).digest("hex");
const need = (ok, code) => { if (!ok) throw new Error(code); };
async function withSubmissionMarker(file, record, submit) {
  const descriptor = fs.openSync(file, "wx", 0o600);
  try { fs.writeFileSync(descriptor, JSON.stringify(record)); fs.fsyncSync(descriptor); }
  finally { fs.closeSync(descriptor); }
  const directory = fs.openSync(path.dirname(file), "r");
  try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  return submit();
}
function admitRequest(method, rawUrl, verifyExisting, counts) {
  const u = new URL(rawUrl), local = ["http://localhost:53000", "http://localhost:58000"].includes(u.origin);
  if (local && ["GET", "HEAD", "OPTIONS"].includes(method)) return true;
  if (u.origin !== "http://localhost:58000" || method !== "POST") return false;
  if (u.pathname === "/v1/product-events") { counts.telemetry++; return true; }
  if (u.pathname === "/v1/guest/session") return true;
  // Reject before dispatch. A failed assertion AFTER sending could charge another proof.
  if (!verifyExisting && u.pathname === "/v1/guest/proof-requests" && ++counts.proofPosts === 1) return true;
  return false;
}
async function run(c) {
  need(c.subject.schema_version === "pals.local-qualification-subject.v1", "local_subject_required");
  const resolve = name => require.resolve(name, { paths: [c.web_root] });
  const { chromium } = require(resolve("playwright"));
  const [{ unified }, { default: parse }, { default: math }] = await Promise.all(
    ["unified", "remark-parse", "remark-math"].map(x => import(pathToFileURL(resolve(x)).href)));
  const processor = unified().use(parse).use(math), f = c.subject.fixture;
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ locale: "en-US", ...(c.verify_existing ? { storageState: path.join(c.state_dir, "guest-storage.json") } : {}) });
  const counts = { proofPosts: 0, telemetry: 0 }; let rejected = 0;
  let observedRequestId = c.existing?.id, injectedReadFaults = 0, successfulReadAttemptsAfterFault = 0;
  try {
    await context.route("**/*", route => {
      const req = route.request();
      if (req.method() === "GET" && observedRequestId && req.url() === `http://localhost:58000/v1/guest/proof-requests/${observedRequestId}`) {
        if (injectedReadFaults === 0) { injectedReadFaults++; return route.abort("failed"); }
        successfulReadAttemptsAfterFault++;
      }
      const allowed = admitRequest(req.method(), req.url(), c.verify_existing, counts);
      if (!allowed) { rejected++; return route.abort("blockedbyclient"); }
      return route.continue();
    });
    if (c.verify_existing) await context.addInitScript(ids => sessionStorage.setItem("pals.guest.request.v1", JSON.stringify(ids)), c.existing);
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    await page.goto("http://localhost:53000/try", { waitUntil: "domcontentloaded" });
    let request = c.existing;
    if (!c.verify_existing) {
    const input = page.locator("#guest-question");
    await input.waitFor({ state: "visible" });
    await page.waitForFunction(() => !document.querySelector("#guest-question")?.disabled);
    await page.locator(".generation-model-selector select").selectOption(`${f.generation_model}:${f.reasoning_effort}`);
    await input.fill(f.statement);
    // This durable exclusive marker exists BEFORE clicking. Ambiguous failures never resubmit.
    const response = await withSubmissionMarker(path.join(c.state_dir, "submission.json"),
      { state: "submission_started", subject_sha256: c.subject_sha256, at: new Date().toISOString() }, async () => {
        const responsePromise = page.waitForResponse(r => r.request().method() === "POST" && new URL(r.url()).pathname === "/v1/guest/proof-requests");
        await input.locator("xpath=ancestor::form").locator("button[type=submit]").click();
        return responsePromise;
      });
    need(response.ok(), `guest_submission_http_${response.status()}`);
    request = await response.json();
    observedRequestId = request.id;
    }
    need(/^[0-9a-f-]{36}$/.test(request.id) && /^[0-9a-f-]{36}$/.test(request.chat_id), "actual_request_ids_required");
    const privateWrite = (name, data) => fs.writeFileSync(path.join(c.state_dir, name), JSON.stringify(data), { mode: 0o600 });
    if (!c.verify_existing) privateWrite("submission.json", { state: "submitted", id: request.id, chat_id: request.chat_id, subject_sha256: c.subject_sha256 });
    const transitions = [], deadline = Date.now() + 9 * 60 * 1000;
    const get = async suffix => {
      const r = await context.request.get(`http://localhost:58000/v1/guest/proof-requests/${request.id}${suffix}`);
      need(r.status() === 200, `guest_read_http_${r.status()}`);
      need(r.headers()["x-pals-release-manifest-sha256"] === c.subject_sha256, "runtime_subject_header_changed");
      return r.json();
    };
    while (Date.now() < deadline) {
      request = await get("");
      if (transitions.at(-1)?.status !== request.status) transitions.push({ status: request.status, at: new Date().toISOString() });
      privateWrite("observed-request.json", request);
      if (["answered", "failed", "needs_input"].includes(request.status)) break;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    need(request.status === "answered" && request.error_code === null, `terminal_answer_required_${request.status}_${request.error_code ?? "none"}`);
    need(Date.parse(request.created_at) >= Date.parse(c.activated_at), "fresh_request_required");
    need(request.generation_model === f.generation_model && request.generation_reasoning_effort === f.reasoning_effort && request.output_language === "en", "model_language_settings_differ");
    const answer = request.answer, lean = await get("/lean");
    privateWrite("observed-lean.json", lean);
    need(answer?.evidence_kind === "lean_verified" && answer.verdict !== "refuted" && lean.state === "verified" && typeof lean.lean_code === "string" && lean.lean_code.trim(), "real_verified_lean_required");
    need(lean.proof_job_id === request.formal_job_id && answer.lean?.proof_job_id === lean.proof_job_id && answer.lean.lean_sha256 === sha(lean.lean_code), "lean_source_binding_differs");
    const expected = sourceSemantics(answer.text, processor);
    // A restored terminal chat has no active polling loop. Its public status button
    // performs a read-only recovery after the deliberately aborted restore GET.
    if (c.verify_existing) await page.getByRole("button", { name: "Check status", exact: true }).click();
    const selector = `[data-proof-request-id="${request.id}"] [data-proof-answer]`;
    async function rendered() {
      const node = page.locator(selector);
      await node.waitFor({ state: "visible", timeout: 30000 });
      need(await node.count() === 1, "unique_bound_answer_required");
      const actual = semanticTokens(await node.evaluate(readRendered));
      need(stable(actual) === stable(expected), "rendered_content_differs_from_saved_answer");
      return sha(stable(actual));
    }
    const first = await rendered();
    await page.screenshot({ path: path.join(c.state_dir, "terminal-answer.png"), fullPage: true });
    await page.reload({ waitUntil: "domcontentloaded" });
    const second = await rendered(), after = await get("");
    need(first === second && after.answer.text === answer.text && after.status === "answered", "reload_changed_saved_answer");
    need(counts.proofPosts === (c.verify_existing ? 0 : 1) && rejected === 0, "unexpected_browser_mutation_or_network");
    need(injectedReadFaults === 1 && successfulReadAttemptsAfterFault >= 1, "real_read_fault_did_not_recover");
    await page.screenshot({ path: path.join(c.state_dir, "reloaded-answer.png"), fullPage: true });
    return { id: request.id, chat_id: request.chat_id, created_at: request.created_at, status_transitions: transitions,
      terminal_status: request.status, evidence_kind: answer.evidence_kind, answer_sha256: sha(answer.text),
      lean_sha256: sha(lean.lean_code), rendered_semantics_sha256: first, reloaded_semantics_sha256: second,
      proof_submissions: counts.proofPosts, rejected_requests: rejected, passive_telemetry_posts: counts.telemetry,
      transient_fault: { kind: "one_real_GET_network_abort", count: injectedReadFaults, read_attempts_after_fault: successfulReadAttemptsAfterFault,
        recovery: c.verify_existing ? "public_Check_status_GET_only" : "automatic_active_request_polling" } };
  } finally {
    await context.storageState({ path: path.join(c.state_dir, "guest-storage.json") });
    fs.chmodSync(path.join(c.state_dir, "guest-storage.json"), 0o600);
    await browser.close();
  }
}
if (require.main === module) {
  let raw = ""; process.stdin.setEncoding("utf8"); process.stdin.on("data", x => { raw += x; });
  process.stdin.on("end", async () => { try { process.stdout.write(JSON.stringify(await run(JSON.parse(raw)))); }
    catch (e) { process.stderr.write(e.message); process.exitCode = 1; } });
}
module.exports = { run, admitRequest, withSubmissionMarker };
