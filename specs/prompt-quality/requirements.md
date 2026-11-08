# Prompt quality measurement

Status: WORKING implementation contract, based on the November 8, 2026 request.
The user selected undergraduate learners as the initial explanation audience.

| ID | Requirement and observable acceptance |
| --- | --- |
| PQ-001 | An explicit offline command shall evaluate a private fixed dataset through the ordinary natural-answer runtime, recording immutable dataset, prompt-source bundle, generation configuration, retrieval snapshot, evaluator and model identities. It shall not create or settle customer tasks. |
| PQ-002 | Every case/repetition shall retain independent mathematical correctness, logical completeness, notation consistency, pedagogical clarity and concision scores. Generation or evaluation failures shall remain visible, with unavailable scores represented as null. QA approval and successful answering shall not be labelled accuracy. |
| PQ-003 | Comparison shall require equal datasets, generation controls, retrieval snapshots, judge/rubric/audience and case/repetition populations. It shall expose paired deltas, improvements/regressions/ties, missing measurements, denominators and case-cluster uncertainty. A source bundle can include implementation changes; comparison shall not assert prompt-only causality. |
| PQ-004 | CloudWatch-bound records shall use a closed schema containing only fingerprints, non-identifying labels, scores, outcomes, latency and measured usage. Questions, references, answers, judge rationales, user identifiers and secrets shall never be accepted into these records. |
| PQ-005 | An explicit publisher shall write validated records to a dedicated CloudWatch log group, verify read-back and fail on uncertain delivery. Retrieval shall paginate, validate records and deduplicate identical deliveries, rejecting conflicting run identities. Partial publication shall not be reported as success. |
| PQ-006 | Operators shall obtain summaries and paired JSON/CSV using a CLI without a new web application. Terraform shall define the dedicated retained log group, narrowly scoped operator policies and discoverable queries. Infrastructure and live measurements require separate runtime verification. |
| PQ-007 | The workflow shall preserve existing canonical Lean evaluation and audited Langfuse exports. It shall not resume stopped observers, alter production prompts, deploy services or incur model calls unless the explicit evaluation command is run. |

LLM judging is a measurement proxy. Claiming actual learner comprehension requires human calibration; claiming an improvement requires measured baseline/candidate results. Neither is supplied by implementation tests.

Current direct execution covers the chat explanation route. Claim-bound Recipe/Lean
proof requests retain their failed/unavailable observations; this slice does not
create the worker claims required to complete that path. Full proof-answer collection
must be integrated before claiming complete production-answer coverage.
