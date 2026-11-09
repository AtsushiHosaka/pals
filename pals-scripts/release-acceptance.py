#!/usr/bin/env python3
"""Live, read-only release qualification. Never accepts caller-authored PASS evidence."""
from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import inspect
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

SCHEMA = "pals.release-acceptance.v1"
HEX = re.compile(r"[a-f0-9]{64}\Z")
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
ROLES = {"api": "api", "reconciler": "api", "web": "web",
         "proof": "worker", "assessment": "worker", "verifier": "verifier"}
HERE = Path(__file__).resolve().parent


class Refusal(ValueError):
    pass


class ProductFailure(Refusal):
    def __init__(self, code, observation):
        super().__init__(code)
        self.observation = observation


class SSMNotReady(Refusal):
    pass


def need(value, code):
    if not value:
        raise Refusal(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(parsed.tzinfo is not None, "timestamp_requires_timezone")
    return parsed


def private_file(path):
    path = Path(path)
    need(path.is_absolute() and path.resolve(strict=True) == path, "unsafe_private_path")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
             and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
             and 0 < info.st_size <= 2**20, "unsafe_private_file")
        return stream.read(2**20 + 1)


def document(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "duplicate_json_member")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique)
    need(isinstance(value, dict), "json_object_required")
    return value


def command(args, *, timeout=30):
    completed = subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    need(completed.returncode == 0, "required_command_failed")
    need(len(completed.stdout) <= 2**23, "command_output_unbounded")
    return completed.stdout


def runner_fingerprint():
    return digest(b"".join(path.name.encode() + b"\0" + path.read_bytes() + b"\0"
                          for path in (Path(__file__).resolve(), HERE / "release-acceptance-browser.cjs")))


def validate_contract(value):
    need(set(value) == {"schema_version", "phase", "target", "manifest", "runtime",
                        "runner_sha256", "web_root", "web_origin", "api_origin", "auth_origin", "request",
                        "timeout_seconds", "max_age_seconds"}, "contract_members_differ")
    need(value["schema_version"] == SCHEMA and value["phase"] in {"pre_release", "post_deployment"}
         and value["target"] in {"staging", "production"}, "contract_target_invalid")
    need(value["phase"] != "pre_release" or value["target"] == "staging", "pre_release_requires_staging")
    need(value["runner_sha256"] == runner_fingerprint(), "executing_runner_changed")
    for name in ("web_origin", "api_origin"):
        url = urlsplit(value[name])
        need(url.username is None and url.password is None and not url.query and not url.fragment
             and url.path in {"", "/"} and url.hostname and value[name].rstrip("/") == value[name]
             and (url.scheme == "https" or value["target"] == "staging"
                  and url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}),
             "unsafe_acceptance_origin")
    if value["auth_origin"] is not None:
        auth = urlsplit(value["auth_origin"])
        need(auth.scheme == "https" and auth.hostname and not auth.username and not auth.password
             and not auth.query and not auth.fragment and auth.path == "", "unsafe_auth_origin")
    need(type(value["timeout_seconds"]) is int and 30 <= value["timeout_seconds"] <= 1800
         and type(value["max_age_seconds"]) is int and 1 <= value["max_age_seconds"] <= 3600,
         "acceptance_window_invalid")
    runtime = value["runtime"]
    need(set(runtime) == set(ROLES), "all_runtime_roles_required")
    for role, binding in runtime.items():
        local_keys = {"context", "endpoint_sha256", "container", "config_sha256", "environment_sha256"}
        remote_keys = {"ssm", "container", "config_sha256", "environment_sha256"}
        need(set(binding) in (local_keys, remote_keys)
             and all(isinstance(binding[k], str) and HEX.fullmatch(binding[k])
                     for k in ("config_sha256", "environment_sha256"))
             and isinstance(binding["container"], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", binding["container"]),
             "runtime_binding_invalid")
        if "ssm" in binding:
            ssm = binding["ssm"]
            need(set(ssm) == {"profile", "region", "account_id", "instance_id"}
                 and ssm["profile"] == "pals-prod-member" and ssm["region"] == "ap-northeast-1"
                 and isinstance(ssm["account_id"], str) and re.fullmatch(r"[0-9]{12}", ssm["account_id"])
                 and isinstance(ssm["instance_id"], str) and re.fullmatch(r"i-[a-f0-9]{8,17}", ssm["instance_id"]),
                 "ssm_target_invalid")
        else:
            need(isinstance(binding["endpoint_sha256"], str) and HEX.fullmatch(binding["endpoint_sha256"])
                 and isinstance(binding["context"], str)
                 and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", binding["context"]), "docker_target_invalid")
    request = value["request"]
    need(set(request) == {"id", "chat_id", "generation_model", "reasoning_effort", "output_language",
                          "required_conclusion_text", "required_conclusion_math"}, "request_contract_invalid")
    deferred = value["phase"] == "post_deployment" and request["id"] is None and request["chat_id"] is None
    if not deferred:
        for key in ("id", "chat_id"):
            need(str(UUID(request[key])) == request[key], "canonical_request_id_required")
    need(request["output_language"] in {"en", "ja", "zh-Hans", "zh-Hant"}
         and request["reasoning_effort"] in {None, "low", "medium", "high"}
         and isinstance(request["generation_model"], str) and request["generation_model"].strip(),
         "request_configuration_invalid")
    for key in ("required_conclusion_text", "required_conclusion_math"):
        need(isinstance(request[key], list) and len(request[key]) <= 20
             and all(isinstance(x, str) and 0 < len(x.strip()) <= 2000 for x in request[key]),
             "conclusion_expectation_invalid")
    need(request["required_conclusion_text"] or request["required_conclusion_math"], "conclusion_oracle_required")
    return value


def effective_contract(contract, request_id, chat_id):
    result = json.loads(encoded(contract))
    need((request_id is None) == (chat_id is None), "both_request_identity_overrides_required")
    if request_id is not None:
        need(contract["phase"] == "post_deployment", "identity_override_only_after_deployment")
        for identifier in (request_id, chat_id):
            need(str(UUID(identifier)) == identifier, "canonical_request_id_required")
        result["request"].update(id=request_id, chat_id=chat_id)
    need(result["request"]["id"] is not None and result["request"]["chat_id"] is not None,
         "post_deployment_request_identity_required")
    return result


def verify_manifest(contract):
    refs = contract["manifest"]
    need(set(refs) == {"path", "sha256", "signature_path", "public_key_path", "public_key_spki_sha256"}
         and HEX.fullmatch(refs["sha256"]) and HEX.fullmatch(refs["public_key_spki_sha256"]),
         "manifest_reference_invalid")
    raw = private_file(refs["path"])
    need(digest(raw) == refs["sha256"], "candidate_manifest_changed")
    signature = private_file(refs["signature_path"])
    public = private_file(refs["public_key_path"])
    need(digest(public) == refs["public_key_spki_sha256"], "independent_signing_key_changed")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, value in (("public.der", public), ("manifest", raw), ("signature", signature)):
            (root / name).write_bytes(value)
        pem = command(["openssl", "pkey", "-pubin", "-inform", "DER", "-in", str(root / "public.der"), "-outform", "PEM"])
        (root / "public.pem").write_bytes(pem)
        command(["openssl", "dgst", "-sha256", "-verify", str(root / "public.pem"), "-signature", str(root / "signature"), str(root / "manifest")])
    manifest = document(raw)
    need(set(manifest["images"]) == {"api", "web", "worker", "verifier"}
         and all(re.fullmatch(r"sha256:[a-f0-9]{64}", x) for x in manifest["images"].values())
         and all(COMMIT.fullmatch(manifest["source_commits"][x])
                 for x in ("pals", "pals-api", "pals-infra", "pals-agent", "pals-webfront")),
         "candidate_identity_invalid")
    now = datetime.now(UTC)
    need(stamp(manifest["issued_at"]) <= now < stamp(manifest["expires_at"]), "candidate_window_invalid")
    return manifest


def sanitize_runtime(container, image):
    """Runs on the observed host. NEVER return full Env/Config or exception text."""
    env = dict(item.split("=", 1) for item in container["Config"].get("Env", []) if "=" in item)
    labels = container["Config"].get("Labels") or {}
    manifest = env.get("PALS_CLOUD_RESTORE_MANIFEST_SHA256")
    if not isinstance(manifest, str) or not re.fullmatch(r"[a-f0-9]{64}", manifest):
        manifest = None
    uri_pattern = r"[0-9]{12}[.]dkr[.]ecr[.]ap-northeast-1[.]amazonaws[.]com/pals-prod-(?:api|web|worker|verifier)@sha256:[a-f0-9]{64}"
    def bounded(value, pattern):
        return value if isinstance(value, str) and re.fullmatch(pattern, value) else None
    state = container["State"]
    health = state.get("Health", {}).get("Status")
    if "Health" in state and health not in {"healthy", "unhealthy", "starting"}:
        health = "invalid"
    return {"schema_version": "pals.release-runtime-observation.v1",
            "container_sha256": hashlib.sha256(container["Id"].encode()).hexdigest(),
            "image_id": bounded(container["Image"], r"sha256:[a-f0-9]{64}"),
            "configured_image": bounded(container["Config"]["Image"], uri_pattern),
            "config_labels": {name: value if isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) else None
                              for name, value in ((key, labels.get(key)) for key in ("com.pals.private-control", "com.pals.private-compute"))},
            "environment_sha256": hashlib.sha256(json.dumps(sorted(container["Config"].get("Env", [])), sort_keys=True,
                                                              separators=(",", ":"), ensure_ascii=False).encode()).hexdigest(),
            "api_manifest_sha256": manifest,
            "state": {"running": state["Running"], "paused": state.get("Paused", False),
                      "restarting": state.get("Restarting", False), "oom_killed": state.get("OOMKilled", False),
                      "started_at": bounded(state["StartedAt"], r"[0-9T:.+Z-]{20,40}"),
                      "health": health},
            "image": {"id": bounded(image["Id"], r"sha256:[a-f0-9]{64}"),
                      "repo_digests": [uri for uri in image.get("RepoDigests", [])[:16] if bounded(uri, uri_pattern)],
                      "revision": bounded((image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision"), r"[a-f0-9]{40}"),
                      "os": bounded(image["Os"], r"linux"), "architecture": bounded(image["Architecture"], r"arm64|amd64")}}


def remote_program(container, asset_path=None):
    """Fixed read-only source; its bytes are included in runner_fingerprint()."""
    need(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", container), "remote_container_invalid")
    if asset_path is not None:
        need(re.fullmatch(r"/_next/static/[A-Za-z0-9_./@()+\[\]-]+[.](js|css)", asset_path)
             and ".." not in asset_path, "remote_asset_path_invalid")
    source = "import hashlib,json,re,subprocess,sys\n" + inspect.getsource(sanitize_runtime)
    source += "\ncontainer_name=" + repr(container) + "\nasset_path=" + repr(asset_path) + "\n"
    source += r'''
try:
    def docker(args):
        value = subprocess.run(['/usr/bin/docker', *args], capture_output=True, timeout=25)
        if value.returncode != 0 or len(value.stdout) > 2**23:
            raise ValueError('docker_read_failed')
        return value.stdout
    if asset_path is None:
        container = json.loads(docker(['container', 'inspect', container_name]))[0]
        image = json.loads(docker(['image', 'inspect', container['Config']['Image']]))[0]
        result = sanitize_runtime(container, image)
    else:
        code = "const f=require('node:fs'),c=require('node:crypto');process.stdout.write(c.createHash('sha256').update(f.readFileSync('/app/.next/static/'+process.argv[1])).digest('hex'))"
        result = {'schema_version': 'pals.release-web-asset.v1',
                  'sha256': docker(['exec', container_name, 'node', '-e', code, asset_path.removeprefix('/_next/static/')]).decode()}
        if not re.fullmatch('[a-f0-9]{64}', result['sha256']):
            raise ValueError('asset_digest_invalid')
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
except Exception:
    print('{"error":"runtime_observation_failed"}')
    sys.exit(1)
'''
    return source


def aws_read(binding, arguments, *, invocation_not_ready=False):
    config = binding["ssm"]
    environment = {key: value for key, value in os.environ.items() if not key.startswith("AWS_")}
    environment.update(AWS_EC2_METADATA_DISABLED="true", AWS_PAGER="", AWS_CLI_AUTO_PROMPT="off",
                       AWS_MAX_ATTEMPTS="1", AWS_IGNORE_CONFIGURED_ENDPOINT_URLS="true")
    result = subprocess.run(["aws", "--profile", config["profile"], "--region", config["region"],
                             "--no-cli-pager", *arguments, "--output", "json"],
                            capture_output=True, timeout=30, env=environment)
    if result.returncode != 0 and invocation_not_ready and b"(InvocationDoesNotExist)" in result.stderr:
        raise SSMNotReady("ssm_invocation_not_ready")
    need(result.returncode == 0 and len(result.stdout) <= 2**20, "ssm_observation_command_failed")
    return json.loads(result.stdout)


def ssm_observe(binding, *, account_id, asset_path=None):
    config = binding["ssm"]
    need(config["account_id"] == account_id, "ssm_manifest_account_differs")
    actual = aws_read(binding, ["sts", "get-caller-identity"])
    need(actual.get("Account") == account_id, "ssm_caller_account_differs")
    program = base64.b64encode(remote_program(binding["container"], asset_path).encode()).decode()
    shell = "/usr/bin/python3.12 -I -c \"import base64;exec(compile(base64.b64decode('" + program + "'),'release-acceptance-observer','exec'))\""
    request = aws_read(binding, ["ssm", "send-command", "--instance-ids", config["instance_id"],
                                  "--document-name", "AWS-RunShellScript", "--timeout-seconds", "90",
                                  "--parameters", json.dumps({"commands": [shell], "executionTimeout": ["70"]})])
    command_id = request.get("Command", {}).get("CommandId")
    need(isinstance(command_id, str) and str(UUID(command_id)) == command_id, "ssm_command_identity_invalid")
    deadline = time.monotonic() + 100
    not_ready_retries = 0
    while time.monotonic() < deadline:
        time.sleep(1)
        try:
            response = aws_read(binding, ["ssm", "get-command-invocation", "--command-id", command_id,
                                         "--instance-id", config["instance_id"]], invocation_not_ready=True)
        except SSMNotReady:
            not_ready_retries += 1
            need(not_ready_retries <= 2, "ssm_invocation_not_observable")
            continue
        if response.get("Status") in {"Pending", "InProgress", "Delayed"}:
            continue
        need(response.get("Status") == "Success" and response.get("ResponseCode") == 0
             and response.get("CommandId") == command_id and response.get("InstanceId") == config["instance_id"]
             and not response.get("StandardErrorContent", "").strip(), "ssm_runtime_observation_failed")
        value = document(response["StandardOutputContent"].encode())
        need(value.get("schema_version") == ("pals.release-web-asset.v1" if asset_path else "pals.release-runtime-observation.v1"),
             "ssm_observation_schema_invalid")
        return value
    raise Refusal("ssm_runtime_observation_timeout")


def inspect_runtime(contract, manifest):
    observed = {}
    contexts = {}
    for role, image_role in ROLES.items():
        binding = contract["runtime"][role]
        if "ssm" in binding:
            data = ssm_observe(binding, account_id=manifest["aws_account_id"])
        else:
            data = local_observe(binding, contexts)
        state = data["state"]
        need(state["running"] is True and not state["paused"] and not state["restarting"]
             and not state["oom_killed"] and state["health"] in {None, "healthy"}, "runtime_not_healthy")
        label = "com.pals.private-control" if role in {"api", "web", "reconciler"} else "com.pals.private-compute"
        need(data["config_labels"].get(label) == binding["config_sha256"], "runtime_configuration_changed")
        need(data["environment_sha256"] == binding["environment_sha256"], "runtime_environment_changed")
        expected_digest = manifest["images"][image_role]
        uri = data["configured_image"]
        need(isinstance(uri, str) and uri.endswith("/pals-prod-" + image_role + "@" + expected_digest), "running_image_not_candidate")
        image = data["image"]
        need(image["id"] == data["image_id"] and uri in image["repo_digests"]
             and image["os"] == "linux" and image["architecture"] == ("arm64" if image_role in {"api", "web"} else "amd64"),
             "running_image_content_binding_changed")
        source_role = "pals-webfront" if image_role == "web" else "pals-api" if image_role == "api" else "pals-agent"
        expected_source = manifest["source_commits"][source_role]
        if image_role == "verifier" and "verifier_source" in manifest:
            expected_source = manifest["verifier_source"]["commit"]
        need(image["revision"] == expected_source, "running_source_not_candidate")
        if role == "api":
            need(data["api_manifest_sha256"] == contract["manifest"]["sha256"], "api_manifest_not_candidate")
        observed[role] = {"container_sha256": data["container_sha256"], "image": expected_digest, "source": expected_source,
                          "config_sha256": binding["config_sha256"], "started_at": state["started_at"],
                          "environment_sha256": data["environment_sha256"]}
    return observed


def local_observe(binding, contexts):
    context = binding["context"]
    if context not in contexts:
        info = json.loads(command(["docker", "context", "inspect", context]))
        need(len(info) == 1 and digest(encoded(info[0]["Endpoints"])) == binding["endpoint_sha256"],
             "docker_endpoint_changed")
        contexts[context] = binding["endpoint_sha256"]
    need(contexts[context] == binding["endpoint_sha256"], "docker_context_binding_conflict")
    args = ["docker", "--context", context]
    data = json.loads(command(args + ["container", "inspect", binding["container"]]))
    need(len(data) == 1, "runtime_container_missing")
    container = data[0]
    uri = container["Config"]["Image"]
    images = json.loads(command(args + ["image", "inspect", uri]))
    need(len(images) == 1, "runtime_image_missing")
    return sanitize_runtime(container, images[0])


def append_attempt(stream, record):
    stream.write(encoded(record) + b"\n"); stream.flush(); os.fsync(stream.fileno())


def verify_web_assets(contract, observation):
    assets = observation.get("web_assets")
    need(isinstance(assets, list) and 1 <= len(assets) <= 128
         and any(item.get("path", "").endswith(".js") for item in assets), "served_web_assets_required")
    web = contract["runtime"]["web"]
    code = ("const f=require('node:fs'),c=require('node:crypto');"
            "process.stdout.write(c.createHash('sha256').update(f.readFileSync('/app/.next/static/'+process.argv[1])).digest('hex'))")
    for item in assets:
        need(set(item) == {"path", "sha256"} and HEX.fullmatch(item["sha256"])
             and re.fullmatch(r"/_next/static/[A-Za-z0-9_./@()+\[\]-]+[.](js|css)", item["path"])
             and ".." not in item["path"], "served_web_asset_invalid")
        if "ssm" in web:
            manifest = document(private_file(contract["manifest"]["path"]))
            actual = ssm_observe(web, account_id=manifest["aws_account_id"], asset_path=item["path"])["sha256"]
        else:
            actual = command(["docker", "--context", web["context"], "exec", web["container"], "node", "-e", code,
                              item["path"].removeprefix("/_next/static/")]).decode()
        need(actual == item["sha256"], "served_web_not_candidate_image")


def latest_status(records, contract_sha256, runner_sha256, now, max_age, effective_contract_sha256=None):
    need(records, "no_live_acceptance")
    last = records[-1]
    need(last.get("state") == "accepted" and last.get("contract_sha256") == contract_sha256
         and last.get("runner_sha256") == runner_sha256, "latest_acceptance_not_green")
    if effective_contract_sha256 is not None:
        need(last.get("effective_contract_sha256") == effective_contract_sha256, "acceptance_request_binding_changed")
    need(0 <= (now - stamp(last["finished_at"])).total_seconds() <= max_age, "acceptance_stale")
    return last


def browser_capture(payload, timeout):
    process = subprocess.Popen(["node", str(HERE / "release-acceptance-browser.cjs")],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    try:
        stdout, stderr = process.communicate(encoded(payload), timeout=timeout)
        if process.returncode != 0:
            code = stderr.decode(errors="replace")
            observation = document(stdout) if 0 < len(stdout) <= 2**20 else None
            if observation is not None:
                need(observation.get("run_id") == payload["run_id"], "failed_observation_not_this_run")
            raise ProductFailure(code if re.fullmatch(r"[a-z0-9_]{1,96}", code) else "live_product_acceptance_failed", observation)
        need(len(stdout) <= 2**20, "browser_output_unbounded")
        return document(stdout)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("fingerprint", "run", "status"))
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--session", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--chat-id")
    args = parser.parse_args()
    if args.operation == "fingerprint":
        print(runner_fingerprint()); return 0
    need(args.contract and args.state_dir, "contract_and_protected_state_required")
    root = args.state_dir
    root.mkdir(mode=0o700, parents=False, exist_ok=True)
    info = root.lstat()
    need(root.is_absolute() and root.resolve(strict=True) == root and stat.S_ISDIR(info.st_mode)
         and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, "protected_runner_state_required")
    journal = root / "attempts.jsonl"
    fd = os.open(journal, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a+b") as stream:
        metadata = os.fstat(stream.fileno())
        need(stat.S_ISREG(metadata.st_mode) and metadata.st_uid == os.geteuid()
             and metadata.st_nlink == 1 and stat.S_IMODE(metadata.st_mode) == 0o600, "protected_journal_required")
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.operation == "status":
            contract = effective_contract(validate_contract(document(private_file(args.contract))), args.request_id, args.chat_id)
            stream.seek(0)
            records = [document(line) for line in stream if line.strip()]
            record = latest_status(records, digest(private_file(args.contract)), runner_fingerprint(), datetime.now(UTC),
                                   contract["max_age_seconds"], digest(encoded(contract)))
            print(json.dumps(record)); return 0
        record = {"schema_version": SCHEMA, "state": "running", "run_id": str(uuid4()),
                  "started_at": datetime.now(UTC).isoformat(), "runner_sha256": runner_fingerprint()}
        append_attempt(stream, record)
        try:
            raw = private_file(args.contract); record["contract_sha256"] = digest(raw)
            contract = effective_contract(validate_contract(document(raw)), args.request_id, args.chat_id)
            record["effective_contract_sha256"] = digest(encoded(contract))
            manifest = verify_manifest(contract)
            need(args.session, "authenticated_browser_session_required")
            private_file(args.session)
            runtime = inspect_runtime(contract, manifest)
            record["runtime"] = runtime
            activation = max(stamp(x["started_at"]) for x in runtime.values()).isoformat()
            payload = {"contract": contract, "session_path": str(args.session), "activated_at": activation,
                       "run_id": record["run_id"]}
            observation = browser_capture(payload, contract["timeout_seconds"] + 30)
            need(observation.get("run_id") == record["run_id"], "browser_observation_not_this_run")
            verify_web_assets(contract, observation)
            need(inspect_runtime(contract, manifest) == runtime, "runtime_changed_during_acceptance")
            need(digest(private_file(args.contract)) == record["contract_sha256"] and runner_fingerprint() == record["runner_sha256"],
                 "acceptance_inputs_changed")
            verify_manifest(contract)
            record.update(state="accepted", phase=contract["phase"], target=contract["target"],
                          manifest_sha256=contract["manifest"]["sha256"], runtime=runtime, observation=observation)
        except Exception as error:
            record.update(state="failed", code=str(error) if isinstance(error, Refusal) else "acceptance_dependency_or_execution_failed")
            if isinstance(error, ProductFailure) and error.observation is not None:
                record["observation"] = error.observation
        record["finished_at"] = datetime.now(UTC).isoformat()
        append_attempt(stream, record)
        print(json.dumps(record))
        return 0 if record["state"] == "accepted" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(json.dumps({"schema_version": SCHEMA, "state": "blocked", "code": "acceptance_precondition_failed"}))
        sys.exit(1)
