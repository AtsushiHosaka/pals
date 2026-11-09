#!/usr/bin/env python3
"""Parent dispatch fence only; detailed release validation remains in pals-infra."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


class Refusal(ValueError):
    pass


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise Refusal("duplicate_plan_key")
        value[key] = item
    return value


def require_v2(path: Path, reviewed_sha256: str) -> None:
    if not re.fullmatch(r"[a-f0-9]{64}", reviewed_sha256):
        raise Refusal("reviewed_raw_plan_hash_required")
    if path.is_symlink() or not path.is_file():
        raise Refusal("regular_private_plan_required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reviewed_sha256:
        raise Refusal("reviewed_raw_plan_hash_changed")
    value = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(value, dict) or value.get("schema_version") != "pals.release-cycle.v2":
        raise Refusal("release_cycle_v2_required")
    if not isinstance(value.get("release_alerts"), dict):
        raise Refusal("release_alerts_object_required")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    args = parser.parse_args()
    try:
        require_v2(args.plan, args.plan_sha256)
    except Refusal as error:
        print("release_cycle_dispatch_refused:" + str(error), file=sys.stderr)
        return 2
    except (OSError, ValueError, UnicodeError):
        print("release_cycle_dispatch_refused:invalid_private_plan", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
