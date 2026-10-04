"""Author typed-calculus-v2 and compile every exact witness before emitting JSON."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_calculus_v2 import (
    canonicalize_typed_calculus_v2_openmath_xml,
    validate_canonical_typed_calculus_v2_openmath_xml,
)

BASE = "urn:pals:openmath:typed-calculus:v2"
WORKSPACE = ROOT / "pals-agent/lean-workspace"
WITNESS = ROOT / "docs/calculus-v2-batch.lean"
OUTPUT = ROOT / "docs/calculus-v2-batch.json"


def sym(cd, name):
    return f'<OMS cdbase="{BASE if cd in ("typed2", "calculus2") else "http://www.openmath.org/cd"}" cd="{cd}" name="{name}"/>'


def var(n):
    return f'<OMV name="{n}"/>'


def app(head, *args):
    return "<OMA>" + head + "".join(args) + "</OMA>"


def ca(n, *a):
    return app(sym("calculus2", n), *a)


def ar(n, *a):
    return app(sym("arith1", n), *a)


def rel(n, *a):
    return app(sym("relation1", n), *a)


def logic(n, *a):
    return app(sym("logic1", n), *a)


def bind(kind, vs, body):
    ds = "".join(
        "<OMATTR><OMATP>"
        + sym("typed2", "type")
        + sym("calculus2" if t == "RealFunction" else "typed2", t)
        + "</OMATP>"
        + var(n)
        + "</OMATTR>"
        for n, t in vs
    )
    return (
        "<OMBIND>"
        + sym("calculus2" if kind == "lambda" else "typed2", kind)
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
            n,
            "RealFunction"
            if n in ["f", "g", "h", "k"]
            else "Nat"
            if n == "n"
            else "Real",
        )
        for n in variables.split()
    ]
    xml = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind("forall", vs, body)
        + "</OMOBJ>"
    )
    canon = canonicalize_typed_calculus_v2_openmath_xml(xml)
    validate_canonical_typed_calculus_v2_openmath_xml(canon)
    cards.append(
        {
            "id": "calculus_v2_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canon,
            "lean_target": target,
            "lean_witness": "by\n  " + proof,
        }
    )


f, g, h, k, a, b, c, d, u, n, x = map(
    var, ["f", "g", "h", "k", "a", "b", "c", "d", "u", "n", "x"]
)
fx, gx, hx, kx = at(f, x), at(g, x), at(h, x), at(k, x)
fa, fb, ga, gb = at(f, a), at(f, b), at(g, a), at(g, b)
z, o, two = ri(0), ri(1), ri(2)
pn = lam(pow(x, n))
nc = ca("of_nat", n)
pred = ca("nat_pred", n)
succ = ca("nat_succ", n)
volume = "(MeasureTheory.volume : MeasureTheory.Measure ℝ)"
C = lambda f: ca("continuous", f)
Cclosed = lambda f: ca("continuous_on_closed", f, a, b)
all_deriv = lambda f, g: forall("x", D(f, x, at(g, x)))
interior_deriv = lambda f, g: forall("x", Imp(opened(x, a, b), D(f, x, at(g, x))))

card(
    "natural_power_derivative",
    "n a",
    [],
    D(pn, a, mul(nc, pow(a, pred))),
    "For every natural n and real a, x ↦ x^n has derivative n*a^(n-1) at a; n-1 is truncated natural subtraction.",
    "Use the natural-power derivative theorem, including n=0 without a nonzero-point premise.",
    [
        "Fix an arbitrary natural exponent n and real evaluation point a.",
        "Use the derivative theorem for the n-th natural power.",
        "Interpret the coefficient as the natural-number cast into ℝ.",
        "Interpret n-1 as Nat.pred n, so the formula also covers n=0.",
    ],
    "example (n : ℕ) (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ n) ((n : ℝ) * a ^ (n - 1)) a",
    "exact hasDerivAt_pow n a",
)
card(
    "natural_power_continuous",
    "n",
    [],
    C(pn),
    "For every natural n, the function x ↦ x^n is continuous on ℝ.",
    "Apply closure of the continuous identity function under arbitrary natural powers.",
    [
        "Fix an arbitrary natural exponent.",
        "The real identity function is continuous.",
        "Take its n-th power using continuity of multiplication.",
        "Conclude global continuity, including the constant zeroth power.",
    ],
    "example (n : ℕ) : Continuous (fun x : ℝ => x ^ n)",
    "exact continuous_id.pow n",
)
card(
    "natural_power_integral",
    "n a b",
    [],
    And(
        Integrable(pn, a, b),
        eq(Int(pn, a, b), div(sub(pow(b, succ), pow(a, succ)), ca("of_nat", succ))),
    ),
    "For every natural n and real endpoints a,b, x^n is interval-integrable and its oriented integral equals (b^(n+1)-a^(n+1))/(n+1).",
    "Combine continuity of natural powers with the power antiderivative formula.",
    [
        "Fix n and arbitrary finite real endpoints.",
        "Continuity gives interval integrability.",
        "Use the antiderivative x^(n+1)/(n+1).",
        "The denominator n+1 is positive, including when n=0.",
        "Evaluate the antiderivative at b and a with the oriented convention.",
    ],
    f"example (n : ℕ) (a b : ℝ) : IntervalIntegrable (fun x : ℝ => x ^ n) {volume} a b ∧ (∫ x : ℝ in a..b, x ^ n) = (b ^ (n + 1) - a ^ (n + 1)) / ((n + 1 : ℕ) : ℝ)",
    "constructor\n  · exact (continuous_id.pow n).intervalIntegrable a b\n  · simpa only [Nat.cast_add, Nat.cast_one] using (integral_pow (a := a) (b := b) (n := n))",
)
card(
    "natural_power_chain",
    "f n a u",
    [D(f, a, u)],
    D(lam(pow(fx, n)), a, mul(mul(nc, pow(fa, pred)), u)),
    "If f has derivative u at a, then f^n has derivative n*f(a)^(n-1)*u at a for every natural n.",
    "Apply the natural-power chain rule at the actual image f(a).",
    [
        "Fix f, its derivative u at a, and an arbitrary natural n.",
        "Differentiate the outer natural-power map at f(a).",
        "Compose with the derivative of f at a.",
        "Multiply the outer slope by u; the formula includes n=0.",
    ],
    "example (f : ℝ → ℝ) (n : ℕ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => (f x)^n) ((n : ℝ) * (f a)^(n-1) * u) a",
    "exact hf.pow n",
)

trans = [
    ("exp", mul(ca("exp", fa), u), "Real.exp (f a) * u", [], "", "hf.exp"),
    (
        "log",
        div(u, fa),
        "u / f a",
        [rel("neq", fa, z)],
        " (hne : f a ≠ 0)",
        "hf.log hne",
    ),
    ("sin", mul(ca("cos", fa), u), "Real.cos (f a) * u", [], "", "hf.sin"),
    ("cos", mul(neg(ca("sin", fa)), u), "-Real.sin (f a) * u", [], "", "hf.cos"),
    (
        "sqrt",
        div(u, mul(two, ca("sqrt", fa))),
        "u / (2 * Real.sqrt (f a))",
        [lt(z, fa)],
        " (hpos : 0 < f a)",
        "hf.sqrt (ne_of_gt hpos)",
    ),
    (
        "arctan",
        mul(div(o, add(o, pow(fa, ni(2)))), u),
        "(1 / (1 + (f a)^2)) * u",
        [],
        "",
        "hf.arctan",
    ),
]
for name, slope, lslope, ps, extra, proof in trans:
    condition = {"log": " and f(a) ≠ 0", "sqrt": " and f(a)>0"}.get(name, "")
    card(
        name + "_chain",
        "f a u",
        [D(f, a, u)] + ps,
        D(lam(ca(name, fx)), a, slope),
        f"If f has derivative u at a{condition}, then {name}(f(x)) has derivative {lslope} at a."
        + (
            " Here log denotes Real.log (the real logarithm of absolute value)."
            if name == "log"
            else ""
        ),
        f"Compose the derivative of {name} at f(a) with the derivative of f.",
        [
            "Fix f and the given derivative u at a.",
            "Evaluate the outer function at the correct base point f(a).",
            "Check the explicit domain condition."
            if ps
            else "The outer derivative is defined at every real input.",
            f"Apply the {name} chain rule and retain the inner derivative factor u.",
        ],
        f"example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a){extra} : HasDerivAt (fun x => Real.{name} (f x)) ({lslope}) a",
        "exact " + proof,
    )

for name, result, lrhs in [
    ("exp", sub(ca("exp", b), ca("exp", a)), "Real.exp b - Real.exp a"),
    ("sin", sub(ca("cos", a), ca("cos", b)), "Real.cos a - Real.cos b"),
    ("cos", sub(ca("sin", b), ca("sin", a)), "Real.sin b - Real.sin a"),
]:
    func = lam(ca(name, x))
    card(
        name + "_integral",
        "a b",
        [],
        And(Integrable(func, a, b), eq(Int(func, a, b), result)),
        f"For arbitrary real endpoints a,b, {name} is interval-integrable and its oriented integral is {lrhs}.",
        "Establish integrability by global continuity, then evaluate a standard antiderivative.",
        [
            "Fix arbitrary finite real endpoints.",
            "Use global continuity of the integrand.",
            "Obtain interval integrability for real volume.",
            "Evaluate the antiderivative at the upper and lower endpoints.",
        ],
        f"example (a b : ℝ) : IntervalIntegrable Real.{name} {volume} a b ∧ (∫ x : ℝ in a..b, Real.{name} x) = {lrhs}",
        f"exact ⟨Real.continuous_{name}.intervalIntegrable a b, integral_{name}⟩",
    )

card(
    "reciprocal_integral_positive",
    "a b",
    [lt(z, a), lt(z, b)],
    And(
        Integrable(lam(div(o, x)), a, b),
        eq(Int(lam(div(o, x)), a, b), ca("log", div(b, a))),
    ),
    "For positive real endpoints a,b, 1/x is interval-integrable between them and its oriented integral is log(b/a).",
    "Exclude zero from the whole unordered interval and apply the reciprocal integral formula.",
    [
        "Fix positive endpoints a,b.",
        "Every point between them is strictly positive, so the reciprocal is continuous there.",
        "Deduce interval integrability from continuity on the unordered compact interval.",
        "Evaluate the logarithmic antiderivative to obtain log(b/a).",
    ],
    f"example (a b : ℝ) (ha : 0 < a) (hb : 0 < b) : IntervalIntegrable (fun x : ℝ => 1 / x) {volume} a b ∧ (∫ x : ℝ in a..b, 1 / x) = Real.log (b / a)",
    "constructor\n  · apply ContinuousOn.intervalIntegrable\n    apply continuousOn_const.div continuousOn_id\n    intro x hx\n    exact ne_of_gt (lt_of_lt_of_le (lt_min ha hb) hx.1)\n  · exact integral_one_div_of_pos ha hb",
)

card(
    "mean_value",
    "f g a b",
    [lt(a, b), Cclosed(f), interior_deriv(f, g)],
    exists("c", And(opened(c, a, b), eq(at(g, c), div(sub(fb, fa), sub(b, a))))),
    "If a<b, f is continuous on [a,b], and f has derivative g(x) at every interior x, some c in (a,b) satisfies g(c)=(f(b)-f(a))/(b-a).",
    "Apply Lagrange’s mean value theorem with the explicitly supplied derivative function.",
    [
        "Fix a nondegenerate closed interval.",
        "Use continuity up to both endpoints.",
        "Use the given two-sided derivative at each interior point.",
        "Apply the mean value theorem.",
        "Retain both strict bounds on c and its secant-slope equality.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x : ℝ, a < x ∧ x < b → HasDerivAt f (g x) x) : ∃ c : ℝ, (a < c ∧ c < b) ∧ g c = (f b - f a) / (b - a)",
    "exact exists_hasDerivAt_eq_slope f g hab hc (fun x hx => hd x hx)",
)
card(
    "rolle",
    "f g a b",
    [lt(a, b), Cclosed(f), eq(fa, fb), interior_deriv(f, g)],
    exists("c", And(opened(c, a, b), eq(at(g, c), z))),
    "If a<b, f is continuous on [a,b], f(a)=f(b), and g is its derivative throughout (a,b), then g(c)=0 at some c in (a,b).",
    "Apply Rolle’s theorem with explicit derivative evidence rather than a total derivative operator.",
    [
        "Fix a<b and continuity on the closed interval.",
        "Check equality of the endpoint values.",
        "Use the supplied derivative function on the interior.",
        "Apply Rolle’s theorem to obtain an interior zero of that derivative.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (heq : f a = f b) (hd : ∀ x : ℝ, a < x ∧ x < b → HasDerivAt f (g x) x) : ∃ c : ℝ, (a < c ∧ c < b) ∧ g c = 0",
    "exact exists_hasDerivAt_eq_zero hab hc heq (fun x hx => hd x hx)",
)
card(
    "fundamental_theorem_antiderivative",
    "f g a b",
    [all_deriv(f, g), Integrable(g, a, b)],
    eq(Int(g, a, b), sub(fb, fa)),
    "If f has derivative g(x) at every real x and g is interval-integrable from a to b, then the integral of g is f(b)-f(a).",
    "Restrict the supplied derivative to the unordered interval and apply the fundamental theorem of calculus.",
    [
        "Fix an antiderivative f of g on ℝ.",
        "Restrict the derivative evidence to points between a and b.",
        "Use the explicit interval-integrability hypothesis for g.",
        "Apply the fundamental theorem to compute the boundary difference.",
    ],
    f"example (f g : ℝ → ℝ) (a b : ℝ) (hd : ∀ x : ℝ, HasDerivAt f (g x) x) (hi : IntervalIntegrable g {volume} a b) : (∫ x : ℝ in a..b, g x) = f b - f a",
    "exact intervalIntegral.integral_eq_sub_of_hasDerivAt (fun x _ => hd x) hi",
)
card(
    "fundamental_theorem_variable_upper",
    "f a b",
    [C(f)],
    D(lam(Int(f, a, x)), b, fb),
    "For continuous f on ℝ and any a,b, the function x ↦ integral from a to x of f has derivative f(b) at b.",
    "Use continuity to obtain local integrability and differentiate the variable upper endpoint.",
    [
        "Fix the lower endpoint a and evaluation point b.",
        "Global continuity ensures integrability on every finite interval.",
        "Continuity at b controls the local integral increment.",
        "Apply the first fundamental theorem to obtain derivative f(b).",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hc : Continuous f) : HasDerivAt (fun x : ℝ => ∫ t : ℝ in a..x, f t) (f b) b",
    "exact (hc.integral_hasStrictDerivAt a b).hasDerivAt",
)
card(
    "integration_by_parts",
    "f g h k a b",
    [all_deriv(f, h), all_deriv(g, k), Integrable(h, a, b), Integrable(k, a, b)],
    eq(
        Int(lam(mul(fx, kx)), a, b),
        sub(sub(mul(fb, gb), mul(fa, ga)), Int(lam(mul(hx, gx)), a, b)),
    ),
    "If f and g have derivatives h and k everywhere and h,k are interval-integrable from a to b, then ∫ f*k = f(b)g(b)-f(a)g(a)-∫ h*g.",
    "Integrate the product derivative and rearrange the two integrable product terms.",
    [
        "Use derivative evidence to obtain continuity of f and g.",
        "Restrict continuity to the unordered compact interval.",
        "Use integrability of h and k together with the continuous factors.",
        "Apply integration by parts on the interval.",
        "Move the integral of h*g to the other side of the boundary identity.",
    ],
    f"example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ∀ x : ℝ, HasDerivAt f (h x) x) (hg : ∀ x : ℝ, HasDerivAt g (k x) x) (hi : IntervalIntegrable h {volume} a b) (hj : IntervalIntegrable k {volume} a b) : (∫ x : ℝ in a..b, f x * k x) = f b * g b - f a * g a - (∫ x : ℝ in a..b, h x * g x)",
    "have cf : Continuous f := continuous_iff_continuousAt.mpr (fun x => (hf x).continuousAt)\n  have cg : Continuous g := continuous_iff_continuousAt.mpr (fun x => (hg x).continuousAt)\n  exact intervalIntegral.integral_mul_deriv_eq_deriv_mul_of_hasDerivAt cf.continuousOn cg.continuousOn (fun x _ => hf x) (fun x _ => hg x) hi hj",
)
card(
    "integration_substitution",
    "f g h a b",
    [all_deriv(f, h), C(h), C(g)],
    eq(Int(lam(mul(at(g, fx), hx)), a, b), Int(g, fa, fb)),
    "If f has continuous derivative h on ℝ and g is continuous on ℝ, then ∫[a,b] g(f(x))*h(x) = ∫[f(a),f(b)] g; f need not be monotone.",
    "Use the change-of-variables theorem for oriented one-dimensional integrals.",
    [
        "Fix f with its explicit continuous derivative h.",
        "Restrict the derivative and its continuity to the unordered interval.",
        "Use continuity of the outer integrand g.",
        "Apply substitution with the transformed endpoints f(a),f(b).",
        "Preserve orientation, so no monotonicity hypothesis is introduced.",
    ],
    "example (f g h : ℝ → ℝ) (a b : ℝ) (hd : ∀ x : ℝ, HasDerivAt f (h x) x) (ch : Continuous h) (cg : Continuous g) : (∫ x : ℝ in a..b, g (f x) * h x) = (∫ y : ℝ in f a..f b, g y)",
    "exact intervalIntegral.integral_comp_mul_deriv (fun x _ => hd x) ch.continuousOn cg",
)
card(
    "integral_additivity",
    "f g a b",
    [Integrable(f, a, b), Integrable(g, a, b)],
    eq(Int(lam(add(fx, gx)), a, b), add(Int(f, a, b), Int(g, a, b))),
    "For two interval-integrable real functions on the same endpoints, the integral of their sum equals the sum of their integrals.",
    "Apply linearity of the Bochner interval integral after checking both integrability hypotheses.",
    [
        "Fix the endpoints and both integrands.",
        "Use integrability of the first function.",
        "Use integrability of the second function.",
        "Apply interval-integral addition; no order on the endpoints is needed.",
    ],
    f"example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f {volume} a b) (hg : IntervalIntegrable g {volume} a b) : (∫ x : ℝ in a..b, f x + g x) = (∫ x : ℝ in a..b, f x) + (∫ x : ℝ in a..b, g x)",
    "exact intervalIntegral.integral_add hf hg",
)
card(
    "integral_scalar_linearity",
    "f a b c",
    [Integrable(f, a, b)],
    And(
        Integrable(lam(mul(c, fx)), a, b),
        eq(Int(lam(mul(c, fx)), a, b), mul(c, Int(f, a, b))),
    ),
    "If f is interval-integrable, multiplying it by any real constant c preserves integrability and multiplies its integral by c.",
    "Use closure of interval integrability under constant multiplication and integral linearity.",
    [
        "Fix an arbitrary real constant c.",
        "Use interval integrability of f.",
        "Deduce interval integrability of c*f.",
        "Pull c through the interval integral.",
    ],
    f"example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f {volume} a b) : IntervalIntegrable (fun x => c * f x) {volume} a b ∧ (∫ x : ℝ in a..b, c * f x) = c * (∫ x : ℝ in a..b, f x)",
    "exact ⟨hf.const_mul c, intervalIntegral.integral_const_mul c f⟩",
)
card(
    "integral_join_intervals",
    "f a b c",
    [Integrable(f, a, b), Integrable(f, b, c)],
    eq(add(Int(f, a, b), Int(f, b, c)), Int(f, a, c)),
    "If f is interval-integrable between a,b and between b,c, the sum of these oriented integrals is its integral between a,c, with no endpoint order required.",
    "Apply oriented additivity across a common endpoint.",
    [
        "Fix three arbitrary real endpoints.",
        "Use integrability on the first interval.",
        "Use integrability on the second interval.",
        "Cancel the shared endpoint in the oriented interval-integral identity.",
    ],
    f"example (f : ℝ → ℝ) (a b c : ℝ) (hab : IntervalIntegrable f {volume} a b) (hbc : IntervalIntegrable f {volume} b c) : (∫ x : ℝ in a..b, f x) + (∫ x : ℝ in b..c, f x) = (∫ x : ℝ in a..c, f x)",
    "exact intervalIntegral.integral_add_adjacent_intervals hab hbc",
)
card(
    "integral_order",
    "f g a b",
    [
        le(a, b),
        Integrable(f, a, b),
        Integrable(g, a, b),
        forall("x", Imp(closed(x, a, b), le(fx, gx))),
    ],
    le(Int(f, a, b), Int(g, a, b)),
    "If a≤b, f and g are interval-integrable and f(x)≤g(x) on [a,b], then the integral of f is at most the integral of g.",
    "Use positivity of integration on an interval with the forward orientation.",
    [
        "Check a≤b; reversing orientation would reverse the inequality.",
        "Use both interval-integrability hypotheses.",
        "Restrict the pointwise order to the closed interval.",
        "Apply monotonicity of the interval integral.",
    ],
    f"example (f g : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hf : IntervalIntegrable f {volume} a b) (hg : IntervalIntegrable g {volume} a b) (hle : ∀ x : ℝ, a ≤ x ∧ x ≤ b → f x ≤ g x) : (∫ x : ℝ in a..b, f x) ≤ (∫ x : ℝ in a..b, g x)",
    "exact intervalIntegral.integral_mono_on hab hf hg (fun x hx => hle x hx)",
)
card(
    "nonnegative_derivative_monotone",
    "f g",
    [all_deriv(f, g), forall("x", le(z, gx))],
    forall("a b", Imp(le(a, b), le(fa, fb))),
    "If f has derivative g(x) at every real x and g(x)≥0 everywhere, then a≤b implies f(a)≤f(b).",
    "Use the mean-value consequence that a globally nonnegative derivative gives monotonicity.",
    [
        "Fix a globally differentiable f with derivative g.",
        "Check nonnegativity of g at every point.",
        "Apply the derivative criterion for monotonicity.",
        "Evaluate the resulting order-preserving property at arbitrary a≤b.",
    ],
    "example (f g : ℝ → ℝ) (hd : ∀ x : ℝ, HasDerivAt f (g x) x) (hn : ∀ x : ℝ, 0 ≤ g x) : ∀ a b : ℝ, a ≤ b → f a ≤ f b",
    "exact fun a b hab => monotone_of_hasDerivAt_nonneg hd hn hab",
)
card(
    "zero_derivative_constant",
    "f",
    [forall("x", D(f, x, z))],
    forall("a b", eq(fa, fb)),
    "A real function with derivative zero at every real point is constant: f(a)=f(b) for all real a,b.",
    "Apply the zero-derivative criterion on the connected real line.",
    [
        "Assume the derivative is zero at every point.",
        "This supplies differentiability everywhere.",
        "The real line is connected, so the mean value theorem forces equal values.",
        "Conclude equality at arbitrary a,b.",
    ],
    "example (f : ℝ → ℝ) (hd : ∀ x : ℝ, HasDerivAt f 0 x) : ∀ a b : ℝ, f a = f b",
    "exact is_const_of_deriv_eq_zero (fun x => (hd x).differentiableAt) (fun x => (hd x).deriv)",
)
card(
    "intermediate_value",
    "f a b u",
    [le(a, b), Cclosed(f), le(fa, u), le(u, fb)],
    exists("c", And(closed(c, a, b), eq(at(f, c), u))),
    "If a≤b and f is continuous on [a,b], every u with f(a)≤u≤f(b) equals f(c) for some c in [a,b].",
    "Use the intermediate value theorem on the connected closed interval.",
    [
        "Fix ordered endpoints and continuity on the closed interval.",
        "Check that the target u lies between the endpoint values.",
        "Apply the intermediate value theorem.",
        "Keep the witness c with both interval membership and f(c)=u.",
    ],
    "example (f : ℝ → ℝ) (a b u : ℝ) (hab : a ≤ b) (hc : ContinuousOn f (Set.Icc a b)) (ha : f a ≤ u) (hb : u ≤ f b) : ∃ c : ℝ, (a ≤ c ∧ c ≤ b) ∧ f c = u",
    "exact intermediate_value_Icc hab hc ⟨ha, hb⟩",
)
card(
    "extreme_value_minimum",
    "f a b",
    [le(a, b), Cclosed(f)],
    exists(
        "c", And(closed(c, a, b), forall("x", Imp(closed(x, a, b), le(at(f, c), fx))))
    ),
    "A real function continuous on a nonempty closed bounded interval [a,b] attains a minimum there.",
    "Apply compactness of a closed bounded interval to the continuous function.",
    [
        "Use a≤b to ensure the closed interval is nonempty.",
        "Use compactness of the interval.",
        "Restrict f to the compact interval using the given continuity.",
        "Apply the extreme value theorem and retain the minimizing point and inequality.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hc : ContinuousOn f (Set.Icc a b)) : ∃ c : ℝ, (a ≤ c ∧ c ≤ b) ∧ ∀ x : ℝ, a ≤ x ∧ x ≤ b → f c ≤ f x",
    "exact isCompact_Icc.exists_isMinOn ⟨a, le_rfl, hab⟩ hc",
)


def main():
    assert len(cards) >= 25
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
            ROOT / "pals-agent/pals_agent/typed_calculus_v2.py"
        ),
        "registry_sha256": hashfile(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-calculus-v2-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": next(p["rev"] for p in packages if p["name"] == "mathlib"),
    }
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": "typed-calculus-v2",
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
