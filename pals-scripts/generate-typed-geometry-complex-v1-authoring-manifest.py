"""Seal the eight phase-A vector/complex typed Draft proposals.

The output is authoring evidence only.  It has no generic OpenMath, Draft DB,
seed, embedding-index, local-typed-catalog, or PFI side effect.
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

from pals_agent.typed_geometry_complex import (
    TYPED_GEOMETRY_COMPLEX_OPENMATH_CDBASE,
    canonicalize_typed_geometry_complex_openmath_xml,
)
from pals_agent.typed_geometry_complex_manifest import (
    validate_typed_geometry_complex_manifest,
)

OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_GEOMETRY_COMPLEX_OPENMATH_CDBASE
REGISTRY = (
    "pals-agent/pals_agent/content_dictionaries/typed-geometry-complex-v1-registry.json"
)
DESIGN = "docs/vector-complex-typed-extension.md"
TOOLCHAIN = "pals-agent/lean-workspace/lean-toolchain"
WITNESSES = "pals-agent/testdata/typed-geometry-complex-v1/vector-complex-phase-a-witnesses.lean"
MANIFEST_DIGEST_INPUT = (
    "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted"
)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _oms(cd: str, name: str, *, cdbase: str) -> str:
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return _oms(cd, name, cdbase=STANDARD)


def _typed(name: str) -> str:
    return _oms("pals2", name, cdbase=TYPED)


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _obj(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _vector(first: str, second: str) -> str:
    return _app(_standard("linalg2", "vector"), first, second)


def _complex(real: str, imaginary: str) -> str:
    return _app(_standard("complex1", "complex_cartesian"), real, imaginary)


def _pals(name: str, *arguments: str) -> str:
    return _app(_typed(name), *arguments)


def _forall_complex(name: str, body: str) -> str:
    return _obj(
        f'<OMBIND>{_typed("forall_complex")}<OMBVAR><OMV name="{name}"/>'
        f"</OMBVAR>{body}</OMBIND>"
    )


def _card(
    *,
    identifier: str,
    domain: str,
    difficulty: str,
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
    canonical = canonicalize_typed_geometry_complex_openmath_xml(openmath)
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} requires 4..8 sketch steps")
    trace = {"result_sort": "Prop", "symbols": symbols}
    return {
        "id": identifier,
        "domain": domain,
        "difficulty": difficulty,
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
        "typed_vector2_component_addition": (
            "vectorAdd (Vector2.mk 1 2) (Vector2.mk 3 (-1)) = Vector2.mk 4 1",
            """example : vectorAdd (Vector2.mk 1 2) (Vector2.mk 3 (-1)) = Vector2.mk 4 1 := by
  norm_num [vectorAdd]
""",
        ),
        "typed_vector2_scalar_multiple": (
            "vectorScale 3 (Vector2.mk 2 (-1)) = Vector2.mk 6 (-3)",
            """example : vectorScale 3 (Vector2.mk 2 (-1)) = Vector2.mk 6 (-3) := by
  norm_num [vectorScale]
""",
        ),
        "typed_vector2_dot_product_orthogonality": (
            "dot (Vector2.mk 1 2) (Vector2.mk 2 (-1)) = 0",
            """example : dot (Vector2.mk 1 2) (Vector2.mk 2 (-1)) = 0 := by
  norm_num [dot]
""",
        ),
        "typed_vector2_triangle_area_determinant": (
            "|determinant2 (Vector2.mk 2 0) (Vector2.mk 0 3)| / 2 = 3",
            """example : |determinant2 (Vector2.mk 2 0) (Vector2.mk 0 3)| / 2 = 3 := by
  norm_num [determinant2]
""",
        ),
        "typed_complex_cartesian_multiplication": (
            "((1 : ℂ) + 2 * Complex.I) * (3 - Complex.I) = 5 + 5 * Complex.I",
            """example : ((1 : ℂ) + 2 * Complex.I) * (3 - Complex.I) = 5 + 5 * Complex.I := by
  calc
    ((1 : ℂ) + 2 * Complex.I) * (3 - Complex.I) =
        3 + 5 * Complex.I - 2 * Complex.I ^ 2 := by ring
    _ = 5 + 5 * Complex.I := by rw [Complex.I_sq]; ring
""",
        ),
        "typed_complex_conjugate_norm_square": (
            "z * star z = (Complex.normSq z : ℂ)",
            """example (z : ℂ) : z * star z = (Complex.normSq z : ℂ) := by
  simpa only [Complex.star_def] using Complex.mul_conj z
""",
        ),
        "typed_complex_multiply_i_quarter_turn": (
            "((1 : ℂ) + 2 * Complex.I) * Complex.I = (-2 : ℂ) + Complex.I",
            """example : ((1 : ℂ) + 2 * Complex.I) * Complex.I = (-2 : ℂ) + Complex.I := by
  calc
    ((1 : ℂ) + 2 * Complex.I) * Complex.I =
        (1 : ℂ) * Complex.I + (2 : ℂ) * Complex.I ^ 2 := by ring
    _ = (-2 : ℂ) + Complex.I := by rw [Complex.I_sq]; ring
""",
        ),
        "typed_complex_argument_quadrant_two": (
            "0 < Complex.arg ((-1 : ℂ) + Complex.I)",
            """example : 0 < Complex.arg ((-1 : ℂ) + Complex.I) := by
  by_contra h
  have hle : Complex.arg ((-1 : ℂ) + Complex.I) ≤ 0 := le_of_not_gt h
  have hnonneg : 0 ≤ Complex.arg ((-1 : ℂ) + Complex.I) := by
    rw [Complex.arg_nonneg_iff]
    norm_num
  have hzero : Complex.arg ((-1 : ℂ) + Complex.I) = 0 := le_antisymm hle hnonneg
  have parts := Complex.arg_eq_zero_iff.mp hzero
  norm_num at parts
""",
        ),
    }


def _cards() -> list[dict[str, Any]]:
    witnesses = _witnesses()
    vector_12 = _vector("<OMI>1</OMI>", "<OMI>2</OMI>")
    vector_2m1 = _vector("<OMI>2</OMI>", "<OMI>-1</OMI>")
    vector_3m1 = _vector("<OMI>3</OMI>", "<OMI>-1</OMI>")
    vector_41 = _vector("<OMI>4</OMI>", "<OMI>1</OMI>")
    vector_2m1_scale = _vector("<OMI>2</OMI>", "<OMI>-1</OMI>")
    vector_6m3 = _vector("<OMI>6</OMI>", "<OMI>-3</OMI>")
    vector_20 = _vector("<OMI>2</OMI>", "<OMI>0</OMI>")
    vector_03 = _vector("<OMI>0</OMI>", "<OMI>3</OMI>")
    complex_12 = _complex("<OMI>1</OMI>", "<OMI>2</OMI>")
    complex_3m1 = _complex("<OMI>3</OMI>", "<OMI>-1</OMI>")
    complex_55 = _complex("<OMI>5</OMI>", "<OMI>5</OMI>")
    complex_m21 = _complex("<OMI>-2</OMI>", "<OMI>1</OMI>")
    complex_m11 = _complex("<OMI>-1</OMI>", "<OMI>1</OMI>")
    return [
        _card(
            identifier="typed_vector2_component_addition",
            domain="high_school.vector",
            difficulty="standard",
            statement="(1,2) + (3,-1) = (4,1) as planar vectors.",
            openmath=_obj(_eq(_pals("vector_add", vector_12, vector_3m1), vector_41)),
            symbols=["pals2:vector_add", "linalg2:vector", "relation1:eq"],
            strategy="Apply componentwise addition and simplify each real coordinate.",
            steps=[
                "Recognize both inputs as V2, not scalar pairs.",
                "Apply the V2 × V2 → V2 signature of vector_add.",
                "Add the first coordinates.",
                "Add the second coordinates and compare the resulting V2.",
            ],
            lean_target=witnesses["typed_vector2_component_addition"][0],
            lean_witness=witnesses["typed_vector2_component_addition"][1],
            statement_to_openmath="The two coordinate pairs are encoded only by linalg2:vector with exactly two real entries.",
            openmath_to_lean="The private vector_add is lowered to Vector2 coordinate addition in the witness.",
        ),
        _card(
            identifier="typed_vector2_scalar_multiple",
            domain="high_school.vector",
            difficulty="standard",
            statement="3(2,-1) = (6,-3) for a planar vector.",
            openmath=_obj(
                _eq(_pals("vector_scale", "<OMI>3</OMI>", vector_2m1_scale), vector_6m3)
            ),
            symbols=["pals2:vector_scale", "linalg2:vector", "relation1:eq"],
            strategy="Use the typed scalar action R × V2 → V2 coordinatewise.",
            steps=[
                "Infer 3 as R and the coordinate pair as V2.",
                "Reject any scalar-scalar or vector-vector interpretation.",
                "Multiply each coordinate by the scalar.",
                "Compare the resulting V2 with (6,-3).",
            ],
            lean_target=witnesses["typed_vector2_scalar_multiple"][0],
            lean_witness=witnesses["typed_vector2_scalar_multiple"][1],
            statement_to_openmath="The first argument of vector_scale is R and its second is V2 by signature.",
            openmath_to_lean="The witness uses the coordinatewise Vector2 scalar-action definition.",
        ),
        _card(
            identifier="typed_vector2_dot_product_orthogonality",
            domain="high_school.vector",
            difficulty="standard",
            statement="The planar vectors (1,2) and (2,-1) are orthogonal.",
            openmath=_obj(
                _eq(
                    _app(_standard("linalg1", "scalarproduct"), vector_12, vector_2m1),
                    "<OMI>0</OMI>",
                )
            ),
            symbols=["linalg1:scalarproduct", "linalg2:vector", "relation1:eq"],
            strategy="Compute the typed V2 scalar product and show that its real value is zero.",
            steps=[
                "Infer both operands of scalarproduct as V2.",
                "Expand the planar dot product.",
                "Evaluate 1·2 + 2·(-1).",
                "Use the zero result as the orthogonality criterion.",
            ],
            lean_target=witnesses["typed_vector2_dot_product_orthogonality"][0],
            lean_witness=witnesses["typed_vector2_dot_product_orthogonality"][1],
            statement_to_openmath="linalg1:scalarproduct is admitted only at V2 × V2 → R in this profile.",
            openmath_to_lean="The witness uses the corresponding planar coordinate dot product.",
        ),
        _card(
            identifier="typed_vector2_triangle_area_determinant",
            domain="high_school.vector",
            difficulty="standard",
            statement="The triangle spanned by (2,0) and (0,3) has area 3.",
            openmath=_obj(
                _eq(
                    _app(
                        _standard("arith1", "divide"),
                        _app(
                            _standard("arith1", "abs"),
                            _pals("determinant2", vector_20, vector_03),
                        ),
                        "<OMI>2</OMI>",
                    ),
                    "<OMI>3</OMI>",
                )
            ),
            symbols=[
                "pals2:determinant2",
                "linalg2:vector",
                "arith1:abs",
                "arith1:divide",
                "relation1:eq",
            ],
            strategy="Compute the signed V2 determinant, take its real absolute value, and halve it.",
            steps=[
                "Infer each side as V2.",
                "Apply determinant2 : V2 × V2 → R.",
                "Evaluate the signed determinant as 6.",
                "Take its absolute value and divide the real result by 2.",
            ],
            lean_target=witnesses["typed_vector2_triangle_area_determinant"][0],
            lean_witness=witnesses["typed_vector2_triangle_area_determinant"][1],
            statement_to_openmath="Only scalar arith1 operations are used after determinant2 returns R.",
            openmath_to_lean="The witness lowers determinant2 to the 2×2 coordinate determinant and uses |det|/2.",
        ),
        _card(
            identifier="typed_complex_cartesian_multiplication",
            domain="high_school.complex_numbers",
            difficulty="standard",
            statement="(1+2i)(3-i)=5+5i.",
            openmath=_obj(
                _eq(_pals("complex_mul", complex_12, complex_3m1), complex_55)
            ),
            symbols=["pals2:complex_mul", "complex1:complex_cartesian", "relation1:eq"],
            strategy="Multiply in the C carrier and use i²=-1 in Cartesian coordinates.",
            steps=[
                "Infer every Cartesian constructor as C.",
                "Apply complex_mul : C × C → C.",
                "Expand the product using i²=-1.",
                "Collect real and imaginary components as (5,5).",
            ],
            lean_target=witnesses["typed_complex_cartesian_multiplication"][0],
            lean_witness=witnesses["typed_complex_cartesian_multiplication"][1],
            statement_to_openmath="The private complex_mul prevents polymorphic arith1 multiplication from accepting non-C values.",
            openmath_to_lean="The witness uses ℂ multiplication with Complex.I_sq.",
        ),
        _card(
            identifier="typed_complex_conjugate_norm_square",
            domain="high_school.complex_numbers",
            difficulty="standard",
            statement="For every complex z, z·conj(z) is the real squared norm embedded in C.",
            openmath=_forall_complex(
                "z",
                _eq(
                    _pals(
                        "complex_mul",
                        '<OMV name="z"/>',
                        _app(_standard("complex1", "conjugate"), '<OMV name="z"/>'),
                    ),
                    _complex(
                        _pals("complex_norm_sq", '<OMV name="z"/>'), "<OMI>0</OMI>"
                    ),
                ),
            ),
            symbols=[
                "pals2:forall_complex",
                "pals2:complex_mul",
                "pals2:complex_norm_sq",
                "complex1:conjugate",
                "complex1:complex_cartesian",
                "relation1:eq",
            ],
            strategy="Use conjugation to eliminate the imaginary component and identify the squared norm.",
            steps=[
                "Bind z with the C-only quantifier.",
                "Infer conjugate(z) as C.",
                "Multiply two C values with complex_mul.",
                "Embed complex_norm_sq(z):R as the Cartesian complex number (normSq,0).",
            ],
            lean_target=witnesses["typed_complex_conjugate_norm_square"][0],
            lean_witness=witnesses["typed_complex_conjugate_norm_square"][1],
            statement_to_openmath="The profile distinguishes complex multiplication from the real-valued complex_norm_sq operation.",
            openmath_to_lean="The Cartesian embedding (r,0) corresponds to coercing Complex.normSq z to ℂ.",
        ),
        _card(
            identifier="typed_complex_multiply_i_quarter_turn",
            domain="high_school.complex_numbers",
            difficulty="standard",
            statement="(1+2i)i=-2+i, a quarter-turn in the complex plane.",
            openmath=_obj(
                _eq(
                    _pals("complex_mul", complex_12, _standard("nums1", "i")),
                    complex_m21,
                )
            ),
            symbols=[
                "pals2:complex_mul",
                "complex1:complex_cartesian",
                "nums1:i",
                "relation1:eq",
            ],
            strategy="Use the C-valued nums1:i constant and simplify i²=-1.",
            steps=[
                "Infer the Cartesian input and nums1:i as C.",
                "Apply complex_mul : C × C → C.",
                "Distribute i across the Cartesian form.",
                "Replace i² with -1 and collect (-2,1).",
            ],
            lean_target=witnesses["typed_complex_multiply_i_quarter_turn"][0],
            lean_witness=witnesses["typed_complex_multiply_i_quarter_turn"][1],
            statement_to_openmath="nums1:i is C in this profile and cannot be multiplied with a V2 or bare R.",
            openmath_to_lean="The witness evaluates the corresponding ℂ product.",
        ),
        _card(
            identifier="typed_complex_argument_quadrant_two",
            domain="high_school.complex_numbers",
            difficulty="standard",
            statement="The principal argument of -1+i is positive (its point lies in quadrant II).",
            openmath=_obj(
                _app(
                    _standard("relation1", "gt"),
                    _app(_standard("complex1", "argument"), complex_m11),
                    "<OMI>0</OMI>",
                )
            ),
            symbols=["complex1:argument", "complex1:complex_cartesian", "relation1:gt"],
            strategy="Use the sign of the imaginary component together with the principal-argument convention.",
            steps=[
                "Construct -1+i as a C value.",
                "Infer complex1:argument as an R value.",
                "Use the positive imaginary part to rule out a negative argument.",
                "Use the negative real part to rule out argument zero, yielding positivity.",
            ],
            lean_target=witnesses["typed_complex_argument_quadrant_two"][0],
            lean_witness=witnesses["typed_complex_argument_quadrant_two"][1],
            statement_to_openmath="complex1:argument is used only as C → R and compared by a real order relation.",
            openmath_to_lean="The witness uses Mathlib's principal Complex.arg lemmas for the same Cartesian complex number.",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    registry = (ROOT / REGISTRY).read_bytes()
    design = (ROOT / DESIGN).read_bytes()
    toolchain = (ROOT / TOOLCHAIN).read_bytes()
    witnesses = (ROOT / WITNESSES).read_bytes()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-geometry-complex-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "phase-A vector and complex-plane typed authoring evidence only",
            "admission": (
                "not admitted to the generic DB, seed, embedding index, or PFI package; "
                "eligible only for local typed catalog preparation"
            ),
            "revision": "typed-geometry-complex-v1-local-r1",
        },
        "profile": {
            "id": "typed-geometry-complex-v1",
            "validator": "pals_agent.typed_geometry_complex.validate_canonical_typed_geometry_complex_openmath_xml",
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
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../testdata/typed-geometry-complex-v1/vector-complex-phase-a-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_candidate_cards": _cards(),
        "deferred_backlog_cards": [
            {
                "id": "geometry_line_through_two_points",
                "disposition": "explicitly_rejected_or_deferred",
                "reason": "Phase B needs distinct Point2 and Line2 sorts plus incidence; V2 is not an affine point.",
            },
            {
                "id": "geometry_circle_through_three_points",
                "disposition": "explicitly_rejected_or_deferred",
                "reason": "Phase B needs Circle2 incidence and non-collinearity semantics.",
            },
            {
                "id": "geometry_perpendicular_bisector_locus",
                "disposition": "explicitly_rejected_or_deferred",
                "reason": "Phase B needs Point2 distance, midpoint, and Line2/perpendicularity sorts.",
            },
            {
                "id": "geometry_reflection_in_line",
                "disposition": "explicitly_rejected_or_deferred",
                "reason": "Phase B needs a line-typed reflection operation; points must remain distinct from vectors.",
            },
        ],
    }
    payload["manifest_digest"] = {
        "algorithm": "sha256",
        "input": MANIFEST_DIGEST_INPUT,
        "sha256": _sha256_bytes(rfc8785.dumps(payload)),
    }
    validate_typed_geometry_complex_manifest(payload, repository_root=ROOT)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "docs/typed-geometry-complex-v1-authoring-manifest.proposal.json",
    )
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
