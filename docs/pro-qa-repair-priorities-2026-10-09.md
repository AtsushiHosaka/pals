# Pro QA repair priorities — 2026-10-09

This ledger tracks work started from the [authenticated Pro dogfood report](pro-dogfood-2026-10-09.md). Priority reflects confirmed impact, confidence in the cause, and the amount of verified repair available. It is not a claim that these changes are deployed.

| Order | Parent issue | Finding and repair | Current status |
|---|---|---|---|
| 1 | [#12](https://github.com/AtsushiHosaka/pals/issues/12), [#36](https://github.com/AtsushiHosaka/pals/issues/36) | Mathematics settings and private Share-dialog reads return edge 404. Existing mathematics fragment plus [infra PR #16](https://github.com/AtsushiHosaka/pals-infra/pull/16) provide narrow authenticated API routes. | Exact sharing head reviewed; Mini installation and authenticated recovery pending. |
| 2 | [#41](https://github.com/AtsushiHosaka/pals/issues/41) | Project materials management was removed from the frontend despite retained backend support. [webfront PR #13](https://github.com/AtsushiHosaka/pals-webfront/pull/13) restores Project-home PDF/image management and OCR state. | Tested draft, stacked on webfront #12; live upload/OCR pending. |
| 3 | [#40](https://github.com/AtsushiHosaka/pals/issues/40) | Clarification controls used answer language instead of UI language. [webfront PR #12](https://github.com/AtsushiHosaka/pals-webfront/pull/12) corrects both chat screens. | Tested draft; deployment and browser verification pending. |
| 4 | [#37](https://github.com/AtsushiHosaka/pals/issues/37), [#38](https://github.com/AtsushiHosaka/pals/issues/38) | Generic formal failure and review rejection need original request/job evidence. [agent PR #5](https://github.com/AtsushiHosaka/pals-agent/pull/5) adds safe settlement diagnostics. | Tested diagnostic improvement; historic root causes and actual behavior repairs remain open. |
| 5 | [#39](https://github.com/AtsushiHosaka/pals/issues/39) | Prior displayed requests are absent from worker assessment input. Repair needs immutable history shared by assessment, quote and proof-evidence contracts. | Source omission confirmed; [working repair specification](../specs/proof-chat-context/requirements.md) prepared. No history/schema implementation yet. |
| 6 | [#16](https://github.com/AtsushiHosaka/pals/issues/16) | No user model selector exists. Current PFR-001 requires automatic Luna routing and bounded Terra escalation. | Product choice pending: display automatic routing or introduce a selectable mode. No selector contract has been invented. |

## Prepared changes and validation

- **Infra #16**, `7fffc7e9c8750011ef171a0e89727171dcec474b`: seven matcher tests and eleven native Caddy HTTP tests (131 requests) passed. The combined sharing, mathematics and billing configuration validated. Tests cover route, UUID, Host, Origin and authenticated-upstream boundaries, denied mutations/internal paths, and temporary upstream failure/recovery. The synthetic upstream proves proxy behavior; actual API authorization and database permissions still need serving-host checks.
- **Webfront #12**, `2ffefdfc31ed728787170df4d1b5d6394bd929fe`: 57 relevant tests, TypeScript, ESLint and diff checks passed. Mounted-screen regressions cover Japanese UI with English answers and the reverse in Project and legacy chat.
- **Webfront #13**, `e12a51627df46cf3c256e29d685240a59014a4cf`: 25 focused tests and 64 related regressions, TypeScript, ESLint and diff checks passed. Upload requires active Pro; existing-material reads remain available after expiry. Management is mounted on Project home and uses the existing preview. Production PDF/image upload and OCR have not been verified.
- **Agent #5**, `bd8246cfd16021087cfb32ca909edd59cd982dfa`: 90 worker/reuse/Lean-flow tests, Ruff and diff checks passed. Logs contain validated UUIDs, allowlisted status/phase/error labels and a boolean review verdict. They exclude prompts, answers, rationale and provider text. Review, charging, leases and retry decisions are unchanged. A formal `verifying` status records handoff, not successful Lean verification.

The original dogfood preceded recently merged language-binding changes in child repositories. Those changes cannot establish the cause of #38 retrospectively. Rejected candidates and independent-review rationale are retained in operator-private evidence; public generic error text alone cannot diagnose #37 or #38.

Remote heads and base relationships were rechecked without drift. All three new code PRs are open, clean and mergeable drafts. CodeRabbit reports success; neither implementation repository has executable Actions workflows or required protected-main checks. That review status does not replace the local test evidence or the outstanding live acceptance checks.

## Mini installation and acceptance

Anonymous public probes returned plain edge 404 for exact mathematics and canonical-UUID private sharing routes, including preflight. The existing preferences route returned API authentication-required 401 and successful allowed-origin preflight, giving a useful route-level comparison.

Read-only Mini inspection run `37804773581` succeeded. It reported signed release sequence 17 and a current 32-step registry containing mathematics, sharing, materials/OCR and QA Pro steps. The registry hash matched the reviewed local fixture: `723c4c3f722539fa4f2476f3ec43991a8b8ee4869967c62aa9e39a4d56265747`. This does not independently prove per-table serving-role permissions or successful authenticated feature requests. Preserve the current signed-v6 authority; older README instructions are not a reason to downgrade or reapply migrations.

Installation must use the approved Mini maintenance procedure, preserve the actual API Host/upstream and existing billing/guest/reject routes, back up the mounted configuration, validate the complete candidate with the pinned Caddy image, and reload the same edge container. Check direct API mathematics/sharing readiness before installation. Afterward verify anonymous 401, allowed/foreign Origin handling and authenticated settings read/save/reload and private share preview. Restore the original mathematics preference after the reversible save check; do not publish a public share.

SSH currently rejects access. Sending this concrete task to the existing Mini chat requires explicit authorization under the chat-messaging tool's rule; that request is pending. No new production installation, signed-registry change or database migration was performed in this repair pass.

## Local test side effect

The first native Caddy fixture wrote a synthetic configuration to the user's default Caddy autosave location. Its previous contents are unknown. The corrected harness binds loopback, disables autosave and uses fixture-local data; its processes were stopped. The default autosave file was preserved rather than overwritten or deleted again. This was a local test side effect, not a production operation.

All eight issues remain open until their corresponding acceptance evidence is available. Child draft PRs must land before any parent dependency pin; this documentation PR deliberately carries no new child pins.
