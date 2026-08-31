#!/usr/bin/env python3
"""Audit Draft coverage without changing Draft records or database state.

This command intentionally separates repository authoring evidence, loader support,
packaged build input, database publication, and runtime verification.  The database
states remain ``not_checked`` until the read-only adapter in DCE-T003 is implemented.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = "pals.draft-catalog-coverage-matrix.v1"
REPORT_VERSION = "pals.draft-catalog-coverage-audit.v1"
GENERIC_PFI_POPULATION_LIMIT = 4096
ID_PATTERN = re.compile(r"^[a-z][a-z0-9._-]{0,127}$")
MAX_JSON_BYTES = 32 * 1024 * 1024

ROOT_KEYS = frozenset(
    {
        "schema_version",
        "stages",
        "courses",
        "domains",
        "modes",
        "difficulties",
        "profile_requirements",
        "scopes",
    }
)
REGISTRY_KEYS = frozenset({"id", "description"})
STAGE_KEYS = frozenset({"id", "description", "course_id", "domain_ids"})
PROFILE_KEYS = frozenset({"id", "status", "profile_ids", "notes"})
REFERENCE_KEYS = frozenset({"kind", "title", "url", "revision"})
STAGE_REFERENCE_KEYS = frozenset({"stage", "url", "section"})
DEFAULT_KEYS = frozenset({"required_modes", "required_difficulties"})
AXIS_KEYS = frozenset({"id", "minimum_distinct_patterns"})
FAMILY_KEYS = frozenset(
    {
        "id",
        "title",
        "stage",
        "prerequisites",
        "profile_requirement",
        "required_modes",
        "required_difficulties",
        "draft_bindings",
    }
)
BINDING_KEYS = frozenset(
    {
        "draft_id",
        "primary_mode",
        "difficulty",
        "authoring_manifest",
        "admission_manifest",
    }
)
COVERAGE_SCOPE_KEYS = frozenset(
    {
        "id",
        "kind",
        "reference",
        "stage_references",
        "defaults",
        "families",
        "can_report_comprehensive",
    }
)
TARGET_SCOPE_KEYS = frozenset(
    {
        "id",
        "kind",
        "reference",
        "target_groups",
        "can_report_comprehensive",
        "refinement_required",
    }
)
TARGET_GROUP_KEYS = frozenset(
    {"id", "title", "target_distinct_patterns", "prerequisites", "profile_requirement"}
)
SOURCE_ROOT_KEYS = frozenset({"schema_version", "sources", "profile_limits"})
SOURCE_KEYS = frozenset(
    {
        "id",
        "path",
        "kind",
        "schema_version",
        "card_keys",
        "profile_id",
        "status_ceiling",
        "loader_supported",
    }
)
PROFILE_LIMIT_KEYS = frozenset(
    {
        "profile_id",
        "configured_population_limit",
        "available_population_limit",
        "source",
    }
)


class CoverageAuditError(ValueError):
    """Raised when the coverage contract or an explicitly inventoried artifact is invalid."""


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise CoverageAuditError(f"{path} must be an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise CoverageAuditError(f"{path} must be an array")
    return value


def _closed(
    value: Mapping[str, Any],
    allowed: frozenset[str],
    required: frozenset[str],
    path: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise CoverageAuditError(f"{path} has unknown keys: {', '.join(unknown)}")
    if missing:
        raise CoverageAuditError(f"{path} is missing keys: {', '.join(missing)}")


def _identifier(value: Any, path: str) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        raise CoverageAuditError(f"{path} must be a stable identifier")
    return value


def _nonblank(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageAuditError(f"{path} must be a nonblank string")
    return value


def _uri(value: Any, path: str) -> str:
    text = _nonblank(value, path)
    if not urlparse(text).scheme:
        raise CoverageAuditError(f"{path} must be an absolute URI")
    return text


def _unique(values: Iterable[str], path: str) -> list[str]:
    items = list(values)
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise CoverageAuditError(
            f"{path} has duplicate identifiers: {', '.join(duplicates)}"
        )
    return items


def _validate_reference(value: Any, path: str) -> None:
    item = _mapping(value, path)
    _closed(item, REFERENCE_KEYS, REFERENCE_KEYS, path)
    if item["kind"] not in {"official_curriculum", "reference_coverage_map"}:
        raise CoverageAuditError(f"{path}.kind is unsupported")
    _nonblank(item["title"], f"{path}.title")
    _uri(item["url"], f"{path}.url")
    _nonblank(item["revision"], f"{path}.revision")


def _validate_axis(
    value: Any,
    path: str,
    registry: set[str],
) -> list[Mapping[str, Any]]:
    raw = _list(value, path)
    if not raw:
        raise CoverageAuditError(f"{path} must not be empty")
    result: list[Mapping[str, Any]] = []
    ids: list[str] = []
    for index, entry in enumerate(raw):
        entry_path = f"{path}[{index}]"
        item = _mapping(entry, entry_path)
        _closed(item, AXIS_KEYS, AXIS_KEYS, entry_path)
        identifier = _identifier(item["id"], f"{entry_path}.id")
        if identifier not in registry:
            raise CoverageAuditError(
                f"{entry_path}.id references unknown registry item {identifier}"
            )
        minimum = item["minimum_distinct_patterns"]
        if (
            not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or not 1 <= minimum <= 64
        ):
            raise CoverageAuditError(
                f"{entry_path}.minimum_distinct_patterns must be an integer from 1 through 64"
            )
        ids.append(identifier)
        result.append(item)
    _unique(ids, path)
    return result


def _validate_binding(
    value: Any,
    path: str,
    modes: set[str],
    difficulties: set[str],
) -> Mapping[str, Any]:
    item = _mapping(value, path)
    _closed(item, BINDING_KEYS, BINDING_KEYS, path)
    _identifier(item["draft_id"], f"{path}.draft_id")
    mode = _identifier(item["primary_mode"], f"{path}.primary_mode")
    difficulty = _identifier(item["difficulty"], f"{path}.difficulty")
    if mode not in modes:
        raise CoverageAuditError(
            f"{path}.primary_mode {mode} is not required by its family"
        )
    if difficulty not in difficulties:
        raise CoverageAuditError(
            f"{path}.difficulty {difficulty} is not required by its family"
        )
    _nonblank(item["authoring_manifest"], f"{path}.authoring_manifest")
    if item["admission_manifest"] is not None:
        _nonblank(item["admission_manifest"], f"{path}.admission_manifest")
    return item


def validate_matrix(payload: Any) -> dict[str, Any]:
    """Validate the closed matrix contract and return derived semantic data."""

    root = _mapping(payload, "matrix")
    _closed(root, ROOT_KEYS, ROOT_KEYS, "matrix")
    if root["schema_version"] != SCHEMA_VERSION:
        raise CoverageAuditError("matrix.schema_version is unsupported")

    registries: dict[str, set[str]] = {}
    for key in ("courses", "domains", "modes", "difficulties"):
        identifiers: list[str] = []
        for index, entry in enumerate(_list(root[key], f"matrix.{key}")):
            path = f"matrix.{key}[{index}]"
            item = _mapping(entry, path)
            _closed(item, REGISTRY_KEYS, REGISTRY_KEYS, path)
            identifiers.append(_identifier(item["id"], f"{path}.id"))
            _nonblank(item["description"], f"{path}.description")
        if not identifiers:
            raise CoverageAuditError(f"matrix.{key} must not be empty")
        registries[key] = set(_unique(identifiers, f"matrix.{key}"))

    stage_ids: list[str] = []
    for index, entry in enumerate(_list(root["stages"], "matrix.stages")):
        path = f"matrix.stages[{index}]"
        item = _mapping(entry, path)
        _closed(item, STAGE_KEYS, STAGE_KEYS, path)
        stage_id = _identifier(item["id"], f"{path}.id")
        _nonblank(item["description"], f"{path}.description")
        course_id = _identifier(item["course_id"], f"{path}.course_id")
        if course_id not in registries["courses"]:
            raise CoverageAuditError(f"{path}.course_id references unknown {course_id}")
        domain_ids = [
            _identifier(value, f"{path}.domain_ids[{domain_index}]")
            for domain_index, value in enumerate(
                _list(item["domain_ids"], f"{path}.domain_ids")
            )
        ]
        if not domain_ids:
            raise CoverageAuditError(f"{path}.domain_ids must not be empty")
        _unique(domain_ids, f"{path}.domain_ids")
        unknown_domains = sorted(set(domain_ids) - registries["domains"])
        if unknown_domains:
            raise CoverageAuditError(
                f"{path}.domain_ids references unknown domains: {', '.join(unknown_domains)}"
            )
        stage_ids.append(stage_id)
    registries["stages"] = set(_unique(stage_ids, "matrix.stages"))

    profile_ids: list[str] = []
    profile_requirements: dict[str, Mapping[str, Any]] = {}
    allowed_statuses = {
        "generic_exact",
        "generic_extension",
        "typed_existing",
        "typed_new",
        "hybrid",
    }
    for index, entry in enumerate(
        _list(root["profile_requirements"], "matrix.profile_requirements")
    ):
        path = f"matrix.profile_requirements[{index}]"
        item = _mapping(entry, path)
        _closed(item, PROFILE_KEYS, PROFILE_KEYS, path)
        identifier = _identifier(item["id"], f"{path}.id")
        if item["status"] not in allowed_statuses:
            raise CoverageAuditError(f"{path}.status is unsupported")
        concrete_profiles = [
            _identifier(value, f"{path}.profile_ids[{profile_index}]")
            for profile_index, value in enumerate(
                _list(item["profile_ids"], f"{path}.profile_ids")
            )
        ]
        if not concrete_profiles:
            raise CoverageAuditError(f"{path}.profile_ids must not be empty")
        _unique(concrete_profiles, f"{path}.profile_ids")
        _nonblank(item["notes"], f"{path}.notes")
        profile_ids.append(identifier)
        profile_requirements[identifier] = item
    _unique(profile_ids, "matrix.profile_requirements")

    scopes = _list(root["scopes"], "matrix.scopes")
    if not scopes:
        raise CoverageAuditError("matrix.scopes must not be empty")
    scope_ids: list[str] = []
    all_node_ids: list[str] = []
    prerequisites: list[tuple[str, str, str]] = []
    binding_ids: list[str] = []
    bindings: list[dict[str, Any]] = []
    derived_scopes: list[dict[str, Any]] = []

    for scope_index, entry in enumerate(scopes):
        path = f"matrix.scopes[{scope_index}]"
        scope = _mapping(entry, path)
        kind = scope.get("kind")
        if kind in {"school", "undergraduate_core"}:
            _closed(
                scope,
                COVERAGE_SCOPE_KEYS,
                COVERAGE_SCOPE_KEYS - {"stage_references"},
                path,
            )
            if scope.get("can_report_comprehensive") is not True:
                raise CoverageAuditError(
                    f"{path}.can_report_comprehensive must be true"
                )
            scope_id = _identifier(scope["id"], f"{path}.id")
            _validate_reference(scope["reference"], f"{path}.reference")
            defaults = _mapping(scope["defaults"], f"{path}.defaults")
            _closed(defaults, DEFAULT_KEYS, DEFAULT_KEYS, f"{path}.defaults")
            default_modes = _validate_axis(
                defaults["required_modes"],
                f"{path}.defaults.required_modes",
                registries["modes"],
            )
            default_difficulties = _validate_axis(
                defaults["required_difficulties"],
                f"{path}.defaults.required_difficulties",
                registries["difficulties"],
            )
            stage_references: set[str] = set()
            for reference_index, reference_value in enumerate(
                scope.get("stage_references", [])
            ):
                reference_path = f"{path}.stage_references[{reference_index}]"
                reference = _mapping(reference_value, reference_path)
                _closed(
                    reference,
                    STAGE_REFERENCE_KEYS,
                    STAGE_REFERENCE_KEYS,
                    reference_path,
                )
                reference_stage = _identifier(
                    reference["stage"], f"{reference_path}.stage"
                )
                if reference_stage not in registries["stages"]:
                    raise CoverageAuditError(
                        f"{reference_path}.stage references unknown {reference_stage}"
                    )
                stage_references.add(reference_stage)
                _uri(reference["url"], f"{reference_path}.url")
                _nonblank(reference["section"], f"{reference_path}.section")
            if len(stage_references) != len(scope.get("stage_references", [])):
                raise CoverageAuditError(
                    f"{path}.stage_references has duplicate stages"
                )

            family_ids: list[str] = []
            family_stages: set[str] = set()
            target = 0
            authored_bindings = 0
            admitted_bindings = 0
            derived_families: list[dict[str, Any]] = []
            for family_index, family_value in enumerate(
                _list(scope["families"], f"{path}.families")
            ):
                family_path = f"{path}.families[{family_index}]"
                family = _mapping(family_value, family_path)
                _closed(
                    family,
                    FAMILY_KEYS,
                    frozenset(
                        {"id", "title", "stage", "prerequisites", "profile_requirement"}
                    ),
                    family_path,
                )
                family_id = _identifier(family["id"], f"{family_path}.id")
                _nonblank(family["title"], f"{family_path}.title")
                stage = _identifier(family["stage"], f"{family_path}.stage")
                if stage not in registries["stages"]:
                    raise CoverageAuditError(
                        f"{family_path}.stage references unknown {stage}"
                    )
                family_stages.add(stage)
                profile_requirement = _identifier(
                    family["profile_requirement"], f"{family_path}.profile_requirement"
                )
                if profile_requirement not in profile_requirements:
                    raise CoverageAuditError(
                        f"{family_path}.profile_requirement references unknown "
                        f"{profile_requirement}"
                    )
                family_modes = _validate_axis(
                    family.get("required_modes", default_modes),
                    f"{family_path}.required_modes",
                    registries["modes"],
                )
                family_difficulties = _validate_axis(
                    family.get("required_difficulties", default_difficulties),
                    f"{family_path}.required_difficulties",
                    registries["difficulties"],
                )
                mode_target = sum(
                    item["minimum_distinct_patterns"] for item in family_modes
                )
                difficulty_target = sum(
                    item["minimum_distinct_patterns"] for item in family_difficulties
                )
                family_target = max(mode_target, difficulty_target)
                target += family_target
                modes = {item["id"] for item in family_modes}
                difficulties = {item["id"] for item in family_difficulties}
                family_bindings = family.get("draft_bindings", [])
                mode_binding_counts: dict[str, int] = defaultdict(int)
                difficulty_binding_counts: dict[str, int] = defaultdict(int)
                family_admitted = 0
                for binding_index, binding_value in enumerate(family_bindings):
                    binding = _validate_binding(
                        binding_value,
                        f"{family_path}.draft_bindings[{binding_index}]",
                        modes,
                        difficulties,
                    )
                    binding_ids.append(binding["draft_id"])
                    bindings.append(
                        {
                            "scope_id": scope_id,
                            "family_id": family_id,
                            "draft_id": binding["draft_id"],
                            "primary_mode": binding["primary_mode"],
                            "difficulty": binding["difficulty"],
                            "authoring_manifest": binding["authoring_manifest"],
                            "admission_manifest": binding["admission_manifest"],
                        }
                    )
                    authored_bindings += 1
                    mode_binding_counts[binding["primary_mode"]] += 1
                    difficulty_binding_counts[binding["difficulty"]] += 1
                    if binding["admission_manifest"] is not None:
                        admitted_bindings += 1
                        family_admitted += 1
                prerequisite_ids = [
                    _identifier(
                        value, f"{family_path}.prerequisites[{prerequisite_index}]"
                    )
                    for prerequisite_index, value in enumerate(
                        _list(family["prerequisites"], f"{family_path}.prerequisites")
                    )
                ]
                _unique(prerequisite_ids, f"{family_path}.prerequisites")
                prerequisites.extend(
                    (family_id, prerequisite, family_path)
                    for prerequisite in prerequisite_ids
                )
                family_ids.append(family_id)
                all_node_ids.append(family_id)
                mode_filled = sum(
                    min(
                        mode_binding_counts[item["id"]],
                        item["minimum_distinct_patterns"],
                    )
                    for item in family_modes
                )
                difficulty_filled = sum(
                    min(
                        difficulty_binding_counts[item["id"]],
                        item["minimum_distinct_patterns"],
                    )
                    for item in family_difficulties
                )
                derived_families.append(
                    {
                        "id": family_id,
                        "stage": stage,
                        "profile_requirement": profile_requirement,
                        "required_distinct_patterns": family_target,
                        "filled_distinct_patterns": min(
                            len(family_bindings), family_target
                        ),
                        "admitted_distinct_patterns": min(
                            family_admitted, family_target
                        ),
                        "mode_cells": {"required": mode_target, "filled": mode_filled},
                        "difficulty_cells": {
                            "required": difficulty_target,
                            "filled": difficulty_filled,
                        },
                        "published_distinct_patterns": None,
                        "retrieval_passing_distinct_patterns": None,
                        "comprehensive": False,
                    }
                )
            _unique(family_ids, f"{path}.families")
            if stage_references and not family_stages <= stage_references:
                missing = sorted(family_stages - stage_references)
                raise CoverageAuditError(
                    f"{path}.stage_references misses stages: {', '.join(missing)}"
                )
            derived_scopes.append(
                {
                    "id": scope_id,
                    "kind": kind,
                    "family_count": len(family_ids),
                    "required_distinct_patterns": target,
                    "filled_distinct_patterns": min(authored_bindings, target),
                    "admitted_distinct_patterns": min(admitted_bindings, target),
                    "authored_bindings": authored_bindings,
                    "admitted_bindings": admitted_bindings,
                    "published_bindings": None,
                    "retrieval_passing_bindings": None,
                    "database_status": "not_checked",
                    "runtime_status": "not_checked",
                    "comprehensive": False,
                    "families": derived_families,
                }
            )
        elif kind == "advanced_target":
            _closed(scope, TARGET_SCOPE_KEYS, TARGET_SCOPE_KEYS, path)
            if scope.get("can_report_comprehensive") is not False:
                raise CoverageAuditError(
                    f"{path}.can_report_comprehensive must be false"
                )
            scope_id = _identifier(scope["id"], f"{path}.id")
            _validate_reference(scope["reference"], f"{path}.reference")
            _nonblank(scope["refinement_required"], f"{path}.refinement_required")
            group_ids: list[str] = []
            target = 0
            for group_index, group_value in enumerate(
                _list(scope["target_groups"], f"{path}.target_groups")
            ):
                group_path = f"{path}.target_groups[{group_index}]"
                group = _mapping(group_value, group_path)
                _closed(group, TARGET_GROUP_KEYS, TARGET_GROUP_KEYS, group_path)
                group_id = _identifier(group["id"], f"{group_path}.id")
                _nonblank(group["title"], f"{group_path}.title")
                count = group["target_distinct_patterns"]
                if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                    raise CoverageAuditError(
                        f"{group_path}.target_distinct_patterns must be positive"
                    )
                target += count
                profile_requirement = _identifier(
                    group["profile_requirement"], f"{group_path}.profile_requirement"
                )
                if profile_requirement not in profile_requirements:
                    raise CoverageAuditError(
                        f"{group_path}.profile_requirement references unknown {profile_requirement}"
                    )
                prerequisite_ids = [
                    _identifier(
                        value, f"{group_path}.prerequisites[{prerequisite_index}]"
                    )
                    for prerequisite_index, value in enumerate(
                        _list(group["prerequisites"], f"{group_path}.prerequisites")
                    )
                ]
                _unique(prerequisite_ids, f"{group_path}.prerequisites")
                prerequisites.extend(
                    (group_id, prerequisite, group_path)
                    for prerequisite in prerequisite_ids
                )
                group_ids.append(group_id)
                all_node_ids.append(group_id)
            _unique(group_ids, f"{path}.target_groups")
            derived_scopes.append(
                {
                    "id": scope_id,
                    "kind": kind,
                    "target_group_count": len(group_ids),
                    "target_distinct_patterns": target,
                    "refinement_status": "required",
                    "comprehensive": False,
                }
            )
        else:
            raise CoverageAuditError(f"{path}.kind is unsupported")
        scope_ids.append(scope_id)

    _unique(scope_ids, "matrix.scopes")
    node_id_set = set(
        _unique(all_node_ids, "matrix family and target-group identifiers")
    )
    for owner, prerequisite, owner_path in prerequisites:
        if prerequisite == owner:
            raise CoverageAuditError(f"{owner_path} must not depend on itself")
        if prerequisite not in node_id_set:
            raise CoverageAuditError(
                f"{owner_path} references unknown prerequisite {prerequisite}"
            )
    graph: dict[str, list[str]] = defaultdict(list)
    for owner, prerequisite, _owner_path in prerequisites:
        graph[owner].append(prerequisite)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise CoverageAuditError(
                f"matrix prerequisites contain a cycle through {node}"
            )
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(node_id_set):
        visit(node)
    _unique(binding_ids, "matrix draft bindings")
    return {
        "scopes": derived_scopes,
        "binding_ids": sorted(binding_ids),
        "bindings": bindings,
        "profile_requirements": copy.deepcopy(profile_requirements),
    }


def _reject_duplicate_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoverageAuditError(f"duplicate JSON member {key!r}")
        result[key] = value
    return result


def _read_json(path: Path) -> Any:
    try:
        size = path.stat().st_size
        if size > MAX_JSON_BYTES:
            raise CoverageAuditError(
                f"JSON input exceeds {MAX_JSON_BYTES} bytes: {path}"
            )
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_members,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise CoverageAuditError(f"cannot read JSON {path}: {exc}") from exc


def _draft_cards(
    payload: Any, card_keys: Sequence[str], path: str
) -> list[Mapping[str, Any]]:
    required = {
        "id",
        "canonical_statement",
        "openmath_xml",
        "proof_strategy",
        "sketch_steps",
    }
    cards: list[Mapping[str, Any]] = []
    for card_key in card_keys:
        if card_key == "$root":
            values = _list(payload, path)
        else:
            source = _mapping(payload, path)
            if card_key not in source:
                raise CoverageAuditError(f"{path} has no declared card key {card_key}")
            values = _list(source[card_key], f"{path}.{card_key}")
        for index, value in enumerate(values):
            item = _mapping(value, f"{path}.{card_key}[{index}]")
            if not required <= set(item) and card_key != "$root":
                raise CoverageAuditError(
                    f"{path}.{card_key}[{index}] does not contain the five authoring fields"
                )
            cards.append(item)
    return cards


def validate_inventory_sources(payload: Any, repository_root: Path) -> dict[str, Any]:
    root = _mapping(payload, "inventory_sources")
    _closed(root, SOURCE_ROOT_KEYS, SOURCE_ROOT_KEYS, "inventory_sources")
    if root["schema_version"] != "pals.draft-catalog-inventory-sources.v1":
        raise CoverageAuditError("inventory_sources.schema_version is unsupported")
    repository_root = repository_root.resolve()
    source_ids: list[str] = []
    source_paths: list[str] = []
    sources: list[dict[str, Any]] = []
    for index, value in enumerate(_list(root["sources"], "inventory_sources.sources")):
        path = f"inventory_sources.sources[{index}]"
        item = _mapping(value, path)
        _closed(item, SOURCE_KEYS, SOURCE_KEYS, path)
        source_id = _identifier(item["id"], f"{path}.id")
        relative = _nonblank(item["path"], f"{path}.path")
        resolved = (repository_root / relative).resolve()
        try:
            resolved.relative_to(repository_root)
        except ValueError as exc:
            raise CoverageAuditError(
                f"{path}.path escapes the repository root"
            ) from exc
        if not resolved.is_file():
            raise CoverageAuditError(f"{path}.path does not exist: {relative}")
        if item["kind"] not in {
            "packaged_seed",
            "generic_authoring",
            "typed_authoring",
        }:
            raise CoverageAuditError(f"{path}.kind is unsupported")
        if item["schema_version"] is not None:
            _nonblank(item["schema_version"], f"{path}.schema_version")
        card_keys = [
            _nonblank(key, f"{path}.card_keys[{key_index}]")
            for key_index, key in enumerate(
                _list(item["card_keys"], f"{path}.card_keys")
            )
        ]
        if not card_keys:
            raise CoverageAuditError(f"{path}.card_keys must not be empty")
        _unique(card_keys, f"{path}.card_keys")
        _nonblank(item["profile_id"], f"{path}.profile_id")
        if item["status_ceiling"] not in {"build_input", "authored", "profile_valid"}:
            raise CoverageAuditError(f"{path}.status_ceiling is unsupported")
        if not isinstance(item["loader_supported"], bool):
            raise CoverageAuditError(f"{path}.loader_supported must be boolean")
        if item["kind"] == "packaged_seed" and card_keys != ["$root"]:
            raise CoverageAuditError(f"{path} packaged seed must use only $root")
        if item["kind"] != "packaged_seed" and "$root" in card_keys:
            raise CoverageAuditError(
                f"{path} authoring source must name its card arrays"
            )
        source_ids.append(source_id)
        source_paths.append(relative)
        sources.append(dict(item))
    _unique(source_ids, "inventory_sources.sources ids")
    _unique(source_paths, "inventory_sources.sources paths")

    limits: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(
        _list(root["profile_limits"], "inventory_sources.profile_limits")
    ):
        path = f"inventory_sources.profile_limits[{index}]"
        item = _mapping(value, path)
        _closed(item, PROFILE_LIMIT_KEYS, PROFILE_LIMIT_KEYS, path)
        profile_id = _nonblank(item["profile_id"], f"{path}.profile_id")
        for key in ("configured_population_limit", "available_population_limit"):
            limit = item[key]
            if limit is not None and (type(limit) is not int or limit < 1):
                raise CoverageAuditError(
                    f"{path}.{key} must be a positive integer or null"
                )
        _nonblank(item["source"], f"{path}.source")
        if profile_id in limits:
            raise CoverageAuditError(
                f"inventory_sources.profile_limits duplicates {profile_id}"
            )
        limits[profile_id] = dict(item)
    return {"sources": sources, "profile_limits": limits}


def _profile_id(payload: Mapping[str, Any]) -> str | None:
    profile = payload.get("profile")
    if isinstance(profile, dict):
        value = profile.get("id") or profile.get("profile_id")
        if isinstance(value, str):
            return value
    openmath_profile = payload.get("openmath_profile")
    if isinstance(openmath_profile, dict) and isinstance(
        openmath_profile.get("profile_id"), str
    ):
        return openmath_profile["profile_id"]
    if isinstance(payload.get("profile_id"), str):
        return payload["profile_id"]
    return None


def _portable_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _card_identity(card: Mapping[str, Any], path: str) -> tuple[str, str]:
    identifier = card.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise CoverageAuditError(f"{path} has a card without an id")
    xml = card.get("canonical_openmath_xml") or card.get("openmath_xml")
    if not isinstance(xml, str) or not xml:
        raise CoverageAuditError(f"{path} card {identifier} has no OpenMath XML")
    return identifier, xml


def _structural_signature(xml: str) -> str | None:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1]
        if local == "OMV" and "name" in element.attrib:
            element.attrib["name"] = "v"
        elif local in {"OMI", "OMF"}:
            element.text = "#"
            if "dec" in element.attrib:
                element.attrib["dec"] = "#"
            if "hex" in element.attrib:
                element.attrib["hex"] = "#"
        element.attrib.clear() if local == "OMOBJ" else None
    normalized = ET.tostring(root, encoding="utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _collision_groups(
    records: Sequence[Mapping[str, str]], key: str
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for record in records:
        value = record.get(key)
        if value:
            grouped[value].append(record)
    result: list[dict[str, Any]] = []
    for value, members in grouped.items():
        ids = sorted({member["id"] for member in members})
        files = sorted({member["manifest"] for member in members})
        if len(members) > 1 and (len(ids) > 1 or len(files) > 1):
            result.append({"signature": value, "draft_ids": ids, "manifests": files})
    return sorted(result, key=lambda item: (item["draft_ids"], item["manifests"]))


def inventory_repository(
    repository_root: Path,
    inventory_sources: Mapping[str, Any],
) -> dict[str, Any]:
    root = repository_root.resolve()
    validated = validate_inventory_sources(inventory_sources, root)
    generic_records: list[dict[str, str]] = []
    generic_manifests: list[str] = []
    typed_records: list[dict[str, str]] = []
    typed_manifests: list[dict[str, Any]] = []
    seed_source: dict[str, Any] | None = None

    for source in validated["sources"]:
        relative = source["path"]
        path = (root / relative).resolve()
        payload = _read_json(path)
        if source["schema_version"] is not None:
            source_payload = _mapping(payload, relative)
            if source_payload.get("schema_version") != source["schema_version"]:
                raise CoverageAuditError(
                    f"{relative} schema_version does not match its source declaration"
                )
        cards = _draft_cards(payload, source["card_keys"], relative)
        if source["kind"] == "packaged_seed":
            if seed_source is not None:
                raise CoverageAuditError(
                    "inventory sources declare more than one packaged seed"
                )
            seed_source = {
                "path": relative,
                "row_count": len(cards),
                "state": "repository_build_input",
                "runtime_publication_claim": False,
            }
            continue

        target = (
            typed_records if source["kind"] == "typed_authoring" else generic_records
        )
        if source["kind"] == "typed_authoring":
            declared_profile = source["profile_id"]
            observed_profile = _profile_id(_mapping(payload, relative))
            if observed_profile != declared_profile:
                raise CoverageAuditError(
                    f"{relative} profile {observed_profile!r} does not match declared "
                    f"{declared_profile!r}"
                )
            typed_manifests.append(
                {
                    "source_id": source["id"],
                    "path": relative,
                    "profile_id": declared_profile,
                    "record_count": len(cards),
                    "status_ceiling": source["status_ceiling"],
                    "loader_supported": source["loader_supported"],
                }
            )
        else:
            generic_manifests.append(relative)
        for card in cards:
            identifier, xml = _card_identity(card, relative)
            target.append(
                {
                    "id": identifier,
                    "xml": xml,
                    "manifest": relative,
                    "profile_id": source["profile_id"],
                    "structural_signature": _structural_signature(xml) or "",
                }
            )

    if seed_source is None:
        raise CoverageAuditError("inventory sources do not declare a packaged seed")
    supported_paths = {
        manifest["path"] for manifest in typed_manifests if manifest["loader_supported"]
    }
    supported_records = [
        record for record in typed_records if record["manifest"] in supported_paths
    ]
    all_records = generic_records + typed_records
    invalid_xml = sorted(
        {record["id"] for record in all_records if not record["structural_signature"]}
    )

    def duplicate_ids(records: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for record in records:
            grouped[record["id"]].append(record["manifest"])
        return [
            {"draft_id": identifier, "manifests": sorted(set(paths))}
            for identifier, paths in sorted(grouped.items())
            if len(paths) > 1
        ]

    typed_unique_ids = sorted({record["id"] for record in typed_records})
    supported_unique_ids = sorted({record["id"] for record in supported_records})
    generic_unique_ids = sorted({record["id"] for record in generic_records})
    return {
        "generic": {
            "packaged_seed": seed_source,
            "authoring": {
                "manifest_count": len(generic_manifests),
                "record_count": len(generic_records),
                "unique_draft_count": len(generic_unique_ids),
                "manifests": sorted(generic_manifests),
            },
        },
        "typed": {
            "authoring": {
                "manifest_count": len(typed_manifests),
                "record_count": len(typed_records),
                "unique_draft_count": len(typed_unique_ids),
                "profile_count": len(
                    {record["profile_id"] for record in typed_records}
                ),
            },
            "loader_supported": {
                "manifest_count": len(supported_paths),
                "unique_draft_count": len(supported_unique_ids),
                "profile_count": len(
                    {record["profile_id"] for record in supported_records}
                ),
                "manifests": sorted(supported_paths),
                "status": "structural_inventory_only",
                "profile_revalidation": "declared_from_closed_source_registry_not_run",
            },
            "manifests": sorted(typed_manifests, key=lambda item: item["path"]),
        },
        "database": {
            "status": "not_checked",
            "legacy_generic_rows": None,
            "local_typed_authoring_rows": None,
            "generic_active_generation_rows": None,
            "typed_active_generation_rows": None,
        },
        "runtime": {"status": "not_checked", "retrieval_passing_rows": None},
        "identities": {
            "generic_ids": generic_unique_ids,
            "typed_ids": typed_unique_ids,
            "loader_supported_typed_ids": supported_unique_ids,
            "records": sorted(
                [
                    {
                        "id": record["id"],
                        "manifest": record["manifest"],
                        "profile_id": record["profile_id"],
                        "structural_signature": record["structural_signature"],
                        "openmath_sha256": hashlib.sha256(
                            record["xml"].encode("utf-8")
                        ).hexdigest(),
                    }
                    for record in all_records
                ],
                key=lambda record: (record["id"], record["manifest"]),
            ),
        },
        "findings": {
            "invalid_openmath_ids": invalid_xml,
            "generic_duplicate_ids": duplicate_ids(generic_records),
            "typed_duplicate_ids": duplicate_ids(typed_records),
            "exact_openmath_collisions": _collision_groups(all_records, "xml"),
            "alpha_or_constant_only_review_flags": _collision_groups(
                all_records, "structural_signature"
            ),
        },
    }


def _compose_psql_json(repository_root: Path, select_sql: str) -> Mapping[str, Any]:
    sql = f"BEGIN TRANSACTION READ ONLY; {select_sql.rstrip().rstrip(';')}; COMMIT;"
    try:
        completed = subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "psql",
                "-X",
                "-q",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "pals",
                "-d",
                "pals",
                "-Atc",
                sql,
            ],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CoverageAuditError(f"local Compose database query failed: {exc}") from exc
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip().splitlines()
        detail = diagnostic[-1] if diagnostic else f"exit {completed.returncode}"
        raise CoverageAuditError(f"local Compose database query failed: {detail}")
    json_lines = [
        line for line in completed.stdout.splitlines() if line.lstrip().startswith("{")
    ]
    if len(json_lines) != 1:
        raise CoverageAuditError(
            "local Compose database query did not return one JSON object"
        )
    try:
        return _mapping(
            json.loads(json_lines[0], object_pairs_hook=_reject_duplicate_members),
            "local Compose database result",
        )
    except json.JSONDecodeError as exc:
        raise CoverageAuditError(
            f"local Compose database returned invalid JSON: {exc}"
        ) from exc


def inventory_local_compose_database(repository_root: Path) -> dict[str, Any]:
    """Read local catalog state through fixed SELECT-only Compose queries."""

    discovery = _compose_psql_json(
        repository_root,
        """
        SELECT json_build_object(
          'legacy_relkind', (
            SELECT c.relkind::text
            FROM pg_class AS c
            JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'dsp_drafts'
          ),
          'typed_authoring_present',
            to_regclass('pals_local_typed_catalog.catalog_cards') IS NOT NULL
            AND to_regclass('pals_local_typed_catalog.card_embeddings') IS NOT NULL
            AND to_regclass('pals_local_typed_catalog.catalog_profiles') IS NOT NULL
            AND to_regclass('pals_local_typed_catalog.catalog_manifests') IS NOT NULL,
          'generic_pfi_present',
            to_regclass('public.pfi_catalog_generations') IS NOT NULL
            AND to_regclass('public.pfi_catalog_rows') IS NOT NULL
            AND to_regclass('public.pfi_catalog_active') IS NOT NULL
            AND to_regclass('public.pfi_catalog_quarantine') IS NOT NULL
            AND to_regclass('public.pfi_catalog_publications') IS NOT NULL,
          'typed_runtime_present',
            to_regclass('public.typed_catalog_generations') IS NOT NULL
            AND to_regclass('public.typed_catalog_rows') IS NOT NULL
            AND to_regclass('public.typed_catalog_active') IS NOT NULL
        )
        """,
    )
    result: dict[str, Any] = {
        "status": "checked",
        "adapter": "local_compose_select_only_transaction",
        "legacy_generic": {
            "status": "not_present",
            "relation_kind": None,
            "row_count": None,
        },
        "local_typed_authoring": {
            "status": "not_present",
            "card_count": None,
            "embedding_count": None,
            "profile_count": None,
            "manifest_count": None,
            "authoring_statuses": {},
        },
        "generic_runtime": {
            "status": "not_present",
            "active_generation_id": None,
            "active_row_count": None,
            "generation_count": None,
        },
        "typed_runtime": {
            "status": "not_present",
            "active_profile_count": None,
            "active_row_count": None,
        },
    }
    if discovery.get("legacy_relkind") is not None:
        legacy = _compose_psql_json(
            repository_root,
            "SELECT json_build_object('row_count', count(*)) FROM public.dsp_drafts",
        )
        result["legacy_generic"] = {
            "status": "checked",
            "relation_kind": discovery["legacy_relkind"],
            "row_count": legacy["row_count"],
        }
    if discovery.get("typed_authoring_present") is True:
        typed = _compose_psql_json(
            repository_root,
            """
            SELECT json_build_object(
              'card_count', (SELECT count(*) FROM pals_local_typed_catalog.catalog_cards),
              'embedding_count', (SELECT count(*) FROM pals_local_typed_catalog.card_embeddings),
              'profile_count', (SELECT count(*) FROM pals_local_typed_catalog.catalog_profiles),
              'manifest_count', (SELECT count(*) FROM pals_local_typed_catalog.catalog_manifests),
              'authoring_statuses', (
                SELECT json_object_agg(authoring_status, manifest_count)
                FROM (
                  SELECT authoring_status, count(*) AS manifest_count
                  FROM pals_local_typed_catalog.catalog_manifests
                  GROUP BY authoring_status
                  ORDER BY authoring_status
                ) AS statuses
              )
            )
            """,
        )
        result["local_typed_authoring"] = {"status": "checked", **typed}
    if discovery.get("generic_pfi_present") is True:
        generic_runtime = _compose_psql_json(
            repository_root,
            """
            SELECT json_build_object(
              'active_generation_id', (
                SELECT generation_id::text FROM public.pfi_catalog_active WHERE singleton IS TRUE
              ),
              'active_row_count', (
                SELECT count(*)
                FROM public.pfi_catalog_rows AS r
                JOIN public.pfi_catalog_active AS a USING (generation_id)
                WHERE a.singleton IS TRUE
              ),
              'generation_count', (SELECT count(*) FROM public.pfi_catalog_generations)
            )
            """,
        )
        result["generic_runtime"] = {"status": "checked", **generic_runtime}
    if discovery.get("typed_runtime_present") is True:
        typed_runtime = _compose_psql_json(
            repository_root,
            """
            SELECT json_build_object(
              'active_profile_count', (SELECT count(*) FROM public.typed_catalog_active),
              'active_row_count', (
                SELECT count(*)
                FROM public.typed_catalog_rows AS r
                JOIN public.typed_catalog_active AS a
                  ON a.profile_id = r.profile_id AND a.generation_id = r.generation_id
              )
            )
            """,
        )
        result["typed_runtime"] = {"status": "checked", **typed_runtime}
    return result


def build_report(
    matrix: Mapping[str, Any],
    repository_root: Path,
    inventory_sources: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    matrix_result = validate_matrix(matrix)
    if inventory_sources is None:
        inventory_sources = _mapping(
            _read_json(
                repository_root
                / "specs/draft-catalog-expansion/inventory-sources.v1.json"
            ),
            "inventory sources",
        )
    validated_sources = validate_inventory_sources(inventory_sources, repository_root)
    repository = inventory_repository(repository_root, inventory_sources)
    authored_ids = set(repository["identities"]["generic_ids"]) | set(
        repository["identities"]["typed_ids"]
    )
    binding_ids = set(matrix_result["binding_ids"])
    unknown_bindings = sorted(binding_ids - authored_ids)
    orphan_authored = sorted(authored_ids - binding_ids)
    record_lookup = {
        (record["id"], record["manifest"]): record
        for record in repository["identities"]["records"]
    }
    binding_source_mismatches: list[dict[str, str]] = []
    binding_profile_mismatches: list[dict[str, Any]] = []
    admission_manifest_errors: list[dict[str, str]] = []
    valid_bindings: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_profile_requirements = {
        family["id"]: matrix_result["profile_requirements"][
            family["profile_requirement"]
        ]["profile_ids"]
        for scope in matrix["scopes"]
        if scope["kind"] != "advanced_target"
        for family in scope["families"]
    }
    for binding in matrix_result["bindings"]:
        record = record_lookup.get((binding["draft_id"], binding["authoring_manifest"]))
        if record is None:
            binding_source_mismatches.append(
                {
                    "family_id": binding["family_id"],
                    "draft_id": binding["draft_id"],
                    "authoring_manifest": binding["authoring_manifest"],
                }
            )
            continue
        candidate = {**binding, **record}
        allowed_profiles = family_profile_requirements[binding["family_id"]]
        if candidate["profile_id"] not in allowed_profiles:
            binding_profile_mismatches.append(
                {
                    "family_id": binding["family_id"],
                    "draft_id": binding["draft_id"],
                    "profile_id": candidate["profile_id"],
                    "allowed_profile_ids": allowed_profiles,
                }
            )
            continue
        if not candidate["structural_signature"]:
            continue
        admission_manifest = binding["admission_manifest"]
        if admission_manifest is not None:
            admission_path = (repository_root.resolve() / admission_manifest).resolve()
            try:
                admission_path.relative_to(repository_root.resolve())
            except ValueError:
                admission_manifest_errors.append(
                    {
                        "draft_id": binding["draft_id"],
                        "admission_manifest": admission_manifest,
                        "error": "path_escape",
                    }
                )
                continue
            if not admission_path.is_file():
                admission_manifest_errors.append(
                    {
                        "draft_id": binding["draft_id"],
                        "admission_manifest": admission_manifest,
                        "error": "missing",
                    }
                )
                continue
        valid_bindings[binding["family_id"]].append(candidate)

    bound_structural_duplicates: list[dict[str, Any]] = []
    source_scopes = {
        scope["id"]: scope
        for scope in matrix["scopes"]
        if scope["kind"] != "advanced_target"
    }
    for scope_report in matrix_result["scopes"]:
        if scope_report["kind"] == "advanced_target":
            continue
        source_scope = source_scopes[scope_report["id"]]
        source_families = {family["id"]: family for family in source_scope["families"]}
        scope_filled = 0
        scope_admitted = 0
        for family_report in scope_report["families"]:
            family = source_families[family_report["id"]]
            defaults = source_scope["defaults"]
            modes = family.get("required_modes", defaults["required_modes"])
            difficulties = family.get(
                "required_difficulties", defaults["required_difficulties"]
            )
            by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for binding in valid_bindings[family_report["id"]]:
                by_signature[binding["structural_signature"]].append(binding)
            effective: list[dict[str, Any]] = []
            for signature, members in sorted(by_signature.items()):
                ordered = sorted(
                    members,
                    key=lambda item: (item["draft_id"], item["authoring_manifest"]),
                )
                effective.append(ordered[0])
                if len(ordered) > 1:
                    bound_structural_duplicates.append(
                        {
                            "family_id": family_report["id"],
                            "signature": signature,
                            "draft_ids": [member["draft_id"] for member in ordered],
                        }
                    )
            mode_counts: dict[str, int] = defaultdict(int)
            difficulty_counts: dict[str, int] = defaultdict(int)
            for binding in effective:
                mode_counts[binding["primary_mode"]] += 1
                difficulty_counts[binding["difficulty"]] += 1
            family_report["filled_distinct_patterns"] = min(
                len(effective), family_report["required_distinct_patterns"]
            )
            family_report["admitted_distinct_patterns"] = min(
                sum(binding["admission_manifest"] is not None for binding in effective),
                family_report["required_distinct_patterns"],
            )
            family_report["mode_cells"]["filled"] = sum(
                min(mode_counts[item["id"]], item["minimum_distinct_patterns"])
                for item in modes
            )
            family_report["difficulty_cells"]["filled"] = sum(
                min(difficulty_counts[item["id"]], item["minimum_distinct_patterns"])
                for item in difficulties
            )
            scope_filled += family_report["filled_distinct_patterns"]
            scope_admitted += family_report["admitted_distinct_patterns"]
        scope_report["filled_distinct_patterns"] = scope_filled
        scope_report["admitted_distinct_patterns"] = scope_admitted

    exclusive_profile_capacity: dict[str, int] = defaultdict(int)
    profile_requirements = matrix_result["profile_requirements"]
    for scope, source_scope in zip(
        matrix_result["scopes"], matrix["scopes"], strict=True
    ):
        if scope["kind"] == "advanced_target":
            continue
        defaults = source_scope["defaults"]
        for family in source_scope["families"]:
            modes = family.get("required_modes", defaults["required_modes"])
            difficulties = family.get(
                "required_difficulties", defaults["required_difficulties"]
            )
            target = max(
                sum(item["minimum_distinct_patterns"] for item in modes),
                sum(item["minimum_distinct_patterns"] for item in difficulties),
            )
            profiles = profile_requirements[family["profile_requirement"]][
                "profile_ids"
            ]
            if len(profiles) == 1:
                exclusive_profile_capacity[profiles[0]] += target

    generic_required = exclusive_profile_capacity.get("generic-v1", 0)
    concrete_profiles = sorted(
        {
            profile_id
            for requirement in profile_requirements.values()
            for profile_id in requirement["profile_ids"]
        }
    )
    profile_capacity: list[dict[str, Any]] = []
    capacity_overflow: list[dict[str, Any]] = []
    for profile_id in concrete_profiles:
        declared = validated_sources["profile_limits"].get(profile_id)
        configured = (
            None if declared is None else declared["configured_population_limit"]
        )
        available = None if declared is None else declared["available_population_limit"]
        required = exclusive_profile_capacity.get(profile_id, 0)
        entry = {
            "profile_id": profile_id,
            "exclusive_required_patterns": required,
            "configured_population_limit": configured,
            "available_population_limit": available,
            "limit_status": "configured"
            if configured is not None and available is not None
            else "not_configured",
            "source": None if declared is None else declared["source"],
        }
        profile_capacity.append(entry)
        effective_limits = [
            limit for limit in (configured, available) if limit is not None
        ]
        if effective_limits and required > min(effective_limits):
            capacity_overflow.append(entry)
    findings = copy.deepcopy(repository["findings"])
    findings.update(
        {
            "unknown_bound_draft_ids": unknown_bindings,
            "binding_source_mismatches": sorted(
                binding_source_mismatches,
                key=lambda item: (item["family_id"], item["draft_id"]),
            ),
            "binding_profile_mismatches": sorted(
                binding_profile_mismatches,
                key=lambda item: (item["family_id"], item["draft_id"]),
            ),
            "binding_admission_manifest_errors": sorted(
                admission_manifest_errors,
                key=lambda item: (item["draft_id"], item["admission_manifest"]),
            ),
            "bound_structural_duplicates": bound_structural_duplicates,
            "unbound_authored_draft_count": len(orphan_authored),
            "capacity_overflow": capacity_overflow,
            "profiles_without_configured_limits": [
                entry["profile_id"]
                for entry in profile_capacity
                if entry["limit_status"] == "not_configured"
            ],
        }
    )
    repository.pop("findings")
    repository.pop("identities")
    return {
        "schema_version": REPORT_VERSION,
        "matrix_schema_version": matrix["schema_version"],
        "coverage": {"scopes": matrix_result["scopes"]},
        "capacity": {
            "generic_v1_population_limit": GENERIC_PFI_POPULATION_LIMIT,
            "generic_v1_exclusive_required_patterns": generic_required,
            "exclusive_required_patterns_by_profile": dict(
                sorted(exclusive_profile_capacity.items())
            ),
            "profiles": profile_capacity,
        },
        "repository_inventory": repository,
        "findings": findings,
        "overall_comprehensive": False,
        "overall_reason": "required cells are not yet bound, published, and retrieval-passing",
    }


def reconcile_database(report: dict[str, Any], database: Mapping[str, Any]) -> None:
    report["repository_inventory"]["database"] = copy.deepcopy(database)
    divergences: list[dict[str, Any]] = []
    typed_database = database.get("local_typed_authoring", {})
    supported = report["repository_inventory"]["typed"]["loader_supported"]
    if typed_database.get("status") == "checked":
        if typed_database.get("card_count") != supported["unique_draft_count"]:
            divergences.append(
                {
                    "catalog": "local_typed_authoring",
                    "repository_loader_supported": supported["unique_draft_count"],
                    "database_cards": typed_database.get("card_count"),
                }
            )
        if typed_database.get("embedding_count") != typed_database.get("card_count"):
            divergences.append(
                {
                    "catalog": "local_typed_authoring_embeddings",
                    "database_cards": typed_database.get("card_count"),
                    "database_embeddings": typed_database.get("embedding_count"),
                }
            )
    report["findings"]["database_count_divergences"] = divergences
    legacy = database.get("legacy_generic", {})
    report["repository_inventory"]["generic"]["observed_local_legacy"] = {
        "status": legacy.get("status", "not_checked"),
        "relation_kind": legacy.get("relation_kind"),
        "row_count": legacy.get("row_count"),
        "publication_claim": False,
    }


def _summary(report: Mapping[str, Any]) -> str:
    scopes = report["coverage"]["scopes"]
    lines = ["Draft catalog coverage audit"]
    for scope in scopes:
        target = scope.get(
            "required_distinct_patterns", scope.get("target_distinct_patterns")
        )
        if scope["kind"] == "advanced_target":
            label = "refinement required"
        else:
            label = (
                f"filled {scope['filled_distinct_patterns']}; "
                f"admitted {scope['admitted_distinct_patterns']}"
            )
        lines.append(f"- {scope['id']}: target {target}; {label}; comprehensive=false")
    generic = report["repository_inventory"]["generic"]
    typed = report["repository_inventory"]["typed"]
    database = report["repository_inventory"]["database"]
    if database["status"] == "checked":
        database_line = (
            "- database: legacy="
            f"{database['legacy_generic']['row_count']}; typed="
            f"{database['local_typed_authoring']['card_count']}; generic PFI="
            f"{database['generic_runtime']['status']}; typed runtime="
            f"{database['typed_runtime']['status']}"
        )
    else:
        database_line = "- database publication: not checked"
    lines.extend(
        [
            (
                f"- packaged generic seed: {generic['packaged_seed']['row_count']} "
                "(build input, not runtime proof)"
            ),
            (
                f"- typed authored: {typed['authoring']['unique_draft_count']} unique / "
                f"{typed['authoring']['profile_count']} profiles"
            ),
            (
                "- typed loader-supported: "
                f"{typed['loader_supported']['unique_draft_count']} unique / "
                f"{typed['loader_supported']['profile_count']} profiles "
                "(profile revalidation not run)"
            ),
            database_line,
            "- runtime retrieval: not checked",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=root)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=root / "specs/draft-catalog-expansion/coverage-matrix.v1.json",
    )
    parser.add_argument(
        "--sources",
        type=Path,
        default=root / "specs/draft-catalog-expansion/inventory-sources.v1.json",
    )
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument(
        "--database",
        choices=("none", "local-compose"),
        default="none",
        help="Optionally reconcile fixed SELECT-only local Compose PostgreSQL queries.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        matrix = _mapping(_read_json(args.matrix), str(args.matrix))
        inventory_sources = _mapping(_read_json(args.sources), str(args.sources))
        report = build_report(matrix, args.repository_root, inventory_sources)
        if args.database == "local-compose":
            reconcile_database(
                report, inventory_local_compose_database(args.repository_root)
            )
    except CoverageAuditError as exc:
        print(f"coverage audit failed: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
