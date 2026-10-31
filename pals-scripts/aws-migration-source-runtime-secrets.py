#!/usr/bin/env python3
"""Prepare five runtime SecureStrings from the existing Mini; Python 3.9+.

Default is a source-only, read-only plan. Only --apply writes SSM. --reconcile
reads SSM and resolves a previous uncertain write; it never writes SSM. Run on
the Mini with its existing SSO login. No credentials, values, value hashes,
fingerprints, raw command output or environment files are persisted/emitted.
An interrupted apply requires explicit reconciliation; there are no retries.
Writes are not a transaction: a failure can leave a verified subset in SSM.
--reconcile reports verified or reconciled_absent truthfully; only an explicit
later --apply can create parameters observed absent during reconciliation.
The metadata journal is ~/pals-mini-deploy/aws-migration-20261030/
runtime-secrets-receipt.json (0600). Never delete it to bypass reconciliation.
"""
from __future__ import annotations

import argparse
import configparser
import fcntl
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

ACCOUNT = "828786775577"
REGION = "ap-northeast-1"
PROFILE = "pals-migration-operator"
ACTORS = {
    "api": "pals-mini-prod-webfix-20261004-api",
    "worker": "pals-mini-prod-20261004-worker",
    "assessment-worker": "pals-assessment-worker",
}
SPEC = {
    "PALS_GUEST_HASH_KEY": ("guest-hash-key", ("api",)),
    "PALS_WORKER_SHARED_SECRET": (
        "worker-shared-secret", ("api", "worker", "assessment-worker")
    ),
    "PALS_RECIPE_WORKER_SECRET": ("recipe-worker-secret", ("api", "worker")),
    "PALS_RECIPE_SEMANTIC_REVIEWER_SECRET": (
        "recipe-semantic-reviewer-secret", ("api",)
    ),
    "PALS_OPENAI_API_KEY": ("openai-api-key", ("worker", "assessment-worker")),
}
ALIASES = {
    "PALS_WORKER_SHARED_SECRET": ("PALS_AGENT_WORKER_SECRET",),
    "PALS_OPENAI_API_KEY": ("OPENAI_API_KEY",),
}
HEX = re.compile(r"[0-9a-f]{64}")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
MAX_OUTPUT = 4 * 1024 * 1024
JOURNAL = "runtime-secrets-receipt.json"
DEADLINE = 0.0
LOCK_FD = None
PHASE = "initialization"
SAFE_FAILURE_CODES = frozenset({
    "guard_rejected", "unsafe_path", "unsafe_parent", "not_private",
    "wrong_path_type", "file_too_large", "duplicate_member", "invalid_arguments",
    "lock_changed", "total_timeout", "command_timeout", "command_output_limit",
    "command_failed", "actor_mismatch", "pending_transition", "image_mismatch",
    "ambiguous_environment", "required_secret_absent", "invalid_secret",
    "alias_mismatch", "aws_config_too_large", "missing_fixed_profile",
    "cli_history_forbidden", "custom_aws_CA_forbidden", "cli_plugins_forbidden",
    "reconcile_required", "existing_value_differs", "controller_changed",
    "source_changed", "explicit_apply_required", "write_outcome_unverified",
    "incomplete_transfer",
})


class GuardError(RuntimeError):
    """Only fixed internal labels; never include untrusted data."""


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise GuardError("invalid_arguments")


def failure_summary(error):
    """Emit fixed diagnostic labels only; exception text may contain secrets."""
    code = "unexpected_failure"
    if isinstance(error, GuardError):
        code = error.args[0] if len(error.args) == 1 and isinstance(
            error.args[0], str
        ) and error.args[0] in SAFE_FAILURE_CODES else "guard_rejected"
    elif isinstance(error, FileNotFoundError):
        code = "required_path_absent"
    elif isinstance(error, PermissionError):
        code = "permission_denied"
    elif isinstance(error, json.JSONDecodeError):
        code = "invalid_json"
    return {"status": "runtime_secret_transfer_failed", "phase": PHASE,
            "code": code,
            "action": "inspect_protected_receipt_and_explicitly_reconcile_before_retry"}


def require(condition, code="guard_rejected"):
    if not condition:
        raise GuardError(code)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate_member")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def protected(path, directory=False):
    require(path.is_absolute() and path.resolve(strict=True) == path, "unsafe_path")
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        require(info.st_uid in (0, os.geteuid()) and not (
            info.st_mode & 0o022 and not (
                info.st_uid == 0 and info.st_mode & stat.S_ISVTX
            )
        ), "unsafe_parent")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    info = os.fstat(fd)
    try:
        require(info.st_uid == os.geteuid() and not info.st_mode & 0o077,
                "not_private")
        require(stat.S_ISDIR(info.st_mode) if directory else (
            stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        ), "wrong_path_type")
    except BaseException:
        os.close(fd)
        raise
    return fd


def read_json(path):
    fd = protected(path)
    try:
        before = os.fstat(fd)
        require(before.st_size <= 1024 * 1024, "file_too_large")
        raw = os.read(fd, 1024 * 1024 + 1)
        after = os.fstat(fd)
        require((before.st_ino, before.st_size, before.st_mtime_ns,
                 before.st_ctime_ns) == (after.st_ino, after.st_size,
                                        after.st_mtime_ns, after.st_ctime_ns))
        value = decode(raw)
        require(isinstance(value, dict))
        return value, raw
    finally:
        os.close(fd)


@contextmanager
def lock(path):
    global LOCK_FD
    fd = protected(path)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        LOCK_FD = fd

        def verify():
            opened, named = os.fstat(fd), path.lstat()
            require((opened.st_dev, opened.st_ino) ==
                    (named.st_dev, named.st_ino), "lock_changed")
            require(path.resolve(strict=True) == path and
                    not named.st_mode & 0o077 and named.st_nlink == 1)

        verify()
        yield verify
        verify()
    finally:
        LOCK_FD = None
        os.close(fd)


def command(args, data=None):
    """Bounded pipes only: secret JSON never enters argv, files or stderr logs."""
    remaining = DEADLINE - time.monotonic()
    require(remaining > 0, "total_timeout")
    environment = {
        "HOME": str(Path.home()),
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C", "LC_ALL": "C", "AWS_PAGER": "",
        "AWS_CLI_AUTO_PROMPT": "off", "AWS_MAX_ATTEMPTS": "1",
        "AWS_RETRY_MODE": "standard", "AWS_EC2_METADATA_DISABLED": "true",
    }
    output = {"out": bytearray(), "err": bytearray()}
    with subprocess.Popen(
        args, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
        start_new_session=True, pass_fds=(() if LOCK_FD is None else (LOCK_FD,)),
    ) as child:
        try:
            until = time.monotonic() + min(30, remaining)
            with selectors.DefaultSelector() as selector:
                for stream, label in ((child.stdout, "out"), (child.stderr, "err")):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, label)
                pending = memoryview(data) if data is not None else None
                if pending is not None:
                    os.set_blocking(child.stdin.fileno(), False)
                    selector.register(child.stdin, selectors.EVENT_WRITE, "in")
                while selector.get_map():
                    require(time.monotonic() < until, "command_timeout")
                    for key, _events in selector.select(min(0.2, max(0, until-time.monotonic()))):
                        if key.data == "in":
                            written = os.write(key.fd, pending[:65536])
                            pending = pending[written:]
                            if not pending:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            block = os.read(key.fd, 65536)
                            if not block:
                                selector.unregister(key.fileobj)
                            else:
                                output[key.data].extend(block)
                                require(len(output[key.data]) <= MAX_OUTPUT,
                                        "command_output_limit")
                child.wait(timeout=max(0.01, until-time.monotonic()))
            return child.returncode, bytes(output["out"]), bytes(output["err"])
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=5)


def successful(args):
    code, out, _err = command(args)
    require(code == 0, "command_failed")
    return decode(out)


def controller(root):
    p, p_raw = read_json(root / "controller-policy.json")
    c, c_raw = read_json(root / "deploy-config.json")
    require(p.get("schema_version") == "pals.macmini-host-controller.v1")
    require(p.get("runtime_profile") == "isolated-lean-v1")
    containers = p.get("containers", {})
    require(set(containers) == {"api", "web", "worker", "assessment-worker",
                                "verifier", "reconciler"})
    require(all(containers.get(k) == v for k, v in ACTORS.items()), "actor_mismatch")
    require(len(set(containers.values())) == 6)
    require(c.get("containers") == containers and c.get("state_dir") == p.get("state_dir")
            and c.get("docker_context") == p.get("docker_context"))
    state = Path(p["state_dir"])
    require(root in state.parents and state.resolve(strict=True) == state)
    os.close(protected(state, directory=True))
    current, raw = read_json(state / "current.json")
    require(current.get("status") == "healthy" and
            HEX.fullmatch(current.get("manifest_sha256", "")) and
            current.get("database_identity") == p.get("database_identity") and
            c.get("database_identity") == p.get("database_identity"))
    for name in ("normal-update-pending.json", "initial-runtime-pending.json"):
        require(not (state / name).exists() and not (state / name).is_symlink(),
                "pending_transition")
    docker = [p["docker_binary"], "--config", p["docker_config"],
              "--context", p["docker_context"]]
    require(Path(docker[0]).is_absolute() and Path(docker[2]).is_absolute())
    return state, current, docker, (p_raw, c_raw, raw)


def source(current, docker):
    items = successful(docker + ["inspect", *ACTORS.values()])
    require(isinstance(items, list) and len(items) == 3, "actor_mismatch")
    by_name = {x.get("Name"): x for x in items}
    require(set(by_name) == {"/" + x for x in ACTORS.values()}, "actor_mismatch")
    environments, identities = {}, {}
    for role, name in ACTORS.items():
        item = by_name["/" + name]
        state = item.get("State", {})
        component = "worker" if role == "assessment-worker" else role
        require(state.get("Running") is True and not any(
            state.get(k) for k in ("Paused", "Restarting", "Dead")))
        require(HEX.fullmatch(item.get("Id", "")) and
                IMAGE.fullmatch(item.get("Image", "")) and
                item["Image"] == current["images"][component], "image_mismatch")
        env = {}
        for entry in item["Config"]["Env"]:
            key, sep, value = entry.partition("=")
            require(sep and key not in env, "ambiguous_environment")
            env[key] = value
        require(env.get("PALS_ENV") == "prod")
        environments[role] = env
        identities[role] = (item["Id"], item["Image"])
    values = {}
    for key, (suffix, required_roles) in SPEC.items():
        observed = []
        for role, env in environments.items():
            if role in required_roles:
                require(key in env, "required_secret_absent")
            for candidate in (key, *ALIASES.get(key, ())):
                if candidate in env:
                    value = env[candidate]
                    require(isinstance(value, str) and 0 < len(value.encode()) <= 4096
                            and not any(ord(c) < 32 or ord(c) == 127 for c in value),
                            "invalid_secret")
                    observed.append(value)
        require(observed and all(x == observed[0] for x in observed), "alias_mismatch")
        values["/pals/prod/" + suffix] = observed[0]
    return values, identities


def arn(name):
    return "arn:aws:ssm:" + REGION + ":" + ACCOUNT + ":parameter" + name


def aws_cli_privacy():
    """CLI history can record parsed stdin values; refuse that configuration."""
    fd = protected(Path.home() / ".aws" / "config")
    try:
        require(os.fstat(fd).st_size <= 1024 * 1024, "aws_config_too_large")
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(os.read(fd, 1024 * 1024 + 1).decode())
        require(parser.has_section("profile " + PROFILE), "missing_fixed_profile")
        for section in parser.sections():
            settings = parser[section]
            require(settings.get("cli_history", "disabled").strip().lower() == "disabled",
                    "cli_history_forbidden")
            require("ca_bundle" not in settings, "custom_aws_CA_forbidden")
            require(section != "plugins" or not settings, "cli_plugins_forbidden")
    finally:
        os.close(fd)


class Parameters:
    def __init__(self):
        self.prefix = ["aws", "--profile", PROFILE, "--region", REGION,
                       "--output", "json", "--no-cli-pager",
                       "--cli-connect-timeout", "10", "--cli-read-timeout", "20"]

    def identity(self):
        result = successful(self.prefix + ["--endpoint-url", "https://sts." + REGION +
                                          ".amazonaws.com", "sts", "get-caller-identity"])
        require(result.get("Account") == ACCOUNT, "wrong_account")

    def get(self, name):
        code, out, err = command(self.prefix + ["--endpoint-url", "https://ssm." + REGION +
                                               ".amazonaws.com", "ssm", "get-parameter", "--name", name,
                                               "--with-decryption"])
        if code:
            if code == 254 and re.match(
                rb"An error occurred \(ParameterNotFound\) when calling the GetParameter operation:",
                err.strip(),
            ):
                return None
            raise GuardError("parameter_read_failed")
        result = decode(out)["Parameter"]
        require(result.get("Name") == name and result.get("ARN") == arn(name)
                and result.get("Type") == "SecureString"
                and type(result.get("Version")) is int and result["Version"] >= 1
                and result.get("DataType", "text") == "text"
                and isinstance(result.get("Value"), str), "parameter_metadata_mismatch")
        return result

    def put(self, name, value):
        payload = json.dumps({"Name": name, "Value": value, "Type": "SecureString",
                              "Overwrite": False}, ensure_ascii=True).encode()
        # The stdin URI is literal. Values never occur in argv or temporary files.
        code, out, _err = command(self.prefix + ["--endpoint-url", "https://ssm." + REGION +
                                                ".amazonaws.com", "ssm", "put-parameter", "--cli-input-json",
                                                "file:///dev/stdin"], payload)
        require(code == 0, "write_outcome_unverified")
        result = decode(out)
        require(type(result.get("Version")) is int and result["Version"] == 1,
                "write_outcome_unverified")
        return result["Version"]


def receipt(directory, value):
    """Replace metadata only, under the existing private directory and host lock."""
    fd = protected(directory, directory=True)
    tmp = ".runtime-secrets-" + uuid4().hex
    try:
        path = directory / JOURNAL
        if path.exists() or path.is_symlink():
            read_json(path)
        stream = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=fd)
        with os.fdopen(stream, "wb") as output:
            output.write(json.dumps(value, sort_keys=True).encode())
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, JOURNAL, src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    finally:
        os.close(fd)


def transfer(store, values, apply, reconcile, directory, recheck):
    path = directory / JOURNAL
    previous = read_json(path)[0] if path.exists() or path.is_symlink() else None
    if previous:
        require(previous.get("schema_version") == "pals.runtime-secrets-transfer.v1")
        require(reconcile or previous.get("status") in ("verified", "reconciled_absent"),
                "reconcile_required")
    store.identity()
    found = {}
    # A difference in the last parameter must prevent even the first put.
    for name, value in values.items():
        existing = store.get(name)
        require(existing is None or existing["Value"] == value, "existing_value_differs")
        found[name] = existing
    recheck()
    result = {"schema_version": "pals.runtime-secrets-transfer.v1",
              "account": ACCOUNT, "region": REGION, "status": "in_progress",
              "admission_eligible": False, "parameters": [], "pending_parameter": None}
    if not reconcile:
        require(apply, "explicit_apply_required")
    for name, value in values.items():
        existing = found[name]
        if existing is None and not reconcile:
            result.update(status="reconcile_required", pending_parameter=name)
            receipt(directory, result)
            recheck()
            version = store.put(name, value)
            existing = store.get(name)
            require(existing is not None and existing["Value"] == value and
                    existing["Version"] == version, "write_outcome_unverified")
            outcome = "created"
        else:
            outcome = "reconciled" if reconcile else "reused"
        if existing is not None:
            result["parameters"].append({"name": name, "arn": existing["ARN"],
                                         "version": existing["Version"], "outcome": outcome})
        result.update(status="in_progress", pending_parameter=None)
        receipt(directory, result)
    recheck()
    missing = [name for name in values if name not in
               {p["name"] for p in result["parameters"]}]
    require(not missing or reconcile, "incomplete_transfer")
    result.update(status="reconciled_absent" if missing else "verified",
                  missing_parameters=missing)
    receipt(directory, result)
    return result


def main(arguments=None):
    global DEADLINE, PHASE
    PHASE = "source_preflight"
    DEADLINE = time.monotonic() + 420
    parser = Parser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--reconcile", action="store_true")
    args = parser.parse_args(arguments)
    root = Path.home() / "pals-mini-deploy"
    os.close(protected(root, directory=True))
    first = controller(root)
    with lock(first[0] / "host-update.lock") as verify_lock:
        _state, current, docker, binding = controller(root)
        require(binding == first[3], "controller_changed")
        values, identities = source(current, docker)

        def recheck():
            verify_lock()
            repeated = controller(root)
            require(repeated[3] == binding, "controller_changed")
            actual, ids = source(current, docker)
            require(actual == values and ids == identities, "source_changed")

        if args.apply or args.reconcile:
            PHASE = "receipt_directory_preflight"
            directory = root / "aws-migration-20261030"
            os.close(protected(directory, directory=True))
            PHASE = "aws_cli_privacy_preflight"
            aws_cli_privacy()
            PHASE = "ssm_reconciliation" if args.reconcile else "ssm_transfer"
            result = transfer(Parameters(), values, args.apply, args.reconcile,
                              directory, recheck)
            print(json.dumps({"status": result["status"],
                              "verified_parameter_count": len(result["parameters"]),
                              "admission_eligible": False}))
        else:
            recheck()
            print(json.dumps({"status": "plan_only_no_AWS_calls", "account": ACCOUNT,
                              "region": REGION, "profile": PROFILE,
                              "parameters": [{"name": name, "arn": arn(name)}
                                             for name in values],
                              "admission_eligible": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001 -- fixed-label privacy boundary
        print(json.dumps(failure_summary(error)), file=sys.stderr)
        sys.exit(2)
