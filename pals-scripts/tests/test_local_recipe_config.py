"""Persistent local Recipe configuration preserves distinct credentials across rebuilds."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "local_recipe_config",
    Path(__file__).resolve().parents[1] / "bootstrap-local-recipe-config.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _prepare(existing=None, fingerprint="a" * 64):
    return module.prepare_config(
        existing,
        worker_secret="ordinary-worker-secret",
        fingerprint=fingerprint,
        lean_version="leanprover/lean4:v4.32.0-rc1",
        manifest_sha256="b" * 64,
    )


def test_rebuild_updates_only_observed_metadata_and_preserves_secrets():
    original = _prepare()
    rebuilt = _prepare(original, "c" * 64)
    for key in (*module._SECRET_KEYS, *module._URL_ROLES):
        assert original[key] == rebuilt[key]
    assert rebuilt["PALS_RECIPE_VERIFIER_SHA256"] == "c" * 64
    assert len({original[key] for key in module._SECRET_KEYS}) == 4
    assert not any("OPENAI" in key for key in original)


def test_existing_config_cannot_alias_credentials_or_add_unknown_values():
    original = _prepare()
    duplicate = {
        **original,
        "PALS_RECIPE_REVIEW_REQUESTER_SECRET": original["PALS_RECIPE_WORKER_SECRET"],
    }
    with pytest.raises(ValueError, match="distinct"):
        _prepare(duplicate)
    with pytest.raises(ValueError, match="schema"):
        _prepare({**original, "OPENAI_API_KEY": "not-allowed"})
    with pytest.raises(ValueError, match="database credential"):
        _prepare(
            {
                **original,
                "PALS_PFI_DRAFT_READER_DATABASE_URL": "postgresql://root:pass@remote/pals",
            }
        )


def test_cli_creates_private_file_and_never_replaces_existing_credentials(tmp_path):
    import json
    import stat
    import subprocess
    import sys

    env = tmp_path / "local.env"
    env.write_text("PALS_WORKER_SHARED_SECRET=ordinary-worker-secret\n")
    release = tmp_path / "release.env"
    release.write_text(
        "PALS_VERIFIER_IMAGE_DIGEST=sha256:"
        + "a" * 64
        + "\n"
        + "PALS_VERIFIER_TOOLCHAIN_SHA256="
        + "a" * 64
        + "\n"
    )
    workspace = tmp_path / "lean-workspace"
    workspace.mkdir()
    (workspace / "lean-toolchain").write_text("leanprover/lean4:v4.32.0-rc1\n")
    (workspace / "lake-manifest.json").write_text('{"packages":[]}')
    output = tmp_path / "recipe.env"
    command = [
        sys.executable,
        str(Path(module.__file__)),
        "--env-file",
        str(env),
        "--release-env",
        str(release),
        "--output",
        str(output),
        "--lean-workspace",
        str(workspace),
    ]
    first = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(first.stdout)["status"] == "created"
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    original = output.read_bytes()
    values = module.read_env(output)
    for key in (*module._SECRET_KEYS, *module._URL_ROLES):
        assert values[key] not in first.stdout + first.stderr
    second = subprocess.run(command, capture_output=True, text=True, check=True)
    assert json.loads(second.stdout)["status"] == "current"
    assert output.read_bytes() == original
    output.chmod(0o644)
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)
    assert rejected.returncode != 0 and "Traceback" not in rejected.stderr
    assert output.read_bytes() == original


def test_predecessor_configuration_adds_only_new_release_secret():
    old = _prepare()
    del old["PALS_TYPED_CATALOG_RELEASE_SECRET"]
    current = _prepare(old)
    assert all(current[k] == v for k, v in old.items())
    assert len(current["PALS_TYPED_CATALOG_RELEASE_SECRET"]) == 64
    assert current == _prepare(current)
