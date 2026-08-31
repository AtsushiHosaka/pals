# Lean Recipe Catalog Design

## Scope and traceability

This design implements `LRC-001`–`LRC-013`. It adds a `pals-api` internal-only catalog service
backed by isolated local PostgreSQL schemas. `pals-agent` calls that service through a private
RecipeSelection port; it does not connect to the database. The public API, generic Draft tables,
PFI, and typed-Draft catalog are unchanged.

## Architecture

```mermaid
flowchart LR
  Q["Proof request"]
  DR["Draft resolver"]
  A["Private catalog service\nRecipe + alignment schemas"]
  P["Agent planner"]
  V["Normal isolated Lean verifier"]
  T["Attempt provenance"]

  Q --> DR
  Q --> A
  DR -->|"DraftRevisionReference"| A
  A -->|"RecipeSelection or exclusion reasons"| P
  Q --> P
  P --> V
  P --> T
  V --> T
```

Draft resolution and Recipe selection are separate operations. An alignment is an admissibility
constraint and provenance edge, not a shared mutable field. The service is `pals-api`, which owns a
dedicated internal request/response contract and no agent-side database driver.

## Private contracts

### DraftRevisionReference

The Draft resolver returns the following immutable value for every Draft it offers to Recipe
selection:

```text
catalog_id, draft_id, draft_payload_sha256, canonicalizer_version
```

v1 fixes `catalog_id` to `pals.draft-candidate-result.v1` and `canonicalizer_version` to
`openmath-cdbase-alpha-c14n-v4`. `draft_payload_sha256` is SHA-256 over RFC 8785 bytes of exactly the closed
object `{id, canonical_statement, openmath_xml, proof_strategy, sketch_steps}`, after an
API-owned v4 OpenMath validator has accepted `openmath_xml`. It is not a database row version.

`pals-api` owns `PFIDraftCatalogReaderV1` and an independently packaged v4 canonicalizer. The
reader takes exactly one Draft ID and, under `REPEATABLE READ` with `SET LOCAL ROLE
`pals_draft_reader`, returns only `{id, canonical_statement, openmath_xml, proof_strategy,
sketch_steps}` from the current generic PFI catalog. It has no Draft write grant and no Recipe
catalog grant. The API v4 canonicalizer has byte-equality compatibility vectors with the agent v4
implementation but does not import the agent at runtime. It validates the retrieved `openmath_xml`,
replaces that one field with its v4 canonical XML bytes, then RFC 8785-serializes the five-field
object. PFI's existing v3 publication or digest does not establish v4 validity. At alignment
admission and at aligned-Draft selection, the API repeats those steps and compares the result's
SHA-256 with `draft_payload_sha256`; absence, invalid XML, or inequality returns
`draft_revision_mismatch`. This reader/canonicalizer boundary does not migrate generic PFI tables,
PFI publication, or existing Draft rows. A resolver that cannot produce the v4 value does not
supply a Draft reference for Recipe selection.

The normative v4 byte contract is the closed artifact
`openmath-cdbase-alpha-c14n-v4-vectors.json` beside this design. Its pinned reference source defines
all-input behavior; its vectors cover namespace/attribute/whitespace normalization, nested shadowed
binders, entity/CDATA parsing, and invalid-profile rejection, and fix the corresponding canonical
UTF-8 XML, five-field RFC 8785 preimages, and SHA-256 values. API and agent implementations must
verify every vector before a v4 result is usable; any mismatch makes aligned-Draft admission and
selection unavailable. A new canonicalizer version and a new vector artifact are required for any
later byte-level change.

### RecipeSelection port

The agent calls `POST /v1/internal/lean-recipe-catalog/selections` exactly once. It sends
`Content-Type: application/json`, `Accept: application/json`, and the dedicated
`X-PALS-Recipe-Worker-Secret`; the body is the RFC 8785 UTF-8 serialization of exactly:

```json
{
  "schema_version": "pals.recipe-selection-query.v1",
  "request_nonce": "<64 lowercase hex characters>",
  "formal_target": {"target_source": "...", "target_sha256": "..."} | null,
  "draft_revision": {
    "catalog_id": "pals.draft-candidate-result.v1",
    "draft_id": "...",
    "draft_payload_sha256": "...",
    "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4"
  } | null,
  "proof_method_tag": "..." | null,
  "toolchain_fingerprint": {
    "schema_version": "pals.lean-toolchain-fingerprint.v1",
    "lean_version": "...",
    "lake_manifest_sha256": "...",
    "verifier_sha256": "...",
    "materializer_version": "..."
  }
}
```

`request_sha256` is SHA-256 of those exact bytes. `formal_target`, when present, is produced only
by `ClosedRecipeHeaderV1`; `target_sha256` is SHA-256 of its UTF-8 `target_source`. All SHA-256
values are 64 lowercase hexadecimal ASCII characters. All objects are closed and all JSON strings are
valid UTF-8. Recipe/alignment IDs are catalog identifiers matching
`[a-z0-9][a-z0-9._-]{0,127}`; `draft_id`, method tags, and reason codes are lower snake-case
identifiers of at most 128 ASCII characters. All omitted optional values are emitted as JSON
`null`, never omitted. The request is at most 32 KiB, source text at most 480,000 code points, other
text at most 20,000 code points, and the response at most 512 KiB. HTTPS and a ten-second deadline
are mandatory.

For an aligned-Draft request, `proof_method_tag` and
`required_proof_method_tag` are compared by exact UTF-8 equality after closed-schema validation;
`null` equals only `null` and is never a wildcard. A formal-target-only request has no alignment
method-tag comparison.

The successful response body is RFC 8785 UTF-8 bytes for exactly:

```json
{
  "schema_version": "pals.recipe-selection-result.v1",
  "status": "selected" | "not_selected",
  "request_nonce": "...",
  "request_sha256": "...",
  "response_mac_sha256": "...",
  "selection": "<selected-object>" | null,
  "exclusions": ["<exclusion>", "..."] | null
}
```

For `selected`, `exclusions` is `null` and `selection` is exactly the closed object
`{recipe_id, recipe_revision, alignment_id, alignment_revision, target_sha256,
materialized_source, materialized_source_sha256, toolchain_fingerprint,
toolchain_fingerprint_sha256, compiler_receipt_sha256, source_author_principal,
selection_payload_sha256, selection_receipt_sha256}`. Alignment ID and revision are both non-null
or both null. The `selection_payload_sha256` preimage is the RFC 8785 serialization of that object
with exactly `selection_payload_sha256` and `selection_receipt_sha256` omitted. For
`not_selected`, `selection` is `null`; `exclusions` is a nonempty, duplicate-free list of at most
64 closed `{reason_code, recipe_id, recipe_revision}` objects, with both identity fields null or
both non-null. The v1 reason-code registry is
`formal_target_and_draft_unavailable`, `formal_target_unavailable`,
`draft_revision_mismatch`, `alignment_unavailable`, `method_tag_mismatch`,
`recipe_target_mismatch`, `toolchain_mismatch`, `recipe_lifecycle_ineligible`,
`alignment_lifecycle_ineligible`, `recipe_evidence_mismatch`, and `ambiguous_recipe`.

The response echoes the request nonce and digest. Its `response_mac_sha256` is HMAC-SHA-256 with
the dedicated secret over the ASCII bytes of `request_sha256` concatenated with the RFC 8785 bytes
of the response object with only `response_mac_sha256` omitted. The agent performs a constant-time
MAC comparison, validates the closed schema and every digest, and rejects a duplicate nonce. It
retains every issued nonce for ten minutes using expiry-based cleanup and fails closed rather than
capacity-evicting a live nonce. The service returns `401 recipe_worker_secret_invalid` for a
missing or wrong secret, `503 recipe_worker_secret_not_configured` when the dedicated secret is
absent, and `400 recipe_selection_request_invalid` for malformed, noncanonical, or oversized input;
the agent treats every non-200 response, transport failure, authentication, schema, size, nonce,
MAC, or digest failure as `recipe_selection_unavailable`. It never constructs or rewrites Recipe
source.

## Data model and lifecycle

The first implementation uses two isolated local PostgreSQL schemas:

| Schema | Records | Purpose |
|---|---|---|
| `pals_local_lean_recipe_catalog` | `profiles`, `toolchains`, `recipes`, `recipe_revisions`, `recipe_evidence`, `recipe_revision_status_events`, `selection_receipts` | Store Lean knowledge and append-only compiler/lifecycle evidence, plus selection-admission receipts. |
| `pals_local_draft_recipe_alignment` | `alignment_revisions`, `alignment_reviews`, `alignment_status_events`, `attempt_recipe_trace` | Store immutable Draft/Recipe relationships, review events, lifecycle, and runtime provenance. |

`recipe_revisions` owns immutable `recipe_id`, `revision`, `kind`, `target_source`,
`target_c14n_sha256`, `imports`, `environment`, `proof_body`, `proof_body_sha256`, `toolchain_id`,
and the sealed `source_author_principal`. `recipe_evidence` owns the exact source bytes, source
digest, compiler command/result digest, and toolchain fingerprint. `alignment_revisions` owns the
full DraftRevisionReference, exact Recipe revision, relation (`exact_target` only), method tag, and
review evidence digest. `alignment_reviews` owns the sealed canonical review object and its reviewer
principal; admission rejects a principal that exactly equals the bound Recipe source-author
principal. Recipe logical identity/revision and immutable payload/evidence digests are
unique; target digest is deliberately not unique, because independent admitted Recipes with the
same target must reach `ambiguous_recipe` at selection.

`recipe_revision_status_events` and `alignment_status_events` own subject identity, monotonically
increasing event sequence, event (`admitted`, `retired`, `rejected`), actor, timestamp, reason, and
evidence digest. Sequence 1 is exactly `admitted`; later events are only `retired` or `rejected`;
and no event can follow either terminal event. They reject duplicate sequences and invalid
transitions. The selection view uses the maximal valid event. All payload/evidence/event tables
reject `UPDATE` and `DELETE`.

`selection_receipts` is an append-only API-owned catalog table keyed by
`selection_receipt_sha256`, the SHA-256 of its RFC 8785 canonical receipt payload. That exact
closed receipt object is `{schema_version: "pals.recipe-selection-receipt.v1", request_sha256,
selection_payload_sha256, recipe_id, recipe_revision, alignment_id, alignment_revision,
materialized_source_sha256, target_sha256, toolchain_fingerprint_sha256,
compiler_receipt_sha256, source_author_principal, issued_at, submission_expires_at}`. Its nullable
alignment fields follow the selected-object rule, timestamps are RFC 3339 UTC strings, and
`submission_expires_at` is no later than ten minutes after `issued_at`.
`source_author_principal` is a nonempty opaque UTF-8 identifier with the exact prefix
`pals.principal.v1/`; the catalog neither derives nor normalizes it.
`selection_payload_sha256` is SHA-256 over the RFC 8785 selected-DTO preimage before adding
`selection_receipt_sha256` or its MAC; therefore neither receipt digest depends on itself. The
selection transaction creates it only after all eligibility checks have passed and returns its key
and preimage digest in the signed selected DTO. `pals_api_recipe_catalog_owner` is release-only and
owns schemas, tables, triggers, and lifecycle functions. A deployment-provisioned release login is
`NOINHERIT` and may be a direct member of both this owner role and `pals_draft_reader`; it activates
exactly one role per transaction. Its reader transaction is `REPEATABLE READ READ ONLY` and has no
Recipe-catalog grants; its separate owner transaction has no generic-PFI table grant. The normal API
and every non-release login are members of neither release role. `pals_api_recipe_catalog_selector` may
read the selection views, insert selection receipts, and execute only the lifecycle-lock function.
`pals_api_recipe_catalog_reader` may read receipts/current lifecycle views and execute that same
function, but cannot create, modify, or delete catalog rows. The lifecycle-lock function is owned by
the owner, has a fixed `search_path`, rejects invalid revision identities, and acquires the same
transaction-scoped advisory locks for selection, candidate admission, and retirement before it reads
current state. `PUBLIC` has no grants on either schema or function; the agent and generic Draft
roles have none. The configured expiry applies only to new candidate admission. The record is
retained read-only after expiry for audit and review of an already persisted proof attempt.

Candidate admission resolves a receipt under the same transaction that inserts the proof candidate.
It invokes the lifecycle-lock function for the selected Recipe/alignment, compares its toolchain
digest with the active verifier fingerprint, and serializes against retirement. Consequently, a
concurrent retirement is ordered either before admission (the receipt is rejected as `retired`) or
after its immutable historical candidate has been persisted; no check-then-insert gap is permitted.

## Target extraction, materialization, and toolchain attestation

The v1 target extractor is `extract_single_target_declaration` plus `ClosedRecipeHeaderV1`. It
accepts exactly one top-level `theorem`, `lemma`, or `example` declaration with no declaration
parameters, universe parameters, or typeclass binders. The closed proposition can still quantify its
own variables. It uses the extractor's existing whitespace-normalized proposition as
`target_source`, then the materializer must compile that target under the declared Recipe
environment. It performs no alpha normalization, rewrite, inferred implicit-argument normalization,
or semantic equivalence check. Header validation or extraction failure yields
`formal_target_unavailable`.

`RecipeMaterializerV1` is a deterministic pure function of `imports`, `environment`,
`target_source`, and `proof_body`. It always produces:

```lean
import Mathlib
<declared namespace/open environment>

example : <target_source> := <proof_body>
```

The materialized bytes and SHA-256 are the only Recipe source. Admission compiles those bytes.
Runtime sends the same stored bytes to the normal verifier; it never substitutes a user declaration
name or raw harness. For a formal request, the pipeline separately compares the extracted request
target digest with the Recipe target digest. A Recipe source bypasses the LLM-only raw-harness
substring preflight after that equality check, while the existing semantic review receives the
materialized bytes and its digest. Thus the compile receipt, displayed verified source, and semantic
review candidate are identical bytes.

`ToolchainFingerprintV1` has exact fields for Lean version, `lake-manifest` SHA-256, verifier image
or executable/configuration SHA-256, and materializer version. The catalog service obtains it from
the active verifier configuration before selection. Missing or different fields make every Recipe
ineligible.

## Admission flow

### RecipeAuthoringManifestV1 and materializer

Admission is a local release operation, never an HTTP endpoint. The release runner alone receives
the `pals_api_recipe_catalog_owner` credential and invokes `lean-recipe-catalog-admit` with one
manifest file. The normal API, selector, reader, agent, generic-Draft roles, and all worker
requests have no permission to call that command or insert a Recipe payload. The command starts one
owner transaction after compiler success; it never grants the owner role to a runtime process. An
alignment release invocation additionally uses the same deployment-provisioned, `NOINHERIT` release
login's `pals_draft_reader` membership only for its separate read-only PFI revalidation transaction;
it then activates the owner role for the catalog-write transaction. No runtime process receives that
combined release login.

The file bytes must be RFC 8785 UTF-8 serialization of one closed object with this exact schema:

```json
{
  "schema_version": "pals.recipe-authoring-manifest.v1",
  "recipe_id": "lower_snake_or_dot_identifier",
  "revision": 1,
  "kind": "exact_target_proof",
  "source_author_principal": "pals.principal.v1/...",
  "author_profile": {
    "schema_version": "pals.recipe-author-profile.v1",
    "source_author_principal": "pals.principal.v1/..."
  },
  "toolchain": {
    "toolchain_id": "lower_snake_or_dot_identifier",
    "fingerprint": {
      "schema_version": "pals.lean-toolchain-fingerprint.v1",
      "lean_version": "...",
      "lake_manifest_sha256": "64 lowercase hex",
      "verifier_sha256": "64 lowercase hex",
      "materializer_version": "pals.recipe-materializer.v1"
    }
  },
  "imports": ["Mathlib"],
  "environment": {"namespace": null, "opens": []},
  "target_source": "closed Lean proposition",
  "proof_body": "by ..."
}
```

Unknown, absent, duplicate, or noncanonical members are rejected. `recipe_id`, `toolchain_id`, and
`revision` use the v1 identifier/integer bounds already defined for catalog rows. The profile
principal equals `source_author_principal` by exact UTF-8 byte equality; the profile payload is the
RFC 8785 object shown above and `profile_payload_sha256` is its SHA-256. `imports` is exactly the
one-element array shown and `environment` is exactly the object shown; namespace/open declarations
are deferred to a new materializer version. `target_source` and `proof_body` are nonempty UTF-8;
`proof_body` begins with `by`; and all existing forbidden-source rules apply to both materialized
bytes and the declared proof body.

`RecipeMaterializerV1` is the complete byte function below, including its final newline. It has no
filesystem, process, network, timestamp, declaration-name, or ambient configuration input:

```text
import Mathlib

example : <target_source> := <proof_body>\n
```

The command runs `ClosedRecipeHeaderV1` / `extract_single_target_declaration` on those materialized
bytes. It accepts only a closed `example` and only when the extracted whitespace-normalized
proposition equals the manifest `target_source` byte-for-byte. This is the only v1 target extractor;
no binder renaming, normalization, or rewrite is applied. `materialized_source_sha256` and
`target_c14n_sha256` are SHA-256 over the exact UTF-8 materialized bytes and target bytes.

`toolchain_fingerprint_sha256` is SHA-256 over RFC 8785 `toolchain.fingerprint`. The release command
computes `proof_body_sha256`, then computes `recipe_payload_sha256` over RFC 8785 bytes of exactly
`{schema_version:"pals.recipe-payload.v1",recipe_id,revision,kind,target_source,target_c14n_sha256,
imports,environment,proof_body,proof_body_sha256,toolchain_id,toolchain_fingerprint_sha256,
source_author_principal,profile_payload_sha256}`. The manifest content address is SHA-256 over its
full canonical file bytes; it is audit input, not a self-referential member. The initial lifecycle
event is the RFC 8785 object `{schema_version:"pals.recipe-admission-event.v1",
actor_principal:"pals.principal.v1/release/lean-recipe-catalog-admit",event_sequence:1,
event:"admitted",reason:null,manifest_sha256,recipe_payload_sha256,materialized_source_sha256,
toolchain_fingerprint_sha256,compiler_receipt_sha256}`. Its SHA-256 is the immutable
`evidence_sha256`; its actor is the fixed release-admission principal, not the source author.
`occurred_at` is database `statement_timestamp()` commit metadata and is outside that preimage.
Before calling the verifier, the release command checks for an existing `(recipe_id, revision)`: an
exact byte/digest match of the profile, toolchain, Recipe payload, evidence, and this sequence-1
event whose current lifecycle is still `admitted` returns `admitted_existing` without recompiling.
A terminal revision returns `recipe_revision_terminal` without a compiler call or mutation, and any
absent or unequal bound value rejects the replay before a compiler call or insert.

### RecipeAdmissionVerifierV1

The isolated verifier owner exposes a separate private, versioned admission contract; it does not
reuse the proof-job/artifact request. Its request is the closed RFC 8785 object
`{schema_version:"pals.recipe-admission-verifier-request.v1",admission_id,materialized_source,
materialized_source_sha256,expected_toolchain_fingerprint,
expected_toolchain_fingerprint_sha256}`. `admission_id` is a UUID generated by the release command.
The verifier recomputes the source and expected-fingerprint digests before compiling. A successful
response is the closed RFC 8785 object
`{schema_version:"pals.recipe-admission-verifier-result.v1",status:"verified",admission_id,
materialized_source_sha256,toolchain_fingerprint,toolchain_fingerprint_sha256,
compiler_command_sha256,compiler_result}`. `admission_id` is transport correlation only and is not
part of an immutable digest. Its `compiler_receipt_sha256` is SHA-256 over RFC 8785 bytes of exactly
`{schema_version:"pals.recipe-admission-compiler-receipt.v1",materialized_source_sha256,
toolchain_fingerprint_sha256,compiler_command_sha256,compiler_result}`. The verifier returns a
distinct closed failure object containing only schema version, `status:
"failed"`, admission ID, a closed failure code, and retryability; no failed compilation is admitted.
It uses the same private mTLS release binding, timeout, response framing, and readiness checks as the
existing verifier, but has no proof-job ID or artifact URI semantics. The API verifies that all
returned IDs, bytes/digests, fingerprint, and receipt preimage equal its inputs before any database
transaction. A missing, malformed, mismatched, or retryable response leaves no catalog row.

1. An author writes the sealed `RecipeAuthoringManifestV1` with a new logical revision.
2. The release-only command validates canonical file bytes, source/environment restrictions, target
   extraction, every declared and computed digest, and the ToolchainFingerprintV1.
3. It materializes and compiles those exact bytes through `RecipeAdmissionVerifierV1`.
4. After the verified response, one owner transaction inserts or exactly revalidates the immutable
   profile, toolchain, Recipe, revision, evidence, and initial `admitted` status event. Any failure
   rolls back all of them. Independent re-materialization before commit must equal the stored bytes.
5. A reviewer distinct from the bound source author submits a separately sealed alignment. The
   service revalidates both referenced payloads, checks `exact_target`, and inserts the alignment,
   review, and status event atomically.

### AlignmentAuthoringManifestV1

Alignment admission is a local release operation, never a worker or public HTTP endpoint. The
release runner invokes `lean-recipe-alignment-admit` with one RFC 8785-canonical closed object:

```json
{
  "schema_version": "pals.alignment-authoring-manifest.v1",
  "alignment_id": "lower_snake_or_dot_identifier",
  "revision": 1,
  "draft_revision": {
    "catalog_id": "pals.draft-candidate-result.v1",
    "draft_id": "...",
    "draft_payload_sha256": "64 lowercase hex",
    "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4"
  },
  "recipe_id": "lower_snake_or_dot_identifier",
  "recipe_revision": 1,
  "relation": "exact_target",
  "required_proof_method_tag": "lower_snake_case" | null,
  "review": {
    "schema_version": "pals.alignment-semantic-review.v1",
    "reviewer_principal": "pals.principal.v1/...",
    "verdict": "exact_target_agrees"
  }
}
```

Unknown, absent, duplicate, and noncanonical members are rejected. The release command locks the
exact Recipe revision, requires its current state to be `admitted`, and exact-fetches/revalidates
the Draft payload through `PFIDraftCatalogReaderV1` before inserting. It rejects any reviewer
principal that byte-equals the Recipe revision's `source_author_principal`. The alignment payload
preimage is RFC 8785 bytes of exactly
`{schema_version:"pals.alignment-payload.v1",alignment_id,revision,draft_revision,recipe_id,
recipe_revision,relation,required_proof_method_tag}`. The review-evidence preimage is RFC 8785
bytes of exactly `{schema_version:"pals.alignment-semantic-review.v1",reviewer_principal,
draft_revision,recipe_id,recipe_revision,relation,required_proof_method_tag,
verdict:"exact_target_agrees"}`. Their SHA-256 values bind the immutable alignment revision and
review row respectively.

The sequence-one evidence preimage is `{schema_version:"pals.alignment-admission-event.v1",
actor_principal:"pals.principal.v1/release/lean-recipe-alignment-admit",event_sequence:1,
event:"admitted",reason:null,manifest_sha256,alignment_payload_sha256,review_evidence_sha256}`.
Under the shared lifecycle lock, an exact byte/digest replay with an admitted Recipe and a current
matching v4 Draft returns `admitted_existing` without mutation. A terminal Recipe or alignment,
stale/invalid Draft, non-identical replay, or any changed bound value rejects without mutation.
The owner transaction inserts the alignment revision, review, and sequence-one event atomically;
retirement serializes through the same lifecycle lock.

Retirement is a separate event transaction. A verification failure observed at runtime creates a
`retired` event if the service can attest the event; the failing attempt remains historical and no
same-revision re-admission is possible.

## Runtime selection and attempt boundary

1. The planner obtains a target with the v1 extractor when the request contains a formal harness.
   Independently, an explicit Draft resolver may return a DraftRevisionReference.
2. The agent calls the RecipeSelection port. The service performs keyed lookup only: target digest
   for formal-target mode, or exact DraftRevisionReference for aligned-Draft mode.
3. A candidate is eligible only with admitted Recipe and alignment lifecycle state, a current
   matching v4 Draft payload when aligned-Draft mode is used, matching payload/evidence/DTO digests,
   exact active toolchain fingerprint, and the selection-mode checks in `LRC-006`. If both inputs
   are present, all checks apply, including exact method-tag equality. More than one eligible
   candidate returns `ambiguous_recipe`.
4. For `selected`, the service atomically stores the selection receipt and signs its digest in the
   DTO. The planner copies the selected binding fields, including `source_author_principal`,
   byte-for-byte into the v2 candidate request; it creates a `recipe` source attempt, sends returned
   source bytes unchanged to the normal verifier, then to the ordinary independent semantic-review
   path using the same bytes. It sets no model/raw-model-output fields and invokes no generator or
   repair loop.
5. Recipe verification failure is terminal as `recipe_verification_failed`; it may retire the
   revision but cannot fall through to LLM repair in that attempt.
6. For `not_selected`, the planner creates a separately traceable no-Recipe attempt and preserves
   the existing generation path. A rejected Recipe is never sent in a model prompt.

The planner and persisted proof candidate use `AttemptSource` as a discriminated union. Its
`recipe` variant has Recipe/alignment/DTO/source/toolchain/selection-receipt/author-principal fields and has no
`model`, `provider`, `raw_model_output`, or repair-route fields. Its `model` variant retains the
existing LLM provenance fields. `attempt_recipe_trace` records the full request selection input, all
candidate outcomes, chosen DTO digest, AttemptSource variant, exact bytes digest, verifier result,
and semantic-review source digest. It is append-only and can prove whether a source came from a
Recipe or a model.

## Failure handling

| Condition | Behavior |
|---|---|
| No formal target and no DraftRevisionReference | `not_selected(formal_target_and_draft_unavailable)`; start a separate no-Recipe attempt if generation proceeds. |
| Draft payload mismatch or no admitted alignment | `not_selected(draft_revision_mismatch or alignment_unavailable)`. |
| Target, method, evidence, DTO, or toolchain mismatch | Reject with the specific code; no downgrade. |
| Multiple eligible Recipes | `not_selected(ambiguous_recipe)`. |
| Selected Recipe fails verifier or semantic review | Terminal Recipe attempt; no LLM repair/fallback. |
| Duplicate immutable identity, payload/evidence digest, or event sequence at admission | Abort the transaction; require a new revision or explicit de-duplication. A duplicate exact target remains eligible for `ambiguous_recipe` if its independent Recipe revisions are admitted. |

## Initial vertical slice

`continuous_square_explicit_eps_delta@1` materializes the target
`Continuous (fun x : ℝ => x ^ 2)` and an explicit proof that:

1. rewrites with `Metric.continuous_iff`;
2. declares `let δ := min 1 (ε / (2 * |x| + 1))`;
3. proves the denominator and `δ` are positive;
4. proves the bound on `|y + x|` via factorization and absolute-value inequalities; and
5. finishes the explicit ε–δ estimate without `continuous_id.pow`.

An independently reviewed exact-target alignment links the immutable payload of `continuous_square`
to this Recipe and sets `explicit_epsilon_delta`. The first test uses both aligned-Draft and formal
target selection modes; it does not claim that current learner traffic already has a Draft resolver.

## Security and operational constraints

- Recipe data are untrusted until every admission check succeeds. The isolated verifier is the only
  component allowed to compile it.
- Manifests, receipts, SQL, DTOs, and traces must contain no credentials or API keys.
- The release-only catalog owner, runtime selector, and catalog reader have only the grants stated
  above; the agent has no database credentials. The internal endpoint accepts only the dedicated
  worker secret and produces authenticated bound DTOs. An isolated test PostgreSQL instance is
  provisioned via `PALS_TEST_POSTGRES_URL`; tests assert schema ownership, role restrictions,
  lifecycle-lock serialization, endpoint authentication, and the absence of direct agent DB
  configuration.
- The Recipe v1 path has no vector extension or embedding-provider dependency. A future similarity
  profile must add its own binding, egress policy, and false-selection evaluation before use.

## Evaluation design

The versioned fixture manifest declares for each case: inputs, available Recipe/alignment lifecycle
events, expected selected ID/revision or expected rejection codes, expected materialized digest,
expected verifier result, and expected method tag. Metrics are calculated as follows:

- compile rate = successful verifier results / fixtures expected to select a Recipe;
- correct-selection rate = fixtures with exactly the expected selected Recipe / fixtures expected to
  select a Recipe;
- false-selection rate = fixtures that select any Recipe when the manifest expects no selection /
  fixtures expected to select no Recipe;
- proof-method fidelity = selected fixtures whose declared method tag equals the fixture's expected
  method tag and whose method-specific structural oracle passes / selected fixtures with a method
  tag.

The gate requires the expected square Recipe to compile, zero false selections, 100% correct
selection in expected-select fixtures, and 100% method fidelity. The suite uses a real isolated
PostgreSQL service and pinned Lean verifier. Existing Draft/PFI corpora run unchanged as regressions.
