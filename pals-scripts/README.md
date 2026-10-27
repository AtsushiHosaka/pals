# PALS Helper Scripts

This directory contains small parent-repository helpers only.

Kept responsibilities:

- secret scanning and public/private boundary checks;
- safe environment selection for explicitly invoked local model tools;
- loopback-only Cognito Local and reviewer-account bootstrap;
- small fetch/redaction helpers.

It does not enforce Spec hashes, approval status, repository ownership tables,
release promotion, or Docker proof-runtime orchestration.
Component-specific development and tests belong to the owning repository.

## Secret checks before repository publication

Install the checksum-pinned scanner into an operator-selected directory:

```bash
bash pals-scripts/install-gitleaks.sh /tmp/pals-gitleaks
export PATH="/tmp/pals-gitleaks:$PATH"
```

The default check requires the parent and every declared submodule. Missing
checkouts fail with exit code 2. An explicit parent check is available for parent
CI, which does not have credentials for private child repositories:

```bash
bash pals-scripts/check-secrets.sh --scope parent --history
bash pals-scripts/check-secrets.sh --scope all --history
```

Exit code 0 means the stated scope passed; 1 means a policy violation; 2 means
coverage is incomplete. Output contains counts and scope, never matched content.
Without `--history`, only tracked filenames, staged contents, and working-tree
contents are checked. Untracked local files are not a publication scan target.

History checking uses all locally available refs, includes merge-result diffs,
and additionally scans child commits referenced by current and historical parent
gitlinks. Missing objects and shallow repositories fail. The command does not
fetch: before publication, fetch all remote branches, tags, and PR heads for
each repository, and recover any historical pinned commits that are missing.
For each repository, run:

```bash
git fetch --no-recurse-submodules origin \
  '+refs/heads/*:refs/remotes/origin/*' \
  'refs/tags/*:refs/tags/*' \
  '+refs/pull/*/head:refs/pals-publication/pull/*'
```

Use an isolated audit checkout containing the refs intended for publication
when a shared object store also contains unrelated, unpublished local branches.
Do not delete or rewrite those branches to make the scan pass. Record the exact
ref set and commit revisions with the result; a pass does not cover future pushes.

The scanner uses built-in Gitleaks rules, ignores repository-local scanner
configuration and inline suppressions, and redacts output. The trusted
`reviewed-secret-findings.txt` contains only exact historical fingerprints of
reviewed non-secret values. Reasons are recorded in
[the publication audit](../docs/repository-publication-audit-2026-10-27.md).
Changes to that file require reviewing the exact source at the specified commit;
do not add blanket file or detector exceptions.

If genuine credentials are found, revoke or rotate them before cleaning history.
Prepare any rewrite in isolation and coordinate the affected branches, tags,
pull requests, and clones before updating GitHub. Neither this gate nor the
installer rewrites history or changes repository visibility.

## Diagnostic exports

Fetch helpers create unique private output directories (`0700`) and stream raw
responses directly into the redactor. Only successfully redacted files are
published (`0600`); provider errors, redaction failures, and handled interrupts
discard the temporary output. Fetch commands still print the export directory
on success and include a manifest describing redaction status.

## Local reviewer account

From the parent repository, prepare the ignored `.env.local` file and run:

```bash
make local-cognito-bootstrap
```

The target starts the pinned Cognito Local container. The helper then creates or
reuses the `pals-local-users` User Pool and `pals-local-web` App Client, creates
or updates one reviewer account, verifies a real `USER_PASSWORD_AUTH` login, and
updates the local Cognito IDs and reviewer credentials in `.env.local`.

If `PALS_LOCAL_COGNITO_EMAIL` is absent, the local-only address
`reviewer@example.test` is used. If `PALS_LOCAL_COGNITO_PASSWORD` is absent, a
random password is generated and stored only in `.env.local`. Neither the
password nor the verification access token is printed. The helper rejects every
endpoint except an explicit loopback HTTP origin, so it cannot modify AWS
Cognito or another remote service.
