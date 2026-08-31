#!/usr/bin/env bash
set -uo pipefail

LC_ALL=C
export LC_ALL

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
ROOT_DIR="${PALS_ROOT:-${SCRIPT_ROOT}}"
AGENT_DIR="${PALS_AGENT_ROOT:-${ROOT_DIR}/pals-agent}"

violations=0
incomplete=0

finish() {
  if [ "${violations}" -eq 0 ] && [ "${incomplete}" -eq 0 ]; then
    printf '%s\n' 'public-agent-boundary: PASS'
    exit 0
  fi
  printf 'public-agent-boundary: FAIL violations=%s incomplete=%s\n' "${violations}" "${incomplete}"
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

if ! command -v python3 >/dev/null 2>&1; then
  add_incomplete
  finish
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pals-public-agent.XXXXXX" 2>/dev/null)" || {
  add_incomplete
  finish
}
trap 'rm -rf "${TMP_DIR}"' EXIT

wheel_path=''
if [ -n "${PALS_PUBLIC_AGENT_WHEEL:-}" ]; then
  wheel_path="${PALS_PUBLIC_AGENT_WHEEL}"
  if [ ! -f "${wheel_path}" ]; then
    add_incomplete
    finish
  fi
else
  if ! AGENT_DIR="$(cd "${AGENT_DIR}" 2>/dev/null && pwd -P)" || [ ! -f "${AGENT_DIR}/pyproject.toml" ]; then
    add_incomplete
    finish
  fi
  wheel_dir="${TMP_DIR}/wheel"
  mkdir -p "${wheel_dir}" || {
    add_incomplete
    finish
  }
  if command -v uv >/dev/null 2>&1; then
    if ! UV_CACHE_DIR="${TMP_DIR}/uv-cache" UV_NO_PROGRESS=1 \
      uv build --wheel --out-dir "${wheel_dir}" "${AGENT_DIR}" >/dev/null 2>&1; then
      add_incomplete
      finish
    fi
  elif python3 -c 'import build' >/dev/null 2>&1; then
    if ! python3 -m build --wheel --outdir "${wheel_dir}" "${AGENT_DIR}" >/dev/null 2>&1; then
      add_incomplete
      finish
    fi
  else
    add_incomplete
    finish
  fi

  set -- "${wheel_dir}"/*.whl
  if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
    add_incomplete
    finish
  fi
  wheel_path="$1"
fi

python3 - "${wheel_path}" >/dev/null 2>&1 <<'PY'
import re
import stat
import sys
import zipfile

MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
OVERLAP_BYTES = 4096

PATH_DENY = re.compile(
    r"(?:^|/)(?:"
    r"\.env(?:\.[^/]*)?|\.claude|\.codex|\.aws|credentials(?:\.[^/]*)?|"
    r"private[-_]?prompts?|private[-_]?datasets?|private[-_]?config|"
    r"prod(?:uction)?[-_.]?config|terraform\.tfstate(?:\.[^/]*)?|"
    r"pals[-_](?:api|webfront|draft[-_]?admin|infra|datasets|observability)"
    r")(?:/|$)|"
    r"(?:^|/)(?:id_rsa|id_dsa|id_ecdsa|id_ed25519)(?:\.[^/]*)?$|"
    r"\.(?:pem|key|p12|pfx|jks|keystore|sqlite|sqlite3|db|dump)$",
    re.IGNORECASE,
)

CONTENT_DENY = [
    re.compile(rb"-----BEGIN\s+(?:(?:RSA|EC|OPENSSH|DSA)\s+)?PRIVATE\s+KEY-----", re.I),
    re.compile(rb"-----BEGIN\s+PGP\s+PRIVATE\s+KEY\s+BLOCK-----", re.I),
    re.compile(rb"(?<![A-Za-z0-9_-])(?:AKIA|ASIA)[0-9A-Z]{16}(?![0-9A-Z])"),
    re.compile(rb"(?<![A-Za-z0-9_])github_pat_[A-Za-z0-9_]{40,}"),
    re.compile(rb"(?<![A-Za-z0-9_])gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"(?<![A-Za-z0-9_-])sk-(?:proj-|ant-[A-Za-z0-9_-]*-)?[A-Za-z0-9_-]{20,}"),
    re.compile(rb"(?<![A-Za-z0-9_])(?:sk|rk)_live_[A-Za-z0-9]{20,}"),
    re.compile(rb"(?<![A-Za-z0-9-])xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(rb"(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}"),
    re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(
        rb"(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://"
        rb"[^\s/:@]+:[^\s@/]{24,}@",
        re.I,
    ),
    re.compile(
        rb"(?:api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|"
        rb"refresh[_-]?token|private[_-]?key|password|aws[_-]?secret[_-]?access[_-]?key)"
        rb"\s*[:=]\s*[\"']?[A-Za-z0-9+/=_-]{24,}",
        re.I,
    ),
    re.compile(rb"https?://[^\s\"'<>]{0,512}(?:internal|prod(?:uction)?)[^\s\"'<>]{0,512}", re.I),
    re.compile(rb"(?:environment|deployment[_-]?stage)\s*[:=]\s*[\"']?(?:prod|production)\b", re.I),
    re.compile(rb"production\s*[:=]\s*(?:true|1)\b", re.I),
    re.compile(
        rb"(?:aws[_-]?account[_-]?id|account[_-]?id)\s*[:=]\s*[\"']?"
        rb"(?!0{12}(?![0-9]))[0-9]{12}(?![0-9])",
        re.I,
    ),
    re.compile(rb"arn:(?:aws|aws-us-gov|aws-cn):[^:\s]*:[^:\s]*:(?!0{12}:)[0-9]{12}:", re.I),
    re.compile(rb"git@github\.com:[^\s/]+/pals-(?:api|webfront|draft-admin|infra|datasets|observability)(?:\.git)?", re.I),
]


def inspect_wheel(path: str) -> int:
    try:
        if not zipfile.is_zipfile(path):
            return 2
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if not infos:
                return 2
            if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
                return 2

            names: set[str] = set()
            package_python = False
            dist_info_roots: set[str] = set()
            required_by_root: dict[str, set[str]] = {}

            for info in infos:
                name = info.filename
                if not name or "\\" in name or name.startswith("/") or "\x00" in name:
                    return 1
                trimmed = name[:-1] if name.endswith("/") else name
                parts = trimmed.split("/")
                if not trimmed or any(part in {"", ".", ".."} for part in parts):
                    return 1
                if name in names:
                    return 1
                names.add(name)

                mode = (info.external_attr >> 16) & 0o170000
                if mode == stat.S_IFLNK:
                    return 1

                top_level = parts[0]
                if top_level != "pals_agent" and not top_level.endswith(".dist-info"):
                    return 1
                if PATH_DENY.search(name):
                    return 1
                if name.startswith("pals_agent/") and name.endswith(".py"):
                    package_python = True
                if top_level.endswith(".dist-info"):
                    dist_info_roots.add(top_level)
                    required_by_root.setdefault(top_level, set()).add("/".join(parts[1:]))

            if not package_python or len(dist_info_roots) != 1:
                return 2
            dist_info_root = next(iter(dist_info_roots))
            required = required_by_root.get(dist_info_root, set())
            if not {"METADATA", "WHEEL", "RECORD"}.issubset(required):
                return 2

            for info in infos:
                if info.is_dir():
                    continue
                with archive.open(info) as stream:
                    tail = b""
                    while True:
                        chunk = stream.read(CHUNK_BYTES)
                        if not chunk:
                            break
                        candidate = tail + chunk
                        if any(pattern.search(candidate) for pattern in CONTENT_DENY):
                            return 1
                        tail = candidate[-OVERLAP_BYTES:]
        return 0
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return 2


sys.exit(inspect_wheel(sys.argv[1]))
PY
scan_rc=$?
case "${scan_rc}" in
  0) ;;
  1) add_violation ;;
  *) add_incomplete ;;
esac

finish
