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
