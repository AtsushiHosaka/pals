#!/usr/bin/env bash
set -uo pipefail

LC_ALL=C
export LC_ALL

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
ROOT_DIR="${PALS_ROOT:-${SCRIPT_ROOT}}"

violations=0
incomplete=0

finish() {
  if [ "${violations}" -eq 0 ] && [ "${incomplete}" -eq 0 ]; then
    printf '%s\n' 'secrets: PASS'
    exit 0
  fi
  printf 'secrets: FAIL violations=%s incomplete=%s\n' "${violations}" "${incomplete}"
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

implementation_repositories=(
  'pals-api'
  'pals-webfront'
  'pals-draft-admin'
  'pals-infra'
  'pals-datasets'
  'pals-observability'
  'pals-agent'
)

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
for repository in "${implementation_repositories[@]}"; do
  repository_paths+=("${ROOT_DIR}/${repository}")
done

repository_counter=0
for repository_dir in "${repository_paths[@]}"; do
  is_parent=false
  [ "${repository_dir}" = "${ROOT_DIR}" ] && is_parent=true
  if [ "${is_parent}" != true ] && [ ! -e "${repository_dir}/.git" ]; then
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

  repository_counter=$((repository_counter + 1))
  tracked_paths="${TMP_DIR}/tracked-${repository_counter}"
  if ! git -C "${repository_dir}" ls-files -z >"${tracked_paths}" 2>/dev/null; then
    add_incomplete
    continue
  fi

  while IFS= read -r -d '' tracked_path; do
    lower_path="$(printf '%s' "${tracked_path}" | tr '[:upper:]' '[:lower:]')"
    base_name="${lower_path##*/}"
    path_bad=false
    case "${base_name}" in
      .env|.env.*)
        [ "${base_name}" = '.env.example' ] || path_bad=true
        ;;
      credentials|credentials.*|id_rsa|id_dsa|id_ecdsa|id_ed25519|*.pem|*.p12|*.pfx|*.jks|*.keystore|terraform.tfstate|terraform.tfstate.*|.npmrc|.pypirc)
        path_bad=true
        ;;
    esac
    case "${lower_path}" in
      */.aws/credentials|.aws/credentials|*/service-account*.json|service-account*.json)
        path_bad=true
        ;;
    esac
    if [ "${path_bad}" = true ]; then
      add_violation
    fi
  done <"${tracked_paths}"

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
