# Mathematical request interpretation

The prompt flow previously described most inputs as supplied claims to prove.
This tuning explicitly distinguishes proving a claim from computing a value,
finding all solutions, determining a classification, and explaining a concept.

Preflight preserves a well-posed computation as an unanswered request. The
unknown result is not a missing premise. Clarification remains appropriate for
missing domains or data that change the answer; existing false-claim and saved
convention handling remains in place. Short questions such as asking for the
units of a particular ring require verification, while asking for the definition
of a unit remains an ordinary explanation.

DSP derives a candidate result in its informal Draft, then places that result in
the theorem conclusion. An exact user-supplied Lean harness remains fixed.
All-solutions requests require completeness, and optimization requires both a
global bound and attainment. Independent semantic review and answer review check
the result against the original task; explanation presents the established result
and its derivation. Recipe search preserves the unknown target without guessing
an answer. No API/schema changes or verification bypasses are introduced.

## Evidence

- Agent commit: `bb62e23`.
- 246 focused tests pass, covering generation, explanations, preflight, false
  claims, follow-ups, chat/PDF routing, Recipe/DSP handoff, and the evaluation tool.
- Ruff passes on all changed Python files. Strict mypy passes on the five changed
  production modules. Independent source review found no actionable defects.
- New handoff tests use mocked provider responses and prove request preservation
  and formal routing, not model understanding or mathematical accuracy.
- `pals-agent/tools/evaluate_math_request_intent.py` evaluates actual preflight
  and informal Draft prompts on seven cases, including Japanese calculation and
  classification inputs, with a separate semantic judge. It reads only an
  existing `OPENAI_API_KEY` environment variable and makes at most 21 calls.
- Live provider evaluation was not run because that variable is absent. The tool
  does not evaluate routing, formalization, Lean compilation or deployed behavior.
  No production accuracy improvement or deployment is claimed.

Run the bounded prompt evaluation from an agent environment with the provider key
already set:

```sh
python tools/evaluate_math_request_intent.py
```
