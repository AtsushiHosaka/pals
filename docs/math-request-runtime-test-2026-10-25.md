# Math request interpretation runtime test

The task-interpretation prompts passed the tested real-provider interpretation
checks. Both unseen local DSP/Lean cases failed (0/2 completed). These are
separate results; passing the informal checks does not establish an end-to-end
solution capability.

## Environment and scope

- Candidate: `pals-agent` commit `bb62e23`; parent integration `aa892a2`.
- Interpreter: existing primary-checkout Python 3.12.13 environment; current
  worktree source imported explicitly.
- Provider: real OpenAI Responses API at `api.openai.com`, using the existing
  local test configuration. No credentials are included in this report or logs.
- Models: `gpt-6-luna` for preflight, DSP and review; `gpt-6.1-sol` for chat intent.
- Lean: existing cached primary-checkout workspace, Lean 4.32.0-rc1. No service
  restart, duplicate container, dependency installation or deployment occurred.
- Local DSP tests use no catalog and allow two repair generations after the
  initial attempt, with a 60-second compiler timeout. They do not exercise API
  reconciliation, queues, real catalog retrieval, billing, persistence or UI.

## Real preflight and informal Draft: 7/7 PASS

The existing evaluation tool supplied actual preflight and Draft prompts to the
provider. Each case used a fresh separate semantic judge call. An independent
source-level mathematical review also checked the returned outputs.

| Request | Observed result | Verdict |
| --- | --- | --- |
| Finite-dimensional linear endomorphism: injective iff surjective | Ready; rank-nullity proof gives both implications under the supplied assumptions. | PASS |
| Rank over the reals of `[[1,2,3],[2,4,6],[1,1,1]]` | Ready; derives rank 2 using an explicit column dependency and independence of the first two columns. | PASS |
| All real solutions of `sqrt(x+2)=x` | Ready; derives exactly `{2}`, rules out the extraneous root -1 and checks the converse. | PASS |
| Units of `Z/12Z` | Ready; derives exactly `{1,5,7,11}`, verifies inverses and excludes every other residue. | PASS |
| Solutions of `x^2+1=0` without a domain | Requests the number system; no Draft is generated. | PASS |
| Every continuous real function is uniformly continuous | Requests clarification with a tentative counterexample and an option to keep the original claim; no Draft is generated. | PASS |
| The domain question above, clarified as complex numbers | Ready; derives exactly `{i,-i}` with completeness, without repeating the question. | PASS |

One minor observed issue: the false-premise clarification offers two substantially
duplicate options to keep the original claim. This is recorded rather than hidden.

These cases are a small smoke sample, not an accuracy estimate. The task prompts
already contain some of these examples, so they do not all measure generalization.
The two local Lean cases below use different questions and constants.

## Real intent routing: 4/4 PASS

| Japanese input | Expected and observed route | Verdict |
| --- | --- | --- |
| Calculate the matrix rank above | `lean` | PASS |
| What are the units of `Z/12Z`? | `lean` | PASS |
| What is a unit in a ring? | `explanation` | PASS |
| What are the real solutions of `abs(x-2)+abs(x+1)=5`? | `lean` | PASS |

These are real calls using the current ChatRuntime classifier prompt. They stop
after routing and do not submit a persistent application request.

## Local DSP and Lean: 0/2 completed

Results are recorded after all bounded attempts finish. Compiler rejection means
the test fails even when the informal answer is mathematically correct. Semantic
and explanation review are attempted only after compilation succeeds.

| Unseen Japanese request | Informal result | Compiler result | Total time | Verdict |
| --- | --- | --- | --- | --- |
| Minimum of `x^2-6x+13` over the reals, including every minimizer | Correctly derives minimum 4, attained exactly at x=3, with a global bound. | Fails after two repairs: syntax errors, unknown local identifiers and unsolved goals. | 69.24 s | FAIL |
| All real solutions of `abs(x-2)+abs(x+1)=5` | Correctly derives exactly x=-2 or x=3 by exhaustive interval cases and substitution. | Fails after two repairs: the final candidate supplies a non-strict inequality where a strict inequality is required. | 62.59 s | FAIL |

Both requests passed preflight without asking the learner to supply the answer.
Their generated Drafts contain the correct result and a complete ordinary
mathematical argument. Their generated Lean is rejected by the actual compiler.
No answer is approved or published, and semantic/explanation review is not reached.
The demonstrated remaining failure is formalization/repair, rather than a missing
task interpretation. The tests do not establish that prompt tuning alone solves
the complete calculation path, nor do they measure the full production repair
budget or deployed behavior.

## Additional user-supplied limit example

Input: `f(x)=0 (x>0), 1(x=0)という関数でx->0の極限を求めよ`.

The real router selects `lean`. Preflight returns `ready` and explicitly resolves
the domain to the nonnegative reals, with the limit taken within that domain
(the right-hand limit). It does not ask a clarification question. The generated
Draft obtains limit 0 using delta=1 for every positive epsilon; the point value
f(0)=1 does not affect this punctured limit.

This example completes the local test: generated Lean compiles after two repairs,
independent semantic review approves the right-limit target, and the final
Japanese explanation passes independent output review. Its generated conclusion
is: `したがって、定義域内で $x\to0$ としたときの極限は $0$ である。`
Evidence: `user-limit-question.json` and `user_limit-lean.json` in the temporary
directory below. This is one observed local run, not a deployed UI result or a
guarantee that every stochastic generation succeeds.

The temporary test wrapper initially passed the unnormalized original question
to the explainer. That produced a conflicting two-sided-limit explanation, which
was retained separately as `user_limit-original-wording-explanation.json`.
Source tracing confirms the actual API/worker passes the resolved linked-job
statement instead. Explanation and output review were rerun using that statement
and the same already verified Lean source; those corrected outputs are the
reported result. The wrapper was also corrected to pass both required deadline
arguments and to treat a returned ProofOutputReview as approval.

## Reproduction and evidence

The checked-in provider evaluator can be run from an agent environment with
`OPENAI_API_KEY` already set:

```sh
python tools/evaluate_math_request_intent.py --output /private/tmp/math-intent.json
```

The provider report and task-owned runner scripts for this run are in
`/private/tmp/pals-math-task-live-20261025/`. They contain synthetic test inputs,
model outputs, judgments and timings, not credentials. `run.py` reads only the
existing key and provider endpoint from the primary checkout's local configuration
and evaluates the seven cases with three concurrent provider tasks.
`route_live.py` captures the actual ChatRuntime classifier prompt for four cases.
`verify_lean.py` composes the existing generator, local verifier and artifact store,
then runs the two unseen questions sequentially and, on compiler success, the
existing semantic reviewer, explainer and answer reviewer. No hand-authored proof
is substituted for generated output.

The exact task-handling prompt text is exported to `current-prompts.md` in that
temporary evidence directory. Raw generated artifacts remain outside Git, as
required by the repository policy. No production or browser end-to-end success
is claimed by this report.
