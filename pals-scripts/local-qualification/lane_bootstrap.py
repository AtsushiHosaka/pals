"""Derive, without executing, the existing local bootstrap commands for one lane."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import stat
import sys
from urllib.parse import urlsplit

from lanes import ENDPOINTS, absolute, fields, need, pin, read, read_document

SCHEMA = "pals.local-qualification-lane-bootstrap.v1"
VERIFIER_RECEIPT = "pals.local-verifier-build.v2"
REGION = "ap-northeast-1"
CANONICAL_SCRIPTS = {
    "verify_native_build": ("local-verifier-build.py", {"--verify-receipt"}),
    "verifier_tls": (
        "bootstrap-local-verifier-tls.py",
        {
            "--endpoint-url",
            "--region",
            "--image-digest",
            "--toolchain-sha256",
            "--output",
        },
    ),
    "recipe": (
        "bootstrap-local-recipe-config.py",
        {"--env-file", "--release-env", "--output", "--lean-workspace"},
    ),
    "database": (
        "local-qualification/bootstrap_database.py",
        {
            "--runtime-dir",
            "--api-source",
            "--enable-plus-coupons",
            "--lane",
            "--lane-binding",
            "--lane-binding-sha256",
            "--lane-candidate-manifest",
        },
    ),
}
LOCAL_AWS = {
    "AWS_ACCESS_KEY_ID": "test",
    "AWS_SECRET_ACCESS_KEY": "test",
    "AWS_REGION": REGION,
    "AWS_DEFAULT_REGION": REGION,
    "AWS_EC2_METADATA_DISABLED": "true",
    "AWS_CONFIG_FILE": "/dev/null",
    "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(value):
    fields(value, {"path", "sha256"}, "exact_lane_bootstrap_reference_required")
    path = absolute(value["path"])
    need(pin(value["sha256"]), "exact_lane_bootstrap_reference_required")
    return path


def referenced_document(value):
    return read_document(reference(value), value["sha256"])


def local_environment_settings(reference_value, runtime, role):
    path = reference(reference_value)
    need(
        path == runtime / "local.env" and path.resolve(strict=True) == path,
        "exact_lane_bootstrap_environment_required",
    )
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as stream:
        info = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.geteuid()
            and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == 0o600
            and 0 < info.st_size <= 16_384,
            "private_lane_bootstrap_environment_required",
        )
        raw = stream.read(16_385)
    need(
        len(raw) == info.st_size and sha(raw) == reference_value["sha256"],
        "lane_bootstrap_environment_hash_changed",
    )
    settings = {}
    for line in raw.decode().splitlines():
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        need(
            separator and re.fullmatch(r"[A-Z0-9_]+", name) and name not in settings,
            "lane_bootstrap_environment_invalid",
        )
        settings[name] = value
    ports = ENDPOINTS[role]
    localstack = f"http://127.0.0.1:{ports['localstack']}"
    expected = {
        "PALS_ENV": "local",
        "PALS_ENVIRONMENT": "local",
        "PALS_HOST_BIND_ADDRESS": "127.0.0.1",
        "PALS_HOST_AWS_ENDPOINT_URL": localstack,
        "LOCALSTACK_HOST_PORT": str(ports["localstack"]),
        "PALS_AWS_ENDPOINT_URL": "http://localstack:4566",
        "POSTGRES_DB": "pals",
        "POSTGRES_HOST_PORT": str(ports["postgres"]),
        "OPENAI_API_KEY": "local-provider-relay",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "AWS_REGION": REGION,
        "AWS_DEFAULT_REGION": REGION,
    }
    need(
        all(settings.get(key) == value for key, value in expected.items())
        and not any(
            settings.get(key)
            for key in (
                "AWS_SESSION_TOKEN",
                "AWS_PROFILE",
                "PALS_OPENAI_API_KEY",
                "PALS_OPENAI_UPSTREAM_IP",
            )
        ),
        "lane_bootstrap_environment_identity_differs",
    )
    for key, host, port in (
        ("PALS_HOST_DATABASE_URL", "127.0.0.1", ports["postgres"]),
        ("PALS_DATABASE_URL", "postgres", 5432),
    ):
        url = urlsplit(settings.get(key, ""))
        need(
            url.scheme == "postgresql"
            and url.hostname == host
            and url.port == port
            and url.path == "/pals"
            and not url.query
            and not url.fragment
            and bool(url.username and url.password)
            and url.username == settings.get("POSTGRES_USER")
            and url.password == settings.get("POSTGRES_PASSWORD"),
            "lane_bootstrap_database_endpoint_differs",
        )
    coupon = settings.get("PALS_PLUS_COUPONS_ENABLED")
    need(coupon in {"true", "false"}, "lane_bootstrap_coupon_setting_required")
    return settings


def checked_local_environment(reference_value, runtime, role):
    settings = local_environment_settings(reference_value, runtime, role)
    return settings["PALS_HOST_AWS_ENDPOINT_URL"], settings["PALS_PLUS_COUPONS_ENABLED"] == "true"


def source_file(path):
    need(
        path.resolve(strict=True) == path and path.is_file(),
        "canonical_lane_bootstrap_source_required",
    )
    with path.open("rb") as stream:
        raw = stream.read(1_048_577)
    need(0 < len(raw) <= 1_048_576, "canonical_lane_bootstrap_source_required")
    return raw


def canonical_script_refs(root):
    scripts = absolute(str(root)).resolve(strict=True) / "pals-scripts"
    refs = {}
    for name, (relative, expected_flags) in CANONICAL_SCRIPTS.items():
        path = scripts / relative
        raw = source_file(path)
        tree = ast.parse(raw, filename=str(path))
        found = {
            item.args[0].value
            for item in ast.walk(tree)
            if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "add_argument"
            and item.args
            and isinstance(item.args[0], ast.Constant)
            and isinstance(item.args[0].value, str)
        }
        need(expected_flags <= found, "canonical_lane_bootstrap_cli_differs")
        if name == "database":
            need(
                any(
                    isinstance(item, ast.FunctionDef)
                    and item.name == "qualify_lane_postgres"
                    for item in tree.body
                ),
                "canonical_lane_bootstrap_cli_differs",
            )
        refs[name] = {"path": str(path), "sha256": sha(raw)}
    return refs


def native_inputs(receipt, manifest):
    verifier = manifest["verifier_source"]
    image = receipt["built_image_id"]
    need(
        receipt.get("schema_version") == VERIFIER_RECEIPT
        and receipt.get("platform") == "linux/arm64"
        and isinstance(image, str)
        and image.startswith("sha256:")
        and pin(image[7:])
        and re.fullmatch(r"[a-f0-9]{40}", receipt["source_revision"])
        and receipt["source_revision"] == verifier["commit"],
        "lane_bootstrap_native_verifier_identity_differs",
    )
    workspace = absolute(receipt["build_context"]) / "lean-workspace"
    toolchain = source_file(workspace / "lean-toolchain").decode().strip()
    lake = sha(source_file(workspace / "lake-manifest.json"))
    need(
        toolchain == receipt["lean_version"] == manifest["recipe_active_lean_version"]
        and lake
        == receipt["lake_manifest_sha256"]
        == manifest["recipe_active_lake_manifest_sha256"],
        "lane_bootstrap_native_lean_files_differ",
    )
    return image, workspace


def derive(document, source_root):
    fields(
        document,
        {
            "schema_version",
            "lane",
            "layout",
            "local_env",
            "candidate_manifest",
            "native_verifier_receipt",
            "api_source",
            "interpreters",
        },
        "lane_bootstrap_binding_invalid",
    )
    role = document["lane"]
    need(
        document["schema_version"] == SCHEMA
        and isinstance(role, str)
        and role in ENDPOINTS,
        "lane_bootstrap_binding_invalid",
    )
    layout_ref = document["layout"]
    layout = read(reference(layout_ref), layout_ref["sha256"])
    selected = layout["lanes"][role]
    runtime = absolute(selected["runtime_directory"])
    info = runtime.lstat()
    need(
        runtime.resolve(strict=True) == runtime
        and stat.S_ISDIR(info.st_mode)
        and info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o700,
        "private_lane_bootstrap_runtime_required",
    )
    manifest_ref = document["candidate_manifest"]
    manifest = referenced_document(manifest_ref)
    need(
        manifest_ref["sha256"] == selected["candidate_sha256"],
        "lane_bootstrap_candidate_differs",
    )
    api_commit = manifest["source_commits"]["pals-api"]
    need(
        isinstance(api_commit, str) and re.fullmatch(r"[a-f0-9]{40}", api_commit),
        "lane_bootstrap_api_revision_required",
    )
    api_source = absolute(document["api_source"])
    need(
        api_source.resolve(strict=True) == api_source and api_source.is_dir(),
        "lane_bootstrap_api_checkout_required",
    )
    endpoint, coupon = checked_local_environment(document["local_env"], runtime, role)
    image, workspace = native_inputs(
        referenced_document(document["native_verifier_receipt"]), manifest
    )
    fields(
        document["interpreters"],
        {"agent", "api"},
        "lane_bootstrap_interpreters_required",
    )
    interpreters = {
        name: absolute(path) for name, path in document["interpreters"].items()
    }
    need(
        all(
            path.is_file() and os.access(path, os.X_OK)
            for path in interpreters.values()
        ),
        "lane_bootstrap_interpreters_required",
    )
    scripts = canonical_script_refs(source_root)
    release_env = runtime / "release.env"
    recipe_env = runtime / "recipe.env"
    need(
        not any(os.path.lexists(path) for path in (release_env, recipe_env)),
        "lane_bootstrap_output_already_exists",
    )

    def command(kind, interpreter, *argv, environment=None):
        return {
            "step": kind,
            "argv": [
                str(interpreters[interpreter]),
                scripts[kind]["path"],
                *map(str, argv),
            ],
            "source": scripts[kind],
            "environment_overrides": environment or {},
        }

    return {
        "status": "derived_lane_bootstrap_commands",
        "activation_authorized": False,
        "live_checks_verified": False,
        "lane": role,
        "candidate_sha256": manifest_ref["sha256"],
        "api_source_commit": api_commit,
        "expected_postgres": selected["postgres"],
        "environment": document["local_env"],
        "docker_socket": layout["docker_socket"],
        "commands": [
            command(
                "verify_native_build",
                "api",
                "--verify-receipt",
                document["native_verifier_receipt"]["path"],
            ),
            command(
                "verifier_tls",
                "agent",
                "--endpoint-url",
                endpoint,
                "--region",
                REGION,
                "--image-digest",
                image,
                "--toolchain-sha256",
                image[7:],
                "--output",
                release_env,
                environment=LOCAL_AWS,
            ),
            command(
                "recipe",
                "api",
                "--env-file",
                runtime / "local.env",
                "--release-env",
                release_env,
                "--output",
                recipe_env,
                "--lean-workspace",
                workspace,
            ),
            command(
                "database",
                "api",
                "--runtime-dir",
                runtime,
                "--api-source",
                api_source,
                "--lane",
                role,
                "--lane-binding",
                layout_ref["path"],
                "--lane-binding-sha256",
                layout_ref["sha256"],
                "--lane-candidate-manifest",
                manifest_ref["path"],
                *(["--enable-plus-coupons"] if coupon else []),
            ),
        ],
        "postgres_preflight": {
            "source": scripts["database"],
            "call": "qualify_lane_postgres",
            "arguments": {
                "runtime_directory": str(runtime),
                "lane": role,
                "binding_path": layout_ref["path"],
                "binding_sha256": layout_ref["sha256"],
            },
        },
        "apply_requires_clean_environment": True,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--source-root", required=True)
    args = parser.parse_args(argv)
    try:
        result = derive(
            read_document(args.binding, args.binding_sha256), args.source_root
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        RecursionError,
        SyntaxError,
    ) as error:
        code = (
            str(error)
            if re.fullmatch(r"[a-z_]+", str(error))
            else "lane_bootstrap_derivation_failed"
        )
        print(json.dumps({"status": "refused", "code": code}, sort_keys=True))
        return 2
    result["binding_sha256"] = args.binding_sha256
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
