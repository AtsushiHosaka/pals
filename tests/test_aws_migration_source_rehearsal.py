"""Rehearsal safety contracts. AWS/production selection doubles are unit-only."""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "pals-scripts/aws-migration-source-rehearsal.py"
)
SPEC = importlib.util.spec_from_file_location("source_rehearsal_helper", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def role_row(name="pals_fixture_runtime", *, rolconfig=None):
    return [name, False, False, False, False, True, False, -1, None, False, rolconfig]


def test_metadata_v2_accepts_only_observed_complete_null_role_configuration():
    rows = [role_row("postgres"), role_row()]
    original = json.loads(json.dumps(rows))
    helper.validate_role_inventory(rows, metadata_schema=helper.METADATA_SCHEMA)
    assert helper.METADATA_SCHEMA == "pals.live-rehearsal.metadata.v2"
    assert rows == original and all(len(row) == 11 and row[10] is None for row in rows)


@pytest.mark.parametrize(
    "rolconfig",
    [[], ["search_path=private_secret"], ["private_secret=value", "timezone=UTC"]],
)
def test_observed_nonnull_role_configuration_fails_closed_without_value_output(
    rolconfig,
):
    helper.mark_phase("role_inventory_validation")
    for name in ("postgres", "pals_fixture_runtime"):
        with pytest.raises(helper.RehearsalError) as failure:
            helper.validate_role_inventory(
                [role_row(name, rolconfig=rolconfig)],
                metadata_schema=helper.METADATA_SCHEMA,
            )
        assert helper.failure_diagnostic(failure.value) == (
            "Rehearsal export failed (phase=role_inventory_validation; category=guard_rejected; "
            "guard=source_role_configuration_unsupported); no payload or credential values were emitted."
        )


@pytest.mark.parametrize(
    "change",
    [
        "missing-config",
        "extra",
        "duplicate",
        "empty",
        "not-list",
        "name",
        "boolean",
        "connection-limit-bool",
        "connection-limit-range",
        "finite-expiry",
        "config-type",
        "config-element",
    ],
)
def test_role_inventory_closed_shape_types_uniqueness_and_no_padding(change):
    rows = [role_row()]
    if change == "missing-config":
        rows[0].pop()
    elif change == "extra":
        rows[0].append(None)
    elif change == "duplicate":
        rows.append(role_row())
    elif change == "empty":
        rows = []
    elif change == "not-list":
        rows = {"private_secret": "not-a-role-array"}
    elif change == "name":
        rows[0][0] = "private secret"
    elif change == "boolean":
        rows[0][2] = 0
    elif change == "connection-limit-bool":
        rows[0][7] = True
    elif change == "connection-limit-range":
        rows[0][7] = -2
    elif change == "finite-expiry":
        rows[0][8] = "2099-01-01"
    elif change == "config-type":
        rows[0][10] = "private_secret=value"
    else:
        rows[0][10] = [{"private_secret": "value"}]
    original = json.loads(json.dumps(rows))
    with pytest.raises(helper.RehearsalError, match="^source_role_inventory_invalid$"):
        helper.validate_role_inventory(rows, metadata_schema=helper.METADATA_SCHEMA)
    assert rows == original


@pytest.mark.parametrize(
    "schema",
    [None, 2, "pals.live-rehearsal.metadata.v1", "pals.live-rehearsal.metadata.v3"],
)
def test_role_inventory_cannot_relabel_old_or_unknown_metadata(schema):
    with pytest.raises(helper.RehearsalError, match="^source_role_inventory_invalid$"):
        helper.validate_role_inventory([role_row()], metadata_schema=schema)


@pytest.mark.parametrize("selection", ["bare-policy", "explicit-policy", "config"])
def test_cli_policy_path_is_optional_only_after_explicit_flag(
    tmp_path, monkeypatch, capsys, selection
):
    monkeypatch.setattr(helper.Path, "home", staticmethod(lambda: tmp_path))
    root = tmp_path / "pals-mini-deploy"
    policy = root / "controller-policy.json"
    config = root / "existing-config.json"
    prepared, loaded, executed = [], [], []

    def prepare(path, selected_root):
        prepared.append((path, selected_root))
        return config

    def load(path, selected_root):
        loaded.append((path, selected_root))
        return {"unit_only": True}

    monkeypatch.setattr(helper, "prepare_from_policy", prepare)
    monkeypatch.setattr(helper, "load_config", load)
    monkeypatch.setattr(
        helper,
        "execute",
        lambda value, selected_root: executed.append((value, selected_root)),
    )
    arguments = (
        ["--config", str(config)]
        if selection == "config"
        else ["--prepare-from-controller-policy", str(policy)]
        if selection == "explicit-policy"
        else ["--prepare-from-controller-policy"]
    )
    assert helper.main(arguments) == 0
    assert prepared == ([] if selection == "config" else [(policy, root)])
    assert loaded == [(config, root)]
    assert executed == [({"unit_only": True}, root)]
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    "arguments",
    [[], ["--config", "/explicit/config", "--prepare-from-controller-policy"]],
)
def test_cli_still_requires_one_explicit_mutually_exclusive_selection(
    arguments, monkeypatch, capsys
):
    monkeypatch.setattr(
        helper,
        "prepare_from_policy",
        lambda *_args: pytest.fail("unexpected preparation"),
    )
    monkeypatch.setattr(
        helper, "load_config", lambda *_args: pytest.fail("unexpected config read")
    )
    with pytest.raises(SystemExit) as failure:
        helper.main(arguments)
    assert failure.value.code == 2
    capsys.readouterr()


@pytest.mark.parametrize(
    "error,category",
    [
        (
            FileNotFoundError(2, "private-message", "/private/credential-path"),
            "missing_path",
        ),
        (PermissionError("private-message"), "permission_denied"),
        (BlockingIOError("private-message"), "lock_or_io_busy"),
        (KeyError("private-credential-member"), "required_member_missing"),
        (TypeError("private-message"), "unexpected_type"),
        (RuntimeError("private-message"), "runtime_failure"),
        (helper.RehearsalError("private_guard_message"), "guard_rejected"),
        (json.JSONDecodeError("private-message", "private-payload", 0), "invalid_json"),
        (
            subprocess.TimeoutExpired(["private-command", "private-secret"], 1),
            "command_timeout",
        ),
        (
            subprocess.CalledProcessError(
                3, ["private-command"], stderr=b"private-secret"
            ),
            "command_failure",
        ),
    ],
)
def test_failure_diagnostic_emits_only_closed_phase_and_category(error, category):
    helper.mark_phase("controller_policy_read")
    assert helper.failure_diagnostic(error) == (
        f"Rehearsal export failed (phase=controller_policy_read; category={category}); "
        "no payload or credential values were emitted."
    )


def test_failure_diagnostic_never_formats_exception_or_untrusted_phase(monkeypatch):
    class PrivateExceptionClassName(RuntimeError):
        def __str__(self):
            raise AssertionError("exception formatting must not run")

    monkeypatch.setattr(helper, "_PHASE", "private-credential-path")
    assert helper.failure_diagnostic(PrivateExceptionClassName()) == (
        "Rehearsal export failed (phase=initialization; category=runtime_failure); "
        "no payload or credential values were emitted."
    )
    with pytest.raises(ValueError, match="^invalid_static_phase$"):
        helper.mark_phase("private-credential-path")


@pytest.mark.parametrize("code", list(helper._PUBLIC_GUARDS))
def test_only_exact_known_guard_codes_can_leave_diagnostics(code):
    helper.mark_phase("aws_identity")
    assert helper.failure_diagnostic(helper.RehearsalError(code)) == (
        "Rehearsal export failed (phase=aws_identity; category=guard_rejected; "
        f"guard={code}); no payload or credential values were emitted."
    )


@pytest.mark.parametrize(
    "args",
    [
        ("wrong_aws_account_private_secret",),
        ("private_secret_wrong_aws_account",),
        ("command_failed_or_output_unbounded_private_secret",),
        ("bucket_acl_not_owner_private\nprivate_secret",),
        ("private_lowercase_credential_secret",),
        ({"wrong_aws_account": "private_secret"},),
        ("wrong_aws_account", "private_secret"),
        (),
    ],
)
def test_guard_lookalikes_and_arbitrary_exception_args_are_never_printed(args):
    helper.mark_phase("bucket_acl")
    assert helper.failure_diagnostic(helper.RehearsalError(*args)) == (
        "Rehearsal export failed (phase=bucket_acl; category=guard_rejected); "
        "no payload or credential values were emitted."
    )


def test_known_guard_does_not_format_exception_subclasses_or_string_subclasses():
    class PrivateError(helper.RehearsalError):
        def __str__(self):
            raise AssertionError("must not format exception")

    class PrivateString(str):
        def __str__(self):
            raise AssertionError("must not format argument")

    helper.mark_phase("bucket_acl")
    for error in (
        PrivateError("wrong_aws_account"),
        helper.RehearsalError(PrivateString("wrong_aws_account")),
    ):
        assert "guard=" not in helper.failure_diagnostic(error)


@pytest.mark.parametrize(
    "operation,phase",
    [
        ("ambient", "bucket_ambient_override"),
        ("get-caller-identity", "aws_identity"),
        ("head-bucket", "bucket_head"),
        ("get-public-access-block", "bucket_public_access"),
        ("get-bucket-acl", "bucket_acl"),
    ],
)
def test_bucket_failure_reports_exact_subphase_without_external_calls(
    monkeypatch, operation, phase
):
    monkeypatch.setattr(
        helper.os,
        "environ",
        {"AWS_CA_BUNDLE": "private_secret"} if operation == "ambient" else {},
    )

    def aws(_service, command, *_arguments):
        assert operation != "ambient"
        if command == operation:
            raise helper.RehearsalError("command_failed_or_output_unbounded")
        if command == "get-caller-identity":
            return {"Account": helper.ACCOUNT}
        if command == "get-public-access-block":
            return {
                "PublicAccessBlockConfiguration": dict.fromkeys(
                    (
                        "BlockPublicAcls",
                        "IgnorePublicAcls",
                        "BlockPublicPolicy",
                        "RestrictPublicBuckets",
                    ),
                    True,
                )
            }
        return {}

    monkeypatch.setattr(helper, "aws", aws)
    with pytest.raises(helper.RehearsalError) as failure:
        helper.require_private_bucket()
    code = (
        "ambient_aws_endpoint_or_ca_override"
        if operation == "ambient"
        else "command_failed_or_output_unbounded"
    )
    assert helper.failure_diagnostic(failure.value) == (
        f"Rehearsal export failed (phase={phase}; category=guard_rejected; guard={code}); "
        "no payload or credential values were emitted."
    )


@pytest.mark.parametrize(
    "stage,phase,category",
    [
        ("policy-missing", "controller_policy_read", "missing_path"),
        ("policy-member", "controller_state_select", "required_member_missing"),
        ("config-missing", "config_load", "missing_path"),
        ("dump-type", "custom_dump", "unexpected_type"),
    ],
)
def test_main_classifies_real_preparation_and_export_boundaries_without_leakage(
    tmp_path, monkeypatch, capsys, stage, phase, category
):
    monkeypatch.setattr(helper.Path, "home", staticmethod(lambda: tmp_path))
    root = tmp_path / "pals-mini-deploy"

    def missing(*_args):
        raise FileNotFoundError(2, "private-payload", "/private/credential-path")

    if stage.startswith("policy"):
        monkeypatch.setattr(
            helper,
            "private_json",
            missing if stage == "policy-missing" else lambda *_args: ({}, "a" * 64),
        )
        args = [
            "--prepare-from-controller-policy",
            str(root / "controller-policy.json"),
        ]
    else:
        args = ["--config", str(root / "private-config.json")]
        if stage == "config-missing":
            monkeypatch.setattr(helper, "load_config", missing)
        else:
            monkeypatch.setattr(helper, "load_config", lambda *_args: {})

            def fail_dump(*_args):
                helper.mark_phase("custom_dump")
                raise TypeError("private-payload credential-secret")

            monkeypatch.setattr(helper, "execute", fail_dump)
    assert helper.main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"Rehearsal export failed (phase={phase}; category={category}); "
        "no payload or credential values were emitted.\n"
    )
    assert str(tmp_path) not in captured.err


def container():
    return {
        "Id": "1" * 64,
        "Image": "sha256:" + "2" * 64,
        "Name": "/" + helper.CONTAINER,
        "State": {"Running": True, "Restarting": False, "Paused": False, "Dead": False},
        "Config": {
            "Env": [
                "POSTGRES_DB=observed_db",
                "POSTGRES_USER=observed_admin",
                "PATH=/usr/bin:/bin",
                "POSTGRES_PASSWORD=must-not-leak",
            ],
            "Labels": {
                "com.docker.compose.project": "pals-observed",
                "com.docker.compose.service": "db",
            },
        },
    }


def test_source_selection_uses_only_observed_required_env_and_exact_container(
    monkeypatch,
):
    monkeypatch.setattr(
        helper, "command", lambda args: json.dumps([container()]).encode()
    )
    selected = helper.inspect_source("observed_db", "observed_admin")
    assert (
        selected["database"] == "observed_db" and selected["user"] == "observed_admin"
    )
    assert "must-not-leak" not in repr(selected)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "multiple",
        "wrong",
        "stopped",
        "paused",
        "missing_db",
        "wrong_user",
        "duplicate",
        "dsn",
        "geekten_name",
    ],
)
def test_wrong_missing_ambiguous_source_fails(change, monkeypatch):
    value = container()
    values = [value]
    if change == "missing":
        values = []
    elif change == "multiple":
        values = [value, value]
    elif change == "wrong":
        value["Name"] = "/other-db"
    elif change == "stopped":
        value["State"]["Running"] = False
    elif change == "paused":
        value["State"]["Paused"] = True
    elif change == "missing_db":
        value["Config"]["Env"] = [
            item
            for item in value["Config"]["Env"]
            if not item.startswith("POSTGRES_DB=")
        ]
    elif change == "wrong_user":
        value["Config"]["Env"][1] = "POSTGRES_USER=wrong_admin"
    elif change == "duplicate":
        value["Config"]["Env"].append("POSTGRES_DB=other")
    elif change == "dsn":
        value["Config"]["Env"][0] = "POSTGRES_DB=host=unsafe"
    else:
        value["Name"] = "/geekten-db"
    monkeypatch.setattr(helper, "command", lambda args: json.dumps(values).encode())
    with pytest.raises(helper.RehearsalError):
        helper.inspect_source("observed_db", "observed_admin")


def test_explicit_config_user_is_required_when_container_omits_user(monkeypatch):
    value = container()
    value["Config"]["Env"] = [
        entry
        for entry in value["Config"]["Env"]
        if not entry.startswith("POSTGRES_USER=")
    ]
    monkeypatch.setattr(helper, "command", lambda args: json.dumps([value]).encode())
    assert (
        helper.inspect_source("observed_db", "observed_admin")["user"]
        == "observed_admin"
    )
    with pytest.raises(helper.RehearsalError):
        helper.inspect_source("different_db", "observed_admin")


def test_existing_lock_and_output_never_follow_symlinks_or_overwrite(tmp_path):
    root = tmp_path.resolve()
    lock = root / "existing.lock"
    lock.write_bytes(b"")
    lock.chmod(0o600)
    with pytest.raises(FileNotFoundError), helper.existing_lock(root / "missing.lock"):
        pytest.fail("created deployment lock")
    with pytest.raises(helper.RehearsalError), helper.existing_lock(lock) as verify:
        lock.rename(root / "old.lock")
        lock.write_bytes(b"")
        lock.chmod(0o600)
        with pytest.raises(helper.RehearsalError):
            verify()


def test_output_private_inode_bound_and_no_overwrite(tmp_path):
    root = tmp_path.resolve()
    path = root / "aws-migration-20261030/rehearsal/run01"
    output = helper.Output(path, root)
    try:
        fd = output.create("source.dump", b"PGDMP")
        assert path.stat().st_mode & 0o777 == 0o700
        assert os.fstat(fd).st_mode & 0o777 == 0o600
        with pytest.raises(FileExistsError):
            output.create("source.dump", b"overwrite")
        assert helper.file_hash(fd)["size_bytes"] == 5
        (path / "source.dump").rename(path / "old.dump")
        (path / "source.dump").symlink_to(path / "old.dump")
        with pytest.raises(helper.RehearsalError):
            output.verify()
    finally:
        output.close()
    with pytest.raises(helper.RehearsalError):
        helper.Output(path, root)


def test_s3_profile_endpoint_owner_private_and_checksum_guards(tmp_path, monkeypatch):
    calls = []

    def response(args, **kwargs):
        calls.append(args)
        return b"{}"

    monkeypatch.setattr(helper, "command", response)
    helper.aws("s3api", "head-bucket", "--expected-bucket-owner", helper.ACCOUNT)
    assert calls[0][:7] == [
        "aws",
        "--profile",
        helper.PROFILE,
        "--region",
        helper.REGION,
        "--endpoint-url",
        "https://s3.ap-northeast-1.amazonaws.com",
    ]
    root = tmp_path.resolve()
    output = helper.Output(root / "aws-migration-20261030/rehearsal/run01", root)
    try:
        fd = output.create("source.dump", b"PGDMP-test")
        details = helper.file_hash(fd)
        checksum = base64.b64encode(bytes.fromhex(details["sha256"])).decode()
        recorded = []

        def aws(service, *args, pass_fds=()):
            recorded.append(args)
            assert args[args.index("--expected-bucket-owner") + 1] == helper.ACCOUNT
            if args[0] == "put-object":
                assert (
                    pass_fds == (fd,)
                    and args[args.index("--body") + 1] == f"/dev/fd/{fd}"
                )
                assert args[args.index("--server-side-encryption") + 1] == "AES256"
                assert args[args.index("--if-none-match") + 1] == "*"
                return {}
            return {
                "ContentLength": details["size_bytes"],
                "ServerSideEncryption": "AES256",
                "ChecksumSHA256": checksum,
                "Metadata": {"sha256": details["sha256"]},
            }

        monkeypatch.setattr(helper, "aws", aws)
        helper.upload(
            output, "source.dump", helper.PREFIX + "synthetic/source.dump", details
        )
        assert len(recorded) == 2
    finally:
        output.close()


def test_reference_paths_never_leave_deployment_root(tmp_path):
    root = tmp_path.resolve() / "deploy"
    root.mkdir()
    with pytest.raises(helper.RehearsalError):
        helper.checked_path(str(tmp_path.resolve() / ".aws/credentials"), root)
    with pytest.raises(helper.RehearsalError):
        helper.checked_path(str(root / "../credentials"), root)


@pytest.mark.parametrize("change", [None, "account", "block", "acl"])
def test_bucket_must_be_same_account_owner_private_and_block_public(
    change, monkeypatch
):
    def aws(service, *arguments):
        if service == "sts":
            return {
                "Account": "000000000000" if change == "account" else helper.ACCOUNT
            }
        assert (
            arguments[arguments.index("--expected-bucket-owner") + 1] == helper.ACCOUNT
        )
        if arguments[0] == "get-public-access-block":
            return {
                "PublicAccessBlockConfiguration": {
                    key: change != "block"
                    for key in (
                        "BlockPublicAcls",
                        "IgnorePublicAcls",
                        "BlockPublicPolicy",
                        "RestrictPublicBuckets",
                    )
                }
            }
        if arguments[0] == "get-bucket-acl":
            return {
                "Owner": {"ID": "same-owner"},
                "Grants": [
                    {
                        "Grantee": {
                            "Type": "CanonicalUser",
                            "ID": "other" if change == "acl" else "same-owner",
                        }
                    }
                ],
            }
        return {}

    monkeypatch.setattr(helper, "aws", aws)
    if change is None:
        helper.require_private_bucket()
    else:
        with pytest.raises(helper.RehearsalError):
            helper.require_private_bucket()


@pytest.mark.parametrize(
    "bad_role",
    [
        None,
        "admission_manifest",
        "admission_signature",
        "historical_registry",
        "missing-role-field",
        "role-settings",
    ],
)
def test_execute_binds_artifacts_and_uploads_manifest_last(
    tmp_path, monkeypatch, bad_role
):
    root = tmp_path.resolve()
    lock = root / "deploy.lock"
    lock.write_bytes(b"")
    lock.chmod(0o600)
    registry = helper.canonical(
        {
            "schema_version": "pals.production-database-release.v1",
            "postgresql_major": 16,
            "steps": [],
        }
    )
    documents = {
        "historical_registry": registry,
        "admission_signature": b"\x30\x06\x02\x01\x01\x02\x01\x01",
    }
    documents["admission_manifest"] = helper.canonical(
        {
            "schema_version": "pals.production-database-update.mac.v8",
            "aws_account_id": helper.ACCOUNT,
            "aws_region": helper.REGION,
            "environment": "prod",
            "database_name": "observed_db",
            "deployment_identity": {
                "database_system_identifier": "123456789",
                "database_name": "observed_db",
                "postgresql_major": 16,
            },
            "artifacts": {
                "production_manifest_sha256": helper.hashlib.sha256(
                    registry
                ).hexdigest()
            },
        }
    )
    references = {}
    for role in ("admission_manifest", "admission_signature", "historical_registry"):
        path = root / (role + ".json")
        path.write_bytes(documents[role])
        path.chmod(0o600)
        references[role] = str(path)
    if bad_role in references:
        Path(references[bad_role]).write_bytes(b"not-a-public-deployment-document")
    source = {
        "id": "1" * 64,
        "image_id": "sha256:" + "2" * 64,
        "project": "pals-observed",
        "service": "db",
        "database": "observed_db",
        "user": "observed_admin",
        "path": "/usr/bin:/bin",
    }
    config = {
        "deployment_lock_file": str(lock),
        "referenced_files": references,
        "database_name": "observed_db",
        "database_user": "observed_admin",
        "runtime_containers": {"database": helper.CONTAINER},
        "expected_database_identity": {
            "database_system_identifier": "123456789",
            "database_name": "observed_db",
            "postgresql_major": 16,
        },
        "postgres_socket_directory": "/synthetic/socket",
        "postgres_port": 5432,
        "output_directory": str(root / "aws-migration-20261030/rehearsal/run01"),
    }
    monkeypatch.setattr(helper, "require_private_bucket", lambda: None)
    monkeypatch.setattr(helper, "inspect_source", lambda *args: source)
    monkeypatch.setattr(
        helper,
        "runtime_images",
        lambda source: [{"id": source["id"], "image_id": source["image_id"]}],
    )
    monkeypatch.setattr(
        helper,
        "container_tools",
        lambda source: {
            key: "/usr/bin/" + key for key in ("env", "psql", "pg_dump", "sha256sum")
        },
    )

    def command(args, **kwargs):
        if "--version" in args:
            return b"pg_dump (PostgreSQL) 16.15 (Debian 16.15-1.pgdg12+2)\n"
        if "getconf" in args:
            return b"glibc 2.36\n"
        return (
            "a" * 64 + "  /usr/bin/psql\n" + "b" * 64 + "  /usr/bin/pg_dump\n"
        ).encode()

    monkeypatch.setattr(helper, "command", command)
    manifest_sha = helper.hashlib.sha256(documents["admission_manifest"]).hexdigest()

    class Snapshot:
        def __init__(self, args):
            self.closed = False

        def query(self, query):
            if query == helper.START:
                return json.dumps(
                    {
                        "snapshot": "00000001-00000001-1",
                        "database": source["database"],
                        "user": source["user"],
                        "session_user": source["user"],
                        "version_num": "160015",
                        "system_identifier": "123456789",
                        "transaction_isolation": "repeatable read",
                        "transaction_read_only": "on",
                        "server_port": "5432",
                        "unix_socket_connection": True,
                    }
                ).encode()
            if query == helper.METADATA:
                roles = [role_row("observed_admin"), role_row()]
                if bad_role == "missing-role-field":
                    roles[0].pop()
                elif bad_role == "role-settings":
                    roles[0][10] = ["application_name=private_secret"]
                return json.dumps(
                    {
                        "latest_admission": {"manifest_sha256": manifest_sha},
                        "database": {"actual_collation_version": "2.36"},
                        "roles": roles,
                    }
                ).encode()
            return b"1"

        def close(self):
            assert helper._LOCK_FD is not None
            self.closed = True

    monkeypatch.setattr(helper, "Snapshot", Snapshot)
    dumps = []

    def dump(args, fd):
        dumps.append(args)
        os.write(
            fd,
            b"PGDMP-synthetic"
            if "--format=custom" in args
            else b"--\n-- PostgreSQL database dump\n--\n",
        )

    monkeypatch.setattr(helper, "dump", dump)
    uploaded = []

    def upload(output, name, key, details):
        output.verify()
        uploaded.append(name)
        assert (
            key.startswith(helper.PREFIX)
            and details == helper.file_hash(output.files[name])
            or name != "manifest.json"
        )

    monkeypatch.setattr(helper, "upload", upload)
    if bad_role is not None:
        with pytest.raises((ValueError, helper.RehearsalError)):
            helper.execute(config, root)
        assert uploaded == []
        assert dumps == []
        return
    helper.execute(config, root)
    assert uploaded == [
        "source.dump",
        "schema.sql",
        *helper.REFERENCE_ARTIFACTS.values(),
        "metadata.json",
        "manifest.json",
    ]
    assert all("--snapshot=00000001-00000001-1" in args for args in dumps)
    manifest = json.loads(
        (Path(config["output_directory"]) / "manifest.json").read_bytes()
    )
    assert manifest["admission_eligible"] is False
    assert manifest["status"] == "rehearsal_export_complete_not_admission"
    report = json.loads(
        (Path(config["output_directory"]) / "metadata.json").read_bytes()
    )
    assert report["schema_version"] == helper.METADATA_SCHEMA
    assert report["admission_eligible"] is False
    assert report["cryptographic_trust_verified"] is False
    assert all(
        len(row) == 11 and row[10] is None
        for row in report["database_metadata"]["roles"]
    )
    assert set(manifest["artifacts"]) == {
        "source.dump",
        "schema.sql",
        "metadata.json",
        *helper.REFERENCE_ARTIFACTS.values(),
    }
    for role, filename in helper.REFERENCE_ARTIFACTS.items():
        assert (Path(config["output_directory"]) / filename).read_bytes() == documents[
            role
        ]


def test_policy_mode_uses_only_named_references_and_lifecycle_lock(tmp_path):
    root = tmp_path.resolve()
    state = root / "state"
    state.mkdir(mode=0o700)
    (root / "aws-migration-20261030").mkdir(mode=0o700)
    lock = state / "host-update.lock"
    lock.write_bytes(b"")
    lock.chmod(0o600)
    references = {}
    for name in ("manifest.jcs", "signature.bin", "current-registry.raw"):
        path = root / name
        path.write_bytes(b"public-reference")
        path.chmod(0o600)
        references[name] = str(path)
    identity = {
        "database_system_identifier": "123456789",
        "database_volume_id": "public-volume",
        "host_binding_sha256": "a" * 64,
    }
    policy = {
        "state_dir": str(state),
        "database_container": helper.CONTAINER,
        "database_identity": identity,
        "signed_predecessor_manifest": references["manifest.jcs"],
        "signed_predecessor_signature": references["signature.bin"],
        "previous_production_registry": references["current-registry.raw"],
        "docker_binary": "/observed/docker",
        "docker_config": "/observed/docker-config",
        "docker_context": "observed-context",
        "containers": {"api": "pals-api-exact", "worker": "pals-worker-other-project"},
        "unrelated_secret": "never-copy-this-value",
    }
    current = {"database_identity": identity, "manifest_sha256": "b" * 64}

    def write(path, value):
        path.write_bytes(helper.canonical(value))
        path.chmod(0o600)

    policy_file = root / "controller-policy.json"
    write(policy_file, policy)
    write(state / "current.json", current)
    generated = helper.prepare_from_policy(policy_file, root)
    config = helper.load_config(generated, root)
    assert generated.stat().st_mode & 0o777 == 0o600
    assert config["database_user"] == "postgres" and config["database_name"] == "pals"
    assert config["deployment_lock_file"] == str(lock)
    assert config["runtime_containers"]["worker"] == "pals-worker-other-project"
    assert config["docker_prefix"] == [
        "/observed/docker",
        "--config",
        "/observed/docker-config",
        "--context",
        "observed-context",
    ]
    assert "never-copy-this-value" not in generated.read_text()
    current["database_identity"] = {**identity, "database_system_identifier": "999"}
    write(state / "current.json", current)
    with pytest.raises(helper.RehearsalError):
        helper.verify_controller_binding(config, root)


def test_runtime_inventory_uses_exact_actors_across_compose_projects(monkeypatch):
    source = {
        "id": "1" * 64,
        "_docker": ["docker"],
        "_runtime_containers": {
            "database": helper.CONTAINER,
            "worker": "pals-worker-other-project",
        },
    }
    db = container()
    db["Config"]["Labels"] = {"com.docker.compose.project": "pals-webfix"}
    worker = {
        "Id": "3" * 64,
        "Image": "sha256:" + "4" * 64,
        "Name": "/pals-worker-other-project",
        "State": {"Status": "running", "Running": True},
        "Config": {
            "Image": "worker:observed",
            "Labels": {"com.docker.compose.project": "pals-legacy"},
        },
    }

    def command(args, **kwargs):
        assert "ps" not in args
        if args[1:3] == ["image", "inspect"]:
            return json.dumps(
                [{"Id": "sha256:" + x * 64, "RepoDigests": []} for x in ("2", "4")]
            ).encode()
        assert set(args[2:]) == {helper.CONTAINER, "pals-worker-other-project"}
        return json.dumps([db, worker]).encode()

    monkeypatch.setattr(helper, "command", command)
    result = helper.runtime_images(source)
    assert {entry["role"] for entry in result} == {"database", "worker"}
    assert {entry["compose_project"] for entry in result} == {
        "pals-webfix",
        "pals-legacy",
    }


def test_command_timeout_and_output_bounds_do_not_emit_stderr(capsys):
    with pytest.raises(helper.RehearsalError):
        helper.command([sys.executable, "-c", "print('x'*10000)"], maximum=100)
    with pytest.raises(helper.RehearsalError):
        helper.command(
            [
                sys.executable,
                "-c",
                "import sys;sys.stderr.write('must-not-leak');sys.exit(1)",
            ]
        )
    assert "must-not-leak" not in repr(capsys.readouterr())


def test_actual_psql_snapshot_binds_both_dumps_and_metadata(tmp_path_factory):
    if os.environ.get("PALS_REHEARSAL_ISOLATED_TEST") != "1":
        pytest.skip("owned PG16 fixture opt-in required")
    api = SCRIPT.parents[1] / "pals-api"
    sys.path.insert(0, str(api))
    try:
        spec = importlib.util.spec_from_file_location(
            "owned_pg16_fixture",
            api / "tests/integration/test_cloud_restore_snapshot.py",
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixture = module.isolated_pg16.__wrapped__(tmp_path_factory)
        name, url = next(fixture)
        try:
            import psycopg

            with psycopg.connect(url) as c:
                c.execute("CREATE TABLE records(value text,original bytea)")
                c.execute(
                    "INSERT INTO records VALUES ('same',decode('00ff','hex')),('same',decode('00ff','hex'))"
                )
                c.execute(
                    "CREATE TABLE proof_runtime_release_admissions(environment text,release_sequence int,manifest_sha256 text,admitted_at timestamptz)"
                )
                c.execute(
                    "INSERT INTO proof_runtime_release_admissions VALUES ('prod',1,'synthetic',now())"
                )
                c.execute(
                    "CREATE TABLE proof_runtime_trust_fence(environment text,fence_committed_at timestamptz)"
                )
                c.execute("INSERT INTO proof_runtime_trust_fence VALUES ('prod',now())")
            inspected = json.loads(helper.command(["docker", "inspect", name]))[0]
            environment = dict(
                item.split("=", 1) for item in inspected["Config"]["Env"]
            )
            source = {
                "id": inspected["Id"],
                "database": "pals",
                "user": "postgres",
                "path": environment["PATH"],
            }
            config = {
                "postgres_socket_directory": "/var/run/postgresql",
                "postgres_port": 5432,
            }
            tools = helper.container_tools(source)
            keeper = helper.Snapshot(
                helper.docker_command(source, tools, config, "psql", interactive=True)
            )
            directory = tmp_path_factory.mktemp("rehearsal-output").resolve()
            output = helper.Output(
                directory / "aws-migration-20261030/rehearsal/run01", directory
            )
            try:
                start = json.loads(keeper.query(helper.START))
                with psycopg.connect(url) as writer:
                    writer.execute("INSERT INTO records VALUES ('later',NULL)")
                    writer.execute("CREATE TABLE later_schema_change(value text)")
                    writer.execute(
                        "UPDATE proof_runtime_release_admissions SET release_sequence=2"
                    )
                metadata = json.loads(keeper.query(helper.METADATA))
                helper.validate_role_inventory(
                    metadata["roles"], metadata_schema=helper.METADATA_SCHEMA
                )
                observed = next(
                    row for row in metadata["roles"] if row[0] == "postgres"
                )
                assert len(observed) == 11 and observed[10] is None
                assert metadata["latest_admission"]["release_sequence"] == 1
                assert "recorded_collation_version" in metadata["database"]
                for filename, option in (
                    ("source.dump", "--format=custom"),
                    ("schema.sql", "--schema-only"),
                ):
                    fd = output.create(filename)
                    helper.dump(
                        helper.docker_command(source, tools, config, "pg_dump")
                        + [option, "--snapshot=" + start["snapshot"]],
                        fd,
                    )
                os.lseek(output.files["schema.sql"], 0, 0)
                schema = os.read(output.files["schema.sql"], helper.MAX_METADATA)
                assert b"later_schema_change" not in schema
                os.lseek(output.files["source.dump"], 0, 0)
                archive = os.read(output.files["source.dump"], helper.MAX_METADATA)
                assert archive.startswith(b"PGDMP")
                with psycopg.connect(url, autocommit=True) as c:
                    c.execute("CREATE DATABASE rehearsal_restore")
                subprocess.run(
                    [
                        "docker",
                        "exec",
                        "-i",
                        name,
                        "pg_restore",
                        "-U",
                        "postgres",
                        "-d",
                        "rehearsal_restore",
                        "--exit-on-error",
                    ],
                    input=archive,
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
                with psycopg.connect(
                    url.replace("/pals?", "/rehearsal_restore?")
                ) as restored:
                    assert restored.execute(
                        "SELECT value,original FROM records"
                    ).fetchall() == [("same", b"\x00\xff"), ("same", b"\x00\xff")]
                    assert restored.execute(
                        "SELECT release_sequence FROM proof_runtime_release_admissions"
                    ).fetchone() == (1,)
                # Observe the real PG16 array instead of inventing an absent GUC.
                # This fixture owns its entire isolated cluster and never runs on Mini.
                with psycopg.connect(url) as writer:
                    writer.execute("CREATE ROLE pals_fixture_role_config")
                    writer.execute(
                        "ALTER ROLE pals_fixture_role_config SET work_mem='4MB'"
                    )
                configured_keeper = helper.Snapshot(
                    helper.docker_command(
                        source, tools, config, "psql", interactive=True
                    )
                )
                try:
                    configured_keeper.query(helper.START)
                    configured = json.loads(configured_keeper.query(helper.METADATA))
                    observed_config = next(
                        row
                        for row in configured["roles"]
                        if row[0] == "pals_fixture_role_config"
                    )
                    assert observed_config[10] == ["work_mem=4MB"]
                    with pytest.raises(
                        helper.RehearsalError,
                        match="^source_role_configuration_unsupported$",
                    ):
                        helper.validate_role_inventory(
                            configured["roles"], metadata_schema=helper.METADATA_SCHEMA
                        )
                finally:
                    configured_keeper.close()
            finally:
                keeper.close()
                output.close()
        finally:
            with pytest.raises(StopIteration):
                next(fixture)
    finally:
        sys.path.pop(0)
