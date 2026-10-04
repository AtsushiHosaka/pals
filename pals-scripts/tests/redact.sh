#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${TEST_DIR}/../.." && pwd)"
# shellcheck source=../lib/common.sh
source "${REPO_DIR}/pals-scripts/lib/common.sh"
# shellcheck source=../lib/redact.sh
source "${REPO_DIR}/pals-scripts/lib/redact.sh"

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-redaction-test.XXXXXX")"
trap 'rm -rf -- "${WORK_DIR}"' EXIT

count=0
ok() {
  count=$((count + 1))
  printf 'ok %d - %s\n' "${count}" "$1"
}

fail() {
  count=$((count + 1))
  printf 'not ok %d - %s\n' "${count}" "$1" >&2
  exit 1
}

assert_absent() {
  local name="$1"
  local needle="$2"
  local file="$3"
  if grep -Fq -- "${needle}" "${file}"; then
    fail "${name}"
  fi
  ok "${name}"
}

JSON_FILE="${WORK_DIR}/structured.json"
cat > "${JSON_FILE}" <<'JSON'
{
  "access_token": "json-access-token-sentinel",
  "PALS_WORKER_SHARED_SECRET": "json-worker-secret-sentinel",
  "AWS_SECRET_ACCESS_KEY": "json-aws-secret-sentinel",
  "jwtToken": "headerPart.payloadPart.signaturePart",
  "localCognitoPassword": "json-password-sentinel",
  "api-key": "json-api-key-sentinel",
  "nested": [
    {"clientSecret": "json-client-secret-sentinel"},
    {"private_key": "json-private-key-sentinel"},
    {"message": "password=embedded-password-sentinel Authorization: Bearer embedded.header.signature"}
  ],
  "database": "postgresql://dbuser:db-password-sentinel@localhost:5432/pals",
  "safe": "retain-this-safe-value"
}
JSON

redact_file_in_place "${JSON_FILE}"

if python3 - "${JSON_FILE}" <<'PY'
import json
import stat
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
for key in (
    "access_token",
    "PALS_WORKER_SHARED_SECRET",
    "AWS_SECRET_ACCESS_KEY",
    "jwtToken",
    "localCognitoPassword",
    "api-key",
):
    assert payload[key] == "[REDACTED]", (key, payload[key])
assert payload["nested"][0]["clientSecret"] == "[REDACTED]"
assert payload["nested"][1]["private_key"] == "[REDACTED]"
assert "embedded-password-sentinel" not in payload["nested"][2]["message"]
assert "embedded.header.signature" not in payload["nested"][2]["message"]
assert "db-password-sentinel" not in payload["database"]
assert payload["safe"] == "retain-this-safe-value"
assert stat.S_IMODE(path.stat().st_mode) == 0o600
PY
then
  ok structured_json_recursive_redaction
else
  fail structured_json_recursive_redaction
fi

for sentinel in \
  json-access-token-sentinel \
  json-worker-secret-sentinel \
  json-aws-secret-sentinel \
  json-password-sentinel \
  json-api-key-sentinel \
  json-client-secret-sentinel \
  json-private-key-sentinel; do
  assert_absent "structured_${sentinel}_absent" "${sentinel}" "${JSON_FILE}"
done

PALS_ENV=local
export PALS_ENV
REDACTED_MANIFEST_DIR="${WORK_DIR}"
write_manifest "${REDACTED_MANIFEST_DIR}" redaction-test
if python3 - "${REDACTED_MANIFEST_DIR}/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["redacted"] is True
PY
then
  ok manifest_true_after_successful_redaction
else
  fail manifest_true_after_successful_redaction
fi

UNREDACTED_MANIFEST_DIR="${WORK_DIR}/unredacted-manifest"
mkdir -p "${UNREDACTED_MANIFEST_DIR}"
write_manifest "${UNREDACTED_MANIFEST_DIR}" no-redaction-test
if python3 - "${UNREDACTED_MANIFEST_DIR}/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["redacted"] is False
PY
then
  ok manifest_false_without_redaction
else
  fail manifest_false_without_redaction
fi

MIXED_MANIFEST_DIR="${WORK_DIR}/mixed-manifest"
mkdir -p "${MIXED_MANIFEST_DIR}"
printf '%s\n' '{"access_token":"mixed-redacted-sentinel"}' \
  > "${MIXED_MANIFEST_DIR}/redacted.json"
printf '%s\n' 'access_token=mixed-unredacted-sentinel' \
  > "${MIXED_MANIFEST_DIR}/unredacted.txt"
redact_file_in_place "${MIXED_MANIFEST_DIR}/redacted.json"
write_manifest "${MIXED_MANIFEST_DIR}" mixed-redaction-test
if python3 - "${MIXED_MANIFEST_DIR}/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["redacted"] is False
PY
then
  ok manifest_false_when_any_artifact_is_unredacted
else
  fail manifest_false_when_any_artifact_is_unredacted
fi

TEXT_FILE="${WORK_DIR}/adversarial.txt"
# Assemble synthetic secret-shaped fixtures only in the temporary test input.
TEST_PRIVATE_KEY_KIND='PRIVATE KEY'
TEST_DB_PASSWORD='text-db-password-sentinel'
cat > "${TEXT_FILE}" <<TEXT
Authorization: Bearer bearerHeader.bearerPayload.bearerSignature
accessToken=text-access-token-sentinel
PALS_WORKER_SHARED_SECRET: text-worker-secret-sentinel
AWS_SECRET_ACCESS_KEY = text-aws-secret-sentinel
password: "text-password-sentinel"
password=space-password-first-sentinel space-password-second-sentinel
api_key='text-api-key-sentinel'
database=postgresql://text-user:${TEST_DB_PASSWORD}@localhost:5432/pals
-----BEGIN ${TEST_PRIVATE_KEY_KIND}-----
text-private-key-sentinel
-----END ${TEST_PRIVATE_KEY_KIND}-----
safe=retain-this-text
TEXT
redact_file_in_place "${TEXT_FILE}"

for sentinel in \
  bearerHeader.bearerPayload.bearerSignature \
  text-access-token-sentinel \
  text-worker-secret-sentinel \
  text-aws-secret-sentinel \
  text-password-sentinel \
  space-password-first-sentinel \
  space-password-second-sentinel \
  text-api-key-sentinel \
  text-db-password-sentinel \
  text-private-key-sentinel; do
  assert_absent "text_${sentinel}_absent" "${sentinel}" "${TEXT_FILE}"
done
if grep -Fq -- 'safe=retain-this-text' "${TEXT_FILE}"; then
  ok conservative_text_preserves_safe_value
else
  fail conservative_text_preserves_safe_value
fi

DUPLICATE_FILE="${WORK_DIR}/duplicate.json"
cat > "${DUPLICATE_FILE}" <<'JSON'
{"access_token":"duplicate-first-sentinel","access_token":"duplicate-second-sentinel","message":"AWS_SECRET_ACCESS_KEY=duplicate-aws-sentinel","safe":"duplicate-safe-value"}
JSON
redact_file_in_place "${DUPLICATE_FILE}"
for sentinel in duplicate-first-sentinel duplicate-second-sentinel duplicate-aws-sentinel; do
  assert_absent "duplicate_${sentinel}_absent" "${sentinel}" "${DUPLICATE_FILE}"
done
if grep -Fq -- 'duplicate-safe-value' "${DUPLICATE_FILE}"; then
  ok duplicate_key_fallback_preserves_safe_value
else
  fail duplicate_key_fallback_preserves_safe_value
fi

INVALID_DIR="${WORK_DIR}/invalid"
INVALID_FILE="${INVALID_DIR}/invalid.bin"
mkdir -p "${INVALID_DIR}"
printf '\377access_token=invalid-byte-sentinel\n' > "${INVALID_FILE}"
INVALID_BEFORE="$(shasum -a 256 "${INVALID_FILE}" | awk '{print $1}')"
if redact_file_in_place "${INVALID_FILE}" >/dev/null 2>&1; then
  fail invalid_utf8_fails_closed
else
  INVALID_AFTER="$(shasum -a 256 "${INVALID_FILE}" | awk '{print $1}')"
  if [[ "${INVALID_AFTER}" == "${INVALID_BEFORE}" ]] \
    && ! find "${INVALID_DIR}" -name '.redact.*' -print -quit | grep -q .; then
    ok invalid_utf8_fails_closed
  else
    fail invalid_utf8_fails_closed
  fi
fi

printf '1..%d\n' "${count}"
