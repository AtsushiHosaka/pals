"""Generate immutable local-authoring evidence for ``typed-math-matrix-v1``.

The script validates every candidate with the isolated matrix profile before
sealing the manifest.  The manifest remains proposal-only until independent
project review; it never seeds the generic Draft catalog or database.
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
MATRIX_REGISTRY_RELATIVE_PATH = (
    "pals-agent/pals_agent/content_dictionaries/typed-math-matrix-v1-registry.json"
)
MATRIX_REGISTRY_PATH = ROOT / MATRIX_REGISTRY_RELATIVE_PATH
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_matrix_profile import canonicalize_typed_matrix_openmath_xml

TYPED = "urn:pals:openmath:typed-math:v1"
STANDARD = "http://www.openmath.org/cd"
OPENMATH = "http://www.openmath.org/OpenMath"
MANIFEST_DIGEST_INPUT = (
    "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted"
)


def tag(name: str, *children: str, **attributes: str) -> str:
    attrs = "".join(f' {key}="{value}"' for key, value in attributes.items())
    return f"<{name}{attrs}>{''.join(children)}</{name}>"


def oms(cd: str, name: str, *, cdbase: str = TYPED) -> str:
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def omi(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator, *arguments)


def matrix(name: str, *arguments: str) -> str:
    return app(oms("matrix1", name), *arguments)


def relation_eq(left: str, right: str) -> str:
    return app(oms("relation1", "eq", cdbase=STANDARD), left, right)


def field_sort() -> str:
    return oms("algebra1", "Field")


def matrix_sort(rows: int, columns: int) -> str:
    return matrix("Matrix", omv("K"), omi(rows), omi(columns))


def annotation(sort: str, variable: str) -> str:
    return tag(
        "OMATTR",
        tag("OMATP", oms("typed1", "type"), sort),
        omv(variable),
    )


def forall_over_field(body: str) -> str:
    return tag(
        "OMOBJ",
        tag(
            "OMBIND",
            oms("typed1", "forall"),
            tag("OMBVAR", annotation(field_sort(), "K")),
            body,
        ),
        xmlns=OPENMATH,
        version="2.0",
    )


def field_nat(value: int) -> str:
    if value < 0:
        raise ValueError("field_nat_cast accepts only nonnegative integer literals")
    return matrix("field_nat_cast", omv("K"), omi(value))


def literal(rows: list[list[int]]) -> str:
    row_count = len(rows)
    column_count = len(rows[0])
    if not row_count or not column_count or any(len(row) != column_count for row in rows):
        raise ValueError("matrix literal must be nonempty and rectangular")
    return matrix(
        "literal",
        omv("K"),
        omi(row_count),
        omi(column_count),
        *(field_nat(entry) for row in rows for entry in row),
    )


def canonical(raw_xml: str) -> str:
    return canonicalize_typed_matrix_openmath_xml(raw_xml)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def card(
    *,
    identifier: str,
    difficulty: str,
    statement: str,
    xml_body: str,
    strategy: str,
    steps: list[str],
    lean_target: str,
    lean_witness: str,
    statement_to_openmath: str,
    openmath_to_lean: str,
) -> dict[str, Any]:
    raw_xml = forall_over_field(xml_body)
    canonical_xml = canonical(raw_xml)
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} needs 4..8 sketch steps")
    return {
        "id": identifier,
        "domain": "linear_algebra_matrices",
        "difficulty": difficulty,
        "authoring_status": "complete_xml_profile_semantics_verified_locally_not_admitted",
        "canonical_statement": statement,
        "openmath_xml": raw_xml,
        "canonical_openmath_xml": canonical_xml,
        "canonical_openmath_xml_sha256": sha256_text(canonical_xml),
        "proof_strategy": strategy,
        "sketch_steps": steps,
        "lean": {
            "target": lean_target,
            "target_sha256": sha256_text(lean_target),
            "witness": lean_witness,
            "witness_sha256": sha256_text(lean_witness),
        },
        "statement_openmath_lean_alignment_review": {
            "status": "reviewed_by_local_authoring_agent_not_admitted",
            "statement_to_openmath": statement_to_openmath,
            "openmath_to_lean": openmath_to_lean,
            "admission_gate": "The isolated typed-math-matrix-v1 validator accepted this exact XML locally; obtain independent project review before any catalog/DB admission.",
        },
    }


LEAN_PREAMBLE = """import Mathlib

abbrev Mat2 (K : Type*) := Matrix (Fin 2) (Fin 2) K
abbrev Vec2 (K : Type*) := Fin 2 → K

def A {K : Type*} [Field K] : Mat2 K := !![1, 2; 3, 4]
def B {K : Type*} [Field K] : Mat2 K := !![2, 0; 1, 2]
def P {K : Type*} [Field K] : Mat2 K := !![0, 1; 1, 0]
def x {K : Type*} [Field K] : Vec2 K := ![2, -1]
def b {K : Type*} [Field K] : Vec2 K := ![0, 2]

def IsMatrixInverse {K : Type*} [Field K] (M N : Mat2 K) : Prop := M * N = 1 ∧ N * M = 1

"""


LEAN_TARGETS = {
    "typed_matrix_v1_literal_add_2x2": "∀ {K : Type*} [Field K], A (K := K) + B (K := K) = (!![3, 2; 4, 6] : Mat2 K)",
    "typed_matrix_v1_literal_mul_2x2": "∀ {K : Type*} [Field K], A (K := K) * B (K := K) = (!![4, 4; 10, 8] : Mat2 K)",
    "typed_matrix_v1_literal_scale_2x2": "∀ {K : Type*} [Field K], (3 : K) • A (K := K) = (!![3, 6; 9, 12] : Mat2 K)",
    "typed_matrix_v1_literal_transpose_2x2": "∀ {K : Type*} [Field K], Matrix.transpose (A (K := K)) = (!![1, 3; 2, 4] : Mat2 K)",
    "typed_matrix_v1_exchange_self_inverse": "∀ {K : Type*} [Field K], IsMatrixInverse (P (K := K)) (P (K := K))",
    "typed_matrix_v1_rank_identity_2": "∀ {K : Type*} [Field K], (1 : Mat2 K).rank = 2",
    "typed_matrix_v1_determinant_literal_2x2": "∀ {K : Type*} [Field K], (A (K := K)).det = (-2 : K)",
    "typed_matrix_v1_mul_vec_solution_2x2": "∀ {K : Type*} [Field K], Matrix.mulVec (A (K := K)) (x (K := K)) = b (K := K)",
}


LEAN_WITNESSES = {
    "typed_matrix_v1_literal_add_2x2": """example : ∀ {K : Type*} [Field K], A (K := K) + B (K := K) = (!![3, 2; 4, 6] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A, B] <;> ring
""",
    "typed_matrix_v1_literal_mul_2x2": """example : ∀ {K : Type*} [Field K], A (K := K) * B (K := K) = (!![4, 4; 10, 8] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A, B, Matrix.mul_apply, Fin.sum_univ_succ] <;> ring
""",
    "typed_matrix_v1_literal_scale_2x2": """example : ∀ {K : Type*} [Field K], (3 : K) • A (K := K) = (!![3, 6; 9, 12] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A] <;> ring
""",
    "typed_matrix_v1_literal_transpose_2x2": """example : ∀ {K : Type*} [Field K], Matrix.transpose (A (K := K)) = (!![1, 3; 2, 4] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A]
""",
    "typed_matrix_v1_exchange_self_inverse": """example : ∀ {K : Type*} [Field K], IsMatrixInverse (P (K := K)) (P (K := K)) := by
  intro K _
  dsimp [IsMatrixInverse]
  constructor <;> ext i j <;> fin_cases i <;> fin_cases j <;>
    simp [P, Matrix.mul_apply, Fin.sum_univ_succ]
""",
    "typed_matrix_v1_rank_identity_2": """example : ∀ {K : Type*} [Field K], (1 : Mat2 K).rank = 2 := by
  intro K _
  simp
""",
    "typed_matrix_v1_determinant_literal_2x2": """example : ∀ {K : Type*} [Field K], (A (K := K)).det = (-2 : K) := by
  intro K _
  simp [A, Matrix.det_fin_two]
  ring
""",
    "typed_matrix_v1_mul_vec_solution_2x2": """example : ∀ {K : Type*} [Field K], Matrix.mulVec (A (K := K)) (x (K := K)) = b (K := K) := by
  intro K _
  funext i
  fin_cases i <;> simp [A, x, b, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
  all_goals ring
""",
}


def witness_bundle() -> str:
    return LEAN_PREAMBLE + "\n".join(LEAN_WITNESSES.values())


def profile_signature_contract() -> dict[str, Any]:
    return {
        "source": "docs/matrix-typed-profile-v1-design.md#minimal-matrix1-signatures",
        "status": "implemented_local_evidence_not_independently_reviewed",
        "sorts": {
            "Field": "algebra1:Field",
            "Elem(K)": "typed1:Elem(K)",
            "Matrix(K,m,n)": "matrix1:Matrix(K,m,n), with literal 1 <= m,n <= 8",
            "ColumnVector(K,n)": "matrix1:ColumnVector(K,n), with literal 1 <= n <= 8",
            "Nat": "typed1:Nat",
        },
        "symbols": {
            "matrix1:field_nat_cast": "(K : Field, OMI n where n >= 0) -> Elem(K)",
            "matrix1:literal": "(K,m,n, exactly m*n entries : Elem(K)) -> Matrix(K,m,n)",
            "matrix1:column_literal": "(K,n, exactly n entries : Elem(K)) -> ColumnVector(K,n)",
            "matrix1:zero": "(K,m,n) -> Matrix(K,m,n)",
            "matrix1:neg": "Matrix(K,m,n) -> Matrix(K,m,n)",
            "matrix1:add": "Matrix(K,m,n) x Matrix(K,m,n) -> Matrix(K,m,n)",
            "matrix1:scale": "Elem(K) x Matrix(K,m,n) -> Matrix(K,m,n)",
            "matrix1:mul": "Matrix(K,m,n) x Matrix(K,n,p) -> Matrix(K,m,p)",
            "matrix1:transpose": "Matrix(K,m,n) -> Matrix(K,n,m)",
            "matrix1:determinant": "Matrix(K,n,n) -> Elem(K)",
            "matrix1:is_inverse": "Matrix(K,n,n) x Matrix(K,n,n) -> Prop",
            "matrix1:rank": "Matrix(K,m,n) -> Nat",
            "matrix1:identity": "(K,n) -> Matrix(K,n,n)",
            "matrix1:mul_vec": "Matrix(K,m,n) x ColumnVector(K,n) -> ColumnVector(K,m)",
        },
        "intentional_absences": [
            "No Elem(K) negation, addition, multiplication, or subtraction operator is in v1.",
            "No total matrix_inverse or solve operator is in v1; is_inverse and mul_vec are the available predicates/terms.",
            "No Field-to-CommRing coercion may be assumed for algebra1:ring_neg.",
        ],
    }


def build_manifest() -> dict[str, Any]:
    a = literal([[1, 2], [3, 4]])
    b_matrix = literal([[2, 0], [1, 2]])
    exchange = literal([[0, 1], [1, 0]])
    contract = profile_signature_contract()
    cards = [
        card(
            identifier="typed_matrix_v1_literal_add_2x2",
            difficulty="introductory",
            statement="For every field K, the 2 by 2 matrices [[1, 2], [3, 4]] and [[2, 0], [1, 2]] over K sum to [[3, 2], [4, 6]].",
            xml_body=relation_eq(matrix("add", a, b_matrix), literal([[3, 2], [4, 6]])),
            strategy="Add corresponding entries and normalize the field-natural casts.",
            steps=[
                "setup: Fix the field K and the two literal 2 by 2 matrices.",
                "entrywise: Expand matrix1:add at each of the four row-column positions.",
                "calculate: Add the corresponding field elements.",
                "normalize: Rewrite the sums of field_nat_cast values as the displayed entries.",
                "conclude: Extensionality gives the stated matrix equality.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_literal_add_2x2"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_literal_add_2x2"],
            statement_to_openmath="exact: both concrete matrices, their common field K, and the result use matrix1:literal and matrix1:add with shape Matrix(K,2,2).",
            openmath_to_lean="exact under the signature contract: field_nat_cast lowers to field numerals and Matrix(Fin 2, Fin 2, K) addition is entrywise addition.",
        ),
        card(
            identifier="typed_matrix_v1_literal_mul_2x2",
            difficulty="standard",
            statement="For every field K, [[1, 2], [3, 4]] times [[2, 0], [1, 2]] equals [[4, 4], [10, 8]].",
            xml_body=relation_eq(matrix("mul", a, b_matrix), literal([[4, 4], [10, 8]])),
            strategy="Compute the four dot products in the common inner dimension two.",
            steps=[
                "setup: Fix K and identify both factors as Matrix(K,2,2).",
                "shape: Use matrix1:mul with matching inner dimension 2.",
                "dot-products: Expand each of the four row-column dot products.",
                "normalize: Simplify the field-natural casts and products.",
                "conclude: Use matrix extensionality to obtain the literal result.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_literal_mul_2x2"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_literal_mul_2x2"],
            statement_to_openmath="exact: the XML has two Matrix(K,2,2) operands, so the product and its Matrix(K,2,2) result have the same dimensions as the statement.",
            openmath_to_lean="exact under the signature contract: matrix1:mul lowers to Lean matrix multiplication over Fin 2 and the explicit literals lower to the displayed field-valued matrices.",
        ),
        card(
            identifier="typed_matrix_v1_literal_scale_2x2",
            difficulty="introductory",
            statement="For every field K, scaling [[1, 2], [3, 4]] by the field element 3 gives [[3, 6], [9, 12]].",
            xml_body=relation_eq(matrix("scale", field_nat(3), a), literal([[3, 6], [9, 12]])),
            strategy="Multiply each matrix entry by the explicitly cast scalar 3.",
            steps=[
                "setup: Fix K and form field_nat_cast(K,3).",
                "shape: Confirm the scalar and matrix have the shared field parameter K.",
                "entrywise: Expand matrix1:scale at each of the four entries.",
                "normalize: Evaluate the four field products.",
                "conclude: Apply matrix extensionality.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_literal_scale_2x2"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_literal_scale_2x2"],
            statement_to_openmath="exact: 3 is not a bare OMI in a field position; it is matrix1:field_nat_cast(K,3), and all matrices have shape Matrix(K,2,2).",
            openmath_to_lean="exact under the signature contract: matrix1:scale lowers to Lean scalar multiplication by `(3 : K)`.",
        ),
        card(
            identifier="typed_matrix_v1_literal_transpose_2x2",
            difficulty="introductory",
            statement="For every field K, the transpose of [[1, 2], [3, 4]] is [[1, 3], [2, 4]].",
            xml_body=relation_eq(matrix("transpose", a), literal([[1, 3], [2, 4]])),
            strategy="Swap row and column indices in the literal matrix.",
            steps=[
                "setup: Fix K and the literal Matrix(K,2,2).",
                "transpose: Apply matrix1:transpose, which reverses its two dimensions.",
                "index: Compare each result entry with the original entry at swapped indices.",
                "assemble: Read off the four entries of the transposed literal.",
                "conclude: Use matrix extensionality.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_literal_transpose_2x2"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_literal_transpose_2x2"],
            statement_to_openmath="exact: the input and output are explicitly Matrix(K,2,2), and matrix1:transpose has precisely that square-shape result here.",
            openmath_to_lean="exact under the signature contract: matrix1:transpose lowers to Matrix.transpose and the literal entries retain their field casts.",
        ),
        card(
            identifier="typed_matrix_v1_exchange_self_inverse",
            difficulty="standard",
            statement="For every field K, the exchange matrix [[0, 1], [1, 0]] is a two-sided inverse of itself.",
            xml_body=matrix("is_inverse", exchange, exchange),
            strategy="Multiply the exchange matrix by itself in both orders and obtain the identity.",
            steps=[
                "setup: Fix K and let P be the displayed Matrix(K,2,2).",
                "predicate: Expand matrix1:is_inverse into its two identity-product requirements.",
                "left-product: Compute P times P entrywise.",
                "right-product: The same calculation supplies the reverse product.",
                "conclude: Both products are identity(K,2), so is_inverse(P,P) holds.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_exchange_self_inverse"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_exchange_self_inverse"],
            statement_to_openmath="exact: the English two-sided-inverse assertion is represented by the profile's primitive is_inverse(P,P), not by an undefined total inverse operator.",
            openmath_to_lean="exact under the stated lowering: matrix1:is_inverse(M,N) is the conjunction `M * N = 1 ∧ N * M = 1` in Matrix(Fin 2, Fin 2, K).",
        ),
        card(
            identifier="typed_matrix_v1_rank_identity_2",
            difficulty="standard",
            statement="For every field K, the rank of the 2 by 2 identity matrix over K is the natural number 2.",
            xml_body=relation_eq(matrix("rank", matrix("identity", omv("K"), omi(2))), omi(2)),
            strategy="Use that the identity map on a two-dimensional vector space has full rank.",
            steps=[
                "setup: Fix K and form identity(K,2).",
                "typing: Apply matrix1:rank, whose codomain is Nat rather than Elem(K).",
                "linear-map: Identify the matrix with the identity linear map on a two-dimensional space.",
                "rank: Its image is the full two-dimensional space.",
                "conclude: The natural rank is OMI 2.",
            ],
            lean_target=LEAN_TARGETS["typed_matrix_v1_rank_identity_2"],
            lean_witness=LEAN_WITNESSES["typed_matrix_v1_rank_identity_2"],
            statement_to_openmath="exact: the statement explicitly calls the result a natural number; XML compares matrix1:rank(identity(K,2)) with the Nat literal 2, never a field cast.",
            openmath_to_lean="exact under the signature contract: matrix1:rank lowers to Matrix.rank and the RHS is Lean's natural number 2.",
        ),
    ]
    for entry in cards:
        target = entry["lean"]["target"]
        witness = entry["lean"]["witness"]
        if target not in witness or witness not in witness_bundle():
            raise ValueError(f"Lean evidence for {entry['id']} is not bundle-bound")

    excluded = [
        {
            "id": "typed_matrix_v1_determinant_literal_2x2",
            "canonical_statement": "For every field K, the determinant of [[1, 2], [3, 4]] is the field element -2.",
            "lean": {
                "target": LEAN_TARGETS["typed_matrix_v1_determinant_literal_2x2"],
                "target_sha256": sha256_text(LEAN_TARGETS["typed_matrix_v1_determinant_literal_2x2"]),
                "witness": LEAN_WITNESSES["typed_matrix_v1_determinant_literal_2x2"],
                "witness_sha256": sha256_text(LEAN_WITNESSES["typed_matrix_v1_determinant_literal_2x2"]),
            },
            "status": "excluded_no_profile_faithful_xml",
            "reason": "matrix1:determinant returns Elem(K), but the v1 signature contract has field_nat_cast only for nonnegative literals and no Elem(K) negation. matrix1:neg is matrix-valued, while algebra1:ring_neg cannot consume K : Field without a forbidden Field-to-CommRing coercion. Therefore `-2 : Elem(K)` has no well-typed XML term.",
            "required_profile_change": "Add an explicit `field_neg : Elem(K) -> Elem(K)` (or an equally explicit field scalar-expression module), define its Lean lowering, add hard negatives, and independently review the resulting XML.",
            "alignment_verdict": "The generic Lean theorem is valid, but it is not admission evidence for the current OpenMath signature. No fictitious complete XML is emitted.",
        },
        {
            "id": "typed_matrix_v1_mul_vec_solution_2x2",
            "canonical_statement": "For every field K, x = [2, -1] satisfies [[1, 2], [3, 4]] x = [0, 2].",
            "lean": {
                "target": LEAN_TARGETS["typed_matrix_v1_mul_vec_solution_2x2"],
                "target_sha256": sha256_text(LEAN_TARGETS["typed_matrix_v1_mul_vec_solution_2x2"]),
                "witness": LEAN_WITNESSES["typed_matrix_v1_mul_vec_solution_2x2"],
                "witness_sha256": sha256_text(LEAN_WITNESSES["typed_matrix_v1_mul_vec_solution_2x2"]),
            },
            "status": "excluded_no_profile_faithful_xml",
            "reason": "The only profile term for a field coefficient literal is field_nat_cast(K,n) with n >= 0. The witness vector contains -1, and no Elem(K) negation exists. Also v1 exposes mul_vec but no `solve` operator or uniqueness predicate; this card is aligned only as a verification that a named vector satisfies Ax=b, never as a claim that a solver returns it.",
            "required_profile_change": "Add explicit field negation for the vector entry. If future wording says `solve`, separately add a solution/uniqueness signature and a reviewed lowering; do not equate it with mul_vec by implication.",
            "alignment_verdict": "The Lean calculation compiles, but it cannot justify an XML card under the current signature. No fictitious complete XML is emitted.",
        },
    ]
    witness_text = witness_bundle()
    if len(cards) != 6 or len(excluded) != 2:
        raise ValueError("expected six profile-faithful cards and two exclusions")
    return {
        "schema_version": "pals.typed-math-matrix-v1-authoring-manifest.proposal.v1",
        "proposal_status": "not_admitted_requires_independent_project_review",
        "profile": {
            "id": "typed-math-matrix-v1",
            "validator": "pals_agent.typed_matrix_profile.validate_canonical_typed_matrix_openmath_xml",
            "validator_status": "implemented_local_evidence_not_independently_reviewed",
            "canonicalizer": "openmath-cdbase-alpha-c14n-v4",
            "canonicalization_scope": "typed-math-matrix-v1 semantic validation followed by core XML/C14N",
            "admission_openmath_field": "canonical_openmath_xml",
            "signature_contract": contract,
            "signature_contract_sha256": "sha256:" + hashlib.sha256(rfc8785.dumps(contract)).hexdigest(),
            "content_dictionary_bundle": {
                "relative_path": MATRIX_REGISTRY_RELATIVE_PATH,
                "sha256": sha256_bytes(MATRIX_REGISTRY_PATH.read_bytes()),
                "digest_input": "exact UTF-8 bytes of the named registry/CD bundle",
            },
            "lean_toolchain": {
                "path": "pals-agent/lean-workspace/lean-toolchain",
                "value": (AGENT_ROOT / "lean-workspace/lean-toolchain").read_text(encoding="utf-8").rstrip("\n"),
                "sha256": sha256_bytes((AGENT_ROOT / "lean-workspace/lean-toolchain").read_bytes()),
                "digest_input": "exact UTF-8 bytes of the named lean-toolchain file",
            },
        },
        "lean_witness_bundle": {
            "path": "docs/matrix-typed-profile-v1-authoring-witnesses.proposal.lean",
            "sha256": sha256_text(witness_text),
            "digest_input": "exact UTF-8 bytes of the named Lean file, including import and final newline",
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/matrix-typed-profile-v1-authoring-witnesses.proposal.lean",
            "verification_status": "verified_local_pinned_workspace",
            "scope": "all eight original Lean witnesses; six are profile-faithful candidates and two are recorded exclusions",
        },
        "admitted_candidate_cards": cards,
        "excluded_witnesses": excluded,
        "manifest_digest": {},
    }


def seal(manifest: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(manifest)
    unsigned.pop("manifest_digest", None)
    manifest["manifest_digest"] = {
        "algorithm": "sha256",
        "input": MANIFEST_DIGEST_INPUT,
        "sha256": "sha256:" + hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest(),
    }
    return manifest


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/typed-math-matrix-v1-authoring-manifest.proposal.json",
    )
    parser.add_argument(
        "--lean-output",
        type=Path,
        default=ROOT / "docs/matrix-typed-profile-v1-authoring-witnesses.proposal.lean",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = seal(build_manifest())
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    lean_text = witness_bundle()
    if not lean_text.endswith("\n"):
        raise AssertionError("Lean witness bundle must end in a newline")
    if args.check:
        if args.output.read_text(encoding="utf-8") != manifest_text:
            raise SystemExit("matrix authoring manifest is stale; rerun this generator")
        if args.lean_output.read_text(encoding="utf-8") != lean_text:
            raise SystemExit("matrix Lean witness bundle is stale; rerun this generator")
        print("matrix authoring manifest and Lean bundle are current")
        return
    write_if_changed(args.output, manifest_text)
    write_if_changed(args.lean_output, lean_text)


if __name__ == "__main__":
    main()
