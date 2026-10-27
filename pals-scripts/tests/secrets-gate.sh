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
  git -C "${repository}" config user.name 'Secret gate fixture'
  git -C "${repository}" config user.email 'fixture@example.invalid'
  printf '%s\n' 'clean fixture' >"${repository}/clean.txt"
  printf '%s\n' 'API_KEY=replace-with-local-placeholder' >"${repository}/.env.example"
  git -C "${repository}" add clean.txt .env.example
  git -C "${repository}" commit -qm 'Clean initial fixture'
}

make_fixture() {
  local fixture="$1" child_oid
  init_repository "${fixture}"
  init_repository "${fixture}/pals-api"
  child_oid="$(git -C "${fixture}/pals-api" rev-parse HEAD)"
  git -C "${fixture}" update-index --add --cacheinfo "160000,${child_oid},pals-api"
  git config --file "${fixture}/.gitmodules" submodule.pals-api.path pals-api
  git config --file "${fixture}/.gitmodules" submodule.pals-api.url https://example.invalid/pals-api.git
  git -C "${fixture}" add .gitmodules
  git -C "${fixture}" commit -qm 'Declare required implementation repository'
}

expect_result() {
  local expected="$1" fixture="$2" output rc
  shift 2
  set +e
  output="$(PALS_ROOT="${fixture}" bash "${GATE}" "$@" 2>&1)"
  rc=$?
  set -e
  [ "${rc}" -eq "${expected}" ] || {
    printf 'Unexpected secret gate exit: expected=%s actual=%s fixture=%s\n' "${expected}" "${rc}" "${fixture##*/}" >&2
    exit 1
  }
  # Restrict the complete output, so neither matched values nor filenames leak.
  if [ "${expected}" -eq 0 ]; then
    [[ "${output}" =~ ^secrets:\ PASS\ scope=(parent|all)\ history=(true|false)$ ]] || {
      printf '%s\n' 'Secret pass output was not content-free and scope-labelled.' >&2
      exit 1
    }
  else
    [[ "${output}" =~ ^secrets:\ FAIL\ violations=[0-9]+\ incomplete=[0-9]+\ scope=(parent|all|invalid)\ history=(true|false)$ ]] || {
      printf '%s\n' 'Secret failure output was not content-free and scope-labelled.' >&2
      exit 1
    }
  fi
}

# Build detector fixtures at runtime; no actual credentials belong in tests.
key_suffix='ABCDEFGHIJKLMNOP'
access_key="AKIA${key_suffix}"
token_prefix='ghp'
history_token="${token_prefix}_8nV4yG7rD2mQ9jL5cB3xK6wF1zH0sA4eT7uP9vR2"

valid_fixture="${TMP_DIR}/valid"
make_fixture "${valid_fixture}"
expect_result 0 "${valid_fixture}"
expect_result 0 "${valid_fixture}" --scope parent
expect_result 2 "${valid_fixture}" --scope
expect_result 2 "${valid_fixture}" --scope invalid
expect_result 2 "${valid_fixture}" --unknown

missing_fixture="${TMP_DIR}/missing-required-child"
make_fixture "${missing_fixture}"
rm -rf "${missing_fixture}/pals-api"
expect_result 2 "${missing_fixture}"
expect_result 0 "${missing_fixture}" --scope parent

undeclared_fixture="${TMP_DIR}/undeclared-gitlink"
make_fixture "${undeclared_fixture}"
git config --file "${undeclared_fixture}/.gitmodules" --remove-section submodule.pals-api
expect_result 2 "${undeclared_fixture}"

for variant in missing malformed traversal; do
  fixture="${TMP_DIR}/modules-${variant}"
  init_repository "${fixture}"
  case "${variant}" in
    malformed) printf '%s\n' '[broken' >"${fixture}/.gitmodules" ;;
    traversal) git config --file "${fixture}/.gitmodules" submodule.outside.path ../outside ;;
  esac
  expect_result 2 "${fixture}"
done

child_fixture="${TMP_DIR}/initialized-child-secret"
make_fixture "${child_fixture}"
printf '%s\n' "${access_key}" >"${child_fixture}/pals-api/credential.txt"
git -C "${child_fixture}/pals-api" add credential.txt
expect_result 1 "${child_fixture}"

inline_fixture="${TMP_DIR}/inline-draft-secret"
make_fixture "${inline_fixture}"
mkdir -p "${inline_fixture}/pals-draft-admin"
printf '%s\n' "${access_key}" >"${inline_fixture}/pals-draft-admin/credential.txt"
git -C "${inline_fixture}" add pals-draft-admin/credential.txt
expect_result 1 "${inline_fixture}"

separate_fixture="${TMP_DIR}/separate-draft-secret"
make_fixture "${separate_fixture}"
init_repository "${separate_fixture}/pals-draft-admin"
printf '%s\n' "${access_key}" >"${separate_fixture}/pals-draft-admin/credential.txt"
git -C "${separate_fixture}/pals-draft-admin" add credential.txt
expect_result 1 "${separate_fixture}"

index_fixture="${TMP_DIR}/index-only-secret"
make_fixture "${index_fixture}"
printf '%s\n' "${access_key}" >"${index_fixture}/credential.txt"
git -C "${index_fixture}" add credential.txt
printf '%s\n' 'clean worktree replacement' >"${index_fixture}/credential.txt"
expect_result 1 "${index_fixture}"

worktree_fixture="${TMP_DIR}/worktree-only-secret"
make_fixture "${worktree_fixture}"
printf '%s\n' 'clean index value' >"${worktree_fixture}/credential.txt"
git -C "${worktree_fixture}" add credential.txt
printf '%s\n' "${access_key}" >"${worktree_fixture}/credential.txt"
expect_result 1 "${worktree_fixture}"

for sensitive_path in .env.production .aws/credentials service-account-production.json service_account.json project-firebase-adminsdk-local.json local.tfstate local.tfstate.backup production.tfvars production.tfvars.json local.key; do
  path_fixture="${TMP_DIR}/sensitive-${sensitive_path//\//-}"
  make_fixture "${path_fixture}"
  mkdir -p "${path_fixture}/$(dirname "${sensitive_path}")"
  printf '%s\n' 'non-secret contents still forbidden by path' >"${path_fixture}/${sensitive_path}"
  git -C "${path_fixture}" add "${sensitive_path}"
  expect_result 1 "${path_fixture}"
done

for example_path in production.example.tfvars production.example.tfvars.json production.template.tfvars production.template.tfvars.json production.tfvars.example .env.playwright.example; do
  example_fixture="${TMP_DIR}/example-${example_path}"
  make_fixture "${example_fixture}"
  printf '%s\n' 'region = "local-placeholder"' >"${example_fixture}/${example_path}"
  git -C "${example_fixture}" add "${example_path}"
  expect_result 0 "${example_fixture}"
  printf 'access_key = "%s"\n' "${access_key}" >"${example_fixture}/${example_path}"
  git -C "${example_fixture}" add "${example_path}"
  expect_result 1 "${example_fixture}"
done

database_fixture="${TMP_DIR}/database-credential"
make_fixture "${database_fixture}"
database_password='sufficientlylongdatabasecredential'
printf 'postgresql://worker:%s@db.private.example/pals\n' "${database_password}" >"${database_fixture}/pals-api/database.txt"
git -C "${database_fixture}/pals-api" add database.txt
expect_result 1 "${database_fixture}"

incomplete_fixture="${TMP_DIR}/incomplete-repository"
make_fixture "${incomplete_fixture}"
rm -rf "${incomplete_fixture}/pals-api/.git"
printf '%s\n' 'invalid gitdir' >"${incomplete_fixture}/pals-api/.git"
expect_result 2 "${incomplete_fixture}"

# Missing tools and tool errors must never turn an incomplete scan into success.
missing_tools="${TMP_DIR}/missing-tools"
mkdir -p "${missing_tools}"
for required_tool in bash dirname git mktemp rm tr; do
  ln -s "$(command -v "${required_tool}")" "${missing_tools}/${required_tool}"
done
PATH="${missing_tools}" expect_result 2 "${valid_fixture}" --scope parent --history
failure_tools="${TMP_DIR}/failure-tools"
mkdir -p "${failure_tools}"
printf '%s\n' '#!/bin/sh' 'echo scanner-error-with-sensitive-details >&2' 'exit 3' >"${failure_tools}/gitleaks"
chmod +x "${failure_tools}/gitleaks"
PATH="${failure_tools}:${PATH}" expect_result 2 "${valid_fixture}" --scope parent --history

if ! command -v gitleaks >/dev/null 2>&1; then
  printf '%s\n' 'History fixtures require the real Gitleaks v8 executable; they were not run.' >&2
  exit 2
fi
expect_result 0 "${valid_fixture}" --history

history_fixture="${TMP_DIR}/deleted-history-secret"
make_fixture "${history_fixture}"
printf 'github_token = "%s"\n' "${history_token}" >"${history_fixture}/old-settings.txt"
git -C "${history_fixture}" add old-settings.txt
git -C "${history_fixture}" commit -qm 'Historical secret fixture'
git -C "${history_fixture}" rm -q old-settings.txt
git -C "${history_fixture}" commit -qm 'Delete secret fixture'
expect_result 0 "${history_fixture}"
expect_result 1 "${history_fixture}" --history

child_history_fixture="${TMP_DIR}/deleted-child-history-secret"
make_fixture "${child_history_fixture}"
printf 'github_token = "%s"\n' "${history_token}" >"${child_history_fixture}/pals-api/old-settings.txt"
git -C "${child_history_fixture}/pals-api" add old-settings.txt
git -C "${child_history_fixture}/pals-api" commit -qm 'Historical child secret fixture'
git -C "${child_history_fixture}/pals-api" rm -q old-settings.txt
git -C "${child_history_fixture}/pals-api" commit -qm 'Delete child secret fixture'
expect_result 0 "${child_history_fixture}" --scope parent --history
expect_result 1 "${child_history_fixture}" --history

historical_path_fixture="${TMP_DIR}/deleted-history-path"
make_fixture "${historical_path_fixture}"
printf '%s\n' 'no secret contents' >"${historical_path_fixture}/service-account-old.json"
git -C "${historical_path_fixture}" add service-account-old.json
git -C "${historical_path_fixture}" commit -qm 'Historical forbidden filename'
git -C "${historical_path_fixture}" rm -q service-account-old.json
git -C "${historical_path_fixture}" commit -qm 'Remove historical file'
expect_result 1 "${historical_path_fixture}" --history

for ref_type in branch tag; do
  fixture="${TMP_DIR}/history-${ref_type}"
  make_fixture "${fixture}"
  clean_oid="$(git -C "${fixture}" rev-parse HEAD)"
  printf 'github_token = "%s"\n' "${history_token}" >"${fixture}/branch-settings.txt"
  git -C "${fixture}" add branch-settings.txt
  git -C "${fixture}" commit -qm 'Secret on separate ref'
  git -C "${fixture}" "${ref_type}" historical-secret
  git -C "${fixture}" checkout -q --detach "${clean_oid}"
  # Drop the original branch so the test depends only on the requested ref.
  for branch in $(git -C "${fixture}" for-each-ref --format='%(refname:short)' refs/heads); do
    [ "${branch}" = historical-secret ] || git -C "${fixture}" branch -D "${branch}" >/dev/null
  done
  expect_result 0 "${fixture}"
  expect_result 1 "${fixture}" --history
done

# A parent gitlink is a scan root even when its child commit no longer has a
# child branch/tag. Cover both the current index pin and superseded parent pins.
for pin_scope in index historical; do
  fixture="${TMP_DIR}/unreachable-${pin_scope}-pin"
  make_fixture "${fixture}"
  child="${fixture}/pals-api"
  clean_oid="$(git -C "${child}" rev-parse HEAD)"
  old_branch="$(git -C "${child}" symbolic-ref --short HEAD)"
  printf 'github_token = "%s"\n' "${history_token}" >"${child}/pinned-settings.txt"
  git -C "${child}" add pinned-settings.txt
  git -C "${child}" commit -qm 'Secret reachable only through parent pin'
  pinned_oid="$(git -C "${child}" rev-parse HEAD)"
  git -C "${fixture}" update-index --cacheinfo "160000,${pinned_oid},pals-api"
  if [ "${pin_scope}" = historical ]; then
    git -C "${fixture}" commit -qm 'Historical parent pin'
    git -C "${fixture}" update-index --cacheinfo "160000,${clean_oid},pals-api"
    git -C "${fixture}" commit -qm 'Return parent to clean pin'
  fi
  git -C "${child}" checkout -q --detach "${clean_oid}"
  git -C "${child}" branch -D "${old_branch}" >/dev/null
  expect_result 0 "${fixture}"
  expect_result 1 "${fixture}" --history
done

missing_pin_fixture="${TMP_DIR}/missing-pin-object"
make_fixture "${missing_pin_fixture}"
missing_oid="$(printf '%040d' 1)"
git -C "${missing_pin_fixture}" update-index --cacheinfo "160000,${missing_oid},pals-api"
expect_result 2 "${missing_pin_fixture}" --history
git -C "${missing_pin_fixture}" commit -qm 'Historical unavailable pin'
available_oid="$(git -C "${missing_pin_fixture}/pals-api" rev-parse HEAD)"
git -C "${missing_pin_fixture}" update-index --cacheinfo "160000,${available_oid},pals-api"
git -C "${missing_pin_fixture}" commit -qm 'Restore available index pin'
expect_result 2 "${missing_pin_fixture}" --history

removed_module_fixture="${TMP_DIR}/unmapped-historical-module"
make_fixture "${removed_module_fixture}"
git -C "${removed_module_fixture}" rm -q --cached pals-api
git config --file "${removed_module_fixture}/.gitmodules" --remove-section submodule.pals-api
git config --file "${removed_module_fixture}/.gitmodules" submodule.other.path other
git config --file "${removed_module_fixture}/.gitmodules" submodule.other.url https://example.invalid/other.git
init_repository "${removed_module_fixture}/other"
other_oid="$(git -C "${removed_module_fixture}/other" rev-parse HEAD)"
git -C "${removed_module_fixture}" update-index --add --cacheinfo "160000,${other_oid},other"
git -C "${removed_module_fixture}" add .gitmodules
git -C "${removed_module_fixture}" commit -qm 'Replace mapped module'
# An initialized retired module is scanned when history is requested.
expect_result 0 "${removed_module_fixture}" --history
printf 'github_token = "%s"\n' "${history_token}" >"${removed_module_fixture}/pals-api/retired-settings.txt"
git -C "${removed_module_fixture}/pals-api" add retired-settings.txt
git -C "${removed_module_fixture}/pals-api" commit -qm 'Secret in retired module'
git -C "${removed_module_fixture}/pals-api" rm -q retired-settings.txt
git -C "${removed_module_fixture}/pals-api" commit -qm 'Delete retired module secret'
expect_result 0 "${removed_module_fixture}"
expect_result 1 "${removed_module_fixture}" --history
# A missing or escaped retired checkout cannot count as successful coverage.
rm -rf "${removed_module_fixture}/pals-api"
expect_result 2 "${removed_module_fixture}" --history
ln -s "${valid_fixture}/pals-api" "${removed_module_fixture}/pals-api"
expect_result 2 "${removed_module_fixture}" --history

# Merge-result-only content is absent from both parent commits. Default git log
# omits merge patches, so the scanner must explicitly request -m.
merge_fixture="${TMP_DIR}/merge-only-secret"
make_fixture "${merge_fixture}"
first_parent="$(git -C "${merge_fixture}" rev-parse HEAD)"
clean_tree="$(git -C "${merge_fixture}" rev-parse HEAD^{tree})"
second_parent="$(printf '%s\n' 'Independent merge parent' | git -C "${merge_fixture}" commit-tree "${clean_tree}" -p "${first_parent}")"
printf 'github_token = "%s"\n' "${history_token}" >"${merge_fixture}/merge-settings.txt"
git -C "${merge_fixture}" add merge-settings.txt
secret_tree="$(git -C "${merge_fixture}" write-tree)"
merge_oid="$(printf '%s\n' 'Merge result contains secret' | git -C "${merge_fixture}" commit-tree "${secret_tree}" -p "${first_parent}" -p "${second_parent}")"
git -C "${merge_fixture}" update-ref HEAD "${merge_oid}"
git -C "${merge_fixture}" rm -q merge-settings.txt
git -C "${merge_fixture}" commit -qm 'Remove merge-only secret'
expect_result 0 "${merge_fixture}"
expect_result 1 "${merge_fixture}" --history

# Repository-controlled allowlists must not suppress the publication history gate.
printf '%s\n' 'title = "Disable every detector"' >"${history_fixture}/.gitleaks.toml"
printf '%s\n' '*' >"${history_fixture}/.gitleaksignore"
expect_result 1 "${history_fixture}" --history

shallow_fixture="${TMP_DIR}/shallow"
git clone -q --depth 1 "file://${valid_fixture}" "${shallow_fixture}"
expect_result 2 "${shallow_fixture}" --scope parent --history

empty_fixture="${TMP_DIR}/empty-history"
mkdir -p "${empty_fixture}"
git -C "${empty_fixture}" init -q
expect_result 2 "${empty_fixture}" --scope parent --history

printf '%s\n' 'Secret gate fixtures passed (including real Gitleaks history scans).'
