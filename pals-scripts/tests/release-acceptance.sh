#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
python3 "$root/pals-scripts/tests/test_release_acceptance.py"
python3 "$root/pals-scripts/tests/test_local_qualification.py"
node --test "$root/pals-scripts/tests/release-acceptance-browser.test.cjs"
node --test "$root/pals-scripts/tests/local-qualification-browser.test.cjs"
