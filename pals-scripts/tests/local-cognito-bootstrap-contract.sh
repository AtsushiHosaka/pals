#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "${ROOT_DIR}"

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  pals-scripts/tests/test_bootstrap_local_cognito.py
