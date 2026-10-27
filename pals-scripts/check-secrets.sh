#!/usr/bin/env bash
set -uo pipefail

LC_ALL=C
export LC_ALL
GIT_NO_REPLACE_OBJECTS=1
export GIT_NO_REPLACE_OBJECTS

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
ROOT_DIR="${PALS_ROOT:-${SCRIPT_ROOT}}"

violations=0
incomplete=0
scope=all
history=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --scope)
      if [ "$#" -lt 2 ]; then incomplete=$((incomplete + 1)); break; fi
      scope="$2"
      shift 2
      ;;
    --history) history=true; shift ;;
    *) incomplete=$((incomplete + 1)); shift ;;
  esac
done
case "${scope}" in
  parent|all) ;;
  *) scope=invalid; incomplete=$((incomplete + 1)) ;;
esac

finish() {
  if [ "${violations}" -eq 0 ] && [ "${incomplete}" -eq 0 ]; then
    printf 'secrets: PASS scope=%s history=%s\n' "${scope}" "${history}"
    exit 0
  fi
  printf 'secrets: FAIL violations=%s incomplete=%s scope=%s history=%s\n' "${violations}" "${incomplete}" "${scope}" "${history}"
  if [ "${incomplete}" -gt 0 ]; then
    exit 2
  fi
  exit 1
}

add_violation() {
  violations=$((violations + 1))
}

add_incomplete() {
  incomplete=$((incomplete + 1))
}

if ! command -v git >/dev/null 2>&1 || ! command -v tr >/dev/null 2>&1; then
  add_incomplete
  finish
fi

if ! ROOT_DIR="$(cd "${ROOT_DIR}" 2>/dev/null && pwd -P)"; then
  add_incomplete
  finish
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-secrets.XXXXXX" 2>/dev/null)" || {
  add_incomplete
  finish
}
trap 'rm -rf "${TMP_DIR}"' EXIT

# An explicit config prevents repository-local Gitleaks configuration from
# weakening the publication scan. Findings and operational errors have distinct
# exit codes, and scanner output never enters logs.
printf '%s\n' 'title = "PALS publication defaults"' '[extend]' 'useDefault = true' >"${TMP_DIR}/gitleaks.toml"
reviewed_findings="${SCRIPT_ROOT}/pals-scripts/reviewed-secret-findings.txt"
if [ ! -f "${reviewed_findings}" ]; then
  reviewed_findings="${TMP_DIR}/reviewed-secret-findings.txt"
  : >"${reviewed_findings}"
fi
if [ "${history}" = true ] && ! command -v gitleaks >/dev/null 2>&1; then
  add_incomplete
fi

content_patterns=(
  '-----BEGIN[[:space:]]+(RSA[[:space:]]+|EC[[:space:]]+|OPENSSH[[:space:]]+|DSA[[:space:]]+)?PRIVATE[[:space:]]+KEY-----'
  '-----BEGIN[[:space:]]+PGP[[:space:]]+PRIVATE[[:space:]]+KEY[[:space:]]+BLOCK-----'
  '(AKIA|ASIA)[0-9A-Z]{16}'
  'github_pat_[A-Za-z0-9_]{40,}'
  'gh[pousr]_[A-Za-z0-9]{30,}'
  'sk-(proj-|ant-[A-Za-z0-9_-]*-)?[A-Za-z0-9_-]{20,}'
  '(sk|rk)_live_[A-Za-z0-9]{20,}'
  'xox[baprs]-[A-Za-z0-9-]{10,}'
  'AIza[0-9A-Za-z_-]{35}'
  'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'
  '(postgres(ql)?|mysql|mariadb|mongodb(\+srv)?|redis)://[^[:space:]/:@]+:[^[:space:]@/]{24,}@'
)

scan_content() {
  local repository_dir="$1"
  local scope="$2"
  local arguments=()
  local pattern rc
  for pattern in "${content_patterns[@]}"; do
    arguments+=(-e "${pattern}")
  done
  if [ "${scope}" = 'index' ]; then
    git -C "${repository_dir}" grep --cached -I -q -E -i "${arguments[@]}" -- . >/dev/null 2>&1
  else
    git -C "${repository_dir}" grep -I -q -E -i "${arguments[@]}" -- . >/dev/null 2>&1
  fi
  rc=$?
  case "${rc}" in
    0) return 0 ;;
    1) return 1 ;;
    *) return 2 ;;
  esac
}

repository_paths=("${ROOT_DIR}")
declared_paths=()

# Pins in the parent can remain fetchable even after their child branch is
# deleted. Keep them as additional revision roots without changing child refs.
record_gitlink() {
  local path="$1" oid="$2" index=0 matched=false
  if ! [[ "${oid}" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]]; then
    add_incomplete
    return
  fi
  case "${oid}" in
    *[!0]*) ;;
    *) return ;;
  esac
  for candidate in "${declared_paths[@]:-}"; do
    if [ "${candidate}" = "${path}" ]; then
      printf '%s\n' "${oid}" >>"${TMP_DIR}/pins-${index}"
      matched=true
      break
    fi
    index=$((index + 1))
  done
  [ "${matched}" = true ] || add_incomplete
}
if [ "${scope}" = all ]; then
  if [ ! -f "${ROOT_DIR}/.gitmodules" ] || ! git config --file "${ROOT_DIR}/.gitmodules" --null --get-regexp '^submodule\..*\.path$' >"${TMP_DIR}/modules" 2>/dev/null; then
    add_incomplete
  else
    while IFS= read -r -d '' entry; do
      repository="${entry#*$'\n'}"
      # Refuse absolute paths, traversal, empty paths, and duplicate entries.
      case "${repository}" in
        ''|/*|.|..|../*|*/../*|*/..|./*|*/./*|*/.) add_incomplete; continue ;;
      esac
      duplicate=false
      for declared in "${declared_paths[@]:-}"; do
        [ "${repository}" != "${declared}" ] || duplicate=true
      done
      if [ "${duplicate}" = true ]; then add_incomplete; continue; fi
      declared_paths+=("${repository}")
      repository_paths+=("${ROOT_DIR}/${repository}")
    done <"${TMP_DIR}/modules"
  fi
  # A removed declaration must not silently hide a tracked submodule.
  if git -C "${ROOT_DIR}" ls-files --stage -z >"${TMP_DIR}/index-entries" 2>/dev/null; then
    index_gitlink_paths=()
    while IFS= read -r -d '' entry; do
      case "${entry}" in
        '160000 '*)
          repository="${entry#*$'\t'}"
          declared=false
          for candidate in "${declared_paths[@]:-}"; do
            [ "${repository}" != "${candidate}" ] || declared=true
          done
          [ "${declared}" = true ] || add_incomplete
          metadata="${entry%%$'\t'*}"
          read -r mode object_id stage <<<"${metadata}"
          if [ "${stage}" != 0 ]; then
            add_incomplete
          else
            record_gitlink "${repository}" "${object_id}"
            index_gitlink_paths+=("${repository}")
          fi
          ;;
      esac
    done <"${TMP_DIR}/index-entries"
    for declared in "${declared_paths[@]:-}"; do
      matched=false
      for indexed in "${index_gitlink_paths[@]:-}"; do
        [ "${declared}" != "${indexed}" ] || matched=true
      done
      [ "${matched}" = true ] || add_incomplete
    done
  else
    add_incomplete
  fi
  if [ "${history}" = true ]; then
    # -m includes gitlink changes made only by a merge result. No rename
    # detection keeps each raw record to one NUL-delimited path.
    if git -C "${ROOT_DIR}" log --all -m --root --raw --no-abbrev --no-renames --format= -z >"${TMP_DIR}/historical-gitlinks" 2>/dev/null; then
      while IFS= read -r -d '' metadata; do
        while [[ "${metadata}" = $'\n'* ]]; do metadata="${metadata#$'\n'}"; done
        case "${metadata}" in
          :*)
            if ! IFS= read -r -d '' repository; then add_incomplete; break; fi
            read -r old_mode new_mode old_oid new_oid change <<<"${metadata}"
            [ "${old_mode}" != ':160000' ] || record_gitlink "${repository}" "${old_oid}"
            [ "${new_mode}" != 160000 ] || record_gitlink "${repository}" "${new_oid}"
            ;;
          '') ;;
          *) add_incomplete ;;
        esac
      done <"${TMP_DIR}/historical-gitlinks"
    else
      add_incomplete
    fi
  fi
  # Parent-tracked Draft admin files are covered by the parent scan. If it is a
  # separate checkout, its own index and history also belong to the all scan.
  if [ -e "${ROOT_DIR}/pals-draft-admin/.git" ]; then
    declared=false
    for candidate in "${declared_paths[@]:-}"; do
      [ "${candidate}" != pals-draft-admin ] || declared=true
    done
    [ "${declared}" = true ] || repository_paths+=("${ROOT_DIR}/pals-draft-admin")
  fi
fi

path_is_sensitive() {
  local lower_path base_name
  lower_path="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  base_name="${lower_path##*/}"
  case "${base_name}" in
    *.example.tfvars|*.example.tfvars.json|*.template.tfvars|*.template.tfvars.json) return 1 ;;
    .env.example|.env.*.example) return 1 ;;
    .env|.env.*) return 0 ;;
    credentials|credentials.*|id_rsa|id_dsa|id_ecdsa|id_ed25519|*.pem|*.key|*.p8|*.p12|*.pfx|*.jks|*.keystore|*.tfstate|*.tfstate.*|*.tfvars|*.tfvars.json|.npmrc|.pypirc|service-account*.json|service_account*.json|*firebase-adminsdk*.json)
      return 0 ;;
  esac
  return 1
}

scan_paths() {
  local paths_file="$1" tracked_path
  while IFS= read -r -d '' tracked_path; do
    if path_is_sensitive "${tracked_path}"; then add_violation; fi
  done <"${paths_file}"
}

repository_counter=0
for repository_dir in "${repository_paths[@]}"; do
  is_parent=false
  [ "${repository_dir}" = "${ROOT_DIR}" ] && is_parent=true
  if [ "${is_parent}" != true ] && [ ! -e "${repository_dir}/.git" ]; then
    add_incomplete
    continue
  fi

  repository_top="$(git -C "${repository_dir}" rev-parse --show-toplevel 2>/dev/null)" || {
    add_incomplete
    continue
  }
  repository_top="$(cd "${repository_top}" 2>/dev/null && pwd -P)" || {
    add_incomplete
    continue
  }
  repository_canonical="$(cd "${repository_dir}" 2>/dev/null && pwd -P)" || {
    add_incomplete
    continue
  }
  if [ "${repository_top}" != "${repository_canonical}" ]; then
    add_incomplete
    continue
  fi
  if [ "${is_parent}" != true ]; then
    case "${repository_canonical}" in
      "${ROOT_DIR}"/*) ;;
      *) add_incomplete; continue ;;
    esac
  fi

  repository_counter=$((repository_counter + 1))
  tracked_paths="${TMP_DIR}/tracked-${repository_counter}"
  if ! git -C "${repository_dir}" ls-files -z >"${tracked_paths}" 2>/dev/null; then
    add_incomplete
    continue
  fi

  scan_paths "${tracked_paths}"

  if [ "${history}" = true ]; then
    history_revisions=(--all -m)
    pin_failure=false
    if [ "${is_parent}" != true ]; then
      declared_index=0
      for candidate in "${declared_paths[@]:-}"; do
        if [ "${repository_dir}" = "${ROOT_DIR}/${candidate}" ] && [ -f "${TMP_DIR}/pins-${declared_index}" ]; then
          if sort -u "${TMP_DIR}/pins-${declared_index}" >"${TMP_DIR}/unique-pins-${repository_counter}" 2>/dev/null; then
            while IFS= read -r object_id; do
              if ! [[ "${object_id}" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || ! git -C "${repository_dir}" cat-file -e "${object_id}^{commit}" >/dev/null 2>&1; then
                pin_failure=true
              else
                history_revisions+=("${object_id}")
              fi
            done <"${TMP_DIR}/unique-pins-${repository_counter}"
          else
            pin_failure=true
          fi
        fi
        declared_index=$((declared_index + 1))
      done
    fi
    if [ "${pin_failure}" = true ] || [ "$(git -C "${repository_dir}" rev-parse --is-shallow-repository 2>/dev/null)" != false ] || ! git -C "${repository_dir}" rev-parse --verify HEAD >/dev/null 2>&1 || ! git -C "${repository_dir}" rev-list "${history_revisions[@]}" --objects --missing=error >/dev/null 2>&1; then
      add_incomplete
    else
      # Include deleted paths and every locally available branch/tag. Fetching
      # the full set of remote refs is a separate publication prerequisite.
      if git -C "${repository_dir}" log "${history_revisions[@]}" --format= --name-only --no-renames -z >"${TMP_DIR}/history-paths-${repository_counter}" 2>/dev/null; then
        scan_paths "${TMP_DIR}/history-paths-${repository_counter}"
      else
        add_incomplete
      fi
      if command -v gitleaks >/dev/null 2>&1; then
        gitleaks git "${repository_dir}" --config "${TMP_DIR}/gitleaks.toml" --log-opts="${history_revisions[*]}" --redact=100 --timeout 300 --exit-code 42 --gitleaks-ignore-path "${reviewed_findings}" --ignore-gitleaks-allow --no-banner >/dev/null 2>&1
        scan_rc=$?
        case "${scan_rc}" in
          0) ;;
          42) add_violation ;;
          *) add_incomplete ;;
        esac
      fi
    fi
  fi

  if scan_content "${repository_dir}" index; then
    add_violation
  else
    scan_rc=$?
    [ "${scan_rc}" -eq 1 ] || add_incomplete
  fi
  if scan_content "${repository_dir}" worktree; then
    add_violation
  else
    scan_rc=$?
    [ "${scan_rc}" -eq 1 ] || add_incomplete
  fi
done

finish
