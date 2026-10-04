"""Author typed-calculus-v3 and compile every exact witness before emitting JSON."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_calculus_v3 import (
    canonicalize_typed_calculus_v3_openmath_xml,
    validate_canonical_typed_calculus_v3_openmath_xml,
)

BASE = "urn:pals:openmath:typed-calculus:v3"
WORKSPACE = ROOT / "pals-agent/lean-workspace"
WITNESS = ROOT / "docs/calculus-v3-supplement-batch.lean"
OUTPUT = ROOT / "docs/calculus-v3-supplement-batch.json"


def sym(cd, name):
    return f'<OMS cdbase="{BASE if cd in ("typed3", "calculus3") else "http://www.openmath.org/cd"}" cd="{cd}" name="{name}"/>'


def var(n):
    return f'<OMV name="{n}"/>'


def app(head, *args):
    return "<OMA>" + head + "".join(args) + "</OMA>"


def ca(n, *a):
    return app(sym("calculus3", n), *a)


def ar(n, *a):
    return app(sym("arith1", n), *a)


def rel(n, *a):
    return app(sym("relation1", n), *a)


def logic(n, *a):
    return app(sym("logic1", n), *a)


def bind(kind, vs, body):
    ds = "".join(
        "<OMATTR><OMATP>"
        + sym("typed3", "type")
        + sym("calculus3" if t in {"RealFunction", "RealSequence"} else "typed3", t)
        + "</OMATP>"
        + var(n)
        + "</OMATTR>"
        for n, t in vs
    )
    return (
        "<OMBIND>"
        + sym("calculus3" if kind in {"lambda", "sequence_lambda"} else "typed3", kind)
        + "<OMBVAR>"
        + ds
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


def forall(names, body):
    return bind("forall", [(n, "Real") for n in names.split()], body)


def exists(names, body):
    return bind("exists", [(n, "Real") for n in names.split()], body)


def lam(body):
    return bind("lambda", [("x", "Real")], body)


def ri(n):
    return ca("of_int", f"<OMI>{n}</OMI>")


def ni(n):
    return f"<OMI>{n}</OMI>"


def at(f, x):
    return ca("apply", f, x)


def D(f, x, d):
    return ca("has_deriv_at", f, x, d)


def Int(f, a, b):
    return ca("interval_integral", f, a, b)


def Integrable(f, a, b):
    return ca("interval_integrable", f, a, b)


def And(*a):
    return logic("and", *a)


def Imp(p, q):
    return logic("implies", p, q)


def eq(a, b):
    return rel("eq", a, b)


def le(a, b):
    return rel("leq", a, b)


def lt(a, b):
    return rel("lt", a, b)


def add(a, b):
    return ar("plus", a, b)


def sub(a, b):
    return ar("minus", a, b)


def mul(a, b):
    return ar("times", a, b)


def div(a, b):
    return ar("divide", a, b)


def neg(a):
    return ar("unary_minus", a)


def pow(a, n):
    return ar("power", a, n)


def closed(x, a, b):
    return And(le(a, x), le(x, b))


def opened(x, a, b):
    return And(lt(a, x), lt(x, b))


cards = []


def card(
    key, variables, premises, conclusion, statement, strategy, steps, target, proof
):
    body = conclusion
    for p in reversed(premises):
        body = Imp(p, body)
    vs = [
        (
            name,
            "RealFunction"
            if name == "f"
            else "RealSequence"
            if name in {"u", "v", "w"}
            else "Nat"
            if name in {"n", "m", "k"}
            else "Real",
        )
        for name in variables.split()
    ]
    xml = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind("forall", vs, body)
        + "</OMOBJ>"
    )
    canon = canonicalize_typed_calculus_v3_openmath_xml(xml)
    validate_canonical_typed_calculus_v3_openmath_xml(canon)
    cards.append(
        {
            "id": "calculus_supp_v3_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canon,
            "lean_target": target,
            "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
        }
    )


u, v, w, f, a, b, c, q, p, n, m, i, x = map(
    var, ["u", "v", "w", "f", "a", "b", "c", "q", "p", "n", "m", "i", "x"]
)
z, o = ri(0), ri(1)


def seq(body):
    return bind("sequence_lambda", [("i", "Nat")], body)


def sa(u, n):
    return ca("sequence_apply", u, n)


def lim(u, a):
    return ca("sequence_limit", u, a)


def hs(u, a):
    return ca("has_sum", u, a)


def summ(u):
    return ca("summable", u)


def ps(u, n):
    return ca("partial_sum", u, n)


def tsum(u):
    return ca("tsum", u)


def qnat(names, body):
    return bind("forall", [(n, "Nat") for n in names.split()], body)


def fact(n):
    return ca("nat_factorial", n)


def castn(n):
    return ca("of_nat", n)


def succ(n):
    return ca("nat_succ", n)


def taylor(n, f, l, r, a, x):
    return ca("taylor_on", n, f, l, r, a, x)


def iterd(n, f, l, r):
    return ca("iterated_deriv_on", n, f, l, r)


def cd(n, f, a, b):
    return ca("cont_diff_on", n, f, a, b)


ui, vi, wi = sa(u, i), sa(v, i), sa(w, i)
limtype = lambda s, L: f"Filter.Tendsto {s} Filter.atTop (nhds {L})"

exp = lambda t: ca("exp", t)
absx = lambda t: ar("abs", t)
Not = lambda p: logic("not", p)
Iff = lambda p, q: logic("equivalent", p, q)


card(
    "taylor_at_center",
    "f n a b c",
    [],
    eq(taylor(n, f, a, b, c, c), at(f, c)),
    "For every natural order n and every derivative domain uIcc(a,b), evaluating the Taylor polynomial centered at c at c itself gives f(c), without smoothness assumptions.",
    "Write the finite Taylor expansion at its center.",
    [
        "Write the finite Taylor expansion at its center.",
        "All positive-degree factors (c-c)^k vanish.",
        "The zero-degree coefficient is the original function value.",
        "Thus only f(c) remains, including at order n=0.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b c : ℝ) : taylorWithinEval f n (Set.uIcc a b) c c = f c",
    "exact taylorWithinEval_self f n (Set.uIcc a b) c",
)

card(
    "taylor_uniform_remainder_bound",
    "f n a b c x",
    [
        le(a, b),
        cd(succ(n), f, a, b),
        closed(x, a, b),
        forall(
            "y",
            Imp(
                closed(var("y"), a, b),
                le(absx(at(iterd(succ(n), f, a, b), var("y"))), c),
            ),
        ),
    ],
    le(
        absx(sub(at(f, x), taylor(n, f, a, b, a, x))),
        div(mul(c, pow(sub(x, a), succ(n))), castn(fact(n))),
    ),
    "For a≤b, f of class C^(n+1) on uIcc(a,b), and |f^(n+1)(y)|≤c throughout [a,b], the Taylor error at x∈[a,b] is at most c*(x-a)^(n+1)/n!, with all derivatives taken within that interval. This is the valid n! bound, not an asserted sharp constant.",
    "Use a≤b to identify the unordered derivative domain with [a,b].",
    [
        "Use a≤b to identify the unordered derivative domain with [a,b].",
        "Retain C^(n+1) regularity and the uniform derivative bound on the entire interval.",
        "Apply the normed Taylor mean-remainder estimate at x.",
        "Replace real norms by absolute values and preserve its n! denominator, including n=0 and a=b.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) (hab : a ≤ b) (hf : ContDiffOn ℝ (n+1) f (Set.uIcc a b)) (hx : a ≤ x ∧ x ≤ b) (hc : ∀ y, a ≤ y ∧ y ≤ b → |iteratedDerivWithin (n+1) f (Set.uIcc a b) y| ≤ c) : |f x - taylorWithinEval f n (Set.uIcc a b) a x| ≤ c*(x-a)^(n+1)/(n.factorial : ℝ)",
    "rw [Set.uIcc_of_le hab] at *\nchange ‖f x - taylorWithinEval f n (Set.Icc a b) a x‖ ≤ _\nexact taylor_mean_remainder_bound hab hf hx (fun y hy => hc y hy)",
)

card(
    "finite_taylor_not_exact",
    "n b",
    [lt(z, b)],
    And(eq(taylor(n, lam(pow(x, succ(n))), z, b, z, b), z), lt(z, pow(b, succ(n)))),
    "For every natural n and b>0, the degree-n Taylor polynomial of x^(n+1) centered at zero with derivative domain [0,b] evaluates to zero at b, while b^(n+1)>0. Finite Taylor truncations need not equal the function.",
    "Expand the degree-n Taylor polynomial as the sum of coefficients of orders k≤n.",
    [
        "Expand the degree-n Taylor polynomial as the sum of coefficients of orders k≤n.",
        "The k-th within derivative of x^(n+1) is a falling-factorial coefficient times x^(n+1-k).",
        "Every exponent n+1-k is positive, so each coefficient at zero vanishes.",
        "The Taylor value is zero while positivity of b gives a strictly positive actual function value, for every n including zero.",
    ],
    "example (n : ℕ) (b : ℝ) (hb : 0 < b) : taylorWithinEval (fun x : ℝ => x^(n+1)) n (Set.uIcc 0 b) 0 b = 0 ∧ (0:ℝ) < b^(n+1)",
    "constructor\n· rw [taylor_within_apply]\n  apply Finset.sum_eq_zero\n  intro k hk\n  have hk' : k ≤ n := Nat.le_of_lt_succ (Finset.mem_range.mp hk)\n  rw [Set.uIcc_of_le hb.le, iteratedDerivWithin_pow (show (0:ℝ) ∈ Set.Icc 0 b from ⟨le_rfl, hb.le⟩) (uniqueDiffOn_Icc hb) (n+1) k]\n  have hn : n+1-k ≠ 0 := by omega\n  simp [zero_pow hn]\n· exact pow_pos hb _",
)

card(
    "harmonic_term_test_counterexample",
    "c",
    [Not(eq(c, z))],
    And(lim(seq(div(c, castn(i))), z), Not(summ(seq(div(c, castn(i)))))),
    "For every nonzero real c, the terms c/n tend to zero as n→∞, yet the real series Σ c/n is not summable. The totalized n=0 term has no effect on either claim.",
    "Use the natural reciprocal limit to show c/n tends to zero.",
    [
        "Use the natural reciprocal limit to show c/n tends to zero.",
        "Rewrite division as c times n inverse.",
        "A nonzero constant multiplier preserves and reflects summability.",
        "Summability would contradict divergence of the harmonic series, proving the term-zero condition is insufficient.",
    ],
    "example (c : ℝ) (hc : c ≠ 0) : Filter.Tendsto (fun n : ℕ => c / (n:ℝ)) Filter.atTop (nhds 0) ∧ ¬Summable (fun n : ℕ => c / (n:ℝ))",
    "refine ⟨tendsto_const_div_atTop_nhds_zero_nat c, ?_⟩\nsimpa only [div_eq_mul_inv] using fun h => Real.not_summable_natCast_inv ((summable_mul_left_iff hc).mp h)",
)

card(
    "geometric_majorant_error",
    "u c q",
    [le(z, q), lt(q, o), qnat("i", le(absx(sa(u, i)), mul(c, pow(q, i))))],
    And(
        summ(u),
        qnat("n", le(absx(sub(ps(u, n), tsum(u))), div(mul(c, pow(q, n)), sub(o, q)))),
    ),
    "If 0≤q<1 and |u(n)|≤c*q^n for every n, then u is summable and every n-term partial sum differs from its total sum by at most c*q^n/(1-q).",
    "The geometric majorant with ratio q is summable.",
    [
        "The geometric majorant with ratio q is summable.",
        "Absolute comparison implies summability of u.",
        "Its finite initial sums therefore converge to its total sum.",
        "Bound successive partial-sum distances by c*q^n and sum the geometric tail.",
        "This yields the stated certified error bound for every truncation length, including zero.",
    ],
    "example (u : ℕ → ℝ) (c q : ℝ) (hq0 : 0 ≤ q) (hq : q < 1) (hu : ∀ n, |u n| ≤ c*q^n) : Summable u ∧ ∀ n, |(∑ i ∈ Finset.range n, u i)-(∑' i, u i)| ≤ c*q^n/(1-q)",
    "have hs : Summable u := ((summable_geometric_of_lt_one hq0 hq).mul_left c).of_norm_bounded hu\nrefine ⟨hs, ?_⟩\nintro n\nexact norm_sub_le_of_geometric_bound_of_hasSum hq hu hs.hasSum n",
)

card(
    "power_series_interior_convergence",
    "u a b c",
    [
        lim(
            bind(
                "sequence_lambda",
                [("j", "Nat")],
                ps(seq(mul(sa(u, i), pow(a, i))), var("j")),
            ),
            c,
        ),
        lt(absx(b), absx(a)),
    ],
    summ(seq(mul(sa(u, i), pow(b, i)))),
    "If the ordered natural partial sums of Σ u(n)*a^n converge to c and |b|<|a|, then Σ u(n)*b^n is unconditionally summable. The boundary series is allowed to converge only conditionally.",
    "Turn convergence of the ordered boundary partial sums into the Cauchy property.",
    [
        "Turn convergence of the ordered boundary partial sums into the Cauchy property.",
        "This bounds the boundary terms u(n)*a^n.",
        "Strictly smaller |b| gives geometric decay with ratio |b|/|a|<1.",
        "Apply the power-series interior convergence theorem to obtain absolute, hence unconditional, summability at b.",
    ],
    "example (u : ℕ → ℝ) (a b c : ℝ) (ha : Filter.Tendsto (fun n => ∑ i ∈ Finset.range n, u i*a^i) Filter.atTop (nhds c)) (hb : |b| < |a|) : Summable (fun n => u n*b^n)",
    "exact summable_powerSeries_of_norm_lt ha.cauchySeq hb",
)

card(
    "weighted_geometric_sum",
    "q",
    [lt(absx(q), o)],
    hs(seq(mul(castn(i), pow(q, i))), div(q, pow(sub(o, q), ni(2)))),
    "For every real |q|<1, the weighted power series Σ n*q^n has unconditional sum q/(1-q)².",
    "Check the strict interior condition |q|<1.",
    [
        "Check the strict interior condition |q|<1.",
        "The natural linear weight is dominated by geometric decay, so the series is summable.",
        "Apply the weighted geometric-series identity.",
        "Keep the n=0 term equal to zero and the sum q/(1-q)².",
    ],
    "example (q : ℝ) (hq : |q| < 1) : HasSum (fun n : ℕ => (n:ℝ)*q^n) (q/(1-q)^2)",
    "exact hasSum_coe_mul_geometric_of_norm_lt_one hq",
)

card(
    "geometric_boundary_counterexample",
    "q",
    [le(o, absx(q))],
    Not(summ(seq(pow(q, i)))),
    "For every real q with |q|≥1, the geometric power series Σ q^n is not summable. In particular, interior convergence does not license its boundary values.",
    "The exact summability criterion for a real geometric series is |q|<1.",
    [
        "The exact summability criterion for a real geometric series is |q|<1.",
        "Assume summability for a ratio with |q|≥1.",
        "The criterion would imply the contradictory strict inequality.",
        "Conclude nonsummability for the entire boundary-and-exterior family.",
    ],
    "example (q : ℝ) (hq : 1 ≤ |q|) : ¬Summable (fun n : ℕ => q^n)",
    "exact fun h => (not_lt.mpr hq) (summable_geometric_iff_norm_lt_one.mp h)",
)

card(
    "geometric_sum_derivative",
    "q",
    [lt(absx(q), o)],
    D(lam(tsum(seq(pow(x, i)))), q, div(o, pow(sub(o, q), ni(2)))),
    "For every |q|<1, the function x↦Σ x^n defined by the total infinite sum has derivative 1/(1-q)² at q. The identity is established locally inside the convergence interval.",
    "The strict condition |q|<1 provides an open neighborhood on which the geometric series converges.",
    [
        "The strict condition |q|<1 provides an open neighborhood on which the geometric series converges.",
        "On that neighborhood its sum equals 1/(1-x).",
        "Differentiate this reciprocal using 1-q≠0.",
        "Transfer the derivative across the neighborhood equality; no unproved general interchange of infinite sums and derivatives is assumed.",
    ],
    "example (q : ℝ) (hq : |q| < 1) : HasDerivAt (fun x : ℝ => ∑' n : ℕ, x^n) (1/(1-q)^2) q",
    "have hn : (1:ℝ)-q ≠ 0 := by have := (abs_lt.mp hq).2; linarith\nhave hd := (hasDerivAt_const q (1:ℝ)).div ((hasDerivAt_const q (1:ℝ)).sub (hasDerivAt_id q)) hn\nhave hd' : HasDerivAt (fun x : ℝ => 1/(1-x)) (1/(1-q)^2) q := by convert! hd using 1 <;> simp\napply hd'.congr_of_eventuallyEq\nfilter_upwards [(isOpen_lt continuous_abs continuous_const).mem_nhds hq] with x hx\nsimpa only [one_div] using tsum_geometric_of_norm_lt_one (show ‖x‖ < 1 from hx)",
)


def main():
    assert len(cards) == 9
    assert len({c["id"] for c in cards}) == len(cards)
    assert len({c["openmath_xml"] for c in cards}) == len(cards)
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
    WITNESS.write_text(source)
    r = subprocess.run(
        ["lake", "env", "lean", str(WITNESS)],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    hashfile = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    packages = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    evidence = {
        "witness_path": str(WITNESS.relative_to(ROOT)),
        "witness_sha256": hashfile(WITNESS),
        "validator_sha256": hashfile(
            ROOT / "pals-agent/pals_agent/typed_calculus_v3.py"
        ),
        "registry_sha256": hashfile(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-calculus-v3-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": next(p["rev"] for p in packages if p["name"] == "mathlib"),
    }
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": "typed-calculus-v3",
                "cards": cards,
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"cards={len(cards)} openmath=validated lean=compiled output={OUTPUT}")


if __name__ == "__main__":
    main()
