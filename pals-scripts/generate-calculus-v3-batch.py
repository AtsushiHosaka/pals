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
WITNESS = ROOT / "docs/calculus-v3-batch.lean"
OUTPUT = ROOT / "docs/calculus-v3-batch.json"


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
            "id": "calculus_v3_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canon,
            "lean_target": target,
            "lean_witness": "by\n  " + proof,
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

# Each statement has an independently stated Lean proposition and mathematical outline.
for key, oper, sign, method in [
    ("sum", "plus", "+", "add"),
    ("product", "times", "*", "mul"),
]:
    card(
        "limit_" + key,
        "u v a b",
        [lim(u, a), lim(v, b)],
        lim(seq(ar(oper, ui, vi)), ar(oper, a, b)),
        f"If real sequences u and v converge to a and b, respectively, their pointwise {key} converges to a {sign} b.",
        f"Apply continuity of real {key} to the pair of converging sequences.",
        [
            "Fix both real sequences and their limits.",
            "Combine their convergence into convergence of the pair.",
            f"Real {key} is continuous on the pair space.",
            "Apply this continuous operation to the converging pair.",
        ],
        f"example (u v : ℕ → ℝ) (a b : ℝ) (hu : {limtype('u', 'a')}) (hv : {limtype('v', 'b')}) : {limtype(f'(fun n => u n {sign} v n)', f'(a {sign} b)')}",
        f"exact hu.{method} hv",
    )
card(
    "limit_quotient",
    "u v a b",
    [lim(u, a), lim(v, b), rel("neq", b, z)],
    lim(seq(div(ui, vi)), div(a, b)),
    "If u→a and v→b with b≠0, the sequence u(n)/v(n) converges to a/b.",
    "Use continuity of division at a pair whose denominator limit is nonzero.",
    [
        "Retain both convergence assumptions.",
        "Check the limit b of the denominator is nonzero.",
        "Division is continuous at (a,b).",
        "Apply continuity to obtain the quotient limit.",
    ],
    f"example (u v : ℕ → ℝ) (a b : ℝ) (hu : {limtype('u', 'a')}) (hv : {limtype('v', 'b')}) (hb : b ≠ 0) : {limtype('(fun n => u n / v n)', '(a / b)')}",
    "exact hu.div hv hb",
)
card(
    "limit_absolute_value",
    "u a",
    [lim(u, a)],
    lim(seq(ar("abs", ui)), ar("abs", a)),
    "If u(n) converges to a, then |u(n)| converges to |a|.",
    "Apply continuity of real absolute value to the convergent sequence.",
    [
        "Fix u and its limit a.",
        "The absolute-value function is continuous everywhere.",
        "Compose the sequence with absolute value.",
        "The resulting limit is the absolute value of a.",
    ],
    f"example (u : ℕ → ℝ) (a : ℝ) (hu : {limtype('u', 'a')}) : {limtype('(fun n => |u n|)', '|a|')}",
    "exact hu.abs",
)
card(
    "limit_unique",
    "u a b",
    [lim(u, a), lim(u, b)],
    eq(a, b),
    "A real sequence cannot converge to two different real limits.",
    "Apply uniqueness of limits in the Hausdorff real topology.",
    [
        "Fix one sequence u.",
        "Assume convergence to both a and b.",
        "The natural atTop filter is nontrivial and ℝ is Hausdorff.",
        "Uniqueness of limits gives a=b.",
    ],
    f"example (u : ℕ → ℝ) (a b : ℝ) (ha : {limtype('u', 'a')}) (hb : {limtype('u', 'b')}) : a = b",
    "exact tendsto_nhds_unique ha hb",
)
card(
    "limit_order",
    "u v a b",
    [lim(u, a), lim(v, b), qnat("i", le(ui, vi))],
    le(a, b),
    "If u(n)≤v(n) for every natural n and both sequences converge to a,b, then a≤b.",
    "Pass a closed non-strict real inequality to the limit.",
    [
        "Fix the two convergent sequences.",
        "The pointwise inequality holds eventually because it holds everywhere.",
        "The order relation ≤ is closed in ℝ×ℝ.",
        "Pass to the limit and retain the non-strict inequality.",
    ],
    f"example (u v : ℕ → ℝ) (a b : ℝ) (hu : {limtype('u', 'a')}) (hv : {limtype('v', 'b')}) (hle : ∀ n, u n ≤ v n) : a ≤ b",
    "exact le_of_tendsto_of_tendsto hu hv (Filter.Eventually.of_forall hle)",
)
card(
    "squeeze",
    "u v w a",
    [lim(u, a), lim(w, a), qnat("i", le(ui, vi)), qnat("i", le(vi, wi))],
    lim(v, a),
    "If u and w converge to a and u(n)≤v(n)≤w(n) for every n, then v converges to a.",
    "Apply the squeeze theorem to the matching lower and upper limits.",
    [
        "Fix matching limit a for the bounding sequences.",
        "Use u(n)≤v(n) at every index.",
        "Use v(n)≤w(n) at every index.",
        "The squeeze theorem yields convergence of v to a.",
    ],
    f"example (u v w : ℕ → ℝ) (a : ℝ) (hu : {limtype('u', 'a')}) (hw : {limtype('w', 'a')}) (hlo : ∀ n, u n ≤ v n) (hhi : ∀ n, v n ≤ w n) : {limtype('v', 'a')}",
    "exact tendsto_of_tendsto_of_tendsto_of_le_of_le hu hw hlo hhi",
)
card(
    "limit_fixed_shift",
    "u n a",
    [],
    logic("equivalent", lim(seq(sa(u, ca("nat_add", i, n))), a), lim(u, a)),
    "For any natural shift n, u(k+n) converges to a if and only if u(k) converges to a.",
    "Deleting a finite initial segment leaves a sequence limit unchanged.",
    [
        "Fix the finite shift n.",
        "Indices k+n eventually exceed any fixed natural bound.",
        "Conversely every sufficiently large index is of that form.",
        "Transfer the eventual conditions defining convergence in both directions.",
    ],
    f"example (u : ℕ → ℝ) (n : ℕ) (a : ℝ) : {limtype('(fun k => u (k+n))', 'a')} ↔ {limtype('u', 'a')}",
    "exact Filter.tendsto_add_atTop_iff_nat n",
)
card(
    "monotone_bounded_limit",
    "u b",
    [qnat("n m", Imp(le(n, m), le(sa(u, n), sa(u, m)))), qnat("i", le(ui, b))],
    exists("a", lim(u, a)),
    "Every nondecreasing real sequence with a real upper bound converges to some real limit.",
    "Use completeness of ℝ: a monotone bounded sequence tends to its supremum.",
    [
        "Use the stated order-preserving property of u.",
        "The common upper bound makes its range bounded above.",
        "Take the supremum of the range.",
        "Monotone convergence gives convergence to that real supremum.",
    ],
    f"example (u : ℕ → ℝ) (b : ℝ) (hm : ∀ n m : ℕ, n ≤ m → u n ≤ u m) (hb : ∀ n, u n ≤ b) : ∃ a : ℝ, {limtype('u', 'a')}",
    "exact ⟨⨆ n, u n, tendsto_atTop_ciSup (fun _ _ h => hm _ _ h) ⟨b, fun _ ⟨n, hn⟩ => hn ▸ hb n⟩⟩",
)
card(
    "geometric_limit",
    "q",
    [lt(ar("abs", q), o)],
    lim(seq(pow(q, i)), z),
    "For every real q with |q|<1, the sequence q^n converges to zero.",
    "Apply the geometric-power limit using the absolute ratio bound.",
    [
        "Fix a real ratio q.",
        "Use the strict bound |q|<1.",
        "The magnitudes |q|^n tend to zero.",
        "The geometric-limit theorem gives q^n→0, including negative ratios.",
    ],
    f"example (q : ℝ) (hq : |q| < 1) : {limtype('(fun n : ℕ => q^n)', '0')}",
    "exact tendsto_pow_atTop_nhds_zero_of_abs_lt_one hq",
)
card(
    "reciprocal_natural_limit",
    "a",
    [],
    lim(seq(div(a, castn(i))), z),
    "For every real constant a, the sequence a/n converges to zero as natural n tends to infinity; the totalized n=0 term does not affect the limit.",
    "Use divergence of natural denominators and continuity of scaling.",
    [
        "Fix any real numerator a.",
        "Natural denominators grow without bound.",
        "Their reciprocals tend to zero.",
        "Multiply by a; the finite initial zero-index convention is irrelevant.",
    ],
    f"example (a : ℝ) : {limtype('(fun n : ℕ => a / (n : ℝ))', '0')}",
    "exact tendsto_const_div_atTop_nhds_zero_nat a",
)

card(
    "has_sum_unique",
    "u a b",
    [hs(u, a), hs(u, b)],
    eq(a, b),
    "An unconditionally summable real series has a unique sum.",
    "Use uniqueness of the limit of its finite-subset sums.",
    [
        "Fix one series u.",
        "Assume unconditional sums a and b.",
        "Both are limits of the same net of finite-subset sums.",
        "Uniqueness of real limits yields a=b.",
    ],
    "example (u : ℕ → ℝ) (a b : ℝ) (ha : HasSum u a) (hb : HasSum u b) : a = b",
    "exact ha.unique hb",
)
card(
    "has_sum_add",
    "u v a b",
    [hs(u, a), hs(v, b)],
    hs(seq(add(ui, vi)), add(a, b)),
    "If real series u,v have unconditional sums a,b, then u+v has unconditional sum a+b.",
    "Add the convergent nets of finite-subset sums.",
    [
        "Use unconditional summability of both series.",
        "Add their sums on each finite subset.",
        "Pass finite additivity through the limit.",
        "The termwise sum has sum a+b.",
    ],
    "example (u v : ℕ → ℝ) (a b : ℝ) (hu : HasSum u a) (hv : HasSum v b) : HasSum (fun n => u n + v n) (a+b)",
    "exact hu.add hv",
)
card(
    "has_sum_scalar",
    "u a b",
    [hs(u, a)],
    hs(seq(mul(b, ui)), mul(b, a)),
    "Multiplying an unconditionally convergent real series of sum a by any real constant b gives sum b*a.",
    "Use continuity of constant scalar multiplication on finite sums.",
    [
        "Fix the convergent series and scalar b.",
        "Pull b out of each finite subset sum.",
        "Multiplication by b is continuous.",
        "The resulting series has sum b*a, including b=0.",
    ],
    "example (u : ℕ → ℝ) (a b : ℝ) (hu : HasSum u a) : HasSum (fun n => b * u n) (b*a)",
    "exact hu.mul_left b",
)
card(
    "absolute_comparison",
    "u v",
    [summ(v), qnat("i", le(ar("abs", ui), vi))],
    summ(u),
    "If a real series v is unconditionally summable and |u(n)|≤v(n) for every n, then u is unconditionally summable.",
    "Apply norm domination in the complete normed real line.",
    [
        "Use the summable majorant v.",
        "The pointwise absolute bound controls the norm of u.",
        "Real numbers form a complete normed space.",
        "Norm comparison proves summability of u.",
    ],
    "example (u v : ℕ → ℝ) (hv : Summable v) (hb : ∀ n, |u n| ≤ v n) : Summable u",
    "exact hv.of_norm_bounded (by simpa only [Real.norm_eq_abs] using hb)",
)
card(
    "absolute_convergence",
    "u",
    [summ(seq(ar("abs", ui)))],
    summ(u),
    "If the series of absolute values |u(n)| is summable, then the real series u is unconditionally summable.",
    "Identify real absolute values with norms and apply norm summability.",
    [
        "Assume summability of the nonnegative absolute-value series.",
        "Real absolute value equals the real norm.",
        "Apply the complete normed-space absolute-convergence criterion.",
        "Conclude unconditional summability of u.",
    ],
    "example (u : ℕ → ℝ) (hu : Summable (fun n => |u n|)) : Summable u",
    "exact Summable.of_norm (by simpa only [Real.norm_eq_abs] using hu)",
)
card(
    "summable_terms_zero",
    "u",
    [summ(u)],
    lim(u, z),
    "The terms of an unconditionally summable real series converge to zero.",
    "Apply the necessary term test for summability.",
    [
        "Fix a summable real series.",
        "Its finite-sum net is Cauchy.",
        "Individual terms outside a sufficiently large finite set are small.",
        "This gives convergence of the natural-indexed terms to zero.",
    ],
    f"example (u : ℕ → ℝ) (hu : Summable u) : {limtype('u', '0')}",
    "exact hu.tendsto_atTop_zero",
)
card(
    "partial_sums_limit",
    "u a",
    [hs(u, a)],
    lim(seq(ps(u, i)), a),
    "If u has unconditional sum a, then the partial sums over indices 0 through n-1 converge to a.",
    "Restrict the finite-subset sum limit to the cofinal increasing initial intervals.",
    [
        "Assume the finite-subset sums converge to a.",
        "Use the finite initial sets range n.",
        "These exhaust the natural indices cofinally.",
        "Their sums therefore converge to the same a.",
    ],
    f"example (u : ℕ → ℝ) (a : ℝ) (hu : HasSum u a) : {limtype('(fun n : ℕ => ∑ i ∈ Finset.range n, u i)', 'a')}",
    "exact hu.tendsto_sum_nat",
)
card(
    "summable_tail_iff",
    "u n",
    [],
    logic("equivalent", summ(seq(sa(u, ca("nat_add", i, n)))), summ(u)),
    "Deleting any finite initial segment of a real series preserves and reflects unconditional summability.",
    "A finite prefix is always summable, so convergence depends only on the tail.",
    [
        "Fix a natural cutoff n.",
        "Split the index set into the finite prefix and its tail.",
        "Finite sums create no convergence obstruction.",
        "Recover equivalence of whole-series and tail summability.",
    ],
    "example (u : ℕ → ℝ) (n : ℕ) : Summable (fun k => u (k+n)) ↔ Summable u",
    "exact summable_nat_add_iff n",
)
card(
    "geometric_sum",
    "q",
    [lt(ar("abs", q), o)],
    hs(seq(pow(q, i)), div(o, sub(o, q))),
    "For every real ratio |q|<1, the geometric series starting with q^0 has unconditional sum 1/(1-q).",
    "Use the geometric-series theorem with the strict absolute ratio condition.",
    [
        "Fix q satisfying |q|<1.",
        "Finite geometric sums have an explicit remainder q^n.",
        "That remainder tends to zero.",
        "The resulting sum is 1/(1-q), including negative q.",
    ],
    "example (q : ℝ) (hq : |q| < 1) : HasSum (fun n : ℕ => q^n) (1/(1-q))",
    "simpa only [one_div] using hasSum_geometric_of_abs_lt_one hq",
)
card(
    "exponential_power_series",
    "a",
    [],
    hs(seq(div(pow(a, i), castn(fact(i)))), ca("exp", a)),
    "For every real a, the power series Σ a^n/n! has unconditional sum exp(a).",
    "Apply the exponential-series expansion valid on the entire real line.",
    [
        "Fix an arbitrary real argument a.",
        "Use factorial denominators with 0!=1.",
        "The exponential series converges absolutely at every real argument.",
        "Identify its sum with Real.exp a.",
    ],
    "example (a : ℝ) : HasSum (fun n : ℕ => a^n / (n.factorial : ℝ)) (Real.exp a)",
    "simpa only [Real.exp_eq_exp_ℝ] using NormedSpace.expSeries_div_hasSum_exp a",
)
card(
    "p_series_criterion",
    "p",
    [],
    logic("equivalent", summ(seq(div(o, ca("rpow", castn(i), p)))), lt(o, p)),
    "For real p, the series Σ 1/n^p over natural n is summable exactly when p>1, using mathlib real exponentiation and its totalized zero-index term.",
    "Apply the real p-series convergence criterion, whose finite initial convention does not change convergence.",
    [
        "Fix an arbitrary real exponent p.",
        "Interpret exponentiation as Real.rpow rather than natural powers.",
        "The p-series comparison test has threshold p=1.",
        "Conclude the exact equivalence, unaffected by the single n=0 term.",
    ],
    "example (p : ℝ) : Summable (fun n : ℕ => 1 / (n : ℝ)^p) ↔ 1 < p",
    "exact Real.summable_one_div_nat_rpow",
)
card(
    "nonnegative_bounded_partial_sums",
    "u b",
    [qnat("i", le(z, ui)), qnat("n", le(ps(u, n), b))],
    summ(u),
    "A nonnegative real series whose natural partial sums have a common real upper bound is unconditionally summable.",
    "Use monotone convergence of the nonnegative partial sums and completeness.",
    [
        "Nonnegative terms make partial sums nondecreasing.",
        "The assumed bound prevents divergence to positive infinity.",
        "Monotone bounded partial sums converge.",
        "For nonnegative terms this implies unconditional summability.",
    ],
    "example (u : ℕ → ℝ) (b : ℝ) (hn : ∀ n, 0 ≤ u n) (hb : ∀ n, ∑ i ∈ Finset.range n, u i ≤ b) : Summable u",
    "exact summable_of_sum_range_le hn hb",
)
card(
    "nonnegative_sum_upper_bound",
    "u b",
    [qnat("i", le(z, ui)), qnat("n", le(ps(u, n), b))],
    le(tsum(u), b),
    "If u has nonnegative terms and every natural partial sum is at most b, then its total sum is at most b.",
    "First infer summability from bounded nonnegative partial sums, then pass the bound to their limit.",
    [
        "Retain nonnegativity of every term.",
        "Use the common upper bound on all finite initial sums.",
        "These assumptions imply summability.",
        "Passing the upper bound to the sum yields tsum(u)≤b.",
    ],
    "example (u : ℕ → ℝ) (b : ℝ) (hn : ∀ n, 0 ≤ u n) (hb : ∀ n, ∑ i ∈ Finset.range n, u i ≤ b) : (∑' n, u n) ≤ b",
    "exact Real.tsum_le_of_sum_range_le hn hb",
)
card(
    "absolute_sum_bound",
    "u",
    [summ(seq(ar("abs", ui)))],
    le(ar("abs", tsum(u)), tsum(seq(ar("abs", ui)))),
    "For an absolutely summable real series, the absolute value of its sum is at most the sum of its absolute values.",
    "Pass the finite-sum triangle inequality to the absolutely convergent sum.",
    [
        "Use absolute summability to justify both limits.",
        "Apply the triangle inequality to every finite sum.",
        "Take the limit of the finite-subset sums.",
        "Identify real norms with absolute values.",
    ],
    "example (u : ℕ → ℝ) (hu : Summable (fun n => |u n|)) : |∑' n, u n| ≤ ∑' n, |u n|",
    "simpa only [Real.norm_eq_abs] using norm_tsum_le_tsum_norm (f := u) (by simpa only [Real.norm_eq_abs] using hu)",
)
card(
    "sum_split_prefix_tail",
    "u n",
    [summ(u)],
    eq(add(ps(u, n), tsum(seq(sa(u, ca("nat_add", i, n))))), tsum(u)),
    "For a summable real series and any natural n, its first n terms plus the sum of the tail beginning at n equal the whole sum.",
    "Split a summable series into a finite prefix and its complementary tail.",
    [
        "Fix a summable sequence and natural cutoff n.",
        "Use indices 0 through n-1 for the finite prefix.",
        "Reindex the remaining terms as u(k+n).",
        "Add the prefix and tail sums to recover the original sum.",
    ],
    "example (u : ℕ → ℝ) (n : ℕ) (hu : Summable u) : (∑ i ∈ Finset.range n, u i) + (∑' k, u (k+n)) = ∑' k, u k",
    "exact hu.sum_add_tsum_nat_add n",
)

# Taylor operators have explicit, fixed derivative-domain endpoints a,b.
# c is the expansion center, x the evaluation point; no hidden theorem-name symbols.
card(
    "taylor_finite_expansion",
    "f n a b c x",
    [],
    eq(
        taylor(n, f, a, b, c, x),
        ps(
            seq(mul(div(pow(sub(x, c), i), castn(fact(i))), at(iterd(i, f, a, b), c))),
            succ(n),
        ),
    ),
    "For every natural n, the degree-n Taylor polynomial of f with derivative domain uIcc(a,b), center c and evaluation x is Σ[k=0..n] (x-c)^k/k! times the k-th within-derivative of f at c.",
    "Expand the finite Taylor polynomial definition, retaining every coefficient and derivative-domain parameter.",
    [
        "Fix n, f, the derivative domain and expansion center.",
        "Use the definition of the Taylor polynomial as a finite sum.",
        "Evaluate each monomial at x.",
        "Keep the factorial coefficient and derivative of order k for each index from 0 through n.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : taylorWithinEval f n (Set.uIcc a b) c x = ∑ k ∈ Finset.range (n+1), ((x-c)^k / (k.factorial : ℝ)) * iteratedDerivWithin k f (Set.uIcc a b) c",
    "simpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using taylor_within_apply f n (Set.uIcc a b) c x",
)
card(
    "taylor_successor",
    "f n a b c x",
    [],
    eq(
        taylor(succ(n), f, a, b, c, x),
        add(
            taylor(n, f, a, b, c, x),
            mul(
                div(pow(sub(x, c), succ(n)), castn(fact(succ(n)))),
                at(iterd(succ(n), f, a, b), c),
            ),
        ),
    ),
    "Increasing the Taylor degree from n to n+1 adds exactly the (n+1)-st derivative coefficient times (x-c)^(n+1)/(n+1)!, for fixed derivative domain uIcc(a,b).",
    "Separate the last summand of the finite Taylor expansion.",
    [
        "Fix all domain and center parameters.",
        "Split the sum through degree n+1 into the sum through n and its last term.",
        "Rewrite the coefficient using (n+1)!=(n+1)n!.",
        "Obtain the exact successor recurrence.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : taylorWithinEval f (n+1) (Set.uIcc a b) c x = taylorWithinEval f n (Set.uIcc a b) c x + ((x-c)^(n+1) / ((n+1).factorial : ℝ)) * iteratedDerivWithin (n+1) f (Set.uIcc a b) c",
    "rw [taylorWithinEval_succ]\n  simp only [smul_eq_mul, Nat.factorial_succ, Nat.cast_mul, Nat.cast_add, Nat.cast_one]\n  ring",
)
card(
    "taylor_polynomial_derivative",
    "f n a b c x",
    [],
    D(
        bind("lambda", [("y", "Real")], taylor(succ(n), f, a, b, c, var("y"))),
        x,
        taylor(n, iterd(ni(1), f, a, b), a, b, c, x),
    ),
    "The derivative in x of the degree-(n+1) Taylor polynomial is the degree-n Taylor polynomial of derivWithin(f,uIcc(a,b)), using the same fixed domain and center.",
    "Differentiate the finite polynomial term by term and shift the derivative index.",
    [
        "Keep a,b,c fixed while varying the evaluation argument.",
        "Differentiate each monomial of the finite Taylor polynomial.",
        "Cancel the exponent against the factorial denominator.",
        "Recognize the Taylor polynomial built from the first within-derivative.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : HasDerivAt (fun y => taylorWithinEval f (n+1) (Set.uIcc a b) c y) (taylorWithinEval (iteratedDerivWithin 1 f (Set.uIcc a b)) n (Set.uIcc a b) c x) x",
    "simpa only [iteratedDerivWithin_one] using (hasDerivAt_taylorWithinEval_succ (x₀ := c) (x := x) (s := Set.uIcc a b) f n)",
)
card(
    "taylor_lagrange_remainder",
    "f n a b",
    [lt(a, b), cd(succ(n), f, a, b)],
    exists(
        "c",
        And(
            opened(c, a, b),
            eq(
                sub(at(f, b), taylor(n, f, a, b, a, b)),
                div(
                    mul(
                        at(ca("iterated_deriv", succ(n), f), c), pow(sub(b, a), succ(n))
                    ),
                    castn(fact(succ(n))),
                ),
            ),
        ),
    ),
    "If a<b and f is C^(n+1) on [a,b], there is c in (a,b) such that f(b)-Taylor_n(f,a)(b)=f^(n+1)(c)*(b-a)^(n+1)/(n+1)!, with within-derivative coefficients on [a,b].",
    "Apply Taylor’s theorem with the Lagrange remainder and an interior remainder point.",
    [
        "Fix a natural order n and distinct ordered endpoints.",
        "Retain C^(n+1) smoothness on the whole closed interval.",
        "Apply the Lagrange-remainder theorem.",
        "The remainder point lies strictly inside the interval.",
        "Use the ordinary iterated derivative at that interior point.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b : ℝ) (hab : a < b) (hf : ContDiffOn ℝ (n+1 : ℕ) f (Set.uIcc a b)) : ∃ c : ℝ, (a<c ∧ c<b) ∧ f b - taylorWithinEval f n (Set.uIcc a b) a b = iteratedDeriv (n+1) f c * (b-a)^(n+1) / ((n+1).factorial : ℝ)",
    "simpa only [Set.uIoo_of_lt hab, Set.mem_Ioo] using taylor_mean_remainder_lagrange_iteratedDeriv (ne_of_lt hab) hf",
)
card(
    "taylor_integral_remainder",
    "f n a b",
    [cd(succ(n), f, a, b)],
    eq(
        sub(at(f, b), taylor(n, f, a, b, a, b)),
        Int(
            lam(
                mul(
                    div(pow(sub(b, x), n), castn(fact(n))),
                    at(iterd(succ(n), f, a, b), x),
                )
            ),
            a,
            b,
        ),
    ),
    "If f is C^(n+1) on the unordered interval between a,b, its Taylor remainder of order n equals the oriented integral from a to b of (b-t)^n/n! times the (n+1)-st within-derivative on that interval.",
    "Use the integral form of Taylor’s theorem with the explicit within-derivative domain.",
    [
        "Fix n and arbitrary real endpoints.",
        "Use C^(n+1) smoothness on the unordered closed interval.",
        "Apply the integral Taylor-remainder formula.",
        "Retain the kernel (b-t)^n/n! and interval orientation.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a b : ℝ) (hf : ContDiffOn ℝ (n+1 : ℕ) f (Set.uIcc a b)) : f b - taylorWithinEval f n (Set.uIcc a b) a b = ∫ t : ℝ in a..b, ((b-t)^n / (n.factorial : ℝ)) * iteratedDerivWithin (n+1) f (Set.uIcc a b) t",
    "simpa only [smul_eq_mul] using taylor_integral_remainder hf",
)


def main():
    assert len(cards) >= 30
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
