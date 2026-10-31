#!/usr/bin/env python3
"""Read source runtime metadata, without credentials, DB rows, or mutations."""
from __future__ import annotations

import configparser
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

PUBLIC_BOOLEANS = frozenset({
    "PALS_LOCAL_RUNTIME_ENABLED", "PALS_GUEST_CHAT_ENABLED",
    "PALS_TOKEN_ACCOUNTING_ENABLED", "UVICORN_PROXY_HEADERS",
    "PALS_TYPED_CATALOG_ENABLED",
})
PUBLIC_TOKENS = frozenset({
    "PALS_PROOF_CAPABILITY", "PALS_DRAFT_EMBEDDING_DIM",
    "PALS_DRAFT_EMBEDDING_MODEL", "PALS_DRAFT_EMBEDDING_PROVIDER",
    "PALS_DRAFT_EMBEDDING_REVISION", "PALS_GUEST_GLOBAL_DAILY_LIMIT",
    "PALS_GUEST_CLIENT_IP_HEADER", "PALS_RECIPE_SEMANTIC_REVIEWER_PRINCIPAL",
    "PALS_RECIPE_ACTIVE_LAKE_MANIFEST_SHA256", "PALS_RECIPE_ACTIVE_LEAN_VERSION",
    "PALS_RECIPE_VERIFIER_SHA256", "PALS_RECIPE_CATALOG_ACTIVE_LAKE_MANIFEST_SHA256",
    "PALS_RECIPE_CATALOG_ACTIVE_LEAN_VERSION", "PALS_RECIPE_CATALOG_ACTIVE_VERIFIER_SHA256",
    "PALS_DRAFT_EMBEDDING_DEPLOYMENT_IDENTITY",
})
PUBLIC_DIGESTS = frozenset({"PALS_PFI_PROVENANCE_SHA256"})
PUBLIC_ENDPOINTS = frozenset({
    "PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY", "PALS_RECIPE_REVIEWER_URL",
})
PUBLIC_ORIGINS = frozenset({"PALS_GUEST_ALLOWED_ORIGINS", "PALS_CORS_ALLOWED_ORIGINS"})


def public_origin(value: object, *, cors: bool) -> bool:
    if not isinstance(value, str) or not 1 <= len(value) <= 253:
        return False
    if value == "*":
        return cors
    try:
        parsed = urlsplit(value)
        return bool(parsed.hostname) and all(ord(char) < 128 for char in value) and (
            parsed.scheme in {"http", "https"} and parsed.username is None and parsed.password is None
            and not parsed.path and not parsed.query and not parsed.fragment
            and re.fullmatch(r"[A-Za-z0-9.:[\]-]+", parsed.netloc) is not None
            and (parsed.port is None or 1 <= parsed.port <= 65535)
        )
    except ValueError:
        return False


def public_endpoint(value: object, *, reviewer: bool) -> bool:
    """Observe public identity only; never URL credentials or query material."""
    if not isinstance(value, str) or not 1 <= len(value) <= 512:
        return False
    try:
        parsed = urlsplit(value)
        if (not parsed.hostname or not value.isascii()
                or any(ord(char) < 33 or ord(char) > 126 for char in value)
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or "?" in value or "#" in value
                or re.fullmatch(r"[A-Za-z0-9.:[\]-]+", parsed.netloc) is None
                or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
            return False
        if reviewer:
            return parsed.path in {"", "/"} and (
                parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {
                    "pals-recipe-reviewer", "recipe-reviewer", "localhost", "127.0.0.1", "::1"}))
        return (parsed.scheme == "https"
                and re.fullmatch(r"[A-Za-z0-9._~/-]*", parsed.path) is not None
                and not any(part.startswith(("sk-", "AKIA", "ASIA"))
                            for part in parsed.path.split("/")))
    except ValueError:
        return False


class PublicConfigurationError(RuntimeError):
    def __init__(self, name: str):
        self.field = name
        super().__init__("Public runtime metadata is invalid")


class InventoryCommandError(RuntimeError):
    def __init__(self, program: str, code: int):
        self.program = program if program in {"aws", "docker"} else "other"
        self.code = code
        super().__init__("Inventory command failed")


def public_runtime_configuration(entries: list[str]) -> dict[str, str]:
    """A closed, validated metadata subset; never credentials or database URLs."""
    values: dict[str, str] = {}
    for entry in entries:
        name, sep, value = entry.partition("=")
        if name not in PUBLIC_BOOLEANS | PUBLIC_TOKENS | PUBLIC_ORIGINS | PUBLIC_DIGESTS | PUBLIC_ENDPOINTS:
            continue
        if not sep or name in values:
            raise RuntimeError("Public runtime metadata is ambiguous")
        if name == "PALS_TYPED_CATALOG_ENABLED":
            # The agent owns this strict opt-in; preserve literal false vs absence.
            valid = value in {"true", "false"}
        elif name in PUBLIC_BOOLEANS:
            valid = value in {"true", "false", "1", "0", "on", "off"}
        elif name in PUBLIC_DIGESTS:
            valid = re.fullmatch(r"[0-9a-f]{64}", value) is not None
        elif name in PUBLIC_ENDPOINTS:
            valid = public_endpoint(value, reviewer=name == "PALS_RECIPE_REVIEWER_URL")
        elif name in PUBLIC_ORIGINS:
            try:
                # Match the owning Settings validators: CORS is comma-separated,
                # while the guest origin setting requires an explicit JSON list.
                origins = ([origin.strip() for origin in value.split(",") if origin.strip()]
                           if name == "PALS_CORS_ALLOWED_ORIGINS" else json.loads(value))
            except (TypeError, ValueError) as error:
                raise PublicConfigurationError(name) from error
            valid = isinstance(origins, list) and 0 < len(origins) <= 32 and all(
                public_origin(origin, cors=name == "PALS_CORS_ALLOWED_ORIGINS") for origin in origins)
        else:
            valid = re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,127}", value) is not None
            valid = valid and not value.startswith(("sk-", "AKIA", "ASIA"))
        if not valid:
            raise PublicConfigurationError(name)
        values[name] = value
    return values


def command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode:
        raise InventoryCommandError(args[0], result.returncode)
    return result.stdout


def shape(value: object) -> object:
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    return type(value).__name__


def path_metadata(value: object) -> object:
    """Retain only named deployment artifact paths, never file/secret contents."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            is_artifact = any(word in key.lower() for word in ("manifest", "signature", "registry", "directory", "state_dir", "controller", "lock"))
            if is_artifact and isinstance(item, str) and item.startswith("/") and "\n" not in item:
                result[key] = item
            else:
                result[key] = path_metadata(item)
        return result
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    return type(value).__name__


def main() -> None:
    if sys.argv[1:] == ["configure-sso"]:
        configure_sso()
        return
    root = pathlib.Path.home() / "pals-mini-deploy"
    config = json.loads((root / "deploy-config.json").read_text())
    report: dict[str, object] = {
        "report_kind": "read_only_inventory_not_backup",
        "deployment_directory": str(root),
        "config_shape": shape(config),
        "deployment_paths": {key: config[key] for key in ("controller", "state_dir", "docker_context") if key in config},
        "database_identity_not_migration_evidence": config.get("database_identity"),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "config":
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return
    report["state_filenames"] = sorted(item.name for item in (root / "state").iterdir())
    report["current_state_metadata"] = path_metadata(json.loads((root / "state" / "current.json").read_text()))
    names = command(["docker", "ps", "--format", "{{.Names}}"]).splitlines()
    names = [name for name in names if name.startswith("pals-") and "geekten" not in name]
    containers = json.loads(command(["docker", "inspect", *names])) if names else []
    public: list[dict[str, object]] = []
    for item in containers:
        cfg = item.get("Config") or {}
        name = item["Name"].lstrip("/")
        entry: dict[str, object] = {
            "name": name,
            "image_id": item["Image"],
            "state": item["State"]["Status"],
            "environment_names": sorted(env.partition("=")[0] for env in cfg.get("Env", [])),
            "public_runtime_configuration": public_runtime_configuration(cfg.get("Env", [])),
            "mounts": [{key: mount.get(key) for key in ("Type", "Source", "Destination", "RW")} for mount in item.get("Mounts", [])],
        }
        if name.endswith("-db"):
            entry["pg_dump_version"] = command(["docker", "exec", name, "pg_dump", "--version"]).strip()
            environment = dict(env.partition("=")[::2] for env in cfg.get("Env", []))
            if name == "pals-mini-prod-webfix-20261004-db" and environment.get("POSTGRES_DB"):
                # The checked-in Mini host controller's query contract explicitly
                # selects postgres/pals. This read-only probe observes that role;
                # it does not infer authority or authorize backup/admission.
                user = environment.get("POSTGRES_USER", "postgres")
                sql = """BEGIN READ ONLY;
SELECT json_build_object(
 'connected_user',current_user,
 'socket_directories',current_setting('unix_socket_directories'),
 'port',current_setting('port'),
 'database', (SELECT json_build_object('name', datname, 'owner',pg_get_userbyid(datdba),'encoding', pg_encoding_to_char(encoding), 'collation', datcollate, 'ctype', datctype, 'provider', datlocprovider,'icu_locale',daticulocale,'recorded_collation_version',datcollversion,'actual_collation_version',pg_database_collation_actual_version(oid)) FROM pg_database WHERE datname=current_database()),
 'roles', (SELECT json_agg(json_build_object('name',rolname,'superuser',rolsuper,'inherit',rolinherit,'createrole',rolcreaterole,'createdb',rolcreatedb,'login',rolcanlogin,'replication',rolreplication,'bypassrls',rolbypassrls) ORDER BY rolname) FROM pg_roles WHERE rolname NOT LIKE 'pg_%'),
 'relation_owners', (SELECT json_agg(json_build_object('owner',owner,'count',n) ORDER BY owner) FROM (SELECT pg_get_userbyid(c.relowner) AS owner,count(*) AS n FROM pg_class c JOIN pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname NOT IN ('pg_catalog','information_schema') AND s.nspname NOT LIKE 'pg_toast%' GROUP BY c.relowner) x),
 'extensions', (SELECT json_agg(json_build_object('name',extname,'version',extversion) ORDER BY extname) FROM pg_extension)
); ROLLBACK;"""
                output = command(["docker", "exec", "--user", "postgres", name, "psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1", "-U", user, "-d", environment["POSTGRES_DB"], "-c", sql])
                entry["database_metadata_not_migration_evidence"] = json.loads(output)
        public.append(entry)
    report["containers"] = public
    if sys.argv[1:] == ["upload-inventory"]:
        upload_inventory(report)
        return
    if len(sys.argv) == 2:
        public = [entry for entry in public if sys.argv[1] in str(entry["name"])]
        report = {"containers": public}
    print(json.dumps(report, indent=2, ensure_ascii=True))


def configure_sso() -> None:
    """Append public SSO metadata only; never replace an existing section."""
    root = pathlib.Path.home() / ".aws"
    if root.is_symlink():
        raise RuntimeError("AWS config directory is a symlink")
    root.mkdir(mode=0o700, exist_ok=True)
    path = root / "config"
    expected = {
        "profile pals-migration-operator": {
            "sso_session": "pals-migration", "sso_account_id": "828786775577",
            "sso_role_name": "AdministratorAccess", "region": "ap-northeast-1", "output": "json",
        },
        "sso-session pals-migration": {
            "sso_start_url": "https://ssoins-72235ad8d20425ad.us-east-1.portal.amazonaws.com/",
            "sso_region": "us-east-1", "sso_registration_scopes": "sso:account:access",
        },
    }
    descriptor = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "a+", encoding="utf-8") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_nlink != 1 or metadata.st_mode & 0o077:
            raise RuntimeError("Unsafe AWS config file")
        stream.seek(0)
        parser = configparser.ConfigParser()
        parser.read_string(stream.read())
        missing = []
        for section, values in expected.items():
            if parser.has_section(section):
                if dict(parser[section]) != values:
                    raise RuntimeError("Existing SSO configuration differs; no overwrite")
            else:
                missing.append((section, values))
        for section, values in missing:
            stream.write("\n[" + section + "]\n" + "".join(key + " = " + value + "\n" for key, value in values.items()))
        stream.flush()
        os.fsync(stream.fileno())
    print("SSO metadata prepared. Run aws sso login --profile pals-migration-operator --use-device-code --no-browser")


def upload_inventory(report: dict[str, object]) -> None:
    prefix = ["aws", "--profile", "pals-migration-operator", "--region", "ap-northeast-1"]
    if json.loads(command(prefix + ["sts", "get-caller-identity"]))["Account"] != "828786775577":
        raise RuntimeError("Wrong AWS account")
    root = pathlib.Path.home() / "pals-mini-deploy" / "aws-migration-20261030"
    root.mkdir(mode=0o700, exist_ok=True)
    if root.is_symlink() or root.stat().st_mode & 0o077:
        raise RuntimeError("Unsafe inventory directory")
    data = (json.dumps(report, indent=2, ensure_ascii=True) + "\n").encode()
    digest = hashlib.sha256(data).hexdigest()
    path = root / ("inventory-" + digest + ".json")
    with path.open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(data)
    key = "aws-migration-20261030/source-inventory/" + path.name
    command(prefix + ["s3api", "put-object", "--bucket", "pals-mini-prod-backups-828786775577", "--expected-bucket-owner", "828786775577", "--key", key, "--body", str(path), "--server-side-encryption", "AES256"])
    print("Inventory uploaded to existing private backup bucket.")
    print("Key: " + key)
    print("SHA256: " + digest)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        result = {"status": "source_inventory_failed", "code": "read_only_inventory_failed"}
        if isinstance(error, PublicConfigurationError):
            result.update(code="public_configuration_invalid", field=error.field)
        elif isinstance(error, InventoryCommandError):
            result.update(code="inventory_command_failed", program=error.program, exit_code=error.code)
        print(json.dumps(result, sort_keys=True), file=sys.stderr)
        sys.exit(1)
