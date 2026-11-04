# Production proof and share smoke — 2026-11-05 JST

Tracking: [proof trial #245](https://github.com/AtsushiHosaka/pals/issues/245),
[Open Graph #228](https://github.com/AtsushiHosaka/pals/issues/228),
[release #234](https://github.com/AtsushiHosaka/pals/issues/234).

## Scope and authority

The owner requested one production trial of a repeating-decimal equality, a
review of the generated proof, and share-card deployment if absent. The trial
uses the existing signed-in Chrome session and the normal PALS UI. No account,
duplicate application stack, database fixture, or replacement answer was created.
The selected UI model was **GPT-6.1 Terra High**. Only one question was submitted.

This is a single smoke trial, not an accuracy benchmark. The public report omits
account identifiers, private chat URLs, share tokens, and request/answer/Lean bodies.
Private screenshots remain outside Git. It does not publish an X post.

## Live card observation

On 2026-11-05 JST, an HTTPS GET to `https://palschat.site/` with
`User-Agent: Twitterbot/1.0` returned HTTP 200 and **zero** `og:*` or `twitter:*`
meta tags. The request used Python's standard-library HTTPS client and an HTML
parser. This establishes the homepage's missing metadata; shared-page metadata
and the actual X preview require separate checks.

[Web PR #31](https://github.com/AtsushiHosaka/pals-webfront/pull/31) implements
cards on the divergent `main` branch. The production-line source tip inspected
was `1706a53007e5e2c601937fb342e391771d6ff37d`; it does not include the two card
commits `73bd6e253cf79eefd78d00da3b6176fc8d971ff0` and
`600a6de0b364644133b29218f0d86786834b4427`. Integration must retain the newer
production-line changes rather than deploy all of `main`.

The separate release chat is preparing a renewal of the existing software
configuration. That candidate retains the old Web revision, so signing it does
not deploy the cards. This chat owns card integration and proof evidence, and
does not modify the other chat's release artifacts or run a concurrent cutover.

## Trial observations

- Submitted at **2026-11-04 15:14:52.979 UTC** (2026-11-05 00:14:52.979 JST).
- The UI created a new conversation and displayed the submitted question.
- Observed states include `Drafting`, `Proving`, `Compiling`, and then `Proving`
  again. These labels alone do not establish proof success or a failure cause.
- A completed answer was observed by **15:22:14.805 UTC**, an upper bound of
  441.826 seconds from submission. This is an observation bound, not server-side
  execution timing or a latency percentile.
- The returned explanation is English. It derives a finite partial-sum formula,
  proves convergence, establishes summability, and identifies the infinite sum
  by uniqueness of limits. It does not rely only on finite decimal arithmetic.
- Manual inspection of the 98-line Lean source confirmed that its target is the
  corresponding infinite sum over the real numbers. It has no added hypotheses,
  `sorry` token, or new axiom declaration. This inspection is not a Lean rerun.
- The normal sharing preview showed two messages and `Lean検証済み`. After
  review, the owner-requested immutable public snapshot was created.
- An independent HTTPS request without cookies or authorization retrieved the
  public snapshot with HTTP 200: two messages, `output_language=en`, assistant
  `status=verified`, and nonempty Lean source. Its response retained
  `Cache-Control: no-store, private, max-age=0` and no-index headers.
- The actual shared-page HTML also returned HTTP 200 with no-store/no-index
  headers and **zero card metadata tags**. Browser navigation to the anonymous
  page stalled in the existing Chrome session; the share dialog and anonymous
  HTTP retrieval were verified independently. Do not count the stalled browser
  navigation as a successful anonymous UI journey.
  A separate in-app anonymous browser was unavailable in this environment.

## Card candidate and review

[Web PR #37](https://github.com/AtsushiHosaka/pals-webfront/pull/37) integrates the
two card commits onto `1706a53`, preserving the existing title and Lean-panel
changes. Independent review identified a sizing-command regex that corrupted
arrows and large set operators. The correction and regression cases were
included in final candidate `073cedbf9d3b2eb357ef72469d5f81d54116a3c5`; a second
independent review reported no remaining P0–P2 findings.

Validation: TypeScript, changed-file ESLint, whitespace checks, 1,687 unit tests
before the operator correction, 47 focused tests and a production rebuild after
it. The final standalone production build fetched this actual anonymous snapshot
from the live API: Twitterbot HTML contained problem-specific title/description,
`summary_large_image` and an absolute image URL. Its PNG was 1200×630, visually
checked with readable Japanese text. The page/image retained private no-store,
no-index and no-referrer headers. An invalid token rendered a brand-only image.
Temporary local servers were stopped and port 3187 was confirmed released.

PR #37 was merged into the production source branch as
`4dbc451818e8d3312f3d72064be5b41eb302b6d8`. The only remote status check was
CodeRabbit, which was skipped; no GitHub Actions run existed for this head.
Local verification and independent review above supply the executed checks.
This merge is **not a deployment**. Host/container API and font connectivity,
the signed software update, activation, and actual X rendering remain pending
the separately owned release flow in #234.

## Verification limits

The source branch and issue history do not prove which image currently serves a
particular request. The model selection above is the observed UI selection;
provider usage receipts and cost were not retrieved. No latency distribution or
general success rate can be inferred from this one trial. A PALS verification
label was confirmed through anonymous persistence readback. An independent Lean
compiler rerun, verifier audit receipt, and production latency/cost receipts were
not obtained. The deliverable share remains active; revocation was not tested on
the owner's intended public result.
