# Math keyboard production release — 2026-10-12

The user explicitly requested deployment after approving the KaTeX palette in the shared regular-chat composer. Frontend #19 and parent #51 are merged. The parent at this checkpoint is `7e7a3bc5da1929bb09d57ab12fa1c7e0bfef1a10`, with frontend `7aabcd48e23aec7eb124912ab23d1603b66073e6`.

The live automatic-deploy preference remains false. Standard deployment releases the exact current parent main through the signed Mac mini controller; it has no frontend-only bypass.

Read-only [host inspection](https://github.com/AtsushiHosaka/pals/actions/runs/38211886916) and [preflight](https://github.com/AtsushiHosaka/pals/actions/runs/38211924325) passed. Inspection proves the installed signed registry has 32 steps, release sequence20, the serving production runtime/token accounting is ready, and both approved interpreters start. The installed controller/authority are the reviewed older v6 tuple; the v7 capability and attachment schema are absent. This is prerequisite evidence, not deployment completion.

The separate guarded `install-chat` operation requires that exact observed predecessor, current main/pinned clean source, the fixed 32-to-33 bytes, exact reviewed installed/source fingerprints, matching identity/state, no child schema and no pending deployment. It updates only reviewed executable pins and the explicit v7 capability with private atomic backup/rollback. Post-install verification confirms unchanged database admission/trust, services, carrier, registry, source and approved interpreter startup. Signing, DDL, admission and service switching remain in the ordinary deployment controller.

The separate `inspect-edge` operation is read-only. It discovers current config/mount/Host routing privately and emits only closed hashes, counts, booleans and formats. Its subprocess capture is stream-limited; matching route names alone is explicitly not effective-route readiness.

Validation before host mutation:

- A real PG16/pgvector signed-chain regression successfully bootstraps the unmodified historical25 source and appends exact signed v6 registry32 to v7 registry33. It checks real EC signatures via offline KMS/Docker transports, invalid-signature rejection, post-DDL admission rollback, preserved row values, only the two approved existing ACL grants, fixed model default, admission, replay and runtime readiness. The task-owned database container was removed. API [PR #13](https://github.com/AtsushiHosaka/pals-api/pull/13) is test-only; no production behavior changed.
- 58 host operator tests pass. The complete host suite ran155 checks with one existing dedicated PostgreSQL fixture skipped; the new exact-chain regression independently covers the release transition. Installer review found no actionable defect in the pinned bytes.
- 17 edge inspection tests and four workflow adapter checks pass. Independent review identified capture-bound and evidence-wording defects; both were repaired and retested.

Infrastructure prerequisite: [PR #21](https://github.com/AtsushiHosaka/pals-infra/pull/21). This parent update exposes only closed, account-free install-chat/inspect-edge modes while retaining existing modes and the shared lifecycle/concurrency locks. Live installation/deployment and browser verification are still pending at this checkpoint.
