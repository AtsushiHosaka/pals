# PALS Claude Notes

Follow AGENTS.md for repository-specific conventions.

Read [the shared release reliability contract](docs/release-reliability-policy.md) before implementation or release work. Pin the exact issue/revisions and expected user behavior; report missing evidence explicitly. A release is `deployed_unverified` until terminal result, persistence, rendering, and reload acceptance are demonstrated. Health, merge, and test counts alone do not establish functional completion.

Use the same contract as Codex. Keep detailed rules in AGENTS.md and the shared contract rather than maintaining a separate, divergent Claude release procedure.

Run the same executable gates: `make release-source-checks`, `make release-qualify`, and `make release-cycle`. Never substitute a health-only check, copied local driver, old green check, skipped dependency test, or imported PASS JSON. Respect the protected actual-production source baseline recorded in AGENTS.md and retain canonical ownership while a remote mutation is unresolved.

The approved pre-release profile is `make release-local-qualify`: real local DB, real retained Lean and real model, with declared local boundaries and a bounded US$1 evaluation. The cycle freshly verifies the exact existing capture before cutover without paying for a duplicate submission. Production auth/network and completion/save/reload are checked separately using the approved current Chrome account. Follow the detailed profile in AGENTS.md; do not create AWS staging or claim local evidence proves production behavior.
