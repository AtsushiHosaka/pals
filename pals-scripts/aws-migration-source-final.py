#!/usr/bin/env python3
"""Mini source capture bridge; Python 3.9 stdlib, existing Docker and AWS CLI.

Default is a read-only plan. --probe-lock-propagation is a real exclusion probe.
--smoke captures a nonadmitting live snapshot. --final explicitly closes ingress,
drains the existing authority predicates, stops writers, captures, then persistently
stops the DB before real KMS signing and private S3 upload. No source restart or
automatic retry exists. Failed/uncertain actions require --reconcile. Only root's
operator should execute mutation modes after reviewing the plan and target gates.
Final capture and fresh fence require the existing watchdog maintenance marker
~/pals-mini-deploy/auto-recovery/disabled.json (owned regular 0600 JSON object).
The helper never creates/removes this marker. Leave it in place on failure;
inspect the protected journal and reconcile before any source restart.
"""
from __future__ import annotations

import argparse
import base64
import configparser
import errno
import fcntl
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit, urlunsplit
from uuid import uuid4

ACCOUNT = "828786775577"
REGION = "ap-northeast-1"
PROFILE = "pals-migration-operator"
BUCKET = "pals-mini-prod-backups-828786775577"
KEY = "arn:aws:kms:ap-northeast-1:828786775577:key/ff0e59ed-e74c-4e8f-aef3-c815a07f2296"
DATABASE = "pals-mini-prod-webfix-20261004-db"
ACTORS = {"api": "pals-mini-prod-webfix-20261004-api",
          "worker": "pals-mini-prod-20261004-worker", "assessment-worker": "pals-assessment-worker",
          "web": "pals-mini-prod-webfix-20261004-web", "verifier": "pals-verifier",
          "reconciler": "pals-reconciler"}
MAX_METADATA = 4 * 1024 * 1024
MAX_ARTIFACT = 5 * 1024**3
HEX = re.compile(r"[0-9a-f]{64}")
IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
PHASE = "initialization"
DEADLINE = 0.0
LOCK_FD = None
LOCK_WAIT_SECONDS = 30.0
ENVELOPE = "pals.cloud-restore.signed-evidence.v1"
FENCE = "pals.cloud-restore.ec2-source-fence.v1"
FINAL_FAILURE_CODES = frozenset({
    'native_container_lock_domain_not_proven','tool_image_not_pinned_native_source','source_workload_not_drained',
    'existing_final_journal_requires_reconcile','explicit_final_source_confirmation_required',
    'actual_authority_drain_definition_changed','actual_DB_identity_volume_not_mounted','wrong_account','kms_verify_failed',
    'command_failed','command_timeout','total_timeout','tool_stdio_timeout','persistent_source_fence_not_observed',
    'reconcile_source_identity_changed','fresh_fence_requires_uploaded_final','invalid_arguments',
    'source_recovery_maintenance_required','guard_rejected','source_lock_changed','controller_changed',
    'source_container_changed','source_transition_pending','source_image_changed','source_inventory_invalid',
    'source_container_identity_invalid','source_container_state_unsafe','source_file_changed','source_file_too_large',
    'unsafe_path','unsafe_parent','unsafe_file','controller_state_path_invalid','controller_policy_invalid',
    'controller_config_invalid','controller_current_invalid','controller_key_invalid','controller_edge_invalid',
    'controller_docker_invalid','source_mount_inventory_invalid','source_mount_destination_duplicate'})
CAPTURE_STAGES = frozenset({'initialization','controller_preflight','tool_identity','native_lock_probe',
    'maintenance_guard','source_running_guard','drain_definition_guard','source_tools_guard','predecessor_guard',
    'aws_preflight','explicit_final_confirmation','journal_guard','prepare_stage','prepare_inputs','source_image_identity',
    'source_recheck','ingress_stop','authority_drain','writers_stop','post_stop_drain','snapshot_tool',
    'native_lock_handoff','archive_registry','database_restart_disable','database_stop','writers_restart_disable',
    'source_fence_check','source_sign','fence_sign','upload','final_state_check','inspect_final_state',
    'recheck_maintenance','recheck_native_locks','recheck_controller_read','recheck_controller_binding',
    'recheck_container_inspect','recheck_container_identity'})
# Exact owning mac_production_database_update._DRAIN_CHECKS. Verify this list
# against the actual admitted API image before any final source operation.
DRAIN = [
    ["public.proof_requests", "status IN ('queued','assessing') OR claim_id IS NOT NULL"],
    ["public.proof_request_outbox", "state <> 'done'"],
    ["public.proof_request_quota_holds", "state = 'active'"],
    ["public.token_operations", "state = 'active'"], ["public.token_calls", "state = 'pending'"],
    ["public.proof_jobs", "state NOT IN ('verified','failed','canceled') OR generation_claim_expires_at IS NOT NULL"],
    ["public.proof_verification_candidates", "state = 'compiling'"],
    ["public.proof_job_dispatch_outbox", "state IN ('pending','dispatching')"],
    ["public.proof_job_dispatch_redrive_attempts", "state IN ('registered','sending')"],
    ["public.proof_mutation_cutover_attempts", "state = 'in_progress'"],
    ["public.proof_mutation_cutover_operations", "state <> 'settled'"],
    ["public.proof_explanations", "state NOT IN ('completed','failed') OR claim_expires_at IS NOT NULL"],
    ["public.proof_clarifications", "state NOT IN ('completed','failed') OR claim_expires_at IS NOT NULL"],
    ["public.proof_explanation_retries", "state <> 'sent'"],
    ["public.proof_clarification_dispatch_outbox", "state = 'pending'"],
    ["public.proof_clarification_dispatch_claims", "state = 'claimed'"],
    ["pals_billing.billing_stripe_operations", "state = 'pending'"],
]


class Refusal(RuntimeError):
    pass


def require(value, code="guard_rejected"):
    if not value:
        raise Refusal(code)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise Refusal("invalid_arguments")


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, "duplicate_member")
        result[key] = value
    return result


def document(raw):
    value = json.loads(raw, object_pairs_hook=pairs)
    require(isinstance(value, dict))
    return value


def encoded(value):
    # Fence/envelope/config contain only ASCII strings, booleans and integers;
    # this subset is JCS. Tool payload bytes are never reserialized for signing.
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode()
    require(raw.isascii(), "non_ascii_host_document")
    return raw


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def private(path, maximum=MAX_METADATA, private_mode=True):
    require(path.is_absolute() and path.resolve(strict=True) == path, "unsafe_path")
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        require(info.st_uid in (0, os.geteuid()) and not (info.st_mode & 0o022 and not
                (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)), "unsafe_parent")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid in (0, os.geteuid())
                and before.st_nlink == 1 and before.st_size <= maximum
                and not before.st_mode & (0o077 if private_mode else 0o022), "unsafe_file")
        raw = os.read(fd, maximum + 1)
        after = os.fstat(fd)
        require(all(getattr(before, n) == getattr(after, n) for n in
                    ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")), "source_file_changed")
        require(len(raw) <= maximum, "source_file_too_large")
        return raw
    finally:
        os.close(fd)


def write(path, raw, replace=False):
    require(path.parent.resolve(strict=True) == path.parent)
    temporary = path.parent / (".final-" + uuid4().hex) if replace else path
    if replace and (path.exists() or path.is_symlink()):
        private(path)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        os.replace(temporary, path)
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


@contextmanager
def existing_lock(path):
    global LOCK_FD
    private(path, 1024)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    previous = LOCK_FD
    try:
        original = os.fstat(fd)

        def verify():
            opened = os.fstat(fd)
            current = path.lstat()
            require(path.resolve(strict=True) == path and current.st_nlink == 1
                    and not current.st_mode & 0o077 and
                    all(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                        and info.st_uid in (0, os.geteuid()) and not info.st_mode & 0o077
                        and (info.st_dev,info.st_ino)==(original.st_dev,original.st_ino)
                        for info in (opened,current)),
                    "source_lock_changed")
        require(0 < LOCK_WAIT_SECONDS <= 30)
        until = min(DEADLINE, time.monotonic()+LOCK_WAIT_SECONDS)
        while True:
            verify()
            now = time.monotonic()
            require(now < DEADLINE, "total_timeout")
            if now >= until:
                raise BlockingIOError(errno.EAGAIN, "source_lock_busy")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(min(0.1, max(0, until-time.monotonic())))
        LOCK_FD = fd
        verify()
        yield verify
        verify()
    finally:
        LOCK_FD = previous
        os.close(fd)


def environment():
    return {"HOME": str(Path.home()),
            "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "LANG": "C", "LC_ALL": "C", "AWS_PAGER": "", "AWS_CLI_AUTO_PROMPT": "off",
            "AWS_MAX_ATTEMPTS": "1", "AWS_EC2_METADATA_DISABLED": "true"}


def run(args, data=None, output=None, timeout=30, maximum=MAX_METADATA, accepted=(0,)):
    remaining = min(timeout, DEADLINE-time.monotonic())
    require(remaining > 0, "total_timeout")
    out, err = bytearray(), bytearray()
    with subprocess.Popen(args, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment(),
                          start_new_session=True,
                          pass_fds=(() if LOCK_FD is None else (LOCK_FD,))) as child:
        try:
            deadline = time.monotonic()+remaining
            size = 0
            with selectors.DefaultSelector() as selector:
                for stream, label in ((child.stdout, "out"), (child.stderr, "err")):
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, label)
                pending = memoryview(data) if data is not None else None
                if pending is not None:
                    os.set_blocking(child.stdin.fileno(), False)
                    selector.register(child.stdin, selectors.EVENT_WRITE, "in")
                while selector.get_map():
                    require(time.monotonic() < deadline, "command_timeout")
                    for key, _events in selector.select(0.2):
                        if key.data == "in":
                            count = os.write(key.fd, pending[:65536]); pending = pending[count:]
                            if not pending:
                                selector.unregister(key.fileobj); key.fileobj.close()
                            continue
                        block = os.read(key.fd, 65536)
                        if not block:
                            selector.unregister(key.fileobj); continue
                        if key.data == "out" and output is not None:
                            size += len(block); require(size <= maximum, "artifact_too_large")
                            output.write(block)
                        else:
                            target = out if key.data == "out" else err
                            target.extend(block); require(len(target) <= MAX_METADATA, "output_too_large")
                child.wait(timeout=max(0.01, deadline-time.monotonic()))
            require(child.returncode in accepted, "command_failed")
            return child.returncode, bytes(out), bytes(err)
        finally:
            if child.poll() is None:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait(timeout=5)


def result(args):
    return json.loads(run(args)[1], object_pairs_hook=pairs)


def aws_args(service, operation):
    require((service, operation) in {
        ("sts", "get-caller-identity"), ("kms", "get-public-key"), ("kms", "sign"), ("kms", "verify"),
        *(("s3api", name) for name in ("get-public-access-block", "get-bucket-acl", "get-bucket-versioning",
                                      "get-object", "put-object", "head-object"))})
    endpoint = {"sts": "sts", "kms": "kms", "s3api": "s3"}[service]
    args = ["aws", "--profile", PROFILE, "--region", REGION, "--output", "json",
            "--no-cli-pager", "--cli-connect-timeout", "10", "--cli-read-timeout", "20",
            "--endpoint-url", "https://"+endpoint+"."+REGION+".amazonaws.com", service, operation]
    return args


def cli(service, operation, payload=None, extra=()):
    """Closed public-metadata requests. No value/body JSON or stdin paramfile."""
    args = aws_args(service, operation)
    require(isinstance(extra, (list, tuple)))
    if service == "sts":
        require(operation == "get-caller-identity" and payload is None and not extra)
        return document(run(args)[1])
    require(isinstance(payload, dict))
    if service == "kms":
        require(operation == "get-public-key" and payload == {"KeyId": KEY} and not extra)
        return document(run(args+["--key-id", KEY])[1])
    fields = {"Bucket", "ExpectedBucketOwner"}
    require(payload.get("Bucket") == BUCKET and payload.get("ExpectedBucketOwner") == ACCOUNT)
    args += ["--bucket", BUCKET, "--expected-bucket-owner", ACCOUNT]
    if operation in ("get-public-access-block", "get-bucket-acl", "get-bucket-versioning"):
        require(set(payload) == fields and not extra)
        return document(run(args)[1])
    fields.add("Key")
    key = payload.get("Key")
    require(isinstance(key, str) and re.fullmatch(r"aws-migration-20261030/[A-Za-z0-9._/-]{1,384}", key)
            and ".." not in PurePosixPath(key).parts)
    args += ["--key", key]
    if "VersionId" in payload:
        fields.add("VersionId")
        version = payload["VersionId"]
        require(isinstance(version, str) and re.fullmatch(r"[A-Za-z0-9._+/=-]{1,1024}", version)
                and version != "null")
        args += ["--version-id", version]
    if operation == "get-object":
        fields.add("Range")
        byte_range = payload.get("Range")
        require(isinstance(byte_range, str) and re.fullmatch(r"bytes=0-[0-9]{1,10}", byte_range)
                and int(byte_range[8:])+1 <= MAX_ARTIFACT)
        require(len(extra) == 1 and isinstance(extra[0], str))
        private(Path(extra[0]), 0)  # Only our exclusive empty download destination.
        args += ["--range", byte_range, extra[0]]
    elif operation == "head-object":
        fields |= {"VersionId", "ChecksumMode"}
        require(payload.get("ChecksumMode") == "ENABLED" and not extra)
        args += ["--checksum-mode", "ENABLED"]
    elif operation == "put-object":
        fields |= {"ServerSideEncryption", "Metadata", "ChecksumSHA256"}
        metadata = payload.get("Metadata")
        require("VersionId" not in payload and payload.get("ServerSideEncryption") == "AES256" and
                isinstance(metadata, dict) and set(metadata) == {"sha256"} and
                isinstance(metadata["sha256"], str) and HEX.fullmatch(metadata["sha256"]) and
                payload.get("ChecksumSHA256") == base64.b64encode(bytes.fromhex(metadata["sha256"])).decode())
        require(len(extra) == 2 and extra[0] == "--body" and isinstance(extra[1], str))
        body = Path(extra[1])
        require(body.is_absolute() and body.resolve(strict=True) == body)
        info = body.lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid() and info.st_nlink == 1
                and not info.st_mode & 0o077 and info.st_size <= MAX_ARTIFACT)
        args += ["--server-side-encryption", "AES256", "--metadata", json.dumps(metadata, separators=(",", ":")),
                 "--checksum-sha256", payload["ChecksumSHA256"], "--body", str(body)]
    else:
        raise Refusal("guard_rejected")
    require(set(payload) == fields)
    return document(run(args)[1])


def aws_preflight(policy, predecessor, signature):
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(private(Path.home()/".aws/config").decode())
    require(config.has_section("profile "+PROFILE))
    for section in config.sections():
        require(config[section].get("cli_history", "disabled").strip().lower() == "disabled")
        require("ca_bundle" not in config[section] and (section != "plugins" or not config[section]))
    require(cli("sts", "get-caller-identity")["Account"] == ACCOUNT, "wrong_account")
    public = cli("kms", "get-public-key", {"KeyId": KEY})
    raw = base64.b64decode(public["PublicKey"], validate=True)
    require(public["KeyId"] == KEY and public["KeySpec"] == "ECC_NIST_P256" and
            public["KeyUsage"] == "SIGN_VERIFY" and sha(raw) == policy["kms_public_key_sha256"])
    verify_signature(predecessor, signature)
    blocked = cli("s3api", "get-public-access-block", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT})
    require(all(blocked["PublicAccessBlockConfiguration"].get(k) is True for k in
                ["BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"]))
    acl = cli("s3api", "get-bucket-acl", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT})
    require(all(grant["Grantee"].get("Type") == "CanonicalUser" and
                grant["Grantee"].get("ID") == acl["Owner"]["ID"] for grant in acl["Grants"]))
    require(cli("s3api", "get-bucket-versioning", {"Bucket": BUCKET,
            "ExpectedBucketOwner": ACCOUNT}).get("Status") == "Enabled")
    return raw


def verify_signature(raw, signature):
    # fileb:// bypasses profile-specific binary-format settings. Passing a blob
    # through --cli-input-json can sign its base64 text instead of 32 digest bytes.
    with tempfile.TemporaryDirectory(prefix="pals-source-signature-") as temporary:
        directory = Path(temporary).resolve(strict=True)
        path = directory/"signature.der"
        digest = directory/"message-digest.bin"
        write(path, signature)
        write(digest, hashlib.sha256(raw).digest())
        args = aws_args("kms", "verify")+["--key-id", KEY, "--message-type", "DIGEST",
                "--signing-algorithm", "ECDSA_SHA_256", "--message", "fileb://"+str(digest),
                "--signature", "fileb://"+str(path)]
        observed = document(run(args)[1])
    require(observed.get("SignatureValid") is True and observed.get("KeyId") == KEY and
            observed.get("SigningAlgorithm") == "ECDSA_SHA_256", "kms_verify_failed")


def signed(raw):
    with tempfile.TemporaryDirectory(prefix="pals-source-signature-") as temporary:
        digest = Path(temporary).resolve(strict=True)/"message-digest.bin"
        write(digest, hashlib.sha256(raw).digest())
        args = aws_args("kms", "sign")+["--key-id", KEY, "--message-type", "DIGEST",
                "--signing-algorithm", "ECDSA_SHA_256", "--message", "fileb://"+str(digest)]
        observed = document(run(args)[1])
    require(observed.get("KeyId") == KEY and observed.get("SigningAlgorithm") == "ECDSA_SHA_256")
    signature = base64.b64decode(observed["Signature"], validate=True)
    require(8 <= len(signature) <= 80 and signature[0] == 0x30)
    verify_signature(raw, signature)
    return encoded({"schema_version": ENVELOPE, "payload_b64": base64.b64encode(raw).decode(),
                    "signature_b64": base64.b64encode(signature).decode()})


def controller(root):
    policy_raw = private(root/"controller-policy.json"); policy = document(policy_raw)
    config = document(private(root/"deploy-config.json"))
    state = Path(policy["state_dir"])
    require(root in state.parents and state.resolve(strict=True) == state, 'controller_state_path_invalid')
    current_raw = private(state/"current.json"); current = document(current_raw)
    require(policy["schema_version"] == "pals.macmini-host-controller.v1" and
            policy.get("runtime_profile") == "isolated-lean-v1" and policy["containers"] == ACTORS, 'controller_policy_invalid')
    require(policy["database_container"] == DATABASE and config["containers"] == ACTORS and
            config["state_dir"] == str(state) and config["docker_context"] == policy["docker_context"], 'controller_config_invalid')
    require(current["status"] == "healthy" and HEX.fullmatch(current["manifest_sha256"]) and
            current["database_identity"] == policy["database_identity"] == config["database_identity"], 'controller_current_invalid')
    for name in ("initial-runtime-pending.json", "normal-update-pending.json"):
        require(not (state/name).exists() and not (state/name).is_symlink(), "source_transition_pending")
    require(HEX.fullmatch(policy["kms_public_key_sha256"]), 'controller_key_invalid')
    edge = policy["edge_container"]
    require(re.fullmatch(r"pals[A-Za-z0-9_.-]{1,120}", edge) and edge not in ACTORS.values() and edge != DATABASE, 'controller_edge_invalid')
    docker = [policy["docker_binary"], "--config", policy["docker_config"], "--context", policy["docker_context"]]
    require(Path(docker[0]).is_absolute() and Path(docker[2]).is_absolute(), 'controller_docker_invalid')
    for name in ("host-update.lock", "deploy.lock"):
        private(state/name, 1024)
    return policy, current, docker, (policy_raw, current_raw, private(root/"deploy-config.json"))


def inspect_all(docker, edge):
    names = [*ACTORS.values(), edge, DATABASE]
    observed = result(docker+["inspect", *names])
    require(isinstance(observed, list) and len(observed) == len(names), 'source_inventory_invalid')
    items = {item["Name"].removeprefix("/"): item for item in observed}
    require(set(items) == set(names) and len({x["Id"] for x in items.values()}) == len(names), 'source_inventory_invalid')
    for name, item in items.items():
        require(item["Name"] == "/"+name and HEX.fullmatch(item["Id"]) and IMAGE.fullmatch(item["Image"]), 'source_container_identity_invalid')
        require(not item["State"].get("Dead") and not item["State"].get("Paused") and
                not item["State"].get("Restarting"), 'source_container_state_unsafe')
    return items


def actor_environment(item):
    values = {}
    for entry in item["Config"]["Env"]:
        key, separator, value = entry.partition("=")
        require(separator and key not in values)
        values[key] = value
    return values


def require_running(items, current):
    require(all(x["State"]["Running"] is True for x in items.values()))
    for role, name in ACTORS.items():
        component = {"assessment-worker": "worker", "reconciler": "api"}.get(role, role)
        require(items[name]["Image"] == current["images"][component], "source_image_changed")


def canonical_mounts(mounts):
    """Docker does not give Mounts array ordering identity significance.

    Compare every complete record, including unknown fields. Only record order
    changes; destination aliases and duplicate destinations are refused.
    """
    require(type(mounts) is list and len(mounts) <= 256, 'source_mount_inventory_invalid')
    destinations = []
    for mount in mounts:
        require(type(mount) is dict and all(type(key) is str for key in mount), 'source_mount_inventory_invalid')
        destination = mount.get('Destination')
        require(type(destination) is str and destination.startswith('/') and len(destination) <= 4096 and
                '\x00' not in destination and str(PurePosixPath(destination)) == destination and
                '..' not in PurePosixPath(destination).parts, 'source_mount_inventory_invalid')
        destinations.append(destination)
    require(len(set(destinations)) == len(destinations), 'source_mount_destination_duplicate')
    return sorted(mounts, key=lambda mount: mount['Destination'])


def require_same(before, after):
    require(set(before) == set(after), 'source_inventory_invalid')
    changes = []
    for name, original in before.items():
        current = after[name]
        changed = [key for key in ("Id", "Image", "Mounts", "Config") if
                   (canonical_mounts(current[key]) != canonical_mounts(original[key]) if key == 'Mounts'
                    else current[key] != original[key])]
        if changed:
            changes.append({'container': name, 'fields': changed})
    if changes:
        error = Refusal('source_container_changed'); error.changed_fields = changes
        raise error


def tool_image(docker, image, commit):
    require(IMAGE.fullmatch(image) and re.fullmatch(r"[0-9a-f]{40}", commit))
    observed = result(docker+["image", "inspect", image]); require(len(observed) == 1)
    item = observed[0]
    require(item["Id"] == image and item["Os"] == "linux" and item["Architecture"] == "arm64" and
            (item["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") == commit,
            "tool_image_not_pinned_native_source")


def docker_tool(docker, image, name, mounts, network="none", interactive=False):
    args = docker+["run", *(["-i"] if interactive else []), "--rm", "--name", name,
                   "--label", "pals.migration.purpose=ec2-source-capture", "--pull=never", "--read-only",
                   "--network", network, "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                   "--user", str(os.geteuid())+":"+str(os.getegid()), "--pids-limit=128",
                   "--memory=512m", "--cpus=1", "--log-driver=none",
                   "--env", "AWS_CONFIG_FILE=/dev/null", "--env", "AWS_SHARED_CREDENTIALS_FILE=/dev/null",
                   "--env", "AWS_EC2_METADATA_DISABLED=true", "--env", "PYTHONDONTWRITEBYTECODE=1",
                   "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=32m", "--entrypoint", "python"]
    for source, target, readonly in mounts:
        require("," not in str(source) and "," not in target)
        args += ["--mount", "type=bind,source="+str(source)+",target="+target+(",readonly" if readonly else "")]
    return args+[image]


def probe_lock(docker, image, path, *, host_native=False):
    code = ("import fcntl,os,sys; f=os.open('/lock',os.O_RDONLY);\n"
            "try: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
            "except BlockingIOError: print('native_lock_refused'); sys.exit(75)\n"
            "print('native_lock_acquired')\n"
            "sys.exit(0)\n")
    def observe(expected):
        args = docker_tool(docker, image, "pals-source-lock-probe-"+uuid4().hex[:12], [(path, "/lock", True)])
        status, out, _err = run(args+["-I", "-c", code], timeout=30, accepted=(0, 75))
        require((status, out) == expected, "native_container_lock_domain_not_proven")
    # Free/held/free controls rule out an unrelated orphan container lock as a
    # false positive. Each metadata-only probe is removed by Docker after exit.
    observe((0, b"native_lock_acquired\n"))
    with existing_lock(path):
        observe((0, b"native_lock_acquired\n") if host_native else (75, b"native_lock_refused\n"))
    observe((0, b"native_lock_acquired\n"))


def source_tools(docker, database):
    paths = run(docker+["exec", "--user", "postgres", database["Id"], "/bin/sh", "-c",
                       "command -v env; command -v psql; command -v pg_dump; command -v sha256sum"])[1].decode().splitlines()
    require(len(paths) == 4 and all(re.fullmatch(r"/[A-Za-z0-9_./+-]+", p) for p in paths))
    tools = dict(zip(["env", "psql", "pg_dump", "sha256sum"], paths))
    version = run(docker+["exec", "--user", "postgres", database["Id"], tools["pg_dump"], "--version"])[1]
    require(re.fullmatch(rb"pg_dump \(PostgreSQL\) 16\.15(?: \([^\r\n]{1,160}\))?\n", version))
    hashed = run(docker+["exec", "--user", "postgres", database["Id"], tools["sha256sum"], tools["pg_dump"]])[1].decode().split()
    require(len(hashed) == 2 and HEX.fullmatch(hashed[0]) and hashed[1] == tools["pg_dump"])
    return tools, hashed[0]


def pg_command(docker, database, tools, executable):
    path = actor_environment(database)["PATH"]
    require(re.fullmatch(r"/[A-Za-z0-9_./+-]+(?::/[A-Za-z0-9_./+-]+)*", path))
    return docker+["exec", "-i", "--user", "postgres", database["Id"], tools["env"], "-i",
                   "PATH="+path, "LC_ALL=C", "PGCONNECT_TIMEOUT=5", tools[executable], "--no-password",
                   "--host=/var/run/postgresql", "--port=5432", "--username=postgres", "--dbname=pals"]


def sql(docker, database, tools, query):
    return run(pg_command(docker, database, tools, "psql")+["-X", "-qAt", "-v", "ON_ERROR_STOP=1"],
               ("BEGIN READ ONLY;\n"+query+"\nROLLBACK;\n").encode())[1].decode().strip()


def require_drain_definition(docker, api):
    code = "import json;from app.release.mac_production_database_update import _DRAIN_CHECKS;print(json.dumps(_DRAIN_CHECKS))"
    require(json.loads(run(docker+["exec", api["Id"], "python", "-c", code])[1]) == DRAIN,
            "actual_authority_drain_definition_changed")


def drained(docker, database, tools):
    for table, predicate in DRAIN:
        if sql(docker, database, tools, "SELECT EXISTS(SELECT 1 FROM "+table+" WHERE "+predicate+");") != "f":
            return False
    if sql(docker, database, tools, "SELECT to_regclass('public.project_material_extractions');"):
        return sql(docker, database, tools, "SELECT EXISTS(SELECT 1 FROM public.project_material_extractions WHERE status IN ('queued','processing') OR lease_until IS NOT NULL);") == "f"
    return True


def external_bindings(policy, api):
    env = actor_environment(api)
    key = private(Path(policy["guest_hash_key_file"]), 65).decode("ascii").removesuffix("\n")
    require(re.fullmatch(r"[0-9a-fA-F]{64}", key) and
            re.fullmatch(r"[0-9a-fA-F]{64}", env["PALS_GUEST_HASH_KEY"]))
    require(bytes.fromhex(key) == bytes.fromhex(env["PALS_GUEST_HASH_KEY"]))
    def queue(name):
        parsed = urlsplit(env[name])
        require(parsed.scheme == "https" and parsed.hostname == "sqs."+REGION+".amazonaws.com" and
                not parsed.query and not parsed.fragment)
        pieces = parsed.path.split("/")
        require(len(pieces) == 3 and pieces[1] == ACCOUNT and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", pieces[2]))
        return "arn:aws:sqs:"+REGION+":"+ACCOUNT+":"+pieces[2]
    bindings = {"cognito_user_pool_id": env["PALS_COGNITO_USER_POOL_ID"],
                "cognito_app_client_id": env["PALS_COGNITO_APP_CLIENT_ID"],
                "cognito_issuer": env["PALS_COGNITO_ISSUER"], "artifact_bucket": env["PALS_S3_ARTIFACT_BUCKET"],
                "proof_jobs_queue_arn": queue("PALS_SQS_PROOF_JOBS_QUEUE_URL"),
                "proof_requests_queue_arn": queue("PALS_PROOF_REQUESTS_QUEUE_URL"),
                "guest_key_sha256": sha(bytes.fromhex(key))}
    require(bindings["proof_jobs_queue_arn"] != bindings["proof_requests_queue_arn"])
    require(re.fullmatch(r"ap-northeast-1_[A-Za-z0-9]+", bindings["cognito_user_pool_id"]) and
            re.fullmatch(r"[a-z0-9]{1,128}", bindings["cognito_app_client_id"]) and
            bindings["cognito_issuer"] == "https://cognito-idp."+REGION+".amazonaws.com/"+bindings["cognito_user_pool_id"] and
            re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bindings["artifact_bucket"]))
    return bindings


def image_identity(docker, database, output):
    item = result(docker+["image", "inspect", database["Image"]])[0]
    require(item["Id"] == database["Image"] and item["Os"] == "linux" and item["Architecture"] == "arm64")
    archive = output/"source-image.tar"
    with os.fdopen(os.open(archive, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600), "wb") as stream:
        run(docker+["image", "save", database["Image"]], output=stream, timeout=180, maximum=MAX_ARTIFACT)
        stream.flush(); os.fsync(stream.fileno())
    with tarfile.open(archive, "r:") as saved:
        members = saved.getmembers(); require(len(members) <= 20000)
        require(all(m.isfile() or m.isdir() for m in members))
        manifest_member = saved.getmember("manifest.json")
        require(manifest_member.isfile() and manifest_member.size <= MAX_METADATA)
        manifest = json.load(saved.extractfile(manifest_member)); require(len(manifest) == 1)
        name = manifest[0]["Config"]; path = PurePosixPath(name)
        require(not path.is_absolute() and ".." not in path.parts and len(name) < 256)
        member = saved.getmember(name); require(member.isfile() and member.size <= MAX_METADATA)
        config = saved.extractfile(member).read(MAX_METADATA+1); require(len(config) <= MAX_METADATA)
    value = document(config)
    require(value["architecture"] == "arm64" and value["os"] == "linux" and
            value["rootfs"]["type"] == "layers" and value["rootfs"]["diff_ids"] == item["RootFS"]["Layers"])
    require(value["rootfs"]["diff_ids"] and all(IMAGE.fullmatch(x) for x in value["rootfs"]["diff_ids"]))
    write(output/"source-image-config.json", config)
    reference = database["Config"]["Image"]
    require(re.fullmatch(r"[A-Za-z0-9_./:@+-]{1,512}@sha256:[0-9a-f]{64}", reference))
    return {"image_uri": reference, "image_id": database["Image"],
            "source_docker_image_id": database["Image"], "source_image_config_sha256": sha(config),
            "source_image_rootfs_diff_ids": value["rootfs"]["diff_ids"]}


def file_hash(path):
    digest = hashlib.sha256(); size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""):
            size += len(block); require(size <= MAX_ARTIFACT); digest.update(block)
    return digest.hexdigest(), size


def upload(output, names, prefix, smoke=False):
    artifacts = {}
    for name in names:
        path = output/name; digest, size = file_hash(path)
        key = prefix+name
        response = cli("s3api", "put-object", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT,
                       "Key": key, "ServerSideEncryption": "AES256", "Metadata": {"sha256": digest},
                       "ChecksumSHA256": base64.b64encode(bytes.fromhex(digest)).decode()},
                       ["--body", str(path)])
        version = response.get("VersionId")
        require(isinstance(version, str) and version and version != "null")
        head = cli("s3api", "head-object", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT,
                   "Key": key, "VersionId": version, "ChecksumMode": "ENABLED"})
        require(head["ContentLength"] == size and head["Metadata"].get("sha256") == digest and
                head["ServerSideEncryption"] == "AES256" and
                head["ChecksumSHA256"] == base64.b64encode(bytes.fromhex(digest)).decode())
        artifacts[name] = {"key": key, "version_id": version, "sha256": digest, "size_bytes": size}
    marker = encoded({"schema_version": "pals.ec2-source.smoke-bundle.v1" if smoke else "pals.ec2-source.final-bundle.v1",
                      "admission_eligible": False, "artifacts": artifacts})
    write(output/"upload-manifest.json", marker)
    response = cli("s3api", "put-object", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT,
                   "Key": prefix+"manifest.json", "ServerSideEncryption": "AES256",
                   "Metadata": {"sha256": sha(marker)},
                   "ChecksumSHA256": base64.b64encode(hashlib.sha256(marker).digest()).decode()},
                   ["--body", str(output/"upload-manifest.json")])
    require(response.get("VersionId") not in (None, "", "null"))
    head = cli("s3api", "head-object", {"Bucket": BUCKET, "ExpectedBucketOwner": ACCOUNT,
               "Key": prefix+"manifest.json", "VersionId": response["VersionId"], "ChecksumMode": "ENABLED"})
    require(head["ContentLength"] == len(marker) and head["Metadata"].get("sha256") == sha(marker) and
            head["ServerSideEncryption"] == "AES256" and
            head["ChecksumSHA256"] == base64.b64encode(hashlib.sha256(marker).digest()).decode())
    write(output/"upload-receipt.json", encoded({"bucket": BUCKET, "key": prefix+"manifest.json",
          "version_id": response["VersionId"], "manifest_sha256": sha(marker), "admission_eligible": False}))


def stage(root):
    parent = root/"aws-migration-20261030"
    require(parent.resolve(strict=True) == parent and not parent.stat().st_mode & 0o077)
    capture_root = parent/"source-final"
    if not capture_root.exists():
        capture_root.mkdir(mode=0o700)
    require(capture_root.resolve(strict=True) == capture_root and
            capture_root.stat().st_uid == os.geteuid() and not capture_root.stat().st_mode & 0o077)
    output = capture_root/uuid4().hex
    output.mkdir(mode=0o700)
    (output/"inputs").mkdir(mode=0o700)
    (output/"artifacts").mkdir(mode=0o700)
    return output


def reference_path(policy, name, root):
    path = Path(policy[name])
    require(root in path.parents and path.is_absolute())
    return path


def read_volume_marker(docker, policy, database):
    """Observe the controller's existing identity volume without adding a DB mount."""
    volume = policy["identity_volume"]
    require(type(volume) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", volume))
    inside = policy.get("database_marker_inside_container", False)
    require(type(inside) is bool)
    if inside:
        require(any(m["Type"] == "volume" and m.get("Name") == volume and
                    m["Destination"] == "/run/pals-volume" for m in database["Mounts"]),
                "actual_DB_identity_volume_not_mounted")
        marker = run(docker+["exec", "--user", "0:0", database["Id"], "cat",
                            "/run/pals-volume/volume.identity"])[1]
    else:
        # Inspect first: Docker otherwise creates a missing named volume, even
        # for a read-only mount. Use the already observed source image ID.
        observed = result(docker+["volume", "inspect", volume])
        require(type(observed) is list and len(observed) == 1 and observed[0]["Name"] == volume and
                observed[0]["Driver"] == "local")
        require(IMAGE.fullmatch(database["Image"]))
        image = result(docker+["image", "inspect", database["Image"]])
        require(type(image) is list and len(image) == 1 and image[0]["Id"] == database["Image"] and
                image[0]["Os"] == "linux" and image[0]["Architecture"] == "arm64")
        marker = run(docker+["run", "--rm", "--pull=never", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges:true", "--pids-limit=32", "--memory=64m",
            "--log-driver=none", "--name", "pals-source-volume-observer-"+uuid4().hex,
            "--label", "pals.migration.purpose=source-volume-observer", "--mount",
            "type=volume,source="+volume+",target=/identity,readonly,volume-nocopy",
            "--entrypoint", "cat", database["Image"], "/identity/volume.identity"])[1]
    require(len(marker) <= 128 and marker.decode("ascii").removesuffix("\n") ==
            policy["database_identity"]["database_volume_id"])
    return marker


def prepare_inputs(root, output, policy, current, docker, items, public, dump_sha):
    inputs, artifacts = output/"inputs", output/"artifacts"
    files = {"predecessor_manifest_file": ("previous-manifest.jcs", "signed_predecessor_manifest"),
             "predecessor_signature_file": ("previous-signature.der", "signed_predecessor_signature"),
             "historical_registry_file": ("historical-registry.json", "previous_production_registry"),
             "host_marker_file": ("host-marker", "host_marker")}
    config = {"schema_version": "pals.cloud-restore.ec2-offline-source-config.v1",
              "aws_account_id": ACCOUNT, "aws_region": REGION, "kms_key_arn": KEY,
              "public_key_spki_sha256": policy["kms_public_key_sha256"],
              "public_key_file": "/inputs/public-key.der", "database_url_file": "/inputs/master-url",
              "volume_marker_file": "/inputs/volume-marker", "deployment_lock_file": "/deployment-lock",
              "pg_dump_sha256": dump_sha,
              "dump_file": "/output/source.dump", "schema_file": "/output/schema.sql",
              "roles_file": "/output/roles.jcs", "authority_file": "/output/authority.jcs",
              "payload_file": "/output/source-payload.jcs",
              "preserved_external_bindings": external_bindings(policy, items[ACTORS["api"]])}
    for field, (filename, selected) in files.items():
        raw = private(reference_path(policy, selected, root), private_mode=False)
        if field == "predecessor_manifest_file":
            require(sha(raw) == current["manifest_sha256"])
        write(inputs/filename, raw)
        config[field] = "/inputs/"+filename
    write(inputs/"public-key.der", public)
    url = private(Path(policy["database_urls"]["master_database_url"])).decode().strip()
    parsed = urlsplit(url)
    require(parsed.scheme in ("postgresql", "postgresql+psycopg") and parsed.path == "/pals"
            and unquote(parsed.username or "") == "postgres" and parsed.password and not parsed.query
            and not parsed.fragment and not any(ord(c) < 32 for c in url)
            and not any(ord(c) < 32 or ord(c) == 127 for c in unquote(parsed.password)))
    url = urlunsplit(("postgresql", parsed.netloc.rsplit("@", 1)[0]+"@127.0.0.1:5432", "/pals", "", ""))
    write(inputs/"master-url", url.encode())
    marker = read_volume_marker(docker, policy, items[DATABASE])
    write(inputs/"volume-marker", marker)
    write(inputs/"capture-config.json", encoded(config))
    require(not any(artifacts.iterdir()))


def line(process, maximum=4096, timeout=190):
    deadline = min(DEADLINE, time.monotonic()+timeout)
    data = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            require(time.monotonic() < deadline, "tool_stdio_timeout")
            if not selector.select(0.2):
                continue
            block = os.read(process.stdout.fileno(), 1)
            require(block, "tool_stdio_closed")
            data.extend(block); require(len(data) <= maximum)
            if block == b"\n":
                return document(bytes(data))


def capture_tool(root, output, policy, docker, items, image, tools, smoke):
    name = "pals-source-capture-"+output.name[:16]
    require(not run(docker+["ps", "-aq", "--filter", "name=^/"+name+"$"])[1].strip())
    args = docker_tool(docker, image, name,
                       [(output/"inputs", "/inputs", True), (output/"artifacts", "/output", False),
                        (Path(policy["state_dir"])/"deploy.lock", "/deployment-lock", True)],
                       network="container:"+items[DATABASE]["Id"], interactive=True)
    args += ["-m", "app.release.cloud_restore_ec2_source",
             "smoke-capture-unsigned" if smoke else "capture-unsigned", "--config", "/inputs/capture-config.json"]
    # Error output is discarded: the API has a static diagnostic; no private SQL
    # exception or configuration can escape to the operator's console.
    with subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, env=environment(), start_new_session=True,
                          pass_fds=(() if LOCK_FD is None else (LOCK_FD,))) as process:
        try:
            ready = line(process)
            require(set(ready) == {"event", "snapshot", "admission_eligible"} and
                    ready["event"] == "snapshot_ready" and ready["admission_eligible"] is False and
                    isinstance(ready["snapshot"], str) and
                    re.fullmatch(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{8}-[0-9]+", ready["snapshot"]))
            for filename, flag in (("source.dump", "--format=custom"), ("schema.sql", "--schema-only")):
                target = output/"artifacts"/filename
                with os.fdopen(os.open(target, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600), "wb") as stream:
                    run(pg_command(docker, items[DATABASE], tools, "pg_dump")+
                        [flag, "--snapshot="+ready["snapshot"]], output=stream, timeout=180, maximum=MAX_ARTIFACT)
                    stream.flush(); os.fsync(stream.fileno())
                if filename == "source.dump":
                    with target.open("rb") as stream:
                        require(stream.read(5) == b"PGDMP")
            process.stdin.write(b'{"action":"dumps-complete"}\n'); process.stdin.flush(); process.stdin.close()
            observed = line(process)
            process.wait(timeout=30)
            expected = "smoke_unsigned_not_admissible" if smoke else "final_unsigned_requires_real_kms_and_source_stop_fence"
            require(process.returncode == 0 and observed.get("status") == expected and
                    observed.get("admission_eligible") is False)
            raw = private(output/"artifacts/source-payload.jcs")
            require(sha(raw) == observed["payload_sha256"])
            payload = document(raw)
            require(payload["schema_version"] == ("pals.cloud-restore.ec2-rehearsal-unsigned.v1" if smoke else
                                                   "pals.cloud-restore.source-evidence.v1"))
            return raw
        finally:
            if process.poll() is None:
                # A separate short cleanup allowance must work after capture's
                # startup budget expires. Only this exact tool image/name is stopped.
                try:
                    probe = subprocess.run(docker+["inspect", name], capture_output=True, timeout=5,
                                           env=environment(), check=False)
                    if probe.returncode == 0 and len(probe.stdout) <= MAX_METADATA:
                        actual = json.loads(probe.stdout)[0]
                        if actual["Image"] == image and (actual["Config"].get("Labels") or {}).get(
                                "pals.migration.purpose") == "ec2-source-capture":
                            subprocess.run(docker+["stop", "--time", "10", actual["Id"]],
                                           capture_output=True, timeout=15, env=environment(), check=False)
                except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                    pass
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)


def journal_path(root):
    return root/"aws-migration-20261030/source-final-journal.json"


def inspect_final_state(root, policy, docker):
    """Public state under BOTH existing native locks. No SQL/tool/AWS."""
    state = Path(policy["state_dir"])
    with existing_lock(state/"host-update.lock") as verify_host, \
            existing_lock(state/"deploy.lock") as verify_deploy:
        current_policy, _, current_docker, _ = controller(root)
        require(current_policy == policy and current_docker == docker)
        actual = _inspect_final_state(root, policy, docker)
        verify_host(); verify_deploy()
        return actual


def _inspect_final_state(root, policy, docker):
    names = [*ACTORS.values(), policy["edge_container"], DATABASE]
    observed = result(docker+["inspect", *names])
    require(type(observed) is list and len(observed) == len(names))
    items = {item["Name"].removeprefix("/"): item for item in observed}
    require(set(items) == set(names))
    containers = {}
    for name, item in items.items():
        restart = item["HostConfig"]["RestartPolicy"]["Name"]
        require(HEX.fullmatch(item["Id"]) and IMAGE.fullmatch(item["Image"]) and
                type(item["State"]["Running"]) is bool and
                restart in {"no", "always", "unless-stopped", "on-failure"})
        containers[name] = {"id": item["Id"], "running": item["State"]["Running"],
                            "restart_policy": restart}
    database = items[DATABASE]
    reference = database["Config"]["Image"]
    require(type(reference) is str and 0 < len(reference) <= 512 and
            re.fullmatch(r"[a-zA-Z0-9._/:@-]+", reference))
    images = result(docker+["image", "inspect", database["Image"]])
    require(type(images) is list and len(images) == 1 and images[0]["Id"] == database["Image"])
    digests = images[0].get("RepoDigests") or []
    require(type(digests) is list and len(digests) <= 64 and all(type(value) is str and len(value) <= 512 and
            re.fullmatch(r"[a-zA-Z0-9._/:-]+@sha256:[0-9a-f]{64}", value) for value in digests))
    path = journal_path(root)
    state = {"exists": os.path.lexists(path), "phase": None, "capture_completed": None,
             "read_status": "absent"}
    if state["exists"]:
        state["read_status"] = "unavailable"
        try:
            data = document(private(path))
            phases = {"ingress_stop_pending", "ingress_stopped_draining", "writers_stop_pending",
                      "writers_stopped_capture_pending", "capture_complete_db_fence_pending",
                      "database_stop_pending", "writer_restart_disable_pending", "source_fenced_sign_pending",
                      "source_fenced_upload_pending", "uploaded_source_fenced", "failed_reconcile_required"}
            require(data.get("phase") in phases and type(data.get("capture_completed")) is bool)
            state.update(phase=data["phase"], capture_completed=data["capture_completed"], read_status="validated")
        except (OSError, ValueError, TypeError, KeyError, Refusal):
            pass
    return {"status": "source_final_state_observed", "admission_eligible": False, "journal": state,
            "containers": containers, "database": {"config_image": reference,
            "docker_image_id": database["Image"], "repo_digests": digests}}


def journal(root, state, phase):
    state["phase"] = phase
    write(journal_path(root), encoded(state), replace=True)


def facts(items):
    return {name: {key: canonical_mounts(item[key]) if key == 'Mounts' else item[key]
                   for key in ("Id", "Image", "Mounts")}
            for name, item in items.items()}


def stopped(items):
    return all(item["State"]["Running"] is False and
               item["HostConfig"]["RestartPolicy"]["Name"] == "no" and
               not item["HostConfig"]["RestartPolicy"].get("MaximumRetryCount", 0)
               for item in items.values())


def require_maintenance(root):
    # This is the watchdog's existing planned-maintenance contract. A source
    # stop alone is unsafe: recovery could restart writers after our lock exits.
    path = root/"auto-recovery/disabled.json"
    try:
        document(private(path))
        info = path.lstat()
        require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o600)
    except (OSError, ValueError, Refusal):
        raise Refusal("source_recovery_maintenance_required") from None


def fence(items, identity, source_envelope, policy_sha, policy, phase):
    require(phase in ("stopped-after-final-capture", "stopped-before-target-admission") and stopped(items))
    source = document(base64.b64decode(document(source_envelope)["payload_b64"], validate=True))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    lifetime = timedelta(minutes=5) if phase == "stopped-before-target-admission" else timedelta(hours=1)
    database = items[DATABASE]
    return {"schema_version": FENCE, "evidence_id": str(uuid4()),
            "issued_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now+lifetime).isoformat().replace("+00:00", "Z"),
            "aws_account_id": ACCOUNT, "aws_region": REGION, "kms_key_arn": KEY,
            "public_key_spki_sha256": policy["kms_public_key_sha256"],
            "source_evidence_sha256": sha(source_envelope),
            "predecessor_manifest_sha256": source["predecessor_manifest_sha256"],
            "controller_policy_sha256": policy_sha,
            "source_database_system_identifier": source["source_identity"]["database_system_identifier"],
            "database_container": {**identity, "id": database["Id"],
                                   "data_volume_id": source["source_identity"]["database_volume_id"],
                                   "running": False, "restart_policy": "no"},
            "writer_containers": [{"id": item["Id"], "running": False, "restart_policy": "no"}
                                  for name, item in sorted(items.items()) if name != DATABASE],
            "phase": phase}


def capture(root, args, policy, current, docker, binding, items, verify):
    global PHASE
    PHASE='maintenance_guard'
    if args.final:
        require_maintenance(root)
    PHASE='source_running_guard'
    require_running(items, current)
    PHASE='drain_definition_guard'
    require_drain_definition(docker, items[ACTORS["api"]])
    PHASE='source_tools_guard'
    tools, dump_sha = source_tools(docker, items[DATABASE])
    if not getattr(args, 'host_native_locks', False):
        PHASE='native_lock_probe'
        probe_lock(docker, args.tool_image, Path(policy["state_dir"])/"deploy.lock")
    PHASE='predecessor_guard'
    previous = private(reference_path(policy, "signed_predecessor_manifest", root), private_mode=False)
    signature = private(reference_path(policy, "signed_predecessor_signature", root), private_mode=False)
    require(sha(previous) == current["manifest_sha256"] and document(previous)["kms_key_arn"] == KEY)
    PHASE='aws_preflight';public = aws_preflight(policy, previous, signature)
    PHASE='explicit_final_confirmation'
    require(not args.final or args.confirm_source_manifest == current["manifest_sha256"],
            "explicit_final_source_confirmation_required")
    PHASE='journal_guard'
    require(not args.final or not journal_path(root).exists(), "existing_final_journal_requires_reconcile")
    PHASE='prepare_stage';output = stage(root)
    PHASE='prepare_inputs'
    prepare_inputs(root, output, policy, current, docker, items, public, dump_sha)
    PHASE='source_image_identity'
    identity = image_identity(docker, items[DATABASE], output/"artifacts")
    state = {"schema_version": "pals.ec2-source-host-journal.v1", "output_directory": str(output),
             "controller_policy_sha256": sha(binding[0]), "controller_current_sha256": sha(binding[1]),
             "source_facts": facts(items), "source_image_identity": identity,
             "tool_image": args.tool_image, "tool_api_commit": args.tool_api_commit,
             "capture_completed": False, "admission_eligible": False}
    def recheck():
        global PHASE
        previous_phase = PHASE
        if args.final:
            PHASE='recheck_maintenance'
            require_maintenance(root)
        PHASE='recheck_native_locks';verify()
        PHASE='recheck_controller_read'; observed_binding = controller(root)[3]
        PHASE='recheck_controller_binding'
        if observed_binding != binding:
            error=Refusal('controller_changed')
            error.controller_changed_fields=[name for name,old,new in zip(('policy','current','config'),binding,observed_binding) if old != new]
            raise error
        PHASE='recheck_container_inspect';actual = inspect_all(docker, policy["edge_container"])
        PHASE='recheck_container_identity';require_same(items, actual)
        PHASE=previous_phase
        return actual
    def mutate(arguments, timeout=30):
        recheck()
        return run(docker+arguments, timeout=timeout)
    try:
        PHASE='source_recheck'
        recheck()
        if args.final:
            PHASE='ingress_stop'
            journal(root, state, "ingress_stop_pending")
            mutate(["stop", "--time", "15", items[policy["edge_container"]]["Id"]])
            require(recheck()[policy["edge_container"]]["State"]["Running"] is False)
            journal(root, state, "ingress_stopped_draining")
            PHASE='authority_drain'
            for _attempt in range(60):
                if drained(docker, items[DATABASE], tools):
                    break
                require(time.monotonic() < DEADLINE); time.sleep(1)
            else:
                raise Refusal("source_workload_not_drained")
            journal(root, state, "writers_stop_pending")
            PHASE='writers_stop'
            mutate(["stop", "--time", "30", *[items[n]["Id"] for n in ACTORS.values()]], timeout=110)
            require(all(recheck()[name]["State"]["Running"] is False for name in ACTORS.values()))
            PHASE='post_stop_drain'
            require(drained(docker, items[DATABASE], tools), "work_reappeared_after_writer_stop")
            journal(root, state, "writers_stopped_capture_pending")
        PHASE='snapshot_tool'
        raw = capture_tool(root, output, policy, docker, items, args.tool_image, tools, not args.final)
        # Default profile reacquires native deploy.lock after the guest exits.
        # The explicit independent-domain profile already holds both native
        # locks in main; the unchanged API tool still takes its real guest lock.
        PHASE='native_lock_handoff'
        with existing_lock(Path(policy["state_dir"])/"deploy.lock") if args.final and not getattr(args, 'host_native_locks', False) else nullcontext():
            state["capture_completed"] = True
            names = ["source.dump", "schema.sql", "roles.jcs", "authority.jcs", "source-payload.jcs",
                     "source-image-config.json"]
            # Historical registry remains necessary for target predecessor validation.
            PHASE='archive_registry'
            write(output/"artifacts/historical-registry.json", private(output/"inputs/historical-registry.json"))
            names.append("historical-registry.json")
            if args.final:
                journal(root, state, "capture_complete_db_fence_pending")
                recheck()
                PHASE='database_restart_disable'
                mutate(["update", "--restart=no", items[DATABASE]["Id"]])
                journal(root, state, "database_stop_pending")
                PHASE='database_stop'
                mutate(["stop", "--time", "60", items[DATABASE]["Id"]], timeout=75)
                journal(root, state, "writer_restart_disable_pending")
                PHASE='writers_restart_disable'
                mutate(["update", "--restart=no", *[items[n]["Id"] for n in
                    [*ACTORS.values(), policy["edge_container"]]]])
                PHASE='source_fence_check'
                actual = recheck(); require(stopped(actual), "persistent_source_fence_not_observed")
                journal(root, state, "source_fenced_sign_pending")
                PHASE='source_sign';source_signed = signed(raw)
                write(output/"artifacts/source-evidence.jcs", source_signed)
                observed = fence(actual, identity, source_signed, sha(binding[0]), policy, "stopped-after-final-capture")
                PHASE='fence_sign';write(output/"artifacts/source-fence.jcs", signed(encoded(observed)))
                names += ["source-evidence.jcs", "source-fence.jcs"]
                journal(root, state, "source_fenced_upload_pending")
            prefix = "aws-migration-20261030/"+("final/" if args.final else "source-smoke/")+output.name+"/"
            PHASE='upload';upload(output/"artifacts", names, prefix, smoke=not args.final)
            if args.final:
                PHASE='final_state_check'
                require(stopped(recheck()))
                journal(root, state, "uploaded_source_fenced")
            return {"status": "final_uploaded_source_fenced" if args.final else "smoke_uploaded_not_admissible",
                    "session": output.name, "admission_eligible": False}
    except BaseException:
        if args.final and journal_path(root).exists():
            state["failed_phase"] = state.get("phase")
            journal(root, state, "failed_reconcile_required")
        raise
    finally:
        # This is a temporary loopback rewrite, not the controller's original.
        # Do not retain an unnecessary duplicate of the source master URL.
        copied_url = output/"inputs/master-url"
        if copied_url.exists():
            copied_url.unlink()


def reconcile(root, args, policy, docker, binding, items):
    state = document(private(journal_path(root)))
    require(state["schema_version"] == "pals.ec2-source-host-journal.v1" and
            state["controller_policy_sha256"] == sha(binding[0]) and
            state["controller_current_sha256"] == sha(binding[1]) and
            state["source_facts"] == facts(items), "reconcile_source_identity_changed")
    require(type(state["capture_completed"]) is bool and state["phase"] in {
        "ingress_stop_pending", "ingress_stopped_draining", "writers_stop_pending",
        "writers_stopped_capture_pending", "capture_complete_db_fence_pending",
        "database_stop_pending", "writer_restart_disable_pending", "source_fenced_sign_pending",
        "source_fenced_upload_pending", "uploaded_source_fenced", "failed_reconcile_required"})
    if not args.refresh_fence:
        return {"status": "source_fenced_stopped" if stopped(items) else "source_not_fully_fenced",
                "capture_completed": state["capture_completed"], "journal_phase": state["phase"],
                "automatic_resume": False, "admission_eligible": False}
    require(state["phase"] == "uploaded_source_fenced" and stopped(items), "fresh_fence_requires_uploaded_final")
    output = Path(state["output_directory"])
    require(output.parent == root/"aws-migration-20261030/source-final")
    aws_preflight(policy, private(output/"inputs/previous-manifest.jcs"),
                  private(output/"inputs/previous-signature.der"))
    source = private(output/"artifacts/source-evidence.jcs")
    envelope = document(source)
    verify_signature(base64.b64decode(envelope["payload_b64"], validate=True),
                     base64.b64decode(envelope["signature_b64"], validate=True))
    observed_image = result(docker+["image", "inspect", items[DATABASE]["Image"]])[0]
    require(observed_image["RootFS"]["Layers"] == state["source_image_identity"]["source_image_rootfs_diff_ids"] and
            observed_image["Id"] == state["source_image_identity"]["source_docker_image_id"])
    refreshed = fence(items, state["source_image_identity"], source, sha(binding[0]), policy,
                      "stopped-before-target-admission")
    filename = "refreshed-source-fence-"+refreshed["evidence_id"]+".jcs"
    write(output/"artifacts"/filename, signed(encoded(refreshed)))
    prefix = "aws-migration-20261030/refreshed-source-fence/"+refreshed["evidence_id"]+"/"
    refresh_dir = output/("refresh-"+refreshed["evidence_id"]); refresh_dir.mkdir(mode=0o700)
    write(refresh_dir/filename, private(output/"artifacts"/filename))
    upload(refresh_dir, [filename], prefix)
    return {"status": "fresh_source_fence_uploaded", "evidence_id": refreshed["evidence_id"],
            "maximum_age_seconds": 300, "admission_eligible": False}


def main(arguments=None):
    global DEADLINE, PHASE
    DEADLINE = time.monotonic()+1200
    parser = Parser(description=__doc__)
    parser.add_argument("--tool-image")
    parser.add_argument("--tool-api-commit")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--probe-lock-propagation", action="store_true")
    mode.add_argument("--smoke", action="store_true")
    mode.add_argument("--final", action="store_true")
    mode.add_argument("--reconcile", action="store_true")
    mode.add_argument("--refresh-fence", action="store_true")
    mode.add_argument("--inspect-final-state", action="store_true")
    parser.add_argument("--confirm-source-manifest")
    parser.add_argument('--host-native-locks', action='store_true')
    args = parser.parse_args(arguments)
    require(args.inspect_final_state or (args.tool_image and args.tool_api_commit), "invalid_arguments")
    root = Path.home()/"pals-mini-deploy"
    PHASE = 'controller_preflight'
    policy, current, docker, binding = controller(root)
    state = Path(policy["state_dir"])
    if args.inspect_final_state:
        PHASE = 'inspect_final_state'
        print(json.dumps(inspect_final_state(root, policy, docker), sort_keys=True))
        return 0
    with existing_lock(state/"host-update.lock") as verify:
        require(controller(root)[3] == binding)
        PHASE = 'tool_identity'
        tool_image(docker, args.tool_image, args.tool_api_commit)
        items = inspect_all(docker, policy["edge_container"])
        if args.probe_lock_propagation:
            PHASE = 'native_lock_probe'
            probe_lock(docker, args.tool_image, state/"deploy.lock", host_native=args.host_native_locks)
            status = 'independent_native_guest_lock_domains_observed' if args.host_native_locks else 'native_container_lock_exclusion_observed'
            print(json.dumps({'status':status,'admission_eligible':False},sort_keys=True))
            return 0
        if args.reconcile or args.refresh_fence:
            with existing_lock(state/"deploy.lock"):
                if args.refresh_fence:
                    require_maintenance(root)
                verify()
                items = inspect_all(docker, policy["edge_container"])
                print(json.dumps(reconcile(root, args, policy, docker, binding, items), sort_keys=True))
            return 0
        if args.smoke or args.final:
            if args.host_native_locks:
                # Prove 0/0/0 while native deploy.lock is initially free, then
                # retain BOTH actual native locks through tool/DBstop/sign/upload.
                probe_lock(docker,args.tool_image,state/'deploy.lock',host_native=True)
                with existing_lock(state/'deploy.lock') as verify_deploy:
                    def verify_both():
                        verify();verify_deploy()
                    result=capture(root,args,policy,current,docker,binding,items,verify_both)
            else:
                result=capture(root,args,policy,current,docker,binding,items,verify)
            print(json.dumps(result,sort_keys=True))
            return 0
        require_running(items, current)
        require_drain_definition(docker, items[ACTORS["api"]])
        source_tools(docker, items[DATABASE])
        print('{"status":"source_final_read_only_plan","actor_count":8,"admission_eligible":false}')
    return 0


def failure_summary(error):
    reason = error.args[0] if type(error) is Refusal and len(error.args) == 1 and error.args[0] in FINAL_FAILURE_CODES else "guard_rejected"
    report = {"status": "source_final_failed_closed", "reason": reason,
            "phase": "final_maintenance_prerequisite" if reason == "source_recovery_maintenance_required"
            else "source_final_operation", "stage": PHASE if PHASE in CAPTURE_STAGES else "initialization",
            "action": "reconcile_before_any_retry"}
    trace = error.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code.co_filename == __file__ and trace.tb_frame.f_code.co_name != 'require' and 1 <= trace.tb_lineno <= 20000:
            report['failed_check_line'] = trace.tb_lineno
        trace = trace.tb_next
    if reason == 'source_container_changed':
        changes = getattr(error, 'changed_fields', [])
        if type(changes) is list and len(changes) <= 8 and all(type(row) is dict and set(row) == {'container','fields'} and
                type(row['container']) is str and re.fullmatch(r'pals[A-Za-z0-9_.-]{1,120}',row['container']) and
                type(row['fields']) is list and 0 < len(row['fields']) <= 4 and
                all(type(field) is str and field in {'Id','Image','Mounts','Config'} for field in row['fields']) for row in changes):
            report['changed_fields'] = changes
    if reason == 'controller_changed':
        changed = getattr(error, 'controller_changed_fields', [])
        if type(changed) is list and len(changed) <= 3 and all(type(field) is str and field in {'policy','current','config'} for field in changed):
            report['controller_changed_fields'] = changed
    return report


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001 -- closed labels only
        print(json.dumps(failure_summary(error)), file=sys.stderr)
        sys.exit(2)
