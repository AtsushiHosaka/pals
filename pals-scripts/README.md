# PALS Scripts

`pals-scripts` contains local helper scripts for collecting AWS, database,
CloudWatch, Langfuse, and proof-job debugging data without sharing secrets with
Codex.

The scripts are committed to GitHub in the private `pals` repository. Local
environment files and generated outputs are not committed.

## Files

- `.env.example` - safe template for local environment files
- `.env.dev` - local-only development environment values
- `.env.prod` - local-only production environment values
- `lib/common.sh` - shared argument/env handling
- `lib/redact.sh` - secret redaction helpers
- `fetch/*.sh` - data collection commands
- `outputs/` - generated, redacted artifacts

## Usage

Create a local env file first:

```bash
cp pals-scripts/.env.example pals-scripts/.env.dev
```

Then run a fetch command:

```bash
pals-scripts/fetch/cloudwatch-logs.sh --env dev --trace-id trace_123
```

Production commands require an explicit confirmation flag:

```bash
pals-scripts/fetch/aws-cost.sh --env prod --confirm-prod
```

## Rules

- Do not commit `.env.dev`, `.env.prod`, or files under `outputs/`.
- Do not print API keys, database URLs, AWS credentials, or Langfuse secrets.
- Give Codex only the redacted files generated under `outputs/`.

