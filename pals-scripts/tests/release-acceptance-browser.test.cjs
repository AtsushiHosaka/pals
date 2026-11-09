"use strict";
const test = require("node:test"), assert = require("node:assert/strict"), crypto = require("node:crypto");
const { semanticTokens, normalizeMath, validateAnswer } = require("../release-acceptance-browser.cjs");
const hash = value => crypto.createHash("sha256").update(value).digest("hex");
// Unit boundary only: the live observer loads real remark/Playwright and never this parser.
const plain = { parse: value => ({ type: "text", value }) };
function fixture() {
  const expected = { id: "request", chat_id: "chat", generation_model: "model", reasoning_effort: "high", output_language: "en",
    required_conclusion_text: ["Therefore the limit is zero."], required_conclusion_math: [] };
  const request = { id: "request", chat_id: "chat", status: "answered", error_code: null, created_at: "2026-11-08T10:01:00Z",
    generation_model: "model", generation_reasoning_effort: "high", output_language: "en", formal_job_id: "job",
    answer: { text: "Overview\n\nThe bound tends to zero.\n\nTherefore the limit is zero.", evidence_kind: "lean_verified",
      lean: { source: "proof_job", proof_job_id: "job", lean_sha256: hash("verified Lean") } } };
  const job = { id: "job", chat_id: "chat", state: "verified", output_language: "en", created_at: "2026-11-08T10:01:01Z" };
  const explanation = { proof_job_id: "job", state: "completed", content: { overview: "Overview", sections: [{ summary: "The bound tends to zero." }], conclusion: "Therefore the limit is zero." } };
  const source = { job_id: "job", chat_id: "chat", lean_code: "verified Lean" };
  return { request, job, explanation, source, expected, activation: Date.parse("2026-11-08T10:00:00Z") };
}
function check(f) { return validateAnswer(f.request, f.job, f.explanation, f.source, f.expected, f.activation, plain); }

test("an accepted proof requires the unique final conclusion in its saved answer", () => {
  check(fixture());
  const f = fixture(); f.request.answer.text = "Overview\n\nThe bound tends to zero.";
  assert.throws(() => check(f), /stored_answer_dropped_explanation_content/u);
});
test("health, submission, llm assessment, and failed explanation cannot qualify", () => {
  for (const mutation of [f => f.request.status = "verifying", f => f.request.answer.evidence_kind = "llm_assessed",
    f => f.job.state = "failed", f => f.explanation.state = "failed", f => f.explanation.content.conclusion = ""]) {
    const f = fixture(); mutation(f); assert.throws(() => check(f));
  }
});
test("old completed requests and old formal jobs cannot qualify a new runtime", () => {
  const f = fixture(); f.request.created_at = "2026-11-08T09:59:00Z";
  assert.throws(() => check(f), /fresh_terminal_request_required/u);
  const g = fixture(); g.job.created_at = "2026-11-08T09:59:00Z";
  assert.throws(() => check(g), /fresh_verified_job_required/u);
});
test("wrong model, locale, or Lean source binding blocks acceptance", () => {
  const f = fixture(); f.request.generation_model = "different";
  assert.throws(() => check(f), /request_configuration_differs/u);
  const g = fixture(); g.source.lean_code = "another proof";
  assert.throws(() => check(g), /verified_source_binding_differs/u);
});
test("an oracle repeated only in the overview cannot stand in for a unique conclusion", () => {
  const f = fixture(); f.expected.required_conclusion_text = ["Overview"];
  assert.throws(() => check(f), /unique_conclusion_text_required/u);
});
test("semantic text joins formatting spans without duplicating math", () => {
  assert.deepEqual(semanticTokens([{ kind: "text", value: "The " }, { kind: "text", value: "limit " },
    { kind: "math", value: "x^2" }, { kind: "text", value: " is zero." }]),
  [{ kind: "text", value: "The limit" }, { kind: "math", value: "x^2" }, { kind: "text", value: "is zero." }]);
});
test("slash math normalizes outside code and preserves inline code", () => {
  assert.equal(normalizeMath("The \\(x^2\\) term and `\\(literal\\)`"), "The $x^2$ term and `\\(literal\\)`");
});
