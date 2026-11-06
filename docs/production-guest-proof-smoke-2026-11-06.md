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
