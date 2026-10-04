#!/usr/bin/env python3
"""Fetch parent-pinned submodules using the Mac runner user's existing gh login.

This command never extracts a token or changes the user's authentication/config.
Only a runner-owned checkout may be updated; conflicting local changes fail closed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

MODULE = importlib.util.spec_from_file_location(
    "macmini_deployment_contract", Path(__file__).with_name("deploy-macmini.py")
)
assert MODULE is not None and MODULE.loader is not None
deployment = importlib.util.module_from_spec(MODULE)
# Importing the contract must not create candidate checkout artifacts.
previous_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    MODULE.loader.exec_module(deployment)
finally:
    sys.dont_write_bytecode = previous_bytecode

CheckoutError = deployment.DeploymentError
require = deployment.require
GIT = "/usr/bin/git"
GH = "/usr/local/bin/gh"
NATIVE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin:/Users/hosakaatsushi/.orbstack/bin"


def checkout_environment(environment: dict[str, str]) -> dict[str, str]:
    # In particular, GH_TOKEN/GITHUB_TOKEN shadow the saved host login. An
    # allowlist also removes every Git/gh trace, askpass and ambient config knob.
    result = {
        name: environment[name]
        for name in (
            "HOME",
            "USER",
            "LOGNAME",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "GH_CONFIG_DIR",
            "XDG_CONFIG_HOME",
        )
        if name in environment
    }
    result.update(
        PATH=NATIVE_PATH,
        GIT_TERMINAL_PROMPT="0",
        GH_PROMPT_DISABLED="1",
        GH_NO_UPDATE_NOTIFIER="1",
        GIT_CONFIG_GLOBAL="/dev/null",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_LFS_SKIP_SMUDGE="1",
    )
    return result


def capture(
    arguments: list[str],
    environment: dict[str, str],
    timeout: int = 30,
    *,
    input_text: str | None = None,
) -> str:
    # Output may include credentials from host tools. Keep it in memory and
    # expose only code-owned diagnostics, including on timeout or cancellation.
    with subprocess.Popen(
        arguments,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
        start_new_session=True,
    ) as process:
        try:
            output, private_error = process.communicate(
                input=input_text, timeout=timeout
            )
        except BaseException:
            deployment.stop_controller(process)
            raise
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            pass
        else:
            deployment.stop_controller(process)
            raise CheckoutError(
                "Checkout command left child processes; checkout failed."
            )
        if process.returncode != 0:
            category = failure_category(private_error)
            raise CheckoutError(
                "Checkout command failed (" + category + "); output is withheld."
            )
    return output.rstrip("\r\n")


def failure_category(private_error: str) -> str:
    """Return only a fixed diagnostic label; never expose host command output."""
    error = private_error.lower()
    patterns = (
        (("transport 'ssh' not allowed",), "SSH transport denied"),
        (("transport 'file' not allowed",), "file transport denied"),
        (
            ("terminal prompts disabled", "could not read username"),
            "Git credentials unavailable",
        ),
        (
            ("authentication failed", "invalid username or token"),
            "Git authentication rejected",
        ),
        (("repository not found",), "repository access unavailable"),
        (
            ("not our ref", "did not contain", "not a valid object name"),
            "pinned revision unavailable",
        ),
        (("index.lock",), "Git index lock conflict"),
        (("destination path",), "checkout destination conflict"),
        (("interaction is not allowed",), "host credential store access unavailable"),
        (("permission denied", "operation not permitted"), "host permission denied"),
    )
    for needles, label in patterns:
        if any(needle in error for needle in needles):
            return label
    return "unclassified host command failure"


def git(source: Path, environment: dict[str, str], *arguments: str) -> str:
    stages = {
        ("rev-parse", "--show-toplevel"): "parent root",
        ("rev-parse", "HEAD"): "parent revision",
        ("status", "--porcelain=v1"): "parent cleanliness",
        ("config", "--local"): "local Git settings",
        ("config", "--file"): "submodule metadata",
        ("ls-tree", "HEAD"): "submodule pins",
        ("submodule", "foreach"): "initialized submodule inspection",
    }
    try:
        return capture([GIT, "-C", str(source), *arguments], environment)
    except CheckoutError as error:
        stage = stages.get(tuple(arguments[:2]), "source inspection")
        raise CheckoutError("Git " + stage + " failed: " + str(error)) from None


def validate_git_settings(source: Path, environment: dict[str, str]) -> None:
    # Local URL-specific settings can override a generic TLS/header setting.
    # Reject them rather than reading a user's credentials or editing config.
    output = git(source, environment, "config", "--local", "--null", "--list")
    for record in output.split("\0"):
        key = record.partition("\n")[0].lower()
        require(
            not key.startswith(
                ("http.", "credential.", "url.", "include.", "includeif.", "filter.")
            )
            and key not in {"core.hookspath", "core.sshcommand"},
            "Checkout Git settings contain an unsupported authentication or transport override.",
        )


def require_runner_checkout(source: Path, environment: dict[str, str]) -> None:
    require(
        sys.platform == "darwin"
        and environment.get("GITHUB_ACTIONS") == "true"
        and environment.get("RUNNER_ENVIRONMENT") == "self-hosted",
        "This command requires the self-hosted Mac Actions runner.",
    )
    workspace = Path(environment.get("GITHUB_WORKSPACE", ""))
    temporary = Path(environment.get("RUNNER_TEMP", ""))
    require(
        source.is_absolute()
        and source in {workspace, workspace / "macmini-deploy"}
        and temporary.is_absolute()
        and deployment.inside(source, temporary.parent)
        and source != temporary.parent
        and not deployment.inside(temporary, source),
        "Source must be the runner's dedicated GitHub workspace.",
    )
    for path in (temporary, source, source / ".git"):
        deployment.trusted_path(path, directory=True)
        require(
            path.stat().st_uid == os.geteuid(),
            "Runner checkout and temporary directories must be owned by the runner user.",
        )


def require_empty_clone(source: Path, root: Path, environment: dict[str, str]) -> str:
    """Recognize only an unindexed empty clone in the dedicated runner checkout."""
    require(
        source == Path(os.environ.get("GITHUB_WORKSPACE", "")) / "macmini-deploy",
        "Interrupted clones may only resume in the dedicated runner checkout.",
    )
    marker = root / ".git"
    deployment.trusted_path(marker, directory=marker.is_dir())
    require(
        marker.stat().st_uid == os.geteuid(),
        "Submodule Git metadata must be runner owned.",
    )
    git_directory = Path(git(root, environment, "rev-parse", "--absolute-git-dir"))
    require(
        deployment.inside(git_directory, source) and git_directory != source,
        "Interrupted clone metadata escaped the dedicated runner checkout.",
    )
    deployment.trusted_path(git_directory, directory=True)
    require(
        git_directory.stat().st_uid == os.geteuid()
        and git(root, environment, "rev-parse", "--show-toplevel") == str(root),
        "Interrupted clone metadata and worktree must be runner owned and exact.",
    )
    head = git(root, environment, "rev-parse", "HEAD")
    require(
        deployment.SHA.fullmatch(head) is not None, "Interrupted clone HEAD is invalid."
    )
    # Check the actual Git-selected index, including a dangling symlink. An
    # existing empty index can encode real staged deletions and is never reset.
    index = Path(git(root, environment, "rev-parse", "--git-path", "index"))
    if not index.is_absolute():
        index = root / index
    require(
        index == git_directory / "index" and not os.path.lexists(index),
        "Interrupted clone resume refuses every existing Git index.",
    )
    require(
        all(entry.name == ".git" for entry in root.iterdir())
        and not git(root, environment, "ls-files", "--stage"),
        "Interrupted clone resume refuses existing worktree entries or staged files.",
    )
    require(
        not os.path.lexists(index)
        and all(entry.name == ".git" for entry in root.iterdir()),
        "Interrupted clone changed during inspection.",
    )
    return head


def validate_initialized_submodules(source: Path, environment: dict[str, str]) -> None:
    initialized = git(
        source,
        environment,
        "submodule",
        "foreach",
        "--quiet",
        "--recursive",
        'printf "%s\\0" "$PWD"',
    )
    resumable: list[tuple[Path, str]] = []
    for value in initialized.split("\0"):
        if not value:
            continue
        root = Path(value)
        require(
            deployment.inside(root, source) and root != source,
            "Submodule escaped the runner checkout.",
        )
        deployment.trusted_path(root, directory=True)
        require(
            root.stat().st_uid == os.geteuid(),
            "Submodule must be owned by the runner user.",
        )
        validate_git_settings(root, environment)
        if git(
            root,
            environment,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=all",
        ):
            resumable.append((root, require_empty_clone(source, root, environment)))
    # Validate every initialized component before resuming any partial clone.
    # Recheck immediately before writing: a diagnostic/fetch may have advanced
    # the shared dedicated workspace since the first inspection.
    for root, head in resumable:
        materialize_empty_clone(source, root, head, environment)
    git(
        source,
        environment,
        "submodule",
        "foreach",
        "--quiet",
        "--recursive",
        "source_status=$(/usr/bin/git status --porcelain=v1 --untracked-files=all --ignore-submodules=all) "
        '&& test -z "$source_status"',
    )


def materialize_empty_clone(
    source: Path, root: Path, head: str, environment: dict[str, str]
) -> None:
    """Resume without replacing an index or forcing any worktree file write."""
    require(
        require_empty_clone(source, root, environment) == head,
        "Interrupted clone changed during validation.",
    )
    git_directory = Path(git(root, environment, "rev-parse", "--absolute-git-dir"))
    index = git_directory / "index"
    lock = git_directory / "index.lock"
    # This is Git's own exclusion protocol, not an advisory helper-only lock.
    try:
        descriptor = os.open(
            lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
    except FileExistsError:
        raise CheckoutError("Interrupted clone index is already locked.") from None
    identity = os.fstat(descriptor)
    try:
        with tempfile.TemporaryDirectory(
            prefix="macmini-index-", dir=git_directory
        ) as temporary:
            alternate_index = Path(temporary) / "index"
            git(
                root,
                {**environment, "GIT_INDEX_FILE": str(alternate_index)},
                "read-tree",
                head,
            )
            require(
                require_empty_clone(source, root, environment) == head,
                "Interrupted clone changed while preparing its index.",
            )
            # Atomic no-replace publication also protects an index created by a
            # direct writer that ignores index.lock. Never rename over real state.
            try:
                os.link(alternate_index, index)
            except FileExistsError:
                raise CheckoutError(
                    "Interrupted clone index appeared during initialization."
                ) from None
            # No --force: a file arriving after the empty check is preserved and
            # makes checkout fail. On failure our new index remains fail-closed.
            git(root, environment, "checkout-index", "--all")
    finally:
        os.close(descriptor)
        try:
            current = lock.lstat()
        except FileNotFoundError:
            pass
        else:
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                lock.unlink()


def validate_parent(source: Path, revision: str, environment: dict[str, str]) -> None:
    require(
        deployment.SHA.fullmatch(revision) is not None, "A full parent SHA is required."
    )
    require(
        git(source, environment, "rev-parse", "--show-toplevel") == str(source)
        and git(source, environment, "rev-parse", "HEAD") == revision,
        "The standalone parent checkout must match the requested commit.",
    )
    require(
        not git(
            source,
            environment,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=all",
        ),
        "Parent checkout contains local changes.",
    )
    validate_git_settings(source, environment)
    modules = source / ".gitmodules"
    deployment.trusted_path(modules)
    fields = {}
    output = git(
        source, environment, "config", "--file", str(modules), "--null", "--list"
    )
    for record in output.split("\0"):
        if not record:
            continue
        name, separator, value = record.partition("\n")
        require(
            separator == "\n" and name not in fields, "Submodule metadata is invalid."
        )
        fields[name] = value
    expected = {
        f"submodule.{name}.{field}"
        for name in deployment.SOURCES
        for field in ("path", "url")
    }
    require(
        set(fields) == expected,
        "Only the six approved PALS source submodules are allowed.",
    )
    for name in deployment.SOURCES:
        require(
            fields[f"submodule.{name}.path"] == name, "Submodule path is not approved."
        )
        require(
            fields[f"submodule.{name}.url"]
            in {
                f"git@github.com:AtsushiHosaka/{name}.git",
                f"https://github.com/AtsushiHosaka/{name}.git",
            },
            "Submodule repository URL is not approved.",
        )
        entry = git(source, environment, "ls-tree", "HEAD", "--", name).split()
        require(
            len(entry) == 4
            and entry[:2] == ["160000", "commit"]
            and deployment.SHA.fullmatch(entry[2]) is not None
            and entry[3] == name,
            "The parent must pin each approved submodule to an exact commit.",
        )
    # Reuse initialized repositories, but never discard tracked or untracked
    # changes inside any nested component when changing the parent-pinned set.
    validate_initialized_submodules(source, environment)


def authenticated_git(source: Path) -> list[str]:
    return [
        GIT,
        "-C",
        str(source),
        "-c",
        "credential.helper=",
        "-c",
        "credential.https://github.com.helper=",
        "-c",
        f"credential.https://github.com.helper={GH} auth git-credential",
        "-c",
        "url.https://github.com/.insteadOf=git@github.com:",
        "-c",
        "http.https://github.com/.extraheader=",
        "-c",
        "http.followRedirects=false",
        "-c",
        "http.sslVerify=true",
        "-c",
        "protocol.allow=never",
        "-c",
        "protocol.https.allow=always",
        "-c",
        "core.hooksPath=/dev/null",
    ]


def verify_exact_source(
    source: Path, revision: str, environment: dict[str, str]
) -> dict:
    # Reuse the same normative source contract as deployment. Its Git calls
    # use the bounded process adapter and native Git without changing global
    # authentication settings or the caller's process environment.
    previous = deployment.capture

    def bounded_capture(arguments, *, timeout=30):
        if arguments[0] == "git":
            arguments = [GIT, *arguments[1:]]
        return capture(arguments, environment, timeout)

    try:
        deployment.capture = bounded_capture
        return deployment.source_revisions(source, revision)
    finally:
        deployment.capture = previous


def execute(source: Path, revision: str) -> dict:
    environment = checkout_environment(dict(os.environ))
    try:
        require_runner_checkout(source, dict(os.environ))
        validate_parent(source, revision, environment)
    except CheckoutError as error:
        raise CheckoutError("Runner source validation failed: " + str(error)) from None
    require(os.access(GH, os.X_OK), "The existing host GitHub CLI is unavailable.")
    arguments = authenticated_git(source)
    try:
        capture([*arguments, "submodule", "sync", "--recursive"], environment)
        capture(
            [*arguments, "submodule", "update", "--init", "--recursive", "--checkout"],
            environment,
            timeout=300,
        )
    except CheckoutError as error:
        raise CheckoutError(
            "Host-authenticated source fetch failed: " + str(error)
        ) from None
    try:
        revisions = verify_exact_source(source, revision, environment)
    except CheckoutError as error:
        raise CheckoutError(
            "Fetched source verification failed: " + str(error)
        ) from None
    return {
        "status": "checkout-passed",
        "parent_sha": revision,
        "source_commits": revisions,
        "deployed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        result = execute(args.source_dir, args.revision)
    except KeyboardInterrupt:
        print("Mac mini checkout interrupted; no deployment occurred.", file=sys.stderr)
        return 130
    except CheckoutError as error:
        # Contract exceptions contain only code-owned diagnostics, never tool output.
        print("Mac mini checkout failed: " + str(error), file=sys.stderr)
        return 2
    except (OSError, ValueError, subprocess.SubprocessError):
        print(
            "Mac mini checkout failed; host command output is withheld.",
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
