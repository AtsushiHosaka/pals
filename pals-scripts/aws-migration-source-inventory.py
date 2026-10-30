#!/usr/bin/env python3
"""Read source runtime metadata, without credentials, DB rows, or mutations."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys


def command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError(f"command failed: {args[0]} (exit {result.returncode})")
    return result.stdout


def shape(value: object) -> object:
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    return type(value).__name__


def main() -> None:
    root = pathlib.Path.home() / "pals-mini-deploy"
    report: dict[str, object] = {
        "report_kind": "read_only_inventory_not_backup",
        "deployment_directory": str(root),
        "config_shape": shape(json.loads((root / "deploy-config.json").read_text())),
        "state_filenames": sorted(item.name for item in (root / "state").iterdir()),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "config":
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return
    names = command(["docker", "ps", "--format", "{{.Names}}"]).splitlines()
    names = [name for name in names if name.startswith("pals-") and "geekten" not in name]
    containers = json.loads(command(["docker", "inspect", *names])) if names else []
    public: list[dict[str, object]] = []
    for item in containers:
        cfg = item.get("Config") or {}
        name = item["Name"].lstrip("/")
        entry: dict[str, object] = {
            "name": name,
            "image_id": item["Image"],
            "state": item["State"]["Status"],
            "environment_names": sorted(env.partition("=")[0] for env in cfg.get("Env", [])),
            "mounts": [{key: mount.get(key) for key in ("Type", "Source", "Destination", "RW")} for mount in item.get("Mounts", [])],
        }
        if name.endswith("-db"):
            entry["pg_dump_version"] = command(["docker", "exec", name, "pg_dump", "--version"]).strip()
        public.append(entry)
    report["containers"] = public
    if len(sys.argv) == 2:
        public = [entry for entry in public if sys.argv[1] in str(entry["name"])]
        report = {"containers": public}
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print("Source inventory failed; no credential values or command stderr were emitted.", file=sys.stderr)
        sys.exit(1)
