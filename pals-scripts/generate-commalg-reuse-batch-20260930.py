"""Create a checked, unpublished ideal-theory expansion with the existing profile.

Run with pals-agent/.venv/bin/python. No provider calls or database writes occur.
The JSON is written only after exact profile validation and local Lean compilation.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_commutative_algebra import (
    canonicalize_typed_commutative_algebra_openmath_xml,
    validate_canonical_typed_commutative_algebra_openmath_xml,
)

PROFILE = "typed-commutative-algebra-v1"
BASE = "urn:pals:openmath:typed-commutative-algebra:v1"
STD = "http://www.openmath.org/cd"


def symbol(cd: str, name: str) -> str:
    base = STD if cd in {"logic1", "relation1"} else BASE
    return f'<OMS cdbase="{base}" cd="{cd}" name="{name}"/>'


def var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def app(cd: str, name: str, *args: str) -> str:
    return "<OMA>" + symbol(cd, name) + "".join(args) + "</OMA>"


def op(name: str, *args: str) -> str:
    return app("commalg1", name, var("R"), *args)


def eq(a: str, b: str) -> str:
    return app("relation1", "eq", a, b)


def logic(name: str, *args: str) -> str:
    return app("logic1", name, *args)


def iff(a: str, b: str) -> str:
    # The existing profile has no iff symbol: use the exact two implications.
    return logic("and", logic("implies", a, b), logic("implies", b, a))


def bind(kind: str, names: list[str], body: str, ring: bool = False) -> str:
    pairs = [("R", symbol("commalg1", "CommRing"))] if ring else []
    pairs += [(n, app("commalg1", "Ideal", var("R"))) for n in names]
    decls = "".join(
        "<OMATTR><OMATP>"
        + symbol("typed1", "type")
        + sort
        + "</OMATP>"
        + var(name)
        + "</OMATTR>"
        for name, sort in pairs
    )
    return (
        "<OMBIND>"
        + symbol("typed1", kind)
        + "<OMBVAR>"
        + decls
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


I, J, K, P = map(var, ["I", "J", "K", "P"])
top = op("ideal_top")
rad = lambda a: op("ideal_radical", a)
add = lambda a, b: op("ideal_sum", a, b)
mul = lambda a, b: op("ideal_product", a, b)
meet = lambda a, b: op("ideal_inf", a, b)
le = lambda a, b: op("ideal_le", a, b)
prime = lambda a: op("is_prime_ideal", a)
maximal = lambda a: op("is_maximal_ideal", a)
ne = lambda a, b: app("relation1", "neq", a, b)
cards: list[dict[str, object]] = []


def card(
    key: str,
    names: str,
    body: str,
    statement: str,
    strategy: str,
    steps: list[str],
    target: str,
    proof: str,
) -> None:
    xml = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind("forall", names.split(), body, ring=True)
        + "</OMOBJ>"
    )
    canonical = canonicalize_typed_commutative_algebra_openmath_xml(xml)
    validate_canonical_typed_commutative_algebra_openmath_xml(canonical)
    if not 4 <= len(steps) <= 10:
        raise ValueError("Each card needs four to ten meaningful proof steps")
    cards.append(
        {
            "id": "commalg_reuse_20260930_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canonical,
            "lean_target": "example {R : Type*} [CommRing R] " + target,
            "lean_witness": "by\n" + proof,
        }
    )


card(
    "radical_product",
    "I J",
    eq(rad(mul(I, J)), meet(rad(I), rad(J))),
    "任意の可換環 R のイデアル I,J について、√(IJ)=√I∩√J。",
    "積の包含と、二つの冪を掛けて指数を加える議論で両包含を示す。",
    [
        "IJ⊆I∩J より √(IJ)⊆√I∩√J を得る。",
        "x∈√I∩√J とし x^m∈I、x^n∈J を選ぶ。",
        "x^(m+n)=x^m x^n は IJ に属する。",
        "したがって x∈√(IJ) であり、両包含から等号を得る。",
    ],
    "(I J : Ideal R) : (I * J).radical = I.radical ⊓ J.radical",
    "  exact Ideal.radical_mul I J",
)

card(
    "radical_sum",
    "I J",
    eq(rad(add(I, J)), rad(add(rad(I), rad(J)))),
    "任意の可換環 R のイデアル I,J について、√(I+J)=√(√I+√J)。",
    "根基の単調性と冪等性で、和の両側の根基を比較する。",
    [
        "I⊆√I、J⊆√J より一方の包含を得る。",
        "I,J⊆I+J より √I,√J⊆√(I+J)。",
        "従って √I+√J⊆√(I+J)。",
        "根基を取り冪等性を使うと逆包含となる。",
    ],
    "(I J : Ideal R) : (I + J).radical = (I.radical + J.radical).radical",
    "  exact Ideal.radical_sup I J",
)

card(
    "radical_closure_containment",
    "I J",
    iff(le(rad(I), rad(J)), le(I, rad(J))),
    "任意の可換環 R のイデアル I,J について、√I⊆√J と I⊆√J は同値である。",
    "根基への包含は、対象が既に根基なら始域の根基を取っても変わらない。",
    [
        "√I⊆√J なら I⊆√I を合成する。",
        "逆に I⊆√J を仮定する。",
        "根基の単調性から √I⊆√(√J) を得る。",
        "√(√J)=√J を使う。",
    ],
    "(I J : Ideal R) : I.radical ≤ J.radical ↔ I ≤ J.radical",
    "  exact Ideal.radical_le_radical_iff",
)

card(
    "radical_top_criterion",
    "I",
    iff(eq(rad(I), top), eq(I, top)),
    "任意の可換環 R のイデアル I について、√I=R と I=R は同値である。",
    "根基が単位元を含むことと、元のイデアルが単位元を含むことを比較する。",
    [
        "√I=R なら 1∈√I。",
        "ある自然数 n について 1^n∈I が従う。",
        "1^n=1 より I=R を得る。",
        "逆に I=R ならその根基も R である。",
    ],
    "(I : Ideal R) : I.radical = ⊤ ↔ I = ⊤",
    "  exact Ideal.radical_eq_top",
)

card(
    "comaximal_product_intersection",
    "I J",
    logic("implies", eq(add(I, J), top), eq(mul(I, J), meet(I, J))),
    "可換環 R のイデアル I,J が I+J=R を満たすなら、IJ=I∩J。",
    "1 を I の元と J の元の和として書き、交わりの各元に掛ける。",
    [
        "一般に IJ⊆I∩J が成り立つ。",
        "I+J=R から a∈I、b∈J、a+b=1 を選ぶ。",
        "x∈I∩J に対し x=xa+xb と書く。",
        "xa と xb はどちらも IJ に属するので逆包含を得る。",
    ],
    "(I J : Ideal R) (h : I + J = ⊤) : I * J = I ⊓ J",
    "  exact Ideal.mul_eq_inf_of_coprime h",
)

card(
    "comaximal_sum_product_reduction",
    "I J K",
    logic("implies", eq(add(I, J), top), eq(add(I, mul(J, K)), add(I, K))),
    "可換環 R のイデアル I,J,K について、I+J=R なら I+JK=I+K。",
    "互いに素な関係から単位元の分解を取り、K の元を I と JK に分ける。",
    [
        "JK⊆K より I+JK⊆I+K。",
        "a∈I、b∈J、a+b=1 を取る。",
        "k∈K を k=ak+bk と分解する。",
        "ak∈I、bk∈JK より K⊆I+JK、従って逆包含を得る。",
    ],
    "(I J K : Ideal R) (h : I + J = ⊤) : I + J * K = I + K",
    "  exact Ideal.sup_mul_eq_of_coprime_left h",
)

card(
    "prime_product_containment",
    "I J P",
    logic("implies", prime(P), iff(le(mul(I, J), P), logic("or", le(I, P), le(J, P)))),
    "可換環 R のイデアル I,J と素イデアル P について、IJ⊆P と『I⊆P または J⊆P』は同値である。",
    "素イデアルの元に関する積の判定を、二つのイデアル全体に適用する。",
    [
        "I⊆P または J⊆P なら、積の吸収性から IJ⊆P。",
        "逆に IJ⊆P と I⊈P を仮定し、a∈I かつ a∉P を満たす a を選ぶ。",
        "任意の b∈J に対して ab∈P。",
        "P の素性と a∉P から b∈P、従って J⊆P。",
    ],
    "(I J P : Ideal R) (hP : P.IsPrime) : I * J ≤ P ↔ I ≤ P ∨ J ≤ P",
    "  exact hP.mul_le",
)

card(
    "prime_intersection_containment",
    "I J P",
    logic("implies", prime(P), iff(le(meet(I, J), P), logic("or", le(I, P), le(J, P)))),
    "可換環 R のイデアル I,J と素イデアル P について、I∩J⊆P と『I⊆P または J⊆P』は同値である。",
    "積は交わりに含まれるので、素イデアルへの積の包含判定に帰着する。",
    [
        "I∩J⊆P を仮定する。",
        "IJ⊆I∩J より IJ⊆P。",
        "P の素性から I⊆P または J⊆P。",
        "逆方向は I∩J⊆I,J を合成すればよい。",
    ],
    "(I J P : Ideal R) (hP : P.IsPrime) : I ⊓ J ≤ P ↔ I ≤ P ∨ J ≤ P",
    "  exact hP.inf_le",
)

card(
    "distinct_maximal_comaximal",
    "I J",
    logic(
        "implies", logic("and", maximal(I), maximal(J), ne(I, J)), eq(add(I, J), top)
    ),
    "可換環 R の異なる極大イデアル I,J は I+J=R を満たす。",
    "和が真なら極大性から元の極大イデアルと等しくなり、異なるという仮定に反する。",
    [
        "I,J が極大で I≠J とする。",
        "I+J が真なら I⊆I+J と極大性より I+J=I。",
        "従って J⊆I となり、J の極大性と I の真性から J=I。",
        "これは仮定に反するので I+J=R。",
    ],
    "(I J : Ideal R) (hI : I.IsMaximal) (hJ : J.IsMaximal) (hne : I ≠ J) : I + J = ⊤",
    "  exact hI.coprime_of_ne hJ hne",
)

card(
    "maximal_above_proper",
    "I",
    logic(
        "implies", ne(I, top), bind("exists", ["P"], logic("and", maximal(P), le(I, P)))
    ),
    "任意の可換環 R の真イデアル I は、ある極大イデアル P に含まれる。",
    "I を含む真イデアルの集合に Zorn の補題を適用する。",
    [
        "I を含む真イデアルの集合は I 自身を含む。",
        "その鎖の合併はイデアルであり I を含む。",
        "合併が 1 を含めば鎖のある真イデアルが 1 を含むため矛盾する。",
        "Zorn の補題で極大元を取り、環の極大イデアルであることを得る。",
    ],
    "(I : Ideal R) (hI : I ≠ ⊤) : ∃ P : Ideal R, P.IsMaximal ∧ I ≤ P",
    "  exact Ideal.exists_le_maximal I hI",
)

card(
    "radical_via_all_containing_primes",
    "I J",
    iff(
        le(J, rad(I)),
        bind(
            "forall",
            ["P"],
            logic("implies", logic("and", le(I, P), prime(P)), le(J, P)),
        ),
    ),
    "可換環 R のイデアル I,J について、J⊆√I は『I を含む全ての素イデアル P に対し J⊆P』と同値である。",
    "根基が、そのイデアルを含む全ての素イデアルの交わりであることを使う。",
    [
        "√I を、I を含む素イデアル全体の交わりとして表す。",
        "J⊆√I なら交わりの各成分 P に J が含まれる。",
        "逆に全てのそのような P に J が含まれると仮定する。",
        "交わりの最大下界性から J⊆√I を得る。",
    ],
    "(I J : Ideal R) : J ≤ I.radical ↔ ∀ P : Ideal R, I ≤ P ∧ P.IsPrime → J ≤ P",
    "  rw [Ideal.radical_eq_sInf I]\n  exact le_sInf_iff",
)

card(
    "comaximal_radicals_criterion",
    "I J",
    iff(eq(add(rad(I), rad(J)), top), eq(add(I, J), top)),
    "可換環 R のイデアル I,J について、√I+√J=R と I+J=R は同値である。",
    "根基を取った和の公式と、根基が全環であるための判定を組み合わせる。",
    [
        "√(I+J)=√(√I+√J) を用いる。",
        "√I+√J=R なら右辺が R となる。",
        "√(I+J)=R から I+J=R が従う。",
        "逆方向は I+J⊆√I+√J と全環の最大性による。",
    ],
    "(I J : Ideal R) : I.radical + J.radical = ⊤ ↔ I + J = ⊤",
    "  change I.radical ⊔ J.radical = ⊤ ↔ I ⊔ J = ⊤\n  rw [← Ideal.radical_eq_top (I := I ⊔ J), Ideal.radical_sup I J, Ideal.radical_eq_top]",
)

card(
    "ideal_modular_law",
    "I J K",
    logic("implies", le(I, K), eq(meet(add(I, J), K), add(I, meet(J, K)))),
    "可換環 R のイデアル I,J,K について、I⊆K なら (I+J)∩K=I+(J∩K)。",
    "和の元を分解し、I⊆K により残りの J 成分も K に属すると示す。",
    [
        "x∈(I+J)∩K を x=i+j、i∈I、j∈J と書く。",
        "I⊆K と x∈K より j=x−i∈K。",
        "従って x∈I+(J∩K)。",
        "逆方向は I,J∩K⊆I+J と I,J∩K⊆K による。",
    ],
    "(I J K : Ideal R) (h : I ≤ K) : (I + J) ⊓ K = I + (J ⊓ K)",
    "  exact sup_inf_assoc_of_le J h",
)

card(
    "ideal_product_distributes_sum",
    "I J K",
    eq(mul(I, add(J, K)), add(mul(I, J), mul(I, K))),
    "任意の可換環 R のイデアル I,J,K について、I(J+K)=IJ+IK。",
    "積イデアルの生成元と環の分配法則で両包含を示す。",
    [
        "J,K⊆J+K より IJ+IK⊆I(J+K)。",
        "逆方向では積の生成元 a(b+c) を考える。",
        "分配法則 a(b+c)=ab+ac より生成元は IJ+IK に属する。",
        "IJ+IK の加法閉性を使い、積イデアル全体の包含を得る。",
    ],
    "(I J K : Ideal R) : I * (J + K) = I * J + I * K",
    "  exact mul_add I J K",
)

card(
    "comaximal_no_common_prime",
    "I J",
    iff(
        eq(add(I, J), top),
        bind(
            "forall",
            ["P"],
            logic("implies", logic("and", le(I, P), le(J, P)), logic("not", prime(P))),
        ),
    ),
    "可換環 R のイデアル I,J について、I+J=R は『I と J をともに含む素イデアルが存在しない』ことと同値である。",
    "和が真なら、それを含む極大イデアルを取ることで共通の素イデアルを作る。",
    [
        "I+J=R とし、I,J を含む素イデアル P を仮定する。",
        "R=I+J⊆P は P の真性に反する。",
        "逆に I+J が真なら、それを含む極大イデアルを取る。",
        "極大イデアルは素で I,J をともに含むため、仮定に反する。",
    ],
    "(I J : Ideal R) : I + J = ⊤ ↔ ∀ P : Ideal R, I ≤ P ∧ J ≤ P → ¬ P.IsPrime",
    "  constructor\n  · intro h P hle hp\n    apply hp.ne_top\n    exact top_unique (h ▸ sup_le hle.1 hle.2)\n  · intro h\n    exact (Ideal.coprime_of_no_prime_ge (fun P hi hj => h P ⟨hi, hj⟩)).sup_eq",
)

card(
    "ideal_product_top_criterion",
    "I J",
    iff(eq(mul(I, J), top), logic("and", eq(I, top), eq(J, top))),
    "可換環 R のイデアル I,J について、IJ=R と『I=R かつ J=R』は同値である。",
    "積が各因子に含まれることと、全イデアルが積の単位元であることを使う。",
    [
        "IJ=R を仮定する。",
        "IJ⊆I と IJ⊆J より R⊆I,J。",
        "全環の最大性から I=J=R。",
        "逆に両方が R なら積も R である。",
    ],
    "(I J : Ideal R) : I * J = ⊤ ↔ I = ⊤ ∧ J = ⊤",
    "  constructor\n  · intro h\n    exact ⟨top_unique (h ▸ Ideal.mul_le_right), top_unique (h ▸ Ideal.mul_le_left)⟩\n  · rintro ⟨rfl, rfl⟩\n    simp",
)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ids = [c["id"] for c in cards]
    xmls = [c["openmath_xml"] for c in cards]
    if len(set(ids)) != len(ids) or len(set(xmls)) != len(xmls):
        raise ValueError("Duplicate expansion card")
    for path in (ROOT / "docs").glob("typed-commutative-algebra*manifest*.json"):
        old = json.loads(path.read_text())
        for row in old["cards"]:
            if row["id"] in ids or row.get("canonical_openmath_xml") in xmls:
                raise ValueError(f"Existing card duplicated: {row['id']}")
    witness = ROOT / "docs/commalg-reuse-batch-20260930.lean"
    witness.write_text(
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + str(c["id"])
            + "\n"
            + str(c["lean_target"])
            + " := "
            + str(c["lean_witness"]).rstrip()
            for c in cards
        )
        + "\n"
    )
    workspace = ROOT / "pals-agent/lean-workspace"
    subprocess.run(
        [str(Path.home() / ".elan/bin/lake"), "env", "lean", str(witness)],
        cwd=workspace,
        check=True,
        timeout=180,
    )
    packages = json.loads((workspace / "lake-manifest.json").read_text())["packages"]
    revision = next(p["rev"] for p in packages if p["name"] == "mathlib")
    evidence = {
        "witness_path": str(witness.relative_to(ROOT)),
        "witness_sha256": digest(witness),
        "toolchain": (workspace / "lean-toolchain").read_text().strip(),
        "mathlib_revision": revision,
        "validator_sha256": digest(
            ROOT / "pals-agent/pals_agent/typed_commutative_algebra.py"
        ),
        "registry_sha256": digest(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-commutative-algebra-v1-registry.json"
        ),
    }
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": cards,
        "evidence": evidence,
    }
    (ROOT / "docs/commalg-reuse-batch-20260930.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Verified {len(cards)} new cards; wrote unpublished expansion JSON")


if __name__ == "__main__":
    main()
