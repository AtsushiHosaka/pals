"""Generate independently authored general linear-map Draft candidates and compile witnesses.

Uses the existing module profile without adding carriers or symbols. Does not publish.
Run with pals-agent/.venv/bin/python and PYTHONPATH=pals-agent.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_commutative_algebra_modules import (
    canonicalize_typed_commutative_algebra_modules_openmath_xml as canonicalize,
)
from pals_agent.typed_commutative_algebra_modules import (
    validate_canonical_typed_commutative_algebra_modules_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
STEM = "linear-algebra-reuse-batch-20260930"
PROFILE = "typed-commutative-algebra-modules-v1"
TYPED = "urn:pals:openmath:typed-commutative-algebra-modules:v1"
STANDARD = "http://www.openmath.org/cd"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(name):
    return f"<OMV name={quoteattr(name)}/>"


def app(head, *xs):
    return "<OMA>" + head + "".join(xs) + "</OMA>"


def mod(name, *xs):
    return app(sym("module1", name), *xs)


def logic(name, *xs):
    return app(sym("logic1", name, STANDARD), *xs)


def eq(x, y):
    return app(sym("relation1", "eq", STANDARD), x, y)


def iff(x, y):
    return logic("and", logic("implies", x, y), logic("implies", y, x))


R = var("R")


def bot(m):
    return mod("submodule_bot", R, var(m))


def top(m):
    return mod("submodule_top", R, var(m))


def sup(m, x, y):
    return mod("submodule_sup", R, var(m), x, y)


def inf(m, x, y):
    return mod("submodule_inf", R, var(m), x, y)


def le(m, x, y):
    return mod("submodule_le", R, var(m), x, y)


def ident(m):
    return mod("linear_id", R, var(m))


def zero(m, n):
    return mod("linear_zero", R, var(m), var(n))


def ker(m, n, f):
    return mod("linear_kernel", R, var(m), var(n), f)


def ran(m, n, f):
    return mod("linear_range", R, var(m), var(n), f)


def inj(m, n, f):
    return mod("linear_injective", R, var(m), var(n), f)


def surj(m, n, f):
    return mod("linear_surjective", R, var(m), var(n), f)


def comp(m, n, p, f, g):
    return mod("linear_comp", R, var(m), var(n), var(p), f, g)


def exact(m, n, p, f, g):
    return mod("exact_at", R, var(m), var(n), var(p), f, g)


def proposition(modules, maps, subs, body):
    ds = [("R", sym("module1", "CommRing"))]
    ds += [(m, mod("Module", R)) for m in modules]
    ds += [(f, mod("LinearMap", R, var(m), var(n))) for f, m, n in maps]
    ds += [(i, mod("Submodule", R, var(m))) for i, m in subs]
    decls = "".join(
        "<OMATTR><OMATP>"
        + sym("typed1", "type")
        + ty
        + "</OMATP>"
        + var(n)
        + "</OMATTR>"
        for n, ty in ds
    )
    return (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"><OMBIND>'
        + sym("typed1", "forall")
        + "<OMBVAR>"
        + decls
        + "</OMBVAR>"
        + body
        + "</OMBIND></OMOBJ>"
    )


def cards():
    result = []

    def add(key, modules, maps, statement, strategy, steps, body, goal, proof, subs=()):
        prefix = "{R " + " ".join(modules) + " : Type*} [CommRing R] "
        prefix += " ".join(f"[AddCommGroup {m}] [Module R {m}]" for m in modules)
        variables = " ".join(f"({f} : {m} →ₗ[R] {n})" for f, m, n in maps)
        variables += " " + " ".join(f"({i} : Submodule R {m})" for i, m in subs)
        xml = canonicalize(proposition(modules, maps, subs, body))
        validate(xml)
        assert 4 <= len(steps) <= 10
        result.append(
            {
                "id": "la_reuse_" + key,
                "canonical_statement": statement,
                "proof_strategy": strategy,
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": f"example {prefix} {variables.strip()} : {goal}",
                "lean_witness": proof,
            }
        )

    f, g, h = map(var, ("f", "g", "h"))
    mn = [("f", "M", "N")]
    mnp = mn + [("g", "N", "P")]
    kf = ker("M", "N", f)
    rf = ran("M", "N", f)
    gf = comp("M", "N", "P", f, g)
    add(
        "kernel_injectivity",
        ["M", "N"],
        mn,
        "任意の可換環 R 上の線形写像 f:M→N は、核が零部分加群であることと単射であることが同値である。",
        "二つの元の像の一致を差が核に属することへ変換する。",
        [
            "核が零であると仮定する。",
            "f(x)=f(y) から f(x−y)=0 を得る。",
            "核の条件から x−y=0、したがって x=y を導く。",
            "逆に単射なら f(x)=0=f(0) から x=0 となり、核が零と結論する。",
        ],
        iff(eq(kf, bot("M")), inj("M", "N", f)),
        "(LinearMap.ker f = ⊥ → Function.Injective f) ∧ (Function.Injective f → LinearMap.ker f = ⊥)",
        "by\n  exact ⟨LinearMap.ker_eq_bot.mp, LinearMap.ker_eq_bot.mpr⟩",
    )
    add(
        "range_surjectivity",
        ["M", "N"],
        mn,
        "任意の可換環 R 上の線形写像 f:M→N は、像が N 全体であることと全射であることが同値である。",
        "像への所属を原像の存在と読み替える。",
        [
            "像が全体であると仮定して任意の y∈N を取る。",
            "y は像に属するので f(x)=y となる x を取れる。",
            "逆に全射なら任意の y にその原像を選ぶ。",
            "全ての y が像に属するため像は全体に一致する。",
        ],
        iff(eq(rf, top("N")), surj("M", "N", f)),
        "(LinearMap.range f = ⊤ → Function.Surjective f) ∧ (Function.Surjective f → LinearMap.range f = ⊤)",
        "by\n  exact ⟨LinearMap.range_eq_top.mp, LinearMap.range_eq_top.mpr⟩",
    )
    add(
        "kernel_detects_zero",
        ["M", "N"],
        mn,
        "線形写像 f:M→N の核が M 全体であることと f が零写像であることは同値である。",
        "核が全体という条件を全ての入力で値が零という写像の外延的条件へ変換する。",
        [
            "核が全体であると仮定する。",
            "任意の x は核に入るため f(x)=0 となる。",
            "写像の外延性から f=0 を得る。",
            "逆に零写像は全ての x を零へ送るので核が全体となる。",
        ],
        iff(eq(kf, top("M")), eq(f, zero("M", "N"))),
        "(LinearMap.ker f = ⊤ → f = 0) ∧ (f = 0 → LinearMap.ker f = ⊤)",
        "by\n  exact ⟨LinearMap.ker_eq_top.mp, LinearMap.ker_eq_top.mpr⟩",
    )
    add(
        "range_detects_zero",
        ["M", "N"],
        mn,
        "線形写像 f:M→N の像が零部分加群であることと f が零写像であることは同値である。",
        "各値 f(x) が像に属することを使って零写像を判定する。",
        [
            "像が零であると仮定し、任意の x を取る。",
            "f(x) は像に属するので f(x)=0 を得る。",
            "外延性から f=0 を示す。",
            "逆に零写像の像は零のみを含み、零自身も像に属する。",
        ],
        iff(eq(rf, bot("N")), eq(f, zero("M", "N"))),
        "(LinearMap.range f = ⊥ → f = 0) ∧ (f = 0 → LinearMap.range f = ⊥)",
        "by\n  exact ⟨LinearMap.range_eq_bot.mp, LinearMap.range_eq_bot.mpr⟩",
    )
    add(
        "kernel_composition_inclusion",
        ["M", "N", "P"],
        mnp,
        "可換環 R 上の線形写像 f:M→N、g:N→P について ker(f)⊆ker(g∘f)。",
        "f によって消える元は、続けて g を適用しても零のままである。",
        [
            "x∈ker(f) を任意に取る。",
            "核の定義から f(x)=0 を取り出す。",
            "線形性による g(0)=0 を用いて g(f(x))=0 とする。",
            "x∈ker(g∘f) を得て包含を閉じる。",
        ],
        le("M", kf, ker("M", "P", gf)),
        "LinearMap.ker f ≤ LinearMap.ker (g.comp f)",
        "by\n  exact LinearMap.ker_le_ker_comp f g",
    )
    add(
        "kernel_postcompose_injective",
        ["M", "N", "P"],
        mnp,
        "線形写像 f:M→N と単射線形写像 g:N→P について ker(g∘f)=ker(f)。",
        "g の単射性によって g(f(x))=0 から f(x)=0 を回復する。",
        [
            "g の単射性を核が零という条件に変える。",
            "合成の核の元 x を取り g(f(x))=g(0) と書く。",
            "g の単射性から f(x)=0 を得る。",
            "逆の包含は零保存から従い、両包含で核の等式を得る。",
        ],
        logic("implies", inj("N", "P", g), eq(ker("M", "P", gf), kf)),
        "Function.Injective g → LinearMap.ker (g.comp f) = LinearMap.ker f",
        "by\n  intro hg\n  exact LinearMap.ker_comp_of_ker_eq_bot f (LinearMap.ker_eq_bot.mpr hg)",
    )
    add(
        "range_precompose_surjective",
        ["M", "N", "P"],
        mnp,
        "全射線形写像 f:M→N と線形写像 g:N→P について im(g∘f)=im(g)。",
        "g の入力を f の原像で置き換えて合成の像の証人を作る。",
        [
            "合成の像は g の像に含まれることを確認する。",
            "逆に g(y) という任意の像の元を取る。",
            "f の全射性で f(x)=y となる x を取る。",
            "g(y)=g(f(x)) として逆包含を得る。",
        ],
        logic("implies", surj("M", "N", f), eq(ran("M", "P", gf), ran("N", "P", g))),
        "Function.Surjective f → LinearMap.range (g.comp f) = LinearMap.range g",
        "by\n  intro hf\n  exact LinearMap.range_comp_of_range_eq_top g (LinearMap.range_eq_top.mpr hf)",
    )
    add(
        "zero_composite_criterion",
        ["M", "N", "P"],
        mnp,
        "線形写像 f:M→N、g:N→P について im(f)⊆ker(g) と g∘f=0 は同値である。",
        "像の証人と核への所属を展開し、合成写像の点ごとの零と対応させる。",
        [
            "im(f)⊆ker(g) を仮定する。",
            "f(x) は像に属するので g(f(x))=0 とわかる。",
            "外延性から合成は零写像となる。",
            "逆に合成が零なら像の任意の元を f(x) と書き、核への所属を得る。",
        ],
        iff(le("N", rf, ker("N", "P", g)), eq(gf, zero("M", "P"))),
        "(LinearMap.range f ≤ LinearMap.ker g → g.comp f = 0) ∧ (g.comp f = 0 → LinearMap.range f ≤ LinearMap.ker g)",
        "by\n  exact ⟨LinearMap.range_le_ker_iff.mp, LinearMap.range_le_ker_iff.mpr⟩",
    )
    add(
        "injective_composition",
        ["M", "N", "P"],
        mnp,
        "単射線形写像 f:M→N、g:N→P の合成 g∘f は単射である。",
        "合成の値の等式から、g、f の順に単射性を適用する。",
        [
            "g(f(x))=g(f(y)) を仮定する。",
            "g の単射性により f(x)=f(y) を得る。",
            "f の単射性により x=y を得る。",
            "任意の二元について成立するので合成は単射である。",
        ],
        logic(
            "implies",
            logic("and", inj("M", "N", f), inj("N", "P", g)),
            inj("M", "P", gf),
        ),
        "Function.Injective f ∧ Function.Injective g → Function.Injective (g.comp f)",
        "by\n  rintro ⟨hf, hg⟩ x y hxy\n  exact hf (hg hxy)",
    )
    add(
        "surjective_composition",
        ["M", "N", "P"],
        mnp,
        "全射線形写像 f:M→N、g:N→P の合成 g∘f は全射である。",
        "目標の元から g、f の順に原像を取る。",
        [
            "任意の z∈P を取る。",
            "g の全射性から g(y)=z となる y を取る。",
            "f の全射性から f(x)=y となる x を取る。",
            "x が合成による z の原像であることを確認する。",
        ],
        logic(
            "implies",
            logic("and", surj("M", "N", f), surj("N", "P", g)),
            surj("M", "P", gf),
        ),
        "Function.Surjective f ∧ Function.Surjective g → Function.Surjective (g.comp f)",
        "by\n  rintro ⟨hf, hg⟩ z\n  obtain ⟨y, rfl⟩ := hg z\n  obtain ⟨x, rfl⟩ := hf y\n  exact ⟨x, rfl⟩",
    )
    add(
        "injective_composite_first_factor",
        ["M", "N", "P"],
        mnp,
        "線形写像の合成 g∘f が単射なら、前段の線形写像 f は単射である。",
        "f の値の等式に g を適用して、合成の単射性に帰着する。",
        [
            "合成が単射であると仮定する。",
            "f(x)=f(y) という任意の等式を取る。",
            "両辺に g を適用し合成の値を一致させる。",
            "合成の単射性から x=y を得る。",
        ],
        logic("implies", inj("M", "P", gf), inj("M", "N", f)),
        "Function.Injective (g.comp f) → Function.Injective f",
        "by\n  intro hgf x y hxy\n  exact hgf (congrArg g hxy)",
    )
    add(
        "surjective_composite_last_factor",
        ["M", "N", "P"],
        mnp,
        "線形写像の合成 g∘f が全射なら、後段の線形写像 g は全射である。",
        "合成による原像 x の f(x) を g の原像にする。",
        [
            "合成が全射であると仮定する。",
            "任意の z∈P を取る。",
            "合成の全射性から g(f(x))=z となる x を取る。",
            "f(x) を原像として g の全射性を示す。",
        ],
        logic("implies", surj("M", "P", gf), surj("N", "P", g)),
        "Function.Surjective (g.comp f) → Function.Surjective g",
        "by\n  intro hgf z\n  obtain ⟨x, hx⟩ := hgf z\n  exact ⟨f x, hx⟩",
    )
    inverse = [("f", "M", "N"), ("g", "N", "M")]
    gfm = comp("M", "N", "M", f, g)
    fgn = comp("N", "M", "N", g, f)
    add(
        "left_inverse_injective",
        ["M", "N"],
        inverse,
        "線形写像 f:M→N が線形左逆写像 g:N→M（g∘f=id_M）を持つなら f は単射である。",
        "像の一致に左逆写像を適用して元を復元する。",
        [
            "左逆関係 g∘f=id_M を任意の元で評価する。",
            "f(x)=f(y) の両辺に g を適用する。",
            "左逆関係で g(f(x)), g(f(y)) を x,y に戻す。",
            "x=y を得て f の単射性を示す。",
        ],
        logic("implies", eq(gfm, ident("M")), inj("M", "N", f)),
        "g.comp f = LinearMap.id → Function.Injective f",
        "by\n  intro hgf x y hxy\n  have hx := LinearMap.congr_fun hgf x\n  have hy := LinearMap.congr_fun hgf y\n  simpa only [LinearMap.comp_apply, LinearMap.id_apply] using hx.symm.trans ((congrArg g hxy).trans hy)",
    )
    add(
        "right_inverse_surjective",
        ["M", "N"],
        inverse,
        "線形写像 f:M→N が線形右逆写像 g:N→M（f∘g=id_N）を持つなら f は全射である。",
        "右逆写像 g によって各目標の原像を明示する。",
        [
            "右逆関係 f∘g=id_N を仮定する。",
            "任意の y∈N を取る。",
            "g(y) を y の原像候補に選ぶ。",
            "右逆関係を y で評価して f(g(y))=y を確認する。",
        ],
        logic("implies", eq(fgn, ident("N")), surj("M", "N", f)),
        "f.comp g = LinearMap.id → Function.Surjective f",
        "by\n  intro hfg y\n  exact ⟨g y, LinearMap.congr_fun hfg y⟩",
    )
    cancel_post = mn + [("h", "M", "N"), ("g", "N", "P")]
    add(
        "cancel_injective_postcomposition",
        ["M", "N", "P"],
        cancel_post,
        "単射線形写像 g:N→P に対し、g∘f=g∘h なら線形写像 f,h:M→N は等しい。",
        "合成の等式を各元で評価して g を単射性で消去する。",
        [
            "g の単射性と合成写像の等式を取る。",
            "任意の x∈M で合成の等式を評価する。",
            "g の単射性により f(x)=h(x) を得る。",
            "線形写像の外延性によって f=h を結論する。",
        ],
        logic(
            "implies",
            logic("and", inj("N", "P", g), eq(gf, comp("M", "N", "P", h, g))),
            eq(f, h),
        ),
        "Function.Injective g ∧ g.comp f = g.comp h → f = h",
        "by\n  rintro ⟨hg, heq⟩\n  ext x\n  exact hg (LinearMap.congr_fun heq x)",
    )
    cancel_pre = mn + [("g", "N", "P"), ("h", "N", "P")]
    add(
        "cancel_surjective_precomposition",
        ["M", "N", "P"],
        cancel_pre,
        "全射線形写像 f:M→N に対し、g∘f=h∘f なら線形写像 g,h:N→P は等しい。",
        "任意の入力を全射 f の原像で表して合成の等式を使う。",
        [
            "f の全射性と合成写像の等式を取る。",
            "任意の y∈N に対して f(x)=y となる x を取る。",
            "合成の等式を x で評価して g(y)=h(y) を得る。",
            "外延性により g=h を示す。",
        ],
        logic(
            "implies",
            logic("and", surj("M", "N", f), eq(gf, comp("M", "N", "P", f, h))),
            eq(g, h),
        ),
        "Function.Surjective f ∧ g.comp f = h.comp f → g = h",
        "by\n  rintro ⟨hf, heq⟩\n  ext y\n  obtain ⟨x, rfl⟩ := hf y\n  exact LinearMap.congr_fun heq x",
    )
    add(
        "inverse_uniqueness",
        ["M", "N"],
        inverse + [("h", "N", "M")],
        "f:M→N の線形左逆写像 g と線形右逆写像 h は一致する。",
        "g=g∘(f∘h)=(g∘f)∘h=h と合成の結合性を使う。",
        [
            "g∘f=id_M と f∘h=id_N を仮定する。",
            "任意の y∈N について y=f(h(y)) と置き換える。",
            "g(f(h(y))) を左逆関係で h(y) に簡約する。",
            "各点での一致から g=h を得る。",
        ],
        logic(
            "implies",
            logic(
                "and", eq(gfm, ident("M")), eq(comp("N", "M", "N", h, f), ident("N"))
            ),
            eq(g, h),
        ),
        "g.comp f = LinearMap.id ∧ f.comp h = LinearMap.id → g = h",
        "by\n  rintro ⟨hgf, hfh⟩\n  ext y\n  have a := LinearMap.congr_fun hgf (h y)\n  have b := LinearMap.congr_fun hfh y\n  exact (congrArg g b).symm.trans a",
    )
    add(
        "split_kernel_range_complement",
        ["M", "N"],
        inverse,
        "f:M→N、g:N→M が f∘g=id_N を満たすなら、im(g)+ker(f)=M かつ im(g)∩ker(f)=0。",
        "各 x を g(f(x)) と x−g(f(x)) に分解し、右逆関係で後者が核に入ることを示す。",
        [
            "任意の x を g(f(x))+(x−g(f(x))) と書く。",
            "第1項は im(g)、第2項は f∘g=id によって ker(f) に入る。",
            "よって im(g)+ker(f) は全体を含む。",
            "共通部分の元を g(y) と書くと f(g(y))=y=0 なので元自体が零となる。",
        ],
        logic(
            "implies",
            eq(fgn, ident("N")),
            logic(
                "and",
                eq(sup("M", ran("N", "M", g), kf), top("M")),
                eq(inf("M", ran("N", "M", g), kf), bot("M")),
            ),
        ),
        "f.comp g = LinearMap.id → LinearMap.range g ⊔ LinearMap.ker f = ⊤ ∧ LinearMap.range g ⊓ LinearMap.ker f = ⊥",
        "by\n  intro hfg\n  constructor\n  · apply top_unique\n    intro x _\n    apply Submodule.mem_sup.mpr\n    refine ⟨g (f x), ⟨f x, rfl⟩, x - g (f x), ?_, ?_⟩\n    · change f (x - g (f x)) = 0\n      rw [map_sub, show f (g (f x)) = f x from LinearMap.congr_fun hfg (f x), sub_self]\n    · abel\n  · apply bot_unique\n    rintro x ⟨⟨y, rfl⟩, hy⟩\n    change g y = 0\n    have hy0 : y = 0 := (LinearMap.congr_fun hfg y).symm.trans hy\n    simp [hy0]",
    )
    endo = [("f", "M", "M")]
    ee = comp("M", "M", "M", f, f)
    er = ran("M", "M", f)
    ek = ker("M", "M", f)
    add(
        "idempotent_kernel_range_complement",
        ["M"],
        endo,
        "冪等線形写像 f:M→M（f∘f=f）について im(f)+ker(f)=M かつ im(f)∩ker(f)=0。",
        "冪等性により各元を像成分 f(x) と核成分 x−f(x) に分ける。",
        [
            "f(f(x))=f(x) から f(x−f(x))=0 を示す。",
            "x=f(x)+(x−f(x)) により像と核の和が全体となる。",
            "共通部分の元を f(y) と書く。",
            "冪等性と核への所属から f(y)=f(f(y))=0 を得る。",
        ],
        logic(
            "implies",
            eq(ee, f),
            logic(
                "and", eq(sup("M", er, ek), top("M")), eq(inf("M", er, ek), bot("M"))
            ),
        ),
        "f.comp f = f → LinearMap.range f ⊔ LinearMap.ker f = ⊤ ∧ LinearMap.range f ⊓ LinearMap.ker f = ⊥",
        "by\n  intro hf\n  have hi : IsIdempotentElem f := hf\n  exact ⟨(LinearMap.IsIdempotentElem.isCompl hi).sup_eq_top, (LinearMap.IsIdempotentElem.isCompl hi).inf_eq_bot⟩",
    )
    i, j, k = map(var, ("I", "J", "K"))
    add(
        "submodule_modular_law",
        ["M"],
        [],
        "部分加群 I,J,K⊆M について I⊆K なら I+(J∩K)=(I+J)∩K。",
        "和の元を分解し、I⊆K を使って差を取ることで J 成分も K に入ると示す。",
        [
            "I⊆K を仮定して左辺の元を I 成分と J∩K 成分に分ける。",
            "両成分が K に入るため左辺から右辺への包含を得る。",
            "逆に右辺の元を i+j と分け、i∈I⊆K を使う。",
            "i+j と i が K に入るので j∈K となり、左辺への包含を得る。",
        ],
        logic(
            "implies",
            le("M", i, k),
            eq(sup("M", i, inf("M", j, k)), inf("M", sup("M", i, j), k)),
        ),
        "I ≤ K → I ⊔ (J ⊓ K) = (I ⊔ J) ⊓ K",
        "by\n  intro hik\n  exact (sup_inf_assoc_of_le J hik).symm",
        subs=[("I", "M"), ("J", "M"), ("K", "M")],
    )
    add(
        "exact_sequence_zero_composite",
        ["M", "N", "P"],
        mnp,
        "線形写像 f:M→N、g:N→P が N で完全（im(f)=ker(g)）なら g∘f=0。",
        "完全性から像が次の核に含まれることを取り出す。",
        [
            "完全性 im(f)=ker(g) を取る。",
            "任意の x について f(x)∈im(f) を確認する。",
            "完全性により f(x)∈ker(g)、したがって g(f(x))=0 を得る。",
            "写像の外延性により合成は零写像である。",
        ],
        logic("implies", exact("M", "N", "P", f, g), eq(gf, zero("M", "P"))),
        "LinearMap.range f = LinearMap.ker g → g.comp f = 0",
        "by\n  intro he\n  exact LinearMap.range_le_ker_iff.mp he.le",
    )
    qmaps = [("h", "Q", "M")] + mnp
    fh = comp("Q", "M", "N", h, f)
    add(
        "exactness_precompose_surjection",
        ["Q", "M", "N", "P"],
        qmaps,
        "h:Q→M が全射で im(f)=ker(g) なら、im(f∘h)=ker(g) である。",
        "全射の前合成で像が変わらないことを使い、完全性を保存する。",
        [
            "h の全射性から im(h)=M を得る。",
            "任意の f(x) に対して h の原像を取る。",
            "これにより im(f∘h)=im(f) を示す。",
            "元の完全性 im(f)=ker(g) とつないで結論する。",
        ],
        logic(
            "implies",
            logic("and", surj("Q", "M", h), exact("M", "N", "P", f, g)),
            exact("Q", "N", "P", fh, g),
        ),
        "Function.Surjective h ∧ LinearMap.range f = LinearMap.ker g → LinearMap.range (f.comp h) = LinearMap.ker g",
        "by\n  rintro ⟨hh, he⟩\n  rw [LinearMap.range_comp_of_range_eq_top f (LinearMap.range_eq_top.mpr hh), he]",
    )
    add(
        "exactness_postcompose_injection",
        ["M", "N", "P", "Q"],
        mnp + [("h", "P", "Q")],
        "h:P→Q が単射で im(f)=ker(g) なら、im(f)=ker(h∘g) である。",
        "単射の後合成で核が変わらないことを使い、完全性を保存する。",
        [
            "h の単射性から ker(h)=0 を得る。",
            "h(g(y))=0 なら h の単射性により g(y)=0 とわかる。",
            "逆の包含と合わせて ker(h∘g)=ker(g) を得る。",
            "元の完全性で像とこの核を一致させる。",
        ],
        logic(
            "implies",
            logic("and", inj("P", "Q", h), exact("M", "N", "P", f, g)),
            exact("M", "N", "Q", f, comp("N", "P", "Q", g, h)),
        ),
        "Function.Injective h ∧ LinearMap.range f = LinearMap.ker g → LinearMap.range f = LinearMap.ker (h.comp g)",
        "by\n  rintro ⟨hh, he⟩\n  rw [LinearMap.ker_comp_of_ker_eq_bot g (LinearMap.ker_eq_bot.mpr hh)]\n  exact he",
    )
    fg = comp("M", "M", "M", g, f)
    gfend = comp("M", "M", "M", f, g)
    add(
        "commuting_maps_kernel_sum",
        ["M"],
        [("f", "M", "M"), ("g", "M", "M")],
        "可換な線形自己写像 f,g:M→M について ker(f)+ker(g)⊆ker(g∘f)。",
        "二つの核からの包含を、可換性で合成順序を交換して示す。",
        [
            "ker(f)⊆ker(g∘f) は合成の零保存から得る。",
            "ker(g) の元に対して f(g(x))=0 を得る。",
            "可換性によりこれを g(f(x))=0 と読み替える。",
            "二つの包含を部分加群の和の最小性でまとめる。",
        ],
        logic(
            "implies",
            eq(fg, gfend),
            le("M", sup("M", ker("M", "M", f), ker("M", "M", g)), ker("M", "M", gfend)),
        ),
        "f.comp g = g.comp f → LinearMap.ker f ⊔ LinearMap.ker g ≤ LinearMap.ker (g.comp f)",
        "by\n  intro hfg\n  apply sup_le\n  · exact LinearMap.ker_le_ker_comp f g\n  · rw [← hfg]\n    exact LinearMap.ker_le_ker_comp g f",
    )
    return result


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    batch = cards()
    assert len(batch) == 24
    identities = [x["openmath_xml"] for x in batch]
    assert len(set(identities)) == len(batch), "duplicate canonical identities"
    old = json.loads(
        (
            ROOT
            / "docs/typed-commutative-algebra-modules-v1-sealed-manifest.proposal.json"
        ).read_text()
    )
    old_ids = {canonicalize(c["openmath_xml"]) for c in old["cards"]}
    assert not set(identities) & old_ids, "collision with existing module cards"
    source = (
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + c["id"]
            + "\n"
            + c["lean_target"]
            + " := "
            + c["lean_witness"].rstrip()
            for c in batch
        )
        + "\n"
    )
    witness = ROOT / "docs" / f"{STEM}.lean"
    witness.write_text(source)
    subprocess.run(
        ["lake", "env", "lean", str(witness)], cwd=WORKSPACE, check=True, timeout=180
    )
    packages = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    mathlib = next(p["rev"] for p in packages if p["name"] == "mathlib")
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": batch,
        "evidence": {
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": sha(witness),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": mathlib,
            "validator_sha256": sha(
                ROOT / "pals-agent/pals_agent/typed_commutative_algebra_modules.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-commutative-algebra-modules-v1-registry.json"
            ),
        },
    }
    output = ROOT / "docs" / f"{STEM}.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Compiled and generated {len(batch)} distinct cards: {output}")


if __name__ == "__main__":
    main()
