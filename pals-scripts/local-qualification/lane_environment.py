"""Prepare private local.env inputs for both qualification lanes without bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
from contextlib import ExitStack, contextmanager

import relay_compose
from lanes import ENDPOINTS, absolute, need, pin, read_document

LOCAL_ENV = "local.env"
OUTPUTS = (LOCAL_ENV, "release.env", "recipe.env")
SEMANTICS = {
    "PALS_ENV": r"local",
    "PALS_ENVIRONMENT": r"local",
    "PALS_LOCAL_RELEASE_CONTRACT": r"legacy-local-v1",
    "PALS_LLM_PROVIDER": r"openai",
    "PALS_OPENAI_MODEL": r"gpt-[0-9][a-z0-9.-]{0,58}",
    "PALS_OPENAI_MAX_OUTPUT_TOKENS": r"[1-9][0-9]{0,4}",
    "PALS_PROOF_WORKER_LANE": r"proof|all",
    "PALS_TOKEN_ACCOUNTING_ENABLED": r"true|false",
    "PALS_PROOF_JOBS_VISIBILITY_TIMEOUT": r"[1-9][0-9]{0,4}",
}


def settings_from_seed(path, sha256):
    path = absolute(str(path))
    need(
        pin(sha256) and path.resolve(strict=True) == path,
        "exact_local_env_seed_required",
    )
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as stream:
        info = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(info.st_mode)
            and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_uid == os.geteuid()
            and info.st_nlink == 1
            and 0 < info.st_size <= 131_072,
            "private_local_env_seed_required",
        )
        raw = stream.read(131_073)
    need(
        len(raw) == info.st_size and hashlib.sha256(raw).hexdigest() == sha256,
        "local_env_seed_hash_changed",
    )
    values = {}
    for line in raw.decode().splitlines():
        key, separator, value = line.partition("=")
        if key not in SEMANTICS:
            continue
        need(
            separator and key not in values and re.fullmatch(SEMANTICS[key], value),
            "local_env_seed_policy_differs",
        )
        values[key] = value
    need(
        set(values) == SEMANTICS.keys()
        and int(values["PALS_OPENAI_MAX_OUTPUT_TOKENS"]) <= 32768
        and int(values["PALS_PROOF_JOBS_VISIBILITY_TIMEOUT"]) <= 43200,
        "local_env_seed_policy_differs",
    )
    return values


def lane_values(role, selected, semantics):
    ports = ENDPOINTS[role]
    web = f"http://localhost:{ports['web']}"
    api = f"http://localhost:{ports['api']}"
    cognito = f"http://localhost:{ports['cognito']}"
    host_aws = f"http://127.0.0.1:{ports['localstack']}"
    service_aws = "http://localstack:4566"
    user = f"pals_qual_{role}"
    password = secrets.token_hex(32)
    queue = f"pals-local-{role}-proof-jobs"
    pool = "ap-northeast-1_local"
    app_client = "pals-local-acceptance"
    return {
        **semantics,
        "POSTGRES_USER": user,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": "pals",
        "POSTGRES_HOST_PORT": str(ports["postgres"]),
        "PALS_DATABASE_URL": f"postgresql://{user}:{password}@postgres:5432/pals",
        "PALS_HOST_DATABASE_URL": f"postgresql://{user}:{password}@127.0.0.1:{ports['postgres']}/pals",
        "PALS_LOCAL_DATABASE_HOST": "postgres",
        "PALS_LOCAL_DATABASE_PORT": "5432",
        "PALS_LOCAL_DATABASE_NAME": "pals",
        "PALS_LOCAL_DATABASE_USERNAME": user,
        "PALS_LOCAL_DATABASE_PASSWORD": password,
        "PALS_HOST_BIND_ADDRESS": "127.0.0.1",
        "PALS_API_HOST_PORT": str(ports["api"]),
        "PALS_WEB_HOST_PORT": str(ports["web"]),
        "COGNITO_LOCAL_HOST_PORT": str(ports["cognito"]),
        "LOCALSTACK_HOST_PORT": str(ports["localstack"]),
        "PALS_AGENT_API_BASE_URL": "http://api:8000",
        "PALS_API_BASE_URL": "http://api:8000",
        "PALS_HOST_AWS_ENDPOINT_URL": host_aws,
        "PALS_AWS_ENDPOINT_URL": service_aws,
        "LOCALSTACK_ENDPOINT_URL": service_aws,
        "PALS_PROOF_JOBS_QUEUE_NAME": queue,
        "PALS_PROOF_JOBS_DLQ_NAME": queue + "-dlq",
        "PALS_PROOF_REQUESTS_QUEUE_NAME": f"pals-local-{role}-proof-requests",
        "PALS_PROOF_REQUESTS_DLQ_NAME": f"pals-local-{role}-proof-requests-dlq",
        "PALS_HOST_PROOF_JOBS_QUEUE_URL": f"{host_aws}/000000000000/{queue}",
        "PALS_PROOF_JOBS_QUEUE_URL": f"{service_aws}/000000000000/{queue}",
        "PALS_ARTIFACTS_BUCKET": f"pals-local-{role}-artifacts",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "AWS_REGION": "ap-northeast-1",
        "AWS_DEFAULT_REGION": "ap-northeast-1",
        "OPENAI_API_KEY": "local-provider-relay",
        "PALS_OPENAI_BASE_URL": "https://api.openai.com/v1",
        "PALS_LOCAL_RUNTIME_ENABLED": "true",
        "PALS_AGENT_MODE": "sqs",
        "PALS_AGENT_USE_S3_ARTIFACTS": "1",
        "PALS_GUEST_CHAT_ENABLED": "true",
        "PALS_AUTH_DISABLED": "false",
        "NEXT_PUBLIC_PALS_AUTH_DISABLED": "false",
        "PALS_GUEST_ALLOWED_ORIGINS": json.dumps([web], separators=(",", ":")),
        "PALS_GUEST_HASH_KEY": secrets.token_hex(32),
        "PALS_WORKER_SHARED_SECRET": secrets.token_hex(32),
        "PALS_PLUS_COUPONS_ENABLED": "true"
        if selected["enable_plus_coupons"]
        else "false",
        "NEXT_PUBLIC_PALS_API_BASE_URL": api,
        "NEXT_PUBLIC_COGNITO_ENDPOINT": cognito,
        "NEXT_PUBLIC_COGNITO_GOOGLE_ENABLED": "false",
        "NEXT_PUBLIC_COGNITO_HOSTED_UI_DOMAIN": "",
        "NEXT_PUBLIC_COGNITO_REDIRECT_URI": web,
        "NEXT_PUBLIC_COGNITO_LOGOUT_URI": web,
        # These are the existing local Web profile's expected resource identifiers, not a bootstrap result.
        "NEXT_PUBLIC_COGNITO_USER_POOL_ID": pool,
        "NEXT_PUBLIC_COGNITO_CLIENT_ID": app_client,
        "PALS_COGNITO_USER_POOL_ID": pool,
        "PALS_COGNITO_APP_CLIENT_ID": app_client,
        "PALS_COGNITO_ISSUER": f"http://cognito-local:9229/{pool}",
        "PALS_COGNITO_JWKS_URL": f"http://cognito-local:9229/{pool}/.well-known/jwks.json",
        "PALS_LOCAL_COGNITO_EMAIL": f"reviewer-{role}@example.test",
        "PALS_LOCAL_COGNITO_PASSWORD": f"PalsReview-{secrets.token_hex(24)}-7",
    }


@contextmanager
def private_directory(path):
    need(
        path.resolve() == path and path.parent.is_dir(),
        "canonical_local_lane_environment_directory_required",
    )
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        need(
            info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
            "private_local_lane_environment_directory_required",
        )
        need(
            not set(os.listdir(fd)) & set(OUTPUTS),
            "local_lane_environment_already_initialized",
        )
        yield fd
    finally:
        os.close(fd)


def same_file(directory, name, identity):
    try:
        info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return (info.st_dev, info.st_ino) == identity


def publish(document, semantics):
    relay_compose.validate(document)
    roots = {
        role: absolute(selected["runtime_directory"])
        for role, selected in document["lanes"].items()
    }
    opened = {}
    staged = {}
    linked = set()
    receipts = {}
    with ExitStack() as stack:
        for role, path in roots.items():
            opened[role] = stack.enter_context(private_directory(path))
        try:
            for role, directory in opened.items():
                values = lane_values(role, document["lanes"][role], semantics)
                raw = "".join(
                    f"{key}={value}\n" for key, value in sorted(values.items())
                ).encode()
                name = ".local-env-" + secrets.token_hex(16)
                fd = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory,
                )
                with os.fdopen(fd, "wb") as stream:
                    info = os.fstat(stream.fileno())
                    staged[role] = name, (info.st_dev, info.st_ino)
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                receipts[role] = {
                    "path": str(roots[role] / LOCAL_ENV),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            for role, directory in opened.items():
                need(
                    not set(os.listdir(directory)) & set(OUTPUTS[1:]),
                    "local_lane_environment_already_initialized",
                )
                os.link(
                    staged[role][0],
                    LOCAL_ENV,
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                    follow_symlinks=False,
                )
                linked.add(role)
            for role, directory in opened.items():
                os.unlink(staged[role][0], dir_fd=directory)
                os.fsync(directory)
        except BaseException:
            for role in linked:
                if same_file(opened[role], LOCAL_ENV, staged[role][1]):
                    os.unlink(LOCAL_ENV, dir_fd=opened[role])
            raise
        finally:
            for role, (name, identity) in staged.items():
                if same_file(opened[role], name, identity):
                    os.unlink(name, dir_fd=opened[role])
    return {
        "status": "local_environment_inputs_prepared",
        "bootstrap_verified": False,
        "activation_authorized": False,
        "lanes": receipts,
        "required_live_bootstrap": [
            "cognito",
            "verifier_mtls_release_env",
            "recipe_env",
            "database",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--seed-env", required=True)
    parser.add_argument("--seed-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = publish(
            read_document(args.binding, args.binding_sha256),
            settings_from_seed(args.seed_env, args.seed_sha256),
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        RecursionError,
    ) as error:
        code = (
            str(error)
            if re.fullmatch(r"[a-z_]+", str(error))
            else "local_lane_environment_preparation_failed"
        )
        print(json.dumps({"status": "refused", "code": code}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
