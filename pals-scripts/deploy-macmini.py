#!/usr/bin/env python3
"""Coordinate a pinned checkout with a separately installed Mac release controller.

This entry does not bootstrap or repair a production database. A host-owned,
hash-pinned controller must implement signed updates before deployment is enabled.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SOURCES = (
    "pals-api",
    "pals-webfront",
    "pals-agent",
    "pals-infra",
    "pals-observability",
    "pals-datasets",
)
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"[0-9a-f]{64}")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
SERVICES = {"api", "web", "worker"}
ASSESSMENT_SERVICE = "assessment-worker"
CONFIG_V1 = "pals.macmini-deploy-config.v1"
CONFIG_V2 = "pals.macmini-deploy-config.v2"


def container_services(schema: str) -> set[str]:
    return SERVICES | ({ASSESSMENT_SERVICE} if schema == CONFIG_V2 else set())


class DeploymentError(Exception):
    """An error whose message contains no credential or command output."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DeploymentError(message)


def inside(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def trusted_path(path: Path, *, directory: bool = False, private: bool = False) -> None:
    require(path.is_absolute(), "Host paths must be absolute.")
    require(
        path == path.resolve(strict=True),
        "Host paths must be canonical and contain no symlinks.",
    )
    for ancestor in reversed(path.parents):
        info = ancestor.lstat()
        sticky_root = info.st_uid == 0 and bool(info.st_mode & stat.S_ISVTX)
        require(
            stat.S_ISDIR(info.st_mode)
            and info.st_uid in {0, os.geteuid()}
            and (not info.st_mode & 0o022 or sticky_root),
            "Host directory is not trusted.",
        )
    info = path.lstat()
    correct_type = (
        stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    )
    require(
        correct_type and info.st_uid in {0, os.geteuid()} and not info.st_mode & 0o022,
        "Host path is not trusted.",
    )
    if not directory:
        require(info.st_nlink == 1, "Host file must have a single link.")
    if private:
        require(
            not info.st_mode & 0o077, "Host configuration and state must be private."
        )


def read_json(path: Path) -> dict:
    trusted_path(path, private=True)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as handle:
        require(
            os.fstat(handle.fileno()).st_size <= 65_536, "Deployment JSON is too large."
        )
        value = json.load(handle)
    require(isinstance(value, dict), "Deployment JSON must be an object.")
    return value


def loopback_url(value: object) -> str:
    require(isinstance(value, str), "Health URL must be a string.")
    parsed = urllib.parse.urlsplit(value)
    require(
        parsed.scheme == "http"
        and parsed.hostname in {"127.0.0.1", "::1"}
        and parsed.port is not None
        and 1 <= parsed.port <= 65535
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment,
        "Health URL must be explicit HTTP loopback.",
    )
    return value


def read_config(path: Path, source: Path) -> dict:
    require(
        not inside(path, source), "Host configuration must be outside the checkout."
    )
    config = read_json(path)
    required = {
        "schema_version",
        "state_dir",
        "controller",
        "controller_sha256",
        "docker_context",
        "containers",
        "database_identity",
        "health_urls",
        "controller_timeout_seconds",
        "health_timeout_seconds",
    }
    require(
        set(config) == required
        and isinstance(config["schema_version"], str)
        and config["schema_version"] in {CONFIG_V1, CONFIG_V2},
        "Mac mini configuration does not match the deployment contract.",
    )
    for name in ("state_dir", "controller"):
        require(isinstance(config[name], str), "Host path must be a string.")
        host_path = Path(config[name])
        require(
            host_path.is_absolute() and not inside(host_path, source),
            "Host state and controller must be outside the checkout.",
        )
        trusted_path(
            host_path, directory=name == "state_dir", private=name == "state_dir"
        )
    controller = Path(config["controller"])
    require(os.access(controller, os.X_OK), "Release controller is not executable.")
    require(
        isinstance(config["controller_sha256"], str)
        and DIGEST.fullmatch(config["controller_sha256"]) is not None
        and hashlib.sha256(controller.read_bytes()).hexdigest()
        == config["controller_sha256"],
        "Release controller fingerprint does not match.",
    )
    header = controller.read_bytes().split(b"\n", 1)[0]
    if header.startswith(b"#!"):
        try:
            interpreter = Path(header[2:].decode("utf-8").strip().split()[0])
        except (UnicodeDecodeError, IndexError):
            raise DeploymentError("Release controller interpreter is invalid.") from None
        require(
            interpreter.is_absolute()
            and interpreter.is_file()
            and os.access(interpreter, os.X_OK),
            "Release controller interpreter is unavailable.",
        )
    require(
        isinstance(config["docker_context"], str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", config["docker_context"])
        is not None,
        "Docker context is invalid.",
    )
    containers = config["containers"]
    expected_services = container_services(config["schema_version"])
    require(
        isinstance(containers, dict)
        and set(containers) == expected_services
        and all(
            isinstance(name, str)
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name)
            for name in containers.values()
        )
        and len(set(containers.values())) == len(expected_services),
        "Configure the exact distinct production containers required by this schema.",
    )
    identity = config["database_identity"]
    require(
        isinstance(identity, dict)
        and set(identity)
        == {"database_system_identifier", "database_volume_id", "host_binding_sha256"}
        and isinstance(identity["database_system_identifier"], str)
        and re.fullmatch(r"[1-9][0-9]{0,19}", identity["database_system_identifier"])
        is not None
        and int(identity["database_system_identifier"]) < 2**64
        and isinstance(identity["database_volume_id"], str)
        and re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            identity["database_volume_id"],
        )
        is not None
        and isinstance(identity["host_binding_sha256"], str)
        and DIGEST.fullmatch(identity["host_binding_sha256"]) is not None,
        "Independently observed production database identity is required.",
    )
    urls = config["health_urls"]
    require(
        isinstance(urls, dict) and set(urls) == {"api", "web"},
        "API and Web health URLs are required.",
    )
    for url in urls.values():
        loopback_url(url)
    require(
        urllib.parse.urlsplit(urls["api"]).path == "/health",
        "API health path must be /health.",
    )
    require(urls["api"] != urls["web"], "Health URLs must be distinct.")
    for name, minimum, maximum in (
        ("controller_timeout_seconds", 30, 3000),
        ("health_timeout_seconds", 1, 300),
    ):
        require(
            type(config[name]) is int and minimum <= config[name] <= maximum,
            "Deployment timeout is invalid.",
        )
    return config


def capture(arguments: list[str], *, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            arguments, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DeploymentError(
            "Required local command is unavailable or timed out."
        ) from error
    require(
        result.returncode == 0,
        "Required local command failed; command output is withheld.",
    )
    return result.stdout.rstrip("\r\n")


def git(root: Path, *arguments: str) -> str:
    return capture(["git", "-C", str(root), *arguments])


def source_revisions(source: Path, revision: str) -> dict[str, str]:
    require(
        SHA.fullmatch(revision) is not None,
        "Parent revision must be a full commit SHA.",
    )
    require(
        Path(git(source, "rev-parse", "--show-toplevel")).resolve() == source,
        "Source directory is not a standalone parent checkout.",
    )
    require(
        git(source, "rev-parse", "HEAD") == revision,
        "Parent checkout differs from the requested commit.",
    )
    require(
        not git(
            source,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ),
        "Parent checkout contains changes.",
    )
    status = git(source, "submodule", "status", "--recursive")
    require(
        bool(status) and all(line.startswith(" ") for line in status.splitlines()),
        "Submodules must be initialized at the parent-pinned commits.",
    )
    # Ignore settings in an intermediate submodule can conceal deeper changes
    # even when the parent's status uses --ignore-submodules=none.
    capture(
        [
            "git",
            "-C",
            str(source),
            "submodule",
            "foreach",
            "--quiet",
            "--recursive",
            (
                "source_status=$(git status --porcelain=v1 --untracked-files=all --ignore-submodules=none) "
                '&& test -z "$source_status"'
            ),
        ]
    )
    result = {"pals": revision}
    for name in SOURCES:
        root = source / name
        require(
            Path(git(root, "rev-parse", "--show-toplevel")).resolve() == root,
            "Required submodule is not initialized.",
        )
        entry = git(source, "ls-tree", "HEAD", "--", name).split()
        require(
            len(entry) == 4 and entry[:2] == ["160000", "commit"] and entry[3] == name,
            "Required submodule is absent from the parent commit.",
        )
        require(
            git(root, "rev-parse", "HEAD") == entry[2],
            "Submodule commit differs from the parent pin.",
        )
        require(
            not git(
                root,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignore-submodules=none",
            ),
            "Submodule checkout contains changes.",
        )
        result[name] = entry[2]
    return result


@contextlib.contextmanager
def deployment_lock(state: Path):
    path = state / "deploy.lock"
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        trusted_path(path, private=True)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise DeploymentError(
                "Another deployment holds the Mac mini lock."
            ) from error
        yield
    finally:
        os.close(
            descriptor
        )  # Keep the inode so another waiter cannot lock a replacement file.


def run_controller(
    config: dict, source: Path, revision: str, receipt: Path, log: Path
) -> None:
    # Do not forward runner tokens or ambient AWS role credentials into the release controller.
    environment = {
        name: os.environ[name]
        for name in ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL")
        if name in os.environ
    }
    arguments = [
        config["controller"],
        "--source-dir",
        str(source),
        "--parent-sha",
        revision,
        "--receipt-file",
        str(receipt),
    ]
    with log.open("wb") as output:
        os.chmod(log, 0o600)
        process = subprocess.Popen(
            arguments,
            stdout=output,
            stderr=subprocess.STDOUT,
            env=environment,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=config["controller_timeout_seconds"])
        except BaseException:
            stop_controller(process)
            raise
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            pass
        else:
            stop_controller(process)
            raise DeploymentError(
                "Release controller left child processes; deployment failed."
            )
    require(
        returncode == 0,
        "Release controller failed. Inspect its private host log; no deployment success was recorded.",
    )


def stop_controller(process: subprocess.Popen) -> None:
    # Runner cancellation sends multiple signals. Keep the lock until the
    # controller group is stopped; the controller must never detach children.
    previous = {
        sig: signal.signal(sig, signal.SIG_IGN)
        for sig in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        signal_controller_group(process.pid, signal.SIGTERM)
        # Reap the parent before checking the remaining group. Some macOS
        # environments reject signals to a group containing only an exited,
        # unreaped parent instead of returning ESRCH.
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            pass
        else:
            signal_controller_group(process.pid, signal.SIGKILL)
        process.wait(timeout=2)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def signal_controller_group(group: int, signum: int) -> None:
    try:
        os.killpg(group, signum)
    except ProcessLookupError:
        return
    except PermissionError:
        # macOS can return EPERM for a group containing only unreaped zombies.
        # Ignore that case only after observing that there are no live members.
        observation = capture(["ps", "-A", "-o", "pgid=", "-o", "stat="])
        members = [line.split() for line in observation.splitlines()]
        require(
            all(len(member) == 2 for member in members),
            "Controller cleanup observation is invalid.",
        )
        if any(
            member[0] == str(group) and not member[1].startswith("Z")
            for member in members
        ):
            raise


def validate_receipt(receipt: dict, revisions: dict[str, str], config: dict) -> None:
    expected_schema = (
        "pals.macmini-deploy-result.v2"
        if config["schema_version"] == CONFIG_V2
        else "pals.macmini-deploy-result.v1"
    )
    require(
        set(receipt)
        == {
            "schema_version",
            "status",
            "parent_sha",
            "source_commits",
            "manifest_sha256",
            "images",
            "database_identity",
        }
        and receipt["schema_version"] == expected_schema
        and receipt["status"] == "applied"
        and receipt["parent_sha"] == revisions["pals"]
        and receipt["source_commits"] == revisions
        and receipt["database_identity"] == config["database_identity"],
        "Controller receipt does not match the requested release and existing database.",
    )
    require(
        isinstance(receipt["manifest_sha256"], str)
        and DIGEST.fullmatch(receipt["manifest_sha256"]) is not None,
        "Signed release manifest fingerprint is missing.",
    )
    images = receipt["images"]
    require(
        isinstance(images, dict)
        and set(images) == SERVICES
        and all(
            isinstance(value, str) and IMAGE.fullmatch(value)
            for value in images.values()
        ),
        "Immutable deployment image IDs are required.",
    )


def verify_containers(config: dict, receipt: dict, revisions: dict[str, str]) -> None:
    for service, name in config["containers"].items():
        component = "worker" if service == ASSESSMENT_SERVICE else service
        value = json.loads(
            capture(["docker", "--context", config["docker_context"], "inspect", name])
        )
        require(
            isinstance(value, list) and len(value) == 1,
            "Production container observation is invalid.",
        )
        container = value[0]
        require(
            container.get("State", {}).get("Running") is True
            and container.get("Image") == receipt["images"][component],
            "Production container is not running the controller-reported image.",
        )
        if config["schema_version"] == CONFIG_V2 and component == "worker":
            state = container.get("State", {})
            require(
                state.get("Status") == "running"
                and all(
                    state.get(flag) is False
                    for flag in ("Paused", "Restarting", "Dead")
                )
                and state.get("Health", {}).get("Status") == "healthy",
                "Both production workers must report healthy readiness.",
            )
        labels = (
            json.loads(
                capture(
                    [
                        "docker",
                        "--context",
                        config["docker_context"],
                        "image",
                        "inspect",
                        receipt["images"][component],
                    ]
                )
            )[0]
            .get("Config", {})
            .get("Labels")
            or {}
        )
        owner = {"api": "pals-api", "web": "pals-webfront", "worker": "pals-agent"}[
            component
        ]
        require(
            labels.get("org.opencontainers.image.revision") == revisions[owner]
            and labels.get("site.pals.parent-sha") == revisions["pals"],
            "Running image provenance does not match the parent and component commits.",
        )


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        return None


def verify_health(config: dict) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    deadline = time.monotonic() + config["health_timeout_seconds"]
    while time.monotonic() < deadline:
        healthy = True
        for url in config["health_urls"].values():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                healthy = False
                break
            try:
                with opener.open(url, timeout=min(5, remaining)) as response:
                    healthy = healthy and response.status == 200
            except (OSError, urllib.error.URLError):
                healthy = False
        if healthy:
            return
        time.sleep(min(1, max(0, deadline - time.monotonic())))
    raise DeploymentError(
        "Production API/Web health checks failed. Recovery belongs to the signed release controller."
    )


def execute(
    config_path: Path, source: Path, revision: str, *, preflight: bool = False
) -> dict:
    require(sys.platform == "darwin", "This entry requires the Mac mini host.")
    revisions = source_revisions(source, revision)
    config = read_config(config_path, source)
    with deployment_lock(Path(config["state_dir"])):
        require(
            capture(
                [
                    "docker",
                    "--context",
                    config["docker_context"],
                    "info",
                    "--format",
                    "{{.OSType}}",
                ]
            )
            == "linux",
            "The configured Docker context is not a Linux container engine.",
        )
        if preflight:
            return {
                "status": "preflight-passed",
                "parent_sha": revision,
                "source_commits": revisions,
                "deployed": False,
            }
        descriptor, temporary = tempfile.mkstemp(
            prefix="receipt-", suffix=".json", dir=config["state_dir"]
        )
        os.close(descriptor)
        receipt_path = Path(temporary)
        log = receipt_path.with_suffix(".log")
        try:
            run_controller(config, source, revision, receipt_path, log)
            require(
                source_revisions(source, revision) == revisions,
                "Controller changed the candidate checkout.",
            )
            receipt = read_json(receipt_path)
            validate_receipt(receipt, revisions, config)
            verify_containers(config, receipt, revisions)
            verify_health(config)
            # Reobserve images after HTTP readiness; a preexisting endpoint alone cannot prove this release.
            verify_containers(config, receipt, revisions)
            result = {**receipt, "status": "healthy"}
            with receipt_path.open("w", encoding="utf-8") as output:
                output.write(json.dumps(result, sort_keys=True) + "\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(receipt_path, Path(config["state_dir"]) / "current.json")
            descriptor = os.open(config["state_dir"], os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            return result
        finally:
            receipt_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument(
        "--source-dir", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        result = execute(
            args.config,
            args.source_dir.resolve(),
            args.revision,
            preflight=args.preflight_only,
        )
    except KeyboardInterrupt:
        print(
            "Mac mini deployment interrupted; no success was recorded.", file=sys.stderr
        )
        return 130
    except (DeploymentError, OSError, ValueError, subprocess.SubprocessError):
        # Exceptions from SDK/local tools can include credentials; expose only our code-owned error messages.
        error = sys.exc_info()[1]
        message = (
            str(error)
            if isinstance(error, DeploymentError)
            else "Deployment input or local operation failed."
        )
        print(message, file=sys.stderr)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            annotation = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print("::error title=PALS Mac mini deployment::" + annotation, file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
