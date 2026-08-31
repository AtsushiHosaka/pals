#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${repository_root}"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  pals-scripts/tests/test_draft_catalog_coverage_audit.py
