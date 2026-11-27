#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
# The lane tests skip Compose rendering when PyYAML is absent; a skip must not pass as evidence.
python3 -c 'import yaml' 2>/dev/null || {
  echo "release-acceptance: PyYAML is required (run pals-scripts/bootstrap-pals-scripts-python.sh and put .venv-pals-scripts/bin first on PATH)" >&2
  exit 1
}
python3 "$root/pals-scripts/tests/test_require_release_cycle_v2.py"
python3 "$root/pals-scripts/tests/test_release_acceptance.py"
python3 "$root/pals-scripts/tests/test_release_post_request.py"
python3 "$root/pals-scripts/tests/test_release_post_request_transport.py"
python3 "$root/pals-scripts/tests/test_release_cognito_refresh_policy.py"
python3 "$root/pals-scripts/tests/test_release_cognito_refresh_browser.py"
python3 "$root/pals-scripts/tests/test_release_acceptance_refresh.py"
node --test "$root/pals-scripts/tests/release-acceptance-refresh.test.cjs"
python3 "$root/pals-scripts/tests/test_local_qualification.py"
python3 "$root/pals-scripts/tests/test_budget_handoff.py"
python3 "$root/pals-scripts/tests/test_capture_lane_topology.py"
python3 "$root/pals-scripts/tests/test_lane_application.py"
python3 "$root/pals-scripts/tests/test_lane_bootstrap.py"
python3 "$root/pals-scripts/tests/test_lane_database.py"
python3 "$root/pals-scripts/tests/test_lane_dependencies.py"
python3 "$root/pals-scripts/tests/test_lane_cleanup.py"
python3 "$root/pals-scripts/tests/test_lane_environment.py"
python3 -m unittest discover -s "$root/pals-scripts/tests" -p test_lane_guard.py
python3 "$root/pals-scripts/tests/test_lane_queue_readiness.py"
python3 -m unittest discover -s "$root/pals-scripts/tests" -p test_lane_subject_freeze.py
python3 "$root/pals-scripts/tests/test_provider_relay.py"
python3 -m unittest discover -s "$root/pals-scripts/tests" -p test_relay_compose.py
node --test "$root/pals-scripts/tests/release-acceptance-browser.test.cjs"
node --test "$root/pals-scripts/tests/local-qualification-browser.test.cjs"
