#!/usr/bin/env python3
"""Deterministic contract tests for PFI-009 before Docker is invoked."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "pals-scripts/continuity-pgvector-validation/run.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("continuity_pgvector_validation", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("PFI-009 runner module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_validation_inputs(fixture_root: Path) -> None:
    shutil.copytree(ROOT / "specs", fixture_root / "specs")
    shutil.copytree(ROOT / "pals-agent/specs", fixture_root / "pals-agent/specs")


class ContinuityPgvectorValidationContractTests(unittest.TestCase):
    def test_catalog_preflight_and_compose_contract(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()

        catalog = runner.validate_catalog(ROOT)
        self.assertEqual(catalog.sha256, "29f8a35e628d5aef2b40a1bb71582e87b3e5dc001024f8f9c39e0a3906ac49a7")
        self.assertEqual(len(catalog.cards), runner.EXPECTED_CARD_COUNT)
        self.assertTrue(
            {
                "cv1_add_continuity_at",
                "cv1_global_identity",
                "cv1_at_identity",
                "cv1_limit_constant_0",
                "cv1_sequence_constant_0",
            }.issubset({card["draft_id"] for card in catalog.cards})
        )
        runner.assert_compose_contract(ROOT)

    def test_child_parent_binding_mutations_reject_before_docker(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        child_path = "pals-agent/specs/continuity-draft-seed-pilot/requirements.md"
        parent_path = "specs/proof-flow-index/requirements.md"
        child_contents = (ROOT / child_path).read_text(encoding="utf-8")
        parent_pins = tuple(
            (key, runner._one_value(runner._frontmatter(child_contents), rf"^  {key}: ([0-9a-f]{{64}})$"))
            for key in ("requirements_sha256", "design_sha256", "tasks_sha256")
        )
        mutations = [
            (child_path, "status: approved", "status: draft"),
            (child_path, "path: specs/proof-flow-index", "path: specs/another-index"),
            (parent_path, "status: approved", "status: draft"),
        ]
        for key, value in parent_pins:
            mutations.append((child_path, f"{key}: {value}", f"{key}: {'0' * 64}"))
        for path_text, original, replacement in mutations:
            with self.subTest(path=path_text, original=original):
                with tempfile.TemporaryDirectory() as temp_dir:
                    fixture_root = Path(temp_dir)
                    copy_validation_inputs(fixture_root)
                    target = fixture_root / path_text
                    contents = target.read_text(encoding="utf-8")
                    self.assertIn(original, contents)
                    target.write_text(contents.replace(original, replacement, 1), encoding="utf-8")
                    with self.assertRaises(runner.ValidationError):
                        runner.validate_catalog(fixture_root)

    def test_catalog_mutations_reject_before_docker(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        original_hash = runner.validate_catalog(ROOT).sha256
        catalog_path = "pals-agent/specs/continuity-draft-seed-pilot/continuity-v1-catalog.json"
        child_path = "pals-agent/specs/continuity-draft-seed-pilot/requirements.md"
        for mutation in ("noncanonical", "duplicate", "count"):
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as temp_dir:
                    fixture_root = Path(temp_dir)
                    copy_validation_inputs(fixture_root)
                    catalog_file = fixture_root / catalog_path
                    decoded = json.loads(catalog_file.read_text(encoding="utf-8"))
                    if mutation == "noncanonical":
                        raw = json.dumps(decoded, ensure_ascii=False, sort_keys=True, separators=(",", ": ")).encode("utf-8")
                    else:
                        if mutation == "duplicate":
                            decoded["cards"][1]["draft_id"] = decoded["cards"][0]["draft_id"]
                        else:
                            decoded["cards"].pop()
                        raw = runner._canonical_json(decoded)
                    catalog_file.write_bytes(raw)
                    pinned_hash = hashlib.sha256(raw).hexdigest()
                    child_file = fixture_root / child_path
                    child_file.write_text(
                        child_file.read_text(encoding="utf-8").replace(original_hash, pinned_hash, 1),
                        encoding="utf-8",
                    )
                    with self.assertRaises(runner.ValidationError):
                        runner.validate_catalog(fixture_root)

    def test_compose_rejects_extra_service_or_environment(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        with tempfile.TemporaryDirectory() as temp_dir:
            fixture_root = Path(temp_dir)
            target = fixture_root / "pals-scripts/continuity-pgvector-validation"
            target.mkdir(parents=True)
            compose = target / "compose.yaml"
            compose.write_text(
                (ROOT / "pals-scripts/continuity-pgvector-validation/compose.yaml").read_text(encoding="utf-8")
                + "\n  unexpected:\n    image: pgvector/pgvector:pg16\n",
                encoding="utf-8",
            )
            with self.assertRaises(runner.ValidationError):
                runner.assert_compose_contract(fixture_root)

            compose.write_text(
                (ROOT / "pals-scripts/continuity-pgvector-validation/compose.yaml")
                .read_text(encoding="utf-8")
                .replace("    environment:\n", "    env_file: prohibited.env\n    environment:\n", 1),
                encoding="utf-8",
            )
            with self.assertRaises(runner.ValidationError):
                runner.assert_compose_contract(fixture_root)

            compose.write_text(
                (ROOT / "pals-scripts/continuity-pgvector-validation/compose.yaml")
                .read_text(encoding="utf-8")
                .replace(
                    "      POSTGRES_HOST_AUTH_METHOD: trust\n",
                    "      POSTGRES_HOST_AUTH_METHOD: trust\n      EXTRA: prohibited\n",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(runner.ValidationError):
                runner.assert_compose_contract(fixture_root)

    def test_deterministic_rows_are_valid_and_nonsemantic(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        rows = runner.build_rows(runner.validate_catalog(ROOT).cards)
        self.assertEqual(len(rows), runner.EXPECTED_CARD_COUNT)
        self.assertEqual({row.vector_kind for row in rows}, {"deterministic-test-v1"})
        self.assertEqual(len({row.source_sha256 for row in rows}), runner.EXPECTED_CARD_COUNT)
        self.assertEqual(len({row.vector_literal for row in rows}), runner.EXPECTED_CARD_COUNT)
        self.assertEqual(
            [(row.draft_id, row.source_sha256, row.vector_literal) for row in rows],
            [
                (row.draft_id, row.source_sha256, row.vector_literal)
                for row in runner.build_rows(runner.validate_catalog(ROOT).cards)
            ],
        )
        for row in rows:
            source = {key: row.card[key] for key in runner.SOURCE_KEYS}
            self.assertEqual(row.source_sha256, hashlib.sha256(runner._canonical_json(source)).hexdigest())
            self.assertEqual(len(row.vector_values), 3)
            self.assertTrue(all(value > 0.0 for value in row.vector_values))

    def test_cli_rejects_noncanonical_mode_without_docker(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        result = subprocess.run(
            ["python3", str(RUNNER_PATH), "validate", "--project=other"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage", result.stderr.lower())

    def test_psql_uses_the_fixture_trust_user(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="1\n", stderr="")
        with mock.patch.object(runner, "_docker", return_value=completed) as docker:
            self.assertEqual(runner._psql(ROOT, "SELECT 1;"), "1")
        command = docker.call_args.args[1]
        self.assertEqual(command[-2:], ["--username", "postgres"])

    def test_database_verification_binds_table_shape_and_full_row(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        row = runner.build_rows(runner.validate_catalog(ROOT).cards)[0]
        expected_columns = "\n".join(runner.EXPECTED_COLUMN_TYPES)
        responses = iter([runner.CATALOG_RELATION, expected_columns, "1", "1", row.draft_id])
        with mock.patch.object(runner, "_psql", side_effect=lambda _root, _sql: next(responses)) as psql:
            runner._verify_rows(ROOT, [row])
        row_query = psql.call_args_list[3].args[1]
        self.assertIn("canonical_statement =", row_query)
        self.assertIn("coverage =", row_query)
        self.assertIn("lean_target =", row_query)
        self.assertIn("sketch_steps =", row_query)
        self.assertIn(f"validation_vector = '{row.vector_literal}'::vector", row_query)

    def test_runtime_environment_is_an_exact_allowlist(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        allowed = [
            "GOSU_VERSION=1.19",
            "LANG=en_US.utf8",
            "PATH=/usr/local/bin",
            "PGDATA=/var/lib/postgresql/data",
            "PG_MAJOR=16",
            "PG_VERSION=16.9",
            "POSTGRES_DB=pals_continuity_validation",
            "POSTGRES_HOST_AUTH_METHOD=trust",
        ]
        runner._assert_runtime_environment(allowed)
        with self.assertRaises(runner.ValidationError):
            runner._assert_runtime_environment(allowed + ["EXTRA=prohibited"])

    def test_missing_local_image_rejects_without_a_pull(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        missing = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="missing")
        with mock.patch.object(runner.subprocess, "run", return_value=missing) as docker:
            with self.assertRaises(runner.ValidationError):
                runner._assert_local_image(ROOT)
        self.assertEqual(docker.call_args.args[0], ["docker", "image", "inspect", runner.IMAGE])

    def test_running_container_isolation_mutations_reject(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        environment = [
            "GOSU_VERSION=test",
            "LANG=test",
            "PATH=test",
            "PGDATA=/var/lib/postgresql/data",
            "PG_MAJOR=16",
            "PG_VERSION=test",
            "POSTGRES_DB=pals_continuity_validation",
            "POSTGRES_HOST_AUTH_METHOD=trust",
        ]
        base = {
            "Config": {
                "Labels": {"com.docker.compose.project": runner.PROJECT},
                "Image": runner.IMAGE,
                "Env": environment,
            },
            "HostConfig": {
                "NetworkMode": "none",
                "PortBindings": {},
                "Tmpfs": {"/var/lib/postgresql/data": ""},
            },
            "Mounts": [],
        }

        def assert_contract(container):
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps([container]), stderr="")
            with (
                mock.patch.object(runner, "_project_container_id", return_value="fixture"),
                mock.patch.object(runner.subprocess, "run", return_value=completed),
            ):
                runner._assert_running_container_contract(ROOT)

        assert_contract(base)
        mutations = (
            ("image", lambda item: item["Config"].__setitem__("Image", "other:image")),
            ("network", lambda item: item["HostConfig"].__setitem__("NetworkMode", "bridge")),
            ("port", lambda item: item["HostConfig"].__setitem__("PortBindings", {"5432/tcp": [{}]})),
            ("tmpfs", lambda item: item["HostConfig"].__setitem__("Tmpfs", {})),
            ("mount", lambda item: item.__setitem__("Mounts", [{"Type": "volume"}])),
        )
        for name, mutate in mutations:
            with self.subTest(mutation=name):
                container = copy.deepcopy(base)
                mutate(container)
                with self.assertRaises(runner.ValidationError):
                    assert_contract(container)

    def test_invalid_validation_vectors_reject(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        cards = runner.validate_catalog(ROOT).cards

        with mock.patch.object(runner, "_vector_from_source_hash", return_value=((0.0, 1.0, 1.0), "[0,1,1]")):
            with self.assertRaises(runner.ValidationError):
                runner.build_rows(cards)

        duplicate_vectors = [((1.0, 2.0, 3.0), "[1,2,3]")] * len(cards)
        with mock.patch.object(runner, "_vector_from_source_hash", side_effect=duplicate_vectors):
            with self.assertRaises(runner.ValidationError):
                runner.build_rows(cards)

        collinear_vectors = [
            ((1.0, 1.0, 1.0), "[1,1,1]"),
            ((2.0, 2.0, 2.0), "[2,2,2]"),
        ] + [
            ((float(index), float(index + 1), float(index + 3)), f"[{index},{index + 1},{index + 3}]")
            for index in range(3, len(cards) + 1)
        ]
        with mock.patch.object(runner, "_vector_from_source_hash", side_effect=collinear_vectors):
            with self.assertRaises(runner.ValidationError):
                runner.build_rows(cards)

    def test_validate_cleans_up_after_failed_start_and_before_reload(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        catalog = runner.Catalog("a" * 64, [])
        failed_start = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
        with (
            mock.patch.object(runner, "validate_catalog", return_value=catalog),
            mock.patch.object(runner, "build_rows", return_value=[]),
            mock.patch.object(runner, "assert_compose_contract"),
            mock.patch.object(runner, "_assert_local_image"),
            mock.patch.object(runner, "teardown") as teardown,
            mock.patch.object(runner, "_docker", return_value=failed_start),
        ):
            with self.assertRaises(runner.ValidationError):
                runner.validate(ROOT)
        self.assertEqual(teardown.call_count, 2)

    def test_teardown_requires_no_remaining_project_container(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(runner, "assert_compose_contract"),
            mock.patch.object(runner, "_project_container_ids", side_effect=[["one"], []]),
            mock.patch.object(runner, "_assert_project_labels") as labels,
            mock.patch.object(runner, "_docker", return_value=completed),
        ):
            runner.teardown(ROOT)
        labels.assert_called_once_with(ROOT, ["one"])

    def test_teardown_remains_available_after_input_drift(self) -> None:
        self.assertTrue(RUNNER_PATH.is_file(), "PFI-009 runner must exist")
        runner = load_runner()
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(runner, "validate_catalog", side_effect=AssertionError("must not read catalog")),
            mock.patch.object(runner, "_assert_local_image", side_effect=AssertionError("must not inspect image")),
            mock.patch.object(runner, "_project_container_ids", side_effect=[[], []]),
            mock.patch.object(runner, "_docker", return_value=completed),
        ):
            runner.teardown(ROOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
