"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { acceptanceRoute, seedSessionOnce } = require("../release-acceptance-browser.cjs");
const init = { api_origin: "https://api.example.test", auth_origin: "https://cognito-idp.ap-northeast-1.amazonaws.com" };
const descriptor = { public: { client_id: "client1" }, refresh: "fixture-refresh-value" };
test("reload preserves the ephemeral app-refreshed session instead of replaying the expired seed", () => {
  const before = { location: global.location, sessionStorage: global.sessionStorage };
  const storage = new Map();
  global.location = { origin: "https://web.example.test" };
  global.sessionStorage = { getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, value) };
  try {
    const seed = { origin: global.location.origin, entries: [["idToken", "expired-fixture"]] };
    seedSessionOnce(seed); assert.equal(storage.get("idToken"), "expired-fixture");
    storage.set("idToken", "fresh-fixture");
    seedSessionOnce(seed); assert.equal(storage.get("idToken"), "fresh-fixture");
    global.location.origin = "https://elsewhere.example.test"; storage.clear();
    seedSessionOnce(seed); assert.equal(storage.size, 0);
  } finally { Object.assign(global, before); }
});
function setup(refresh = descriptor) {
  const counters = { attemptedWrites: 0, telemetryPosts: 0, authPosts: 0 };
  return { counters, handle: acceptanceRoute(init, refresh, Date.now() + 60000, counters) };
}
function route(options = {}) {
  const calls = [];
  const request = { method: () => options.method || "POST", url: () => options.url || init.auth_origin + "/",
    headers: () => ({ "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth" }),
    postData: () => JSON.stringify(options.body || { AuthFlow: "REFRESH_TOKEN_AUTH", ClientId: "client1", AuthParameters: { REFRESH_TOKEN: descriptor.refresh } }),
    redirectedFrom: () => null };
  return { calls, request: () => request, continue: async () => calls.push("continue"), abort: async () => calls.push("abort"),
    fetch: async opts => { calls.push(opts); return { status: () => options.status || 200 }; },
    fulfill: async () => calls.push("fulfill") };
}
test("acceptance forwards only one app refresh without following redirects", async () => {
  const { handle, counters } = setup(); const first = route(); await handle(first);
  assert.equal(first.calls[0].maxRedirects, 0); assert.ok(first.calls[0].timeout > 0 && first.calls[0].timeout <= 30000);
  assert.equal(first.calls[1], "fulfill"); assert.equal(counters.authPosts, 1);
  const second = route(); await handle(second); assert.deepEqual(second.calls, ["abort"]);
  assert.equal(counters.attemptedWrites, 1);
});
test("refresh redirects fail closed and cannot receive a second send", async () => {
  const { handle, counters } = setup(); const first = route({ status: 307 }); await handle(first);
  assert.equal(first.calls[0].maxRedirects, 0); assert.equal(first.calls[1], "abort");
  assert.equal(counters.attemptedWrites, 1);
  const second = route(); await handle(second); assert.deepEqual(second.calls, ["abort"]);
});
test("unconfigured auth, oauth token grants and other auth flows are blocked", async () => {
  const absent = setup(null), denied = route(); await absent.handle(denied); assert.deepEqual(denied.calls, ["abort"]);
  for (const options of [{ url: init.auth_origin + "/oauth2/token" },
    { body: { AuthFlow: "USER_PASSWORD_AUTH", ClientId: "client1", AuthParameters: { REFRESH_TOKEN: descriptor.refresh } } }]) {
    const { handle } = setup(); const item = route(options); await handle(item); assert.deepEqual(item.calls, ["abort"]);
  }
});
test("existing reads and passive product telemetry stay available", async () => {
  const { handle, counters } = setup(null);
  const read = route({ method: "GET", url: "https://assets.example.test/file.js" }); await handle(read);
  assert.deepEqual(read.calls, ["continue"]);
  const telemetry = route({ url: init.api_origin + "/v1/product-events" }); await handle(telemetry);
  assert.deepEqual(telemetry.calls, ["continue"]); assert.equal(counters.telemetryPosts, 1);
});
