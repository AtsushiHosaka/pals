#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${SCRIPT_DIR}/../lib/redact.sh"

load_env "$@"
out_dir="$(make_output_dir aws-cost)"

start_date="$(date -u -v-30d +%Y-%m-%d 2>/dev/null || date -u -d '30 days ago' +%Y-%m-%d)"
end_date="$(date -u +%Y-%m-%d)"

aws ce get-cost-and-usage \
  --profile "${AWS_PROFILE}" \
  --region "${AWS_REGION}" \
  --time-period "Start=${start_date},End=${end_date}" \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json > "${out_dir}/aws-cost.json"

redact_file_in_place "${out_dir}/aws-cost.json"
write_manifest "${out_dir}" "aws-cost"
echo "${out_dir}"

