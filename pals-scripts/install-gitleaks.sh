#!/usr/bin/env bash
# Download the pinned official release; verify its independently pinned checksum.
set -euo pipefail

destination="${1:?Usage: install-gitleaks.sh DESTINATION_DIRECTORY}"
version=8.30.1
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) platform=linux_x64; checksum=551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb ;;
  Linux-aarch64|Linux-arm64) platform=linux_arm64; checksum=e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080 ;;
  Darwin-arm64) platform=darwin_arm64; checksum=b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5 ;;
  Darwin-x86_64) platform=darwin_x64; checksum=dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709 ;;
  *) echo 'Unsupported Gitleaks platform.' >&2; exit 2 ;;
esac
temporary="$(mktemp -d "${TMPDIR:-/tmp}/pals-gitleaks.XXXXXX")"
trap 'rm -rf "${temporary}"' EXIT
archive="gitleaks_${version}_${platform}.tar.gz"
curl --fail --silent --show-error --location --retry 2 \
  "https://github.com/gitleaks/gitleaks/releases/download/v${version}/${archive}" \
  --output "${temporary}/${archive}"
python3 - "${temporary}/${archive}" "${checksum}" "${temporary}" <<'PY'
import hashlib
import pathlib
import sys
import tarfile

archive, expected, directory = sys.argv[1:]
if hashlib.sha256(pathlib.Path(archive).read_bytes()).hexdigest() != expected:
    raise SystemExit("Gitleaks checksum mismatch.")
with tarfile.open(archive) as release:
    member = release.getmember("gitleaks")
    if not member.isfile():
        raise SystemExit("Invalid Gitleaks release member.")
    target = pathlib.Path(directory) / "gitleaks"
    target.write_bytes(release.extractfile(member).read())
    target.chmod(0o755)
PY
mkdir -p "${destination}"
mv "${temporary}/gitleaks" "${destination}/gitleaks"
"${destination}/gitleaks" version
