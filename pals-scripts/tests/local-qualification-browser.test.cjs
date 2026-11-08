"use strict";
// Dispatch-policy unit tests only; no browser, fake product answer, or live release qualification.
const test = require("node:test"), assert = require("node:assert/strict");
const { admitRequest } = require("../local-qualification-browser.cjs");
test("verify-existing rejects every paid proof mutation BEFORE dispatch", () => {
  const c = { proofPosts: 0, telemetry: 0 };
  for (const method of ["POST", "PUT", "PATCH", "DELETE"]) {
    for (const endpoint of ["/v1/guest/proof-requests", "/v1/guest/proof-requests/old/premise", "/v1/proof-requests", "/v1/chats/new"]) {
      assert.equal(admitRequest(method, "http://localhost:58000" + endpoint, true, c), false);
    }
  }
  assert.equal(c.proofPosts, 0);
  assert.equal(admitRequest("POST", "http://localhost:58000/v1/guest/session", true, c), true);
});
test("initial capture permits only one actual guest proof submission", () => {
  const c = { proofPosts: 0, telemetry: 0 };
  assert.equal(admitRequest("POST", "http://localhost:58000/v1/guest/proof-requests", false, c), true);
  assert.equal(admitRequest("POST", "http://localhost:58000/v1/guest/proof-requests", false, c), false);
  assert.equal(admitRequest("POST", "https://external.invalid/v1/guest/proof-requests", false, c), false);
});
