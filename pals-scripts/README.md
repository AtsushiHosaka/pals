# PALS Helper Scripts

This directory contains small parent-repository helpers only.

Kept responsibilities:

- secret scanning and public/private boundary checks;
- safe environment selection for explicitly invoked local model tools;
- small fetch/redaction helpers.

It does not enforce Spec hashes, approval status, repository ownership tables,
release promotion, Cognito bootstrap, or Docker proof-runtime orchestration.
Component-specific development and tests belong to the owning repository.
