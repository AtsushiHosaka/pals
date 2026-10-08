#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${SCRIPT_DIR}/../lib/redact.sh"

trace_id=""
load_env "$@"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --trace-id)
      trace_id="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z "${trace_id}" ]]; then
  echo "error: provide --trace-id" >&2
  exit 2
fi

out_dir="$(make_output_dir langfuse-traces)"

fetch_redacted_file "${out_dir}/langfuse-trace.json" curl -fsS \
  -u "${LANGFUSE_PUBLIC_KEY}:${LANGFUSE_SECRET_KEY}" \
  "${LANGFUSE_HOST}/api/public/traces/${trace_id}"
write_manifest "${out_dir}" "langfuse-traces"
echo "${out_dir}"
