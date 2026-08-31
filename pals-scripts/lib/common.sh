#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALS_SCRIPTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
unset PALS_REDACTED_OUTPUT_FILES
declare -a PALS_REDACTED_OUTPUT_FILES=()

usage_common() {
  cat <<'EOF'
Common flags:
  --env local|dev|prod Environment to load. Required.
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

  if [[ "${env_name}" != "local" && "${env_name}" != "dev" && "${env_name}" != "prod" ]]; then
    echo "error: --env must be local, dev, or prod" >&2
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
  export AWS_REGION="${AWS_REGION:-ap-northeast-1}"

  local default_llm_provider="bedrock"
  if [[ "${env_name}" == "local" ]]; then
    default_llm_provider="ollama"
  fi
  export PALS_LLM_PROVIDER="${PALS_LLM_PROVIDER:-${default_llm_provider}}"
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
  local all_artifacts_redacted="true"
  local artifact_count=0
  local artifact_file
  local artifact_was_redacted
  local normalized_out_dir
  local redacted="false"
  local redacted_file

  normalized_out_dir="$(cd "${out_dir}" && pwd)"
  while IFS= read -r -d '' artifact_file; do
    artifact_count=$((artifact_count + 1))
    artifact_was_redacted="false"
    for redacted_file in "${PALS_REDACTED_OUTPUT_FILES[@]-}"; do
      if [[ "${redacted_file}" == "${artifact_file}" ]]; then
        artifact_was_redacted="true"
        break
      fi
    done
    if [[ "${artifact_was_redacted}" != "true" ]]; then
      all_artifacts_redacted="false"
    fi
  done < <(find "${normalized_out_dir}" -type f ! -name manifest.json -print0)
  if [[ ${artifact_count} -gt 0 && "${all_artifacts_redacted}" == "true" ]]; then
    redacted="true"
  fi

  cat > "${out_dir}/manifest.json" <<EOF
{
  "environment": "${PALS_ENV}",
  "command": "${command_name}",
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "redacted": ${redacted}
}
EOF
}
