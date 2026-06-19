#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${SCRIPT_DIR}/../lib/redact.sh"

trace_id=""
proof_job_id=""

load_env "$@"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --trace-id)
      trace_id="${2:-}"
      shift 2
      ;;
    --proof-job-id)
      proof_job_id="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

query="${trace_id:-${proof_job_id:-}}"
if [[ -z "${query}" ]]; then
  echo "error: provide --trace-id or --proof-job-id" >&2
  exit 2
fi

out_dir="$(make_output_dir cloudwatch-logs)"
log_groups=("${PALS_CLOUDWATCH_LOG_GROUP_API:-}" "${PALS_CLOUDWATCH_LOG_GROUP_AGENT:-}")

for log_group in "${log_groups[@]}"; do
  if [[ -z "${log_group}" ]]; then
    continue
  fi

  safe_name="$(echo "${log_group}" | tr '/:' '__')"
  aws logs filter-log-events \
    --profile "${AWS_PROFILE}" \
    --region "${AWS_REGION}" \
    --log-group-name "${log_group}" \
    --filter-pattern "\"${query}\"" \
    --output json > "${out_dir}/${safe_name}.json"
  redact_file_in_place "${out_dir}/${safe_name}.json"
done

write_manifest "${out_dir}" "cloudwatch-logs"
echo "${out_dir}"

