#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

for path in .aws/credentials nested/.aws/config .gcp/credentials.json \
  service-account-production.json nested/service_account_prod.json \
  project-firebase-adminsdk-local.json terraform.tfstate \
  nested/custom.tfstate.backup production.tfvars production.tfvars.json \
  id_rsa id_ed25519 signing.pfx signing.p12 signing.jks signing.keystore; do
  git -C "${ROOT_DIR}" check-ignore --no-index -q -- "${path}" || {
    echo 'Sensitive artifact is not ignored.' >&2
    exit 1
  }
done

for path in .env.example .env.playwright.example settings.json backend.tf production.example.tfvars \
  production.template.tfvars.json production.tfvars.example; do
  set +e
  git -C "${ROOT_DIR}" check-ignore --no-index -q -- "${path}"
  status=$?
  set -e
  [ "${status}" -eq 1 ] || {
    echo 'An ordinary file or example was ignored, or ignore inspection failed.' >&2
    exit 1
  }
done
echo 'Secret ignore cases passed.'
