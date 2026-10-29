# Implementation work streams

All deliverables begin as pending. A research result, dispatch, or PR is not a
verified runtime feature. All six chats below were confirmed active and attached
to PALS project `local-da76878add3e9ce6a27a5a03bcb4330b` on 2026-10-28 JST.

| Task | Chat title | Chat ID | Observed state |
| --- | --- | --- | --- |
| T1 | PALS公開状態と安全性を再監査 | `01a17e1a-54d2-7521-8f56-1908f9fdcb71` | Active at dispatch verification |
| T2 | PALS初等幾何と公理に基づくLean証明 | `01a17e1a-bbb0-7280-b009-9b563cb1f04f` | Active at dispatch verification |
| T3 | PALSチャット内のTikZ図形と可換図式描画 | `01a17e1a-c75b-7f50-982b-bf6045a1cb2a` | Active at dispatch verification |
| T4 | PALS変数名に依存しない定理検索DB | `01a17e1b-506f-7e61-a1ae-ad28006f13b4` | Active at dispatch verification |
| T5 | PALS Leanコンパイルと検証済み成果物の高速化 | `01a17e1b-5a11-71a3-810a-d66bf539260e` | Active at dispatch verification |
| T6 | PALS大学数学から難関入試までの検証コーパス | `01a17e1b-675b-7110-9f7b-11fda8dbf163` | Active at dispatch verification |

| Task | Requirements | Owner and bounded deliverable | Required evidence |
| --- | --- | --- | --- |
| T1 Security | MRD-001, 010 | Refresh public Git refs and secret-history coverage; standard source-backed application/trust-boundary audit of parent plus six children; retain excluded admin boundary. | Exact revisions, visibility readback, redacted gate result, source-backed findings and honest unavailable coverage. |
| T2 Geometry | MRD-002, 003, 004, 011 | Research reusable foundations; implement one substantive input-to-formal-geometry-to-checked-trace slice in agent and necessary API domain code; use T3 payload contract. | Actual pinned Lean proof, transitive axiom review, original/confirmed assumptions, checked ordered steps, negative/degenerate cases, and matching rendered result after T3 integration. |
| T3 Chat diagrams | MRD-004, 005, 010 | Own shared diagram payload, safe renderer, persistence/transport, frontend chat rendering and TikZ/tikz-cd source. | Real render worker and browser checks for geometry and a commutative square, reload/mobile/accessibility, malicious-input bounds, render-failure behavior, and preservation of existing explanation/source actions. |
| T4 Theorem search | MRD-006, 007, 008, 009 | Measure each current retrieval path; implement versioned alpha/typed structural matching alongside existing recall and preserve admission boundaries. | Real DB and pinned Lean checks; binder-renaming positives; scope/type/repeated-variable/premise/dependent-quantifier negatives; typed specialization obligations; Recall@k/MRR/false-accept/latency comparison. |
| T5 Lean acceleration | MRD-007, 008, 009 | Reuse existing local prototypes where applicable; implement measured import/compiler/artifact-cache acceleration without weakening verified status. | Same substantive proof corpus before/after, cold/warm p50/p95 and stage timing, real compiled-artifact hits, stale/tampered/dependency/toolchain invalidation and concurrent isolation. |
| T6 Coverage | MRD-003, 005, 007, 011 | Audit supported undergraduate families; add substantive verified examples through the existing catalog-authoring workflow and define an entrance-exam evaluation corpus. | Family-to-source/toolchain/proof coverage matrix; hard negatives and explicit assumptions; actual compilation; distinguish prepared/admitted/runtime/deployed evidence. |

## Integration checks

1. Review T3's payload with T2 before edits to shared transport/schema files.
2. Review T4 candidate relations with T5 cache identity; neither relaxes verified
   status, proof-method constraints, PFR-011 compilation, or catalog admission.
3. Reproduce a geometry request including a figure through the actual chat,
   stored request, formal proof, explanation, diagram, and reload.
4. Reproduce an undergraduate commutative-diagram problem with checked
   commutativity, rather than treating a rendered graph as a proof.
5. Confirm renamed-variable retrieval, reject a superficially similar false
   match, and prove a valid specialization through the required new-Lean path.
6. Inspect all child PRs and pinned revisions before proposing parent integration.
   Report local/CI, real DB/provider, runtime, and deployed evidence separately.

No fixed speedup or broad mathematical success rate is promised before baseline
measurements. No task may use mocked/fixed successful responses as completion.
