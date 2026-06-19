#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${SCRIPT_DIR}/../lib/redact.sh"

load_env "$@"
out_dir="$(make_output_dir aurora-schema)"

cat > "${out_dir}/README.txt" <<'EOF'
This placeholder avoids printing DATABASE_URL. Wire this script to a safe
schema-only dump command once Aurora access is configured through SSM or
Secrets Manager. Do not output credentials.
EOF

write_manifest "${out_dir}" "aurora-schema"
echo "${out_dir}"

