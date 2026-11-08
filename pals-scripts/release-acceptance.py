#!/usr/bin/env python3
"""Live, read-only release qualification. Never accepts caller-authored PASS evidence."""
from __future__ import annotations

import argparse
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
        need(set(binding) == {"context", "endpoint_sha256", "container", "config_sha256", "environment_sha256"}
             and all(isinstance(binding[k], str) and HEX.fullmatch(binding[k])
                     for k in ("endpoint_sha256", "config_sha256", "environment_sha256"))
             and all(isinstance(binding[k], str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", binding[k])
                     for k in ("context", "container")), "runtime_binding_invalid")
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


def inspect_runtime(contract, manifest):
    observed = {}
    contexts = {}
    for role, image_role in ROLES.items():
        binding = contract["runtime"][role]
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
        config, state = container["Config"], container["State"]
        need(state["Running"] is True and not state.get("Paused") and not state.get("Restarting")
             and not state.get("OOMKilled") and ("Health" not in state or state["Health"]["Status"] == "healthy"),
             "runtime_not_healthy")
        label = "com.pals.private-control" if role in {"api", "web", "reconciler"} else "com.pals.private-compute"
        need(config["Labels"].get(label) == binding["config_sha256"], "runtime_configuration_changed")
        need(digest(encoded(sorted(config.get("Env", [])))) == binding["environment_sha256"], "runtime_environment_changed")
        expected_digest = manifest["images"][image_role]
        uri = config["Image"]
        need(isinstance(uri, str) and uri.endswith("/pals-prod-" + image_role + "@" + expected_digest),
             "running_image_not_candidate")
        images = json.loads(command(args + ["image", "inspect", uri]))
        need(len(images) == 1 and images[0]["Id"] == container["Image"]
             and uri in images[0].get("RepoDigests", []), "running_image_content_binding_changed")
        source_role = "pals-webfront" if image_role == "web" else "pals-api" if image_role == "api" else "pals-agent"
        expected_source = manifest["source_commits"][source_role]
        if image_role == "verifier" and "verifier_source" in manifest:
            expected_source = manifest["verifier_source"]["commit"]
        need(images[0]["Config"]["Labels"].get("org.opencontainers.image.revision") == expected_source,
             "running_source_not_candidate")
        if role == "api":
            env = dict(item.split("=", 1) for item in config.get("Env", []) if "=" in item)
            need(env.get("PALS_CLOUD_RESTORE_MANIFEST_SHA256") == contract["manifest"]["sha256"],
                 "api_manifest_not_candidate")
        observed[role] = {"container_sha256": digest(container["Id"].encode()), "image": expected_digest,
                          "source": expected_source, "config_sha256": binding["config_sha256"],
                          "started_at": state["StartedAt"], "environment_sha256": digest(encoded(sorted(config.get("Env", []))))}
    return observed


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
        actual = command(["docker", "--context", web["context"], "exec", web["container"], "node", "-e", code,
                          item["path"].removeprefix("/_next/static/")])
        need(actual.decode() == item["sha256"], "served_web_not_candidate_image")


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
            raise Refusal(code if re.fullmatch(r"[a-z0-9_]{1,96}", code) else "live_product_acceptance_failed")
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
