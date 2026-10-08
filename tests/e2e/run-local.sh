#!/bin/sh
set -eu

up_only=false
case "${1:-}" in
  '') ;;
  --up-only) up_only=true ;;
  *) printf '%s\n' "usage: $0 [--up-only]" >&2; exit 2 ;;
esac
test "$#" -le 1 || { printf '%s\n' "usage: $0 [--up-only]" >&2; exit 2; }

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
base_compose="$project_root/docker-compose.yml"
infra_compose="$project_root/pals-infra/docker-compose.localstack.yml"
e2e_compose="$project_root/docker-compose.e2e.yml"
local_env="${PALS_E2E_LOCAL_ENV_FILE:-$project_root/.env.local}"
release_env="${PALS_E2E_RELEASE_ENV_FILE:-$project_root/.local/e2e/release.env}"
recipe_env="${PALS_E2E_RECIPE_ENV_FILE:-$project_root/.local/e2e/recipe.env}"
bootstrap="$project_root/pals-scripts/bootstrap-local-verifier-tls.py"
project_name=pals-local
verifier_image=pals-lean-verifier:local

fail() {
  printf '%s\n' "local E2E: $*" >&2
  exit 2
}

command -v docker >/dev/null 2>&1 || fail "docker is required"
test -f "$local_env" || fail "local environment file is missing: $local_env"
test -f "$bootstrap" || fail "TLS bootstrap is missing: $bootstrap"
test -x "$project_root/pals-agent/.venv/bin/python" || \
  fail "pals-agent/.venv/bin/python is required for TLS bootstrap"
test -x "$project_root/pals-api/.venv/bin/python" || \
  fail "pals-api/.venv/bin/python is required for local role configuration"
test ! -L "$release_env" || fail "release environment must not be a symbolic link"

umask 077
mkdir -p "$(dirname -- "$release_env")"

set -a
# shellcheck disable=SC1090
. "$local_env"
set +a

# Caller state and .env.local must not override the immutable generated release file.
unset \
  PALS_RELEASE_ID \
  PALS_VERIFIER_DEPLOYMENT_BINDING_SHA256 \
  PALS_VERIFIER_IMAGE_DIGEST \
  PALS_VERIFIER_TOOLCHAIN_SHA256 \
  PALS_VERIFIER_CA_SPKI_SHA256 \
  PALS_RECONCILER_CLIENT_SPKI_SHA256 \
  PALS_RECONCILER_CLIENT_SPIFFE_URI \
  PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_ARN \
  PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_VERSION_ID \
  PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_ARN \
  PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_VERSION_ID \
  PALS_VERIFIER_CA_CERTIFICATE_SECRET_ARN \
  PALS_VERIFIER_CA_CERTIFICATE_SECRET_VERSION_ID \
  PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_ARN \
  PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_VERSION_ID \
  PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_ARN \
  PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_VERSION_ID

for required_name in \
  OPENAI_API_KEY \
  PALS_DATABASE_URL \
  PALS_COGNITO_USER_POOL_ID \
  PALS_COGNITO_APP_CLIENT_ID \
  PALS_COGNITO_ISSUER \
  PALS_WORKER_SHARED_SECRET; do
  test -n "$(printenv "$required_name" 2>/dev/null || true)" || \
    fail "required environment is missing: $required_name"
done
if test "$up_only" = false; then
  for required_name in PALS_LOCAL_COGNITO_EMAIL PALS_LOCAL_COGNITO_PASSWORD; do
    test -n "$(printenv "$required_name" 2>/dev/null || true)" || \
      fail "required environment is missing: $required_name"
  done
fi

compose() {
  docker compose \
    --project-name "$project_name" \
    --env-file "$local_env" \
    -f "$base_compose" \
    -f "$infra_compose" \
    -f "$e2e_compose" \
    "$@"
}

# Fixed tags are rebuilt on every invocation. Docker's cache keeps the unchanged case cheap,
# while source changes can never silently reuse stale application code.
# BuildKit provenance records contain per-build metadata. Disabling them keeps the
# local image ID stable when the source and Dockerfiles are unchanged.
compose build --provenance=false api verifier worker webfront

# Secrets Manager must be ready before a real certificate generation can be created.
compose up -d --wait postgres localstack cognito-local
compose exec -T localstack sh /etc/localstack/init/ready.d/10-pals-resources.sh
"$project_root/pals-agent/.venv/bin/python" \
  "$project_root/pals-scripts/harden-local-postgres-access.py" --apply

verifier_digest=$(docker image inspect --format '{{.Id}}' "$verifier_image")
toolchain_sha256=${verifier_digest#sha256:}
case "$toolchain_sha256" in
  ''|*[!0-9a-f]*) fail "verifier image did not expose a canonical sha256 digest" ;;
esac
test "${#toolchain_sha256}" -eq 64 || \
  fail "verifier image did not expose a canonical sha256 digest"

release_value() {
  awk -F= -v name="$1" '$1 == name { sub(/^[^=]*=/, ""); print; exit }' "$release_env"
}

release_secret_exists() {
  secret_arn=$(release_value "$1")
  version_id=$(release_value "$2")
  test -n "$secret_arn" && test -n "$version_id" &&
    compose exec -T localstack awslocal \
      --region "${AWS_REGION:-ap-northeast-1}" \
      secretsmanager get-secret-value \
      --secret-id "$secret_arn" \
      --version-id "$version_id" >/dev/null 2>&1
}

release_secrets_exist() {
  release_secret_exists \
    PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_ARN \
    PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_VERSION_ID &&
  release_secret_exists \
    PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_ARN \
    PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_VERSION_ID &&
  release_secret_exists \
    PALS_VERIFIER_CA_CERTIFICATE_SECRET_ARN \
    PALS_VERIFIER_CA_CERTIFICATE_SECRET_VERSION_ID &&
  release_secret_exists \
    PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_ARN \
    PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_VERSION_ID &&
  release_secret_exists \
    PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_ARN \
    PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_VERSION_ID
}

refresh_release=false
old_server_certificate_arn=
old_server_private_key_arn=
old_ca_certificate_arn=
old_client_certificate_arn=
old_client_private_key_arn=
if test ! -f "$release_env"; then
  refresh_release=true
elif test "${PALS_E2E_REFRESH_RELEASE:-0}" = 1; then
  refresh_release=true
elif test "$(release_value PALS_VERIFIER_IMAGE_DIGEST)" != "$verifier_digest"; then
  refresh_release=true
elif test -n "$(find "$release_env" -prune -mmin +1200 -print)"; then
  # Local certificates live for 24 hours. Refresh early enough for a full E2E run.
  refresh_release=true
elif ! release_secrets_exist; then
  refresh_release=true
fi

if test "$refresh_release" = true; then
  if test -f "$release_env"; then
    old_server_certificate_arn=$(release_value PALS_VERIFIER_SERVER_CERTIFICATE_SECRET_ARN)
    old_server_private_key_arn=$(release_value PALS_VERIFIER_SERVER_PRIVATE_KEY_SECRET_ARN)
    old_ca_certificate_arn=$(release_value PALS_VERIFIER_CA_CERTIFICATE_SECRET_ARN)
    old_client_certificate_arn=$(release_value PALS_RECONCILER_CLIENT_CERTIFICATE_SECRET_ARN)
    old_client_private_key_arn=$(release_value PALS_RECONCILER_CLIENT_PRIVATE_KEY_SECRET_ARN)
  fi
  AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}" \
  AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}" \
    "$project_root/pals-agent/.venv/bin/python" "$bootstrap" \
      --endpoint-url "http://127.0.0.1:${LOCALSTACK_HOST_PORT:-4566}" \
      --region "${AWS_REGION:-ap-northeast-1}" \
      --image-digest "$verifier_digest" \
      --toolchain-sha256 "$toolchain_sha256" \
      --output "$release_env"
fi

test -f "$release_env" || fail "release environment was not created"
"$project_root/pals-api/.venv/bin/python" \
  "$project_root/pals-scripts/bootstrap-local-recipe-config.py" \
  --env-file "$local_env" --release-env "$release_env" \
  --output "$recipe_env" --lean-workspace "$project_root/pals-agent/lean-workspace"

compose_runtime() {
  docker compose \
  --project-name "$project_name" \
  --env-file "$local_env" \
  --env-file "$release_env" \
  --env-file "$recipe_env" \
  -f "$base_compose" \
  -f "$infra_compose" \
  -f "$e2e_compose" \
  "$@"
}

# Quiesce mutations before the release job; it has no API ports or fixed IP.
# Failure stops startup and preserves the database for diagnosis.
compose_runtime stop worker assessment-worker recipe-reviewer api reconciler
compose_runtime run --rm --no-deps schema-release
compose_runtime up -d --wait

# A successful rotation makes only the five references from this runner's previous
# release file obsolete. Delete exactly those; unrelated local secrets are untouched.
for obsolete_secret_arn in \
  "$old_server_certificate_arn" \
  "$old_server_private_key_arn" \
  "$old_ca_certificate_arn" \
  "$old_client_certificate_arn" \
  "$old_client_private_key_arn"; do
  if test -n "$obsolete_secret_arn"; then
    compose exec -T localstack awslocal \
      --region "${AWS_REGION:-ap-northeast-1}" \
      secretsmanager delete-secret \
      --secret-id "$obsolete_secret_arn" \
      --force-delete-without-recovery >/dev/null
  fi
done

printf '%s\n' \
  "local E2E ready: web=http://localhost:${PALS_WEB_HOST_PORT:-3000} api=http://localhost:${PALS_API_HOST_PORT:-8000}"

if test "$up_only" = true; then
  exit 0
fi

exec "$project_root/pals-agent/.venv/bin/python" \
  "$project_root/tests/e2e/run_public_api_e2e.py" \
  --fixture "$project_root/tests/e2e/fixtures/university-math-v1.json" \
  --env-file "$local_env" \
  --api-base-url "http://127.0.0.1:${PALS_API_HOST_PORT:-8000}" \
  --cognito-endpoint "http://127.0.0.1:${COGNITO_LOCAL_HOST_PORT:-9229}" \
  --sqs-endpoint-url "http://127.0.0.1:${LOCALSTACK_HOST_PORT:-4566}" \
  --sqs-queue-url "http://127.0.0.1:${LOCALSTACK_HOST_PORT:-4566}/000000000000/${PALS_PROOF_JOBS_QUEUE_NAME:-pals-local-proof-jobs}" \
  --aws-region "${AWS_REGION:-ap-northeast-1}" \
  --overall-timeout-seconds "${PALS_E2E_OVERALL_TIMEOUT_SECONDS:-7200}"
