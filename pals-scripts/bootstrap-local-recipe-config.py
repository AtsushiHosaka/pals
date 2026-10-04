#!/usr/bin/env python3
"""Create persistent, distinct local Recipe credentials without exposing their values."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

_SCHEMA = "pals.local-recipe-config.v1"
_REVIEWER_PRINCIPAL = "pals.principal.v1/reviewer/pals-recipe-reviewer"
_SECRET_KEYS = (
    "PALS_RECIPE_WORKER_SECRET",
    "PALS_RECIPE_REVIEW_REQUESTER_SECRET",
    "PALS_RECIPE_SEMANTIC_REVIEWER_SECRET",
    "PALS_TYPED_CATALOG_RELEASE_SECRET",
)
_URL_ROLES = {
    "PALS_RECIPE_CATALOG_SELECTOR_DATABASE_URL": "pals_local_recipe_selector",
    "PALS_PFI_DRAFT_READER_DATABASE_URL": "pals_local_recipe_draft_reader",
}
_METADATA_KEYS = {
    "PALS_LOCAL_RECIPE_CONFIG_SCHEMA",
    "PALS_RECIPE_SEMANTIC_REVIEWER_PRINCIPAL",
    "PALS_RECIPE_CATALOG_ACTIVE_LEAN_VERSION",
    "PALS_RECIPE_CATALOG_ACTIVE_LAKE_MANIFEST_SHA256",
    "PALS_RECIPE_CATALOG_ACTIVE_VERIFIER_SHA256",
    "PALS_RECIPE_ACTIVE_LEAN_VERSION",
    "PALS_RECIPE_ACTIVE_LAKE_MANIFEST_SHA256",
    "PALS_RECIPE_VERIFIER_SHA256",
}


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise ValueError("environment file has malformed or duplicate keys")
        values[key] = value.strip().strip('"').strip("'")
    return values


def prepare_config(
    existing: dict[str, str] | None,
    *,
    worker_secret: str,
    fingerprint: str,
    lean_version: str,
    manifest_sha256: str,
) -> dict[str, str]:
    if not worker_secret or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("observed local release binding is missing")
    if not lean_version or re.search(r"[\s'\"$`\\]", lean_version):
        raise ValueError("Lean toolchain identity is invalid")
    if existing is None:
        values = {"PALS_LOCAL_RECIPE_CONFIG_SCHEMA": _SCHEMA}
        for key in _SECRET_KEYS:
            values[key] = secrets.token_hex(32)
        for key, role in _URL_ROLES.items():
            values[key] = (
                f"postgresql://{role}:{secrets.token_hex(32)}@postgres:5432/pals"
            )
    else:
        values = dict(existing)
        old_keys = (
            (set(_SECRET_KEYS) - {"PALS_TYPED_CATALOG_RELEASE_SECRET"})
            | set(_URL_ROLES)
            | _METADATA_KEYS
        )
        if (
            set(values) == old_keys
            and values.get("PALS_LOCAL_RECIPE_CONFIG_SCHEMA") == _SCHEMA
        ):
            values["PALS_TYPED_CATALOG_RELEASE_SECRET"] = secrets.token_hex(32)
        if (
            set(values) != set(_SECRET_KEYS) | set(_URL_ROLES) | _METADATA_KEYS
            or values.get("PALS_LOCAL_RECIPE_CONFIG_SCHEMA") != _SCHEMA
        ):
            raise ValueError("existing Recipe config has incompatible schema")
        if values["PALS_RECIPE_SEMANTIC_REVIEWER_PRINCIPAL"] != _REVIEWER_PRINCIPAL:
            raise ValueError("existing Recipe reviewer identity is incompatible")
    credentials = [worker_secret]
    for key in _SECRET_KEYS:
        if not re.fullmatch(r"[0-9a-f]{64}", values[key]):
            raise ValueError("existing Recipe credential is invalid")
        credentials.append(values[key])
    for key, role in _URL_ROLES.items():
        parsed = urlsplit(values[key])
        if (
            parsed.scheme != "postgresql"
            or parsed.hostname != "postgres"
            or parsed.port != 5432
            or parsed.path != "/pals"
            or parsed.query
            or parsed.fragment
            or parsed.username != role
            or not parsed.password
            or not re.fullmatch(r"[0-9a-f]{64}", parsed.password)
        ):
            raise ValueError("existing Recipe database credential is invalid")
        credentials.append(parsed.password)
    if len(set(credentials)) != len(credentials):
        raise ValueError(
            "Recipe credentials must be distinct from each other and the worker"
        )
    values.update(
        {
            "PALS_RECIPE_SEMANTIC_REVIEWER_PRINCIPAL": _REVIEWER_PRINCIPAL,
            "PALS_RECIPE_CATALOG_ACTIVE_LEAN_VERSION": lean_version,
            "PALS_RECIPE_ACTIVE_LEAN_VERSION": lean_version,
            "PALS_RECIPE_CATALOG_ACTIVE_LAKE_MANIFEST_SHA256": manifest_sha256,
            "PALS_RECIPE_ACTIVE_LAKE_MANIFEST_SHA256": manifest_sha256,
            "PALS_RECIPE_CATALOG_ACTIVE_VERIFIER_SHA256": fingerprint,
            "PALS_RECIPE_VERIFIER_SHA256": fingerprint,
        }
    )
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--release-env", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lean-workspace", type=Path, required=True)
    args = parser.parse_args()
    if args.output.is_symlink():
        raise ValueError("Recipe output cannot be a symbolic link")
    existing = None
    if args.output.exists():
        metadata = args.output.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ValueError("existing Recipe config must be a regular mode-0600 file")
        existing = read_env(args.output)
    local, release = read_env(args.env_file), read_env(args.release_env)
    fingerprint = release.get("PALS_VERIFIER_TOOLCHAIN_SHA256", "")
    if release.get("PALS_VERIFIER_IMAGE_DIGEST") != "sha256:" + fingerprint:
        raise ValueError("local release image and verifier fingerprint disagree")
    values = prepare_config(
        existing,
        worker_secret=local.get("PALS_WORKER_SHARED_SECRET", ""),
        fingerprint=fingerprint,
        lean_version=(args.lean_workspace / "lean-toolchain").read_text().strip(),
        manifest_sha256=hashlib.sha256(
            (args.lean_workspace / "lake-manifest.json").read_bytes()
        ).hexdigest(),
    )
    content = "".join(f"{key}={value}\n" for key, value in sorted(values.items()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if existing is None:
        descriptor = os.open(
            args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(descriptor, "w") as stream:
            stream.write(content)
    elif args.output.read_text() != content:
        descriptor, temporary = tempfile.mkstemp(
            prefix=".recipe-config-", dir=args.output.parent
        )
        try:
            with os.fdopen(descriptor, "w") as stream:
                stream.write(content)
            os.replace(temporary, args.output)
        finally:
            Path(temporary).unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "status": "created" if existing is None else "current",
                "schema_version": _SCHEMA,
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError):
        raise SystemExit("Local Recipe configuration failed validation.") from None
