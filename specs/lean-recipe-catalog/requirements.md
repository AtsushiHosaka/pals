# Lean Recipe Catalog Requirements

## Overview

Lean Recipe Catalog は、数学的な主張・方針・説明を保持する Draft Catalog とは独立に、
再利用可能な Lean 4/mathlib の証明本体を管理する。各 Recipe は実際にコンパイルした
証跡に束縛され、Draft と Recipe の対応は別の明示的な多対多 alignment として管理する。自然言語の証明要求は、検索用の命題説明とレビュー済み回答を持つ Recipe を最初に検索する。この検索と再利用に Draft や alignment は要らない。

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
- 既存 v1 の形式目標 selector を意味同値の判定器に変えること。
- Recipe template の自動展開や本番公開を、この変更だけで提供すること。

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
| LRC-006 | The existing formal proof-job catalog selector shall select a Recipe only through one of two v1 modes: (a) a formal-target mode whose extracted target exactly equals the Recipe target and whose active toolchain fingerprint exactly equals the Recipe fingerprint; or (b) an aligned-Draft mode whose immutable DraftRevisionReference exactly equals an admitted exact-target alignment. If a Draft is supplied together with a formal target, both mode checks and the alignment's method tag shall match by exact UTF-8 equality, including `null` matching only `null`. A missing target and missing Draft reference select no Recipe. |
| LRC-007 | `pals-api` shall return a `RecipeSelection` DTO only from `POST /v1/internal/lean-recipe-catalog/selections`, over HTTPS using the dedicated `X-PALS-Recipe-Worker-Secret` and a request nonce. The request/result schemas, exact RFC 8785 preimages, HMAC input, bounds, and status/error mapping are defined in the design and are closed: unknown, absent, or duplicate members are invalid; the service emits RFC 8785 bytes and the agent recomputes the defined canonical preimages before authenticating them. The agent shall reject missing, replayed, oversized, malformed, or MAC/digest-mismatched DTOs. The agent shall retain every locally issued nonce for the full ten-minute receipt-admission window and fail closed if its nonce store cannot do so; it shall not evict a still-valid nonce by capacity. A selected DTO contains the exact materialized source bytes, source digest, Recipe revision, optional alignment revision, target digest, toolchain fingerprint, `source_author_principal`, `selection_payload_sha256`, and an immutable `selection_receipt_sha256` issued under LRC-013. The agent shall forward these selected binding fields byte-for-byte to the v2 candidate contract, submit the source bytes unchanged to the normal verifier, and preserve them as a discriminated `recipe` attempt source with no LLM provenance fields. A selected Recipe verifier failure is terminal for that attempt and shall not invoke LLM generation or repair. |
| LRC-008 | If no Recipe is eligible, or any lifecycle, Draft-reference, target, method, source, receipt, toolchain, or DTO digest check fails, the system shall exclude that Recipe and record a closed v1 reason code. It shall not substitute another Recipe, alter a Draft, or claim that Recipe-backed generation occurred. Existing non-Recipe generation may begin only as a separate no-Recipe attempt. |
| LRC-009 | The system shall record, per proof attempt, the formal-target source if any, DraftRevisionReference if any, all considered Recipe revisions, selection or exclusion reasons, selected alignment revision if any, materialized source digest, toolchain fingerprint, attempt source kind, verifier outcome, and the exact source sent to independent proof review. |
| LRC-010 | The existing v1 formal proof-job lookup shall use exact target digest and/or exact DraftRevisionReference keys; it shall not require an embedding provider. The catalog service shall obtain its active toolchain fingerprint from the verifier configuration, Lean version, and pinned Mathlib lock identity. If that fingerprint cannot be produced or exactly matched, the service shall select no Recipe. Multiple otherwise eligible Recipes shall result in `ambiguous_recipe` and no selection. |
| LRC-011 | The initial catalog shall include a compiler-checked exact-target Recipe for the explicit ε–δ proof that `fun x : ℝ => x ^ 2` is continuous, aligned to the existing mathematical Draft only through a separate alignment record. Its proof body shall explicitly bind the chosen `δ`; it shall not use the shortcut `continuous_id.pow`. |
| LRC-012 | The system shall evaluate the Recipe path with a versioned corpus containing an exact formal-target match, an aligned-Draft match, a Draft-only/no-Recipe case, an incompatible-toolchain case, an alignment-mismatch case, an ambiguous-candidate case, and a no-Recipe case. Every fixture shall declare its expected selection, rejection codes, verifier result, and proof-method tag. The result shall report compile rate, correct-selection rate, false-selection rate, and proof-method fidelity from those expected outcomes without replacing the existing Draft/PFI corpus. |
| LRC-013 | When the selection service returns `selected`, it shall atomically create an immutable selection receipt keyed by `selection_receipt_sha256`. The receipt shall bind the exact receipt preimage defined in the design: request digest, `selection_payload_sha256`, Recipe and optional alignment revisions, exact materialized-source/target/toolchain/compiler-receipt digests, `source_author_principal`, issuance time, and a submission expiry no later than ten minutes after issuance. `source_author_principal` is an opaque identifier in the versioned `pals.principal.v1/` namespace and is compared by exact UTF-8 byte equality. `selection_payload_sha256` is the digest of the exact canonical selected-DTO preimage defined in the design, so its construction cannot be circular. Only API-owned catalog readers may resolve the receipt. The receipt is usable for new proof-candidate admission only before expiry, while its Recipe/alignment remain admitted, and while its toolchain fingerprint remains active; the authoritative lifecycle/toolchain check and candidate insertion shall serialize as one transaction. The receipt is retained read-only after expiry for audit and historical proof review. |
| LRC-014 | For the natural learner proof-request catalog-reuse path ([PFR-010](../proof-request-reuse/requirements.md)), the API may return an admitted Recipe source and stored independently reviewed answer without compilation or generation only when the immutable admission compiler receipt binds the same source and exact active toolchain, its admitted reuse entry is source/answer/review bound, and independent request correspondence/QA passes. Draft and alignment are not prerequisites. The existing formal proof-job Recipe attempt path (LRC-006–LRC-009) keeps its compile requirement. |

| LRC-015 | Add immutable, API-owned Recipe reuse entries containing a mathematical search description and reviewed natural-language answer bound to one admitted Recipe revision, materialized source digest and target digest. The description records statement, domain/objects, assumptions, quantifiers, conclusion and proof method independently of Draft. Store output language, exact answer SHA-256 and independent admission-review evidence binding description, target, source and answer. Description/answer changes create a new entry revision; neither runtime worker nor agent can publish or edit one. |
| LRC-016 | Add dedicated worker-authenticated, bounded direct Recipe candidate retrieval for natural proof requests. It reads only admitted reuse entries and Recipe evidence, filters active toolchain, validates every immutable binding, returns at most eight candidates and records deterministic retrieval evidence. It must not query Drafts or require alignment or a generated formal target. Similarity/keyword/description matching is candidate ranking only. A valid empty catalog returns a search miss; missing configuration, invalid receipts and database/provider failures are unavailable/integrity outcomes, never fabricated empty catalogs. |
| LRC-017 | Reuse-entry admission requires an admitted compiler-checked Recipe, a closed bounded description/answer payload, scalar Unicode, exact source/target binding and independent source-grounded description/answer review. A reviewer principal differs from the Recipe source author. The answer must faithfully explain the compiled statement and recorded method. Admission adds no learner question, conversation, owner, account or Project data. Registration of reuse metadata does not require a Draft schema migration, alignment admission or runtime recompile. |
| LRC-018 | Natural-request correspondence uses the entry's complete mathematical description and actual Lean source, plus independent separate-session review against the exact learner request and confirmed assumptions. Binder renaming/wording differences may be accepted; implication, specialization, missing assumptions, domain/type changes, dependent quantifier changes and method mismatch cannot be accepted as identical. The old v1 target digest only normalizes whitespace and is not natural-request equality evidence. Stored answer bytes and language must be directly usable; unknown correspondence or adaptation needed uses new Lean and compilation. |
| LRC-019 | DSP の検証済み Lean source を Recipe に登録するときは、その UTF-8 バイト列を変更せず、実際の隔離された admission verifier で検証する。既存の v1 materializer が再現できない named theorem は、別の raw-source authoring policy と不変の manifest・コンパイル証拠で登録する。未対応の環境や宣言は候補として保留し、コードの書き換えで登録条件を満たしたことにしない。未承認の raw source は従来の selector に選ばせず、独立レビューと公開の全段階が完了するまで直接検索にも出さない。 |
| LRC-020 | Semantic natural-request reuse shall not stop at a fixed small catalog size. The API shall narrow each eligible request to a retrieved window of at most five entries before the two model judges, so judge calls, prompt size and API response size stay flat as the catalog grows. A safety bound of 4,096 selectable entries per language and toolchain returns an explicit `catalog_limit` refusal and the ordinary non-reuse route, never a prefix of the catalog. |
| LRC-021 | The API shall rank its own frozen request statement; a worker supplies no query text and no limit. Only the shown entries are fetched and fully revalidated (signature, source, target, compiler receipt, toolchain). The server-side receipt binds the ordered window pins, the catalog count, the digest of the sorted catalog pins, the retrieval profile and the window digest, and settlement accepts only an entry inside that exact window. Ranking and scores are never correspondence evidence, and scores are not persisted. |
| LRC-022 | Ranking shall use exact cosine distance over versioned query vectors when the worker supplies a query vector under the exact binding and every selectable entry has a vector under that binding. Otherwise it shall use deterministic local character n-gram ranking and record that profile. A provider failure, missing storage or partial coverage changes only ranking quality; none of them may fail the request, widen a judge gate or claim reuse. Vectors are bound to the embedded entry text by digest, immutable and written only by a release identity; a vector cannot make an entry selectable. |
| LRC-023 | A change to retrieval or window size shall report recall, false reuse and latency at about 32, 100 and 1,000 entries, using paraphrase positives and near-variant negatives (including a changed constant and one-sided versus two-sided) with real judges. False reuse shall not exceed the 32-entry result; any false reuse is a release blocker to be reported, not averaged away. |
| LRC-024 | The complete-snapshot route and its 32-entry bound remain only for workers released before the window. Historical snapshot receipts keep validating unchanged. |
| LRC-025 | A semantic judge shall not resolve an unstated scope in the candidate's favour. When a request leaves the number or dimension of its objects, its domain, or another scope-determining term open, and a candidate covers only some of the readings a learner could mean, the judge shall return `needs_input` or `miss`, not `reuse`. A request that states the candidate's scope stays reusable. |
| LRC-026 | A change to the judges or consensus shall be adopted only when measured with real judges. A rejected option stays unimplemented and is recorded with its result. A relaxed consensus rule shall keep both judges' approval of the same immutable Recipe and shall not accept opposite verdicts on the request. Readings either approving judge called relevant all apply. The second judge uses a different model from the first. |
| LRC-027 | The published catalog shall not grow past its current size until a run at about 1,000 entries shows no false reuse in near-variant negatives, in paraphrases with their correct card removed, or in wrong-card selection; repeated review of the recorded ambiguous case reuses the wrong card zero times; single-judge false approvals fall below the recorded values; and reuse of positives stays at or above the recorded 65.4%. The paid cost of the run is reported. |

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
- Direct natural-request reuse works with no alignment and with the Draft reader unavailable; source and stored reviewed answer are returned byte-for-byte without generator/verifier/Draft calls.
- Paraphrases and bound-variable names can differ, but negative domain/hypothesis/quantifier/conclusion/method fixtures never produce reuse. Answer/description/review tampering or stale lifecycle/toolchain cannot pass settlement revalidation.
- The evaluation corpus demonstrates no false Recipe selection in all negative fixtures and uses a
  real local PostgreSQL service plus the pinned Lean verifier.
- A question that leaves the number of terms open never reuses a card fixed to two terms, and the same question stating two terms can still reuse it.
- A catalog above 32 entries still reaches the two judges with at most five shown entries, and an
  entry outside the recorded window cannot settle. Deleting all query vectors or failing the provider
  still answers through the lexical profile with unchanged judge gates.

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
- The agent receives Recipe data only through authenticated, digest-bound private ports and never gets database credentials or direct database access. The old `RecipeSelection` DTO and new natural-request candidate contract serve distinct callers.
- Production publication, authorization, and cross-device sharing are deferred. The first schemas
  are isolated from `public.dsp_drafts` and existing typed-Draft schemas.

## Open questions

None for the approved local Recipe-first behavior. The bounded retrieval method is defined by LRC-020–LRC-022, must report its actual ranking evidence, and cannot certify equality. Template expansion and production publication remain outside this local slice.
