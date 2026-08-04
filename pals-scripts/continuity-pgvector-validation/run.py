#!/usr/bin/env python3
"""PFI-009 detached local pgvector plumbing validation."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable


PROJECT = "pals-continuity-pgvector-validation"
IMAGE = "pgvector/pgvector:pg16"
DATABASE = "pals_continuity_validation"
VECTOR_KIND = "deterministic-test-v1"
CATALOG_RELATION = "continuity_validation_cards"
EXPECTED_COLUMN_TYPES = (
    "draft_id:text",
    "canonical_statement:text",
    "coverage:jsonb",
    "coverage_objective:text",
    "english_expected_draft_id:text",
    "english_query:text",
    "hard_negative_expected_result:text",
    "hard_negative_query:text",
    "japanese_expected_draft_id:text",
    "japanese_query:text",
    "lean_target:text",
    "novelty_key:text",
    "openmath_xml:text",
    "proof_strategy:text",
    "sketch_steps:jsonb",
    "source_sha256:text",
    "vector_kind:text",
    "validation_vector:vector(3)",
)
CATALOG_PATH = Path("pals-agent/specs/continuity-draft-seed-pilot/continuity-v1-catalog.json")
CHILD_REQUIREMENTS_PATH = Path("pals-agent/specs/continuity-draft-seed-pilot/requirements.md")
PARENT_PATH = Path("specs/proof-flow-index")
PARENT_FILES = ("requirements.md", "design.md", "tasks.md")
EXPECTED_CARD_COUNT = 110
CARD_TEXT_COLUMNS = (
    "draft_id",
    "canonical_statement",
    "coverage_objective",
    "english_expected_draft_id",
    "english_query",
    "hard_negative_expected_result",
    "hard_negative_query",
    "japanese_expected_draft_id",
    "japanese_query",
    "lean_target",
    "novelty_key",
    "openmath_xml",
    "proof_strategy",
)
CARD_JSON_COLUMNS = ("coverage", "sketch_steps")
CARD_KEYS = set(CARD_TEXT_COLUMNS + CARD_JSON_COLUMNS)
SOURCE_KEYS = tuple(sorted(CARD_KEYS))
ALLOWED_CONTAINER_ENVIRONMENT_NAMES = {
    "GOSU_VERSION",
    "LANG",
    "PATH",
    "PGDATA",
    "PG_MAJOR",
    "PG_VERSION",
    "POSTGRES_DB",
    "POSTGRES_HOST_AUTH_METHOD",
}
EXPECTED_COMPOSE_TEXT = """name: pals-continuity-pgvector-validation

services:
  postgres:
    image: pgvector/pgvector:pg16
    pull_policy: never
    environment:
      POSTGRES_DB: pals_continuity_validation
      POSTGRES_HOST_AUTH_METHOD: trust
    network_mode: none
    tmpfs:
      - /var/lib/postgresql/data
"""


class ValidationError(RuntimeError):
    """A closed PFI-009 validation failure without content output."""


class Catalog:
    def __init__(self, sha256: str, cards: list[dict[str, Any]]) -> None:
        self.sha256 = sha256
        self.cards = cards


class ValidationRow:
    def __init__(
        self,
        card: dict[str, Any],
        source_sha256: str,
        vector_values: tuple[float, float, float],
        vector_literal: str,
    ) -> None:
        self.card = card
        self.draft_id = card["draft_id"]
        self.source_sha256 = source_sha256
        self.vector_values = vector_values
        self.vector_literal = vector_literal
        self.vector_kind = VECTOR_KIND


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def compose_path(root: Path) -> Path:
    return root / "pals-scripts/continuity-pgvector-validation/compose.yaml"


def _read_utf8(path: Path) -> tuple[bytes, str]:
    try:
        raw = path.read_bytes()
        return raw, raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValidationError("required local validation input is unreadable") from error


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise ValidationError("required local validation input is unreadable") from error


def _frontmatter(text: str) -> str:
    match = re.fullmatch(r"---\n(.*?)\n---\n.*", text, re.DOTALL)
    if match is None:
        raise ValidationError("spec frontmatter is invalid")
    return match.group(1)


def _one_value(frontmatter: str, expression: str) -> str:
    values = re.findall(expression, frontmatter, flags=re.MULTILINE)
    if len(values) != 1:
        raise ValidationError("spec frontmatter field is invalid")
    return values[0]


def _mapping_block(frontmatter: str, name: str) -> str:
    match = re.search(
        rf"^{re.escape(name)}:\n((?:  [^\n]+(?:\n|$))*)(?=^[^ ]|\Z)",
        frontmatter,
        flags=re.MULTILINE,
    )
    if match is None or not match.group(1):
        raise ValidationError("spec frontmatter mapping is invalid")
    return match.group(1)


def _validate_parent_binding(root: Path, child_frontmatter: str) -> None:
    parent_spec = _mapping_block(child_frontmatter, "parent_spec")
    parent_path = _one_value(parent_spec, r"^  path: ([^\n]+)$")
    if parent_path != str(PARENT_PATH):
        raise ValidationError("parent path mismatch")
    parent = root / PARENT_PATH
    for filename in PARENT_FILES:
        expected = _one_value(parent_spec, rf"^  {filename[:-3]}_sha256: ([0-9a-f]{{64}})$")
        if _sha256_file(parent / filename) != expected:
            raise ValidationError("parent hash mismatch")
    _, parent_requirements = _read_utf8(parent / "requirements.md")
    if _one_value(_frontmatter(parent_requirements), r"^status: ([a-z]+)$") != "approved":
        raise ValidationError("parent status is not approved")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def validate_catalog(root: Path) -> Catalog:
    child_raw, child_requirements = _read_utf8(root / CHILD_REQUIREMENTS_PATH)
    if b"\n" in child_raw and not child_raw.endswith(b"\n"):
        raise ValidationError("child requirements encoding is invalid")
    child_frontmatter = _frontmatter(child_requirements)
    if _one_value(child_frontmatter, r"^status: ([a-z]+)$") != "approved":
        raise ValidationError("child status is not approved")
    _validate_parent_binding(root, child_frontmatter)

    catalog_raw, catalog_text = _read_utf8(root / CATALOG_PATH)
    if b"\n" in catalog_raw:
        raise ValidationError("catalog must be no-LF JCS")
    companion = _mapping_block(child_frontmatter, "catalog_companion")
    expected_catalog_path = _one_value(companion, r"^  path: ([^\n]+)$")
    if expected_catalog_path != str(CATALOG_PATH):
        raise ValidationError("catalog path mismatch")
    expected_digest = _one_value(companion, r"^  sha256: ([0-9a-f]{64})$")
    actual_digest = hashlib.sha256(catalog_raw).hexdigest()
    if actual_digest != expected_digest:
        raise ValidationError("catalog hash mismatch")
    try:
        decoded = json.loads(catalog_text)
    except json.JSONDecodeError as error:
        raise ValidationError("catalog JSON is invalid") from error
    if _canonical_json(decoded) != catalog_raw:
        raise ValidationError("catalog is not canonical JCS")
    if not isinstance(decoded, dict) or set(decoded) != {"schema_version", "coverage_profile", "cards"}:
        raise ValidationError("catalog schema is invalid")
    cards = decoded["cards"]
    if decoded["schema_version"] != "pals.continuity-draft-catalog.v2" or not isinstance(cards, list):
        raise ValidationError("catalog schema is invalid")
    coverage_profile = decoded["coverage_profile"]
    if (
        not isinstance(coverage_profile, dict)
        or set(coverage_profile) != {"schema_version", "required_signatures"}
        or coverage_profile["schema_version"] != "pals.continuity-coverage-profile.v1"
        or not isinstance(coverage_profile["required_signatures"], list)
        or not coverage_profile["required_signatures"]
    ):
        raise ValidationError("catalog coverage profile is invalid")
    if len(cards) != EXPECTED_CARD_COUNT:
        raise ValidationError("catalog card count mismatch")
    for card in cards:
        if not isinstance(card, dict) or set(card) != CARD_KEYS:
            raise ValidationError("catalog card schema is invalid")
        if not all(isinstance(card[key], str) and card[key] for key in CARD_TEXT_COLUMNS):
            raise ValidationError("catalog card field is invalid")
        if not isinstance(card["coverage"], dict) or not card["coverage"]:
            raise ValidationError("catalog coverage is invalid")
        if not isinstance(card["sketch_steps"], list) or not all(
            isinstance(step, str) for step in card["sketch_steps"]
        ) or not card["sketch_steps"]:
            raise ValidationError("catalog sketch steps are invalid")
    ids = tuple(card["draft_id"] for card in cards)
    if (
        ids != tuple(sorted(ids))
        or len(set(ids)) != len(ids)
        or any(not draft_id.startswith("cv1_") for draft_id in ids)
        or any(card["english_expected_draft_id"] != card["draft_id"] for card in cards)
        or any(card["japanese_expected_draft_id"] != card["draft_id"] for card in cards)
        or any(card["hard_negative_expected_result"] != "no_match" for card in cards)
    ):
        raise ValidationError("catalog IDs are invalid")
    return Catalog(actual_digest, cards)


def _round_fraction_to_even(numerator: int, denominator: int) -> int:
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = remainder * 2
    if twice_remainder > denominator or (twice_remainder == denominator and quotient % 2 == 1):
        return quotient + 1
    return quotient


def _f32_bits_from_fraction(numerator: int, denominator: int) -> int:
    if numerator <= 0 or denominator <= 0:
        raise ValidationError("validation vector component is invalid")
    exponent = 0
    while numerator >= denominator * (1 << (exponent + 1)):
        exponent += 1
    while exponent > 0 and numerator < denominator * (1 << exponent):
        exponent -= 1
    scale = 23 - exponent
    if scale >= 0:
        significand = _round_fraction_to_even(numerator << scale, denominator)
    else:
        significand = _round_fraction_to_even(numerator, denominator << (-scale))
    if significand == 1 << 24:
        exponent += 1
        significand = 1 << 23
    if not (0 <= exponent <= 1 and (1 << 23) <= significand < (1 << 24)):
        raise ValidationError("validation vector component is outside the supported range")
    return ((exponent + 127) << 23) | (significand - (1 << 23))


def _vector_from_source_hash(source_hash: str) -> tuple[tuple[float, float, float], str]:
    digest = bytes.fromhex(source_hash)
    values: list[float] = []
    parts: list[str] = []
    for offset in range(0, 6, 2):
        unsigned = int.from_bytes(digest[offset : offset + 2], "big")
        bits = _f32_bits_from_fraction(65536 + unsigned, 65535)
        value = struct.unpack("!f", struct.pack("!I", bits))[0]
        if not math.isfinite(value) or value <= 0.0:
            raise ValidationError("validation vector component is invalid")
        values.append(value)
        parts.append(format(value, ".9g"))
    return (values[0], values[1], values[2]), "[" + ",".join(parts) + "]"


def _is_collinear(left: tuple[float, float, float], right: tuple[float, float, float]) -> bool:
    return (
        left[0] * right[1] == left[1] * right[0]
        and left[0] * right[2] == left[2] * right[0]
        and left[1] * right[2] == left[2] * right[1]
    )


def build_rows(cards: Iterable[dict[str, Any]]) -> list[ValidationRow]:
    rows: list[ValidationRow] = []
    for card in cards:
        source = {key: card[key] for key in SOURCE_KEYS}
        source_sha256 = hashlib.sha256(_canonical_json(source)).hexdigest()
        vector_values, vector_literal = _vector_from_source_hash(source_sha256)
        rows.append(
            ValidationRow(
                card=card,
                source_sha256=source_sha256,
                vector_values=vector_values,
                vector_literal=vector_literal,
            )
        )
    if len(rows) != EXPECTED_CARD_COUNT:
        raise ValidationError("validation row count mismatch")
    if len({row.source_sha256 for row in rows}) != len(rows):
        raise ValidationError("duplicate validation source hash")
    if len({row.vector_literal for row in rows}) != len(rows):
        raise ValidationError("duplicate validation vector")
    for index, row in enumerate(rows):
        if not all(math.isfinite(value) and value != 0.0 for value in row.vector_values):
            raise ValidationError("invalid validation vector component")
        if not math.isfinite(math.sqrt(sum(value * value for value in row.vector_values))):
            raise ValidationError("non-finite validation vector norm")
        for other in rows[index + 1 :]:
            if _is_collinear(row.vector_values, other.vector_values):
                raise ValidationError("collinear validation vector")
    return rows


def assert_compose_contract(root: Path) -> None:
    raw, text = _read_utf8(compose_path(root))
    if raw != EXPECTED_COMPOSE_TEXT.encode("utf-8") or text != EXPECTED_COMPOSE_TEXT:
        raise ValidationError("Compose fixture contract mismatch")


def _docker(root: Path, args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "--project-name", PROJECT, "--file", str(compose_path(root)), *args]
    return subprocess.run(
        command,
        cwd=root,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _require_success(result: subprocess.CompletedProcess[str], message: str) -> str:
    if result.returncode != 0:
        raise ValidationError(message)
    return result.stdout.strip()


def _assert_local_image(root: Path) -> None:
    result = subprocess.run(
        ["docker", "image", "inspect", IMAGE],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    _require_success(result, "required local pgvector image is unavailable")


def _project_container_id(root: Path) -> str:
    identifier = _require_success(_docker(root, ["ps", "--quiet", "postgres"]), "fixture container is unavailable")
    if not identifier or "\n" in identifier:
        raise ValidationError("fixture container identity is invalid")
    return identifier


def _assert_running_container_contract(root: Path) -> None:
    identifier = _project_container_id(root)
    result = subprocess.run(
        ["docker", "inspect", identifier],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    inspect_data = json.loads(_require_success(result, "fixture inspection failed"))
    if not isinstance(inspect_data, list) or len(inspect_data) != 1:
        raise ValidationError("fixture inspection is invalid")
    container = inspect_data[0]
    labels = container.get("Config", {}).get("Labels", {})
    image = container.get("Config", {}).get("Image")
    host_config = container.get("HostConfig", {})
    mounts = container.get("Mounts", [])
    environment = container.get("Config", {}).get("Env", [])
    if labels.get("com.docker.compose.project") != PROJECT:
        raise ValidationError("fixture project label mismatch")
    if image != IMAGE:
        raise ValidationError("fixture image contract mismatch")
    if host_config.get("NetworkMode") != "none" or host_config.get("PortBindings"):
        raise ValidationError("fixture network contract mismatch")
    if "/var/lib/postgresql/data" not in (host_config.get("Tmpfs") or {}):
        raise ValidationError("fixture tmpfs contract mismatch")
    if mounts:
        raise ValidationError("fixture volume contract mismatch")
    _assert_runtime_environment(environment)


def _assert_runtime_environment(environment: Any) -> None:
    if not isinstance(environment, list) or not all(isinstance(value, str) and "=" in value for value in environment):
        raise ValidationError("fixture environment contract mismatch")
    names = {value.partition("=")[0] for value in environment}
    if names != ALLOWED_CONTAINER_ENVIRONMENT_NAMES:
        raise ValidationError("fixture environment contract mismatch")
    if "POSTGRES_DB=pals_continuity_validation" not in environment or "POSTGRES_HOST_AUTH_METHOD=trust" not in environment:
        raise ValidationError("fixture environment contract mismatch")


def _wait_for_postgres(root: Path) -> None:
    for _ in range(120):
        result = _docker(root, ["exec", "-T", "postgres", "pg_isready", "-U", "postgres", "-d", DATABASE])
        if result.returncode == 0:
            return
        time.sleep(0.25)
    raise ValidationError("fixture PostgreSQL did not become ready")


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _sql_json(value: Any) -> str:
    return _sql_literal(json.dumps(value, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"


def _seed_sql(rows: list[ValidationRow]) -> str:
    values = []
    for row in rows:
        card_values = []
        for column in CARD_TEXT_COLUMNS:
            card_values.append(_sql_literal(row.card[column]))
        for column in CARD_JSON_COLUMNS:
            card_values.append(_sql_json(row.card[column]))
        values.append(
            "(" + ",".join(
                tuple(card_values)
                + (
                    _sql_literal(row.source_sha256),
                    _sql_literal(row.vector_kind),
                    _sql_literal(row.vector_literal) + "::vector",
                )
            ) + ")"
        )
    return "\n".join(
        (
            "BEGIN;",
            "CREATE EXTENSION IF NOT EXISTS vector;",
            f"CREATE TABLE {CATALOG_RELATION} ("
            "draft_id text PRIMARY KEY, canonical_statement text NOT NULL, coverage jsonb NOT NULL, "
            "coverage_objective text NOT NULL, "
            "english_expected_draft_id text NOT NULL, english_query text NOT NULL, "
            "hard_negative_expected_result text NOT NULL, hard_negative_query text NOT NULL, "
            "japanese_expected_draft_id text NOT NULL, japanese_query text NOT NULL, lean_target text NOT NULL, "
            "novelty_key text NOT NULL, openmath_xml text NOT NULL, proof_strategy text NOT NULL, "
            "sketch_steps jsonb NOT NULL, source_sha256 text NOT NULL "
            "CHECK (source_sha256 ~ '^[0-9a-f]{64}$'), vector_kind text NOT NULL "
            f"CHECK (vector_kind = '{VECTOR_KIND}'), validation_vector vector(3) NOT NULL);",
            f"INSERT INTO {CATALOG_RELATION} "
            "(draft_id,canonical_statement,coverage_objective,english_expected_draft_id,english_query,"
            "hard_negative_expected_result,hard_negative_query,japanese_expected_draft_id,japanese_query,"
            "lean_target,novelty_key,openmath_xml,proof_strategy,coverage,sketch_steps,source_sha256,"
            "vector_kind,validation_vector) VALUES\n"
            + ",\n".join(values)
            + ";",
            "COMMIT;",
        )
    ) + "\n"


def _psql(root: Path, sql: str) -> str:
    return _require_success(
        _docker(
            root,
            [
                "exec",
                "-T",
                "postgres",
                "psql",
                "--set=ON_ERROR_STOP=1",
                "--tuples-only",
                "--no-align",
                "--dbname",
                DATABASE,
                "--username",
                "postgres",
            ],
            input_text=sql,
        ),
        "fixture SQL validation failed",
    )


def _verify_rows(root: Path, rows: list[ValidationRow]) -> None:
    tables = _psql(
        root,
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;",
    )
    if tables != CATALOG_RELATION:
        raise ValidationError("fixture relation contract mismatch")
    column_types = _psql(
        root,
        "SELECT attname || ':' || format_type(atttypid, atttypmod) "
        f"FROM pg_attribute WHERE attrelid = 'public.{CATALOG_RELATION}'::regclass "
        "AND attnum > 0 AND NOT attisdropped ORDER BY attnum;",
    )
    if tuple(column_types.splitlines()) != EXPECTED_COLUMN_TYPES:
        raise ValidationError("fixture column contract mismatch")
    count = _psql(root, f"SELECT count(*) FROM {CATALOG_RELATION};")
    if count != str(len(rows)):
        raise ValidationError("fixture row count mismatch")
    for row in rows:
        predicates = []
        for column in CARD_TEXT_COLUMNS:
            predicates.append(f"{column} = {_sql_literal(row.card[column])}")
        for column in CARD_JSON_COLUMNS:
            predicates.append(f"{column} = {_sql_json(row.card[column])}")
        predicates.extend(
            (
                f"source_sha256 = {_sql_literal(row.source_sha256)}",
                f"vector_kind = {_sql_literal(row.vector_kind)}",
                f"validation_vector = {_sql_literal(row.vector_literal)}::vector",
            )
        )
        exact_match = _psql(
            root,
            f"SELECT count(*) FROM {CATALOG_RELATION} WHERE " + " AND ".join(predicates) + ";",
        )
        if exact_match != "1":
            raise ValidationError("fixture row content mismatch")
        nearest = _psql(
            root,
            f"WITH q AS (SELECT validation_vector FROM {CATALOG_RELATION} "
            f"WHERE draft_id = {_sql_literal(row.draft_id)}) "
            f"SELECT draft_id FROM {CATALOG_RELATION} "
            f"ORDER BY validation_vector <=> (SELECT validation_vector FROM q), draft_id LIMIT 1;",
        )
        if nearest != row.draft_id:
            raise ValidationError("fixture self nearest-neighbour check failed")


def _project_container_ids(root: Path) -> list[str]:
    identifiers = subprocess.run(
        ["docker", "ps", "--all", "--quiet", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    _require_success(identifiers, "fixture project lookup failed")
    return list(filter(None, identifiers.stdout.splitlines()))


def _assert_project_labels(root: Path, identifiers: Iterable[str]) -> None:
    for identifier in identifiers:
        inspected = subprocess.run(
            ["docker", "inspect", "--format", "{{ index .Config.Labels \"com.docker.compose.project\" }}", identifier],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if _require_success(inspected, "fixture project inspection failed").strip() != PROJECT:
            raise ValidationError("fixture project label mismatch")


def teardown(root: Path) -> None:
    assert_compose_contract(root)
    _assert_project_labels(root, _project_container_ids(root))
    _require_success(_docker(root, ["down", "--volumes", "--remove-orphans"]), "fixture teardown failed")
    remaining = _project_container_ids(root)
    if remaining:
        raise ValidationError("fixture teardown left project containers")


def validate(root: Path) -> None:
    catalog = validate_catalog(root)
    rows = build_rows(catalog.cards)
    assert_compose_contract(root)
    _assert_local_image(root)
    start_attempted = False
    try:
        teardown(root)
        start_attempted = True
        _require_success(_docker(root, ["up", "--detach", "--pull", "never", "postgres"]), "fixture startup failed")
        _assert_running_container_contract(root)
        _wait_for_postgres(root)
        _psql(root, _seed_sql(rows))
        _verify_rows(root, rows)
    except Exception:
        if start_attempted:
            try:
                teardown(root)
            except ValidationError as cleanup_error:
                raise ValidationError("fixture validation cleanup failed") from cleanup_error
        raise
    print("PFI-009 local pgvector validation: PASS")
    print(f"project={PROJECT}")
    print(f"catalog_sha256_prefix={catalog.sha256[:12]}")
    print(f"card_count={len(rows)}")
    print("card_ids=" + ",".join(row.draft_id for row in rows))
    print(f"vector_kind={VECTOR_KIND}")
    print(f"self_nearest_neighbour={len(rows)}/{len(rows)}")
    print("teardown_status=available")


def main(arguments: list[str]) -> int:
    if arguments not in (["validate"], ["teardown"]):
        print("usage: run.py {validate|teardown}", file=sys.stderr)
        return 2
    try:
        if arguments[0] == "validate":
            validate(repository_root())
        else:
            teardown(repository_root())
    except ValidationError as error:
        print(f"PFI-009 local pgvector validation: FAIL: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError):
        print("PFI-009 local pgvector validation: FAIL: local fixture command failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
