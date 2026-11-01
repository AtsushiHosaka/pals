# Static Lean model selection — 2026-11-01

This change selects a production configuration after a manual comparison. It does
not add attempt-based model switching, automatic Sol fallback, or Astra fallback.
The same selected model and reasoning effort are used throughout Lean repairs.

## Fixed roles

| Work | Model | Reasoning |
| --- | --- | --- |
| Lean Draft, Sketch, Prove, Repair | `gpt-6.1-terra` | `medium` |
| OpenMath, retrieval ranking, repair routing | `gpt-6-luna` | `low` |
| Explanation, clarification, independent publication review | `gpt-6-luna` | `low` |
| Existing uncertain Recipe correspondence escalation | `gpt-6.1-terra` | `high` |
| Chat intent classification | `gpt-6.1-sol` | `medium` |

The last two rows describe pre-existing mechanisms; no new Lean generation model
cascade is introduced. Existing explicitly selected Lean models remain supported.
New API and guest requests default to Terra. Ordinary explanations remain Luna;
historical independently reviewed explanations keep their original model identity.

The Lean output allowance is 16,384 tokens, including reasoning tokens. The native
Terra context limit is not a target prompt size. Only relevant mathematical context
is supplied. Temperature and `top_p` are omitted for reasoning requests.

## Same-input comparison

Input: `f:[0,∞)→ℝ`, `f(x)=0` for `x>0`, and `f(0)=1`. Determine the
right-hand limit at zero, prove it, and determine continuity on the stated domain.
Both runs used the real application Draft → Sketch → Prove prompts, one fixed
model and effort, and no repairs. No user histories were submitted.

| Fixed model | Effort | Generation | AWS isolated compilation | Outcome |
| --- | --- | ---: | ---: | --- |
| GPT-6.1 Terra | high | 126.335 s | 1.869 s | Rejected: type mismatch, line 77 |
| GPT-6.1 Terra | medium | 74.872 s | 3.539 s | Accepted |

Accepted Lean source SHA-256:
`a7e6903a9b8f8fbe89b64430691f56ca2f09e0103c6ae466d9b4eca674f49fac`.
The theorem concludes convergence through `nhdsWithin 0 (Set.Ioi 0)` to zero
and failure of `ContinuousWithinAt f (Set.Ici 0) 0`. Its hypotheses retain
both supplied function-value conditions. It does not assert a two-sided limit
for a function left undefined on negative inputs.

Compilation used the existing AWS verifier through its normal verified mTLS
client and unchanged single compile slot. No proof-job row or artifact object
was created. This is compiler evidence, not a public request acceptance result.
One problem with one sample per configuration does not establish comparative
reliability across mathematics. Greater reasoning effort was not better in this
sample; medium is the measured successful and faster fixed configuration.

## Additional requested model and Fast comparison

The same synthetic question was sent through the same three application prompts,
using one fixed model, effort and service tier per run. Returned provider tiers
matched the requested tiers on every call. All five rows are single runs, without
repairs or manual source edits. Provider calls for the three additional settings
were started concurrently; comparisons are not a statistical latency study.

| Fixed configuration | Generation | Estimated generation cost, USD | AWS Lean result |
| --- | ---: | ---: | --- |
| Terra high Standard | 126.335 s | 0.056168–0.05771375 | Rejected |
| Terra medium Standard | 74.872 s | 0.035215–0.036650 | Accepted, 3.539 s |
| Sol medium Standard | 50.670 s | 0.0623985 | Rejected, 1.719 s |
| Terra high Fast | 72.685 s | 0.109081 | Rejected, 3.512 s |
| Terra medium Fast | 45.409 s | 0.0671335 | Rejected, 3.689 s |

New-run estimates include reported cache writes and the actual processing tier.
The two earlier records omit cache-write counts, so their cost is a range between
ordinary input and all uncached input charged at the default 30-minute write rate.
Reasoning tokens are included in output tokens exactly once. These are estimates
from token usage and published rates, not invoices. Compilation, subsequent
explanation, retries and public request waiting time are excluded.

Terra Fast short-context input/output prices equal Sol Standard: USD 2/10 per
million tokens; cached input is USD 0.10 and a 30-minute cache write is USD 2.50.
Fast costs twice the corresponding Standard rates, but the amount of generated
text/reasoning also changes between samples. In this sample, Sol medium was faster
and slightly more expensive than Terra high; neither produced an accepted proof.
No ten-second verified response is demonstrated by these experiments.

## Parallel-lemma prototype and repair feedback finding

An offline prototype schedules independent lemma bodies with at most four API
workers and enforces exact typed goal/context/dependency bindings. Its 26 tests
cover scheduling and fail-closed assembly, not mathematical validity or live
speed. It is not enabled in the production worker. Current Draft output is prose;
a safe general typed-plan extraction and admission path remains necessary.
Parallelizing only after Sketch cannot meet ten seconds in this measured example:
Draft plus Sketch already took 35.686 seconds.

Source inspection and an offline diagnostic probe also found that the current
verifier HTTP boundary reduces multiline Lean errors to code, symbol and source
position. The repair prompt receives a generic type-mismatch sentence without the
expected/actual types. This information loss is established; it is not established
as the sole cause of the earlier twelve unsuccessful repairs. A separately
versioned, source-bound internal mathematical diagnostic contract is needed to
carry useful detail without exposing raw compiler logs or weakening validation.

## Recipe latency change

For an initial text-only request without prior conversation or materials,
premise resolution and search-intent extraction now share one structured call.
If later convention resolution changes the final statement, its prepared search
intent is discarded. Contextual, visual, material and clarification paths retain
the established separate extraction. Both independent Recipe applicability and
answer reviews remain mandatory. Sealed source hashes remain checked locally and
in settlement evidence; non-mathematical hashes are omitted from the judge prompt.

The simple full chat path has four sequential model calls rather than five.
This is a structural improvement, not evidence that the five-second target has
been achieved. Public guest measurements must be recorded after deployment.

## Price provenance

[Official API pricing](https://developers.openai.com/api/docs/pricing), checked
2026-11-01: Terra Standard short-context input USD 1.00, cached input USD 0.05,
30-minute cache write USD 1.25, and output USD 5.00 per million tokens. Above
272,000 input tokens, input/cache-write prices double and output is USD 7.50.
The versioned application estimator conservatively uses the 30-minute write rate
for all input; it is not an exact provider invoice. Historical prices are immutable.

[GPT-6 usage guidance](https://developers.openai.com/api/docs/guides/latest-model)
and the [Terra model reference](https://developers.openai.com/api/docs/models/gpt-6.1-terra)
are the source for reasoning controls and supported context sizes.
