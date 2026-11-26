#!/usr/bin/env python3
"""Freeze a running lane's subject before binding its digest to the local API."""

from __future__ import annotations

import argparse
import fcntl
import http.client
import importlib.util
import json
import os
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("local_qualification_prepare", HERE / "local-qualification-prepare.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
gate = prepare.gate

ROLES = ("api", "reconciler", "worker", "assessment-worker", "recipe-reviewer", "verifier", "webfront", "worker-network-guard")


def reference(path):
    return {"path": str(path.resolve(strict=True)), "sha256": gate.sha(path.read_bytes())}


def freeze(args):
    runtime_dir = prepare.require_runtime_directory(args.runtime_dir)
    state = args.state_dir.resolve()
    environment_file = runtime_dir / "local.env"
    environment = gate.private_env(environment_file)
    gate.need(environment.get("PALS_ENV") == "local" and environment.get("PALS_ENVIRONMENT") == "local",
              "explicit_local_environment_required")
    candidate_raw = args.candidate.read_bytes()
    candidate = json.loads(candidate_raw)
    subject = json.loads(args.base_subject.read_bytes())
    web = json.loads(args.web_receipt.read_bytes())
    verifier = json.loads(args.verifier_receipt.read_bytes())
    source = args.api_source.resolve(strict=True)
    subject["local_lane"] = {
        "role": args.role, "candidate_sha256": gate.sha(candidate_raw), "topology": reference(args.topology),
    }
    subject["preparation"] = {"lane_freezer_sha256": gate.sha(Path(__file__).read_bytes())}
    subject["local_profile"]["compiler"] = "native ARM64 verifier with the exact production source, Lean and Mathlib"
    gate.need(subject["local_lane"]["topology"]["sha256"] == args.topology_sha256, "frozen_lane_topology_changed")
    scope = gate.lane_runtime(subject, state, environment_file)
    prepare.database_bootstrap.require_lane_migration_source(source, args.candidate, subject["local_lane"]["candidate_sha256"])
    gate.need(
        all(subject["images"][role]["image_id"] == candidate["images"][role] for role in ("api", "worker", "verifier"))
        and subject["web_variant"]["production_image_digest"] == candidate["images"]["web"]
        and all(subject["images"][role]["source_revision"] == candidate["source_commits"][repo]
                for role, repo in (("api", "pals-api"), ("worker", "pals-agent"), ("web", "pals-webfront")))
        and subject["images"]["verifier"]["source_revision"] == candidate["verifier_source"]["commit"],
        "local_lane_base_differs_from_candidate",
    )
    for role, receipt in (("web", web), ("verifier", verifier)):
        gate.need(receipt["source_revision"] == subject["images"][role]["source_revision"],
                  "local_lane_receipt_source_differs_from_candidate")
        subject["images"][role].update(
            image_id=receipt["built_image_id"], image_reference=receipt["built_image_id"], platform=receipt["platform"],
        )
    subject["verifier_variant"] = prepare.verifier_variant(candidate["images"]["verifier"], verifier, reference(args.verifier_receipt))
    subject["web_variant"].update(
        production_publication=web["production_publication"], source_archive=web["source_archive"],
        local_build_provenance=reference(args.web_receipt), local_build_args=web["local_build_args"],
    )
    guard_id = scope["guard"]["image_id"]
    subject["images"]["guard"] = {"image_id": guard_id, "image_reference": guard_id, "platform": "linux/amd64"}
    tls = prepare.require_provider_tls(args.provider_tls_dir)
    raw, ledger, limit = prepare.require_known_budget(args.budget_before)
    handoff_ref = {"path": str(args.handoff_receipt.resolve()), "sha256": args.handoff_receipt_sha256}
    handoff = json.loads(gate.file_reference(handoff_ref).read_bytes())
    gate.need(
        handoff.get("status") == "verified_read_only" and handoff.get("ledger") == {
            "path": str(Path(scope["guard"]["ledger_directory"]) / "ledger.json"), "sha256": gate.sha(raw),
        },
        "live_local_guard_must_continue_authoritative_handoff",
    )
    subject["preparation"]["budget_handoff_receipt"] = handoff_ref
    subject["guard"].update(
        source_sha256={name: gate.sha((HERE / "local-qualification" / name).read_bytes())
                       for name in ("guard.py", "budget_proxy.py", "Dockerfile")},
        budget_limit_microusd=limit, budget_rollover=ledger.get("rollover"),
        resumed_budget={"path": str(args.budget_before.resolve()), "sha256": gate.sha(raw)},
        ca_bundle_sha256=tls["ca_bundle_sha256"],
        provider_tls={"server_certificate_sha256": tls["server_certificate_sha256"],
                      "not_after": tls["not_after"],
                      "trust_scope": "local CA only, name constrained to the proxied host"},
    )
    subject["runtime_config"] = {}
    for role in ROLES:
        observed = json.loads(gate.scoped_docker(scope, "inspect", gate.runtime_name(role, scope)))[0]
        subject["runtime_config"][role] = prepare.runtime_config_entry(observed)
    subject["database_contract"] = {
        "api_source_root": str(source), "api_source_revision": subject["images"]["api"]["source_revision"],
        "migration_sql": reference(source / "app/db/migrations/draft_addition_candidates/001_candidates.sql"),
        "migration_manifest": reference(source / "app/db/migrations/draft_addition_candidates/manifest.json"),
    }
    database = gate.database_readiness(subject, environment_file, require_frozen=False, lane=args.role)
    subject["database_contract"]["schema_fingerprint_sha256"] = database["schema_fingerprint_sha256"]
    coupon_plan = prepare.database_bootstrap.coupon_bootstrap_plan(
        source, environment, enabled=environment.get("PALS_PLUS_COUPONS_ENABLED") == "true",
    )
    if coupon_plan:
        prepare.freeze_plus_coupons(subject, environment_file, coupon_plan)
    gate.web_provenance(subject, scope=scope)
    gate.verifier_provenance(subject, scope=scope)
    gate.check_lane_helpers(scope)
    gate.runtime(subject, scope=scope)
    gate.provider_tls_status(subject, scope=scope)
    gate.budget_status(subject, scope=scope)
    gate.need(gate.lane_runtime(subject, state, environment_file) == scope, "local_lane_topology_changed_during_freeze")
    return subject


def subject_bytes(subject):
    return (gate.stable(subject) + "\n").encode()


def publish_subject(out, subject):
    with tempfile.TemporaryDirectory(prefix="subject-", dir=out.parent) as directory:
        path = Path(directory) / "subject.json"
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(subject_bytes(subject))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(path, out)


def api_header(port, expected):
    with_connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        with_connection.request("GET", "/health")
        response = with_connection.getresponse()
        gate.need(response.status == 200 and response.getheader("X-PALS-Release-Manifest-SHA256") == expected,
                  "lane_api_does_not_serve_frozen_subject")
    finally:
        with_connection.close()


def bind_api(args, subject, out):
    runtime_directory = out.parent
    state = args.state_dir.resolve()
    local_env = runtime_directory / "local.env"
    gate.need(not (state / "submission.json").exists() and not out.exists(), "unused_local_lane_capture_required")
    scope = gate.lane_runtime(subject, state, local_env)
    rendered_ref = {"path": str(args.rendered_compose.resolve()), "sha256": args.rendered_compose_sha256}
    rendered = json.loads(gate.file_reference(rendered_ref).read_bytes())
    gate.need(rendered.get("status") == "rendered_relay_compose" and rendered.get("activation_authorized") is False,
              "preactivation_rendered_lane_compose_required")
    subject["preparation"]["rendered_lane_compose"] = rendered_ref
    lane = rendered["lanes"][args.role]
    gate.need(
        lane["compose_project"] == scope["lane"]["compose_project"]
        and lane["candidate_sha256"] == subject["local_lane"]["candidate_sha256"]
        and lane["environment_files"] == [str(runtime_directory / name) for name in ("local.env", "release.env", "recipe.env")]
        and rendered["budget_continuity"]["sha256"] == subject["guard"]["resumed_budget"]["sha256"],
        "local_lane_compose_scope_differs",
    )
    for path in lane["environment_files"]:
        gate.private_env(Path(path))
    for ref in lane["base_files"]:
        gate.file_reference(ref)
    original = local_env.read_bytes()
    environment = gate.private_env(local_env)
    old_header = environment.get("PALS_LOCAL_CANDIDATE_SHA256")
    gate.need(isinstance(old_header, str) and len(old_header) == 64, "initial_lane_api_header_required")
    compose_env = {key: value for key, value in os.environ.items() if key in {"HOME", "LANG", "LOGNAME", "PATH", "TMPDIR", "USER"}}
    with tempfile.TemporaryDirectory(prefix="lane-compose-", dir=runtime_directory) as directory:
        overlays = []
        for key in ("profile_overlay_yaml", "relay_overlay_yaml"):
            path = Path(directory) / (key + ".yml")
            path.write_text(lane[key], encoding="utf-8")
            overlays.append(str(path))
        command = ["compose", "--project-directory", str(args.compose_root), "--project-name", lane["compose_project"]]
        for path in lane["environment_files"]:
            command.extend(["--env-file", path])
        for path in [*(ref["path"] for ref in lane["base_files"]), *overlays]:
            command.extend(["-f", path])
        def inspect_api():
            return json.loads(gate.scoped_docker(scope, "inspect", gate.runtime_name("api", scope)))[0]

        def compose(*args, timeout=60):
            return gate.command(["docker", "--host", "unix://" + scope["docker_socket"], *command, *args],
                                timeout=timeout, env=compose_env)

        def recreate_api():
            compose("up", "-d", "--no-deps", "--no-build", "--wait", "--wait-timeout", "45", "api")

        api = inspect_api()
        initial_hash = api["Config"]["Labels"].get("com.docker.compose.config-hash")
        gate.need(initial_hash and compose("config", "--hash", "api").split() == ["api", initial_hash],
                  "lane_api_does_not_match_initial_reviewed_compose_model")
        port = scope["lane"]["http_ports"]["api"]
        api_header(port, old_header)
        recovery = runtime_directory / "api-binding-recovery"
        recovery.mkdir(mode=0o700)
        original_path = recovery / "original.env"
        with os.fdopen(os.open(original_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
            stream.write(original)
            stream.flush()
            os.fsync(stream.fileno())
        gate.private_json(recovery / "intent.json", {
            "original_sha256": gate.sha(original), "original_compose_config_hash": initial_hash,
            "candidate_sha256": lane["candidate_sha256"], "rendered_compose": rendered_ref,
        })
        recovery_fd = os.open(recovery, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(recovery_fd)
        finally:
            os.close(recovery_fd)

        def bind_round():
            environment["PALS_LOCAL_CANDIDATE_SHA256"] = gate.sha(subject_bytes(subject))
            pending = recovery / "pending.env"
            prepare.write_env(pending, environment)
            os.replace(pending, local_env)
            recreate_api()

        try:
            prepare.freeze_until_api_is_stable(subject, api, bind_round, inspect_api)
            refreshed = gate.lane_runtime(subject, state, local_env)
            gate.runtime(subject, scope=refreshed)
            api_header(port, gate.sha(subject_bytes(subject)))
            publish_subject(out, subject)
        except BaseException:
            try:
                restore = Path(directory) / "original.env"
                restore.write_bytes(original)
                restore.chmod(0o600)
                os.replace(restore, local_env)
                recreate_api()
                gate.need(inspect_api()["Config"]["Labels"].get("com.docker.compose.config-hash") == initial_hash,
                          "lane_api_previous_config_not_restored")
                api_header(port, old_header)
            except Exception:
                raise gate.Refusal("local_lane_api_binding_restore_failed") from None
            shutil.rmtree(recovery)
            raise
        shutil.rmtree(recovery)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=("primary", "standby"), required=True)
    parser.add_argument("--topology-sha256", required=True)
    parser.add_argument("--bind-api", action="store_true")
    parser.add_argument("--rendered-compose", type=Path)
    parser.add_argument("--rendered-compose-sha256")
    parser.add_argument("--compose-root", type=Path)
    parser.add_argument("--handoff-receipt-sha256", required=True)
    for name in ("runtime-dir", "state-dir", "topology", "candidate", "base-subject", "web-receipt",
                 "verifier-receipt", "api-source", "provider-tls-dir", "budget-before", "handoff-receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    compose_options = (args.rendered_compose, args.rendered_compose_sha256, args.compose_root)
    if args.bind_api != all(compose_options) or (any(compose_options) and not all(compose_options)):
        parser.error("--bind-api requires the pinned Compose input and canonical Compose root")
    directory = prepare.require_runtime_directory(args.runtime_dir)
    out = directory / ("subject-native.json" if args.bind_api else "subject-inspected.json")
    lock = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        gate.need(not (directory / "api-binding-recovery").exists(), "local_lane_api_binding_requires_recovery")
        subject = freeze(args)
        if args.bind_api:
            bind_api(args, subject, out)
        else:
            publish_subject(out, subject)
    finally:
        os.close(lock)
    print(gate.stable({"state": "api_bound_to_frozen_subject" if args.bind_api else "subject_frozen_pending_api_binding",
                       "subject": reference(out)}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, gate.Refusal) as error:
        raise SystemExit(str(error)) from None
