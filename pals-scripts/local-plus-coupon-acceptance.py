#!/usr/bin/env python3
"""Local Plus coupon acceptance: real PostgreSQL, real API over HTTP, local Cognito.

Separate from ``make release-local-qualify`` and never part of its frozen runner. It
issues two one-use coupons with the candidate's own operator CLI, signs two throw-away
learners in through the loopback Cognito emulator, redeems over HTTP, and reads the
result back from PostgreSQL. It calls no model and no provider. Coupon codes and tokens
exist only in memory: nothing here writes or prints one (counts and closed results only).

PASS means only: this local stack behaved as listed. It is not production admission, not
production Cognito, and not a guest or paid-model qualification.
"""

from __future__ import annotations

import argparse
import calendar
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import uuid4

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Dataclasses with postponed annotations resolve their module through sys.modules.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gate = load("local_plus_coupon_acceptance_gate", HERE / "local-qualification.py")
cognito_tool = load(
    "local_plus_coupon_acceptance_cognito", HERE / "bootstrap-local-cognito.py"
)
sys.path.insert(0, str(HERE / "local-qualification"))
bootstrap = load(
    "local_plus_coupon_acceptance_bootstrap",
    HERE / "local-qualification/bootstrap_database.py",
)
readiness = load(
    "local_plus_coupon_acceptance_readiness",
    HERE / "local-qualification/database_readiness.py",
)

LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
OPERATOR_ROLE = "pals_billing_test_admin"
REQUEST_TIMEOUT = 20
ISSUE_TIMEOUT = 60


class Failure(gate.Refusal):
    """A closed, secret-free acceptance failure."""


def require(value, code):
    if not value:
        raise Failure(code)


def loopback_origin(value, code):
    parts = urlsplit(value)
    try:
        port = parts.port
    except ValueError:
        raise Failure(code) from None
    require(
        parts.scheme == "http"
        and parts.hostname in LOOPBACK
        and port is not None
        and not parts.username
        and not parts.password
        and parts.path in ("", "/")
        and not parts.query
        and not parts.fragment,
        code,
    )
    return value.rstrip("/")


def add_one_utc_month(moment):
    """PostgreSQL's ``timestamp + interval '1 month'``: same wall time, day clamped."""
    utc = moment.astimezone(timezone.utc)
    year = utc.year + utc.month // 12
    month = utc.month % 12 + 1
    day = min(utc.day, calendar.monthrange(year, month)[1])
    return utc.replace(year=year, month=month, day=day)


def parse_time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "acceptance_timestamp_without_zone")
    return parsed.astimezone(timezone.utc)


class Http:
    """JSON over loopback HTTP. Bodies are parsed here and never printed."""

    def request(self, method, url, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            url, data=data, method=method, headers=headers or {}
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                return response.status, _json(response.read())
        except urllib.error.HTTPError as error:
            return error.code, _json(error.read())
        except (OSError, urllib.error.URLError):
            raise Failure("acceptance_api_unreachable") from None


def _json(raw):
    try:
        return json.loads(raw or b"null")
    except ValueError:
        return None


def error_code(body):
    error = body.get("error") if isinstance(body, dict) else None
    code = error.get("code") if isinstance(error, dict) else None
    return code if isinstance(code, str) else None


class Learner:
    """One throw-away local Cognito account and its current access token."""

    def __init__(self, api, cognito, client_id, pool_id):
        self.api, self.cognito = api, cognito
        self.client_id, self.pool_id = client_id, pool_id
        self.email = "coupon-acc-" + secrets.token_hex(6) + "@example.test"
        self.password = cognito_tool._new_password()
        self.token = None
        self.user_id = None
        self.created = False

    def create(self):
        attributes = [
            {"Name": "email", "Value": self.email},
            {"Name": "email_verified", "Value": "true"},
        ]
        self.cognito.call(
            "AdminCreateUser",
            {
                "MessageAction": "SUPPRESS",
                "UserAttributes": attributes,
                "UserPoolId": self.pool_id,
                "Username": self.email,
            },
        )
        self.created = True
        self.cognito.call(
            "AdminSetUserPassword",
            {
                "Password": self.password,
                "Permanent": True,
                "UserPoolId": self.pool_id,
                "Username": self.email,
            },
        )

    def login(self):
        result = self.cognito.call(
            "InitiateAuth",
            {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {"USERNAME": self.email, "PASSWORD": self.password},
                "ClientId": self.client_id,
            },
        ).get("AuthenticationResult")
        token = result.get("AccessToken") if isinstance(result, dict) else None
        require(isinstance(token, str) and token, "acceptance_cognito_login_failed")
        self.token = token
        status, me = self.api.call("GET", "/v1/auth/me", token=token)
        require(
            status == 200
            and isinstance(me, dict)
            and isinstance(me.get("user_id"), str)
            and me["user_id"],
            "acceptance_authenticated_identity_failed",
        )
        require(
            self.user_id in (None, me["user_id"]),
            "acceptance_identity_changed_on_reload",
        )
        self.user_id = me["user_id"]

    def delete(self):
        if self.created:
            self.cognito.call(
                "AdminDeleteUser",
                {"UserPoolId": self.pool_id, "Username": self.email},
            )
            self.created = False


class Api:
    def __init__(self, base, http):
        self.base, self.http = base, http

    def call(self, method, path, *, token=None, body=None):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["Authorization"] = "Bearer " + token
        return self.http.request(method, self.base + path, body, headers)


class Database:
    """Administrator reads of the dedicated local database; operator role lifecycle."""

    def __init__(self, url, connect=None):
        bootstrap.validate_local_dsn(url)
        self.url = url
        if connect is None:
            import psycopg

            connect = psycopg.connect
        self.connect = connect
        self.operator_role = None

    def rows(self, query, parameters=()):
        with self.connect(self.url) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            return connection.execute(query, parameters).fetchall()

    def create_operator(self):
        """A login that is a member of the signed operator role, nothing else."""
        from psycopg import sql

        role = "coupon_acc_operator_" + secrets.token_hex(8)
        password = secrets.token_urlsafe(32)
        with self.connect(self.url, autocommit=True) as connection:
            connection.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}"
                ).format(sql.Identifier(role), sql.Literal(password))
            )
            self.operator_role = role
            connection.execute(
                sql.SQL("GRANT {} TO {} WITH INHERIT FALSE, SET TRUE").format(
                    sql.Identifier(OPERATOR_ROLE), sql.Identifier(role)
                )
            )
        parts = urlsplit(self.url)
        return urlunsplit(
            parts._replace(
                netloc=role
                + ":"
                + quote(password, safe="")
                + "@"
                + parts.netloc.rsplit("@", 1)[1]
            )
        )

    def drop_operator(self):
        if self.operator_role is None:
            return
        from psycopg import sql

        with self.connect(self.url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP ROLE {}").format(sql.Identifier(self.operator_role))
            )
        self.operator_role = None


def issue_with_cli(api_python, api_source, operator_url, *, runner=subprocess.run):
    """One coupon through the candidate's own initial-campaign CLI; stdout stays in memory."""
    coupon_id = str(uuid4())
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PALS_ENV": "local",
        "PALS_PLUS_COUPONS_ENABLED": "true",
        "PALS_BILLING_OPERATOR_DATABASE_URL": operator_url,
    }
    deadline = datetime.now(timezone.utc) + timedelta(days=7)
    result = runner(
        [
            str(api_python),
            "-m",
            "app.release.plus_coupon_admin",
            "issue-initial-campaign",
            "--coupon-id",
            coupon_id,
            "--max-redemptions",
            "1",
            "--redeem-until",
            deadline.isoformat(),
            "--reason",
            "local acceptance",
        ],
        cwd=str(api_source),
        env=environment,
        capture_output=True,
        text=True,
        timeout=ISSUE_TIMEOUT,
        check=False,
    )
    require(result.returncode == 0, "acceptance_coupon_issue_failed")
    try:
        issued = json.loads(result.stdout)
    except ValueError:
        raise Failure("acceptance_coupon_issue_output_invalid") from None
    require(
        isinstance(issued, dict)
        and set(issued) == {"coupon_id", "code"}
        and issued["coupon_id"] == coupon_id
        and isinstance(issued["code"], str)
        and issued["code"],
        "acceptance_coupon_issue_output_invalid",
    )
    return coupon_id, issued["code"]


class Report:
    def __init__(self):
        self.checks = []

    def passed(self, name, **facts):
        self.checks.append({"check": name, "ok": True, **facts})


def summary(api, learner):
    status, body = api.call("GET", "/v1/billing/summary", token=learner.token)
    require(status == 200 and isinstance(body, dict), "acceptance_summary_unavailable")
    return body


def redeem(api, learner, code):
    status, body = api.call(
        "POST",
        "/v1/billing/plus-coupons/redeem",
        token=learner.token,
        body={"code": code},
    )
    return status, body


def run(config, *, http=None, connect=None, issue=issue_with_cli, cognito=None):
    env = config["environment"]
    require(
        env.get("PALS_ENV") == "local"
        and env.get("PALS_PLUS_COUPONS_ENABLED") == "true",
        "acceptance_local_coupon_environment_required",
    )
    api_base = loopback_origin(
        config["api_base_url"], "acceptance_loopback_api_required"
    )
    endpoint = loopback_origin(
        config["cognito_endpoint"], "acceptance_loopback_cognito_required"
    )
    database = Database(env["PALS_HOST_DATABASE_URL"], connect=connect)
    api = Api(api_base, http or Http())
    cognito = cognito or cognito_tool.CognitoClient(endpoint)
    client_id, pool_id = (
        env["PALS_COGNITO_APP_CLIENT_ID"],
        env["PALS_COGNITO_USER_POOL_ID"],
    )
    source = Path(config["api_source"])
    revision = bootstrap.coupon_source_contract(source)["api_source_revision"]
    report = Report()
    rejected = []

    def schema():
        try:
            return readiness.inspect_plus_coupons(
                env["PALS_HOST_DATABASE_URL"], source, revision, connect=connect
            )
        except ValueError as error:
            raise Failure("acceptance_" + str(error)) from None

    before = schema()
    frozen = config.get("frozen_fingerprint")
    if frozen is not None:
        require(
            frozen == before["plus_coupons_schema_fingerprint_sha256"],
            "acceptance_schema_differs_from_subject_freeze",
        )
    report.passed(
        "schema_acl_readback_after_api_start",
        matches_subject_freeze=None if frozen is None else True,
        schema_sha256=before["schema_sha256"],
        functions=len(before["functions"]),
        tables=len(before["tables"]),
    )
    require(api.call("GET", "/health")[0] == 200, "acceptance_api_health_failed")
    learners = [Learner(api, cognito, client_id, pool_id) for _ in range(2)]
    try:
        for learner in learners:
            learner.create()
            learner.login()
        first, second = learners
        report.passed("local_cognito_login", accounts=2)
        status, enabled = api.call(
            "GET", "/v1/billing/plus-coupons/status", token=first.token
        )
        require(
            status == 200 and enabled == {"enabled": True},
            "acceptance_coupon_status_not_enabled",
        )
        free = summary(api, first)
        require(
            free.get("billing_product_id") == "free" and free.get("period_end") is None,
            "acceptance_account_not_free_before_redemption",
        )
        project = {"name": "plus coupon acceptance"}
        denied = None
        if config["project_access"]:
            denied, body = api.call(
                "POST", "/v1/projects", token=first.token, body=project
            )
            require(
                denied == 403 and error_code(body) == "project_plan_required",
                "acceptance_project_not_denied_before_redemption",
            )
        report.passed(
            "free_before_redemption",
            project_create_status=denied,
        )

        operator_url = database.create_operator()
        coupons = [issue(config["api_python"], source, operator_url) for _ in range(2)]
        report.passed("coupons_issued_by_cli", count=len(coupons))
        (coupon_a, code_a), (coupon_b, code_b) = coupons
        stored = database.rows(
            "SELECT coupon_id::text,max_redemptions,duration_days,duration_months "
            "FROM pals_plus_coupons.codes WHERE coupon_id::text = ANY(%s) ORDER BY 1",
            ([coupon_a, coupon_b],),
        )
        require(
            sorted(stored) == sorted([(coupon_a, 1, None, 1), (coupon_b, 1, None, 1)]),
            "acceptance_issued_coupon_rows_differ",
        )

        status, body = redeem(api, first, code_a)
        require(status == 200 and isinstance(body, dict), "acceptance_redeem_failed")
        require(
            body.get("billing_product_id") == "plus"
            and body.get("billing_source") == "complimentary"
            and set(body)
            == {
                "billing_product_id",
                "billing_source",
                "grant_id",
                "starts_at",
                "expires_at",
            },
            "acceptance_redeem_response_differs",
        )
        starts, expires = parse_time(body["starts_at"]), parse_time(body["expires_at"])
        require(
            expires == add_one_utc_month(starts), "acceptance_period_not_one_utc_month"
        )
        rows = database.rows(
            "SELECT grant_id::text,coupon_id::text,starts_at,expires_at "
            "FROM pals_plus_coupons.redemptions WHERE owner_user_id=%s",
            (first.user_id,),
        )
        require(len(rows) == 1, "acceptance_redemption_row_count_differs")
        grant, stored_coupon, stored_start, stored_end = rows[0]
        require(
            grant == body["grant_id"]
            and stored_coupon == coupon_a
            and stored_start.astimezone(timezone.utc) == starts
            and stored_end.astimezone(timezone.utc) == expires,
            "acceptance_redemption_row_differs_from_response",
        )
        plus = summary(api, first)
        require(
            plus.get("billing_product_id") == "plus"
            and plus.get("billing_source") == "complimentary"
            and plus.get("entitlement_state") == "active"
            and plus.get("price") is None
            and isinstance(plus.get("period_end"), str)
            and parse_time(plus["period_end"]) == expires,
            "acceptance_summary_not_plus_after_redemption",
        )
        created = None
        if config["project_access"]:
            created, body = api.call(
                "POST", "/v1/projects", token=first.token, body=project
            )
            require(created == 201, "acceptance_project_not_allowed_after_redemption")
        report.passed(
            "redeemed_with_authentication",
            plus=True,
            one_utc_calendar_month=True,
            project_create_status=created,
        )

        for label, code in (("second_coupon", code_b), ("same_coupon_again", code_a)):
            status, body = redeem(api, first, code)
            require(
                status == 409
                and error_code(body) == "plus_coupon_existing_entitlement",
                "acceptance_second_redemption_not_refused:" + label,
            )
            rejected.append(status)
        counts = database.rows(
            "SELECT coupon_id::text,count(*) FROM pals_plus_coupons.redemptions "
            "WHERE coupon_id::text = ANY(%s) GROUP BY 1 ORDER BY 1",
            ([coupon_a, coupon_b],),
        )
        require(
            sorted(counts) == [(coupon_a, 1)]
            and database.rows(
                "SELECT count(*) FROM pals_plus_coupons.redemptions "
                "WHERE owner_user_id=%s",
                (first.user_id,),
            )
            == [(1,)],
            "acceptance_refused_redemption_changed_rows",
        )
        report.passed(
            "same_account_second_redemption_refused",
            http_statuses=rejected,
            coupon_b_unconsumed=True,
        )

        status, body = redeem(api, second, code_a)
        require(
            status == 422 and error_code(body) == "plus_coupon_invalid",
            "acceptance_used_coupon_not_single_use",
        )
        status, body = redeem(api, second, code_b)
        require(
            status == 200 and body.get("billing_product_id") == "plus",
            "acceptance_unconsumed_coupon_not_redeemable",
        )
        totals = database.rows(
            "SELECT count(*),count(DISTINCT owner_user_id),count(DISTINCT coupon_id) "
            "FROM pals_plus_coupons.redemptions WHERE coupon_id::text = ANY(%s)",
            ([coupon_a, coupon_b],),
        )
        require(totals == [(2, 2, 2)], "acceptance_single_use_rows_differ")
        report.passed("single_use", used_coupon_refused_for_other_account=True)

        first.login()
        reloaded = summary(api, first)
        require(
            reloaded.get("billing_product_id") == "plus"
            and reloaded.get("period_end") == plus.get("period_end"),
            "acceptance_plus_not_persisted_across_login",
        )
        require(
            database.rows(
                "SELECT grant_id::text FROM pals_plus_coupons.redemptions "
                "WHERE owner_user_id=%s",
                (first.user_id,),
            )
            == [(grant,)],
            "acceptance_grant_changed_across_login",
        )
        report.passed("persisted_across_new_login")
    finally:
        cleanup = []
        for name, step in (
            ("operator_role", database.drop_operator),
            *(("learner_" + str(i), x.delete) for i, x in enumerate(learners)),
        ):
            try:
                step()
            except Exception:  # noqa: BLE001 - reported by closed name only.
                cleanup.append(name)
        if cleanup:
            raise Failure("acceptance_cleanup_failed:" + ",".join(cleanup))
    after = schema()
    require(
        after["plus_coupons_schema_fingerprint_sha256"]
        == before["plus_coupons_schema_fingerprint_sha256"],
        "acceptance_schema_changed_during_acceptance",
    )
    report.passed("schema_acl_unchanged_after_acceptance")
    return {
        "state": "local_plus_coupon_acceptance_passed",
        "scope": (
            "local PostgreSQL 16, real API process over HTTP, local Cognito emulator; "
            "not production, not production Cognito, no model or provider call"
        ),
        "api_source_revision": revision,
        "plus_coupons_schema_fingerprint_sha256": before[
            "plus_coupons_schema_fingerprint_sha256"
        ],
        "coupons_issued": 2,
        "redemptions_succeeded": 2,
        "redemptions_refused": len(rejected) + 1,
        "failures": 0,
        "checks": report.checks,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-file", type=Path, required=True)
    parser.add_argument("--api-source", type=Path, required=True)
    parser.add_argument("--api-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--cognito-endpoint")
    parser.add_argument("--subject", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--no-project-access", action="store_true")
    args = parser.parse_args(argv)
    env = gate.private_env(args.environment_file)
    frozen = None
    if args.subject is not None:
        subject = json.loads(args.subject.read_text())
        frozen = subject.get("database_contract", {}).get(
            "plus_coupons_schema_fingerprint_sha256"
        )
        gate.need(frozen, "acceptance_subject_has_no_coupon_freeze")
    result = run(
        {
            "environment": env,
            "api_source": args.api_source.resolve(),
            "api_python": args.api_python,
            "api_base_url": args.api_base_url,
            "cognito_endpoint": args.cognito_endpoint
            or env.get("NEXT_PUBLIC_COGNITO_ENDPOINT")
            or "http://localhost:9229",
            "frozen_fingerprint": frozen,
            "project_access": not args.no_project_access,
        }
    )
    if args.result is not None:
        gate.private_json(args.result, result)
    print(gate.stable(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except gate.Refusal as error:
        print(gate.stable({"state": "refused", "code": str(error)}))
        raise SystemExit(1) from None
    except Exception as error:  # noqa: BLE001 - closed name only; never a message or value.
        print(
            gate.stable(
                {
                    "state": "refused",
                    "code": "acceptance_unexpected_error:" + type(error).__name__,
                }
            )
        )
        raise SystemExit(1) from None
