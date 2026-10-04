"""Compile and generate general finite-dimensional linear algebra authoring cards."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_linear_algebra_v2 import (
    canonicalize_typed_linear_algebra_v2_openmath_xml as canonicalize,
)
from pals_agent.typed_linear_algebra_v2 import (
    validate_canonical_typed_linear_algebra_v2_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
TYPED = "urn:pals:openmath:typed-linear-algebra:v2"
STANDARD = "http://www.openmath.org/cd"
PROFILE = "typed-linear-algebra-v2"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(n):
    return f"<OMV name={quoteattr(n)}/>"


def app(h, *a):
    return "<OMA>" + h + "".join(a) + "</OMA>"


def op(n, *a):
    return app(sym("la2", n), *a)


def std(cd, n, *a):
    return app(sym(cd, n, STANDARD), *a)


def eq(a, b):
    return std("relation1", "eq", a, b)


def ne(a, b):
    return std("relation1", "neq", a, b)


def le(a, b):
    return std("relation1", "leq", a, b)


def lt(a, b):
    return std("relation1", "lt", a, b)


def addn(a, b):
    return std("arith1", "plus", a, b)


def conj(a, b):
    return std("logic1", "and", a, b)


def imp(a, b):
    return std("logic1", "implies", a, b)


def iff(a, b):
    return conj(imp(a, b), imp(b, a))


K = var("K")
V = var("V")
W = var("W")
f = var("f")
g = var("g")
S = var("S")
T = var("T")
n = var("n")
v = var("v")
a = var("a")
b = var("b")
Z = "<OMI>0</OMI>"


def dim(x):
    return op("dim", K, x)


def sd(x, s):
    return op("sub_dim", K, x, s)


def bot(x):
    return op("sub_bot", K, x)


def top(x):
    return op("sub_top", K, x)


def ker(x, y, f):
    return op("kernel", K, x, y, f)


def ran(x, y, f):
    return op("range", K, x, y, f)


def inj(x, y, f):
    return op("injective", K, x, y, f)


def surj(x, y, f):
    return op("surjective", K, x, y, f)


def sup(s, t):
    return op("sub_sup", K, V, s, t)


def inf(s, t):
    return op("sub_inf", K, V, s, t)


def suble(s, t):
    return op("sub_le", K, V, s, t)


def span(v):
    return op("family_span", K, V, n, v)


def li(v):
    return op("independent", K, V, n, v)


def es(a):
    return op("eigenspace", K, V, f, a)


def build_cards():
    cards = []

    def card(key, spaces, extra, statement, strategy, steps, body, target, proof):
        decls = [("K", sym("la2", "Field"))] + [
            (x, op("FiniteDimensionalSpace", K)) for x in spaces
        ]
        decls += [(name, ty) for name, ty, _ in extra]
        bound = "".join(
            "<OMATTR><OMATP>"
            + sym("typed1", "type")
            + ty
            + "</OMATP>"
            + var(name)
            + "</OMATTR>"
            for name, ty in decls
        )
        raw = (
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"><OMBIND>'
            + sym("typed1", "forall")
            + "<OMBVAR>"
            + bound
            + "</OMBVAR>"
            + body
            + "</OMBIND></OMOBJ>"
        )
        xml = canonicalize(raw)
        validate(xml)
        prefix = "{K " + " ".join(spaces) + " : Type*} [Field K] "
        prefix += " ".join(
            f"[AddCommGroup {x}] [Module K {x}] [FiniteDimensional K {x}]"
            for x in spaces
        )
        params = " ".join(f"({name} : {lean})" for name, _, lean in extra)
        cards.append(
            {
                "id": "la_v2_" + key,
                "canonical_statement": "体 K 上の有限次元ベクトル空間について、"
                + statement,
                "proof_strategy": strategy,
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": f"example {prefix} {params} : {target}",
                "lean_witness": proof,
            }
        )

    def lm(name, x, y):
        return (name, op("LinearMap", K, var(x), var(y)), f"{x} →ₗ[K] {y}")

    def sub(name):
        return (name, op("Subspace", K, V), "Submodule K V")

    scalar = lambda name: (name, op("Scalar", K), "K")
    natural = ("n", sym("la2", "Nat"), "ℕ")
    family = ("v", op("VectorFamily", K, V, n), "Fin n → V")
    basis = ("b", op("Basis", K, V, n), "Module.Basis (Fin n) K V")
    sf = ("a", op("ScalarFamily", K, n), "Fin n → K")
    maps = [lm("f", "V", "W")]
    subs = [sub("S"), sub("T")]
    r = ran(V, W, f)
    k = ker(V, W, f)
    dR = sd(W, r)
    dK = sd(V, k)
    card(
        "rank_nullity",
        ["V", "W"],
        maps,
        "任意の線形写像 f:V→W に対して dim(im f)+dim(ker f)=dim V。",
        "核の基底を V の基底へ延長し、追加ベクトルの像が像の基底になることを用いる。",
        [
            "ker f の基底を選ぶ。",
            "その基底を V の基底に延長する。",
            "延長で追加したベクトルの像が im f の基底になることを示す。",
            "二つの基底の本数を加えて dim V を得る。",
        ],
        eq(addn(dR, dK), dim(V)),
        "Module.finrank K (LinearMap.range f) + Module.finrank K (LinearMap.ker f) = Module.finrank K V",
        "by\n  exact f.finrank_range_add_finrank_ker",
    )
    card(
        "rank_domain_bound",
        ["V", "W"],
        maps,
        "線形写像 f:V→W の階数は dim V 以下である。",
        "階数と退化次数の和から退化次数の非負性を使う。",
        [
            "階数・退化次数定理を適用する。",
            "dim(ker f) は自然数なので非負である。",
            "dim(im f)≤dim(im f)+dim(ker f) を得る。",
            "右辺を dim V に置き換える。",
        ],
        le(dR, dim(V)),
        "Module.finrank K (LinearMap.range f) ≤ Module.finrank K V",
        "by\n  exact f.finrank_range_le",
    )
    card(
        "rank_codomain_bound",
        ["V", "W"],
        maps,
        "線形写像 f:V→W の階数は dim W 以下である。",
        "像を W の部分空間とみなし、その基底を W の基底へ延長する。",
        [
            "im f は W の部分空間である。",
            "im f の基底を選ぶ。",
            "その基底を W の基底へ延長する。",
            "元の基底の本数は延長後の本数以下なので次元不等式を得る。",
        ],
        le(dR, dim(W)),
        "Module.finrank K (LinearMap.range f) ≤ Module.finrank K W",
        "by\n  exact (LinearMap.range f).finrank_le",
    )
    card(
        "nullity_injectivity",
        ["V", "W"],
        maps,
        "dim(ker f)=0 と線形写像 f:V→W の単射性は同値である。",
        "有限次元部分空間の次元零判定と、核による単射判定をつなぐ。",
        [
            "dim(ker f)=0 から ker f=0 を得る。",
            "f(x)=f(y) を差が核に属するという条件へ変える。",
            "核が零なので x=y となる。",
            "逆に単射なら核が零であり、その次元も零となる。",
        ],
        iff(eq(dK, Z), inj(V, W, f)),
        "(Module.finrank K (LinearMap.ker f) = 0 → Function.Injective f) ∧ (Function.Injective f → Module.finrank K (LinearMap.ker f) = 0)",
        "by\n  have h : Module.finrank K (LinearMap.ker f) = 0 ↔ Function.Injective f := by\n    rw [Submodule.finrank_eq_zero, LinearMap.ker_eq_bot]\n  exact ⟨h.mp, h.mpr⟩",
    )
    card(
        "full_rank_surjectivity",
        ["V", "W"],
        maps,
        "dim(im f)=dim W と線形写像 f:V→W の全射性は同値である。",
        "全体と同じ次元を持つ部分空間は全体に一致することを使う。",
        [
            "im f⊆W と次元の一致を取る。",
            "有限次元性により im f=W を得る。",
            "像が全体なので f は全射となる。",
            "逆に全射なら像が全体であり次元も一致する。",
        ],
        iff(eq(dR, dim(W)), surj(V, W, f)),
        "(Module.finrank K (LinearMap.range f) = Module.finrank K W → Function.Surjective f) ∧ (Function.Surjective f → Module.finrank K (LinearMap.range f) = Module.finrank K W)",
        "by\n  constructor\n  · intro h\n    exact LinearMap.range_eq_top.mp (Submodule.eq_top_of_finrank_eq h)\n  · intro h\n    rw [LinearMap.range_eq_top.mpr h]\n    exact finrank_top K W",
    )
    card(
        "injective_dimension_bound",
        ["V", "W"],
        maps,
        "単射線形写像 f:V→W が存在すると dim V≤dim W。",
        "単射は一次独立性を保存するので V の基底の像を W の独立族として数える。",
        [
            "V の基底を選ぶ。",
            "f の単射性で基底の像が一次独立であることを示す。",
            "W の一次独立族の本数は dim W 以下である。",
            "基底の本数が dim V であることを代入する。",
        ],
        imp(inj(V, W, f), le(dim(V), dim(W))),
        "Function.Injective f → Module.finrank K V ≤ Module.finrank K W",
        "by\n  exact LinearMap.finrank_le_finrank_of_injective",
    )
    card(
        "surjective_dimension_bound",
        ["V", "W"],
        maps,
        "全射線形写像 f:V→W が存在すると dim W≤dim V。",
        "V の基底の像が W を生成することから次元を比較する。",
        [
            "V の基底を選ぶ。",
            "W の任意の元に f の原像を取る。",
            "原像を基底で展開して、基底の像が W を生成することを示す。",
            "生成族の本数 dim V が dim W 以上であることを得る。",
        ],
        imp(surj(V, W, f), le(dim(W), dim(V))),
        "Function.Surjective f → Module.finrank K W ≤ Module.finrank K V",
        "by\n  exact LinearMap.finrank_le_finrank_of_surjective",
    )
    card(
        "equal_dimension_injective_surjective",
        ["V", "W"],
        maps,
        "dim V=dim W なら、線形写像 f:V→W は単射であることと全射であることが同値である。",
        "階数・退化次数定理と像の次元判定を使い両方向を示す。",
        [
            "二つの空間の次元が等しいと仮定する。",
            "単射なら退化次数が零なので階数が dim W となり全射である。",
            "逆に全射なら階数は dim W=dim V である。",
            "階数・退化次数定理から核の次元が零となり単射である。",
        ],
        imp(eq(dim(V), dim(W)), iff(inj(V, W, f), surj(V, W, f))),
        "Module.finrank K V = Module.finrank K W → (Function.Injective f → Function.Surjective f) ∧ (Function.Surjective f → Function.Injective f)",
        "by\n  intro h\n  exact ⟨(LinearMap.injective_iff_surjective_of_finrank_eq_finrank h).mp, (LinearMap.injective_iff_surjective_of_finrank_eq_finrank h).mpr⟩",
    )
    card(
        "subspace_dimension_bound",
        ["V"],
        [sub("S")],
        "任意の部分空間 S⊆V は dim S≤dim V を満たす。",
        "部分空間の基底延長で次元を比較する。",
        [
            "S の基底を選ぶ。",
            "S の基底を V の一次独立族とみなす。",
            "V の基底まで延長する。",
            "延長で本数は減らないので dim S≤dim V を得る。",
        ],
        le(sd(V, S), dim(V)),
        "Module.finrank K S ≤ Module.finrank K V",
        "by\n  exact S.finrank_le",
    )
    card(
        "zero_dimensional_subspace",
        ["V"],
        [sub("S")],
        "部分空間 S の次元が零であることと S=0 は同値である。",
        "非零ベクトルがあれば少なくとも一次元を生成することを使う。",
        [
            "dim S=0 を仮定する。",
            "非零ベクトルが S にあれば一本の一次独立族を作れて矛盾する。",
            "よって S は零部分空間である。",
            "逆に零部分空間には空基底があり次元は零である。",
        ],
        iff(eq(sd(V, S), Z), eq(S, bot(V))),
        "(Module.finrank K S = 0 → S = ⊥) ∧ (S = ⊥ → Module.finrank K S = 0)",
        "by\n  exact ⟨Submodule.finrank_eq_zero.mp, Submodule.finrank_eq_zero.mpr⟩",
    )
    card(
        "full_dimensional_subspace",
        ["V"],
        [sub("S")],
        "dim S=dim V なら部分空間 S は V 全体に一致する。",
        "真部分空間なら基底へ新しいベクトルを追加できて次元が小さくなることを使う。",
        [
            "dim S=dim V を仮定する。",
            "S が真部分空間と仮定して S 外のベクトルを取る。",
            "S の基底にそのベクトルを追加すると一次独立族ができる。",
            "dim V を超える本数となる矛盾から S=V を結論する。",
        ],
        imp(eq(sd(V, S), dim(V)), eq(S, top(V))),
        "Module.finrank K S = Module.finrank K V → S = ⊤",
        "by\n  exact Submodule.eq_top_of_finrank_eq",
    )
    card(
        "grassmann_dimension_formula",
        ["V"],
        subs,
        "dim(S+T)+dim(S∩T)=dim S+dim T。",
        "共通部分の基底をそれぞれの部分空間の基底へ延長し、共通部分の重複を一度引く。",
        [
            "S∩T の基底を選ぶ。",
            "それを S の基底と T の基底へそれぞれ延長する。",
            "共通部分を一度だけ含む合併が S+T の基底になることを示す。",
            "基底の本数を数えて次元等式を得る。",
        ],
        eq(addn(sd(V, sup(S, T)), sd(V, inf(S, T))), addn(sd(V, S), sd(V, T))),
        "Module.finrank K (S ⊔ T : Submodule K V) + Module.finrank K (S ⊓ T : Submodule K V) = Module.finrank K S + Module.finrank K T",
        "by\n  exact Submodule.finrank_sup_add_finrank_inf_eq S T",
    )
    card(
        "contained_equal_dimension",
        ["V"],
        subs,
        "S⊆T かつ dim S=dim T なら S=T。",
        "包含関係のある二つの部分空間の基底を比較する。",
        [
            "S⊆T と次元の一致を仮定する。",
            "S の基底は T でも一次独立である。",
            "本数が dim T なので T の基底となる。",
            "S の基底が T を生成することから逆包含を得る。",
        ],
        imp(conj(suble(S, T), eq(sd(V, S), sd(V, T))), eq(S, T)),
        "S ≤ T ∧ Module.finrank K S = Module.finrank K T → S = T",
        "by\n  rintro ⟨hST, hd⟩\n  exact Submodule.eq_of_le_of_finrank_eq hST hd",
    )
    card(
        "strict_subspace_dimension",
        ["V"],
        subs,
        "S が T の真部分空間なら dim S<dim T。",
        "包含による次元の弱い不等式と、等号なら部分空間が一致する事実を合わせる。",
        [
            "S⊊T を仮定する。",
            "包含から dim S≤dim T を得る。",
            "もし次元が等しければ包含と次元判定から S=T となる。",
            "真包含に反するので次元は厳密に小さい。",
        ],
        imp(op("sub_lt", K, V, S, T), lt(sd(V, S), sd(V, T))),
        "S < T → Module.finrank K S < Module.finrank K T",
        "by\n  exact Submodule.finrank_lt_finrank_of_lt",
    )
    card(
        "complementary_subspace_dimension",
        ["V"],
        subs,
        "S+T=V かつ S∩T=0 なら dim S+dim T=dim V。",
        "Grassmann の次元公式に和と共通部分の条件を代入する。",
        [
            "S+T=V と S∩T=0 を取る。",
            "Grassmann の次元公式を S,T に適用する。",
            "和の次元を dim V、共通部分の次元を零に置き換える。",
            "零を除いて次元の加法性を得る。",
        ],
        imp(
            conj(eq(sup(S, T), top(V)), eq(inf(S, T), bot(V))),
            eq(addn(sd(V, S), sd(V, T)), dim(V)),
        ),
        "(S ⊔ T = ⊤) ∧ (S ⊓ T = ⊥) → Module.finrank K S + Module.finrank K T = Module.finrank K V",
        "by\n  rintro ⟨hs, hi⟩\n  have h := Submodule.finrank_sup_add_finrank_inf_eq S T\n  rw [hs, hi, finrank_top, finrank_bot, add_zero] at h\n  exact h.symm",
    )
    card(
        "basis_cardinality",
        ["V"],
        [natural, basis],
        "n 本のベクトルで添字付けられた基底 b:Basis(Fin n,K,V) があれば dim V=n。",
        "有限基底の本数による次元の定義を適用する。",
        [
            "b が V の基底であることを取る。",
            "b の添字集合 Fin n の要素数は n である。",
            "有限基底の本数が空間の次元に等しいことを用いる。",
            "Fin n の要素数を n に簡約する。",
        ],
        eq(dim(V), n),
        "Module.finrank K V = n",
        "by\n  simpa using Module.finrank_eq_card_basis b",
    )
    card(
        "independent_family_cardinality",
        ["V"],
        [natural, family],
        "n 本の一次独立なベクトル族 v:Fin n→V は n≤dim V を満たす。",
        "独立族を基底へ延長して本数を比較する。",
        [
            "v が一次独立であると仮定する。",
            "v を V の基底へ延長する。",
            "元の n 本は延長後の基底に含まれる。",
            "基底の本数 dim V と比較して不等式を得る。",
        ],
        imp(li(v), le(n, dim(V))),
        "LinearIndependent K v → n ≤ Module.finrank K V",
        "by\n  intro h\n  simpa using h.fintype_card_le_finrank",
    )
    card(
        "spanning_family_cardinality",
        ["V"],
        [natural, family],
        "n 本のベクトル族 v が V を生成するなら dim V≤n。",
        "有限生成族から基底を選び、その本数を比較する。",
        [
            "v の生成空間が V 全体であると仮定する。",
            "有限族 v の生成空間の次元は族の本数以下である。",
            "生成空間を V 全体に置き換える。",
            "全体部分空間の次元を dim V に簡約する。",
        ],
        imp(eq(span(v), top(V)), le(dim(V), n)),
        "Submodule.span K (Set.range v) = ⊤ → Module.finrank K V ≤ n",
        "by\n  intro h\n  have bound := finrank_range_le_card v (R := K)\n  change Module.finrank K (Submodule.span K (Set.range v)) ≤ Fintype.card (Fin n) at bound\n  rw [h, finrank_top] at bound\n  simpa using bound",
    )
    card(
        "full_size_independent_spans",
        ["V"],
        [natural, family],
        "n=dim V で v:Fin n→V が一次独立なら、v は V を生成する。",
        "独立族の生成空間はその本数の次元を持つため全体と次元が一致する。",
        [
            "v の一次独立性と n=dim V を取る。",
            "span(v) の次元は独立族の本数 n である。",
            "したがって span(v) は V と同じ次元を持つ。",
            "全次元の部分空間の判定により span(v)=V を得る。",
        ],
        imp(conj(li(v), eq(n, dim(V))), eq(span(v), top(V))),
        "LinearIndependent K v ∧ n = Module.finrank K V → Submodule.span K (Set.range v) = ⊤",
        "by\n  rintro ⟨h, hn⟩\n  exact h.span_eq_top_of_card_eq_finrank' (by simpa using hn)",
    )
    card(
        "full_size_spanning_independent",
        ["V"],
        [natural, family],
        "n=dim V で v:Fin n→V が V を生成するなら、v は一次独立である。",
        "基底と同じ本数の生成族に従属関係があると、一本を除いても生成でき次元と矛盾する。",
        [
            "span(v)=V と n=dim V を仮定する。",
            "従属なら一つのベクトルを残りの線形結合で表せる。",
            "その一本を除いても V を生成できる。",
            "dim V 未満の生成族は存在しないので独立性を得る。",
        ],
        imp(conj(eq(span(v), top(V)), eq(n, dim(V))), li(v)),
        "Submodule.span K (Set.range v) = ⊤ ∧ n = Module.finrank K V → LinearIndependent K v",
        "by\n  rintro ⟨h, hn⟩\n  exact linearIndependent_of_top_le_span_of_card_eq_finrank h.ge (by simpa using hn)",
    )
    endo = [lm("f", "V", "V")]
    scaled = op("linear_smul", K, V, V, a, op("linear_id", K, V))
    difference = op("linear_sub", K, V, V, f, scaled)
    card(
        "eigenspace_as_kernel",
        ["V"],
        endo + [scalar("a")],
        "線形自己写像 f とスカラー a の固有空間は ker(f−a id_V) に一致する。",
        "固有方程式 f(x)=a x を移項して核への所属に直す。",
        [
            "任意の x について固有空間への所属を展開する。",
            "f(x)=a x を f(x)−a x=0 と読み替える。",
            "左辺は線形写像 f−a id の x での値である。",
            "各元で所属条件が同じなので部分空間が一致する。",
        ],
        eq(es(a), ker(V, V, difference)),
        "Module.End.eigenspace f a = LinearMap.ker (f - a • LinearMap.id)",
        "by\n  ext x\n  simp [LinearMap.mem_ker, sub_eq_zero]",
    )
    card(
        "distinct_eigenspaces_intersection",
        ["V"],
        endo + [scalar("a"), scalar("b")],
        "a≠b なら f の a 固有空間と b 固有空間の共通部分は零である。",
        "二つの固有方程式を引き、非零スカラー a−b を消去する。",
        [
            "両方の固有空間に入るベクトル x を取る。",
            "f(x)=a x と f(x)=b x を引いて (a−b)x=0 を得る。",
            "a≠b なので a−b は非零であり x=0 となる。",
            "零ベクトルは両方に入るため共通部分は零に一致する。",
        ],
        imp(ne(a, b), eq(inf(es(a), es(b)), bot(V))),
        "a ≠ b → Module.End.eigenspace f a ⊓ Module.End.eigenspace f b = ⊥",
        "by\n  intro hab\n  apply bot_unique\n  intro x hx\n  have ha := Module.End.mem_eigenspace_iff.mp hx.1\n  have hb := Module.End.mem_eigenspace_iff.mp hx.2\n  change x = 0\n  have hh : (a - b) • x = 0 := by rw [sub_smul, ← ha, ← hb, sub_self]\n  exact (smul_eq_zero.mp hh).resolve_left (sub_ne_zero.mpr hab)",
    )
    ef = op("eigenfamily", K, V, n, f, a, v)
    ai = op("scalar_family_injective", K, n, a)
    card(
        "distinct_eigenvectors_independent",
        ["V"],
        [natural, *endo, sf, family],
        "相異なる固有値族 a:Fin n→K に対応する非零固有ベクトル族 v は一次独立である。",
        "相異なる固有空間が独立であることを、各空間から選んだ非零ベクトルへ適用する。",
        [
            "固有値族 a が単射であることを取る。",
            "各 v(i) は対応する固有空間に属し、零でないことを確認する。",
            "異なる固有空間の族の独立性を a に沿って制限する。",
            "各空間から選んだ非零ベクトル族 v の一次独立性を得る。",
        ],
        imp(conj(ai, ef), li(v)),
        "Function.Injective a ∧ (∀ i, Module.End.HasEigenvector f (a i) (v i)) → LinearIndependent K v",
        "by\n  rintro ⟨ha, hv⟩\n  exact Module.End.eigenvectors_linearIndependent' f a ha v hv",
    )
    card(
        "distinct_full_spectrum_eigenbasis",
        ["V"],
        [natural, *endo, sf, family],
        "n=dim V 個の相異なる固有値に対応する非零固有ベクトルがあれば、その固有値順の固有ベクトル基底が存在する。",
        "相異なる固有値の固有ベクトルの独立性と、次元に一致する独立族からの基底構成を合わせる。",
        [
            "相異なる固有値に対応する v が一次独立であることを示す。",
            "本数 n=dim V なので v は V 全体を生成する。",
            "独立性と生成性から Fin n 添字の基底を構成する。",
            "構成した基底の各ベクトルは元の v(i) なので固有方程式と非零性を引き継ぐ。",
        ],
        imp(conj(conj(ai, ef), eq(n, dim(V))), op("has_eigenbasis", K, V, n, f, a)),
        "(Function.Injective a ∧ (∀ i, Module.End.HasEigenvector f (a i) (v i))) ∧ n = Module.finrank K V → ∃ b : Module.Basis (Fin n) K V, ∀ i, Module.End.HasEigenvector f (a i) (b i)",
        "by\n  rintro ⟨⟨ha, hv⟩, hn⟩\n  have hi := Module.End.eigenvectors_linearIndependent' f a ha v hv\n  have hs := hi.span_eq_top_of_card_eq_finrank' (by simpa using hn)\n  refine ⟨Module.Basis.mk hi hs.ge, ?_⟩\n  simpa using hv",
    )
    det = lambda f: op("det", K, V, f)
    card(
        "determinant_zero_kernel",
        ["V"],
        endo,
        "det(f)=0 と ker(f)≠0 は同値である。",
        "基底で行列表現し、行列式の消失と非自明な同次連立方程式の解の存在を対応させる。",
        [
            "V の有限基底を選び f を正方行列で表す。",
            "行列式が零なら非零ベクトルが行列の核に存在する。",
            "基底座標を戻して ker(f)≠0 を得る。",
            "逆に非零核ベクトルの座標は非自明な同次解なので行列式は零である。",
        ],
        iff(eq(det(f), op("scalar_zero", K)), ne(ker(V, V, f), bot(V))),
        "(LinearMap.det f = 0 → LinearMap.ker f ≠ ⊥) ∧ (LinearMap.ker f ≠ ⊥ → LinearMap.det f = 0)",
        "by\n  exact ⟨LinearMap.det_eq_zero_iff_ker_ne_bot.mp, LinearMap.det_eq_zero_iff_ker_ne_bot.mpr⟩",
    )
    card(
        "determinant_composition",
        ["V"],
        endo + [lm("g", "V", "V")],
        "det(g∘f)=det(g)det(f)。",
        "同じ基底で二つの写像を行列表示し、行列積の行列式の積公式を適用する。",
        [
            "V の有限基底を一つ選ぶ。",
            "合成 g∘f の行列は g の行列と f の行列の積になる。",
            "行列式の乗法性を適用する。",
            "基底に依存しない線形写像の行列式へ読み戻す。",
        ],
        eq(
            det(op("linear_comp", K, V, V, V, f, g)),
            op("scalar_mul", K, det(g), det(f)),
        ),
        "LinearMap.det (g.comp f) = LinearMap.det g * LinearMap.det f",
        "by\n  exact LinearMap.det_comp g f",
    )
    card(
        "determinant_scalar_degree",
        ["V"],
        endo + [scalar("a")],
        "det(a f)=a^(dim V) det(f)。",
        "行列の各列からスカラー a を取り出し、次元と同じ回数だけ積にする。",
        [
            "V の有限基底を選ぶ。",
            "a f の行列では各列が f の対応する列の a 倍である。",
            "行列式の各列での線形性により列の数だけ a を取り出す。",
            "列数は dim V なので a^(dim V) が係数となる。",
        ],
        eq(
            det(op("linear_smul", K, V, V, a, f)),
            op("scalar_mul", K, op("scalar_pow", K, a, dim(V)), det(f)),
        ),
        "LinearMap.det (a • f) = a ^ Module.finrank K V * LinearMap.det f",
        "by\n  exact LinearMap.det_smul a f",
    )
    return cards


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cards = build_cards()
    assert len(cards) == 27
    assert len({c["openmath_xml"] for c in cards}) == len(cards)
    assert all(4 <= len(c["sketch_steps"]) <= 10 for c in cards)
    source = (
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + c["id"]
            + "\n"
            + c["lean_target"]
            + " := "
            + c["lean_witness"].rstrip()
            for c in cards
        )
        + "\n"
    )
    witness = ROOT / "docs/linear-algebra-v2-batch.lean"
    witness.write_text(source)
    subprocess.run(
        ["lake", "env", "lean", str(witness)], cwd=WORKSPACE, check=True, timeout=180
    )
    pkg = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": cards,
        "evidence": {
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": sha(witness),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": next(p["rev"] for p in pkg if p["name"] == "mathlib"),
            "validator_sha256": sha(
                ROOT / "pals-agent/pals_agent/typed_linear_algebra_v2.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-linear-algebra-v2-registry.json"
            ),
        },
    }
    (ROOT / "docs/linear-algebra-v2-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"PASS: {len(cards)} general finite-dimensional cards compiled and canonicalized"
    )


if __name__ == "__main__":
    main()
