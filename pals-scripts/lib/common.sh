#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALS_SCRIPTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

usage_common() {
  cat <<'EOF'
Common flags:
  --env dev|prod       Environment to load. Required.
  --confirm-prod       Required when --env prod is used.
EOF
}

load_env() {
  local env_name=""
  local confirm_prod="false"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --env)
        env_name="${2:-}"
        shift 2
        ;;
      --confirm-prod)
        confirm_prod="true"
        shift
        ;;
      *)
        shift
        ;;
    esac
  done

  if [[ "${env_name}" != "dev" && "${env_name}" != "prod" ]]; then
    echo "error: --env must be dev or prod" >&2
    exit 2
  fi

  if [[ "${env_name}" == "prod" && "${confirm_prod}" != "true" ]]; then
    echo "error: prod requires --confirm-prod" >&2
    exit 2
  fi

  local env_file="${PALS_SCRIPTS_DIR}/.env.${env_name}"
  if [[ ! -f "${env_file}" ]]; then
    echo "error: missing ${env_file}" >&2
    echo "hint: cp ${PALS_SCRIPTS_DIR}/.env.example ${env_file}" >&2
    exit 2
  fi

  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a

  export PALS_ENV="${env_name}"
  export AWS_PROFILE="${AWS_PROFILE:-pals-${env_name}}"
  export AWS_REGION="${AWS_REGION:-us-east-1}"
}

make_output_dir() {
  local name="$1"
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local out_dir="${PALS_SCRIPTS_DIR}/outputs/${PALS_ENV}/${stamp}-${name}"
  mkdir -p "${out_dir}"
  printf '%s\n' "${out_dir}"
}

write_manifest() {
  local out_dir="$1"
  local command_name="$2"
  cat > "${out_dir}/manifest.json" <<EOF
{
  "environment": "${PALS_ENV}",
  "command": "${command_name}",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "redacted": true
}
EOF
}

