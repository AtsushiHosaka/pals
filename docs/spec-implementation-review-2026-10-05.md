# Spec ↔ implementation review — 2026-10-05

Scope: `specs/` against the pinned `pals-api`, `pals-webfront` and `pals-agent` sources, plus a security, billing and responsive-layout pass.

## Spec alignment

Implemented behavior without a canonical spec now has one: `specs/public-guest-chat`, `specs/project-materials`, `specs/chat-navigation`. `specs/README.md` indexes every canonical and repository-owned spec. `individual-billing` BILL-007/BILL-014 describe the current plan UI and gating, and two product decisions are recorded as open questions. The materials proposal points to the canonical spec.

## Changes made

| Repo | Commit | Change |
|---|---|---|
| pals-webfront | `fc3a0b5` | Remove the project-home materials panel (user decision); remove PDF/material claims from the landing copy in four languages. |
| pals-webfront | `299d1ea` | Phone layout: wide display equations no longer push chat messages past the viewport; the mobile navigation sheet no longer clips icons; the composer grows with its text; TeX in suggested follow-up placeholders is shown as plain Unicode or falls back. |
| pals-api | `bdd3e26` | An unnamed failed OCR material no longer rejects every question in its project. |

The answer citation panel was removed by a separate session in webfront `5267537`.

## Verification

- pals-webfront: typecheck, full ESLint and 121 files / 1,348 tests passed after rebasing onto `5267537`; production build passed.
- pals-api: 1,758 unit tests passed. `test_initial_mac_recipe_authority.py::test_production_registry_retains_recipe_positions_and_adds_catalog_before_reader` fails identically on the unmodified base. The real-PostgreSQL material integration tests were not run.
- Responsive: a build of these changes against the running local API, signed in as a throwaway local Cognito test user (`pals-responsive-check@example.test`), checked at 375×812, 768×1024 and 1280×800: dashboard, projects, project home, project chat with a real answer, mobile navigation, settings/billing, chat search, `/about` and `/try`. No page-level horizontal overflow remained. That user, its "Responsive check" project and one answered request remain in the local stack.
- `pals-scripts/check-secrets.sh` reports 4 pre-existing matches in `pals-agent` and `pals-observability` test fixtures, unrelated to these changes.

## Findings left for decision

- Stripe webhook: a transient Stripe API failure during reconciliation records the event as `reconciliation_pending`, marks the entitlement inactive and still returns 200, so Stripe does not redeliver. A paying subscriber stays downgraded until another event or a manual fix (the design says this deliberately). Returning 503 without recording the event on transient failures would let Stripe's retries restore access.
- Paid gating of Project creation (approved token policy) conflicts with the public "free account can organize into projects" copy; Project creation is currently open.
- Production settings show the provisional USD plans as unavailable while public pages say prices are unpublished.
- The landing page advertises Lean compilation and Lean-line hover; per CORE-012 new questions are not Lean-verified, so those features apply only to older verified history.
- Stripe Portal plan switching must stay disabled: a Portal plan change keeps the old `billing_product_id` metadata and the reconciler would mark the subscription inactive.
