"""Generate the sealed local authoring manifest for ``typed-probability-v1``.

This script is deliberately profile-local.  It does not create a ProofDraft,
an embedding, a database row, or a Lean translation receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from pals_agent.typed_probability_profile import (
    TYPED_PROBABILITY_OPENMATH_CDBASE,
    canonicalize_typed_probability_openmath_xml,
    validate_canonical_typed_probability_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "docs/probability-typed-profile-v1-design.md"
COMPANION = ROOT / "docs/probability-typed-profile-v1-lean-companion.json"
WITNESS = ROOT / "docs/typed-probability-v1-authoring-witnesses.lean"
REGISTRY = ROOT / "pals-agent/pals_agent/content_dictionaries/typed-probability-v1-registry.json"
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
SCHEMA = "pals.typed-probability-v1.sealed-manifest.v1"
STATUS = "sealed_local_authoring_revision_not_admitted"


@dataclass(frozen=True, slots=True)
class Card:
    id: str
    canonical_statement: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    openmath_xml: str
    signature_trace: tuple[str, ...]
    lean_target: str
    lean_witness: str
    alignment: str
    conventions: dict[str, str]


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def oms(cd: str, name: str, *, standard: bool = False) -> str:
    cdbase = STANDARD if standard else TYPED_PROBABILITY_OPENMATH_CDBASE
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def typed(name: str) -> str:
    return oms("typed1", name)


def probability(name: str) -> str:
    return oms("probability1", name)


def app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def omi(value: int) -> str:
    if value < 0:
        raise ValueError("typed-probability-v1 authoring literals must be natural.")
    return f"<OMI>{value}</OMI>"


def declaration(name: str, sort: str) -> str:
    return f"<OMATTR><OMATP>{typed('type')}{sort}</OMATP>{omv(name)}</OMATTR>"


def sort_application(name: str, carrier: str) -> str:
    return app(probability(name), omv(carrier))


def forall(declarations: tuple[tuple[str, str], ...], body: str) -> str:
    declared = "".join(declaration(name, sort) for name, sort in declarations)
    return f"<OMBIND>{typed('forall')}<OMBVAR>{declared}</OMBVAR>{body}</OMBIND>"


def statement(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def relation(name: str, left: str, right: str) -> str:
    return app(oms("relation1", name, standard=True), left, right)


def implies(premise: str, conclusion: str) -> str:
    return app(oms("logic1", "implies", standard=True), premise, conclusion)


def papp(name: str, *arguments: str) -> str:
    return app(probability(name), *arguments)


def nat_add(left: str, right: str) -> str:
    return papp("nat_add", left, right)


def choose(left: str, right: str) -> str:
    return papp("choose", left, right)


def real_of_int(value: int) -> str:
    return papp("real_of_int", omi(value))


def prob_to_real(value: str) -> str:
    return papp("prob_to_real", value)


def pmf(n: str, p: str, outcome: str) -> str:
    return papp("pmf", papp("binomial_distribution", n, p), outcome)


def _source() -> dict[str, dict[str, object]]:
    payload = json.loads(COMPANION.read_text(encoding="utf-8"))
    cards = payload.get("admitted_cards")
    if not isinstance(cards, list):
        raise TypeError("Probability Lean companion has no admitted cards.")
    result: dict[str, dict[str, object]] = {}
    for item in cards:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise TypeError("Probability Lean companion card is invalid.")
        result[item["id"]] = item
    if len(result) != 10:
        raise ValueError("typed-probability-v1 must bind exactly ten reviewed source cards.")
    return result


def _lean(card_id: str) -> tuple[str, str]:
    source = _source()[card_id]
    target = source.get("lean_target")
    witness = source.get("lean_witness")
    if not isinstance(target, str) or not isinstance(witness, str) or " := " not in target:
        raise ValueError(f"Probability Lean companion has invalid evidence for `{card_id}`.")
    prefix, _proof = target.rsplit(" := ", 1)
    return prefix, witness


def _choose_card(
    card_id: str,
    canonical_statement: str,
    body: str,
    declarations: tuple[tuple[str, str], ...],
    *,
    strategy: str,
    steps: tuple[str, ...],
    trace: tuple[str, ...],
    alignment: str,
) -> Card:
    target, witness = _lean(card_id)
    return Card(
        card_id,
        canonical_statement,
        strategy,
        steps,
        statement(forall(declarations, body)),
        trace,
        target,
        witness,
        alignment,
        {
            "scalar_convention": "All operators and literals are Nat; no Real or Probability coercion is present.",
            "boundary_convention": "Nat.choose and Nat division/subtraction use the total/truncated Lean Nat convention.",
            "probability_scope": "No sample-space, event, measure, or probability scalar is used.",
        },
    )


def adopted_cards() -> list[Card]:
    nat = typed("Nat")
    real = typed("Real")
    probability_sort = probability("Probability")
    sample_space = probability("SampleSpace")
    n, k, p = omv("n"), omv("k"), omv("p")
    one, two, zero = omi(1), omi(2), omi(0)
    basic_steps = (
        "Fix the natural-number variables in the displayed statement.",
        "Use the applicable boundary case or Pascal recurrence for Nat.choose.",
        "Keep every arithmetic operation in the natural numbers.",
        "Apply the reviewed Lean identity and close the universal statement.",
    )
    cards = [
        _choose_card(
            "prob_choose_zero",
            "For every natural number n, choose(n, 0) = 1.",
            relation("eq", choose(n, zero), one),
            (("n", nat),),
            strategy="Use the empty-selection boundary case for the total natural binomial coefficient.",
            steps=basic_steps,
            trace=("typed1:forall", "typed1:Nat", "probability1:choose", "relation1:eq"),
            alignment="The typed Nat binder, OMI boundary literal, and Lean Nat.choose target use the same total natural-number convention.",
        ),
        _choose_card(
            "prob_choose_self",
            "For every natural number n, choose(n, n) = 1.",
            relation("eq", choose(n, n), one),
            (("n", nat),),
            strategy="Use the all-elements selection boundary case.",
            steps=basic_steps,
            trace=("typed1:forall", "typed1:Nat", "probability1:choose", "relation1:eq"),
            alignment="Both occurrences of n have the same typed Nat binder and lower directly to Nat.choose n n.",
        ),
        _choose_card(
            "prob_choose_one",
            "For every natural number n, choose(n, 1) = n.",
            relation("eq", choose(n, one), n),
            (("n", nat),),
            strategy="Count singleton selections by the selected element, including the n=0 boundary case.",
            steps=basic_steps,
            trace=("typed1:forall", "typed1:Nat", "probability1:choose", "relation1:eq"),
            alignment="The XML and Lean target both use the total Nat.choose convention at n=0.",
        ),
        _choose_card(
            "prob_choose_pascal",
            "For natural n and k, choose(n + 1, k + 1) = choose(n, k) + choose(n, k + 1).",
            relation(
                "eq",
                choose(nat_add(n, one), nat_add(k, one)),
                nat_add(choose(n, k), choose(n, nat_add(k, one))),
            ),
            (("n", nat), ("k", nat)),
            strategy="Partition selections according to whether a distinguished element is selected.",
            steps=(
                "Fix arbitrary natural n and k.",
                "Partition (k+1)-element selections from n+1 elements by one distinguished element.",
                "Identify the two classes with choose(n,k) and choose(n,k+1).",
                "Use natural addition to combine the disjoint counts.",
                "Apply the reviewed Pascal Lean theorem.",
            ),
            trace=(
                "typed1:forall",
                "typed1:Nat",
                "probability1:nat_add",
                "probability1:choose",
                "relation1:eq",
            ),
            alignment="Every plus is probability1:nat_add and the Lean target is the same Nat.choose_succ_succ' identity.",
        ),
        _choose_card(
            "prob_choose_symmetry",
            "For natural n and k with k ≤ n, choose(n, n - k) = choose(n, k).",
            implies(
                relation("leq", k, n),
                relation("eq", choose(n, papp("nat_sub", n, k)), choose(n, k)),
            ),
            (("n", nat), ("k", nat)),
            strategy="Map a chosen subset to its complement while retaining the k≤n hypothesis.",
            steps=(
                "Fix natural n and k and assume k≤n.",
                "Take the complement of each k-element subset of an n-element set.",
                "The complement has natural size n-k under the stated hypothesis.",
                "This mapping is a bijection between the two selection families.",
                "Apply the reviewed Nat.choose_symm Lean theorem.",
            ),
            trace=(
                "typed1:forall",
                "typed1:Nat",
                "probability1:nat_sub",
                "probability1:choose",
                "relation1:leq",
                "logic1:implies",
            ),
            alignment="The XML retains the explicit k≤n premise and truncated Nat subtraction used by the reviewed Lean theorem.",
        ),
        _choose_card(
            "prob_choose_two",
            "For every natural number n, choose(n, 2) = n*(n - 1)/2.",
            relation(
                "eq",
                choose(n, two),
                papp("nat_div", papp("nat_mul", n, papp("nat_sub", n, one)), two),
            ),
            (("n", nat),),
            strategy="Count ordered pairs of distinct elements, then quotient by their two possible orders.",
            steps=(
                "Fix a natural number n.",
                "Count ordered choices of two distinct elements as n·(n-1).",
                "Each unordered two-element choice has exactly two orders.",
                "Use natural truncated division by two in the stated formula.",
                "Apply the reviewed Nat.choose_two_right Lean theorem.",
            ),
            trace=(
                "typed1:forall",
                "typed1:Nat",
                "probability1:choose",
                "probability1:nat_mul",
                "probability1:nat_sub",
                "probability1:nat_div",
                "relation1:eq",
            ),
            alignment="The denominator is probability1:nat_div, never real division; the Lean target is the same Nat formula.",
        ),
    ]
    omega, mu, c = omv("Omega"), omv("mu"), omv("c")
    target, witness = _lean("prob_expectation_constant")
    cards.append(
        Card(
            "prob_expectation_constant",
            "For a sample space Ω, a probability measure μ on Ω, and a real c, expectation(constant_rv(Ω,c), μ) = c.",
            "Use normalization of a probability measure to evaluate the integral of a constant function.",
            (
                "Fix the sample space, its probability measure, and a real constant c.",
                "Recognize constant_rv(Ω,c) as the constant real random variable.",
                "Derive integrability from constancy and the probability-measure normalization.",
                "Evaluate the Bochner integral of the constant function.",
                "Conclude that the expectation is c.",
            ),
            statement(
                forall(
                    (
                        ("Omega", sample_space),
                        ("mu", sort_application("ProbabilityMeasure", "Omega")),
                        ("c", real),
                    ),
                    relation(
                        "eq",
                        papp("expectation", papp("constant_rv", omega, c), mu),
                        c,
                    ),
                )
            ),
            (
                "typed1:forall",
                "probability1:SampleSpace",
                "probability1:ProbabilityMeasure",
                "typed1:Real",
                "probability1:constant_rv",
                "probability1:expectation",
                "relation1:eq",
            ),
            target,
            witness,
            "The typed SampleSpace and ProbabilityMeasure(Ω) bind the same carrier. expectation is accepted only for constant_rv, whose integrability is the documented profile derivation; the Lean target is the probability-measure constant integral.",
            {
                "probability_codomain": "No Probability scalar is silently lowered in this card; expectation has Real codomain.",
                "integrability_source": "The profile admits only expectation(constant_rv(Ω,c),μ), deriving integrability from constancy under ProbabilityMeasure(Ω).",
                "sample_space_dependency": "μ is declared as ProbabilityMeasure(Ω), exactly the carrier used by constant_rv(Ω,c).",
            },
        )
    )
    binomial_common = {
        "probability_codomain": "p has sort Probability, whose v1 meaning is a value in [0,1]; no Real-to-Probability constructor exists.",
        "real_lowering": "PMF and p enter Real arithmetic only through probability1:prob_to_real; choose enters only through probability1:nat_to_real.",
        "edge_convention": "Nat.choose is total, so the PMF formula retains its reviewed k>n boundary behavior.",
    }
    binomial_left = prob_to_real(pmf(n, p, k))
    binomial_right = papp(
        "real_mul",
        papp(
            "real_mul",
            papp("nat_to_real", choose(n, k)),
            papp("real_pow_nat", prob_to_real(p), k),
        ),
        papp(
            "real_pow_nat",
            papp("real_sub", real_of_int(1), prob_to_real(p)),
            papp("nat_sub", n, k),
        ),
    )
    for card_id, text, body, declarations, strategy, steps in (
        (
            "prob_binomial_pmf",
            "For natural n and k and probability p, the explicitly Real-lowered BinomialPMF(n,p,k) equals choose(n,k)·p^k·(1-p)^(n-k).",
            relation("eq", binomial_left, binomial_right),
            (("n", nat), ("k", nat), ("p", probability_sort)),
            "Apply the real-valued singleton PMF theorem after explicit Probability and Nat lowerings.",
            (
                "Fix natural n, natural k, and p : Probability.",
                "Form the Binomial distribution with the bounded Probability parameter p.",
                "Lower its PMF and p explicitly to Real.",
                "Lower choose(n,k) explicitly from Nat to Real.",
                "Apply the reviewed real singleton-PMF identity.",
            ),
        ),
        (
            "prob_binomial_zero_success",
            "For natural n and probability p, the explicitly Real-lowered BinomialPMF(n,p,0) equals (1-p)^n.",
            relation(
                "eq",
                prob_to_real(pmf(n, p, zero)),
                papp("real_pow_nat", papp("real_sub", real_of_int(1), prob_to_real(p)), n),
            ),
            (("n", nat), ("p", probability_sort)),
            "Specialize the reviewed Binomial PMF identity to the zero-success outcome.",
            (
                "Fix natural n and p : Probability.",
                "Use outcome 0 as a Nat literal in the Binomial PMF.",
                "Lower the PMF and p explicitly to Real.",
                "Simplify the choose(n,0) and p^0 factors.",
                "Conclude with the reviewed Lean simplification.",
            ),
        ),
        (
            "prob_binomial_all_success",
            "For natural n and probability p, the explicitly Real-lowered BinomialPMF(n,p,n) equals p^n.",
            relation("eq", prob_to_real(pmf(n, p, n)), papp("real_pow_nat", prob_to_real(p), n)),
            (("n", nat), ("p", probability_sort)),
            "Specialize the reviewed Binomial PMF identity to the all-success outcome n.",
            (
                "Fix natural n and p : Probability.",
                "Use the same Nat variable n as the PMF outcome.",
                "Lower the PMF and p explicitly to Real.",
                "Simplify the choose(n,n) and (1-p)^0 factors.",
                "Conclude with the reviewed Lean simplification.",
            ),
        ),
    ):
        target, witness = _lean(card_id)
        cards.append(
            Card(
                card_id,
                text,
                strategy,
                steps,
                statement(forall(declarations, body)),
                (
                    "typed1:forall",
                    "typed1:Nat",
                    "probability1:Probability",
                    "probability1:binomial_distribution",
                    "probability1:pmf",
                    "probability1:prob_to_real",
                    "probability1:nat_to_real",
                    "probability1:real_pow_nat",
                    "relation1:eq",
                ),
                target,
                witness,
                "The XML binds p at the bounded Probability sort, lowers each probability-valued PMF/p operand explicitly to Real, and lowers Nat.choose explicitly before Real multiplication. The Lean target uses p : I and Bin(...).real {k}, the reviewed matching lowering.",
                binomial_common,
            )
        )
    if len(cards) != 10:
        raise AssertionError("typed-probability-v1 card count drift")
    return cards


def _witness_text(cards: list[Card]) -> str:
    prelude = """import Mathlib
open MeasureTheory Set
open ProbabilityTheory
open scoped ProbabilityTheory unitInterval ENNReal

"""
    return prelude + "\n\n".join(
        f"-- manifest card: {card.id}\n{card.lean_target} := {card.lean_witness}" for card in cards
    ) + "\n"


def _rendered_card(card: Card, witness_text: str) -> dict[str, object]:
    if not 4 <= len(card.sketch_steps) <= 8 or any(not item.strip() for item in card.sketch_steps):
        raise ValueError(f"Card `{card.id}` needs 4..8 nonempty sketch steps.")
    marker = f"-- manifest card: {card.id}\n{card.lean_target} := {card.lean_witness}"
    if marker not in witness_text:
        raise ValueError(f"Lean witness file does not bind card `{card.id}`.")
    canonical = canonicalize_typed_probability_openmath_xml(card.openmath_xml)
    validate_canonical_typed_probability_openmath_xml(canonical)
    rendered = asdict(card)
    rendered.update(
        {
            "source_candidate_id": card.id,
            "openmath_profile": "typed-probability-v1",
            "openmath_xml_sha256": sha256(card.openmath_xml),
            "canonical_openmath_xml": canonical,
            "canonical_openmath_xml_sha256": sha256(canonical),
            "canonical_statement_sha256": sha256(card.canonical_statement),
            "lean_target_sha256": sha256(card.lean_target),
            "lean_witness_sha256": sha256(card.lean_witness),
            "compiler_receipt_status": "verified",
            "profile_validation_status": "validated_local_typed_probability_v1_sealed",
            "admission_status": "sealed-local-authoring-revision: not a DB Draft or a translation receipt",
            "embedding_namespace_preimage": "typed-probability-v1||" + canonical,
        }
    )
    return rendered


def _excluded_cards() -> list[dict[str, object]]:
    payload = json.loads(COMPANION.read_text(encoding="utf-8"))
    excluded = payload.get("excluded_cards")
    if not isinstance(excluded, list) or len(excluded) != 7:
        raise ValueError("Probability Lean companion must contain exactly seven excluded cards.")
    result: list[dict[str, object]] = []
    for item in excluded:
        if not isinstance(item, dict):
            raise TypeError("Probability excluded-card record is invalid.")
        copied = dict(item)
        copied["typed_profile_disposition"] = "explicitly_rejected_or_deferred"
        copied["registry_gate"] = (
            "conditional_probability and variance signatures are intentionally absent "
            "from typed-probability-v1."
        )
        result.append(copied)
    return result


def verify_lean() -> None:
    completed = subprocess.run(
        ["lake", "env", "lean", str(WITNESS)],
        cwd=ROOT / "pals-agent/lean-workspace",
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"Lean compilation failed:\n{completed.stdout}{completed.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-witness", action="store_true")
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()

    cards = adopted_cards()
    witness_text = _witness_text(cards)
    if args.write_witness:
        WITNESS.write_text(witness_text, encoding="utf-8")
    if not WITNESS.is_file() or WITNESS.read_text(encoding="utf-8") != witness_text:
        raise ValueError("Probability Lean witness is stale; rerun with --write-witness.")
    rendered = [_rendered_card(card, witness_text) for card in cards]
    excluded = _excluded_cards()
    manifest: dict[str, object] = {
        "schema_version": SCHEMA,
        "status": STATUS,
        "seal": {
            "scope": "local typed-probability authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-probability-v1-local-r1",
        },
        "immutability_contract": {
            "digest_algorithm": "sha256 over exact UTF-8 field bytes",
            "structural_openmath_c14n": "Canonical XML is produced only after typed-probability-v1 validation and profile C14N; raw authoring XML is separately hashed.",
            "mutation_rule": "Any change to statement, strategy, sketch, XML, signature trace, Lean evidence, design, registry, or excluded disposition creates a new sealed revision and manifest digest.",
            "profile_separation": "No card may enter generic-v1, typed-math-v1, the six-column Draft loader, or a shared embedding namespace.",
        },
        "profile": {
            "id": "typed-probability-v1",
            "typed_cdbase": TYPED_PROBABILITY_OPENMATH_CDBASE,
            "design_path": "docs/probability-typed-profile-v1-design.md",
            "design_sha256": sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-probability-v1-registry.json",
            "probability1_cd_bundle_sha256": sha256(REGISTRY.read_bytes()),
            "validator": "pals_agent.typed_probability_profile.validate_canonical_typed_probability_openmath_xml",
            "validator_version": "typed-probability-v1-local-r1",
            "canonicalizer_version": "openmath-v4-profile-c14n",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-probability-v1-authoring-witnesses.lean",
            "witness_file_sha256": sha256(witness_text),
            "toolchain": "leanprover/lean4:v4.32.0-rc1",
            "verification_status": "compiled when generator is run with --verify-lean; sealed evidence only, not an OpenMath-to-Lean translation receipt",
        },
        "admitted_card_count": len(rendered),
        "excluded_card_count": len(excluded),
        "cards": rendered,
        "excluded_cards": excluded,
    }
    unsigned = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    manifest["manifest_payload_sha256"] = sha256(unsigned)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.verify_lean:
        verify_lean()
    print(f"sealed_cards={len(rendered)} excluded_cards={len(excluded)} profile_c14n=validated")
    if args.verify_lean:
        print("lean=passed")


if __name__ == "__main__":
    main()
