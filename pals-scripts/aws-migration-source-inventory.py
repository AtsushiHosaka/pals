#!/usr/bin/env python3
"""Read source runtime metadata, without credentials, DB rows, or mutations."""
from __future__ import annotations

import json
import configparser
import hashlib
import os
import pathlib
import stat
import subprocess
import sys


def command(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode:
        raise RuntimeError(f"command failed: {args[0]} (exit {result.returncode})")
    return result.stdout


def shape(value: object) -> object:
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    return type(value).__name__


def main() -> None:
    if sys.argv[1:] == ["configure-sso"]:
        configure_sso()
        return
    root = pathlib.Path.home() / "pals-mini-deploy"
    report: dict[str, object] = {
        "report_kind": "read_only_inventory_not_backup",
        "deployment_directory": str(root),
        "config_shape": shape(json.loads((root / "deploy-config.json").read_text())),
    }
    if len(sys.argv) == 2 and sys.argv[1] == "config":
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return
    report["state_filenames"] = sorted(item.name for item in (root / "state").iterdir())
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
            "mounts": [{key: mount.get(key) for key in ("Type", "Source", "Destination", "RW")} for mount in item.get("Mounts", [])],
        }
        if name.endswith("-db"):
            entry["pg_dump_version"] = command(["docker", "exec", name, "pg_dump", "--version"]).strip()
            environment = dict(env.partition("=")[::2] for env in cfg.get("Env", []))
            if environment.get("POSTGRES_USER") and environment.get("POSTGRES_DB"):
                sql = """BEGIN READ ONLY;
SELECT json_build_object(
 'database', (SELECT json_build_object('name', datname, 'encoding', pg_encoding_to_char(encoding), 'collation', datcollate, 'ctype', datctype, 'provider', datlocprovider) FROM pg_database WHERE datname=current_database()),
 'roles', (SELECT json_agg(json_build_object('name',rolname,'superuser',rolsuper,'inherit',rolinherit,'createrole',rolcreaterole,'createdb',rolcreatedb,'login',rolcanlogin,'replication',rolreplication,'bypassrls',rolbypassrls) ORDER BY rolname) FROM pg_roles WHERE rolname NOT LIKE 'pg_%'),
 'relation_owners', (SELECT json_agg(json_build_object('owner',owner,'count',n) ORDER BY owner) FROM (SELECT pg_get_userbyid(c.relowner) AS owner,count(*) AS n FROM pg_class c JOIN pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname NOT IN ('pg_catalog','information_schema') AND s.nspname NOT LIKE 'pg_toast%' GROUP BY c.relowner) x),
 'extensions', (SELECT json_agg(json_build_object('name',extname,'version',extversion) ORDER BY extname) FROM pg_extension)
); ROLLBACK;"""
                output = command(["docker", "exec", "--user", "postgres", name, "psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1", "-U", environment["POSTGRES_USER"], "-d", environment["POSTGRES_DB"], "-c", sql])
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
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        print("Source inventory failed; no credential values or command stderr were emitted.", file=sys.stderr)
        sys.exit(1)
