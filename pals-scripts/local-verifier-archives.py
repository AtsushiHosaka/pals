#!/usr/bin/env python3
"""The two archives the release plan requires of a local verifier variant, and their proof.

pals-infra is the specification (`scripts/release_plan.py`, `VERIFIER_VARIANT_ARCHIVES`, and
`scripts/release-cycle.py`, `local_verifier_variant`):

* ``source_archive`` is ``git archive --format=tar <verifier commit> pals_agent``. Its hash is
  the candidate manifest's reviewed ``verifier_source.source_archive_sha256``.
* ``recipe_archive`` is ``git archive --format=tar <verifier commit>
  docker/lean-verifier.Dockerfile lean-workspace``: the compiler recipe.

Neither can build the image alone: the Dockerfile also copies ``pyproject.toml`` and
``README.md``. The native image is therefore still built from the complete archive of the
same commit, and this module proves that both plan archives are byte-identical projections
of that commit: each is re-derived from the repository at the commit with the command above,
and each is compared member by member with the complete archive the image was built from.
Nothing is read from a path whose hash is not checked.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import tarfile
from pathlib import Path

# Path order is part of the command and so of the bytes: keep it exactly as pals-infra has it.
PROJECTIONS = {
    "source_archive": ("pals_agent",),
    "recipe_archive": ("docker/lean-verifier.Dockerfile", "lean-workspace"),
}
FILES = {"source_archive": "source-archive.tar", "recipe_archive": "recipe-archive.tar"}
RECIPE_FILES = (
    "docker/lean-verifier.Dockerfile",
    "lean-workspace/lean-toolchain",
    "lean-workspace/lake-manifest.json",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, code):
    if not ok:
        raise ValueError(code)


def git_archive(source_root, revision, paths=()):
    """Exactly pals-infra's command and environment (`release-plan.py`, `Git.run`)."""
    need(
        type(revision) is str
        and len(revision) == 40
        and all(x in "0123456789abcdef" for x in revision),
        "exact_verifier_commit_required",
    )
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0")
    done = subprocess.run(
        ["git", "-C", str(source_root), "archive", "--format=tar", revision, *paths],
        capture_output=True,
        timeout=120,
        check=False,
        env=environment,
    )
    need(done.returncode == 0, "verifier_git_archive_failed")
    return done.stdout


def members(path):
    """Every member with all metadata that can change what a build or a reader sees."""
    result = {}
    with tarfile.open(path, "r:") as archive:
        for member in archive.getmembers():
            need(member.name not in result, "duplicate_verifier_archive_member")
            need(
                member.isfile() or member.isdir() or member.issym(),
                "unsupported_verifier_archive_member",
            )
            content = None
            if member.isfile():
                content = sha(archive.extractfile(member).read())
            result[member.name] = (
                member.type,
                member.mode,
                member.size,
                member.mtime,
                member.linkname,
                content,
            )
    return result


def below(name, paths):
    return any(name == path or name.startswith(path + "/") for path in paths)


def require_projection(complete, projection, paths, code):
    """``projection`` holds exactly what ``complete`` holds under ``paths``, unchanged."""
    whole, part = members(complete), members(projection)
    expected = {
        name: value
        for name, value in whole.items()
        if below(name, paths) and value[0] != tarfile.DIRTYPE
    }
    actual = {
        name: value for name, value in part.items() if value[0] != tarfile.DIRTYPE
    }
    need(expected and actual == expected, code)
    # git lists parent directories of a path too; none may differ from the complete archive.
    for name, value in part.items():
        if value[0] == tarfile.DIRTYPE:
            need(whole.get(name) == value, code)
    return len(actual)


def derive(source_root, revision, complete, directory):
    """Write both plan archives next to the build and prove them. Returns ``{name: path}``."""
    result = {}
    for name, paths in PROJECTIONS.items():
        raw = git_archive(source_root, revision, paths)
        path = Path(directory) / FILES[name]
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as output:
            output.write(raw)
        require_projection(
            complete, path, paths, "verifier_" + name + "_not_of_the_built_commit"
        )
        result[name] = path
    return result


def verify(source_root, revision, complete, references, code):
    """Verify-time proof: frozen bytes, git at the commit, and the built archive all agree.

    ``references`` maps both names to ``{path, sha256}``.
    """
    need(type(references) is dict and set(references) == set(PROJECTIONS), code)
    for name, paths in PROJECTIONS.items():
        reference = references[name]
        need(type(reference) is dict and set(reference) == {"path", "sha256"}, code)
        path = Path(reference["path"])
        need(path.is_absolute() and path.is_file() and not path.is_symlink(), code)
        raw = path.read_bytes()
        need(sha(raw) == reference["sha256"], code)
        need(raw == git_archive(source_root, revision, paths), code)
        require_projection(complete, path, paths, code)


def recipe(path):
    """The Dockerfile, toolchain pin and manifest bytes of a recipe archive."""
    result = []
    with tarfile.open(path, "r:") as archive:
        for name in RECIPE_FILES:
            found = [m for m in archive.getmembers() if m.name == name]
            need(
                len(found) == 1
                and found[0].isfile()
                and 1 <= found[0].size <= 1024 * 1024,
                "exact_native_verifier_recipe_file_required",
            )
            result.append(archive.extractfile(found[0]).read())
    return result
