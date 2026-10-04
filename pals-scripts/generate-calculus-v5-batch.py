"""Author typed-calculus-v5 and compile every exact witness before emitting JSON."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_calculus_v5 import (
    canonicalize_typed_calculus_v5_openmath_xml,
    validate_canonical_typed_calculus_v5_openmath_xml,
)

BASE = "urn:pals:openmath:typed-calculus:v5"
WORKSPACE = ROOT / "pals-agent/lean-workspace"
WITNESS = ROOT / "docs/calculus-v5-batch.lean"
OUTPUT = ROOT / "docs/calculus-v5-batch.json"


def sym(cd, name):
    return f'<OMS cdbase="{BASE if cd in ("typed5", "calculus5") else "http://www.openmath.org/cd"}" cd="{cd}" name="{name}"/>'


def var(n):
    return f'<OMV name="{n}"/>'


def app(head, *args):
    return "<OMA>" + head + "".join(args) + "</OMA>"


def ca(n, *a):
    return app(sym("calculus5", n), *a)


def ar(n, *a):
    return app(sym("arith1", n), *a)


def rel(n, *a):
    return app(sym("relation1", n), *a)


def logic(n, *a):
    return app(sym("logic1", n), *a)


def bind(kind, vs, body):
    ds = "".join(
        "<OMATTR><OMATP>"
        + sym("typed5", "type")
        + sym("calculus5" if t == "RealFunction" else "typed5", t)
        + "</OMATP>"
        + var(n)
        + "</OMATTR>"
        for n, t in vs
    )
    return (
        "<OMBIND>"
        + sym("calculus5" if kind == "lambda" else "typed5", kind)
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
    canon = canonicalize_typed_calculus_v5_openmath_xml(xml)
    validate_canonical_typed_calculus_v5_openmath_xml(canon)
    cards.append(
        {
            "id": "calculus_v5_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canon,
            "lean_target": target,
            "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
        }
    )


f, g, h, k, a, b, c, d, u, v, n, x, y = map(
    var, ["f", "g", "h", "k", "a", "b", "c", "d", "u", "v", "n", "x", "y"]
)
z, o, two = ri(0), ri(1), ri(2)
fx, gx, hx, kx = at(f, x), at(g, x), at(h, x), at(k, x)
fa, fb, ga, gb = at(f, a), at(f, b), at(g, a), at(g, b)
C = lambda f: ca("continuous", f)
Cu = lambda f, a, b: ca("continuous_on_unordered", f, a, b)
Cc = lambda f, a, b: ca("continuous_on_closed", f, a, b)
der = lambda f: ca("deriv", f)
absx = lambda t: ar("abs", t)
unord = lambda x, a, b: closed(x, ca("min", a, b), ca("max", a, b))
allD = lambda f, g: forall("x", D(f, x, at(g, x)))
Dopen = lambda f, g, a, b: forall("x", Imp(opened(x, a, b), D(f, x, at(g, x))))
Dclosed = lambda f, g, a, b: forall("x", Imp(closed(x, a, b), D(f, x, at(g, x))))
Du = lambda f, g, a, b: forall("x", Imp(unord(x, a, b), D(f, x, at(g, x))))
volume = "MeasureTheory.volume"


def emit(key, vs, ps, q, statement, steps, target, proof):
    card(key, vs, ps, q, statement, steps[0], steps, target, proof)


emit(
    "integral_absolute_bound",
    "f a b",
    [le(a, b), Integrable(f, a, b)],
    le(absx(Int(f, a, b)), Int(lam(absx(fx)), a, b)),
    "For a≤b and interval-integrable f, |∫[a,b] f|≤∫[a,b]|f|.",
    [
        "Use the triangle inequality for the Bochner integral.",
        "The endpoint order fixes positive orientation.",
        "Identify the real norm with absolute value.",
        "The absolute-value integrand is integrable by the original premise.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hf : IntervalIntegrable f MeasureTheory.volume a b) : |∫ x in a..b, f x| ≤ ∫ x in a..b, |f x|",
    "exact intervalIntegral.abs_integral_le_integral_abs hab",
)
emit(
    "integral_uniform_bound",
    "f a b c",
    [Integrable(f, a, b), forall("x", Imp(unord(x, a, b), le(absx(fx), c)))],
    le(absx(Int(f, a, b)), mul(c, absx(sub(b, a)))),
    "If f is interval-integrable and |f(x)|≤c throughout the unordered interval between a,b, then |∫[a,b]f|≤c|b-a|.",
    [
        "Restrict the pointwise bound to the integration interval.",
        "The integral norm is bounded by the integral of the constant bound.",
        "Its measure is the absolute interval length.",
        "Retain absolute value for either endpoint orientation.",
    ],
    "example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hb : ∀ x ∈ Set.uIcc a b, |f x| ≤ c) : |∫ x in a..b, f x| ≤ c*|b-a|",
    "simpa only [Real.norm_eq_abs] using (intervalIntegral.norm_integral_le_of_norm_le_const (f := f) (a := a) (b := b) (C := c) (fun x hx => by simpa only [Real.norm_eq_abs] using hb x (Set.uIoc_subset_uIcc hx)))",
)
emit(
    "integral_strict_positive",
    "f a b",
    [
        lt(a, b),
        Cc(f, a, b),
        forall("x", Imp(closed(x, a, b), le(z, fx))),
        exists("c", And(closed(c, a, b), lt(z, at(f, c)))),
    ],
    lt(z, Int(f, a, b)),
    "For a<b, a continuous nonnegative function on [a,b] that is positive at some point of [a,b] has strictly positive integral.",
    [
        "Use continuity to spread strict positivity from the chosen point.",
        "The strict endpoint order gives a nontrivial interval.",
        "Nonnegativity prevents cancellation elsewhere.",
        "Apply strict positivity of the integral.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hn : ∀ x ∈ Set.Icc a b, 0 ≤ f x) (hp : ∃ c ∈ Set.Icc a b, 0 < f c) : 0 < ∫ x in a..b, f x",
    "exact intervalIntegral.integral_pos hab hc (fun x hx => hn x ⟨le_of_lt hx.1,hx.2⟩) hp",
)
emit(
    "zero_integral_continuous_nonnegative",
    "f a b",
    [lt(a, b), Cc(f, a, b), forall("x", Imp(closed(x, a, b), le(z, fx)))],
    logic(
        "equivalent", eq(Int(f, a, b), z), forall("x", Imp(closed(x, a, b), eq(fx, z)))
    ),
    "On a nondegenerate closed interval, a continuous nonnegative f has integral zero exactly when it vanishes at every point of that interval.",
    [
        "If f vanishes, integral congruence gives zero.",
        "Conversely, a nonzero nonnegative value would be strictly positive.",
        "Continuity and positivity at that point force a positive integral.",
        "This contradicts a zero integral, proving pointwise vanishing.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hn : ∀ x ∈ Set.Icc a b, 0 ≤ f x) : (∫ x in a..b, f x)=0 ↔ ∀ x ∈ Set.Icc a b, f x=0",
    "constructor\n· intro hi x hx\n  by_contra h\n  have hp := intervalIntegral.integral_pos hab hc (fun y hy => hn y ⟨le_of_lt hy.1,hy.2⟩) ⟨x,hx,lt_of_le_of_ne (hn x hx) (Ne.symm h)⟩\n  linarith\n· intro hz\n  calc\n    (∫ x in a..b, f x) = ∫ x in a..b, (0 : ℝ) := intervalIntegral.integral_congr (by intro x hx; exact hz x (by simpa only [Set.uIcc_of_le hab.le] using hx))\n    _ = 0 := by simp",
)
emit(
    "weighted_integral_mean_value",
    "f g a b",
    [Cu(f, a, b), Integrable(g, a, b), forall("x", Imp(unord(x, a, b), le(z, gx)))],
    exists(
        "c",
        And(
            unord(c, a, b), eq(Int(lam(mul(fx, gx)), a, b), mul(at(f, c), Int(g, a, b)))
        ),
    ),
    "For continuous f on uIcc(a,b) and nonnegative interval-integrable weight g there, some c in uIcc(a,b) satisfies ∫f*g=f(c)∫g, for either interval orientation.",
    [
        "Continuity bounds f between its interval extrema.",
        "Nonnegative weights preserve the corresponding integral inequalities.",
        "The intermediate value property supplies the weighted average value.",
        "The result also includes zero total weight and equal endpoints.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.uIcc a b)) (hg : IntervalIntegrable g MeasureTheory.volume a b) (hn : ∀ x ∈ Set.uIcc a b, 0 ≤ g x) : ∃ c ∈ Set.uIcc a b, (∫ x in a..b, f x*g x)=f c*(∫ x in a..b, g x)",
    "exact exists_eq_const_mul_intervalIntegral_of_nonneg hf hg (fun x hx => hn x (Set.uIoc_subset_uIcc hx))",
)
emit(
    "odd_symmetric_integral",
    "f a",
    [forall("x", eq(at(f, neg(x)), neg(fx)))],
    eq(Int(f, neg(a), a), z),
    "Every odd real function has total oriented interval integral zero over [-a,a] for every real a; this value identity alone does not assert integrability.",
    [
        "Substitute x↦-x in the symmetric interval integral.",
        "Oddness identifies the transformed integrand with -f.",
        "Integral linearity under negation makes the value its own negative.",
        "Over ℝ this forces the value to be zero.",
    ],
    "example (f : ℝ → ℝ) (a : ℝ) (hf : ∀ x, f (-x) = -f x) : (∫ x in (-a)..a, f x)=0",
    "have h := intervalIntegral.integral_comp_neg (a := -a) (b := a) f\nsimp only [neg_neg, hf, intervalIntegral.integral_neg] at h\nlinarith",
)
emit(
    "even_symmetric_integral",
    "f a",
    [C(f), forall("x", eq(at(f, neg(x)), fx))],
    eq(Int(f, neg(a), a), mul(two, Int(f, z, a))),
    "For continuous even f and every real a, the oriented integral from -a to a is twice the integral from 0 to a.",
    [
        "Reflect the interval from -a to zero to the interval from zero to a.",
        "Evenness leaves the integrand unchanged.",
        "Continuity supplies integrability for joining the adjacent intervals.",
        "The two equal half-interval integrals add to twice one half.",
    ],
    "example (f : ℝ → ℝ) (a : ℝ) (hc : Continuous f) (hf : ∀ x, f (-x)=f x) : (∫ x in (-a)..a, f x)=2*(∫ x in (0:ℝ)..a, f x)",
    "have h : (∫ x in (-a)..(0:ℝ), f x) = ∫ x in (0:ℝ)..a, f x := by simpa only [hf, neg_zero, neg_neg] using (intervalIntegral.integral_comp_neg (a := -a) (b := 0) f)\nhave hj := intervalIntegral.integral_add_adjacent_intervals (μ := MeasureTheory.volume) (hc.intervalIntegrable (-a) 0) (hc.intervalIntegrable 0 a)\nlinarith",
)
emit(
    "period_integral_translation",
    "f a b c",
    [ca("periodic", f, c)],
    eq(Int(f, a, add(a, c)), Int(f, b, add(b, c))),
    "For a function with real period c, its total oriented integral over one period is independent of the starting point.",
    [
        "Translate an interval whose length is the period.",
        "Periodicity identifies corresponding function values.",
        "The integral over a complete period is translation invariant.",
        "This identity keeps its totalized meaning without inferring integrability.",
    ],
    "example (f : ℝ → ℝ) (a b c : ℝ) (hf : Function.Periodic f c) : (∫ x in a..a+c, f x)=(∫ x in b..b+c, f x)",
    "exact hf.intervalIntegral_add_eq a b",
)
emit(
    "affine_substitution_integrable",
    "f a b c d",
    [rel("neq", c, z), Integrable(f, add(mul(c, a), d), add(mul(c, b), d))],
    eq(
        Int(lam(at(f, add(mul(c, x), d))), a, b),
        mul(div(o, c), Int(f, add(mul(c, a), d), add(mul(c, b), d))),
    ),
    "For c≠0 and f interval-integrable between ca+d and cb+d, ∫[a,b]f(cx+d)=(1/c)∫[ca+d,cb+d]f; c may be negative.",
    [
        "Use the affine change of variables y=cx+d.",
        "The slope c is nonzero, so the coordinate change is invertible.",
        "The new endpoints retain orientation when c is negative.",
        "The reciprocal slope gives the factor 1/c without requiring continuity of f.",
    ],
    "example (f : ℝ → ℝ) (a b c d : ℝ) (hc : c ≠ 0) (hi : IntervalIntegrable f MeasureTheory.volume (c*a+d) (c*b+d)) : (∫ x in a..b, f (c*x+d))=(1/c)*(∫ x in c*a+d..c*b+d, f x)",
    "simpa only [one_div, smul_eq_mul] using intervalIntegral.integral_comp_mul_add (a := a) (b := b) f hc d",
)
emit(
    "absolute_integrability",
    "f a b",
    [Integrable(f, a, b)],
    Integrable(lam(absx(fx)), a, b),
    "Interval integrability of a real function implies interval integrability of its absolute value on the same endpoints.",
    [
        "Use the integrability premise on the unordered integration interval.",
        "Apply the norm-integrability theorem.",
        "For real values the norm is the absolute value.",
        "The endpoint orientation does not change integrability.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) : IntervalIntegrable (fun x => |f x|) MeasureTheory.volume a b",
    "exact hf.abs",
)
emit(
    "continuous_multiplier_integrability",
    "f g a b",
    [Integrable(f, a, b), Cu(g, a, b)],
    Integrable(lam(mul(fx, gx)), a, b),
    "An interval-integrable f multiplied by a function g continuous on uIcc(a,b) remains interval-integrable.",
    [
        "A continuous function on the compact interval is bounded there.",
        "Multiplying an integrable function by this bounded continuous factor preserves integrability.",
        "Apply the interval version of that product result.",
        "No differentiability or global continuity of g is needed.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hg : ContinuousOn g (Set.uIcc a b)) : IntervalIntegrable (fun x => f x*g x) MeasureTheory.volume a b",
    "exact hf.mul_continuousOn hg",
)
emit(
    "integral_orientation_reversal",
    "f a b",
    [],
    eq(Int(f, b, a), neg(Int(f, a, b))),
    "Reversing the endpoints negates the total oriented interval integral of any real function.",
    [
        "Use the oriented interval-integral definition.",
        "Interchange the two endpoints.",
        "The two measure-restricted integrals exchange places.",
        "Their difference is the negative of the original value.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) : (∫ x in b..a, f x)= -(∫ x in a..b, f x)",
    "exact intervalIntegral.integral_symm a b",
)
emit(
    "integral_difference",
    "f g a b",
    [Integrable(f, a, b), Integrable(g, a, b)],
    eq(Int(lam(sub(fx, gx)), a, b), sub(Int(f, a, b), Int(g, a, b))),
    "The integral of the difference of two interval-integrable functions is the difference of their integrals.",
    [
        "Negating an integrable function preserves integrability.",
        "Represent the difference as addition of a negation.",
        "Apply linearity under the two integrability premises.",
        "Rewrite the resulting integral sum as a difference.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hg : IntervalIntegrable g MeasureTheory.volume a b) : (∫ x in a..b, f x-g x)=(∫ x in a..b, f x)-(∫ x in a..b, g x)",
    "exact intervalIntegral.integral_sub hf hg",
)
emit(
    "fundamental_theorem_lower_endpoint",
    "f a b",
    [C(f)],
    D(lam(Int(f, x, b)), a, neg(fa)),
    "For continuous f, differentiation of x↦∫[x,b]f at a gives -f(a).",
    [
        "Reverse the integral to put the variable endpoint on the right.",
        "The upper-endpoint fundamental theorem gives derivative f(a).",
        "Negate the integral and its derivative.",
        "The fixed upper endpoint b remains unchanged.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hf : Continuous f) : HasDerivAt (fun x => ∫ t in x..b, f t) (-f a) a",
    "convert! (hf.integral_hasStrictDerivAt b a).hasDerivAt.neg using 1\nfunext x\nexact intervalIntegral.integral_symm b x",
)
emit(
    "moving_both_endpoints",
    "f g h a u v",
    [C(f), D(g, a, u), D(h, a, v)],
    D(
        lam(Int(f, at(g, x), at(h, x))),
        a,
        sub(mul(at(f, at(h, a)), v), mul(at(f, at(g, a)), u)),
    ),
    "If f is continuous and g,h have derivatives u,v at a, then d/dx ∫[g(x),h(x)]f at a equals f(h(a))*v-f(g(a))*u.",
    [
        "Write the moving interval integral as two integrals from a fixed origin.",
        "Apply the fundamental theorem to each upper-endpoint integral.",
        "Compose with h and g, retaining both endpoint velocities.",
        "Subtract the lower-endpoint contribution from the upper contribution.",
    ],
    "example (f g h : ℝ → ℝ) (a u v : ℝ) (hf : Continuous f) (hg : HasDerivAt g u a) (hh : HasDerivAt h v a) : HasDerivAt (fun x => ∫ t in g x..h x, f t) (f (h a)*v-f (g a)*u) a",
    "have h1 := ((hf.integral_hasStrictDerivAt 0 (h a)).hasDerivAt.comp a hh).sub ((hf.integral_hasStrictDerivAt 0 (g a)).hasDerivAt.comp a hg)\nconvert! h1 using 1\nfunext x\nexact (intervalIntegral.integral_interval_sub_left (hf.intervalIntegrable 0 (h x)) (hf.intervalIntegrable 0 (g x))).symm",
)
emit(
    "local_integration_by_parts",
    "f g h k a b",
    [
        Cu(f, a, b),
        Cu(g, a, b),
        Dopen(f, h, ca("min", a, b), ca("max", a, b)),
        Dopen(g, k, ca("min", a, b), ca("max", a, b)),
        Integrable(h, a, b),
        Integrable(k, a, b),
    ],
    eq(Int(lam(add(mul(hx, gx), mul(fx, kx))), a, b), sub(mul(fb, gb), mul(fa, ga))),
    "If f,g are continuous on uIcc(a,b), have derivatives h,k on its interior, and h,k are interval-integrable, then ∫[a,b](h*g+f*k)=f(b)g(b)-f(a)g(a). No endpoint derivatives are required.",
    [
        "Continuity on the closed interval controls the endpoint values.",
        "Differentiate the product only on the open interval.",
        "The derivative terms are integrable using the continuous multipliers.",
        "Apply the interval fundamental theorem to the product.",
    ],
    "example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.uIcc a b)) (hg : ContinuousOn g (Set.uIcc a b)) (hfh : ∀ x ∈ Set.Ioo (min a b) (max a b), HasDerivAt f (h x) x) (hgk : ∀ x ∈ Set.Ioo (min a b) (max a b), HasDerivAt g (k x) x) (hh : IntervalIntegrable h MeasureTheory.volume a b) (hk : IntervalIntegrable k MeasureTheory.volume a b) : (∫ x in a..b, h x*g x+f x*k x)=f b*g b-f a*g a",
    "exact intervalIntegral.integral_deriv_mul_eq_sub_of_hasDerivAt hf hg hfh hgk hh hk",
)
emit(
    "local_image_substitution",
    "f g h a b",
    [Du(f, h, a, b), Cu(h, a, b), ca("continuous_on_image", g, f, a, b)],
    eq(Int(lam(mul(at(g, fx), hx)), a, b), Int(g, fa, fb)),
    "If f has continuous derivative h on uIcc(a,b) and g is continuous only on f(image uIcc(a,b)), then ∫[a,b]g(f(x))*h(x)=∫[f(a),f(b)]g.",
    [
        "Restrict the derivative witness and its continuity to the source interval.",
        "Require outer continuity only on the actual image of that interval.",
        "Apply change of variables with the oriented image endpoints.",
        "No global smoothness or monotonicity of the substitution is assumed.",
    ],
    "example (f g h : ℝ → ℝ) (a b : ℝ) (hd : ∀ x ∈ Set.uIcc a b, HasDerivAt f (h x) x) (hc : ContinuousOn h (Set.uIcc a b)) (hg : ContinuousOn g (f '' Set.uIcc a b)) : (∫ x in a..b, g (f x)*h x)=∫ x in f a..f b, g x",
    "exact intervalIntegral.integral_comp_mul_deriv' hd hc hg",
)
emit(
    "inverse_derivative",
    "f g a u",
    [
        ca("continuous_at", g, a),
        D(f, ga, u),
        rel("neq", u, z),
        forall("x", eq(at(f, gx), x)),
    ],
    D(g, a, div(o, u)),
    "If f∘g is the identity, g is continuous at a, and f has nonzero derivative u at g(a), then g has derivative 1/u at a.",
    [
        "The composition identity provides a local left inverse for g.",
        "Continuity of g keeps its values near g(a).",
        "The nonzero derivative of f is invertible as a real linear map.",
        "The inverse-function derivative rule yields the reciprocal derivative.",
    ],
    "example (f g : ℝ → ℝ) (a u : ℝ) (hg : ContinuousAt g a) (hf : HasDerivAt f u (g a)) (hu : u ≠ 0) (hi : ∀ x, f (g x)=x) : HasDerivAt g (1/u) a",
    "simpa only [one_div] using hf.of_local_left_inverse hg hu (Filter.Eventually.of_forall hi)",
)
emit(
    "positive_derivative_strict_monotonicity",
    "f g a b",
    [Cc(f, a, b), Dopen(f, g, a, b), forall("x", Imp(opened(x, a, b), lt(z, gx)))],
    ca("strict_monotone_on_closed", f, a, b),
    "A function continuous on [a,b] with an explicitly positive derivative throughout (a,b) is strictly increasing on [a,b].",
    [
        "Take any two ordered points of the closed interval.",
        "Continuity gives the mean-value theorem its endpoint hypotheses.",
        "Every interior derivative is strictly positive.",
        "The resulting secant slope is positive, proving strict increase.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x ∈ Set.Ioo a b, HasDerivAt f (g x) x) (hp : ∀ x ∈ Set.Ioo a b, 0 < g x) : StrictMonoOn f (Set.Icc a b)",
    "apply strictMonoOn_of_deriv_pos (convex_Icc a b) hc\nintro x hx\nhave hx' : x ∈ Set.Ioo a b := by simpa only [interior_Icc] using hx\nrw [(hd x hx').deriv]\nexact hp x hx'",
)
emit(
    "monotone_derivative_nonnegative",
    "f a u",
    [ca("monotone", f), D(f, a, u)],
    le(z, u),
    "If f is nondecreasing on ℝ and has derivative u at a, then u≥0.",
    [
        "Difference quotients of a nondecreasing function have nonnegative sign.",
        "Pass that sign to their limit.",
        "The derivative witness identifies that limit with u.",
        "Conclude nonnegativity, without claiming strict positivity.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) (hm : Monotone f) (hf : HasDerivAt f u a) : 0 ≤ u",
    "simpa only [hf.deriv] using (hm.deriv_nonneg (x := a))",
)
emit(
    "monotone_derivative_convex",
    "f",
    [ca("differentiable", f), ca("monotone", der(f))],
    ca("convex", f),
    "A differentiable real function whose derivative is nondecreasing on ℝ is globally convex.",
    [
        "Compare neighboring secant slopes using the mean-value theorem.",
        "Monotonicity orders the intermediate derivative values.",
        "Thus secant slopes increase from left to right.",
        "The ordered-slope criterion yields global convexity.",
    ],
    "example (f : ℝ → ℝ) (hf : Differentiable ℝ f) (hm : Monotone (deriv f)) : ConvexOn ℝ Set.univ f",
    "exact Monotone.convexOn_univ_of_deriv hf hm",
)
emit(
    "strict_derivative_strict_convex",
    "f",
    [C(f), forall("x y", Imp(lt(x, y), lt(at(der(f), x), at(der(f), y))))],
    ca("strict_convex", f),
    "A continuous real function with strictly increasing total derivative is strictly convex; strict derivative inequalities already rule out nondifferentiability except possibly at one point.",
    [
        "Use continuity of the function on the convex real domain.",
        "Strict increase of derivative values gives strict secant-slope separation.",
        "Apply the strict convexity criterion for the derivative.",
        "No extra differentiability premise is silently inferred from a zero derivative value.",
    ],
    "example (f : ℝ → ℝ) (hc : Continuous f) (hm : StrictMono (deriv f)) : StrictConvexOn ℝ Set.univ f",
    "apply StrictMonoOn.strictConvexOn_of_deriv convex_univ hc.continuousOn\nexact hm.strictMonoOn _",
)
emit(
    "second_derivative_convex",
    "f",
    [
        ca("differentiable", f),
        ca("differentiable", der(f)),
        forall("x", le(z, at(der(der(f)), x))),
    ],
    ca("convex", f),
    "If f and its derivative are differentiable everywhere and f″≥0 everywhere, then f is globally convex.",
    [
        "The second derivative is the derivative of the first derivative.",
        "Its nonnegative sign makes the first derivative nondecreasing.",
        "The original function is differentiable by hypothesis.",
        "Apply the monotone-derivative criterion for convexity.",
    ],
    "example (f : ℝ → ℝ) (hf : Differentiable ℝ f) (h2 : Differentiable ℝ (deriv f)) (hn : ∀ x, 0 ≤ deriv (deriv f) x) : ConvexOn ℝ Set.univ f",
    "exact convexOn_univ_of_deriv2_nonneg hf h2 hn",
)
emit(
    "second_derivative_minimum",
    "f a u",
    [D(f, a, z), D(der(f), a, u), lt(z, u)],
    ca("local_min", f, a),
    "If f′(a)=0 with an actual derivative witness and the derivative function has a positive derivative u at a, then f has an unconstrained local minimum at a.",
    [
        "The first derivative witness supplies continuity and the stationary condition.",
        "A positive derivative of f′ makes f′ change from negative to positive near a.",
        "Apply the derivative-sign local minimum test.",
        "This is a sufficient condition; zero second derivative gives no conclusion.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f 0 a) (h2 : HasDerivAt (deriv f) u a) (hu : 0 < u) : IsLocalMin f a",
    "exact isLocalMin_of_deriv_deriv_pos (by simpa only [h2.deriv] using hu) hf.deriv hf.continuousAt",
)
emit(
    "darboux_derivative_intermediate",
    "f g a b u",
    [le(a, b), Dclosed(f, g, a, b), le(ga, u), le(u, gb)],
    exists("c", And(closed(c, a, b), eq(at(g, c), u))),
    "If f has derivative g at every point of [a,b], a≤b, and g(a)≤u≤g(b), some c in [a,b] satisfies g(c)=u; continuity of g is not required.",
    [
        "Restrict the derivative witnesses to the closed interval.",
        "Darboux’s theorem makes the image of the derivative order-connected.",
        "The endpoint derivative values straddle u.",
        "Obtain an interior-or-endpoint value realizing u.",
    ],
    "example (f g : ℝ → ℝ) (a b u : ℝ) (hab : a ≤ b) (hf : ∀ x ∈ Set.Icc a b, HasDerivAt f (g x) x) (ha : g a ≤ u) (hb : u ≤ g b) : ∃ c ∈ Set.Icc a b, g c=u",
    "exact exists_hasDerivWithinAt_eq_of_ge_of_le hab (fun x hx => (hf x hx).hasDerivWithinAt) ha hb",
)
emit(
    "cauchy_mean_value",
    "f g h k a b",
    [lt(a, b), Cc(f, a, b), Cc(g, a, b), Dopen(f, h, a, b), Dopen(g, k, a, b)],
    exists(
        "c",
        And(
            opened(c, a, b), eq(mul(sub(gb, ga), at(h, c)), mul(sub(fb, fa), at(k, c)))
        ),
    ),
    "For a<b and continuous f,g on [a,b] with derivatives h,k on (a,b), some c in (a,b) satisfies (g(b)-g(a))*h(c)=(f(b)-f(a))*k(c). No division or nonzero denominator is assumed.",
    [
        "Form the endpoint-weighted difference of f and g.",
        "It has equal endpoint values.",
        "Rolle’s theorem gives a zero derivative at an interior point.",
        "Expand that derivative to obtain the cross-multiplied identity.",
    ],
    "example (f g h k : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hf : ContinuousOn f (Set.Icc a b)) (hg : ContinuousOn g (Set.Icc a b)) (hd : ∀ x ∈ Set.Ioo a b, HasDerivAt f (h x) x) (he : ∀ x ∈ Set.Ioo a b, HasDerivAt g (k x) x) : ∃ c ∈ Set.Ioo a b, (g b-g a)*h c=(f b-f a)*k c",
    "exact exists_ratio_hasDerivAt_eq_ratio_slope f h hab hf hd g k hg he",
)
emit(
    "derivative_difference_quotient_limit",
    "f a u",
    [],
    logic(
        "equivalent",
        D(f, a, u),
        ca("limit_punctured", lam(div(sub(at(f, add(a, x)), fa), x)), z, u),
    ),
    "Having derivative u at a is equivalent to the punctured limit of (f(a+t)-f(a))/t as t→0 being u.",
    [
        "Write the derivative criterion using increments from a.",
        "Exclude t=0 in the source neighborhood filter.",
        "Identify division by t with inverse scalar multiplication.",
        "The little-o derivative condition and difference-quotient limit are equivalent.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) : HasDerivAt f u a ↔ Filter.Tendsto (fun t => (f (a+t)-f a)/t) (nhdsWithin 0 {0}ᶜ) (nhds u)",
    "simpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using (hasDerivAt_iff_tendsto_slope_zero (f := f) (x := a) (f' := u))",
)
emit(
    "exponential_dominates_natural_power",
    "n",
    [],
    ca("limit_at_top", lam(mul(pow(x, n), ca("exp", neg(x)))), z),
    "For every natural n, x^n exp(-x) tends to zero as the real variable x tends to positive infinity.",
    [
        "Fix an arbitrary natural degree n.",
        "Exponential growth eventually dominates that polynomial degree.",
        "Rewrite polynomial divided by exp(x) as multiplication by exp(-x).",
        "Conclude a zero real-variable limit, including degree zero.",
    ],
    "example (n : ℕ) : Filter.Tendsto (fun x : ℝ => x^n*Real.exp (-x)) Filter.atTop (nhds 0)",
    "exact Real.tendsto_pow_mul_exp_neg_atTop_nhds_zero n",
)
emit(
    "log_power_over_affine_limit",
    "n a b",
    [rel("neq", a, z)],
    ca("limit_at_top", lam(div(pow(ca("log", x), n), add(mul(a, x), b))), z),
    "For every natural n and real a≠0,b, (log x)^n/(a*x+b) tends to zero as x→+∞.",
    [
        "Fix the logarithmic degree and nonzero leading affine coefficient.",
        "Logarithmic powers grow more slowly than the real variable.",
        "An affine denominator with nonzero slope has the same eventual scale as x.",
        "The quotient therefore tends to zero for either sign of a.",
    ],
    "example (n : ℕ) (a b : ℝ) (ha : a ≠ 0) : Filter.Tendsto (fun x : ℝ => Real.log x^n/(a*x+b)) Filter.atTop (nhds 0)",
    "exact Real.tendsto_pow_log_div_mul_add_atTop a b n ha",
)
emit(
    "lhopital_zero_right",
    "f g h k a b u",
    [
        lt(a, b),
        Dopen(f, h, a, b),
        Dopen(g, k, a, b),
        forall("x", Imp(opened(x, a, b), rel("neq", kx, z))),
        ca("limit_right", f, a, z),
        ca("limit_right", g, a, z),
        ca("limit_right", lam(div(hx, kx)), a, u),
    ],
    ca("limit_right", lam(div(fx, gx)), a, u),
    "For a<b, if f,g have derivatives h,k on (a,b), k never vanishes there, f,g both tend to zero from the right at a, and h/k tends to u there, then f/g tends to u from the right at a.",
    [
        "Both numerator and denominator have the zero limiting form.",
        "The nonzero denominator derivative allows a Cauchy mean-value comparison on each short interval.",
        "The derivative quotient tends to the specified finite real u.",
        "Pass the comparison to the right-hand limit of the original quotient.",
    ],
    "example (f g h k : ℝ → ℝ) (a b u : ℝ) (hab : a < b) (hf : ∀ x ∈ Set.Ioo a b, HasDerivAt f (h x) x) (hg : ∀ x ∈ Set.Ioo a b, HasDerivAt g (k x) x) (hk : ∀ x ∈ Set.Ioo a b, k x ≠ 0) (hfa : Filter.Tendsto f (nhdsWithin a (Set.Ioi a)) (nhds 0)) (hga : Filter.Tendsto g (nhdsWithin a (Set.Ioi a)) (nhds 0)) (hq : Filter.Tendsto (fun x => h x/k x) (nhdsWithin a (Set.Ioi a)) (nhds u)) : Filter.Tendsto (fun x => f x/g x) (nhdsWithin a (Set.Ioi a)) (nhds u)",
    "exact HasDerivAt.lhopital_zero_right_on_Ioo hab hf hg hk hfa hga hq",
)
emit(
    "compact_interval_uniform_continuity",
    "f a b",
    [Cc(f, a, b)],
    ca("uniform_continuous_on_closed", f, a, b),
    "Every real function continuous on the closed bounded interval [a,b] is uniformly continuous there.",
    [
        "The closed bounded interval is compact, including the empty case.",
        "Restrict f to that compact domain.",
        "The compact-domain continuity theorem supplies a common modulus for every point.",
        "Conclude uniform continuity on the interval without asserting it on all of ℝ.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.Icc a b)) : UniformContinuousOn f (Set.Icc a b)",
    "exact isCompact_Icc.uniformContinuousOn_of_continuous hf",
)
emit(
    "monotone_interval_integrability",
    "f a b",
    [ca("monotone_on_unordered", f, a, b)],
    Integrable(f, a, b),
    "A real function nondecreasing on uIcc(a,b) is interval-integrable between a,b even if it has jump discontinuities.",
    [
        "Monotonicity on a compact interval bounds the function by endpoint values.",
        "Monotone real functions have the required measurability.",
        "The finite interval measure turns this boundedness into integrability.",
        "The same unordered interval handles either endpoint orientation.",
    ],
    "example (f : ℝ → ℝ) (a b : ℝ) (hf : MonotoneOn f (Set.uIcc a b)) : IntervalIntegrable f MeasureTheory.volume a b",
    "exact hf.intervalIntegrable",
)
emit(
    "convex_secant_derivative_bounds",
    "f a b u v",
    [ca("convex", f), lt(a, b), D(f, a, u), D(f, b, v)],
    And(le(u, div(sub(fb, fa), sub(b, a))), le(div(sub(fb, fa), sub(b, a)), v)),
    "For globally convex f and a<b with derivatives u at a and v at b, the secant slope lies between u and v.",
    [
        "Convexity orders the slopes of nested secants.",
        "Pass to the right limit at a to obtain the lower derivative bound.",
        "Pass to the left limit at b to obtain the upper derivative bound.",
        "The strict endpoint inequality ensures the secant denominator is nonzero.",
    ],
    "example (f : ℝ → ℝ) (a b u v : ℝ) (hc : ConvexOn ℝ Set.univ f) (hab : a < b) (ha : HasDerivAt f u a) (hb : HasDerivAt f v b) : u ≤ (f b-f a)/(b-a) ∧ (f b-f a)/(b-a) ≤ v",
    "simpa only [slope_def_field] using And.intro (hc.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ b) hab ha) (hc.slope_le_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ b) hab hb)",
)
emit(
    "convex_derivative_monotone",
    "f",
    [ca("convex", f), ca("differentiable", f)],
    ca("monotone", der(f)),
    "A differentiable globally convex real function has a nondecreasing derivative.",
    [
        "Take two ordered points of the real domain.",
        "The derivative at the left is bounded above by their secant slope.",
        "That slope is bounded above by the derivative at the right.",
        "Transitivity gives monotonicity of the derivative.",
    ],
    "example (f : ℝ → ℝ) (hc : ConvexOn ℝ Set.univ f) (hf : Differentiable ℝ f) : Monotone (deriv f)",
    "exact monotoneOn_univ.mp (hc.monotoneOn_deriv (fun x _ => hf x))",
)

L = lambda f, a, u: ca("limit_punctured", f, a, u)
emit(
    "punctured_limit_sum_product",
    "f g a u v",
    [L(f, a, u), L(g, a, v)],
    And(L(lam(add(fx, gx)), a, add(u, v)), L(lam(mul(fx, gx)), a, mul(u, v))),
    "If f(x)→u and g(x)→v as real x approaches a with x≠a, their sum tends to u+v and their product tends to uv; no condition is imposed on f(a),g(a).",
    [
        "Use the common punctured neighborhood filter at a.",
        "Addition is continuous at the limiting pair (u,v).",
        "Multiplication is continuous at the same pair.",
        "Compose those operations with the pair of convergent functions.",
    ],
    "example (f g : ℝ → ℝ) (a u v : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hg : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds v)) : Filter.Tendsto (fun x => f x+g x) (nhdsWithin a {a}ᶜ) (nhds (u+v)) ∧ Filter.Tendsto (fun x => f x*g x) (nhdsWithin a {a}ᶜ) (nhds (u*v))",
    "exact ⟨hf.add hg,hf.mul hg⟩",
)
emit(
    "punctured_limit_quotient",
    "f g a u v",
    [L(f, a, u), L(g, a, v), rel("neq", v, z)],
    L(lam(div(fx, gx)), a, div(u, v)),
    "If f(x)→u and g(x)→v≠0 as real x approaches a punctured, then f(x)/g(x)→u/v.",
    [
        "The limiting denominator is nonzero.",
        "Continuity of inversion yields the reciprocal limit.",
        "Multiply that limit by the numerator limit.",
        "No value of the quotient at a is required for the punctured limit.",
    ],
    "example (f g : ℝ → ℝ) (a u v : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hg : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds v)) (hv : v ≠ 0) : Filter.Tendsto (fun x => f x/g x) (nhdsWithin a {a}ᶜ) (nhds (u/v))",
    "exact hf.div hg hv",
)
emit(
    "punctured_limit_continuous_composition",
    "f g a b",
    [L(f, a, b), ca("continuous_at", g, b)],
    L(lam(at(g, fx)), a, at(g, b)),
    "If f(x)→b as real x approaches a punctured and g is continuous at b, then g(f(x))→g(b), even if f takes the value b near a.",
    [
        "The inner limit enters the full neighborhood filter at b.",
        "Continuity of g supplies a limit from that full filter.",
        "Compose the two filter maps.",
        "This avoids the extra avoidance premise needed for a merely punctured outer limit.",
    ],
    "example (f g : ℝ → ℝ) (a b : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds b)) (hg : ContinuousAt g b) : Filter.Tendsto (fun x => g (f x)) (nhdsWithin a {a}ᶜ) (nhds (g b))",
    "exact hg.tendsto.comp hf",
)
emit(
    "removable_singularity_extension",
    "f a u",
    [],
    logic(
        "equivalent", L(f, a, u), ca("continuous_at", ca("update_value", f, a, u), a)
    ),
    "A finite punctured limit f(x)→u at a exists with value u exactly when replacing f(a) by u makes the function continuous at a.",
    [
        "Updating the value changes only the singleton {a}.",
        "The old and new functions agree on the punctured neighborhood.",
        "Continuity at a is equivalent to the punctured limit being the new value there.",
        "Use the update identity to obtain both implications.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u) ↔ ContinuousAt (Function.update f a u) a",
    "exact continuousAt_update_same.symm",
)
emit(
    "punctured_squeeze_limit",
    "f g h a u",
    [L(f, a, u), L(h, a, u), forall("x", le(fx, gx)), forall("x", le(gx, hx))],
    L(g, a, u),
    "If real functions f≤g≤h pointwise and f,h both tend to u as x approaches a punctured, then g tends to u there.",
    [
        "Every punctured neighborhood inherits the two pointwise inequalities.",
        "Both bounding functions eventually enter any ordered neighborhood of u.",
        "The middle value lies in the same neighborhood.",
        "The order-topology squeeze theorem gives the middle limit.",
    ],
    "example (f g h : ℝ → ℝ) (a u : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hh : Filter.Tendsto h (nhdsWithin a {a}ᶜ) (nhds u)) (hfg : ∀ x, f x ≤ g x) (hgh : ∀ x, g x ≤ h x) : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds u)",
    "exact tendsto_of_tendsto_of_tendsto_of_le_of_le hf hh hfg hgh",
)
emit(
    "two_sided_limit_characterization",
    "f a u",
    [],
    logic(
        "equivalent",
        L(f, a, u),
        And(ca("limit_left", f, a, u), ca("limit_right", f, a, u)),
    ),
    "A real function has punctured two-sided limit u at a if and only if its left-hand and right-hand limits at a both equal u.",
    [
        "The punctured line is the union of the strict left and right half-lines.",
        "The neighborhood-within filter of a union is the supremum of the two filters.",
        "Convergence from that supremum is equivalent to convergence from each side.",
        "Both sides must have the same target value u.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u) ↔ Filter.Tendsto f (nhdsWithin a (Set.Iio a)) (nhds u) ∧ Filter.Tendsto f (nhdsWithin a (Set.Ioi a)) (nhds u)",
    "simp [← Set.Iio_union_Ioi, nhdsWithin_union]",
)


constant = lam(u)
spike = ca("update_value", constant, a, v)
emit(
    "counterexample_limit_without_continuity",
    "a u v",
    [rel("neq", u, v)],
    And(L(spike, a, u), logic("not", ca("continuous_at", spike, a))),
    "For every real a and distinct u,v, the function equal to u away from a and v at a has punctured limit u at a but is not continuous at a.",
    [
        "The exceptional point is absent from the punctured source filter.",
        "The modified function therefore has the same limit as the constant u.",
        "Continuity would force its limit to equal its value v at a.",
        "Uniqueness of finite real limits would give u=v, contradicting the premise.",
    ],
    "example (a u v : ℝ) (hne : u ≠ v) : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds u) ∧ ¬ContinuousAt (Function.update (fun _ : ℝ => u) a v) a",
    "have hl : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds u) := by\n  apply Filter.Tendsto.congr' _ (tendsto_const_nhds (x := u))\n  filter_upwards [self_mem_nhdsWithin] with x hx\n  simp only [Set.mem_compl_iff, Set.mem_singleton_iff] at hx\n  exact (Function.update_of_ne hx v (fun _ : ℝ => u)).symm\nrefine ⟨hl, ?_⟩\nintro hc\nhave hv : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds v) := by\n  simpa only [Function.update_self] using hc.tendsto.mono_left nhdsWithin_le_nhds\nexact hne (tendsto_nhds_unique hl hv)",
)
midpoint = div(add(a, b), two)
centered = lam(sub(x, midpoint))
emit(
    "counterexample_zero_integral_cancellation",
    "a b",
    [lt(a, b)],
    And(C(centered), eq(Int(centered, a, b), z), rel("neq", sub(a, midpoint), z)),
    "For every a<b, the continuous function x↦x-(a+b)/2 has integral zero on [a,b] but a nonzero value at a. Thus zero integral need not imply pointwise vanishing without nonnegativity.",
    [
        "An affine function is continuous.",
        "Integrate x and subtract the constant midpoint times interval length.",
        "The two contributions cancel algebraically.",
        "At a its value is (a-b)/2, nonzero because a<b.",
    ],
    "example (a b : ℝ) (hab : a < b) : Continuous (fun x : ℝ => x-(a+b)/2) ∧ (∫ x in a..b, (x-(a+b)/2))=0 ∧ (a-(a+b)/2) ≠ 0",
    "refine ⟨continuous_id.sub continuous_const, ?_, ?_⟩\n· rw [intervalIntegral.integral_sub (f := fun x : ℝ => x) (g := fun _ : ℝ => (a+b)/2) (continuous_id.intervalIntegrable a b) (continuous_const.intervalIntegrable a b), integral_id, intervalIntegral.integral_const]\n  simp only [smul_eq_mul]\n  ring\n· linarith",
)
cusp = lam(absx(sub(x, a)))
emit(
    "counterexample_continuous_not_differentiable",
    "a",
    [],
    And(C(cusp), logic("not", ca("differentiable_at", cusp, a))),
    "For every real a, x↦|x-a| is continuous everywhere but not differentiable at a, so continuity does not imply differentiability.",
    [
        "Translation and absolute value preserve continuity.",
        "Suppose the translated absolute-value function were differentiable at a.",
        "Compose with x↦x+a to obtain differentiability of |x| at zero.",
        "The unequal one-sided slopes of |x| contradict differentiability there.",
    ],
    "example (a : ℝ) : Continuous (fun x : ℝ => |x-a|) ∧ ¬ DifferentiableAt ℝ (fun x : ℝ => |x-a|) a",
    "refine ⟨(continuous_id.sub continuous_const).abs, ?_⟩\nintro hd\nhave hx : DifferentiableAt ℝ (fun x : ℝ => x+a) 0 := differentiableAt_id.add_const a\nhave hh : DifferentiableAt ℝ (fun x : ℝ => |x-a|) (0+a) := by simpa using hd\nhave hc := hh.comp 0 hx\nexact not_differentiableAt_abs_zero (by simpa only [Function.comp_def, add_sub_cancel_right] using hc)",
)


def main():
    assert len(cards) >= 40
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
            ROOT / "pals-agent/pals_agent/typed_calculus_v5.py"
        ),
        "registry_sha256": hashfile(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-calculus-v5-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": next(p["rev"] for p in packages if p["name"] == "mathlib"),
    }
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": "typed-calculus-v5",
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
