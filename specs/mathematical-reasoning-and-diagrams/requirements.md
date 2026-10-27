# Mathematical reasoning, diagrams, and theorem retrieval

Authority: user-directed working requirements, 2026-10-28 JST. The user confirmed
that the dictated terms mean elementary geometry, axioms, Lean, and commutative
diagrams. This scope authorizes implementation and review PRs. Existing
verification, feature-preservation, catalog-admission, and release boundaries
continue to apply. Repository visibility is not a security certificate.

| ID | Required behavior and acceptance condition |
| --- | --- |
| MRD-001 | The security review shall distinguish public repository exposure, secret-history coverage, application authorization, and untrusted computation. It shall record exact reviewed revisions and incomplete coverage. The parent and six current submodules are in scope; `pals-draft-admin` remains excluded. Missing history, source, or tools shall never produce a pass. |
| MRD-002 | Geometry requests shall retain the original problem and any supplied figure, explicit hypotheses, objects, constructions, and conclusion. An ambiguous image interpretation that changes the theorem shall require clarification. Drawing measurements shall never silently supply mathematical premises. |
| MRD-003 | Geometry proofs shall expose an ordered trace in which each step references an accepted theorem or declared foundational rule, its instantiated premises, and earlier dependencies. The active Lean verifier shall check the proof and the binding between the trace and its source. Unrestricted solver axioms, `sorryAx`, undeclared assumptions, and unverified numerical observations shall not establish verified status. |
| MRD-004 | Geometry figures shall render inside the chat answer and provide corresponding TikZ source. Given objects, derived constructions, labels, and display coordinates shall remain consistent with the mathematical object model. A verified proof and an illustrative figure shall have distinguishable evidence. Reload and existing source/explanation access shall remain usable. |
| MRD-005 | Commutative diagrams shall render inline with labeled objects, directed arrows, and mathematical labels, and provide TikZ/tikz-cd source. A drawing alone shall not certify commutativity; verified claims shall reference checked equalities of composites or the appropriate Lean structure. |
| MRD-006 | Retrieval shall recognize reviewed bound-variable renamings while preserving types, constants, scopes, repeated-variable identity, assumptions, quantifier dependencies, and requested methods. Typed structural matching shall distinguish an identical target from specialization, implication, and an inapplicable candidate. Search similarity shall never certify equivalence. |
| MRD-007 | Searchable theorem data shall retain immutable source and admission bindings, exact toolchain/dependency identities, and lifecycle eligibility. Draft content, Lean Recipes, matching metadata, and compiled-module artifacts shall retain their existing ownership and admission boundaries. Agent workers shall not acquire catalog database credentials. |
| MRD-008 | A changed source, wrapper, specialization, or substitution requiring a new proof shall follow the current new-Lean verification contract. Search improvements shall not silently relax PFR-010/011/016/017 or the legacy LRC exact-target selector. Any changed matching contract shall be versioned and reviewed with its affected specification. |
| MRD-009 | Acceleration shall report baseline and changed Recall@k, MRR, false acceptance, verified application rate, and stage-level cold/warm p50/p95 latency. It shall reject stale or untrusted compiled artifacts and preserve semantic review and verification guarantees. An unexecuted performance check shall remain unverified. |
| MRD-010 | TeX and diagram rendering shall use bounded, isolated execution with no shell escape or network access and controlled inputs, outputs, dependencies, and resource limits. Untrusted TikZ, SVG, file paths, imports, and external references shall not bypass this boundary. Render failure shall retain readable mathematical text and existing chat actions. |
| MRD-011 | Coverage shall expand toward third/fourth-year undergraduate mathematics and then difficult entrance-exam problems using high-school mathematics. Each reported supported family shall have explicit assumptions, a substantive proof, actual Lean evidence, and diagram evidence when relevant. Aggregate catalog counts and trivial identities shall not establish support. |
| MRD-012 | Each implementation chat shall belong to the existing PALS Codex project, declare its owned paths and dependencies, preserve peer changes and existing features, and provide a concrete tested change or an explicit blocker. Creating a chat or writing a specification shall not count as implemented or deployed behavior. |

The shared implementation design and verification tasks are in
[the roadmap directory](../../docs/mathematics-roadmap-2026-10-28/design.md).
