#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
MAKEFILE="${ROOT_DIR}/Makefile"
HELPER_SOURCE="${ROOT_DIR}/pals-scripts/bootstrap-pals-scripts-python.sh"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-scripts-bootstrap-test.XXXXXX")"
REAL_MV="$(command -v mv)"
REAL_MAKE="$(command -v make)"
trap 'rm -rf "${TMP_DIR}"' EXIT

fail() {
  printf '%s\n' "$1" >&2
  exit 1
}

assert_make_contract() {
  grep -Fqx \
    '.venv-pals-scripts/bin/python: pals-scripts/requirements.txt pals-scripts/bootstrap-pals-scripts-python.sh' \
    "${MAKEFILE}" || fail 'Exact pals-scripts Python target header is missing.'
  grep -Fqx $'\t@./pals-scripts/bootstrap-pals-scripts-python.sh' "${MAKEFILE}" \
    || fail 'Exact pals-scripts Python target recipe is missing.'
  grep -Fqx 'pals-scripts-test: .venv-pals-scripts/bin/python' "${MAKEFILE}" \
    || fail 'pals-scripts-test does not have the exact interpreter prerequisite.'
  grep -Fqx 'repository-gates:' "${MAKEFILE}" \
    || fail 'repository-gates target is missing.'
  if grep -Eq '^[A-Z][A-Z0-9_]*[[:space:]]+(\?=|:=|=).*\.venv-pals-scripts|^[A-Z][A-Z0-9_]*[[:space:]]+(\?=|:=|=).*bootstrap-pals-scripts-python' "${MAKEFILE}"; then
    fail 'Make assignment indirection controls the pals-scripts interpreter/helper.'
  fi
  [ "$(grep -Fxc '.venv-pals-scripts/bin/python: pals-scripts/requirements.txt pals-scripts/bootstrap-pals-scripts-python.sh' "${MAKEFILE}")" -eq 1 ] \
    || fail 'The pals-scripts Python target header is not unique.'
  [ "$(grep -Ec '^\.venv-pals-scripts/bin/python:' "${MAKEFILE}")" -eq 1 ] \
    || fail 'The pals-scripts Python target has another rule or prerequisite set.'
  [ "$(grep -Ec '^pals-scripts-test:' "${MAKEFILE}")" -eq 1 ] \
    && [ "$(grep -Ec '^repository-gates:' "${MAKEFILE}")" -eq 1 ] \
    || fail 'A pals-scripts aggregate target header is duplicated.'
  awk '
    $0 == ".venv-pals-scripts/bin/python: pals-scripts/requirements.txt pals-scripts/bootstrap-pals-scripts-python.sh" {
      headers++
      active = 1
      next
    }
    active && /^\t/ {
      recipes++
      if ($0 != "\t@./pals-scripts/bootstrap-pals-scripts-python.sh") bad = 1
      next
    }
    active { active = 0 }
    END { exit(headers == 1 && recipes == 1 && !bad ? 0 : 1) }
  ' "${MAKEFILE}" || fail 'The pals-scripts Python target must have the sole exact recipe.'
}

make_shims() {
  local fixture="$1"
  mkdir -p "${fixture}/bin" "${fixture}/pals-scripts"
  cp "${HELPER_SOURCE}" "${fixture}/pals-scripts/bootstrap-pals-scripts-python.sh"
  chmod +x "${fixture}/pals-scripts/bootstrap-pals-scripts-python.sh"
  printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'if [ "${1:-}" = -c ]; then' \
    '  [ "${PALS_TEST_CPYTHON_OK:-1}" = 1 ] && [ "${PALS_TEST_VERSION_OK:-1}" = 1 ]' \
    '  exit' \
    'fi' \
    'if [ "${1:-}" = -m ] && [ "${2:-}" = venv ]; then' \
    '  stage="$3"' \
    '  mkdir -p "${stage}/bin"' \
    '  cp "${PALS_TEST_STAGE_PYTHON}" "${stage}/bin/python"' \
    '  chmod +x "${stage}/bin/python"' \
    '  if [ -n "${PALS_TEST_SIGNAL_AFTER_VENV:-}" ]; then kill -s "${PALS_TEST_SIGNAL_AFTER_VENV}" "$PPID"; fi' \
    '  exit 0' \
    'fi' \
    'exit 97' \
    >"${fixture}/bin/python3"
  chmod +x "${fixture}/bin/python3"

  printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'if [ "${1:-}" = -m ] && [ "${2:-}" = pip ] && [ "${3:-}" = install ]; then' \
    '  [ "${PALS_TEST_PIP_FAIL:-0}" = 0 ]' \
    '  exit' \
    'fi' \
    'if [ "${1:-}" = -c ]; then [ "${PALS_TEST_IMPORT_OK:-1}" = 1 ]; exit; fi' \
    'exit 98' \
    >"${fixture}/stage-python"
  chmod +x "${fixture}/stage-python"

  printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'case "${1:-}:${2:-}" in' \
    '  .venv-pals-scripts:.venv-pals-scripts.old.*)' \
    "    '${REAL_MV}' \"\$@\"" \
    '    if [ -n "${PALS_TEST_SIGNAL_AFTER_OLD_MOVE:-}" ]; then kill -s "${PALS_TEST_SIGNAL_AFTER_OLD_MOVE}" "$PPID"; fi' \
    '    exit 0' \
    '    ;;' \
    '  .venv-pals-scripts.stage.*:.venv-pals-scripts)' \
    '    [ "${PALS_TEST_FAIL_STAGE_PUBLISH:-0}" = 0 ] || exit 1' \
    "    '${REAL_MV}' \"\$@\"" \
    '    if [ -n "${PALS_TEST_SIGNAL_AFTER_PUBLISH:-}" ]; then kill -s "${PALS_TEST_SIGNAL_AFTER_PUBLISH}" "$PPID"; fi' \
    '    exit 0' \
    '    ;;' \
    'esac' \
    "exec '${REAL_MV}' \"\$@\"" \
    >"${fixture}/bin/mv"
  chmod +x "${fixture}/bin/mv"
}

make_target_fixture() {
  local fixture="$1"
  mkdir -p "${fixture}/pals-scripts/tests"
  make_shims "${fixture}"
  cp "${MAKEFILE}" "${fixture}/Makefile"
  cp "${ROOT_DIR}/pals-scripts/requirements.txt" "${fixture}/pals-scripts/requirements.txt"
  printf '%s\n' '#!/bin/sh' 'set -eu' 'printf "test\n" >>"${PALS_TEST_RECIPE_LOG:?}"' \
    >"${fixture}/pals-scripts/tests/fixture.sh"
  chmod +x "${fixture}/pals-scripts/tests/fixture.sh"
  for gate in check-secrets.sh check-public-agent-boundary.sh; do
    printf '%s\n' '#!/bin/sh' 'set -eu' 'printf "gate\n" >>"${PALS_TEST_RECIPE_LOG:?}"' \
      >"${fixture}/pals-scripts/${gate}"
    chmod +x "${fixture}/pals-scripts/${gate}"
  done
}

run_make_target() {
  local fixture="$1"
  shift
  (
    cd "${fixture}"
    PATH="${fixture}/bin:${PATH}" \
      PALS_TEST_STAGE_PYTHON="${fixture}/stage-python" \
      PALS_TEST_RECIPE_LOG="${fixture}/recipe.log" \
      "${REAL_MAKE}" -s "$@"
  )
}

run_helper() {
  local fixture="$1"
  shift
  (
    cd "${fixture}"
    PATH="${fixture}/bin:${PATH}" \
      PALS_TEST_STAGE_PYTHON="${fixture}/stage-python" \
      "$@" bash "${fixture}/pals-scripts/bootstrap-pals-scripts-python.sh"
  )
}

expect_failure() {
  set +e
  "$@" >/dev/null 2>&1
  local rc=$?
  set -e
  [ "${rc}" -ne 0 ] || fail 'Expected bootstrap helper failure.'
}

assert_make_contract
[ -x "${HELPER_SOURCE}" ] || fail 'Bootstrap helper is missing or not executable.'

make_scripts_fixture="${TMP_DIR}/make-pals-scripts-test"
make_target_fixture "${make_scripts_fixture}"
run_make_target "${make_scripts_fixture}" pals-scripts-test
[ "$(cat "${make_scripts_fixture}/recipe.log")" = test ] \
  || fail 'The clean pals-scripts-test fixture did not execute its test recipe exactly once.'

make_gates_fixture="${TMP_DIR}/make-repository-gates"
make_target_fixture "${make_gates_fixture}"
run_make_target "${make_gates_fixture}" repository-gates
[ "$(wc -l <"${make_gates_fixture}/recipe.log" | tr -d ' ')" -eq 2 ] \
  || fail 'The clean repository-gates fixture did not execute both gates exactly once.'

make_install_failure_fixture="${TMP_DIR}/make-install-failure"
make_target_fixture "${make_install_failure_fixture}"
expect_failure env PALS_TEST_PIP_FAIL=1 bash -c \
  'cd "$1" && PATH="$1/bin:$PATH" PALS_TEST_STAGE_PYTHON="$1/stage-python" PALS_TEST_RECIPE_LOG="$1/recipe.log" "$2" -s pals-scripts-test' \
  _ "${make_install_failure_fixture}" "${REAL_MAKE}"
[ ! -e "${make_install_failure_fixture}/recipe.log" ] \
  || fail 'A Make provisioning failure executed the dependent test recipe.'

clean_fixture="${TMP_DIR}/clean"
mkdir -p "${clean_fixture}"
make_shims "${clean_fixture}"
run_helper "${clean_fixture}" env
[ -x "${clean_fixture}/.venv-pals-scripts/bin/python" ] \
  || fail 'Clean bootstrap did not publish the final interpreter.'
compgen -G "${clean_fixture}/.venv-pals-scripts.stage.*" >/dev/null \
  && fail 'Clean bootstrap left a stage directory.'
compgen -G "${clean_fixture}/.venv-pals-scripts.old.*" >/dev/null \
  && fail 'Clean bootstrap left an old directory.'

install_failure_fixture="${TMP_DIR}/install-failure"
mkdir -p "${install_failure_fixture}/.venv-pals-scripts"
printf '%s\n' preserved >"${install_failure_fixture}/.venv-pals-scripts/marker"
make_shims "${install_failure_fixture}"
expect_failure run_helper "${install_failure_fixture}" env PALS_TEST_PIP_FAIL=1
[ "$(cat "${install_failure_fixture}/.venv-pals-scripts/marker")" = preserved ] \
  || fail 'Install failure damaged the last complete target.'
compgen -G "${install_failure_fixture}/.venv-pals-scripts.stage.*" >/dev/null \
  && fail 'Install failure left a stage directory.'
run_helper "${install_failure_fixture}" env PALS_TEST_PIP_FAIL=0
[ -x "${install_failure_fixture}/.venv-pals-scripts/bin/python" ] \
  || fail 'Retry did not publish the interpreter.'

for signal in HUP INT TERM; do
  signal_fixture="${TMP_DIR}/signal-${signal}"
  mkdir -p "${signal_fixture}"
  make_shims "${signal_fixture}"
  expect_failure run_helper "${signal_fixture}" env PALS_TEST_SIGNAL_AFTER_VENV="${signal}"
  compgen -G "${signal_fixture}/.venv-pals-scripts.stage.*" >/dev/null \
    && fail "${signal} left a stage directory."
done

non_cpython_fixture="${TMP_DIR}/non-cpython"
mkdir -p "${non_cpython_fixture}"
make_shims "${non_cpython_fixture}"
expect_failure run_helper "${non_cpython_fixture}" env PALS_TEST_CPYTHON_OK=0 PALS_TEST_VERSION_OK=1

old_python_fixture="${TMP_DIR}/old-python"
mkdir -p "${old_python_fixture}"
make_shims "${old_python_fixture}"
expect_failure run_helper "${old_python_fixture}" env PALS_TEST_CPYTHON_OK=1 PALS_TEST_VERSION_OK=0

import_failure_fixture="${TMP_DIR}/import-failure"
mkdir -p "${import_failure_fixture}"
make_shims "${import_failure_fixture}"
expect_failure run_helper "${import_failure_fixture}" env PALS_TEST_IMPORT_OK=0
[ ! -e "${import_failure_fixture}/.venv-pals-scripts" ] \
  || fail 'Import/version verification failure published an interpreter.'

restore_fixture="${TMP_DIR}/restore-old"
mkdir -p "${restore_fixture}/.venv-pals-scripts.old.41"
printf '%s\n' restored >"${restore_fixture}/.venv-pals-scripts.old.41/marker"
make_shims "${restore_fixture}"
expect_failure run_helper "${restore_fixture}" env PALS_TEST_CPYTHON_OK=0
[ "$(cat "${restore_fixture}/.venv-pals-scripts/marker")" = restored ] \
  || fail 'A sole old directory was not restored before provisioning.'

stale_fixture="${TMP_DIR}/stale-stage"
mkdir -p "${stale_fixture}/.venv-pals-scripts.stage.42"
make_shims "${stale_fixture}"
expect_failure run_helper "${stale_fixture}" env PALS_TEST_CPYTHON_OK=0
[ ! -e "${stale_fixture}/.venv-pals-scripts.stage.42" ] \
  || fail 'A stale stage directory was not removed on startup.'

final_fixture="${TMP_DIR}/final-with-old"
mkdir -p "${final_fixture}/.venv-pals-scripts" "${final_fixture}/.venv-pals-scripts.old.43"
printf '%s\n' final >"${final_fixture}/.venv-pals-scripts/marker"
make_shims "${final_fixture}"
expect_failure run_helper "${final_fixture}" env PALS_TEST_CPYTHON_OK=0
[ "$(cat "${final_fixture}/.venv-pals-scripts/marker")" = final ] \
  || fail 'Startup recovery replaced an existing final target.'
[ ! -e "${final_fixture}/.venv-pals-scripts.old.43" ] \
  || fail 'Startup recovery retained an old directory beside a final target.'

multiple_old_fixture="${TMP_DIR}/multiple-old"
mkdir -p "${multiple_old_fixture}/.venv-pals-scripts.old.44" \
  "${multiple_old_fixture}/.venv-pals-scripts.old.45"
make_shims "${multiple_old_fixture}"
expect_failure run_helper "${multiple_old_fixture}" env
[ -d "${multiple_old_fixture}/.venv-pals-scripts.old.44" ] \
  && [ -d "${multiple_old_fixture}/.venv-pals-scripts.old.45" ] \
  || fail 'Ambiguous old directories were deleted.'

manual_residue_fixture="${TMP_DIR}/manual-residue"
mkdir -p "${manual_residue_fixture}/.venv-pals-scripts.stage.manual-backup" \
  "${manual_residue_fixture}/.venv-pals-scripts.old.manual-backup" \
  "${manual_residue_fixture}/manual-link-target"
printf '%s\n' manual >"${manual_residue_fixture}/.venv-pals-scripts.stage.manual-backup/marker"
printf '%s\n' manual >"${manual_residue_fixture}/.venv-pals-scripts.old.manual-backup/marker"
printf '%s\n' manual >"${manual_residue_fixture}/.venv-pals-scripts.stage.77"
ln -s manual-link-target "${manual_residue_fixture}/.venv-pals-scripts.old.78"
make_shims "${manual_residue_fixture}"
expect_failure run_helper "${manual_residue_fixture}" env PALS_TEST_CPYTHON_OK=0
[ "$(cat "${manual_residue_fixture}/.venv-pals-scripts.stage.manual-backup/marker")" = manual ] \
  && [ "$(cat "${manual_residue_fixture}/.venv-pals-scripts.old.manual-backup/marker")" = manual ] \
  && [ "$(cat "${manual_residue_fixture}/.venv-pals-scripts.stage.77")" = manual ] \
  && [ -L "${manual_residue_fixture}/.venv-pals-scripts.old.78" ] \
  || fail 'Bootstrap touched a non-PID manual residue.'

for signal in HUP INT TERM; do
  between_moves_fixture="${TMP_DIR}/between-moves-${signal}"
  mkdir -p "${between_moves_fixture}/.venv-pals-scripts"
  printf '%s\n' prior >"${between_moves_fixture}/.venv-pals-scripts/marker"
  make_shims "${between_moves_fixture}"
  expect_failure run_helper "${between_moves_fixture}" env PALS_TEST_SIGNAL_AFTER_OLD_MOVE="${signal}"
  [ "$(cat "${between_moves_fixture}/.venv-pals-scripts/marker")" = prior ] \
    || fail "${signal} between publication moves did not restore the prior interpreter."
  compgen -G "${between_moves_fixture}/.venv-pals-scripts.stage.*" >/dev/null \
    && fail "${signal} between publication moves left a stage directory."

  after_publish_fixture="${TMP_DIR}/after-publish-${signal}"
  mkdir -p "${after_publish_fixture}/.venv-pals-scripts"
  printf '%s\n' prior >"${after_publish_fixture}/.venv-pals-scripts/marker"
  make_shims "${after_publish_fixture}"
  expect_failure run_helper "${after_publish_fixture}" env PALS_TEST_SIGNAL_AFTER_PUBLISH="${signal}"
  [ -x "${after_publish_fixture}/.venv-pals-scripts/bin/python" ] \
    || fail "${signal} after publication removed the complete new interpreter."
  compgen -G "${after_publish_fixture}/.venv-pals-scripts.old.*" >/dev/null \
    && fail "${signal} after publication left an old directory."
done

publish_failure_fixture="${TMP_DIR}/publish-failure"
mkdir -p "${publish_failure_fixture}/.venv-pals-scripts"
printf '%s\n' prior >"${publish_failure_fixture}/.venv-pals-scripts/marker"
make_shims "${publish_failure_fixture}"
expect_failure run_helper "${publish_failure_fixture}" env PALS_TEST_FAIL_STAGE_PUBLISH=1
[ "$(cat "${publish_failure_fixture}/.venv-pals-scripts/marker")" = prior ] \
  || fail 'Publication failure did not restore the prior complete target.'

printf '%s\n' 'pals-scripts Python bootstrap tests passed.'
