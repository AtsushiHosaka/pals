# Prompt quality measurement

Status: WORKING implementation contract, based on the November 8, 2026 request.
The user selected undergraduate learners as the initial explanation audience.
The follow-up authorizes completing the Lean evaluator, deployment, real evaluation,
CloudWatch retrieval and graphs. The user selected their existing PALS account.

| ID | Requirement and observable acceptance |
| --- | --- |
| PQ-001 | Explicit commands shall evaluate a fixed dataset through either the direct explanation runtime or the real owner-scoped API. Live execution may create isolated benchmark chats/quotes/requests for the selected account, retaining its ordinary billing, claim and Lean flow. References remain evaluation-only. Both modes record dataset, source/configuration, retrieval, evaluator and model identities. |
| PQ-002 | Every case/repetition shall retain independent mathematical correctness, logical completeness, notation consistency, pedagogical clarity and concision scores. Generation or evaluation failures shall remain visible, with unavailable scores represented as null. QA approval and successful answering shall not be labelled accuracy. |
| PQ-003 | Comparison shall require equal datasets, generation controls, retrieval snapshots, judge/rubric/audience and case/repetition populations. It shall expose paired deltas, improvements/regressions/ties, missing measurements, denominators and case-cluster uncertainty. A source bundle can include implementation changes; comparison shall not assert prompt-only causality. |
| PQ-004 | CloudWatch-bound records shall use a closed schema containing only fingerprints, non-identifying labels, scores, outcomes, latency and measured usage. Questions, references, answers, judge rationales, user identifiers and secrets shall never be accepted into these records. |
| PQ-005 | An explicit publisher shall write validated records to a dedicated CloudWatch log group, verify read-back and fail on uncertain delivery. Retrieval shall paginate, validate records and deduplicate identical deliveries, rejecting conflicting run identities. Partial publication shall not be reported as success. |
| PQ-006 | Operators shall obtain summaries and paired JSON/CSV using a CLI without a new web application. Terraform shall define the dedicated retained log group, narrowly scoped operator policies and discoverable queries. Infrastructure and live measurements require separate runtime verification. |
| PQ-007 | The workflow shall preserve existing Lean evaluation, audited Langfuse exports and stopped observers. Deployment is limited to measurement infrastructure; live model calls and benchmark tasks occur through explicit commands. A prompt improvement requires a distinct identified candidate and real measurements. |
| PQ-008 | Live proof cases shall independently read owner-authorized Lean evidence and recompute source/answer digests. Catalog cases require immutable Recipe/entry/compiler/toolchain bindings; generated cases require a matching verified job and source. Formal verification and delivered explanation are separate. Answered/QA status alone is insufficient. |
| PQ-009 | A private durable journal shall precede external mutations, avoid replay after uncertain POSTs and bind resume to the same account/run/configuration. Normal request/credit limits remain enforced. Pending or unknown submission is distinct from terminal failure. Passwords, bearer tokens and raw API responses remain local. |
| PQ-010 | Deployment shall use separate encrypted/locked measurement state and an inspected additive saved plan. Displayed graphs shall use validated results fetched from CloudWatch, with missingness and sample sizes visible. |
| PQ-011 | A versioned problem registry shall pin complete fixture and dataset digests and preserve append-only observations. Confirmed content defects, review candidates, application defects and operational delays shall remain distinct. Recovery shall add an observation rather than erase an earlier pending state. Private production content shall not be added to public fixtures under the authored-benchmark consent. |
| PQ-012 | An explicit explanation-stage experiment shall replay fixed, previously verified authored Lean sources through the actual generator, validators and reviewer. Both prompt arms shall generate fresh outputs with identical source, model, projection and judging controls. Only the versioned instruction policy may differ. It shall retain unsuccessful calls and repeated paired observations without claiming a new Lean proof or full-flow improvement. |
| PQ-013 | A frozen iteration manifest shall identify the stage, ordered baseline/candidate runs and evaluation population. A reusable report shall reject unmatched controls or populations and expose all five score changes, per-case regressions, missingness and uncertainty. Displayed iteration graphs shall be generated from validated CloudWatch fetches. Small or inconclusive changes shall not be promoted as established gains. |

LLM judging is a measurement proxy. Claiming actual learner comprehension requires human calibration; claiming an improvement requires measured baseline/candidate results. Neither is supplied by implementation tests.

Direct execution still covers explanations. The live API runner follows the actual
claim-bound proof path. Local tests do not establish production success; the live
observations and any missing prerequisites are recorded separately.
