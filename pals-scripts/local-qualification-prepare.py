#!/usr/bin/env python3
"""Prepare one owned local qualification stack. Never submit a proof or reset spending."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("local_qualification_prepare_gate", HERE / "local-qualification.py")
provider_tls = load(
    "local_qualification_provider_tls", HERE / "bootstrap-local-provider-tls.py"
)
PROJECT = "pals-reliability-local"
# Services the application roles depend on. They hold the emulated secrets, queues and
# identities, so they must be converged BEFORE anything is written into them.
STABLE_DEPENDENCIES = ("localstack", "cognito-local")
# The accepted capture stays fresh for 3600 s; the margin covers preparation and the
# bounded paid journey that happen between this check and the capture.
CAPTURE_FRESHNESS_SECONDS = 3600
PROVIDER_TLS_MARGIN_SECONDS = 900
# What the running proxy must still have left when preparation has finished.
PROVIDER_TLS_SERVED_SECONDS = CAPTURE_FRESHNESS_SECONDS + PROVIDER_TLS_MARGIN_SECONDS
# Upper bound of everything preparation does after its first check (guard build 600 s,
# dependency and application start, bootstraps, readiness 120 s, provenance, canary).
# Marginal material is therefore refused BEFORE the stack is stopped and rebuilt.
PREPARATION_BOUND_SECONDS = 1800
PROVIDER_TLS_MINIMUM_SECONDS = PROVIDER_TLS_SERVED_SECONDS + PREPARATION_BOUND_SECONDS
APPLICATION_ROLES = (
    "verifier",
    "reconciler",
    "api",
    "worker-network-guard",
    "recipe-reviewer",
    "worker",
    "assessment-worker",
    "webfront",
)
CHILD_MODULES = {
    "api_python": ("psycopg",),
    "agent_python": ("boto3", "cryptography"),
}
KNOWN_ROLES = {
    "api",
    "reconciler",
    "worker",
    "assessment-worker",
    "recipe-reviewer",
    "verifier",
    "webfront",
    "worker-network-guard",
    "localstack",
    "cognito-local",
    "schema-release",
}


def validate_existing_role_owners(labels):
    for item in labels:
        gate.need(
            item.get("com.docker.compose.project") == PROJECT
            and item.get("codex.owner") == gate.OWNER
            and item.get("com.docker.compose.service") in KNOWN_ROLES,
            "foreign_or_unknown_local_project_role_refused",
        )


def assert_existing_project_owned():
    ids = set(
        run(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ]
        ).split()
    )
    ids.update(
        run(["docker", "ps", "-aq", "--filter", "name=^/" + PROJECT + "-"]).split()
    )
    labels = []
    for container in ids:
        labels.append(
            json.loads(
                run(
                    [
                        "docker",
                        "inspect",
                        "--format",
                        "{{json .Config.Labels}}",
                        container,
                    ]
                )
            )
        )
    validate_existing_role_owners(labels)


def run(args, timeout=45):
    return gate.command([str(x) for x in args], timeout=timeout)


def require_child_modules(python, modules, prefix, *, run_=None):
    """Fail fast with the interpreter and module named instead of a late child failure."""
    program = (
        "import importlib.util,sys;"
        "print(','.join(m for m in sys.argv[1:] if importlib.util.find_spec(m) is None))"
    )
    try:
        missing = (run_ or run)([python, "-c", program, *modules]).strip()
    except (OSError, gate.Refusal):
        raise gate.Refusal(prefix + "_unavailable") from None
    gate.need(not missing, prefix + "_missing_module:" + missing.split(",")[0])


def require_runtime_directory(path):
    """The owned runtime directory: existing, private, with a plain absolute path.

    Any such location is accepted. Every bind mount, the subject and the environment
    files are derived from it on each run, so a copy in a persistent place continues
    the same ledger. Do not keep it under a path that is cleared on reboot.
    """
    path = Path(path).resolve()
    gate.need(
        path.is_dir()
        and path.stat().st_mode & 0o777 == 0o700
        and re.fullmatch(r"/[A-Za-z0-9_./-]+", str(path)),
        "existing_private_runtime_directory_required",
    )
    return path


def serving_budget_directory(*, run_=None):
    """Host directory the existing guard container records provider spending in.

    ``None`` when no guard container exists: then nothing could have forwarded a call.
    """
    run_ = run_ or run
    name = PROJECT + "-worker-network-guard-1"
    if not run_(["docker", "ps", "-aq", "--filter", "name=^/" + name + "$"]).strip():
        return None
    mounts = json.loads(
        run_(["docker", "inspect", "--format", "{{json .Mounts}}", name])
    )
    sources = [m["Source"] for m in mounts if m.get("Destination") == "/run/budget"]
    gate.need(len(sources) == 1, "serving_budget_directory_required")
    return Path(sources[0])


def require_ledger_continuity(ledger, serving):
    """A relocated runtime directory must hold the ledger the guard last wrote.

    Call this only AFTER the task containers and the guard are stopped: from then on no
    provider call can be recorded. If the guard served another directory, a call made
    after that directory was copied exists only in its ledger; continuing with the copy
    would under-count spending, so the two must agree exactly.
    """
    if serving is None or Path(serving).resolve() == ledger.parent.resolve():
        return "same_directory"
    source = Path(serving) / "ledger.json"
    gate.need(
        source.is_file() and not source.is_symlink(),
        "relocated_budget_serving_ledger_required",
    )
    try:
        old, new = json.loads(source.read_bytes()), json.loads(ledger.read_bytes())
    except (OSError, ValueError):
        raise gate.Refusal("relocated_budget_serving_ledger_required") from None
    gate.need(
        type(old) is dict
        and type(new) is dict
        and all(
            name in old and old[name] == new.get(name)
            for name in ("calls", "actual_microusd", "reserved_microusd", "blocked")
        ),
        "relocated_budget_ledger_differs_from_the_serving_ledger",
    )
    return "relocated_identical"


def render_profile(template, values):
    for key, value in values.items():
        template = template.replace(key, value)
    gate.need("@@" not in template, "unresolved_local_profile_binding")
    return template


def verifier_variant(production_image_digest, receipt, receipt_reference):
    """Exactly what pals-infra's release plan accepts for a native local verifier.

    `release-cycle.py` (`local_verifier_variant`) requires this closed key set, and
    `release_plan.py` (`VERIFIER_VARIANT_ARCHIVES`) requires `source_archive` and
    `recipe_archive` to be git's own archives of the manifest's verifier commit. Both
    come from the build receipt, which proves them against the built archive.
    """
    variant = {
        "production_image_digest": production_image_digest,
        "source_archive": receipt["source_archive"],
        "recipe_archive": receipt["recipe_archive"],
        "local_build_provenance": receipt_reference,
        "dockerfile_sha256": receipt["dockerfile_sha256"],
        "lean_version": receipt["lean_version"],
        "lake_manifest_sha256": receipt["lake_manifest_sha256"],
    }
    gate.need(
        set(variant) == gate.VERIFIER_VARIANT_KEYS,
        "closed_native_local_verifier_variant_required",
    )
    return variant


def require_provider_tls(directory, *, inspect=None):
    """Refuse before quiescing anything when the local proxy certificate cannot last.

    Preparation only checks. It never mints trust material implicitly: reissuing replaces
    the CA the task containers trust, so it stays one explicit, documented operator step.
    """
    result = (inspect or provider_tls.inspect)(
        directory, minimum_remaining_seconds=PROVIDER_TLS_MINIMUM_SECONDS
    )
    codes = {
        "expired": "local_provider_tls_expired",
        "expires_within_window": "local_provider_tls_expires_before_capture_window",
    }
    gate.need(
        result.get("state") == "valid",
        codes.get(result.get("state"), "local_provider_tls_missing_or_invalid"),
    )
    return result


def dependency_identity(*, run_=None):
    return {
        role: json.loads(
            (run_ or run)(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{json .Id}}",
                    PROJECT + "-" + role + "-1",
                ]
            )
        )
        for role in STABLE_DEPENDENCIES
    }


def bootstrap_on_stable_dependencies(compose, bootstrap, *, run_=None, identity=None):
    """Converge the dependency containers first, then write state into them.

    A changed compose root changes the bind-mount sources of LocalStack and Cognito, so
    ``up`` recreates them. LocalStack keeps secrets in memory only: a verifier mTLS
    secret created before that recreation is silently lost and the verifier then cannot
    start. Converging first makes the later application ``up`` a no-op for them.
    """
    (run_ or run)(
        [
            *compose,
            "up",
            "-d",
            "--no-build",
            "--wait",
            "--wait-timeout",
            "90",
            *STABLE_DEPENDENCIES,
        ],
        120,
    )
    before = (identity or dependency_identity)()
    bootstrap()
    return before


def require_dependencies_unchanged(before, *, identity=None):
    gate.need(
        (identity or dependency_identity)() == before,
        "local_dependency_recreated_after_verifier_tls_bootstrap",
    )


def start_stack(compose, bootstrap, *, run_=None, identity=None):
    """The whole ordered start: dependencies, bootstrap, application roles, identity.

    The identity is compared immediately after the application ``up``. A replaced
    LocalStack has lost the verifier secret, the verifier never becomes healthy, and a
    later check would only ever be reached after the generic readiness refusal.
    """
    before = bootstrap_on_stable_dependencies(
        compose, bootstrap, run_=run_, identity=identity
    )
    (run_ or run)([*compose, "up", "-d", "--no-build", *APPLICATION_ROLES], 60)
    require_dependencies_unchanged(before, identity=identity)
    return before


def read_env(path):
    return gate.private_env(path)


def write_env(path, values):
    gate.need(
        all(
            re.fullmatch(r"[A-Z0-9_]+", k) and "\n" not in v and "\r" not in v
            for k, v in values.items()
        ),
        "closed_private_env_required",
    )
    path.write_text("".join(k + "=" + v + "\n" for k, v in sorted(values.items())))
    path.chmod(0o600)


def build(args, log):
    with log.open("wb") as output:
        process = subprocess.Popen(
            [str(x) for x in args], stdout=output, stderr=subprocess.STDOUT
        )
        started = time.monotonic()
        try:
            while process.poll() is None:
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    gate.need(
                        time.monotonic() - started < 600, "local_helper_build_timeout"
                    )
            gate.need(process.returncode == 0, "local_helper_build_failed")
        except BaseException:
            process.terminate()
            process.wait(timeout=10)
            raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in (
        "runtime-dir",
        "compose-root",
        "api-source",
        "base-subject",
        "web-build-receipt",
        "verifier-build-receipt",
        "api-python",
        "agent-python",
    ):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    gate.require_modules()
    r = require_runtime_directory(a.runtime_dir)
    source = a.compose_root.resolve()
    gate.set_diagnostic_directory(r / "diagnostics")
    for prefix, modules in CHILD_MODULES.items():
        require_child_modules(getattr(a, prefix), modules, prefix)
    gate.need(
        os.environ.get("DOCKER_HOST", "unix://").startswith("unix://")
        and run(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"]
        )
        .strip()
        .startswith("unix://"),
        "local_docker_socket_required",
    )
    labels = json.loads(
        run(
            [
                "docker",
                "inspect",
                "--format",
                "{{json .Config.Labels}}",
                "pals-reliability-test-postgres",
            ]
        )
    )
    gate.need(
        labels.get("codex.owner") == gate.OWNER, "dedicated_owned_postgres_required"
    )
    assert_existing_project_owned()
    env = read_env(r / "local.env")
    gate.need(
        env.get("PALS_ENV") == "local" and env.get("PALS_ENVIRONMENT") == "local",
        "explicit_local_environment_required",
    )
    for name in ("release.env", "recipe.env"):
        # Registers their values for redaction of any persisted child diagnostics.
        if (r / name).is_file():
            read_env(r / name)
    observed_provider_tls = require_provider_tls(r / "provider-tls")
    # The reused private env/PG service are deliberate prerequisites. No other env files,
    # production database URLs or global Docker credentials are copied into this stack.
    subject = json.loads(a.base_subject.read_bytes())
    web = json.loads(a.web_build_receipt.read_bytes())
    verifier = json.loads(a.verifier_build_receipt.read_bytes())
    run(
        [
            a.api_python,
            HERE / "local-web-build.py",
            "--verify-receipt",
            a.web_build_receipt,
        ],
        60,
    )
    run(
        [
            a.api_python,
            HERE / "local-verifier-build.py",
            "--verify-receipt",
            a.verifier_build_receipt,
        ],
        60,
    )
    gate.need(
        web["source_revision"] == subject["images"]["web"]["source_revision"]
        and verifier["source_revision"]
        == subject["images"]["verifier"]["source_revision"],
        "prepared_candidate_sources_changed",
    )
    gate.need(
        run(["git", "-C", a.api_source, "rev-parse", "HEAD"]).strip()
        == subject["images"]["api"]["source_revision"]
        and not run(
            ["git", "-C", a.api_source, "diff", "--name-only", "HEAD", "--", "app"]
        ).strip(),
        "exact_clean_api_migration_source_required",
    )
    compose = [
        "docker",
        "compose",
        "--project-name",
        "pals-reliability-local",
        "--project-directory",
        source,
        "--env-file",
        r / "local.env",
        "--env-file",
        r / "release.env",
        "--env-file",
        r / "recipe.env",
        "-f",
        source / "docker-compose.yml",
        "-f",
        source / "pals-infra/docker-compose.localstack.yml",
        "-f",
        source / "docker-compose.e2e.yml",
        "-f",
        r / "override.yml",
    ]
    # Where the guard has been recording spending, read before anything is recreated.
    serving = serving_budget_directory()
    # Quiesce only this owned project before rotating local release/TLS bindings.
    run(
        [
            *compose,
            "stop",
            "-t",
            "10",
            "worker",
            "assessment-worker",
            "recipe-reviewer",
            "api",
            "reconciler",
            "verifier",
            "worker-network-guard",
        ],
        60,
    )
    ledger = r / "budget/ledger.json"
    # Producers and guard are stopped: the serving ledger is final. A relocated copy
    # that misses a call made after it was copied is refused here.
    require_ledger_continuity(ledger, serving)
    raw = ledger.read_bytes()
    previous = json.loads(raw)
    gate.need(
        not previous["blocked"]
        and previous["calls"]
        and all(x["state"] == "completed" for x in previous["calls"])
        and previous["actual_microusd"] == previous["reserved_microusd"] <= 700000,
        "known_existing_budget_required_no_reset",
    )
    env["PALS_BUDGET_RESUME_SHA256"] = gate.sha(raw)
    backup = r / ("budget-before-prepare-" + gate.sha(raw) + ".json")
    if not backup.exists():
        backup.write_bytes(raw)
        backup.chmod(0o600)
    write_env(r / "local.env", env)
    native_id = verifier["built_image_id"]
    worker = subject["images"]["worker"]["image_reference"]
    run(
        [
            "docker",
            "image",
            "tag",
            worker,
            "pals-reliability-network-guard-base:b27f1d8",
        ]
    )
    guard_tag = "pals-reliability-network-guard:bounded-local"
    build(
        [
            "docker",
            "buildx",
            "build",
            "--load",
            "--provenance=false",
            "--platform",
            "linux/amd64",
            "--metadata-file",
            r / "guard-build-metadata.json",
            "--label",
            "codex.owner=" + gate.OWNER,
            "-t",
            guard_tag,
            HERE / "local-qualification",
        ],
        r / "guard-build.log",
    )
    guard = json.loads(run(["docker", "image", "inspect", guard_tag]))[0]
    values = {
        "@@RUNTIME@@": str(r),
        "@@API_IMAGE@@": subject["images"]["api"]["image_reference"],
        "@@WORKER_IMAGE@@": worker,
        "@@WEB_IMAGE@@": web["built_image_id"],
        "@@VERIFIER_IMAGE@@": native_id,
        "@@GUARD_IMAGE@@": guard["Id"],
    }
    template = render_profile(
        (HERE / "local-qualification/compose.override.yml.in").read_text(), values
    )
    (r / "override.yml").write_text(template)
    run([*compose, "config", "--quiet"])

    def bootstrap():
        new_env = dict(
            os.environ, AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test"
        )
        new_env.pop("AWS_SESSION_TOKEN", None)
        tls = subprocess.run(
            [
                str(a.agent_python),
                str(HERE / "bootstrap-local-verifier-tls.py"),
                "--endpoint-url",
                "http://127.0.0.1:54566",
                "--region",
                "ap-northeast-1",
                "--image-digest",
                native_id,
                "--toolchain-sha256",
                native_id.removeprefix("sha256:"),
                "--output",
                str(r / "release.env"),
            ],
            env=new_env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if tls.returncode != 0:
            raise gate.Refusal(
                "actual_local_mtls_bootstrap_failed",
                gate.persist_diagnostic(
                    [a.agent_python, HERE / "bootstrap-local-verifier-tls.py"],
                    tls.returncode,
                    tls.stderr,
                ),
            )
        run(
            [
                a.api_python,
                HERE / "bootstrap-local-recipe-config.py",
                "--env-file",
                r / "local.env",
                "--release-env",
                r / "release.env",
                "--output",
                r / "recipe.env",
                "--lean-workspace",
                Path(verifier["build_context"]) / "lean-workspace",
            ]
        )
        run(
            [
                a.api_python,
                HERE / "local-qualification/bootstrap_database.py",
                "--runtime-dir",
                r,
                "--api-source",
                a.api_source,
            ],
            60,
        )

    # LocalStack and Cognito are converged to this compose root and profile first; only
    # then are the verifier mTLS secret, recipe configuration and schema written. The
    # database container is external to this project and is never recreated here.
    dependencies = start_stack(compose, bootstrap)
    roles = {
        "api": "api",
        "reconciler": "api",
        "worker": "worker",
        "assessment-worker": "worker",
        "recipe-reviewer": "worker",
        "verifier": "verifier",
        "webfront": "web",
        "worker-network-guard": "guard",
    }
    started = time.monotonic()
    while True:
        actual = {
            role: json.loads(
                run(["docker", "inspect", "pals-reliability-local-" + role + "-1"])
            )[0]
            for role in roles
        }
        if all(
            x["State"].get("Health", {}).get("Status") == "healthy"
            for x in actual.values()
        ):
            break
        gate.need(
            time.monotonic() - started < 120, "actual_local_runtime_readiness_failed"
        )
        time.sleep(1)
    # Checked once more after readiness: nothing may have replaced a dependency while
    # the roles were starting.
    require_dependencies_unchanged(dependencies)
    subject["images"]["web"].update(
        image_id=web["built_image_id"],
        image_reference=web["built_image_id"],
        platform=web["platform"],
    )
    subject["images"]["verifier"].update(
        image_id=native_id, image_reference=native_id, platform=verifier["platform"]
    )
    subject["images"]["guard"] = {
        "image_id": guard["Id"],
        "image_reference": guard["Id"],
        "platform": "linux/amd64",
    }
    ref = lambda path: {
        "path": str(path.resolve()),
        "sha256": gate.sha(path.read_bytes()),
    }
    subject["web_variant"].update(
        production_publication=web["production_publication"],
        source_archive=web["source_archive"],
        local_build_provenance=ref(a.web_build_receipt),
    )
    subject["verifier_variant"] = verifier_variant(
        json.loads(a.base_subject.read_bytes())["images"]["verifier"]["image_id"],
        verifier,
        ref(a.verifier_build_receipt),
    )
    subject["guard"].update(
        source_sha256={
            n: gate.sha((HERE / "local-qualification" / n).read_bytes())
            for n in ("guard.py", "budget_proxy.py", "Dockerfile")
        },
        budget_limit_microusd=700000,
        ca_bundle_sha256=observed_provider_tls["ca_bundle_sha256"],
        provider_tls={
            "server_certificate_sha256": observed_provider_tls[
                "server_certificate_sha256"
            ],
            "not_after": observed_provider_tls["not_after"],
            "trust_scope": "local CA only, name constrained to the proxied host",
        },
        resumed_budget=ref(backup),
        helper_build_metadata=ref(r / "guard-build-metadata.json"),
    )
    subject["local_profile"]["compiler"] = (
        "real native ARM64 verifier: same189 source/Dockerfile/Lean/Mathlib; actual Python dependency versions differ, not production byte equivalence"
    )
    subject["runtime_config"] = {}
    for role, item in actual.items():
        environment = sorted(
            x
            for x in item["Config"]["Env"]
            if not x.startswith("PALS_CLOUD_RESTORE_MANIFEST_SHA256=")
        )
        subject["runtime_config"][role] = {
            "image_id": item["Image"],
            "environment_sha256": gate.sha(gate.stable(environment).encode()),
            "host_config_sha256": gate.sha(gate.stable(item["HostConfig"]).encode()),
        }
    subject["preparation"] = {
        "driver_sha256": gate.sha(Path(__file__).read_bytes()),
        "compose_sources": {
            str(path): gate.sha(path.read_bytes())
            for path in (
                source / "docker-compose.yml",
                source / "docker-compose.e2e.yml",
                source / "pals-infra/docker-compose.localstack.yml",
                HERE / "local-qualification/compose.override.yml.in",
            )
        },
    }
    sql = (
        a.api_source / "app/db/migrations/draft_addition_candidates/001_candidates.sql"
    )
    manifest = (
        a.api_source / "app/db/migrations/draft_addition_candidates/manifest.json"
    )
    subject["database_contract"] = {
        "api_source_root": str(a.api_source.resolve()),
        "api_source_revision": subject["images"]["api"]["source_revision"],
        "migration_sql": ref(sql),
        "migration_manifest": ref(manifest),
    }
    observed_database = gate.database_readiness(
        subject, r / "local.env", require_frozen=False
    )
    subject["database_contract"]["schema_fingerprint_sha256"] = observed_database[
        "schema_fingerprint_sha256"
    ]
    out = r / "subject-native.json"
    gate.private_json(out, subject)
    digest = gate.sha(out.read_bytes())
    env["PALS_LOCAL_CANDIDATE_SHA256"] = digest
    write_env(r / "local.env", env)
    run(
        [*compose, "up", "-d", "--no-build", "--wait", "--wait-timeout", "45", "api"],
        60,
    )
    gate.web_provenance(subject)
    gate.verifier_provenance(subject)
    gate.runtime(subject)
    canary = gate.compiler_canary(subject)
    budget = gate.budget_status(subject)
    # The restarted guard must actually serve the inspected certificate.
    served = gate.provider_tls_status(
        subject, minimum_seconds=PROVIDER_TLS_SERVED_SECONDS
    )
    result = {
        "state": "prepared_dependency_ready_not_product_accepted",
        "subject": ref(out),
        "compiler_canary": canary,
        "provider_tls": served,
        "all_lane_cost_microusd": budget["actual_microusd"],
        "budget_limit_microusd": budget["limit_microusd"],
    }
    gate.private_json(r / "preparation-result.json", result)
    print(gate.stable(result))


if __name__ == "__main__":
    try:
        main()
    except gate.Refusal as error:
        # Closed code on stdout; the cause, if any, is in the named private file.
        refusal = {"state": "refused", "code": str(error)}
        if error.detail:
            refusal["diagnostic"] = error.detail
        print(gate.stable(refusal))
        raise SystemExit(1) from None
