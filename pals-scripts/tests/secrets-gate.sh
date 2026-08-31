#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
GATE="${ROOT_DIR}/pals-scripts/check-secrets.sh"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-secrets-test.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

init_repository() {
  local repository="$1"
  mkdir -p "${repository}"
  git -C "${repository}" init -q
  printf '%s\n' 'clean fixture' >"${repository}/clean.txt"
  printf '%s\n' 'API_KEY=replace-with-local-placeholder' >"${repository}/.env.example"
  git -C "${repository}" add clean.txt .env.example
}

make_fixture() {
  local fixture="$1"
  init_repository "${fixture}"
  init_repository "${fixture}/pals-draft-admin"
}

run_gate() {
  PALS_ROOT="$1" bash "${GATE}"
}

expect_pass() {
  local fixture="$1"
  local output
  output="$(run_gate "${fixture}" 2>&1)" || {
    printf '%s\n' 'Expected secret fixture to pass.' >&2
    exit 1
  }
  [ "${output}" = 'secrets: PASS' ] || {
    printf '%s\n' 'Secret pass output was not content-free.' >&2
    exit 1
  }
}

expect_fail() {
  local fixture="$1"
  local forbidden_output="${2:-}"
  local output rc
  set +e
  output="$(run_gate "${fixture}" 2>&1)"
  rc=$?
  set -e
  [ "${rc}" -ne 0 ] || {
    printf '%s\n' 'Expected secret fixture to fail.' >&2
    exit 1
  }
  case "${output}" in
    'secrets: FAIL violations='*' incomplete='*) ;;
    *)
      printf '%s\n' 'Secret failure output was not content-free.' >&2
      exit 1
      ;;
  esac
  if [ -n "${forbidden_output}" ]; then
    case "${output}" in
      *"${forbidden_output}"*)
        printf '%s\n' 'Secret gate exposed matched content.' >&2
        exit 1
        ;;
    esac
  fi
}

key_suffix='ABCDEFGHIJKLMNOP'
access_key="AKIA${key_suffix}"

valid_fixture="${TMP_DIR}/valid"
make_fixture "${valid_fixture}"
expect_pass "${valid_fixture}"

child_fixture="${TMP_DIR}/initialized-child-secret"
make_fixture "${child_fixture}"
printf '%s\n' "${access_key}" >"${child_fixture}/pals-draft-admin/credential.txt"
git -C "${child_fixture}/pals-draft-admin" add credential.txt
expect_fail "${child_fixture}" "${access_key}"

index_fixture="${TMP_DIR}/index-only-secret"
make_fixture "${index_fixture}"
printf '%s\n' "${access_key}" >"${index_fixture}/credential.txt"
git -C "${index_fixture}" add credential.txt
printf '%s\n' 'clean worktree replacement' >"${index_fixture}/credential.txt"
expect_fail "${index_fixture}" "${access_key}"

worktree_fixture="${TMP_DIR}/worktree-only-secret"
make_fixture "${worktree_fixture}"
printf '%s\n' 'clean index value' >"${worktree_fixture}/credential.txt"
git -C "${worktree_fixture}" add credential.txt
printf '%s\n' "${access_key}" >"${worktree_fixture}/credential.txt"
expect_fail "${worktree_fixture}" "${access_key}"

env_fixture="${TMP_DIR}/tracked-env"
make_fixture "${env_fixture}"
printf '%s\n' 'MODE=local' >"${env_fixture}/.env.production"
git -C "${env_fixture}" add .env.production
expect_fail "${env_fixture}" '.env.production'

database_fixture="${TMP_DIR}/database-credential"
make_fixture "${database_fixture}"
database_password='sufficientlylongdatabasecredential'
printf 'postgresql://worker:%s@db.private.example/pals\n' "${database_password}" >"${database_fixture}/pals-draft-admin/database.txt"
git -C "${database_fixture}/pals-draft-admin" add database.txt
expect_fail "${database_fixture}" "${database_password}"

incomplete_fixture="${TMP_DIR}/incomplete-repository"
init_repository "${incomplete_fixture}"
mkdir -p "${incomplete_fixture}/pals-api"
printf '%s\n' 'invalid gitdir' >"${incomplete_fixture}/pals-api/.git"
expect_fail "${incomplete_fixture}"

printf '%s\n' 'Secret gate fixtures passed.'
