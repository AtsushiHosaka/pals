# Draft addition candidates design

## Storage

An additive, API-owned `pals_draft_candidates` schema with an append-only candidate table and a separate append-only decision table, installed by a release migration (serving never migrates). A candidate row holds: candidate id, proof job id, formal target SHA-256, verified Lean source and its SHA-256, toolchain fingerprint, verifier attestation reference, reviewed explanation text, referenced Draft ids, created_at. A unique constraint on (Lean source SHA-256, target SHA-256) prevents duplicates. No request statement, chat text, clarification text, owner or project column exists. The runtime role may only insert candidates and read clarification counts; decisions use a distinct operator role through fixed-search-path functions, modelled on `recipe_curation_proposals`.

## Lifecycle

The API inserts the candidate in the same transaction that marks a request `answered` with `lean_verified` (DAC-001). Eligibility is computed at read time: `created_at + 24 h <= now()` and zero explanation clarifications for the job created before that time (DAC-003). Decisions are `approved` or `rejected` with closed reason codes and the expected-state check under a row lock (DAC-004).

## Operator CLI and admission

`python -m app.release.draft_candidates list|approve|reject` runs with the operator database credential, outside the web application. Approval of an eligible candidate writes the decision and emits a sealed authoring bundle: Draft payload (canonical statement, OpenMath, proof strategy and sketch steps derived from the verified source and explanation), `RecipeAuthoringManifestV1` and the alignment manifest. Locally the command then runs the existing Draft insertion with the real embedding provider and `lean-recipe-catalog-admit` / `lean-recipe-alignment-admit`, which recompile the source through the admission verifier. In production the bundle is included in the next signed Draft catalog release. A failed admission leaves the candidate approved with no catalog change and reports the failing step.
