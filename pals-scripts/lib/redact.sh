#!/usr/bin/env bash
set -euo pipefail

redact_stream() {
  sed -E \
    -e 's/(AKIA|ASIA)[A-Z0-9]{16}/[REDACTED_AWS_ACCESS_KEY]/g' \
    -e 's/sk-[A-Za-z0-9_-]{20,}/[REDACTED_SECRET_KEY]/g' \
    -e 's/pk-[A-Za-z0-9_-]{20,}/[REDACTED_PUBLIC_KEY]/g' \
    -e 's#postgres(ql)?://[^[:space:]"]+#postgres://[REDACTED_DATABASE_URL]#g' \
    -e 's#mysql://[^[:space:]"]+#mysql://[REDACTED_DATABASE_URL]#g' \
    -e 's#Bearer[[:space:]]+[A-Za-z0-9._~+/=-]+#Bearer [REDACTED_TOKEN]#g' \
    -e 's#(authorization|Authorization):[[:space:]]*[^[:space:]]+#\1: [REDACTED]#g' \
    -e 's#([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})#[REDACTED_EMAIL]#g'
}

redact_file_in_place() {
  local file="$1"
  local tmp_file="${file}.tmp"
  redact_stream < "${file}" > "${tmp_file}"
  mv "${tmp_file}" "${file}"
}

