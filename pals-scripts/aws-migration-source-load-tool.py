#!/usr/bin/env python3
"""Pinned Mini tool-image loader. Default plan performs no AWS call or image load.

Requires the sibling source-final helper from this same reviewed checkout.
Never starts containers, authenticates ECR, changes source tags, or retries a load.
"""
import configparser
import importlib.util
import json
import os
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath
from uuid import uuid4

SPEC = importlib.util.spec_from_file_location("source_final", Path(__file__).with_name("aws-migration-source-final.py"))
b = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(b)
COMMIT = "7027478ef6664a0ab8f8a245e3da714e18dc0f37"
TAG = b.ACCOUNT+".dkr.ecr."+b.REGION+".amazonaws.com/pals-prod-api:migration-private-7027478"
MANIFEST_KEY = "aws-migration-20261030/tools/api-tool-transfer.json"
ARCHIVE_KEY = "aws-migration-20261030/tools/api-7027478-arm64.tar.gz"
SIZE = 149928497
ARCHIVE_SHA = "450e684cfa1ca25e752ea19925de9117e98d864efd2ecd9a23878efdf3884c40"
VERSION = "1MfCzRK8zYelAFqgiGxO1fgChCMnHC8v"
STAGE = "argument_validation"
KEYS = {"admission_eligible", "bucket", "bytes", "docker_inspect_config_json_sha256", "image_tag", "key",
        "platform", "rootfs_diff_ids", "schema_version", "sha256", "source_commit", "version_id"}


def failure(error):
    """Only fixed labels/known field names; never exception text or raw output."""
    code = "unexpected_failure"
    field = None
    if isinstance(error, b.Refusal):
        allowed = {"guard_rejected", "unsafe_path", "unsafe_parent", "unsafe_file", "duplicate_member",
                   "total_timeout", "command_timeout", "command_failed", "output_too_large",
                   "artifact_too_large", "source_transition_pending", "invalid_arguments"}
        code = error.args[0] if len(error.args) == 1 and error.args[0] in allowed else "guard_rejected"
    elif isinstance(error, KeyError):
        code = "required_field_absent"
        known = {"database_container", "edge_container", "kms_public_key_sha256", "state_dir", "containers",
                 "docker_binary", "docker_config", "docker_context", "database_identity", "status", "images",
                 "schema_version", "manifest_sha256", "Account", "RootFS", "Layers", "Config", "Labels", "Id"}
        if len(error.args) == 1 and error.args[0] in known:
            field = error.args[0]
    elif isinstance(error, BlockingIOError):
        code = "source_lock_busy"
    elif isinstance(error, FileNotFoundError):
        code = "required_path_absent"
    elif isinstance(error, PermissionError):
        code = "permission_denied"
    elif isinstance(error, (ValueError, UnicodeError)):
        code = "invalid_json_or_format"
    result = {"status": "tool_load_failed_closed", "stage": STAGE, "code": code,
              "action": "inspect_protected_files_and_image_before_retry"}
    if field:
        result["known_field"] = field
    return result


def public_inspection(root):
    """Public metadata only. Does not execute installed code, Docker, or AWS."""
    report = {"status": "tool_loader_public_controller_inspection", "admission_eligible": False}
    documents = {}
    files = {}
    for label, path, private_mode in (
            ("policy", root/"controller-policy.json", True), ("config", root/"deploy-config.json", True),
            ("watchdog", root/"auto-recovery/auto_recovery.py", False), ("controller", root/"controller.py", False)):
        entry = {"path": str(path), "exists": path.exists() or path.is_symlink()}
        try:
            raw = b.private(path, private_mode=private_mode)
            entry.update(sha256=b.sha(raw), mode=oct(path.stat().st_mode & 0o777), owned=path.stat().st_uid == os.geteuid())
            if label in ("policy", "config"):
                documents[label] = b.document(raw)
        except (OSError, ValueError, b.Refusal):
            entry["read_status"] = "unavailable_or_untrusted"
        files[label] = entry
    report["files"] = files
    policy = documents.get("policy", {})
    config = documents.get("config", {})
    fields = {}
    for name in ("database_container", "edge_container", "kms_public_key_sha256", "state_dir",
                 "runtime_profile", "containers", "docker_binary", "docker_config", "docker_context"):
        value = policy.get(name)
        fields[name] = {"present": name in policy, "type": type(value).__name__}
    fields["database_container"]["matches_fixed_source"] = policy.get("database_container") == b.DATABASE
    edge = policy.get("edge_container")
    fields["edge_container"]["valid_container_name"] = isinstance(edge, str) and bool(b.re.fullmatch(r"pals[A-Za-z0-9_.-]{1,120}", edge))
    pin = policy.get("kms_public_key_sha256")
    fields["kms_public_key_sha256"]["valid_sha256"] = isinstance(pin, str) and bool(b.HEX.fullmatch(pin))
    fields["containers"]["matches_fixed_source"] = policy.get("containers") == b.ACTORS
    fields["runtime_profile"]["matches_required"] = policy.get("runtime_profile") == "isolated-lean-v1"
    report["policy_fields"] = fields
    report["config_matches_policy"] = {key: key in policy and key in config and policy[key] == config[key]
                                        for key in ("containers", "state_dir", "docker_context", "database_identity")}
    state = policy.get("state_dir")
    locks = {}
    if isinstance(state, str) and Path(state).is_absolute() and root in Path(state).parents:
        fields["state_dir"]["path"] = state
        for name in ("host-update.lock", "deploy.lock"):
            path = Path(state)/name
            entry = {"path": str(path), "exists": path.exists() or path.is_symlink()}
            try:
                b.private(path, 1024)
                info = path.stat()
                entry.update(owned=info.st_uid == os.geteuid(), mode=oct(info.st_mode & 0o777), size=info.st_size)
            except (OSError, ValueError, b.Refusal):
                entry["read_status"] = "unavailable_or_untrusted"
            locks[name] = entry
    report["locks"] = locks
    return report


def metadata(raw, expected):
    b.require(b.sha(raw) == expected)
    value = b.document(raw)
    b.require(set(value) == KEYS and value["schema_version"] == "pals.migration-tool-image.v1" and
              value["admission_eligible"] is False and value["bucket"] == b.BUCKET and
              type(value["bytes"]) is int and value["bytes"] == SIZE and value["image_tag"] == TAG and
              value["key"] == ARCHIVE_KEY and value["platform"] == "linux/arm64" and
              value["source_commit"] == COMMIT and value["sha256"] == ARCHIVE_SHA and
              value["version_id"] == VERSION and b.HEX.fullmatch(value["docker_inspect_config_json_sha256"]))
    layers = value["rootfs_diff_ids"]
    b.require(isinstance(layers, list) and 1 <= len(layers) <= 128 and all(b.IMAGE.fullmatch(x) for x in layers))
    return value


def directory(root):
    current = root
    for name in ("aws-migration-20261030", "tools"):
        current = current/name
        if not current.exists():
            current.mkdir(mode=0o700)
        info = current.lstat()
        b.require(current.resolve(strict=True) == current and current.is_dir() and
                  info.st_uid == os.geteuid() and not info.st_mode & 0o077)
    return current


def download(folder, name, key, maximum, digest, version=None):
    path = folder/name
    if path.exists() or path.is_symlink():
        b.private(path, maximum, True)
        b.require(b.file_hash(path) == (digest, maximum) if version else b.sha(b.private(path, maximum)) == digest)
        return path
    pending = folder/(".download-"+uuid4().hex)
    b.write(pending, b"")
    request = {"Bucket": b.BUCKET, "Key": key, "ExpectedBucketOwner": b.ACCOUNT,
               "Range": "bytes=0-"+str(maximum-1)}
    if version:
        request["VersionId"] = version
    # CLI writes only our exclusive private file. Failed partial downloads stay
    # under a random name and are never reused or overwritten on a later run.
    response = b.cli("s3api", "get-object", request, [str(pending)])
    b.private(pending, maximum)
    observed, size = b.file_hash(pending)
    b.require(observed == digest and size > 0 and response["ContentLength"] == size and
              response.get("ServerSideEncryption") == "AES256")
    if version:
        b.require(response.get("VersionId") == version and size == maximum)
    os.link(pending, path)
    pending.unlink()
    return path


def archive_contract(path):
    with tarfile.open(path, "r:*") as saved:
        members = saved.getmembers()
        b.require(len(members) <= 20000 and len({m.name for m in members}) == len(members))
        for member in members:
            parsed = PurePosixPath(member.name)
            b.require(not parsed.is_absolute() and ".." not in parsed.parts and
                      (member.isfile() or member.isdir()))
        member = saved.getmember("manifest.json")
        b.require(member.isfile() and member.size < b.MAX_METADATA)
        manifests = json.load(saved.extractfile(member))
        b.require(isinstance(manifests, list) and len(manifests) == 1 and manifests[0]["RepoTags"] == [TAG])


def verify_image(docker, expected):
    observed = b.result(docker+["image", "inspect", TAG])
    b.require(isinstance(observed, list) and len(observed) == 1)
    image = observed[0]
    config_sha = b.sha(json.dumps(image["Config"], sort_keys=True, separators=(",", ":")).encode())
    b.require(b.IMAGE.fullmatch(image["Id"]) and image["Os"] == "linux" and image["Architecture"] == "arm64" and
              image["Config"]["Labels"]["org.opencontainers.image.revision"] == COMMIT and
              image["RootFS"]["Layers"] == expected["rootfs_diff_ids"] and
              config_sha == expected["docker_inspect_config_json_sha256"] and TAG in image["RepoTags"])
    return image["Id"]


def execute(root, args, policy, docker, binding, verify):
    global STAGE
    if not args.apply:
        return {"status": "tool_image_load_read_only_plan", "admission_eligible": False}
    STAGE = "aws_cli_config"
    aws_config = configparser.ConfigParser(interpolation=None)
    aws_config.read_string(b.private(Path.home()/".aws/config").decode())
    b.require(aws_config.has_section("profile "+b.PROFILE))
    for section in aws_config.sections():
        b.require(aws_config[section].get("cli_history", "disabled").strip().lower() == "disabled" and
                  "ca_bundle" not in aws_config[section] and (section != "plugins" or not aws_config[section]))
    STAGE = "aws_identity"
    b.require(b.cli("sts", "get-caller-identity")["Account"] == b.ACCOUNT)
    folder = directory(root)
    STAGE = "metadata_download"
    manifest = download(folder, args.manifest_sha256+".json", MANIFEST_KEY, 65536, args.manifest_sha256)
    STAGE = "metadata_validation"
    expected = metadata(b.private(manifest, 65536), args.manifest_sha256)
    STAGE = "existing_image"
    present = b.run(docker+["image", "ls", "--quiet", "--no-trunc", TAG])[1].decode().strip()
    if present:
        image_id = verify_image(docker, expected)  # Conflicting existing tag is never overwritten.
    else:
        STAGE = "archive_download"
        archive = download(folder, ARCHIVE_SHA+".tar.gz", ARCHIVE_KEY, SIZE, ARCHIVE_SHA, VERSION)
        STAGE = "archive_contract"
        archive_contract(archive)
        verify(); b.require(b.controller(root)[3] == binding)
        b.require(not b.run(docker+["image", "ls", "--quiet", "--no-trunc", TAG])[1].strip())
        STAGE = "image_load"
        b.run(docker+["image", "load", "--input", str(archive)], timeout=180)
        STAGE = "loaded_image_validation"
        image_id = verify_image(docker, expected)
    STAGE = "receipt_write"
    receipt = b.encoded({"schema_version": "pals.migration-tool-load.v1", "manifest_sha256": args.manifest_sha256,
                         "source_docker_image_id": image_id, "admission_eligible": False})
    receipt_path = folder/(args.manifest_sha256+"-loaded.json")
    if receipt_path.exists():
        b.require(b.private(receipt_path) == receipt)
    else:
        b.write(receipt_path, receipt)
    return {"source_docker_image_id": image_id, "admission_eligible": False}


def main(arguments=None):
    global STAGE
    STAGE = "argument_validation"
    b.DEADLINE = time.monotonic()+300
    parser = b.Parser(description=__doc__)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--inspect-controller", action="store_true")
    args = parser.parse_args(arguments)
    root = Path.home()/"pals-mini-deploy"
    if args.inspect_controller:
        b.require(not args.apply and args.manifest_sha256 is None, "invalid_arguments")
        print(json.dumps(public_inspection(root), sort_keys=True))
        return 0
    b.require(isinstance(args.manifest_sha256, str) and b.HEX.fullmatch(args.manifest_sha256), "invalid_arguments")
    STAGE = "controller_read"
    policy, _current, docker, binding = b.controller(root)
    STAGE = "source_lock"
    with b.existing_lock(Path(policy["state_dir"])/"host-update.lock") as verify:
        verify(); b.require(b.controller(root)[3] == binding)
        print(json.dumps(execute(root, args, policy, docker, binding, verify), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001 -- no AWS/Docker diagnostic disclosure
        print(json.dumps(failure(error), sort_keys=True), file=sys.stderr)
        sys.exit(2)
