# Repository publication preparation — 2026-10-27

## Scope and result

The requested scope is `pals` and its six declared submodules: `pals-api`,
`pals-webfront`, `pals-infra`, `pals-datasets`, `pals-observability`, and
`pals-agent`. The user explicitly excluded `pals-draft-admin`.

No genuine credential was identified among the scanner's reported candidates.
This is evidence from the checks below, not a guarantee that every confidential
value or document has been identified. No history was rewritten, no credential
was rotated, and no repository visibility was changed.

## Changes prepared for review

- Added cloud credential, service-account, Terraform state/variable, and private
  identity artifact ignore rules in the parent and all six submodules. Ordinary
  JSON files and example Terraform variables remain usable.
- Made the default secret gate require every declared child repository. Missing
  or malformed checkouts, missing pinned objects, shallow history, and scanner
  failures produce an incomplete result instead of PASS.
- Added an explicit parent-only scope for parent CI. Both parent workflows fetch
  full history and run the history check with that limited scope.
- Added historical filenames and Gitleaks content scanning, including deleted
  files, branch/tag/PR refs available locally, merge-result diffs, and child
  commits referenced by current or historical parent gitlinks.
- Added a version/checksum-pinned Gitleaks installer and regression checks for
  the failure cases above. Synthetic observability test strings now construct
  at runtime with identical resulting values, avoiding false current-content hits.

## History evidence

Gitleaks 8.30.1 was obtained from its official release, with the archive checked
against the published SHA256 checksum. Scans used built-in rules, disabled
target-local suppressions, redacted output, and a 300-second timeout. Remote
branches, tags, and PR head refs were fetched. The initial PR-head inventory was:

| Repository | Fetched PR heads | Findings including merge-result diffs |
| --- | ---: | ---: |
| pals | 101 | 5 |
| pals-api | 25 | 24 |
| pals-webfront | 25 | 4 |
| pals-infra | 74 | 17 |
| pals-datasets | 1 | 0 |
| pals-observability | 1 | 0 |
| pals-agent | 17 | 0 |

The 50 fingerprints represent 29 reviewed source findings and 21 additional
merge-result occurrences of byte-identical reviewed source lines. Categories:

- documented revision identifiers, an image tag, and requirements prose;
- artifact/schema integrity digests, migration filenames, a JSON marker name,
  and a cryptography class expression;
- test idempotency values and a browser storage key;
- certificate subject identifiers, IAM role identifiers, and a deliberately
  alphabetic AWS-shaped parser-rejection test sentinel.

Each suppression is restricted to the immutable commit, file, rule, and line
fingerprint. No whole file, detector, or newly introduced commit is exempted.
The two API revisions documented in unpublished parent notes were not available
as API objects; their source explicitly labels them as revisions. They were not
treated as credential values or as verified API commits.

Tracked and historical filename checks found no non-template sensitive path in
the available histories. The historical `.env.playwright.example` is treated as
an example filename; its contents remain subject to content scanning.

## Unpublished local branch boundary

The shared parent object store contains an unrelated local branch,
`codex/math-task-interpretation`, that is three commits ahead of its fetched
remote counterpart. Commit `386c2bb35b63` introduced two child pins whose
objects are unavailable locally and were rejected by GitHub's fetch-by-SHA:

| Child | Unavailable commit prefix |
| --- | --- |
| pals-api | `462ae4526222` |
| pals-webfront | `5f7de44c585b` |

No fetched remote branch, tag, or PR head contains that introducing parent
commit. It is not an ancestor of the audited remote main or this hardening
branch. These missing pins prevent a complete scan of that unpublished local
branch. They do not establish a credential leak in current GitHub history.

The strict `--all` local-history check must report incomplete in that shared
checkout. Audit the fetched GitHub refs and the proposed hardening commits in an
isolated ref snapshot, preserving the unrelated local branch. Before that branch
is pushed later, recover its child objects or deliberately correct its pins.

## Limits and release order

The checks cover available Git file content and configured sensitive filenames.
They do not inspect commit/tag messages, GitHub issue/PR discussion text, Actions
logs or artifacts, release assets, LFS payloads, other clones, or secrets outside
Git. This work does not constitute an application security audit or decide
whether internal operational documentation should be public.

Review and merge the six child PRs, then update/review the parent pins and
workflow changes. Refresh remote refs and rerun the complete publication gate
on the final release revisions before changing visibility. If a genuine secret
is found, rotate/revoke it first and prepare a separately reviewed history
cleanup. No current finding justifies rewriting existing GitHub history.

References: [GitHub sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository),
[Gitleaks source and usage](https://github.com/gitleaks/gitleaks),
[pinned scanner release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
