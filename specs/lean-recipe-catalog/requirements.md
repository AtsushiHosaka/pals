# Lean Recipe Catalog Requirements

## Overview

Lean Recipe Catalog は、数学的な主張・方針・説明を保持する Draft Catalog とは独立に、
再利用可能な Lean 4/mathlib の証明本体を管理する。各 Recipe は実際にコンパイルした
証跡に束縛され、Draft と Recipe の対応は別の明示的な多対多 alignment として管理する。

初回の対象は、agent が private catalog service を通じて利用するローカル開発用の catalog
である。既存の `verified` 判定、Draft の内容、PFI、既存 typed-Draft catalog、および
利用者向け API の公開契約は変更しない。

## Goals

- 数学的 Draft を Lean 固有の import、定理名、補題、構文、toolchain 制約から独立させる。
- 既知の形式的目標に対して、コンパイル済みの Recipe をそのまま使えるようにする。
- Recipe を使えない場合に、古い・別の型の・意味の違う Lean コードを混入させない。
- どの Draft、Recipe、alignment、toolchain、検証結果を使ったかを再現可能にする。

## Non-goals

- Draft に Lean source、Mathlib 定理名、import、または compiler 証跡を埋め込むこと。
- Recipe を生成モデルの出力だけで自動公開すること。
- v1 で変数置換、意味同値変形、一般化・特殊化を自動適用すること。
- generic Draft schema、PFI、既存 typed-Draft catalog、または利用者向け API の migration を
  変更すること。
- Recipe を使わない要求に対する既存の生成・検証の意味を変更すること。
- v1 で Recipe vector search、template、または本番公開を提供すること。

## User stories

- 証明生成者として、数学的な Draft を Lean に依存させずに追加したい。
- Lean author として、同じ形式的目標を解くコンパイル済みの証明本体を、数学的 Draft の
  編集を待たずに追加・改訂したい。
- 運用者として、出力がなぜその Lean source になったかを、選択された Recipe と compiler
  証跡まで追跡したい。

## Functional requirements

| ID | Requirement |
|---|---|
| LRC-001 | The system shall keep Draft records and Lean Recipe records in independent catalogs with independent identities, canonicalization, evidence, and publication lifecycles. A Draft record shall not require Lean code or Lean metadata to be admitted. `pals-api` shall own Recipe and alignment database reads and writes and expose selection only through its internal worker-authenticated endpoint; the agent process shall not own a Recipe database connection. The API shall use separate catalog-owner, selection-writer, and catalog-reader execution identities; neither the agent nor a generic-Draft identity shall receive catalog access. |
| LRC-002 | The system shall represent a Draft-to-Recipe relationship only as an explicit, immutable alignment revision. An alignment shall store an immutable `DraftRevisionReference` consisting of catalog ID, Draft ID, canonical Draft payload SHA-256, and canonicalizer version, plus the exact Recipe revision. v1 supports `pals.draft-candidate-result.v1` only: its payload is the RFC 8785 serialization of `{id, canonical_statement, openmath_xml, proof_strategy, sketch_steps}` after an API-owned `openmath-cdbase-alpha-c14n-v4` validator. Its immutable byte contract and compatibility vectors are `openmath-cdbase-alpha-c14n-v4-vectors.json`; the API and agent shall both verify that artifact before using v4. `pals-api` shall exact-fetch those five fields by Draft ID through a read-only PFI catalog-reader identity, revalidate and rehash them with v4 at alignment admission and selection, and never treat a PFI v3 digest as v4 evidence. This adds no generic-PFI schema or write migration. One Draft reference may link to zero or more Recipes, and one Recipe revision may link to zero or more Draft references. |
| LRC-003 | Each v1 Lean Recipe shall be an immutable exact-target proof body. It shall declare a canonical target proposition, required imports, namespace/open declarations, proof body, recipe kind, and pinned Lean/mathlib toolchain fingerprint. The only v1 canonical target extractor is the existing single top-level `theorem`, `lemma`, or `example` declaration extractor with its whitespace-normalized proposition bytes. The source declaration shall have no declaration parameters, universe parameters, or typeclass binders, and the extracted proposition shall be closed under the declared Recipe environment. v1 does not treat binder renaming or mathematical rewrites as equal. |
| LRC-004 | Before a Recipe revision becomes selectable, the catalog service shall accept only the closed, RFC 8785-canonical `RecipeAuthoringManifestV1` defined in the design. The release-only admission command shall use one versioned materializer to create its source from the declared environment, canonical target, and proof body, then compile those exact bytes through the versioned pinned isolated admission-verifier contract. The immutable revision shall bind its nonempty opaque `source_author_principal` in the `pals.principal.v1/` namespace, sealed author-profile, materialized source, canonical target, Recipe payload, compiler result, compiler receipt, and toolchain fingerprint by digest. The principal comes from the sealed authoring manifest and is propagated verbatim to all selection evidence; it is neither inferred from a worker request nor normalized by the catalog. |
| LRC-005 | Before an alignment becomes selectable, the catalog service shall admit only a closed, RFC 8785-canonical alignment authoring manifest. It shall bind the immutable DraftRevisionReference and Recipe revision, state `exact_target`, record any required proof-method tag, and record a closed independent semantic-review evidence object whose reviewer principal is a nonempty `pals.principal.v1/` identifier and differs from the exact Recipe `source_author_principal`. An alignment whose current Draft reference cannot be revalidated is ineligible. For both Recipe and alignment revisions, lifecycle sequence 1 shall be `admitted`; later events may be only `retired` or `rejected`; and no event may follow either terminal event. |
| LRC-006 | The catalog service shall select a Recipe only through one of two v1 modes: (a) a formal-target mode whose extracted target exactly equals the Recipe target and whose active toolchain fingerprint exactly equals the Recipe fingerprint; or (b) an aligned-Draft mode whose immutable DraftRevisionReference exactly equals an admitted exact-target alignment. If a Draft is supplied together with a formal target, both mode checks and the alignment's method tag shall match by exact UTF-8 equality, including `null` matching only `null`. A missing target and missing Draft reference select no Recipe. |
| LRC-007 | `pals-api` shall return a `RecipeSelection` DTO only from `POST /v1/internal/lean-recipe-catalog/selections`, over HTTPS using the dedicated `X-PALS-Recipe-Worker-Secret` and a request nonce. The request/result schemas, exact RFC 8785 preimages, HMAC input, bounds, and status/error mapping are defined in the design and are closed: unknown, absent, or duplicate members are invalid; the service emits RFC 8785 bytes and the agent recomputes the defined canonical preimages before authenticating them. The agent shall reject missing, replayed, oversized, malformed, or MAC/digest-mismatched DTOs. The agent shall retain every locally issued nonce for the full ten-minute receipt-admission window and fail closed if its nonce store cannot do so; it shall not evict a still-valid nonce by capacity. A selected DTO contains the exact materialized source bytes, source digest, Recipe revision, optional alignment revision, target digest, toolchain fingerprint, `source_author_principal`, `selection_payload_sha256`, and an immutable `selection_receipt_sha256` issued under LRC-013. The agent shall forward these selected binding fields byte-for-byte to the v2 candidate contract, submit the source bytes unchanged to the normal verifier, and preserve them as a discriminated `recipe` attempt source with no LLM provenance fields. A selected Recipe verifier failure is terminal for that attempt and shall not invoke LLM generation or repair. |
| LRC-008 | If no Recipe is eligible, or any lifecycle, Draft-reference, target, method, source, receipt, toolchain, or DTO digest check fails, the system shall exclude that Recipe and record a closed v1 reason code. It shall not substitute another Recipe, alter a Draft, or claim that Recipe-backed generation occurred. Existing non-Recipe generation may begin only as a separate no-Recipe attempt. |
| LRC-009 | The system shall record, per proof attempt, the formal-target source if any, DraftRevisionReference if any, all considered Recipe revisions, selection or exclusion reasons, selected alignment revision if any, materialized source digest, toolchain fingerprint, attempt source kind, verifier outcome, and the exact source sent to independent proof review. |
| LRC-010 | v1 Recipe lookup shall use exact target digest and/or exact DraftRevisionReference keys; it shall not require an embedding provider. The catalog service shall obtain its active toolchain fingerprint from the verifier configuration, Lean version, and pinned Mathlib lock identity. If that fingerprint cannot be produced or exactly matched, the service shall select no Recipe. Multiple otherwise eligible Recipes shall result in `ambiguous_recipe` and no selection. |
| LRC-011 | The initial catalog shall include a compiler-checked exact-target Recipe for the explicit ε–δ proof that `fun x : ℝ => x ^ 2` is continuous, aligned to the existing mathematical Draft only through a separate alignment record. Its proof body shall explicitly bind the chosen `δ`; it shall not use the shortcut `continuous_id.pow`. |
| LRC-012 | The system shall evaluate the Recipe path with a versioned corpus containing an exact formal-target match, an aligned-Draft match, a Draft-only/no-Recipe case, an incompatible-toolchain case, an alignment-mismatch case, an ambiguous-candidate case, and a no-Recipe case. Every fixture shall declare its expected selection, rejection codes, verifier result, and proof-method tag. The result shall report compile rate, correct-selection rate, false-selection rate, and proof-method fidelity from those expected outcomes without replacing the existing Draft/PFI corpus. |
| LRC-013 | When the selection service returns `selected`, it shall atomically create an immutable selection receipt keyed by `selection_receipt_sha256`. The receipt shall bind the exact receipt preimage defined in the design: request digest, `selection_payload_sha256`, Recipe and optional alignment revisions, exact materialized-source/target/toolchain/compiler-receipt digests, `source_author_principal`, issuance time, and a submission expiry no later than ten minutes after issuance. `source_author_principal` is an opaque identifier in the versioned `pals.principal.v1/` namespace and is compared by exact UTF-8 byte equality. `selection_payload_sha256` is the digest of the exact canonical selected-DTO preimage defined in the design, so its construction cannot be circular. Only API-owned catalog readers may resolve the receipt. The receipt is usable for new proof-candidate admission only before expiry, while its Recipe/alignment remain admitted, and while its toolchain fingerprint remains active; the authoritative lifecycle/toolchain check and candidate insertion shall serialize as one transaction. The receipt is retained read-only after expiry for audit and historical proof review. |
| LRC-014 | For the learner proof-request catalog-reuse path ([PFR-010](../proof-request-reuse/requirements.md)), the API may present an exact aligned Recipe as Lean-verified without recompiling, only when its immutable admission compiler receipt binds the same materialized source SHA-256 and the toolchain fingerprint of the currently active verifier, and the Recipe and alignment revisions are selectable. The proof-job Recipe attempt path (LRC-006–LRC-009) keeps its compile requirement. |

## Acceptance criteria

- A new Draft can be admitted with no Lean source or Lean-specific field, and a new Recipe can be
  admitted or revised without changing any Draft record.
- A Draft and a Recipe can each have multiple independent, immutable alignments; every selected
  alignment identifies the exact Draft payload digest and Recipe revision it joined.
- A PFI v3 payload digest is never accepted as an alignment's v4 Draft digest; the API re-fetches
  the exact five-field payload by ID and independently obtains the pinned v4 digest before
  admitting or selecting an alignment.
- Tampering with a selectable Recipe's source, target, import environment, compiler receipt, or
  toolchain binding makes it ineligible before a DTO is returned to the agent.
- A query whose formal target differs by an unapproved rewrite, whose Draft payload digest differs,
  or whose toolchain differs does not select a v1 Recipe.
- Two concurrently admitted Recipes eligible for the same exact key cause no selection with
  `ambiguous_recipe`; selection never depends on unspecified row or vector order.
- For the square-continuity fixture, the selected DTO's source equals its admission-evidence source
  byte-for-byte, has a local `δ` binding, compiles in the pinned workspace, and its provenance names
  both the `continuous_square` Draft alignment and the Recipe revision.
- A selected Recipe that fails current verification ends as `recipe_verification_failed` without an
  LLM model call or repair call in that attempt.
- Every selected DTO has a resolvable immutable selection receipt. A receipt that is expired,
  retired, altered, or otherwise no longer eligible cannot admit a new Recipe candidate, while its
  original sealed record remains available to authorized audit readers.
- A no-Recipe request leaves the existing generation and verifier path available as a separately
  traced no-Recipe attempt.
- The evaluation corpus demonstrates no false Recipe selection in all negative fixtures and uses a
  real local PostgreSQL service plus the pinned Lean verifier.

## Constraints and assumptions

- Recipe payloads, alignment payloads, compiler receipts, and lifecycle events are append-only.
  `admitted`, `retired`, and `rejected` are immutable lifecycle events, not mutable columns. A
  revision's current state is the highest valid event sequence; `retired` and `rejected` can never
  be followed by `admitted` for that same revision.
- `Mathlib` is the only v1 import root. Recipes may use an explicit namespace/open environment, but
  arbitrary process execution, external files, `sorry`, `admit`, `axiom`, `constant`, `opaque`,
  and `unsafe` are prohibited in selectable evidence.
- “Independent review” in LRC-005 means a reviewer whose exact versioned principal differs from
  the Recipe `source_author_principal`; it is admission evidence, not a replacement for the
  proof-attempt review required by `CORE-002`. Method tags are lower-snake-case identifiers and
  use exact equality; `null` is an explicit no-method value, not a wildcard.
- The agent receives only the authenticated, HMAC/digest-bound `RecipeSelection` DTO through a
  private port and never gets database credentials or direct database access.
- Production publication, authorization, and cross-device sharing are deferred. The first schemas
  are isolated from `public.dsp_drafts` and existing typed-Draft schemas.

## Open questions

None for the initial exact-target local slice. Template parameters, vector retrieval, and production
publication are explicitly deferred non-goals rather than unresolved v1 behavior.
