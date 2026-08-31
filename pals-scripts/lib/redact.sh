#!/usr/bin/env bash
set -euo pipefail

if ! declare -p PALS_REDACTED_OUTPUT_FILES >/dev/null 2>&1; then
  declare -a PALS_REDACTED_OUTPUT_FILES=()
fi

redact_stream() {
  local python_bin
  python_bin="$(command -v python3 2>/dev/null || true)"
  if [[ -z "${python_bin}" ]]; then
    printf '%s\n' 'error: python3 is required for structured redaction' >&2
    return 127
  fi

  "${python_bin}" -c '
import json
import re
import sys


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate JSON key")
        result[key] = value
    return result


def normalize_key(value):
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def is_secret_field(key):
    normalized = normalize_key(key)
    tokens = set(filter(None, normalized.split("_")))
    exact = {
        "authorization",
        "proxy_authorization",
        "cookie",
        "set_cookie",
        "credential",
        "credentials",
        "jwt",
        "key",
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
    }
    if normalized in exact:
        return True
    if tokens.intersection({"password", "passwd", "pwd", "secret"}):
        return True
    if normalized.endswith("_token"):
        return True
    key_prefixes = (
        "api",
        "private",
        "secret",
        "access",
        "signing",
        "encryption",
        "credential",
    )
    return any(normalized.endswith(f"{prefix}_key") for prefix in key_prefixes)


private_key_pattern = re.compile(
    r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----.*?"
    r"-----END(?: [A-Z0-9]+)* PRIVATE KEY-----",
    re.DOTALL,
)
credential_url_pattern = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|redis(?:s)?|"
    r"mongodb(?:\+srv)?|amqp(?:s)?)://[^\s\"\x27<>]+"
)
bearer_pattern = re.compile(r"(?i)\bBearer[ \t]+[^\s,;\"\x27]+")
jwt_pattern = re.compile(
    r"(?<![A-Za-z0-9_-])(?:[A-Za-z0-9_-]{4,}\.){2}"
    r"[A-Za-z0-9_-]{4,}(?![A-Za-z0-9_-])"
)
aws_access_key_pattern = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
prefixed_key_pattern = re.compile(
    r"(?<![A-Za-z0-9_-])(?:sk|pk)-[A-Za-z0-9_-]{12,}(?![A-Za-z0-9_-])"
)
email_pattern = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
field_name = (
    r"(?:authorization|proxy[_ .-]*authorization|cookie|set[_ .-]*cookie|"
    r"token|jwt|[A-Za-z0-9_.-]*(?:access|refresh|id|jwt|bearer|session)"
    r"[A-Za-z0-9_.-]*token|[A-Za-z0-9_.-]*(?:password|passwd|pwd)|"
    r"[A-Za-z0-9_.-]*secret[A-Za-z0-9_.-]*|"
    r"[A-Za-z0-9_.-]*(?:api|private|secret|access|signing|encryption|credential)"
    r"[A-Za-z0-9_.-]*key)"
)
quoted_assignment_pattern = re.compile(
    rf"(?P<prefix>(?<![A-Za-z0-9])(?:\"|\x27)?{field_name}"
    rf"(?:\"|\x27)?\s*[:=]\s*)(?P<quote>[\"\x27])"
    rf"(?P<value>[^\r\n]*?)(?P=quote)",
    re.IGNORECASE,
)
plain_assignment_pattern = re.compile(
    rf"(?P<prefix>(?<![A-Za-z0-9])(?:\"|\x27)?{field_name}"
    rf"(?:\"|\x27)?\s*[:=]\s*)(?P<value>[^\r\n,;}}\]]+)",
    re.IGNORECASE,
)


def redact_text(value):
    value = private_key_pattern.sub("[REDACTED_PRIVATE_KEY]", value)
    value = credential_url_pattern.sub("[REDACTED_CREDENTIAL_URL]", value)
    value = bearer_pattern.sub("Bearer [REDACTED]", value)
    value = jwt_pattern.sub("[REDACTED_JWT]", value)
    value = aws_access_key_pattern.sub("[REDACTED_AWS_ACCESS_KEY]", value)
    value = prefixed_key_pattern.sub("[REDACTED_KEY]", value)
    value = quoted_assignment_pattern.sub(
        lambda match: "{}{}[REDACTED]{}".format(
            match.group("prefix"),
            match.group("quote"),
            match.group("quote"),
        ),
        value,
    )
    value = plain_assignment_pattern.sub(
        lambda match: "{}[REDACTED]".format(match.group("prefix")),
        value,
    )
    return email_pattern.sub("[REDACTED_EMAIL]", value)


def redact_json(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if is_secret_field(key) else redact_json(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


raw = sys.stdin.buffer.read()
text = raw.decode("utf-8", errors="strict")
try:
    payload = json.loads(text, object_pairs_hook=reject_duplicate_keys)
except (json.JSONDecodeError, DuplicateKeyError):
    output = redact_text(text)
else:
    output = json.dumps(
        redact_json(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
sys.stdout.buffer.write(output.encode("utf-8"))
'
}

redact_file_in_place() {
  local file="$1"
  local canonical_file
  local output_dir
  local tmp_file

  if [[ ! -f "${file}" || ! -r "${file}" ]]; then
    printf 'error: redaction input must be a readable regular file\n' >&2
    return 64
  fi

  output_dir="$(cd "$(dirname "${file}")" && pwd)"
  canonical_file="${output_dir}/$(basename "${file}")"
  tmp_file="$(mktemp "${output_dir}/.redact.XXXXXX")"
  chmod 600 "${tmp_file}"
  if ! redact_stream < "${file}" > "${tmp_file}"; then
    rm -f -- "${tmp_file}"
    return 1
  fi
  chmod 600 "${tmp_file}"
  if ! mv -f -- "${tmp_file}" "${file}"; then
    rm -f -- "${tmp_file}"
    return 1
  fi

  local known_file
  for known_file in "${PALS_REDACTED_OUTPUT_FILES[@]-}"; do
    if [[ "${known_file}" == "${canonical_file}" ]]; then
      return 0
    fi
  done
  PALS_REDACTED_OUTPUT_FILES+=("${canonical_file}")
}
