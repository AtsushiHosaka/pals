"""Seal the native ``typed-plane-geometry-v1`` authoring proposal.

The result is immutable local evidence only.  It never changes a Draft DB,
seed, embedding index, local typed catalog, or PFI package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_plane_geometry import (
    TYPED_PLANE_GEOMETRY_OPENMATH_CDBASE,
    canonicalize_typed_plane_geometry_openmath_xml,
)
from pals_agent.typed_plane_geometry_manifest import (
    validate_typed_plane_geometry_manifest,
)

OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_PLANE_GEOMETRY_OPENMATH_CDBASE
PRIVATE_CD = "pals_plane_geometry"
REGISTRY = "pals-agent/pals_agent/content_dictionaries/typed-plane-geometry-v1-registry.json"
DESIGN = "docs/typed-plane-geometry-v1-design.md"
TOOLCHAIN = "pals-agent/lean-workspace/lean-toolchain"
WITNESSES = "pals-agent/testdata/typed-plane-geometry-v1/plane-geometry-witnesses.lean"
MANIFEST_DIGEST_INPUT = (
    "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted"
)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _oms(cd: str, name: str, *, cdbase: str) -> str:
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def _typed(name: str) -> str:
    return _oms(PRIVATE_CD, name, cdbase=TYPED)


def _standard(cd: str, name: str) -> str:
    return _oms(cd, name, cdbase=STANDARD)


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _obj(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _declaration(name: str, sort: str) -> str:
    return f"<OMATTR><OMATP>{_typed('type')}{_typed(sort)}</OMATP>{_var(name)}</OMATTR>"


def _forall(declarations: list[tuple[str, str]], body: str) -> str:
    encoded = "".join(_declaration(name, sort) for name, sort in declarations)
    return _obj(f"<OMBIND>{_typed('forall')}<OMBVAR>{encoded}</OMBVAR>{body}</OMBIND>")


def _exists(declarations: list[tuple[str, str]], body: str) -> str:
    encoded = "".join(_declaration(name, sort) for name, sort in declarations)
    return _obj(f"<OMBIND>{_typed('exists')}<OMBVAR>{encoded}</OMBVAR>{body}</OMBIND>")


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _and(*arguments: str) -> str:
    return _app(_standard("logic1", "and"), *arguments)


def _plane(name: str, *arguments: str) -> str:
    return _app(_typed(name), *arguments)


def _point(x: int, y: int) -> str:
    return _plane("point2", f"<OMI>{x}</OMI>", f"<OMI>{y}</OMI>")


def _card(
    *,
    identifier: str,
    statement: str,
    openmath: str,
    symbols: list[str],
    strategy: str,
    steps: list[str],
    lean_target: str,
    lean_witness: str,
    statement_to_openmath: str,
    openmath_to_lean: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_plane_geometry_openmath_xml(openmath)
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} requires 4..8 sketch steps")
    trace = {"result_sort": "Prop", "symbols": symbols}
    return {
        "id": identifier,
        "domain": "high_school.coordinate_geometry",
        "difficulty": "standard",
        "canonical_statement": statement,
        "openmath_xml": openmath,
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha256_text(canonical),
        "signature_trace": trace,
        "signature_trace_sha256": _sha256_bytes(rfc8785.dumps(trace)),
        "proof_strategy": strategy,
        "proof_strategy_sha256": _sha256_text(strategy),
        "sketch_steps": steps,
        "sketch_steps_sha256": _sha256_bytes(rfc8785.dumps(steps)),
        "lean": {
            "target": lean_target,
            "target_sha256": _sha256_text(lean_target),
            "witness": lean_witness,
            "witness_sha256": _sha256_text(lean_witness),
        },
        "statement_openmath_lean_alignment_review": {
            "status": "reviewed_by_local_authoring_agent_not_admitted",
            "statement_to_openmath": statement_to_openmath,
            "openmath_to_lean": openmath_to_lean,
            "admission_gate": (
                "An independent project reviewer must accept this sealed record before any "
                "typed catalog or database admission."
            ),
        },
    }


def _witnesses() -> dict[str, tuple[str, str]]:
    return {
        "typed_plane_distance_self_zero": (
            "∀ p : Point2, distanceSq p p = 0",
            """example : ∀ p : Point2, distanceSq p p = 0 := by
  intro p
  simp [distanceSq]
""",
        ),
        "typed_plane_line_through_two_points": (
            "∃ line : Line2,\n      incidentPointLine ⟨0, 1⟩ line ∧ incidentPointLine ⟨2, 5⟩ line",
            """example :
    ∃ line : Line2,
      incidentPointLine ⟨0, 1⟩ line ∧ incidentPointLine ⟨2, 5⟩ line := by
  refine ⟨⟨-2, 1, -1⟩, ?_⟩
  norm_num [incidentPointLine]
""",
        ),
        "typed_plane_circle_through_three_points": (
            "∃ circle : Circle2,\n      incidentPointCircle ⟨1, 0⟩ circle ∧ incidentPointCircle ⟨0, 1⟩ circle ∧\n        incidentPointCircle ⟨-1, 0⟩ circle",
            """example :
    ∃ circle : Circle2,
      incidentPointCircle ⟨1, 0⟩ circle ∧ incidentPointCircle ⟨0, 1⟩ circle ∧
        incidentPointCircle ⟨-1, 0⟩ circle := by
  refine ⟨⟨⟨0, 0⟩, 1⟩, ?_⟩
  norm_num [incidentPointCircle, distanceSq]
""",
        ),
        "typed_plane_perpendicular_symmetric": (
            "∀ first second : Line2, perpendicular first second → perpendicular second first",
            """example : ∀ first second : Line2, perpendicular first second → perpendicular second first := by
  intro first second h
  simpa [perpendicular, add_comm, mul_comm] using h
""",
        ),
        "typed_plane_parallel_symmetric": (
            "∀ first second : Line2, parallel first second → parallel second first",
            """example : ∀ first second : Line2, parallel first second → parallel second first := by
  intro first second h
  simpa [parallel, mul_comm] using h.symm
""",
        ),
    }


def _cards() -> list[dict[str, Any]]:
    witnesses = _witnesses()
    point = _var("p")
    line = _var("line")
    circle = _var("circle")
    first = _var("first")
    second = _var("second")
    return [
        _card(
            identifier="typed_plane_distance_self_zero",
            statement="For every plane point p, the squared distance from p to p is zero.",
            openmath=_forall(
                [("p", "Point2")],
                _eq(_plane("distance_sq", point, point), "<OMI>0</OMI>"),
            ),
            symbols=["pals_plane_geometry:forall", "Point2", "distance_sq", "relation1:eq"],
            strategy="Expand the squared coordinate differences; both coordinate differences vanish.",
            steps=[
                "Bind p with sort P2.",
                "Apply distance_sq only to the two P2 occurrences of p.",
                "Infer the result as R and compare it to scalar zero.",
                "Expand the coordinate differences and simplify both zero squares.",
            ],
            lean_target=witnesses["typed_plane_distance_self_zero"][0],
            lean_witness=witnesses["typed_plane_distance_self_zero"][1],
            statement_to_openmath="distance_sq(P2, P2) is equated only to the scalar literal 0.",
            openmath_to_lean="The witness defines distanceSq on Point2 and proves the same self-distance equality.",
        ),
        _card(
            identifier="typed_plane_line_through_two_points",
            statement="There exists a plane line incident with both (0,1) and (2,5).",
            openmath=_exists(
                [("line", "Line2")],
                _and(
                    _plane("incident_point_line", _point(0, 1), line),
                    _plane("incident_point_line", _point(2, 5), line),
                ),
            ),
            symbols=["exists", "Line2", "point2", "incident_point_line", "logic1:and"],
            strategy="Exhibit the line -2x+y-1=0 and verify both coordinate substitutions.",
            steps=[
                "Bind the witness line with sort L2.",
                "Construct both coordinates as P2 values with point2.",
                "Type each point-line incidence atom as Prop.",
                "Use -2x+y-1=0 to verify incidence at both points.",
            ],
            lean_target=witnesses["typed_plane_line_through_two_points"][0],
            lean_witness=witnesses["typed_plane_line_through_two_points"][1],
            statement_to_openmath="The existential binds L2 and each incident_point_line atom has exact signature P2 × L2 → Prop.",
            openmath_to_lean="The witness supplies Line2(-2, 1, -1) and evaluates the same incidence equation at both points.",
        ),
        _card(
            identifier="typed_plane_circle_through_three_points",
            statement="There exists a plane circle incident with (1,0), (0,1), and (-1,0).",
            openmath=_exists(
                [("circle", "Circle2")],
                _and(
                    _plane("incident_point_circle", _point(1, 0), circle),
                    _plane("incident_point_circle", _point(0, 1), circle),
                    _plane("incident_point_circle", _point(-1, 0), circle),
                ),
            ),
            symbols=["exists", "Circle2", "point2", "incident_point_circle", "logic1:and"],
            strategy="Exhibit the unit circle centered at the origin and evaluate each squared distance.",
            steps=[
                "Bind the witness circle with sort Circle2.",
                "Construct the three specified coordinates as P2 values.",
                "Type all point-circle incidence atoms as Prop.",
                "Evaluate squared distance to the origin and obtain radius square one three times.",
            ],
            lean_target=witnesses["typed_plane_circle_through_three_points"][0],
            lean_witness=witnesses["typed_plane_circle_through_three_points"][1],
            statement_to_openmath="The existential binds Circle2 and all incidence atoms have exact signature P2 × Circle2 → Prop.",
            openmath_to_lean="The witness supplies the origin-centered radius-one Circle2 and evaluates the same distanceSq definition.",
        ),
        _card(
            identifier="typed_plane_perpendicular_symmetric",
            statement="Perpendicularity of two plane lines is symmetric.",
            openmath=_forall(
                [("first", "Line2"), ("second", "Line2")],
                _implies(
                    _plane("perpendicular", first, second),
                    _plane("perpendicular", second, first),
                ),
            ),
            symbols=["forall", "Line2", "perpendicular", "logic1:implies"],
            strategy="Use commutativity of the normal-vector scalar product defining perpendicularity.",
            steps=[
                "Bind first and second as L2 values.",
                "Infer perpendicular(first, second) as Prop.",
                "Swap the two L2 operands in the conclusion.",
                "Use commutativity of multiplication and addition in the scalar equation.",
            ],
            lean_target=witnesses["typed_plane_perpendicular_symmetric"][0],
            lean_witness=witnesses["typed_plane_perpendicular_symmetric"][1],
            statement_to_openmath="perpendicular accepts only L2 × L2 and yields Prop on both sides of implication.",
            openmath_to_lean="The witness uses the symmetric zero dot-product equation for the two Line2 normals.",
        ),
        _card(
            identifier="typed_plane_parallel_symmetric",
            statement="Parallelism of two plane lines is symmetric.",
            openmath=_forall(
                [("first", "Line2"), ("second", "Line2")],
                _implies(_plane("parallel", first, second), _plane("parallel", second, first)),
            ),
            symbols=["forall", "Line2", "parallel", "logic1:implies"],
            strategy="Reverse the proportional normal-coefficient equation defining parallel lines.",
            steps=[
                "Bind first and second as L2 values.",
                "Infer parallel(first, second) as Prop.",
                "Swap the two L2 operands in the conclusion.",
                "Reverse and commute the scalar coefficient equality.",
            ],
            lean_target=witnesses["typed_plane_parallel_symmetric"][0],
            lean_witness=witnesses["typed_plane_parallel_symmetric"][1],
            statement_to_openmath="parallel accepts only L2 × L2 and yields Prop on both sides of implication.",
            openmath_to_lean="The witness reverses the proportional-coefficient equality for the two Line2 normals.",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    registry = (ROOT / REGISTRY).read_bytes()
    design = (ROOT / DESIGN).read_bytes()
    toolchain = (ROOT / TOOLCHAIN).read_bytes()
    witnesses = (ROOT / WITNESSES).read_bytes()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-plane-geometry-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "native planar-geometry typed authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, local typed catalog, or PFI package",
            "revision": "typed-plane-geometry-v1-local-r1",
        },
        "profile": {
            "id": "typed-plane-geometry-v1",
            "validator": "pals_agent.typed_plane_geometry.validate_canonical_typed_plane_geometry_openmath_xml",
            "canonicalizer": "openmath-cdbase-alpha-c14n-v4",
            "validator_status": "implemented_isolated_profile",
            "content_dictionary_bundle": {
                "relative_path": REGISTRY,
                "sha256": _sha256_bytes(registry),
                "digest_input": "exact UTF-8 bytes of the named registry/CD bundle",
            },
            "profile_design": {
                "relative_path": DESIGN,
                "sha256": _sha256_bytes(design),
                "digest_input": "exact UTF-8 bytes of the named profile design document",
            },
            "lean_toolchain": {
                "relative_path": TOOLCHAIN,
                "value": toolchain.decode("utf-8").rstrip("\n"),
                "sha256": _sha256_bytes(toolchain),
                "digest_input": "exact UTF-8 bytes of the named lean-toolchain file",
            },
        },
        "lean_witness_bundle": {
            "relative_path": WITNESSES,
            "sha256": _sha256_bytes(witnesses),
            "digest_input": "exact UTF-8 bytes of the named Lean file, including imports and final newline",
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../testdata/typed-plane-geometry-v1/plane-geometry-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_candidate_cards": _cards(),
    }
    payload["manifest_digest"] = {
        "algorithm": "sha256",
        "input": MANIFEST_DIGEST_INPUT,
        "sha256": _sha256_bytes(rfc8785.dumps(payload)),
    }
    validate_typed_plane_geometry_manifest(payload, repository_root=ROOT)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/typed-plane-geometry-v1-authoring-manifest.proposal.json",
    )
    args = parser.parse_args()
    args.output.write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
