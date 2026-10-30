#!/usr/bin/env python3
"""Live, consistent PG16 rehearsal export. Never final capture/admission evidence.

Only stdlib, Docker's existing PostgreSQL tools, and the existing AWS CLI/profile
are used. No source writes, drain, service control, bootstrap, or credential copy.
All command stderr and payload stdout remain private; console output is status only.
Failures report only closed static phase/category/known-guard labels, never arbitrary exception contents.

Private config schema pals.live-rehearsal.config.v1 requires explicit database_name,
database_user, postgres_socket_directory, postgres_port, existing deployment_lock_file,
new output_directory under ~/pals-mini-deploy/aws-migration-20261030/rehearsal/, and
referenced_files with admission_manifest/admission_signature/historical_registry,
expected_database_identity, and exact runtime_containers actor names. Public
reference bytes are copied only after carrier/registry/DER shape and hash binding;
the selected manifest hash must match the same-snapshot latest admission. KMS
signature verification remains an independent root step; trust is not asserted.
Use --prepare-from-controller-policy ABSOLUTE_CONTROLLER_POLICY for a one-command
protected config preparation and export using named policy references, current.json,
the existing host-update.lock and the policy's exact Docker context/actor names.
Each child command is bounded to at most 240 seconds; files are limited to 5 GiB.
Partial protected exports/uploads may remain after failure without a final remote
manifest marker. This helper cannot generate final signed source evidence.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any
from uuid import uuid4

ACCOUNT = "828786775577"
REGION = "ap-northeast-1"
PROFILE = "pals-migration-operator"
BUCKET = "pals-mini-prod-backups-828786775577"
PREFIX = "aws-migration-20261030/rehearsal/"
CONTAINER = "pals-mini-prod-webfix-20261004-db"
MAX_FILE = 5 * 1024**3
MAX_METADATA = 4 * 1024**2
_HEX = re.compile(r"[0-9a-f]{64}")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}")
_LOCK_FD: int | None = None
_PHASE = "initialization"
_PHASES = frozenset(
    {
        "initialization",
        "deployment_root",
        "controller_policy_read",
        "controller_state_select",
        "controller_state_read",
        "controller_identity_check",
        "controller_reference_select",
        "controller_config_build",
        "controller_config_validate",
        "controller_lock_check",
        "config_output_parent_check",
        "config_output_write",
        "config_load",
        "source_lock",
        "controller_binding_check",
        "private_bucket_check",
        "bucket_ambient_override",
        "aws_identity",
        "bucket_head",
        "bucket_public_access",
        "bucket_acl",
        "reference_open",
        "reference_document_check",
        "source_container_inspect",
        "runtime_image_inventory",
        "source_tool_inventory",
        "source_tool_version",
        "export_directory_create",
        "snapshot_open",
        "snapshot_identity",
        "snapshot_metadata",
        "custom_dump",
        "schema_dump",
        "snapshot_close",
        "provider_library_observation",
        "tool_hash_observation",
        "runtime_recheck",
        "reference_recheck",
        "reference_copy",
        "metadata_write",
        "manifest_prepare",
        "artifact_upload",
        "manifest_upload",
    }
)
_PUBLIC_GUARDS = {
    "ambient_aws_endpoint_or_ca_override": "ambient_aws_endpoint_or_ca_override",
    "wrong_aws_account": "wrong_aws_account",
    "bucket_public_access_not_blocked": "bucket_public_access_not_blocked",
    "bucket_acl_not_owner_private": "bucket_acl_not_owner_private",
    "command_failed_or_output_unbounded": "command_failed_or_output_unbounded",
}
REFERENCE_ARTIFACTS = {
    "admission_manifest": "admission-manifest.jcs",
    "admission_signature": "admission-signature.der",
    "historical_registry": "production-registry.json",
}


class RehearsalError(RuntimeError):
    pass


def mark_phase(value: str) -> None:
    global _PHASE
    if value not in _PHASES:
        raise ValueError("invalid_static_phase")
    _PHASE = value


def failure_diagnostic(error: Exception) -> str:
    """Closed labels only: never format an exception, path, key or class name."""
    category = "unexpected_failure"
    for kind, label in (
        (RehearsalError, "guard_rejected"),
        (FileNotFoundError, "missing_path"),
        (FileExistsError, "existing_path"),
        (PermissionError, "permission_denied"),
        (BlockingIOError, "lock_or_io_busy"),
        (NotADirectoryError, "not_a_directory"),
        (IsADirectoryError, "not_a_file"),
        (BrokenPipeError, "broken_pipe"),
        (json.JSONDecodeError, "invalid_json"),
        (UnicodeError, "invalid_text_encoding"),
        (KeyError, "required_member_missing"),
        (IndexError, "invalid_sequence"),
        (AttributeError, "unexpected_attribute"),
        (TypeError, "unexpected_type"),
        (OverflowError, "numeric_overflow"),
        (subprocess.TimeoutExpired, "command_timeout"),
        (subprocess.SubprocessError, "command_failure"),
        (OSError, "operating_system_failure"),
        (ValueError, "invalid_value"),
        (RuntimeError, "runtime_failure"),
    ):
        if isinstance(error, kind):
            category = label
            break
    phase = _PHASE if _PHASE in _PHASES else "initialization"
    guard = ""
    if (
        type(error) is RehearsalError
        and len(error.args) == 1
        and type(error.args[0]) is str
        and error.args[0] in _PUBLIC_GUARDS
    ):
        guard = "; guard=" + _PUBLIC_GUARDS[error.args[0]]
    return f"Rehearsal export failed (phase={phase}; category={category}{guard}); no payload or credential values were emitted."


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in items:
        if name in result:
            raise RehearsalError("duplicate_config_member")
        result[name] = value
    return result


def trusted_file(path: Path, *, maximum: int | None = None) -> int:
    if not path.is_absolute() or path.parent.resolve(strict=True) != path.parent:
        raise RehearsalError("unsafe_input_path")
    for parent in (path.parent, *path.parent.parents):
        info = parent.stat()
        if info.st_uid not in {0, os.geteuid()} or (
            info.st_mode & 0o022
            and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)
        ):
            raise RehearsalError("unsafe_input_parent")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid not in {0, os.geteuid()}
        or info.st_nlink != 1
        or info.st_mode & 0o022
        or maximum is not None
        and info.st_size > maximum
    ):
        os.close(fd)
        raise RehearsalError("unsafe_input_file")
    return fd


def file_hash(fd: int) -> dict[str, Any]:
    os.lseek(fd, 0, os.SEEK_SET)
    hashed, size = hashlib.sha256(), 0
    while chunk := os.read(fd, 1024 * 1024):
        size += len(chunk)
        hashed.update(chunk)
    os.lseek(fd, 0, os.SEEK_SET)
    return {"sha256": hashed.hexdigest(), "size_bytes": size}


def same_inode(path: Path, fd: int) -> bool:
    try:
        if path.parent.resolve(strict=True) != path.parent:
            return False
        entry, opened = path.lstat(), os.fstat(fd)
        return (entry.st_dev, entry.st_ino) == (opened.st_dev, opened.st_ino) and (
            stat.S_ISREG(entry.st_mode)
            and entry.st_nlink == 1
            and entry.st_uid in {0, os.geteuid()}
            and not entry.st_mode & 0o022
        )
    except OSError:
        return False


@contextmanager
def existing_lock(path: Path) -> Iterator[Any]:
    global _LOCK_FD
    fd = trusted_file(path)
    previous = _LOCK_FD
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        def verify() -> None:
            if path.parent.resolve(strict=True) != path.parent or not same_inode(
                path, fd
            ):
                raise RehearsalError("deployment_lock_changed")

        verify()
        _LOCK_FD = fd
        yield verify
        verify()
    finally:
        _LOCK_FD = previous
        os.close(fd)


def inherited_fds(extra: tuple[int, ...] = ()) -> tuple[int, ...]:
    return tuple(sorted(set(extra + ((_LOCK_FD,) if _LOCK_FD is not None else ()))))


class Output:
    """Retain directory/file descriptors; paths are never reopened for upload."""

    def __init__(self, path: Path, root: Path):
        self.path, self.files = path, {}
        expected = root / "aws-migration-20261030" / "rehearsal"
        if not path.is_absolute() or path.parent != expected:
            raise RehearsalError("output_must_be_new_rehearsal_child")
        if (
            path.name in {"", ".", ".."}
            or re.fullmatch(r"[A-Za-z0-9-]{1,80}", path.name) is None
        ):
            raise RehearsalError("invalid_output_name")
        current = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for index, part in enumerate(
                ("aws-migration-20261030", "rehearsal", path.name)
            ):
                try:
                    os.mkdir(part, 0o700, dir_fd=current)
                except FileExistsError:
                    if index == 2:
                        raise RehearsalError("output_already_exists") from None
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current
                )
                info = os.fstat(child)
                if info.st_uid != os.geteuid() or info.st_mode & 0o077:
                    os.close(child)
                    raise RehearsalError("output_directory_not_private")
                os.close(current)
                current = child
            self.fd = current
            current = -1
        finally:
            if current >= 0:
                os.close(current)

    def create(self, name: str, data: bytes | None = None) -> int:
        if name not in {
            "source.dump",
            "schema.sql",
            "metadata.json",
            "manifest.json",
            *REFERENCE_ARTIFACTS.values(),
        }:
            raise RehearsalError("invalid_output_artifact")
        fd = os.open(
            name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=self.fd,
        )
        self.files[name] = fd
        if data is not None:
            remaining = memoryview(data)
            while remaining:
                remaining = remaining[os.write(fd, remaining) :]
            os.fsync(fd)
        return fd

    def verify(self) -> None:
        if self.path.parent.resolve(strict=True) != self.path.parent:
            raise RehearsalError("output_parent_changed")
        current = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            a, b = os.fstat(current), os.fstat(self.fd)
            if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino) or a.st_mode & 0o077:
                raise RehearsalError("output_directory_changed")
        finally:
            os.close(current)
        for name, fd in self.files.items():
            if not same_inode(self.path / name, fd) or os.fstat(fd).st_mode & 0o077:
                raise RehearsalError("output_artifact_changed")

    def close(self) -> None:
        for fd in self.files.values():
            os.close(fd)
        os.close(self.fd)


def command(
    args: list[str],
    *,
    maximum: int = MAX_METADATA,
    timeout: int = 30,
    pass_fds: tuple[int, ...] = (),
) -> bytes:
    # Small provider/metadata commands only; dump output always streams to an FD.
    with (
        tempfile.TemporaryFile() as spool,
        subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=spool,
            stderr=subprocess.DEVNULL,
            pass_fds=inherited_fds(pass_fds),
            start_new_session=True,
        ) as process,
    ):
        try:
            deadline = time.monotonic() + timeout
            while process.poll() is None and time.monotonic() < deadline:
                if os.fstat(spool.fileno()).st_size > maximum:
                    raise RehearsalError("command_output_unbounded")
                try:
                    process.wait(timeout=0.25)
                except subprocess.TimeoutExpired:
                    pass
            if (
                process.poll() is None
                or process.returncode
                or os.fstat(spool.fileno()).st_size > maximum
            ):
                raise RehearsalError("command_failed_or_output_unbounded")
            spool.seek(0)
            return spool.read(maximum + 1)
        finally:
            if process.poll() is None:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)


def inspect_source(
    database_name: str, database_user: str, docker_prefix: list[str] | None = None
) -> dict[str, Any]:
    if any(
        re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", value) is None
        for value in (database_name, database_user)
    ):
        raise RehearsalError("explicit_database_and_user_required")
    prefix = docker_prefix or ["docker"]
    values = json.loads(command([*prefix, "inspect", CONTAINER]))
    if not isinstance(values, list) or len(values) != 1:
        raise RehearsalError("source_container_not_unique")
    item = values[0]
    state = item.get("State", {})
    if (
        item.get("Name") != "/" + CONTAINER
        or state.get("Running") is not True
        or state.get("Restarting")
        or state.get("Paused")
        or state.get("Dead")
        or not _HEX.fullmatch(item.get("Id", ""))
        or not _IMAGE.fullmatch(item.get("Image", ""))
    ):
        raise RehearsalError("source_container_identity_or_state_differs")
    environment: dict[str, str] = {}
    for entry in item.get("Config", {}).get("Env", []):
        key, separator, value = entry.partition("=")
        if key in {"POSTGRES_DB", "POSTGRES_USER", "PATH"}:
            if (
                not separator
                or key in environment
                or not value
                or any(ord(c) < 32 for c in value)
            ):
                raise RehearsalError("ambiguous_source_environment")
            environment[key] = value
    if not {"POSTGRES_DB", "PATH"} <= set(environment):
        raise RehearsalError("explicit_postgres_environment_required")
    if any(
        re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", environment[key]) is None
        for key in ("POSTGRES_DB", "POSTGRES_USER")
        if key in environment
    ):
        raise RehearsalError("source_database_or_user_is_not_an_identifier")
    if (
        environment["POSTGRES_DB"] != database_name
        or environment.get("POSTGRES_USER", database_user) != database_user
    ):
        raise RehearsalError("source_environment_differs_from_explicit_selection")
    labels = item.get("Config", {}).get("Labels") or {}
    project = labels.get("com.docker.compose.project")
    service = labels.get("com.docker.compose.service")
    return {
        "id": item["Id"],
        "image_id": item["Image"],
        "project": project,
        "service": service,
        "database": database_name,
        "user": database_user,
        "path": environment["PATH"],
        "_docker": prefix,
    }


def runtime_images(source: dict[str, Any]) -> list[dict[str, Any]]:
    actors = source.get("_runtime_containers")
    if not isinstance(actors, dict) or not actors or len(actors) > 32:
        raise RehearsalError("explicit_runtime_actor_names_required")
    names = sorted(actors.values())
    if len(set(names)) != len(names) or names.count(CONTAINER) != 1:
        raise RehearsalError("runtime_actor_names_ambiguous")
    items = json.loads(command([*source.get("_docker", ["docker"]), "inspect", *names]))
    if (
        not isinstance(items, list)
        or len(items) != len(names)
        or {item.get("Name", "").lstrip("/") for item in items} != set(names)
    ):
        raise RehearsalError("runtime_actor_inventory_differs")
    roles = {name: role for role, name in actors.items()}
    result = []
    for item in items:
        name = item["Name"].lstrip("/")
        if not _HEX.fullmatch(item.get("Id", "")) or not _IMAGE.fullmatch(
            item.get("Image", "")
        ):
            raise RehearsalError("runtime_actor_identity_invalid")
        labels = item.get("Config", {}).get("Labels") or {}
        result.append(
            {
                "id": item["Id"],
                "name": name,
                "role": roles[name],
                "image_id": item["Image"],
                "image_reference": item.get("Config", {}).get("Image"),
                "state": item.get("State", {}).get("Status"),
                "running": item.get("State", {}).get("Running"),
                "compose_project": labels.get("com.docker.compose.project"),
                "service": labels.get("com.docker.compose.service"),
            }
        )
    if (
        len(
            [
                item
                for item in result
                if item["id"] == source["id"] and item["name"] == CONTAINER
            ]
        )
        != 1
    ):
        raise RehearsalError("source_database_missing_from_runtime")
    image_ids = sorted({item["image_id"] for item in result})
    inspected = json.loads(
        command([*source.get("_docker", ["docker"]), "image", "inspect", *image_ids])
    )
    by_id = {item["Id"]: item for item in inspected}
    if set(by_id) != set(image_ids) or len(inspected) != len(image_ids):
        raise RehearsalError("runtime_image_inventory_differs")
    for item in result:
        digests = by_id[item["image_id"]].get("RepoDigests") or []
        if not isinstance(digests, list) or any(
            not isinstance(value, str)
            or re.fullmatch(r"[A-Za-z0-9./:_-]+@sha256:[0-9a-f]{64}", value) is None
            for value in digests
        ):
            raise RehearsalError("runtime_registry_digest_invalid")
        item["repo_digests"] = sorted(digests)
        item["registry_digest_status"] = "observed" if digests else "absent_local_image"
    return sorted(result, key=lambda item: item["name"])


def container_tools(source: dict[str, Any]) -> dict[str, str]:
    paths = (
        command(
            [
                *source.get("_docker", ["docker"]),
                "exec",
                "--user",
                "postgres",
                source["id"],
                "/bin/sh",
                "-c",
                "command -v env; command -v psql; command -v pg_dump; command -v sha256sum",
            ]
        )
        .decode()
        .splitlines()
    )
    if len(paths) != 4 or any(
        not item.startswith("/") or any(c.isspace() for c in item) for item in paths
    ):
        raise RehearsalError("required_source_tools_unavailable")
    names = ("env", "psql", "pg_dump", "sha256sum")
    return {names[index]: paths[index] for index in range(4)}


def docker_command(
    source: dict[str, Any],
    tools: dict[str, str],
    config: dict[str, Any],
    executable: str,
    *,
    interactive: bool = False,
) -> list[str]:
    return [
        *source.get("_docker", ["docker"]),
        "exec",
        *(["-i"] if interactive else []),
        "--user",
        "postgres",
        source["id"],
        tools["env"],
        "-i",
        "PATH=" + source["path"],
        "LC_ALL=C",
        "PGCONNECT_TIMEOUT=5",
        "PGAPPNAME=pals-live-rehearsal",
        tools[executable],
        "--no-password",
        "--host=" + config["postgres_socket_directory"],
        "--port=" + str(config["postgres_port"]),
        "--username=" + source["user"],
        "--dbname=" + source["database"],
    ]


class Snapshot:
    def __init__(self, args: list[str]):
        self.process = subprocess.Popen(
            args + ["-X", "-qAt", "-v", "ON_ERROR_STOP=1"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            pass_fds=inherited_fds(),
        )
        self.buffer = b""
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def query(self, sql: str) -> bytes:
        marker = ("rehearsal-" + uuid4().hex).encode()
        self.process.stdin.write(sql.encode() + b"\n\\echo " + marker + b"\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + 180
        result = []
        size = 0
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                if line == marker:
                    return b"\n".join(result)
                if line:
                    result.append(line)
                size += len(line)
                if size > MAX_METADATA:
                    raise RehearsalError("snapshot_metadata_unbounded")
            if self.selector.select(min(1, max(0, deadline - time.monotonic()))):
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RehearsalError("snapshot_session_ended")
                self.buffer += chunk
                if size + len(self.buffer) > MAX_METADATA:
                    raise RehearsalError("snapshot_metadata_unbounded")
        raise RehearsalError("snapshot_session_timeout")

    def close(self) -> None:
        with suppress(OSError, BrokenPipeError):
            self.process.stdin.write(b"ROLLBACK;\n\\q\n")
            self.process.stdin.flush()
        with suppress(OSError):
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=5)
        self.selector.close()
        self.process.stdout.close()


START = """BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='120s'; SET LOCAL idle_in_transaction_session_timeout='300s';
SET LOCAL timezone='UTC'; SET LOCAL DateStyle='ISO,YMD'; SET LOCAL extra_float_digits=3;
SET LOCAL bytea_output='hex'; SET LOCAL search_path=pg_catalog,public;
SELECT json_build_object('snapshot',pg_export_snapshot(),'database',current_database(),
'user',current_user,'session_user',session_user,'version_num',current_setting('server_version_num'),
'transaction_isolation',current_setting('transaction_isolation'),'transaction_read_only',current_setting('transaction_read_only'),
'server_port',current_setting('port'),'unix_socket_directories',current_setting('unix_socket_directories'),'unix_socket_connection',inet_server_addr() IS NULL,
'system_identifier',(SELECT system_identifier::text FROM pg_control_system()));"""

METADATA = """SELECT json_build_object(
'database',(SELECT json_build_object('name',datname,'owner',pg_get_userbyid(datdba),
'encoding',pg_encoding_to_char(encoding),'collation',datcollate,'ctype',datctype,
'provider',datlocprovider,'icu_locale',daticulocale,'recorded_collation_version',datcollversion,
'actual_collation_version',pg_database_collation_actual_version(oid),'acl',datacl::text)
FROM pg_database WHERE datname=current_database()),
'postgresql_build',version(),
'icu_actual_versions',(SELECT json_agg(DISTINCT pg_collation_actual_version(oid)) FROM pg_collation WHERE collprovider='i'),
'roles',(SELECT json_agg(json_build_array(rolname,rolsuper,rolinherit,rolcreaterole,rolcreatedb,
rolcanlogin,rolreplication,rolconnlimit,rolvaliduntil::text,rolbypassrls) ORDER BY rolname)
FROM pg_roles WHERE rolname !~ '^pg_'),
'memberships',(SELECT json_agg(json_build_array(pg_get_userbyid(roleid),pg_get_userbyid(member),
pg_get_userbyid(grantor),admin_option,inherit_option,set_option) ORDER BY roleid,member,grantor) FROM pg_auth_members),
'schemas',(SELECT json_agg(json_build_array(nspname,pg_get_userbyid(nspowner),nspacl::text) ORDER BY nspname) FROM pg_namespace WHERE nspname !~ '^pg_' AND nspname<>'information_schema'),
'relations',(SELECT json_agg(json_build_array(n.nspname,c.relname,c.relkind,pg_get_userbyid(c.relowner),c.relacl::text) ORDER BY n.nspname,c.relname) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'),
'column_acls',(SELECT json_agg(json_build_array(n.nspname,c.relname,a.attname,a.attacl::text) ORDER BY n.nspname,c.relname,a.attnum) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema' AND a.attacl IS NOT NULL),
'routines',(SELECT json_agg(json_build_array(n.nspname,p.proname,pg_get_function_identity_arguments(p.oid),p.prokind,pg_get_userbyid(p.proowner),p.proacl::text,p.prosecdef) ORDER BY n.nspname,p.proname,p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'),
'types',(SELECT json_agg(json_build_array(n.nspname,t.typname,t.typtype,pg_get_userbyid(t.typowner),t.typacl::text) ORDER BY n.nspname,t.typname) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname !~ '^pg_' AND n.nspname<>'information_schema'),
'default_acls',(SELECT json_agg(json_build_array(pg_get_userbyid(defaclrole),coalesce(n.nspname,''),defaclobjtype,defaclacl::text) ORDER BY defaclrole,defaclnamespace,defaclobjtype) FROM pg_default_acl a LEFT JOIN pg_namespace n ON n.oid=a.defaclnamespace),
'extensions',(SELECT json_agg(json_build_array(extname,extversion,n.nspname) ORDER BY extname) FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace),
'latest_admission',(SELECT to_jsonb(a)-'admitted_at' FROM public.proof_runtime_release_admissions a WHERE environment='prod' ORDER BY release_sequence DESC LIMIT 1),
'trust_fence',(SELECT to_jsonb(f)-'fence_committed_at' FROM public.proof_runtime_trust_fence f WHERE environment='prod'));
"""


def dump(args: list[str], fd: int) -> None:
    process = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=fd,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        pass_fds=inherited_fds(),
    )
    try:
        deadline = time.monotonic() + 240
        while process.poll() is None and time.monotonic() < deadline:
            if os.fstat(fd).st_size > MAX_FILE:
                raise RehearsalError("dump_exceeds_single_upload_limit")
            try:
                process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
        if process.poll() is None:
            raise RehearsalError("dump_timeout")
        if process.returncode or not 0 < os.fstat(fd).st_size <= MAX_FILE:
            raise RehearsalError("dump_failed")
        os.fsync(fd)
    finally:
        if process.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)


def aws(
    service: str, *arguments: str, pass_fds: tuple[int, ...] = ()
) -> dict[str, Any]:
    endpoint = (
        f"https://{'s3' if service == 's3api' else service}.{REGION}.amazonaws.com"
    )
    result = command(
        [
            "aws",
            "--profile",
            PROFILE,
            "--region",
            REGION,
            "--endpoint-url",
            endpoint,
            service,
            *arguments,
        ],
        timeout=240,
        pass_fds=pass_fds,
    )
    return json.loads(result or b"{}")


def require_private_bucket() -> None:
    mark_phase("bucket_ambient_override")
    if any(
        name.startswith("AWS_ENDPOINT_URL")
        or name in {"AWS_CA_BUNDLE", "REQUESTS_CA_BUNDLE"}
        for name in os.environ
    ):
        raise RehearsalError("ambient_aws_endpoint_or_ca_override")
    mark_phase("aws_identity")
    if aws("sts", "get-caller-identity").get("Account") != ACCOUNT:
        raise RehearsalError("wrong_aws_account")
    base = ("--bucket", BUCKET, "--expected-bucket-owner", ACCOUNT)
    mark_phase("bucket_head")
    aws("s3api", "head-bucket", *base)
    mark_phase("bucket_public_access")
    block = aws("s3api", "get-public-access-block", *base).get(
        "PublicAccessBlockConfiguration", {}
    )
    if any(
        block.get(key) is not True
        for key in (
            "BlockPublicAcls",
            "IgnorePublicAcls",
            "BlockPublicPolicy",
            "RestrictPublicBuckets",
        )
    ):
        raise RehearsalError("bucket_public_access_not_blocked")
    mark_phase("bucket_acl")
    acl = aws("s3api", "get-bucket-acl", *base)
    owner = acl.get("Owner", {}).get("ID")
    if (
        not owner
        or not acl.get("Grants")
        or any(
            grant.get("Grantee", {}).get("Type") != "CanonicalUser"
            or grant["Grantee"].get("ID") != owner
            for grant in acl["Grants"]
        )
    ):
        raise RehearsalError("bucket_acl_not_owner_private")


def upload(output: Output, name: str, key: str, details: dict[str, Any]) -> None:
    fd = output.files[name]
    os.lseek(fd, 0, os.SEEK_SET)
    checksum = base64.b64encode(bytes.fromhex(details["sha256"])).decode()
    base = ("--bucket", BUCKET, "--expected-bucket-owner", ACCOUNT, "--key", key)
    aws(
        "s3api",
        "put-object",
        *base,
        "--body",
        f"/dev/fd/{fd}",
        "--if-none-match",
        "*",
        "--server-side-encryption",
        "AES256",
        "--checksum-algorithm",
        "SHA256",
        "--checksum-sha256",
        checksum,
        "--metadata",
        "purpose=live-rehearsal-not-admission,sha256=" + details["sha256"],
        pass_fds=(fd,),
    )
    observed = aws("s3api", "head-object", *base, "--checksum-mode", "ENABLED")
    if (
        observed.get("ContentLength") != details["size_bytes"]
        or observed.get("ServerSideEncryption") != "AES256"
        or observed.get("ChecksumSHA256") != checksum
        or observed.get("Metadata", {}).get("sha256") != details["sha256"]
    ):
        raise RehearsalError("uploaded_object_does_not_match")


def load_config(path: Path, root: Path) -> dict[str, Any]:
    fd = trusted_file(path, maximum=65536)
    try:
        if os.fstat(fd).st_mode & 0o077:
            raise RehearsalError("config_not_private")
        value = json.loads(os.read(fd, 65537), object_pairs_hook=_pairs)
    finally:
        os.close(fd)
    return validate_config(value, root)


def validate_config(value: Any, root: Path) -> dict[str, Any]:
    if (
        not isinstance(value, dict)
        or set(value) - {"controller_binding", "docker_prefix"}
        != {
            "schema_version",
            "output_directory",
            "deployment_lock_file",
            "postgres_socket_directory",
            "postgres_port",
            "database_name",
            "database_user",
            "referenced_files",
            "expected_database_identity",
            "runtime_containers",
        }
        or value["schema_version"] != "pals.live-rehearsal.config.v1"
    ):
        raise RehearsalError("config_shape_differs")
    if not isinstance(value["referenced_files"], dict) or set(
        value["referenced_files"]
    ) != {"admission_manifest", "admission_signature", "historical_registry"}:
        raise RehearsalError("reference_paths_required")
    for name in ("deployment_lock_file",):
        checked_path(value[name], root)
    for entry in value["referenced_files"].values():
        checked_path(entry, root)
    socket = value["postgres_socket_directory"]
    if (
        not isinstance(socket, str)
        or not socket.startswith("/")
        or any(c.isspace() for c in socket)
        or "\x00" in socket
    ):
        raise RehearsalError("explicit_socket_directory_required")
    if (
        type(value["postgres_port"]) is not int
        or not 1 <= value["postgres_port"] <= 65535
    ):
        raise RehearsalError("explicit_postgres_port_required")
    if any(
        not isinstance(value[key], str)
        or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", value[key]) is None
        for key in ("database_name", "database_user")
    ):
        raise RehearsalError("explicit_database_and_user_required")
    identity = value["expected_database_identity"]
    if (
        not isinstance(identity, dict)
        or set(identity)
        != {"database_system_identifier", "database_name", "postgresql_major"}
        or identity["database_name"] != value["database_name"]
        or identity["postgresql_major"] != 16
        or not isinstance(identity["database_system_identifier"], str)
        or re.fullmatch(r"[1-9][0-9]{0,19}", identity["database_system_identifier"])
        is None
    ):
        raise RehearsalError("expected_database_identity_required")
    if "docker_prefix" in value:
        prefix = value["docker_prefix"]
        if (
            not isinstance(prefix, list)
            or len(prefix) != 5
            or prefix[1] != "--config"
            or prefix[3] != "--context"
            or not all(
                isinstance(x, str) and x and not any(ord(c) < 32 for c in x)
                for x in prefix
            )
            or not Path(prefix[0]).is_absolute()
            or not Path(prefix[2]).is_absolute()
            or re.fullmatch(r"[A-Za-z0-9._-]{1,80}", prefix[4]) is None
        ):
            raise RehearsalError("invalid_policy_docker_prefix")
    actors = value["runtime_containers"]
    if (
        not isinstance(actors, dict)
        or not 1 <= len(actors) <= 32
        or not all(isinstance(name, str) for name in actors.values())
        or len(set(actors.values())) != len(actors)
        or list(actors.values()).count(CONTAINER) != 1
        or any(
            not isinstance(role, str)
            or re.fullmatch(r"pals[A-Za-z0-9._-]{1,120}", name) is None
            or "geekten" in name
            for role, name in actors.items()
        )
    ):
        raise RehearsalError("explicit_runtime_actor_names_required")
    return value


def checked_path(value: object, root: Path) -> Path:
    if not isinstance(value, str):
        raise RehearsalError("explicit_reference_path_required")
    path = Path(value)
    if (
        not path.is_absolute()
        or root not in path.parents
        or path.parent.resolve(strict=True) != path.parent
    ):
        raise RehearsalError("reference_outside_deployment")
    return path


def private_json(path: Path) -> tuple[dict[str, Any], str]:
    fd = trusted_file(path, maximum=1024**2)
    try:
        if os.fstat(fd).st_mode & 0o077:
            raise RehearsalError("policy_or_state_not_private")
        details = file_hash(fd)
        value = json.loads(os.read(fd, 1024**2 + 1), object_pairs_hook=_pairs)
        if not isinstance(value, dict):
            raise RehearsalError("policy_or_state_not_object")
        return value, details["sha256"]
    finally:
        os.close(fd)


def prepare_from_policy(path: Path, root: Path) -> Path:
    mark_phase("controller_policy_read")
    if path != root / "controller-policy.json":
        raise RehearsalError("explicit_controller_policy_path_differs")
    policy, policy_sha = private_json(path)
    mark_phase("controller_state_select")
    state = checked_path(policy["state_dir"], root)
    current_path = state / "current.json"
    mark_phase("controller_state_read")
    current, current_sha = private_json(current_path)
    mark_phase("controller_identity_check")
    identity = policy["database_identity"]
    if (
        policy.get("database_container") != CONTAINER
        or not isinstance(identity, dict)
        or current.get("database_identity") != identity
        or not _HEX.fullmatch(current.get("manifest_sha256", ""))
    ):
        raise RehearsalError("controller_current_database_identity_differs")
    mark_phase("controller_reference_select")
    refs = {
        role: policy[key]
        for role, key in (
            ("admission_manifest", "signed_predecessor_manifest"),
            ("admission_signature", "signed_predecessor_signature"),
            ("historical_registry", "previous_production_registry"),
        )
    }
    session = uuid4().hex
    mark_phase("controller_config_build")
    config = {
        "schema_version": "pals.live-rehearsal.config.v1",
        "database_name": "pals",
        "database_user": "postgres",
        "postgres_socket_directory": "/var/run/postgresql",
        "postgres_port": 5432,
        "deployment_lock_file": str(state / "host-update.lock"),
        "output_directory": str(root / "aws-migration-20261030/rehearsal" / session),
        "referenced_files": refs,
        "runtime_containers": {**policy["containers"], "database": CONTAINER},
        "expected_database_identity": {
            "database_system_identifier": identity["database_system_identifier"],
            "database_name": "pals",
            "postgresql_major": 16,
        },
        "docker_prefix": [
            policy["docker_binary"],
            "--config",
            policy["docker_config"],
            "--context",
            policy["docker_context"],
        ],
        "controller_binding": {
            "policy_file": str(path),
            "policy_sha256": policy_sha,
            "current_file": str(current_path),
            "current_sha256": current_sha,
            "manifest_sha256": current["manifest_sha256"],
            "database_identity": identity,
        },
    }
    mark_phase("controller_config_validate")
    validate_config(config, root)
    mark_phase("controller_lock_check")
    with existing_lock(Path(config["deployment_lock_file"])):
        verify_controller_binding(config, root)
    mark_phase("config_output_parent_check")
    directory = root / "aws-migration-20261030"
    if directory.resolve(strict=True) != directory or directory.stat().st_mode & 0o077:
        raise RehearsalError("migration_directory_not_private")
    mark_phase("config_output_write")
    parent = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        name = "rehearsal-config-" + session + ".json"
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(config))
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(parent)
    return directory / name


def verify_controller_binding(config: dict[str, Any], root: Path) -> None:
    binding = config.get("controller_binding")
    if binding is None:
        return
    if not isinstance(binding, dict) or set(binding) != {
        "policy_file",
        "policy_sha256",
        "current_file",
        "current_sha256",
        "manifest_sha256",
        "database_identity",
    }:
        raise RehearsalError("controller_binding_shape_differs")
    policy, p_sha = private_json(checked_path(binding["policy_file"], root))
    current, c_sha = private_json(checked_path(binding["current_file"], root))
    expected_refs = {
        role: policy[key]
        for role, key in (
            ("admission_manifest", "signed_predecessor_manifest"),
            ("admission_signature", "signed_predecessor_signature"),
            ("historical_registry", "previous_production_registry"),
        )
    }
    if (
        p_sha != binding["policy_sha256"]
        or c_sha != binding["current_sha256"]
        or policy.get("database_identity") != binding["database_identity"]
        or current.get("database_identity") != binding["database_identity"]
        or current.get("manifest_sha256") != binding["manifest_sha256"]
        or config["expected_database_identity"]["database_system_identifier"]
        != binding["database_identity"]["database_system_identifier"]
        or binding["policy_file"] != str(root / "controller-policy.json")
        or binding["current_file"] != str(Path(policy["state_dir"]) / "current.json")
        or config["deployment_lock_file"]
        != str(Path(policy["state_dir"]) / "host-update.lock")
        or config["referenced_files"] != expected_refs
        or config["runtime_containers"]
        != {**policy["containers"], "database": CONTAINER}
        or config["docker_prefix"]
        != [
            policy["docker_binary"],
            "--config",
            policy["docker_config"],
            "--context",
            policy["docker_context"],
        ]
    ):
        raise RehearsalError("controller_policy_or_current_state_changed")


def validate_reference_documents(
    references: dict[str, tuple[Path, int, dict[str, Any]]], config: dict[str, Any]
) -> None:
    def read(role: str) -> bytes:
        fd = references[role][1]
        os.lseek(fd, 0, 0)
        return os.read(fd, 16 * 1024**2 + 1)

    manifest = json.loads(read("admission_manifest"), object_pairs_hook=_pairs)
    registry = json.loads(read("historical_registry"), object_pairs_hook=_pairs)
    if (
        not isinstance(manifest, dict)
        or re.fullmatch(
            r"pals\.production-database-(?:bootstrap|update)\.mac\.v[1-8]",
            manifest.get("schema_version", ""),
        )
        is None
        or manifest.get("aws_account_id") != ACCOUNT
        or manifest.get("aws_region") != REGION
        or manifest.get("environment") != "prod"
        or manifest.get("database_name") != config["database_name"]
    ):
        raise RehearsalError("referenced_manifest_not_known_public_carrier")
    if (
        not isinstance(registry, dict)
        or set(registry) != {"schema_version", "postgresql_major", "steps"}
        or registry.get("schema_version") != "pals.production-database-release.v1"
        or registry.get("postgresql_major") != 16
        or not isinstance(registry.get("steps"), list)
        or manifest.get("artifacts", {}).get("production_manifest_sha256")
        != references["historical_registry"][2]["sha256"]
    ):
        raise RehearsalError("referenced_registry_not_manifest_bound_public_document")
    expected = config["expected_database_identity"]
    observed = manifest.get("deployment_identity", {})
    if any(observed.get(key) != value for key, value in expected.items()):
        raise RehearsalError("manifest_database_identity_differs")
    raw = read("admission_signature")
    if not 8 <= len(raw) <= 72 or raw[:1] != b"\x30" or raw[1] != len(raw) - 2:
        raise RehearsalError("signature_not_public_p256_der")
    offset = 2
    for _ in range(2):
        if offset + 2 > len(raw) or raw[offset] != 2:
            raise RehearsalError("signature_not_public_p256_der")
        size = raw[offset + 1]
        offset += 2
        integer = raw[offset : offset + size]
        if (
            not 1 <= size <= 33
            or len(integer) != size
            or integer[0] & 0x80
            or not int.from_bytes(integer, "big")
            or (size > 1 and integer[0] == 0 and not integer[1] & 0x80)
        ):
            raise RehearsalError("signature_not_public_p256_der")
        offset += size
    if offset != len(raw):
        raise RehearsalError("signature_not_public_p256_der")


def execute(config: dict[str, Any], root: Path) -> None:
    mark_phase("deployment_root")
    if root.resolve(strict=True) != root or root.is_symlink():
        raise RehearsalError("unsafe_deployment_root")
    references: dict[str, tuple[Path, int, dict[str, Any]]] = {}
    output = None
    snapshot = None
    mark_phase("source_lock")
    with existing_lock(
        checked_path(config["deployment_lock_file"], root)
    ) as verify_lock:
        try:
            mark_phase("controller_binding_check")
            verify_controller_binding(config, root)
            mark_phase("private_bucket_check")
            require_private_bucket()
            mark_phase("reference_open")
            for role, value in config["referenced_files"].items():
                path = checked_path(value, root)
                fd = trusted_file(path, maximum=16 * 1024**2)
                references[role] = (path, fd, file_hash(fd))
                if os.fstat(fd).st_size == 0:
                    raise RehearsalError("referenced_file_empty")
            mark_phase("reference_document_check")
            validate_reference_documents(references, config)
            if (
                config.get("controller_binding", {}).get(
                    "manifest_sha256", references["admission_manifest"][2]["sha256"]
                )
                != references["admission_manifest"][2]["sha256"]
            ):
                raise RehearsalError("controller_manifest_reference_differs")
            mark_phase("source_container_inspect")
            source = inspect_source(
                config["database_name"],
                config["database_user"],
                config.get("docker_prefix"),
            )
            source["_runtime_containers"] = config["runtime_containers"]
            mark_phase("runtime_image_inventory")
            images = runtime_images(source)
            mark_phase("source_tool_inventory")
            tools = container_tools(source)
            mark_phase("source_tool_version")
            version = command(
                [
                    *source.get("_docker", ["docker"]),
                    "exec",
                    "--user",
                    "postgres",
                    source["id"],
                    tools["env"],
                    "-i",
                    "PATH=" + source["path"],
                    "LC_ALL=C",
                    tools["pg_dump"],
                    "--version",
                ]
            )
            if (
                re.fullmatch(
                    rb"pg_dump \(PostgreSQL\) 16\.[0-9]+(?: \([^\n]+\))?\n", version
                )
                is None
            ):
                raise RehearsalError("source_pg_dump_not_pg16")
            mark_phase("export_directory_create")
            output = Output(Path(config["output_directory"]), root)
            mark_phase("snapshot_open")
            snapshot = Snapshot(
                docker_command(source, tools, config, "psql", interactive=True)
            )
            mark_phase("snapshot_identity")
            start = json.loads(snapshot.query(START))
            if (
                start.get("database") != source["database"]
                or start.get("user") != source["user"]
                or start.get("session_user") != source["user"]
                or start.get("transaction_isolation") != "repeatable read"
                or start.get("transaction_read_only") != "on"
                or int(start.get("server_port", "0")) != config["postgres_port"]
                or start.get("unix_socket_connection") is not True
                or int(start.get("version_num", "0")) // 10000 != 16
                or re.fullmatch(
                    r"[0-9A-Fa-f]+-[0-9A-Fa-f]+-[0-9]+", start.get("snapshot", "")
                )
                is None
            ):
                raise RehearsalError("source_sql_identity_differs")
            expected = config["expected_database_identity"]
            if (
                start["system_identifier"] != expected["database_system_identifier"]
                or start["database"] != expected["database_name"]
            ):
                raise RehearsalError("source_sql_policy_identity_differs")
            mark_phase("snapshot_metadata")
            metadata = json.loads(snapshot.query(METADATA))
            if (
                metadata.get("latest_admission", {}).get("manifest_sha256")
                != references["admission_manifest"][2]["sha256"]
            ):
                raise RehearsalError("referenced_manifest_is_not_snapshot_admission")
            for name, option in (
                ("source.dump", "--format=custom"),
                ("schema.sql", "--schema-only"),
            ):
                mark_phase("custom_dump" if name == "source.dump" else "schema_dump")
                fd = output.create(name)
                dump(
                    docker_command(source, tools, config, "pg_dump")
                    + [option, "--snapshot=" + start["snapshot"]],
                    fd,
                )
                if name == "source.dump":
                    os.lseek(fd, 0, os.SEEK_SET)
                    if os.read(fd, 5) != b"PGDMP":
                        raise RehearsalError("custom_dump_format_differs")
                else:
                    os.lseek(fd, 0, os.SEEK_SET)
                    if not os.read(fd, 128).startswith(
                        b"--\n-- PostgreSQL database dump\n--\n"
                    ):
                        raise RehearsalError("schema_dump_format_differs")
                if snapshot.query("SELECT 1;") != b"1":
                    raise RehearsalError("snapshot_session_lost")
            mark_phase("snapshot_close")
            snapshot.close()
            snapshot = None
            mark_phase("provider_library_observation")
            libc = (
                command(
                    [
                        *source.get("_docker", ["docker"]),
                        "exec",
                        "--user",
                        "postgres",
                        source["id"],
                        tools["env"],
                        "-i",
                        "PATH=" + source["path"],
                        "getconf",
                        "GNU_LIBC_VERSION",
                    ],
                    maximum=1024,
                )
                .decode()
                .strip()
            )
            if re.fullmatch(r"glibc [0-9]+\.[0-9]+", libc) is None:
                raise RehearsalError("provider_library_evidence_unavailable")
            mark_phase("tool_hash_observation")
            tool_hash = (
                command(
                    [
                        *source.get("_docker", ["docker"]),
                        "exec",
                        "--user",
                        "postgres",
                        source["id"],
                        tools["sha256sum"],
                        tools["psql"],
                        tools["pg_dump"],
                    ],
                    maximum=4096,
                )
                .decode()
                .splitlines()
            )
            if len(tool_hash) != 2 or any(
                not _HEX.fullmatch(line.split()[0]) for line in tool_hash
            ):
                raise RehearsalError("tool_hash_evidence_unavailable")
            mark_phase("runtime_recheck")
            if {
                **inspect_source(
                    config["database_name"],
                    config["database_user"],
                    config.get("docker_prefix"),
                ),
                "_runtime_containers": config["runtime_containers"],
            } != source or runtime_images(source) != images:
                raise RehearsalError("runtime_changed_during_export")
            mark_phase("reference_recheck")
            for path, fd, details in references.values():
                if not same_inode(path, fd) or file_hash(fd) != details:
                    raise RehearsalError("referenced_file_changed")
            verify_controller_binding(config, root)
            mark_phase("reference_copy")
            for role, (_path, fd, details) in references.items():
                target = output.create(REFERENCE_ARTIFACTS[role])
                os.lseek(fd, 0, os.SEEK_SET)
                while chunk := os.read(fd, 1024**2):
                    remaining = memoryview(chunk)
                    while remaining:
                        remaining = remaining[os.write(target, remaining) :]
                os.fsync(target)
                if file_hash(target) != details:
                    raise RehearsalError("reference_copy_does_not_match")
            verify_lock()
            output.verify()
            report = {
                "schema_version": "pals.live-rehearsal.metadata.v1",
                "admission_eligible": False,
                "source_quiescence": "not_requested_not_verified",
                "snapshot": start,
                "source_selection": {
                    key: value
                    for key, value in source.items()
                    if key != "path" and not key.startswith("_")
                },
                "operator_connection": {
                    "socket_directory": config["postgres_socket_directory"],
                    "port": config["postgres_port"],
                },
                "database_metadata": metadata,
                "libc_evidence": libc,
                "tools": {
                    "psql": tool_hash[0].split()[0],
                    "pg_dump": tool_hash[1].split()[0],
                },
                "runtime_images": images,
                "runtime_inventory_scope": "explicit_actor_names_plus_database",
                "reference_binding": "public_documents_copied_manifest_snapshot_and_registry_hash_bound_not_signature_verification",
                "cryptographic_trust_verified": False,
                "controller_binding": {
                    key: value
                    for key, value in config.get("controller_binding", {}).items()
                    if key not in {"policy_file", "current_file"}
                },
                "referenced_files": {
                    role: {
                        "path": str(path.relative_to(root)),
                        "artifact": REFERENCE_ARTIFACTS[role],
                        **details,
                    }
                    for role, (path, _fd, details) in references.items()
                },
            }
            mark_phase("metadata_write")
            output.create("metadata.json", canonical(report))
            mark_phase("manifest_prepare")
            session = uuid4().hex
            artifacts = {
                name: {**file_hash(fd), "s3_key": PREFIX + session + "/" + name}
                for name, fd in output.files.items()
            }
            manifest = {
                "schema_version": "pals.live-rehearsal.export.v1",
                "admission_eligible": False,
                "status": "rehearsal_export_complete_not_admission",
                "snapshot": start,
                "artifacts": artifacts,
                "bucket": BUCKET,
                "bucket_owner": ACCOUNT,
                "encryption": "AES256",
                "manifest_key": PREFIX + session + "/manifest.json",
            }
            output.create("manifest.json", canonical(manifest))
            mark_phase("artifact_upload")
            for name, details in artifacts.items():
                verify_lock()
                output.verify()
                upload(output, name, details["s3_key"], details)
                if file_hash(output.files[name]) != {
                    key: details[key] for key in ("sha256", "size_bytes")
                }:
                    raise RehearsalError("artifact_changed_during_upload")
            verify_lock()
            output.verify()
            mark_phase("manifest_upload")
            upload(
                output,
                "manifest.json",
                PREFIX + session + "/manifest.json",
                file_hash(output.files["manifest.json"]),
            )
        finally:
            if snapshot:
                snapshot.close()
            if output:
                output.close()
            for _path, fd, _details in references.values():
                os.close(fd)


def main(arguments: list[str] | None = None) -> int:
    mark_phase("initialization")
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--config", type=Path)
    selection.add_argument("--prepare-from-controller-policy", type=Path)
    args = parser.parse_args(arguments)

    def interrupted(_signal: int, _frame: object) -> None:
        raise RehearsalError("interrupted")

    previous = signal.signal(signal.SIGTERM, interrupted)
    previous_int = signal.signal(signal.SIGINT, interrupted)
    previous_alarm = signal.signal(signal.SIGALRM, interrupted)
    timer = signal.setitimer(signal.ITIMER_REAL, 1200)
    try:
        mark_phase("deployment_root")
        root = Path.home() / "pals-mini-deploy"
        config_path = args.config or prepare_from_policy(
            args.prepare_from_controller_policy, root
        )
        mark_phase("config_load")
        config = load_config(config_path, root)
        execute(config, root)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            failure_diagnostic(error),
            file=__import__("sys").stderr,
        )
        return 2
    finally:
        signal.setitimer(signal.ITIMER_REAL, *timer)
        signal.signal(signal.SIGINT, previous_int)
        signal.signal(signal.SIGALRM, previous_alarm)
        signal.signal(signal.SIGTERM, previous)
    print("Rehearsal export uploaded. Not admission evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
