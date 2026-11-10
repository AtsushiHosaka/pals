/* Credential holder for release-post-request-transport.py.
 *
 * It seeds one browser context from the private session file (as release-acceptance-browser.cjs
 * does), takes the bearer the product itself sends to the API, closes the browser, and then
 * serves a closed list of HTTPS calls against the contract's API origin over a line protocol on
 * stdin/stdout. The bearer and the session contents stay in this process: they are never written
 * to stdout, stderr, a file, or an error. Redirects are never followed and no response text is
 * interpreted beyond JSON parsing.
 */
"use strict";
const fs = require("node:fs");
const https = require("node:https");
const readline = require("node:readline");

class Refusal extends Error {}
const need = (value, code) => { if (!value) throw new Refusal(code); };
const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}";
// [method, path, body allowed]. Nothing else can be sent with the session's credential.
const ROUTES = [
  ["POST", /^\/v1\/chats$/u, false],
  ["GET", new RegExp(`^/v1/chats/${UUID}$`, "u"), false],
  ["GET", new RegExp(`^/v1/chats/${UUID}/proof-requests$`, "u"), false],
  ["POST", new RegExp(`^/v1/chats/${UUID}/proof-requests$`, "u"), true],
  ["GET", new RegExp(`^/v1/proof-requests/${UUID}$`, "u"), false],
  ["POST", /^\/v1\/billing\/token-quotes$/u, true],
];
// Owner reads the signed-in workspace issues on load. The bearer is taken only from one of these.
const CAPTURE = [/^\/v1\/chats$/u, /^\/v1\/projects$/u, /^\/v1\/auth\/me(?:\/[a-z-]{1,64})?$/u];
const MAX_BODY = 2 ** 20;

function httpsOrigin(value, code) {
  let url;
  try { url = new URL(value); } catch { throw new Refusal(code); }
  need(url.protocol === "https:" && url.origin === value && !url.username && !url.password, code);
  return url;
}

function readSession(sessionPath, webOrigin) {
  let fd;
  try { fd = fs.openSync(sessionPath, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW); }
  catch { throw new Refusal("private_session_required"); }
  try {
    const info = fs.fstatSync(fd);
    need(info.isFile() && (info.mode & 0o777) === 0o600 && info.nlink === 1 && info.uid === process.geteuid()
      && info.size > 0 && info.size <= MAX_BODY, "private_session_required");
    let session;
    try { session = JSON.parse(fs.readFileSync(fd, "utf8")); } catch { throw new Refusal("session_origin_invalid"); }
    need(session && session.schema_version === "pals.acceptance-session.v1" && session.origin === webOrigin
      && session.session_storage && typeof session.session_storage === "object"
      && Object.entries(session.session_storage).every(([k, v]) => typeof k === "string" && typeof v === "string"),
      "session_origin_invalid");
    return session;
  } finally { fs.closeSync(fd); }
}

// The page may only read the web and API origins (plus the product's passive telemetry POST).
// Every other origin is aborted, the auth origin included: the session file is never written
// back, so a renewal here could rotate away the owner's stored refresh token. An expired
// session therefore fails closed and must be provisioned again.
async function bearerFromBrowser(init, session) {
  const deadline = Date.now() + init.start_ms;
  const resolve = name => require.resolve(name, { paths: [init.web_root] });
  const { chromium } = require(resolve("playwright"));
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ serviceWorkers: "block" });
    await context.addInitScript(({ origin, entries }) => {
      if (location.origin === origin) for (const [key, value] of entries) sessionStorage.setItem(key, value);
    }, { origin: session.origin, entries: Object.entries(session.session_storage) });
    await context.route("**/*", async route => {
      const request = route.request();
      let url = null;
      try { url = new URL(request.url()); } catch { url = null; }
      const read = ["GET", "HEAD", "OPTIONS"].includes(request.method());
      if (url && read && (url.origin === init.web_origin || url.origin === init.api_origin)) await route.continue();
      else if (url && request.method() === "POST" && url.origin === init.api_origin
        && url.pathname === "/v1/product-events" && !url.search) await route.continue();
      else await route.abort();
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30_000);
    let bearer = null;
    const seen = new Set();
    // First bearer on an allow-listed owner read wins; then the listener is removed.
    const listener = request => {
      let url;
      try { url = new URL(request.url()); } catch { return; }
      if (url.origin !== init.api_origin) return;
      const value = request.headers().authorization;
      if (typeof value !== "string" || !value.startsWith("Bearer ")) return;
      seen.add(value);
      if (request.method() === "GET" && CAPTURE.some(pattern => pattern.test(url.pathname))) {
        bearer = value;
        page.off("request", listener);
      }
    };
    page.on("request", listener);
    await page.goto(`${init.web_origin}/`, { waitUntil: "domcontentloaded" });
    while (!bearer && Date.now() < deadline) await page.waitForTimeout(100);
    page.off("request", listener);
    need(bearer, "authenticated_context_not_observed");
    need(seen.size === 1, "conflicting_bearers_observed");
    // A header-safe token only: no whitespace or control characters can reach the wire.
    need(/^Bearer [A-Za-z0-9._~+/=-]{16,8192}$/u.test(bearer), "authenticated_context_not_observed");
    return bearer;
  } finally { await browser.close(); }
}

function exchange(api, bearer, message, callMs) {
  return new Promise(resolve => {
    const headers = { Authorization: bearer, Accept: "application/json", "Cache-Control": "no-cache" };
    let payload = null;
    if (message.body !== undefined) {
      payload = Buffer.from(JSON.stringify(message.body), "utf8");
      headers["Content-Type"] = "application/json";
      headers["Content-Length"] = String(payload.length);
    }
    let settled = false;
    const finish = value => { if (!settled) { settled = true; clearTimeout(timer); resolve(value); } };
    // The URL is the contract's origin plus an allow-listed path; nothing from a response is used.
    const request = https.request({ protocol: "https:", hostname: api.hostname.replace(/^\[|\]$/gu, ""),
      port: api.port || 443, method: message.method, path: message.path, headers, agent: false }, response => {
      const chunks = [];
      let size = 0;
      response.on("data", chunk => {
        size += chunk.length;
        if (size > MAX_BODY) { request.destroy(); finish({ ok: false, error: "response_unbounded" }); }
        else chunks.push(chunk);
      });
      response.on("error", () => finish({ ok: false, error: "connection" }));
      response.on("end", () => {
        const release = response.headers["x-pals-release-manifest-sha256"];
        let body = null;
        try { body = JSON.parse(Buffer.concat(chunks).toString("utf8")); } catch { body = null; }
        finish({ ok: true, status: response.statusCode,
          release: typeof release === "string" && /^[a-f0-9]{64}$/u.test(release) ? release : null, body });
      });
    });
    const timer = setTimeout(() => { request.destroy(); finish({ ok: false, error: "timeout" }); }, callMs);
    request.on("error", () => finish({ ok: false, error: "connection" }));
    request.end(payload ?? undefined);
  });
}

function allowed(message) {
  return message && typeof message.method === "string" && typeof message.path === "string"
    && ROUTES.some(([method, pattern, withBody]) => method === message.method && pattern.test(message.path)
      && (message.body !== undefined) === withBody
      && (!withBody || (message.body && typeof message.body === "object" && !Array.isArray(message.body))));
}

async function serve(input, output, bearerSource = bearerFromBrowser) {
  const write = value => output.write(JSON.stringify(value) + "\n");
  const lines = readline.createInterface({ input, crlfDelay: Infinity })[Symbol.asyncIterator]();
  let api, bearer, init;
  try {
    const first = await lines.next();
    need(!first.done, "live_session_helper_unavailable");
    init = JSON.parse(first.value);
    api = httpsOrigin(init.api_origin, "https_api_origin_required");
    httpsOrigin(init.web_origin, "https_web_origin_required");
    if (init.auth_origin !== null) httpsOrigin(init.auth_origin, "unsafe_auth_origin");
    need(Number.isSafeInteger(init.start_ms) && init.start_ms > 0 && init.start_ms <= 300_000
      && Number.isSafeInteger(init.call_ms) && init.call_ms > 0 && init.call_ms <= 120_000, "bounded_wait_required");
    bearer = await bearerSource(init, readSession(init.session_path, init.web_origin));
  } catch (error) {
    write({ ready: false, code: error instanceof Refusal ? error.message : "browser_dependency_or_execution_failed" });
    return 1;
  }
  write({ ready: true });
  for (;;) {
    const next = await lines.next();
    if (next.done) return 0;
    let message = null;
    try { message = JSON.parse(next.value); } catch { message = null; }
    const id = message && Number.isSafeInteger(message.id) ? message.id : null;
    if (!allowed(message)) write({ id, ok: false, error: "route_not_allowed" });
    else write({ id, ...await exchange(api, bearer, message, init.call_ms) });
  }
}

module.exports = { Refusal, ROUTES, allowed, exchange, httpsOrigin, readSession, serve };
if (require.main === module) {
  serve(process.stdin, process.stdout).then(code => process.exit(code), () => process.exit(1));
}
