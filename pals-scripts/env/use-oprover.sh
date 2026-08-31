#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PALS_SCRIPTS_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PALS_SCRIPTS_DIR}/.." && pwd)"

usage() {
  cat <<'EOF'
Usage: pals-scripts/env/use-oprover.sh [options]

Update only the OProver/MLX-related lines in a local env file.

Options:
  --file PATH          Env file to update. Default: .env.local
  --model-dir PATH     MLX model directory. Default: ~/Models/PALS/OProver-32B-MLX-4bit
  --binary PATH        mlx_lm.generate binary. Default: <repo>/.venv-oprover/bin/mlx_lm.generate
  --max-tokens N       PALS_MLX_MAX_TOKENS. Default: 4096
  --timeout SECONDS    PALS_MLX_TIMEOUT_SECONDS. Default: 600
  --temperature FLOAT  PALS_MLX_TEMPERATURE. Default: 0
  --light-provider P   Also set PALS_LLM_PROVIDER to openai or ollama.
  -h, --help           Show this help.

This script does not write API keys and does not change unrelated env lines.
EOF
}

env_file="${REPO_ROOT}/.env.local"
model_dir="${HOME}/Models/PALS/OProver-32B-MLX-4bit"
binary="${REPO_ROOT}/.venv-oprover/bin/mlx_lm.generate"
max_tokens="4096"
timeout_seconds="600"
temperature="0"
light_provider=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      env_file="$2"
      shift 2
      ;;
    --model-dir)
      model_dir="$2"
      shift 2
      ;;
    --binary)
      binary="$2"
      shift 2
      ;;
    --max-tokens)
      max_tokens="$2"
      shift 2
      ;;
    --timeout)
      timeout_seconds="$2"
      shift 2
      ;;
    --temperature)
      temperature="$2"
      shift 2
      ;;
    --light-provider)
      light_provider="$2"
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

case "${light_provider}" in
  ""|openai|ollama) ;;
  *)
    echo "error: --light-provider must be openai or ollama" >&2
    exit 2
    ;;
esac

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

set_env_var "PALS_PROVE_MLX_MODEL_PATH" "${model_dir}"
set_env_var "PALS_MLX_GENERATE_BINARY" "${binary}"
set_env_var "PALS_MLX_MAX_TOKENS" "${max_tokens}"
set_env_var "PALS_MLX_TIMEOUT_SECONDS" "${timeout_seconds}"
set_env_var "PALS_MLX_TEMPERATURE" "${temperature}"

if [[ -n "${light_provider}" ]]; then
  set_env_var "PALS_LLM_PROVIDER" "${light_provider}"
fi

if [[ ! -d "${model_dir}" ]]; then
  echo "warning: model directory does not exist: ${model_dir}" >&2
  echo "hint: run 'mise run oprover:download' and 'mise run oprover:convert-mlx'" >&2
fi

if [[ ! -x "${binary}" ]]; then
  echo "warning: MLX binary is not executable: ${binary}" >&2
  echo "hint: run 'mise run oprover:venv'" >&2
fi

echo "updated ${env_file}"
