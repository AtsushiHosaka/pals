#!/usr/bin/env bash
# Adds ONE self-hosted GitHub Actions runner to an OrbStack Linux machine (pals#467).
# Additive only: never touches an existing runner, user, or service.
# Run inside the machine as root:
#   REPO=pals-api NAME=pals-ci-api-pr LABEL=pals-pr TOKEN=<registration token> DOCKER=1 \
#     bash ci-runner-add.sh
# The registration token is short-lived: `gh api -X POST repos/AtsushiHosaka/$REPO/actions/runners/registration-token --jq .token`
# LABEL is pals-release (release gate checks) or pals-pr (ordinary PR checks). The legacy `pals` label is not added.
set -euo pipefail
: "${REPO:?}" "${NAME:?}" "${LABEL:?}" "${TOKEN:?}"
case "$LABEL" in pals-release|pals-pr) ;; *) echo "LABEL must be pals-release or pals-pr" >&2; exit 2;; esac
TARBALL=${TARBALL:-/opt/pals-ci-cache/actions-runner-linux-arm64-2.338.2.tar.gz}
U=$NAME
[ -f "$TARBALL" ] && tar tzf "$TARBALL" >/dev/null || { echo "TARBALL unreadable: $TARBALL" >&2; exit 4; }
id "$U" >/dev/null 2>&1 && { echo "user $U already exists; refusing to reuse" >&2; exit 3; }
# A leftover home (even a symlink) would be re-owned by useradd -m: refuse before creating anything.
{ [ -e "/home/$U" ] || [ -L "/home/$U" ]; } && { echo "/home/$U already exists; refusing to reuse" >&2; exit 3; }
CREATED=0; REGISTERED=0
cleanup() { # remove only what this invocation created, and only if setup failed before registration
  if [ "$CREATED" = 1 ] && [ "$REGISTERED" = 0 ]; then userdel -r "$U" 2>/dev/null || true; fi
}
trap cleanup EXIT
useradd -m -s /bin/bash "$U"; CREATED=1
[ "${DOCKER:-0}" = 1 ] && usermod -aG docker "$U"
install -d -o "$U" -g "$U" "/home/$U/actions-runner"
sudo -u "$U" tar xzf "$TARBALL" -C "/home/$U/actions-runner"
cd "/home/$U/actions-runner"
sudo -u "$U" ./config.sh --unattended --url "https://github.com/AtsushiHosaka/$REPO" \
  --token "$TOKEN" --name "$NAME" --labels "$LABEL" --work _work
REGISTERED=1
./svc.sh install "$U"
./svc.sh start
