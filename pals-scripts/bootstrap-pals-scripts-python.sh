#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
cd "${ROOT_DIR}"

FINAL='.venv-pals-scripts'
STAGE="${FINAL}.stage.$$"
OLD="${FINAL}.old.$$"

cleanup() {
  local prior_rc=$?
  local rc="${1:-${prior_rc}}"
  trap - EXIT HUP INT TERM

  if [ -e "${OLD}" ] && [ ! -e "${FINAL}" ]; then
    if mv "${OLD}" "${FINAL}"; then
      :
    else
      rc=1
    fi
  elif [ -e "${OLD}" ] && [ -e "${FINAL}" ]; then
    rm -rf "${OLD}"
  fi

  rm -rf "${STAGE}"
  exit "${rc}"
}
trap cleanup EXIT
trap 'cleanup 129' HUP
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

is_pid_residue_directory() {
  local path="$1"
  local prefix="$2"
  local suffix="${path#${prefix}}"
  [ "${suffix}" != "${path}" ] || return 1
  case "${suffix}" in
    ''|*[!0-9]*) return 1 ;;
  esac
  [ -d "${path}" ] && [ ! -L "${path}" ]
}

old_paths=()
for path in "${FINAL}.old."*; do
  [ -e "${path}" ] || [ -L "${path}" ] || continue
  if is_pid_residue_directory "${path}" "${FINAL}.old."; then
    old_paths+=("${path}")
  fi
done
old_count="${#old_paths[@]}"
if [ -e "${FINAL}" ]; then
  if [ "${old_count}" -gt 0 ]; then
    for path in "${old_paths[@]}"; do
      rm -rf "${path}"
    done
  fi
elif [ "${old_count}" -eq 1 ]; then
  [ -d "${old_paths[0]}" ] && [ ! -L "${old_paths[0]}" ] || exit 1
  mv "${old_paths[0]}" "${FINAL}"
elif [ "${old_count}" -gt 1 ]; then
  exit 1
fi

for path in "${FINAL}.stage."*; do
  [ -e "${path}" ] || [ -L "${path}" ] || continue
  if is_pid_residue_directory "${path}" "${FINAL}.stage."; then
    rm -rf "${path}"
  fi
done

python3 -c 'import platform, sys; raise SystemExit(0 if platform.python_implementation() == "CPython" and sys.version_info >= (3, 10) else 1)'
python3 -m venv "${STAGE}"
"${STAGE}/bin/python" -m pip install -r pals-scripts/requirements.txt
"${STAGE}/bin/python" -c 'import importlib.metadata as metadata; import markdown_it, mdurl; assert metadata.version("markdown-it-py") == "4.2.0"; assert metadata.version("mdurl") == "0.1.2"'

if [ -e "${FINAL}" ]; then
  mv "${FINAL}" "${OLD}"
fi

if ! mv "${STAGE}" "${FINAL}"; then
  exit 1
fi

if [ -e "${OLD}" ]; then
  rm -rf "${OLD}"
fi
