#!/usr/bin/env python3
"""Controlled local qualification. Real DB/compiler/provider; explicitly no AWS/auth equivalence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).resolve().parent
OWNER = "01a1bb4b-dec2-76f0-a6fe-32405e465d6e"


REQUIRED_MODULES = ("psycopg",)
DIAGNOSTIC_LIMIT = 16 * 1024
# The paid browser journey is bounded at 620 s; the local proxy certificate must outlive it.
PROVIDER_TLS_CAPTURE_SECONDS = 1200
_DIAGNOSTICS = {"directory": None}
_SECRET_VALUES = set()
# Redaction input is bounded too; the cut is moved to a line start (see persist_diagnostic).
DIAGNOSTIC_SCAN_LIMIT = 64 * DIAGNOSTIC_LIMIT
_SECRET_WORD = (
    r"pass(?:word|wd|phrase)?|secret|token|api[_-]?key|private[_-]?key|credential"
    r"|authorization|auth|hash[_-]?key|dsn|database[_-]?url"
)
_SECRET_NAME = re.compile(r"KEY|" + _SECRET_WORD, re.I)
_QUOTED = r"""\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'"""
# Deliberately conservative: losing harmless text is acceptable, writing a secret is not.
_SECRET_PATTERNS = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]+-----.*?(?:-----END [A-Z0-9 ]+-----|\Z)", re.S
        ),
        "<pem>",
    ),
    # A key block whose BEGIN line is not in the text still shows as encoded lines.
    (re.compile(r"(?m)^[ \t]*[A-Za-z0-9+/=_-]{40,}[ \t]*$"), "<encoded>"),
    # Whole userinfo up to the LAST "@" of the token: passwords may contain "/" or ":".
    (re.compile(r"([A-Za-z][A-Za-z0-9+.-]*://)[^\s\"'<>]*@"), r"\1<credentials>@"),
    (re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{4,}"), r"\1 <token>"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{8,}"), "<token>"),
    (re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "<access-key>"),
    (re.compile(r"\b\d{12}\b"), "<account>"),
    # key=value, key: value, "key": "value", 'key': 'value' and dict/JSON reprs.
    (
        re.compile(
            r"(?i)([\"']?[A-Za-z0-9_.-]*(?:"
            + _SECRET_WORD
            + r")[A-Za-z0-9_.-]*[\"']?\s*[:=]\s*)(?:"
            + _QUOTED
            + r"|[^\s,;}\])]+)"
        ),
        r"\1<redacted>",
    ),
)


class Refusal(Exception):
    """Closed refusal code. ``detail`` names a private diagnostic file, never its content."""

    def __init__(self, code, detail=None):
        super().__init__(code)
        self.detail = detail or {}


def need(value, code):
    if not value:
        raise Refusal(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def now():
    return datetime.now(timezone.utc).isoformat()


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def private_json(path, value):
    path.write_text(stable(value) + "\n")
    path.chmod(0o600)


def require_modules(modules=REQUIRED_MODULES, *, prefix="release_python"):
    # Fail before any dependency is touched. A missing driver otherwise surfaces much
    # later as an unexplained child-process failure.
    for name in modules:
        try:
            found = importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            found = False
        need(found, prefix + "_missing_module:" + name)


def set_diagnostic_directory(path):
    path = Path(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    need(
        not path.is_symlink() and path.stat().st_mode & 0o777 == 0o700,
        "private_diagnostic_directory_required",
    )
    _DIAGNOSTICS["directory"] = path


def _secret_parts(name, value):
    """Exact values to hide for one environment entry, including URI credentials."""
    if type(value) is not str or not value:
        return
    named = bool(_SECRET_NAME.search(name or ""))
    # Short values are hidden only under a secret-looking name: hiding every short
    # ordinary setting ("local", "true") would leave nothing readable.
    if len(value) >= (4 if named else 8):
        yield value
    match = re.match(r"[A-Za-z][A-Za-z0-9+.-]*://([^\s]*)@", value)
    if match:
        userinfo = match.group(1)
        yield userinfo
        user, _, password = userinfo.partition(":")
        if password:
            yield password
        if len(user) >= 8:
            yield user


def register_secrets(values):
    """``values`` is a mapping of names to values, or bare values of unknown name."""
    items = values.items() if hasattr(values, "items") else (("", v) for v in values)
    for name, value in items:
        _SECRET_VALUES.update(_secret_parts(name, value))


def register_private_env(path):
    """Best effort: a missing or unsafe file is refused later by its real consumer."""
    try:
        private_env(Path(path))
    except (OSError, ValueError, Refusal):
        pass


def redact(text):
    known = set(_SECRET_VALUES)
    for name, value in os.environ.items():
        known.update(_secret_parts(name, value))
    for value in sorted(known, key=len, reverse=True):
        text = text.replace(value, "<redacted>")
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _tail_from_line_start(text, limit):
    """Last ``limit`` characters, never starting inside a line.

    A cut inside a line could keep the unrecognisable remainder of a secret or of a
    redaction match, so the partial first line is dropped entirely.
    """
    if len(text) <= limit:
        return text, False
    tail = text[-limit:]
    if text[-limit - 1] != "\n":
        _, newline, tail = tail.partition("\n")
        if not newline:
            tail = ""
    return tail, True


def redacted_tail(stderr):
    # Redact BEFORE taking the tail: truncating first can cut a secret or key block so
    # that its remainder no longer matches any rule and is written in clear text.
    scanned, cut = _tail_from_line_start(stderr or "", DIAGNOSTIC_SCAN_LIMIT)
    tail, truncated = _tail_from_line_start(redact(scanned), DIAGNOSTIC_LIMIT)
    return tail, cut or truncated


def command_name(args):
    """Program and script/subcommand names only: never arguments, paths or environment."""
    words = [Path(str(args[0])).name]
    for value in args[1:]:
        value = str(value)
        if "/" in value:
            if not value.startswith("-"):
                words.append(Path(value).name)
            break
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", value) or len(words) >= 3:
            break
        words.append(value)
    return " ".join(re.sub(r"[^A-Za-z0-9._-]", "_", word)[:64] for word in words)


def persist_diagnostic(args, returncode, stderr):
    """Keep a bounded, redacted stderr tail in a private file and return its reference."""
    name = command_name(args)
    detail = {"failed_command": name}
    directory = _DIAGNOSTICS["directory"]
    if directory is None:
        return detail
    tail, truncated = redacted_tail(stderr)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    file = directory / ("command-failure-" + stamp + "-" + uuid4().hex[:8] + ".json")
    descriptor = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.write(
            stable(
                {
                    "schema_version": "pals.local-qualification-command-failure.v1",
                    "failed_command": name,
                    "returncode": returncode,
                    "stderr_tail_redacted": tail,
                    "stderr_truncated": truncated,
                    "at": now(),
                }
            )
            + "\n"
        )
    detail["diagnostic_file"] = str(file)
    return detail


def command(args, timeout=30):
    result = subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode != 0:
        # The closed code stays stable; the cause is kept in a private bounded file.
        raise Refusal(
            "local_dependency_command_failed",
            persist_diagnostic(args, result.returncode, result.stderr),
        )
    return result.stdout


def private_env(path):
    st = path.lstat()
    need(
        path.is_file() and not path.is_symlink() and st.st_mode & 0o777 == 0o600,
        "private_environment_required",
    )
    values = dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if line and not line.startswith("#")
    )
    register_secrets(values)
    return values


def file_reference(value):
    need(
        type(value) is dict
        and set(value) == {"path", "sha256"}
        and type(value["path"]) is str
        and type(value["sha256"]) is str,
        "closed_file_reference_required",
    )
    p = Path(value["path"])
    need(
        p.is_absolute()
        and p.is_file()
        and not p.is_symlink()
        and sha(p.read_bytes()) == value["sha256"],
        "frozen_provenance_file_changed",
    )
    return p


def web_provenance(subject):
    v = subject["web_variant"]
    publication = file_reference(v["production_publication"])
    archive = file_reference(v["source_archive"])
    provenance = file_reference(v["local_build_provenance"])
    pub = json.loads(publication.read_bytes())
    receipt = json.loads(provenance.read_bytes())
    image = subject["images"]["web"]
    need(
        pub["image_uri"].endswith("@" + v["production_image_digest"])
        and pub["docker_image_id"] == v["production_image_digest"]
        and pub["source_commit"] == image["source_revision"]
        and pub["source_archive_sha256"] == sha(archive.read_bytes()),
        "production_web_source_binding_changed",
    )
    with tarfile.open(archive) as t:
        dockerfile = t.extractfile("Dockerfile").read()
    need(
        sha(dockerfile) == v["dockerfile_sha256"] == receipt["dockerfile_sha256"]
        and sha(archive.read_bytes()) == v["source_archive_sha256"],
        "actual_archive_dockerfile_changed",
    )
    need(
        receipt["schema_version"] == "pals.local-web-build.v1"
        and receipt["source_archive"] == v["source_archive"]
        and receipt["production_publication"] == v["production_publication"]
        and receipt["source_revision"] == image["source_revision"]
        and receipt["built_image_id"] == image["image_id"]
        and receipt["platform"] == image["platform"],
        "actual_local_build_binding_changed",
    )
    spec = importlib.util.spec_from_file_location(
        "local_web_build", HERE / "local-web-build.py"
    )
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    need(
        v["local_build_args"] == receipt["local_build_args"] == builder.LOCAL_ARGS,
        "closed_loopback_build_args_required",
    )
    command(
        [
            sys.executable,
            str(HERE / "local-web-build.py"),
            "--verify-receipt",
            str(provenance),
        ],
        timeout=60,
    )
    return {
        "publication_sha256": sha(publication.read_bytes()),
        "source_archive_sha256": sha(archive.read_bytes()),
        "build_provenance_sha256": sha(provenance.read_bytes()),
    }


def compiler_canary(subject):
    # Dependency readiness only. This fixed True theorem is never a proof-quality
    # fixture or acceptance answer; the paid journey below still must verify real math.
    program = """import asyncio,json,hashlib
from dataclasses import asdict
from uuid import uuid4
from app.release.verified_reconciler import VerifiedReconcilerSettings,_tls_reader
from app.infrastructure.verifier.tls_material import build_reconciler_ssl_context
from app.infrastructure.verifier.isolated_http import HttpxIsolatedVerifierClient,IsolatedVerifierTransportError
from app.domain.ports.isolated_verifier import IsolatedVerifierRequest
async def check():
 s=VerifiedReconcilerSettings.from_env()
 client=HttpxIsolatedVerifierClient(base_url=s.verifier_url,binding=s.binding,ssl_context=build_reconciler_ssl_context(s.tls,reader=_tls_reader(s)))
 ready=await client.readiness()
 source="theorem pals_local_readiness_canary : True := by trivial\\n"
 job=str(uuid4());uri="s3://pals-local-artifacts/proof-jobs/"+job+"/result.lean"
 answer=await client.verify(IsolatedVerifierRequest(proof_job_id=job,lean_code=source,result_artifact_uri=uri))
 if answer.attestation is None:return {"state":"rejected","failure_code":answer.failure_code,"retryable":answer.retryable,"diagnostic_codes":[x.code for x in answer.diagnostics]}
 assert answer.attestation.verification_succeeded and answer.attestation.proof_job_id==job and answer.attestation.result_artifact_uri==uri and answer.attestation.lean_sha256==hashlib.sha256(source.encode()).hexdigest()
 return {"state":"verified","scope":"dependency_readiness_only_not_product_acceptance","source_sha256":hashlib.sha256(source.encode()).hexdigest(),"verifier_image_digest":ready.verifier_image_digest,"toolchain_sha256":ready.verifier_toolchain_sha256,"release_id":str(ready.release_id),"deployment_binding_sha256":ready.deployment_binding_sha256,"attestation_sha256":hashlib.sha256(json.dumps(asdict(answer.attestation),sort_keys=True).encode()).hexdigest(),"elapsed_ms":answer.elapsed_ms}
try:print(json.dumps(asyncio.run(asyncio.wait_for(check(),timeout=45))))
except IsolatedVerifierTransportError:print(json.dumps({"state":"unavailable","failure_code":"verifier_contract_or_transport_invalid"}))
except TimeoutError:print(json.dumps({"state":"unavailable","failure_code":"verifier_canary_deadline"}))
"""
    try:
        result = json.loads(
            command(
                [
                    "docker",
                    "exec",
                    "pals-reliability-local-reconciler-1",
                    "python",
                    "-c",
                    program,
                ],
                timeout=55,
            )
        )
    except (Refusal, subprocess.TimeoutExpired):
        raise Refusal("actual_http_compiler_canary_dependency_failed") from None
    need(
        result.get("state") == "verified",
        "actual_http_compiler_canary_"
        + str(result.get("failure_code", "invalid_result")),
    )
    need(
        result["verifier_image_digest"] == subject["images"]["verifier"]["image_id"],
        "actual_http_canary_runtime_mismatch",
    )
    return result


# Exactly the key set pals-infra's release-cycle.py `local_verifier_variant` accepts.
VERIFIER_VARIANT_KEYS = {
    "production_image_digest",
    "source_archive",
    "recipe_archive",
    "local_build_provenance",
    "dockerfile_sha256",
    "lean_version",
    "lake_manifest_sha256",
}


def verifier_provenance(subject):
    v = subject["verifier_variant"]
    need(
        type(v) is dict and set(v) == VERIFIER_VARIANT_KEYS,
        "closed_native_local_verifier_variant_required",
    )
    archive = file_reference(v["source_archive"])
    recipe = file_reference(v["recipe_archive"])
    provenance = file_reference(v["local_build_provenance"])
    receipt = json.loads(provenance.read_bytes())
    image = subject["images"]["verifier"]
    need(
        receipt["schema_version"] == "pals.local-verifier-build.v2"
        and receipt["source_archive"] == v["source_archive"]
        and receipt["recipe_archive"] == v["recipe_archive"]
        and receipt["source_revision"] == image["source_revision"]
        and receipt["built_image_id"] == image["image_id"]
        and receipt["platform"] == image["platform"] == "linux/arm64",
        "native_verifier_build_binding_changed",
    )
    # The image was built from the complete archive of the commit, which the receipt
    # (itself hash-bound into the subject) pins. The two archives the release plan
    # pins must be exact projections of that same commit: re-derived from git and
    # compared member by member with the built archive.
    complete = file_reference(receipt["build_archive"])
    spec = importlib.util.spec_from_file_location(
        "local_verifier_archives", HERE / "local-verifier-archives.py"
    )
    archives = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(archives)
    try:
        archives.verify(
            receipt["source_root"],
            receipt["source_revision"],
            complete,
            {name: v[name] for name in archives.PROJECTIONS},
            "differs",
        )
        dockerfile, lean, lake = archives.recipe(recipe)
        lean = lean.decode().strip()
    except (ValueError, OSError, tarfile.TarError, subprocess.TimeoutExpired):
        raise Refusal(
            "native_verifier_plan_archive_differs_from_the_built_commit"
        ) from None
    need(
        sha(dockerfile) == v["dockerfile_sha256"] == receipt["dockerfile_sha256"]
        and lean == v["lean_version"] == receipt["lean_version"]
        and sha(lake) == v["lake_manifest_sha256"] == receipt["lake_manifest_sha256"],
        "actual_native_verifier_toolchain_changed",
    )
    command(
        [
            sys.executable,
            str(HERE / "local-verifier-build.py"),
            "--verify-receipt",
            str(provenance),
        ],
        timeout=60,
    )
    return {
        "source_archive_sha256": sha(archive.read_bytes()),
        "recipe_archive_sha256": sha(recipe.read_bytes()),
        "build_archive_sha256": sha(complete.read_bytes()),
        "build_provenance_sha256": sha(provenance.read_bytes()),
        "difference_scope": receipt["difference_scope"],
    }


def provider_tls_status(subject, minimum_seconds=PROVIDER_TLS_CAPTURE_SECONDS):
    """Real handshake with the running local budget proxy, trusting the task CA only.

    Workers reach the provider solely through this proxy. An expired or replaced proxy
    certificate fails every provider call, so refuse before the single paid submission.
    No HTTP request is sent and no provider is contacted.
    """
    expected = subject["guard"].get("provider_tls")
    need(
        type(expected) is dict
        and re.fullmatch(
            r"[0-9a-f]{64}", str(expected.get("server_certificate_sha256"))
        ),
        "local_provider_tls_subject_binding_required",
    )
    program = """import hashlib,json,socket,ssl,time
context=ssl.create_default_context(cafile='/run/provider/ca-bundle.pem')
try:
 with socket.create_connection(('127.0.0.1',443),5) as raw:
  with context.wrap_socket(raw,server_hostname='api.openai.com') as tls:
   der=tls.getpeercert(binary_form=True);peer=tls.getpeercert()
   try:tls.unwrap()
   except (OSError,ssl.SSLError):pass
 print(json.dumps({'state':'trusted','sha256':hashlib.sha256(der).hexdigest(),'remaining_seconds':int(ssl.cert_time_to_seconds(peer['notAfter'])-time.time())}))
except ssl.SSLCertVerificationError as error:print(json.dumps({'state':'expired' if error.verify_code==10 else 'untrusted'}))
except (OSError,ssl.SSLError):print(json.dumps({'state':'unavailable'}))
"""
    try:
        result = json.loads(
            command(
                [
                    "docker",
                    "exec",
                    "pals-reliability-local-worker-network-guard-1",
                    "python",
                    "-c",
                    program,
                ],
                timeout=20,
            )
        )
    except subprocess.TimeoutExpired:
        raise Refusal("local_provider_tls_unavailable_or_untrusted") from None
    need(result.get("state") != "expired", "local_provider_tls_expired")
    need(
        result.get("state") == "trusted", "local_provider_tls_unavailable_or_untrusted"
    )
    need(
        result["sha256"] == expected["server_certificate_sha256"],
        "local_provider_tls_differs_from_subject",
    )
    need(
        type(result["remaining_seconds"]) is int
        and result["remaining_seconds"] >= minimum_seconds,
        "local_provider_tls_expires_before_capture_window",
    )
    return {
        "scope": "local_budget_proxy_transport_only_not_provider_identity",
        "server_certificate_sha256": result["sha256"],
        "remaining_seconds": result["remaining_seconds"],
    }


def budget_status(subject):
    ledger = json.loads(
        command(
            [
                "docker",
                "exec",
                "pals-reliability-local-worker-network-guard-1",
                "cat",
                "/run/budget/ledger.json",
            ]
        )
    )
    need(
        not ledger["blocked"]
        and ledger["limit_microusd"]
        == subject["guard"]["budget_limit_microusd"]
        == 700000
        and all(x["state"] == "completed" for x in ledger["calls"])
        and 0 <= ledger["actual_microusd"] == ledger["reserved_microusd"] <= 700000,
        "bounded_known_all_lane_provider_usage_required",
    )
    return ledger


def database_readiness(subject, environment_file, *, require_frozen=True):
    contract = subject["database_contract"]
    need(
        contract["api_source_revision"] == subject["images"]["api"]["source_revision"],
        "database_source_contract_changed",
    )
    sql_file = file_reference(contract["migration_sql"])
    manifest = file_reference(contract["migration_manifest"])
    source = Path(contract["api_source_root"])
    need(
        sql_file
        == source / "app/db/migrations/draft_addition_candidates/001_candidates.sql"
        and manifest
        == source / "app/db/migrations/draft_addition_candidates/manifest.json",
        "closed_database_migration_files_required",
    )
    program = """import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from database_readiness import inspect
values=dict(line.split('=',1) for line in Path(sys.argv[2]).read_text().splitlines() if line and not line.startswith('#'))
try:
 result=inspect(values['PALS_HOST_DATABASE_URL'],Path(sys.argv[3]),sys.argv[4])
 print(json.dumps({'state':'ready','observation':result},sort_keys=True))
except ValueError as error:print(json.dumps({'state':'unavailable','code':str(error)}))
"""
    result = json.loads(
        command(
            [
                sys.executable,
                "-c",
                program,
                str(HERE / "local-qualification"),
                str(environment_file),
                str(source),
                contract["api_source_revision"],
            ]
        )
    )
    need(
        result.get("state") == "ready",
        "actual_local_database_readiness_failed:"
        + str(result.get("code", "dependency_failed")),
    )
    observation = result["observation"]
    if require_frozen:
        need(
            contract.get("schema_fingerprint_sha256")
            == observation["schema_fingerprint_sha256"],
            "actual_database_schema_or_privileges_differ_from_subject",
        )
    return observation


def runtime(subject):
    result = {}
    role_images = {
        "api": "api",
        "reconciler": "api",
        "worker": "worker",
        "assessment-worker": "worker",
        "recipe-reviewer": "worker",
        "verifier": "verifier",
        "webfront": "web",
    }
    role_images["worker-network-guard"] = "guard"
    for role, image_role in role_images.items():
        name = "pals-reliability-local-" + role + "-1"
        x = json.loads(command(["docker", "inspect", name]))[0]
        expected = subject["images"][image_role]
        need(
            x["Config"]["Labels"].get("codex.owner") == OWNER, "runtime_owner_mismatch"
        )
        need(
            x["Image"] == expected["image_id"]
            and x["State"]["Running"]
            and x["State"].get("Health", {}).get("Status") == "healthy",
            "exact_healthy_runtime_required_" + role,
        )
        image = json.loads(command(["docker", "image", "inspect", x["Image"]]))[0]
        need(
            image["Os"] + "/" + image["Architecture"] == expected["platform"],
            "actual_runtime_platform_changed",
        )
        if image_role != "guard":
            need(
                image["Config"]["Labels"].get("org.opencontainers.image.revision")
                == expected["source_revision"],
                "runtime_source_mismatch",
            )
        environment = sorted(x["Config"]["Env"])
        # The local subject identity is checked through the real response header; exclude
        # only that self-reference from the frozen environment hash to avoid a hash cycle.
        frozen_environment = [
            item
            for item in environment
            if not item.startswith("PALS_CLOUD_RESTORE_MANIFEST_SHA256=")
        ]
        result[role] = {
            "container_id": x["Id"],
            "image_id": x["Image"],
            "started_at": x["State"]["StartedAt"],
            "environment_sha256": sha(stable(frozen_environment).encode()),
            "full_environment_sha256": sha(stable(environment).encode()),
            "host_config_sha256": sha(stable(x["HostConfig"]).encode()),
        }
        need(
            subject["runtime_config"][role]
            == {
                key: result[role][key]
                for key in ("image_id", "environment_sha256", "host_config_sha256")
            },
            "frozen_runtime_configuration_changed_" + role,
        )
    for name in ("guard.py", "budget_proxy.py"):
        actual = command(
            [
                "docker",
                "exec",
                "pals-reliability-local-worker-network-guard-1",
                "python",
                "-c",
                "from pathlib import Path;import hashlib;print(hashlib.sha256(Path('/opt/pals-local/"
                + name
                + "').read_bytes()).hexdigest())",
            ]
        ).strip()
        need(
            actual
            == subject["guard"]["source_sha256"][name]
            == sha((HERE / "local-qualification" / name).read_bytes()),
            "guard_source_changed",
        )
    return result


def database(url, browser, subject):
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as c:
        c.execute("SET TRANSACTION READ ONLY")
        c.execute("SET LOCAL statement_timeout='5s'")
        need(
            c.execute(
                "SELECT current_database() name,current_setting('server_version_num')::int/10000 major"
            ).fetchone()
            == {"name": "pals", "major": 16},
            "local_database_identity_mismatch",
        )
        row = c.execute(
            "SELECT to_jsonb(r) request,to_jsonb(p) job,to_jsonb(e) explanation FROM proof_requests r JOIN proof_jobs p ON p.id=r.formal_job_id JOIN proof_explanations e ON e.proof_job_id=p.id WHERE r.id=%s",
            (browser["id"],),
        ).fetchone()
        need(row is not None, "persisted_proof_and_explanation_required")
        request, job, explanation = row["request"], row["job"], row["explanation"]
        need(
            request["status"] == "answered"
            and job["state"] == "verified"
            and explanation["state"] == "completed",
            "persisted_terminal_states_required",
        )
        need(
            request["chat_id"] == browser["chat_id"] == job["chat_id"]
            and job["owner_user_id"] == request["owner_user_id"],
            "persisted_owner_binding_mismatch",
        )
        content = explanation["content"]
        need(
            isinstance(content.get("conclusion"), str)
            and content["conclusion"].strip(),
            "persisted_conclusion_required",
        )
        preceding = [
            content.get("overview", ""),
            *[section["summary"] for section in content["sections"]],
        ]
        projection = "\n\n".join(
            x.strip() for x in [*preceding, content["conclusion"]] if x.strip()
        )
        norm = lambda x: " ".join(x.split())
        need(
            norm(request["answer"]["text"]) == norm(projection),
            "persisted_answer_dropped_conclusion",
        )
        need(
            sha(request["answer"]["text"].encode()) == browser["answer_sha256"]
            and sha(job["lean_code"].encode()) == browser["lean_sha256"],
            "api_db_content_mismatch",
        )
        attestation = job.get("verifier_attestation")
        need(
            isinstance(attestation, dict) and attestation,
            "real_verifier_attestation_required",
        )
        # The real attestation predicate validates the stored job/code binding, not a caller flag.
        bound = c.execute(
            "SELECT public.pals_verifier_attestation_is_bound(id,lean_code,result_artifact_uri,verifier_attestation) bound FROM proof_jobs WHERE id=%s",
            (job["id"],),
        ).fetchone()
        need(bound and bound["bound"] is True, "bound_verifier_attestation_required")
        usage = c.execute(
            "SELECT usage,cost_microusd FROM proof_request_usage WHERE request_id=%s ORDER BY created_at,call_id",
            (browser["id"],),
        ).fetchall()
        need(
            usage and all(x["cost_microusd"] is not None for x in usage),
            "known_real_provider_usage_required",
        )
        cost = sum(x["cost_microusd"] for x in usage)
        need(0 < cost < 1_000_000, "approved_cost_limit_exceeded_or_no_usage")
        return {
            "request_sha256": sha(browser["id"].encode()),
            "chat_sha256": sha(browser["chat_id"].encode()),
            "job_sha256": sha(job["id"].encode()),
            "explanation_sha256": sha(stable(content).encode()),
            "conclusion_sha256": sha(content["conclusion"].encode()),
            "conclusion_characters": len(content["conclusion"]),
            "verifier_attestation_sha256": sha(stable(attestation).encode()),
            "provider_calls": len(usage),
            "cost_microusd": cost,
            "provider_usage": [x["usage"] for x in usage],
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--subject", type=Path, required=True)
    p.add_argument("--state-dir", type=Path, required=True)
    p.add_argument("--web-root", type=Path, required=True)
    p.add_argument("--database-env", type=Path, required=True)
    p.add_argument("--verify-existing", action="store_true")
    args = p.parse_args()
    require_modules()
    state = args.state_dir.resolve()
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    need(
        state.stat().st_mode & 0o777 == 0o700 and not state.is_symlink(),
        "private_state_directory_required",
    )
    set_diagnostic_directory(state / "diagnostics")
    # Known private values are hidden from any diagnostic written from here on.
    register_private_env(args.database_env)
    raw = args.subject.read_bytes()
    subject = json.loads(raw)
    digest = sha(raw)
    need(
        subject.get("schema_version") == "pals.local-qualification-subject.v1"
        and subject.get("basis") == "approved-local-real-db-lean-model",
        "explicit_local_subject_required",
    )
    fixture = subject["fixture"]
    need(
        type(fixture["paid_submissions"]) is int
        and fixture["paid_submissions"] == 1
        and type(fixture["maximum_approved_usd"]) is int
        and fixture["maximum_approved_usd"] == 1
        and fixture["output_language"] == "en",
        "approved_one_proof_budget_required",
    )
    prior = None
    if args.verify_existing:
        prior = json.loads((state / "latest.json").read_text())
        need(
            prior.get("state") == "accepted"
            and prior["subject_sha256"] == digest
            and type(prior["expires_at"]) in (int, float)
            and datetime.now(timezone.utc).timestamp() < prior["expires_at"]
            and parse_time(prior["finished_at"]) <= datetime.now(timezone.utc),
            "fresh_existing_capture_required",
        )
        need(
            prior["runner_sha256"] == sha(Path(__file__).read_bytes())
            and prior["browser_runner_sha256"]
            == sha((HERE / "local-qualification-browser.cjs").read_bytes())
            and prior["semantics_runner_sha256"]
            == sha((HERE / "release-acceptance-browser.cjs").read_bytes()),
            "existing_capture_runner_changed",
        )
        private_env_path = state / "guest-storage.json"
        need(
            private_env_path.is_file()
            and not private_env_path.is_symlink()
            and private_env_path.stat().st_mode & 0o777 == 0o600,
            "own_private_guest_session_required",
        )
    else:
        need(
            not (state / "submission.json").exists(),
            "prior_submission_exists_no_automatic_retry",
        )
    record = {
        "schema_version": "pals.local-qualification-result.v1",
        "basis": subject["basis"],
        "run_id": str(uuid4()),
        "subject_sha256": digest,
        "state": "running",
        "started_at": now(),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "browser_runner_sha256": sha(
            (HERE / "local-qualification-browser.cjs").read_bytes()
        ),
        "semantics_runner_sha256": sha(
            (HERE / "release-acceptance-browser.cjs").read_bytes()
        ),
        "boundaries": subject["local_profile"],
    }
    private_json(state / "latest.json", record)
    try:
        record["web_provenance"] = web_provenance(subject)
        record["verifier_provenance"] = verifier_provenance(subject)
        before = runtime(subject)
        if prior:
            need(before == prior["runtime_before"], "existing_capture_runtime_changed")
        record["runtime_before"] = before
        private_json(state / "latest.json", record)
        record["provider_budget_before"] = budget_status(subject)
        record["database_before"] = database_readiness(subject, args.database_env)
        if not prior:
            # Re-reading an accepted capture makes no provider call. A fresh capture
            # must not spend its only submission on a dead local provider transport.
            record["provider_tls_before"] = provider_tls_status(subject)
        # Never launch a browser that could submit a paid proof while the actual
        # mTLS verifier cannot establish its mandatory compiler sandbox.
        record["compiler_canary"] = compiler_canary(subject)
        activated = max(
            parse_time(x["started_at"]) for x in before.values()
        ).isoformat()
        payload = {
            "subject": subject,
            "subject_sha256": digest,
            "state_dir": str(state),
            "web_root": str(args.web_root.resolve()),
            "activated_at": activated,
        }
        if prior:
            payload.update(
                verify_existing=True,
                existing={key: prior["browser"][key] for key in ("id", "chat_id")},
            )
        proc = subprocess.Popen(
            ["node", str(HERE / "local-qualification-browser.cjs")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(stable(payload), timeout=620)
        need(proc.returncode == 0, "browser_journey_failed:" + stderr[:200])
        observed = json.loads(stdout)
        private_json(state / "browser-result.json", observed)
        record["browser"] = observed
        record["database"] = database(
            private_env(args.database_env)["PALS_HOST_DATABASE_URL"], observed, subject
        )
        record["database_after"] = database_readiness(subject, args.database_env)
        need(
            record["database_before"] == record["database_after"],
            "database_schema_or_privileges_changed_during_capture",
        )
        ledger = budget_status(subject)
        need(
            ledger["calls"] and ledger["actual_microusd"] > 0,
            "real_provider_usage_required",
        )
        record["all_lane_provider_budget"] = ledger
        after = runtime(subject)
        need(before == after, "runtime_changed_during_capture")
        record.update(
            state="accepted",
            finished_at=now(),
            expires_at=(datetime.now(timezone.utc).timestamp() + 3600),
        )
    except Exception as error:  # noqa: BLE001 - Persist every failure without leaking dependency secrets.
        record.update(
            state="failed",
            finished_at=now(),
            code=str(error)
            if isinstance(error, Refusal)
            else "local_dependency_or_capture_failed",
        )
        if isinstance(error, Refusal) and error.detail:
            record["diagnostic"] = error.detail
        private_json(state / "latest.json", record)
        print(
            stable(
                {
                    k: record[k]
                    for k in ("state", "subject_sha256", "code", "diagnostic")
                    if k in record
                }
            )
        )
        return 1
    private_json(state / "latest.json", record)
    print(
        stable(
            {
                "state": record["state"],
                "subject_sha256": digest,
                "all_lane_provider_calls": len(
                    record["all_lane_provider_budget"]["calls"]
                ),
                "all_lane_cost_microusd": record["all_lane_provider_budget"][
                    "actual_microusd"
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as error:
        print(str(error), file=sys.stderr)
        if error.detail:
            print(stable(error.detail), file=sys.stderr)
        raise SystemExit(1)
