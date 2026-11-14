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
const { spawnSync } = require("node:child_process");

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

function jwtClaims(value) {
  need(typeof value === "string" && /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/u.test(value)
    && value.length <= 16384, "refresh_session_invalid");
  try { return JSON.parse(Buffer.from(value.split(".")[1], "base64url").toString("utf8")); }
  catch { throw new Refusal("refresh_session_invalid"); }
}

// Claims locate the seeded SDK credentials; they grant no authority. The separate read-only
// guard checks STS ownership and the exact Cognito client before any auth POST is allowed.
function refreshDescriptor(init, session) {
  if (!init.refresh_policy || !init.auth_origin) return null;
  const authority = init.refresh_policy, storage = session.session_storage;
  need(authority.region === "ap-northeast-1" && /^[0-9]{12}$/u.test(authority.account_id)
    && init.auth_origin === `https://cognito-idp.${authority.region}.amazonaws.com`, "refresh_authority_invalid");
  const keys = Object.keys(storage).filter(key => /^CognitoIdentityServiceProvider\.[A-Za-z0-9]{1,128}\.LastAuthUser$/u.test(key));
  need(keys.length === 1, "refresh_session_invalid");
  const client = keys[0].split(".")[1], user = storage[keys[0]];
  need(user.length > 0 && user.length <= 256, "refresh_session_invalid");
  const prefix = `CognitoIdentityServiceProvider.${client}.${user}.`;
  const id = jwtClaims(storage[prefix + "idToken"]), access = jwtClaims(storage[prefix + "accessToken"]);
  const issuer = `https://cognito-idp.${authority.region}.amazonaws.com/`;
  need(id && access && id.token_use === "id" && access.token_use === "access"
    && id.aud === client && access.client_id === client && typeof id.sub === "string"
    && id.sub === access.sub && typeof id.iss === "string" && id.iss.startsWith(issuer)
    && id.iss === access.iss, "refresh_session_invalid");
  const pool = id.iss.slice(issuer.length);
  need(/^ap-northeast-1_[A-Za-z0-9]{1,128}$/u.test(pool), "refresh_session_invalid");
  const refresh = storage[prefix + "refreshToken"], device = storage[prefix + "deviceKey"];
  need(typeof refresh === "string" && /^[A-Za-z0-9._~+/=-]{16,16384}$/u.test(refresh)
    && (device === undefined || typeof device === "string" && /^[A-Za-z0-9_-]{1,256}$/u.test(device)),
  "refresh_session_invalid");
  return { public: { region: authority.region, account_id: authority.account_id,
    user_pool_id: pool, client_id: client }, identity: { issuer: id.iss, sub: id.sub }, refresh, device };
}

function checkRefreshPolicy(init, descriptor) {
  if (!descriptor) return;
  const policy = init.refresh_policy;
  need(typeof policy.python === "string" && policy.python.startsWith("/")
    && typeof policy.guard === "string" && policy.guard.startsWith("/"), "refresh_policy_unavailable");
  // No token is passed to the SDK process, its argv, or its environment.
  const environment = Object.fromEntries(["PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE"]
    .filter(key => process.env[key] !== undefined).map(key => [key, process.env[key]]));
  const result = spawnSync(policy.python, [policy.guard], { input: JSON.stringify(descriptor.public),
    encoding: "utf8", env: environment, timeout: 20000, maxBuffer: 4096, stdio: ["pipe", "pipe", "ignore"] });
  need(!result.error && result.status === 0 && result.stdout.trim() === '{"allowed":true}',
    "refresh_policy_not_verified");
}

function allowedRefresh(request, url, init, descriptor) {
  if (!descriptor || request.method() !== "POST" || url.origin !== init.auth_origin
    || url.pathname !== "/" || url.search || url.hash || request.redirectedFrom?.()) return false;
  if (request.headers()["x-amz-target"] !== "AWSCognitoIdentityProviderService.InitiateAuth") return false;
  let body;
  try { body = JSON.parse(request.postData()); } catch { return false; }
  if (!body || Object.keys(body).sort().join(",") !== "AuthFlow,AuthParameters,ClientId"
    || body.AuthFlow !== "REFRESH_TOKEN_AUTH" || body.ClientId !== descriptor.public.client_id) return false;
  const params = body.AuthParameters;
  if (!params || Array.isArray(params) || typeof params !== "object"
    || !["REFRESH_TOKEN", "DEVICE_KEY,REFRESH_TOKEN"].includes(Object.keys(params).sort().join(","))) return false;
  return params.REFRESH_TOKEN === descriptor.refresh
    && (!Object.hasOwn(params, "DEVICE_KEY") || (descriptor.device === undefined
      ? params.DEVICE_KEY === null : params.DEVICE_KEY === descriptor.device));
}

function freshBearer(value, refresh) {
  if (!refresh) return true;
  if (typeof value !== "string" || !value.startsWith("Bearer ")) return false;
  let claims;
  try { claims = jwtClaims(value.slice(7)); } catch { return false; }
  return claims !== null && typeof claims === "object" && !Array.isArray(claims)
    && claims.token_use === "access" && claims.iss === refresh.identity.issuer
    && claims.sub === refresh.identity.sub && claims.client_id === refresh.public.client_id
    && Number.isSafeInteger(claims.exp) && claims.exp >= Date.now() / 1000 + 180;
}

// Only the normal app's one nonrotating refresh is permitted, after fresh policy verification.
// The private seed is read-only; no replacement credentials leave this ephemeral context.
async function bearerFromBrowser(init, session) {
  const deadline = Date.now() + init.start_ms;
  const refresh = refreshDescriptor(init, session);
  checkRefreshPolicy(init, refresh);
  const resolve = name => require.resolve(name, { paths: [init.web_root] });
  const { chromium } = require(resolve("playwright"));
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ serviceWorkers: "block" });
    await context.addInitScript(({ origin, entries }) => {
      if (location.origin === origin) for (const [key, value] of entries) sessionStorage.setItem(key, value);
    }, { origin: session.origin, entries: Object.entries(session.session_storage) });
    let refreshUsed = false;
    await context.route("**/*", async route => {
      const request = route.request();
      let url = null;
      try { url = new URL(request.url()); } catch { url = null; }
      const read = ["GET", "HEAD", "OPTIONS"].includes(request.method());
      if (url && read && (url.origin === init.web_origin || url.origin === init.api_origin)) await route.continue();
      else if (url && request.method() === "POST" && url.origin === init.api_origin
        && url.pathname === "/v1/product-events" && !url.search) await route.continue();
      else if (url && !refreshUsed && allowedRefresh(request, url, init, refresh)) {
        refreshUsed = true;
        // Playwright route.fetch does not follow a credential-bearing redirect.
        try {
          const response = await route.fetch({ maxRedirects: 0, timeout: Math.max(1, Math.min(30000, deadline - Date.now())) });
          if (response.status() >= 300 && response.status() < 400) await route.abort();
          else await route.fulfill({ response });
        } catch { await route.abort(); }
      }
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
      if (!freshBearer(value, refresh)) return;
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
  const nonce = () => (init && typeof init.nonce === "string" ? { nonce: init.nonce } : {});
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
    write({ ready: false, code: error instanceof Refusal ? error.message : "browser_dependency_or_execution_failed", ...nonce() });
    return 1;
  }
  write({ ready: true, ...nonce() });
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

module.exports = { Refusal, ROUTES, allowed, exchange, httpsOrigin, readSession, serve,
  refreshDescriptor, checkRefreshPolicy, allowedRefresh, freshBearer, bearerFromBrowser };
if (require.main === module) {
  serve(process.stdin, process.stdout).then(code => process.exit(code), () => process.exit(1));
}
