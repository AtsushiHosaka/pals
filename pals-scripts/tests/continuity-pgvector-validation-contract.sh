#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
python3 "${ROOT_DIR}/pals-scripts/tests/continuity-pgvector-validation-contract.py"
