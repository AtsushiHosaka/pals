# Source routes and functional monitoring — 2026-10-15

The user requested fixes for audit items1 (source-route gaps) and5 (functional monitoring), prioritizing production safety. Items2–4 are unchanged.

Implementation: infra PR72 adds exact GET/OPTIONS routes for guest referenced sources and member catalog Lean source. Its separate operator binds a plan to the current main checkout and existing production identity, validates the entire Caddy configuration, preserves previous adapted semantics, snapshots old bytes, and rolls back if activation/public checks fail. API, database and proof workers are not replaced. Only the existing edge may need a brief restart if its admin endpoint is already disabled.

An independent five-minute observer checks guest admission, source routes/CORS, existing Cognito session refresh, authenticated account/project/proof/settings/material/search reads. It never restarts services, writes projects, runs migrations or submits proofs. It reports checks_passed rather than claiming global health and explicitly excludes fresh password sign-in, new proof execution, project writes and payments. Existing maintenance locks and release changes cause the check to be skipped/discarded. Persistent failure emits a sanitized transition after two checks; credentials never enter status or argv.

Validation: all131 edge tests pass, including isolated real-Caddy tests for existing routes plus new method/path/Host/CORS boundaries and rollback/stale-plan tests. All11 functional monitor tests pass, covering read-only behavior, guest-cookie reuse, renewal throttling, maintenance/release races, degraded/recovered states, private-file protection and secret-free output.

Local full-parent secret scanning detects existing test fixture strings in the newly initialized, unchanged pals-observability tests/test_cli_subprocess.py and tests/test_langfuse_loader.py. The observed matches are outside this change; no values are copied here. The modified infra component is checked separately. Do not weaken the scanner or change unrelated files to hide this result.

## Rollout status

- Infra PR72 merged; parent pin pending.
- Public route production activation pending exact plan and public checks.
- Functional monitor credentials/install pending: automatic approval review rejected storing a new long-lived QA refresh token without explicit user approval. The user was asked whether to allow that private storage or limit monitoring to credential-free checks. No password or refresh token was saved by the rejected command.
