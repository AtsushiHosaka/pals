# Production guest proof smoke — 2026-11-06

Status: **NOT VERIFIED** after the observation window. This is a single
owner-authorized production guest UI trial, not a model comparison or a general
accuracy measurement. No completed answer was visible at the last observation;
the backend terminal outcome is unknown.

## Trial and evidence

The browser observer reports exactly one guest proof request. Its UI click-start
was `2026-11-06T00:37:23.810Z`. The displayed default model was GPT-6.1 Terra High;
the observer did not change that selection. The controlled problem concerns
universal integer divisibility, including negative integers. The raw request and
response are omitted from this public record.

| Observation | Result |
|---|---|
| User submissions | 1, reported by the browser observer |
| UI at `00:52:31.772Z` | Still verifying the proof in Lean; no completed answer, 907.962 seconds after click-start |
| UI at `00:53:22.627Z` | Added a taking-longer-than-expected warning and a Check status button; 958.817 seconds after click-start |
| Read-only status check at `00:53:39.016Z` | Clicked Check status once; the warning disappeared, but the UI still showed verification in progress and no completed answer |
| Completed end-to-end proof | NOT VERIFIED |
| Backend terminal result | Unknown |
| Actual formal artifact and target | Unknown |
| Fresh generation versus catalog reuse | Unknown |
| Independent Lean rerun | Not performed for this record |
| UI observation lower bound | At least 975.206 seconds from click-start through the status check; not a measured backend execution time |
| Model usage and cost | Not observed |

The observer did not resubmit the question. The read-only status check is not a
second proof trial. The earlier panel message exposing no artifact does not show
that generation had not started: this UI withholds unverified candidates. The
900-second UI waiting budget is an observation budget, not backend cancellation,
a worker lease, or a pipeline deadline. No mathematical failure, terminal job
failure, or cause has been established.

The recorder did not operate the browser or run a proof, model, service, or
deployment. UI answer delivery, displayed verification, target inspection, and
an independent compiler result are distinct observations. This smoke does not
establish the deployed source revision or unrelated feature behavior.

## Ledger and monitoring scope

Ledger row `2026-11-06-production-guest-proof-ui-unfinished` records one attempt
while preserving all 447 baseline rows. Success count, success rate, failure
counts, cost, and latency percentiles are blank. Its `latency_other` records the
unfinished UI-observation lower bound. No failure count is invented from an
incomplete observation, and internal calls or UI stages do not increase the
number of user attempts. The existing
[localized-diagnostic issue #270](https://github.com/AtsushiHosaka/pals/issues/270)
is not established as the cause of this request's unfinished state.

An attempted automation update to schedule new charged proof requests was
rejected by automatic approval review because recurring model-cost approval was
absent. A safer update to the same automation succeeded and its saved instructions
were read back:
prioritize read-only observation of this one-off request, keep an unfinished
outcome unknown rather than healthy, and block new charged proof submissions
until explicit recurring-cost approval. This changes recording and monitoring
instructions only; it does not change the application implementation or deploy
a release.

Coordination: [monitor #246](https://github.com/AtsushiHosaka/pals/issues/246).
The existing [ledger schema](quality-ledger/ledger.schema.md) and
[failure taxonomy](quality-ledger/taxonomy.md) govern the row. The monitor's
sanitized observation is the row's public source; the observer published and
read it back at `2026-11-06T00:55:07Z`. Raw content, identifiers, private URLs,
screenshots, and logs stay outside this report.

## Terminal UI follow-up — 2026-11-06

The earlier unfinished snapshot above is preserved verbatim. At
`2026-11-06T01:02:45.950Z`, the observer first saw a terminal UI failure for the
same submitted guest request. The Lean panel was removed and the UI stated,
in English translation: “The answer will not be shown because Lean could not
verify it. You can retry.” The composer became available again. The observer
retained another private accessibility capture and screenshot at
`2026-11-06T01:03:26.011Z`. No retry or new proof submission was made. The observer
also confirmed the entry path as `/try`.

The interval from the original click-start to the first observed terminal UI
failure is **1522.140 seconds**. This is an observation upper bound for the UI
failure becoming visible, not the exact backend execution duration. The
previous 975.206-second unfinished snapshot remains valid for its earlier
observation time; the 900-second UI budget did not cancel the pipeline.

The user-facing proof attempt ended without a completed answer. There is no
underlying diagnostic, log, or available formal artifact establishing the cause.
In particular, this does not establish a compiler error, mathematical invalidity,
missing Lean runtime, or the cause tracked in #270. Generation versus reuse,
model usage and cost remain unknown, and no independent Lean rerun was made.
No application implementation, deployment, or recurring-cost authorization was
changed by this follow-up.

Ledger row `2026-11-06-production-guest-proof-ui-terminal-followup` records the
same one attempt with `n=1`, `successes=0`, `success_rate=0`, and one
`unclassified` UI failure. Its `overlap_with` points to
`2026-11-06-production-guest-proof-ui-unfinished`; it is not a second trial.
All 448 previously committed rows remain byte-for-byte unchanged. Cost and
latency percentiles remain blank; `latency_other` carries the observation upper
bound. The public source remains the monitor's sanitized report in #246.

Under the existing chart contract, overlapping rows are excluded from success
and failure aggregates. The original snapshot has no numeric outcome and the
terminal follow-up is overlapping, so neither contributes a success or failure
point to those charts. They do not implement latest-outcome coalescing; the
terminal result is explicit in this report and ledger, rather than inferred
from an aggregate chart.
