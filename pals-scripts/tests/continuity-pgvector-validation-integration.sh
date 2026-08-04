#!/usr/bin/env bash
# Developer-invoked PFI-009 Docker integration test. It leaves no fixture behind.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
RUNNER="${ROOT_DIR}/pals-scripts/continuity-pgvector-validation/run.py"

cleanup() {
  python3 "${RUNNER}" teardown >/dev/null || true
}
trap cleanup EXIT

# The second run proves that validate reloads only the current pinned source.
python3 "${RUNNER}" validate
python3 "${RUNNER}" validate
python3 "${RUNNER}" teardown
trap - EXIT

printf '%s\n' 'PFI-009 local Docker integration: PASS'
