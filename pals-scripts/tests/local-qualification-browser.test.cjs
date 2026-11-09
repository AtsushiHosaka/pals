"use strict";
// Dispatch-policy unit tests only; no browser, fake product answer, or live release qualification.
const test = require("node:test"), assert = require("node:assert/strict");
const { admitRequest, withSubmissionMarker } = require("../local-qualification-browser.cjs");
const fs = require("node:fs"), path = require("node:path"), os = require("node:os");
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
test("the real private marker exists and is synced before submission and cannot be reused", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "pals-submission-barrier-"));
  try {
    const file = path.join(directory, "submission.json"); let submissions = 0;
    await withSubmissionMarker(file, { state: "submission_started" }, () => {
      assert.equal(JSON.parse(fs.readFileSync(file)).state, "submission_started");
      assert.equal(fs.statSync(file).mode & 0o777, 0o600); submissions++;
    });
    await assert.rejects(withSubmissionMarker(file, {}, () => { submissions++; }), /EEXIST/u);
    assert.equal(submissions, 1);
  } finally { fs.rmSync(directory, { recursive: true }); }
});
test("a real file sync failure prevents submission", async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "pals-submission-sync-failure-"));
  const original = fs.fsyncSync; let submitted = false;
  try {
    fs.fsyncSync = () => { throw new Error("injected_disk_sync_failure"); };
    await assert.rejects(withSubmissionMarker(path.join(directory, "submission.json"), {}, () => { submitted = true; }), /injected_disk_sync_failure/u);
    assert.equal(submitted, false);
  } finally { fs.fsyncSync = original; fs.rmSync(directory, { recursive: true }); }
});
