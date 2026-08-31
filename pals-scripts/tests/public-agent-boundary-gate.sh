#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
GATE="${ROOT_DIR}/pals-scripts/check-public-agent-boundary.sh"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-public-agent-test.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

command -v zip >/dev/null 2>&1 || {
  printf '%s\n' 'zip is required for public-agent boundary fixtures.' >&2
  exit 1
}

make_wheel() {
  local fixture="$1"
  local extra_path="${2:-}"
  local extra_content="${3:-}"
  local tree="${fixture}/tree"
  local dist_info='pals_agent-0.1.0.dist-info'
  local wheel="${fixture}/pals_agent-0.1.0-py3-none-any.whl"
  mkdir -p "${tree}/pals_agent" "${tree}/${dist_info}"
  printf '%s\n' '__version__ = "0.1.0"' >"${tree}/pals_agent/__init__.py"
  printf '%s\n' 'Name: pals-agent' 'Version: 0.1.0' >"${tree}/${dist_info}/METADATA"
  printf '%s\n' 'Wheel-Version: 1.0' 'Tag: py3-none-any' >"${tree}/${dist_info}/WHEEL"
  : >"${tree}/${dist_info}/RECORD"
  if [ -n "${extra_path}" ]; then
    mkdir -p "$(dirname "${tree}/${extra_path}")"
    printf '%s\n' "${extra_content}" >"${tree}/${extra_path}"
  fi
  (
    cd "${tree}"
    zip -q -X -r "${wheel}" pals_agent "${dist_info}"
  )
  printf '%s' "${wheel}"
}

run_gate() {
  PALS_PUBLIC_AGENT_WHEEL="$1" bash "${GATE}"
}

expect_pass() {
  local wheel="$1"
  local output
  output="$(run_gate "${wheel}" 2>&1)" || {
    printf '%s\n' 'Expected public-agent wheel fixture to pass.' >&2
    exit 1
  }
  [ "${output}" = 'public-agent-boundary: PASS' ] || {
    printf '%s\n' 'Public-agent boundary pass output was not content-free.' >&2
    exit 1
  }
}

expect_fail() {
  local wheel="$1"
  local forbidden_output="${2:-}"
  local output rc
  set +e
  output="$(run_gate "${wheel}" 2>&1)"
  rc=$?
  set -e
  [ "${rc}" -ne 0 ] || {
    printf '%s\n' 'Expected public-agent wheel fixture to fail.' >&2
    exit 1
  }
  case "${output}" in
    'public-agent-boundary: FAIL violations='*' incomplete='*) ;;
    *)
      printf '%s\n' 'Public-agent boundary failure output was not content-free.' >&2
      exit 1
      ;;
  esac
  if [ -n "${forbidden_output}" ]; then
    case "${output}" in
      *"${forbidden_output}"*)
        printf '%s\n' 'Public-agent boundary gate exposed matched content.' >&2
        exit 1
        ;;
    esac
  fi
}

valid_wheel="$(make_wheel "${TMP_DIR}/valid")"
expect_pass "${valid_wheel}"

localstack_identifier_wheel="$(make_wheel "${TMP_DIR}/localstack-identifier" pals_agent/runtime.py 'aws_secret_access_key=_LOCALSTACK_TEST_SECRET')"
expect_pass "${localstack_identifier_wheel}"

key_suffix='ABCDEFGHIJKLMNOP'
access_key="AKIA${key_suffix}"
credential_wheel="$(make_wheel "${TMP_DIR}/credential" pals_agent/credential.py "VALUE = '${access_key}'")"
expect_fail "${credential_wheel}" "${access_key}"

prompt_wheel="$(make_wheel "${TMP_DIR}/private-prompt" pals_agent/private_prompts/system.txt 'fixture prompt')"
expect_fail "${prompt_wheel}" 'fixture prompt'

dataset_wheel="$(make_wheel "${TMP_DIR}/private-dataset" pals_agent/private_datasets/cases.json '{}')"
expect_fail "${dataset_wheel}" 'cases.json'

endpoint='https://api.internal.pals.example/v1'
endpoint_wheel="$(make_wheel "${TMP_DIR}/production-endpoint" pals_agent/endpoint.py "BASE_URL = '${endpoint}'")"
expect_fail "${endpoint_wheel}" "${endpoint}"

config_value='environment = "production"'
config_wheel="$(make_wheel "${TMP_DIR}/production-config" pals_agent/runtime.py "${config_value}")"
expect_fail "${config_wheel}" "${config_value}"

account_id='123456789012'
account_wheel="$(make_wheel "${TMP_DIR}/account-id" pals_agent/account.py "AWS_ACCOUNT_ID = '${account_id}'")"
expect_fail "${account_wheel}" "${account_id}"

private_config_wheel="$(make_wheel "${TMP_DIR}/private-config" pals_agent/.env.production 'MODE=production')"
expect_fail "${private_config_wheel}" '.env.production'

invalid_wheel="${TMP_DIR}/invalid.whl"
printf '%s\n' 'not a wheel' >"${invalid_wheel}"
expect_fail "${invalid_wheel}"

printf '%s\n' 'Public-agent boundary gate fixtures passed.'
