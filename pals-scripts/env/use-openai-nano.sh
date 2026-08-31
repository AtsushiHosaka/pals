#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALS_SCRIPTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PALS_SCRIPTS_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: pals-scripts/env/use-openai-nano.sh [options]

Update only the OpenAI nano / local prove override lines in a local env file.

Options:
  --file PATH      Env file to update. Default: .env.local
  --model MODEL    OpenAI model. Default: gpt-5.4-nano
  --base-url URL   OpenAI-compatible base URL. Default: https://api.openai.com/v1
  -h, --help       Show this help.

This script does not write API keys and does not change unrelated env lines.
EOF
}

env_file="${REPO_ROOT}/.env.local"
model="gpt-5.4-nano"
base_url="https://api.openai.com/v1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      env_file="$2"
      shift 2
      ;;
    --model)
      model="$2"
      shift 2
      ;;
    --base-url)
      base_url="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "$(dirname "${env_file}")"
touch "${env_file}"

set_env_var() {
  local key="$1"
  local value="$2"
  local tmp_file
  tmp_file="$(mktemp)"
  if grep -qE "^${key}=" "${env_file}"; then
    awk -v key="${key}" -v value="${value}" '
      index($0, key "=") == 1 { print key "=" value; next }
      { print }
    ' "${env_file}" > "${tmp_file}"
    mv "${tmp_file}" "${env_file}"
  else
    printf '%s=%s\n' "${key}" "${value}" >> "${env_file}"
    rm -f "${tmp_file}"
  fi
}

set_env_var "PALS_LLM_PROVIDER" "openai"
set_env_var "PALS_OPENAI_MODEL" "${model}"
set_env_var "PALS_OPENAI_BASE_URL" "${base_url}"
set_env_var "PALS_PROVE_MLX_MODEL_PATH" ""

echo "updated ${env_file}"
