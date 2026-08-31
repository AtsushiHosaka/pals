#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${SCRIPT_DIR}/../lib/redact.sh"

proof_job_id=""
load_env "$@"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --proof-job-id)
      proof_job_id="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -z "${proof_job_id}" ]]; then
  echo "error: provide --proof-job-id" >&2
  exit 2
fi

if [[ -z "${PALS_ACCESS_TOKEN:-}" ]]; then
  echo "error: PALS_ACCESS_TOKEN is required; anonymous proof-job fetch is disabled" >&2
  exit 64
fi

out_dir="$(make_output_dir proof-job)"

curl -fsS \
  -H "Authorization: Bearer ${PALS_ACCESS_TOKEN}" \
  "${PALS_API_BASE_URL}/v1/proof-jobs/${proof_job_id}" \
  > "${out_dir}/proof-job.json"

redact_file_in_place "${out_dir}/proof-job.json"
write_manifest "${out_dir}" "proof-job"
echo "${out_dir}"
