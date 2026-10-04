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
WITNESS = ROOT / "docs/calculus-v5-supplement-batch.lean"
OUTPUT = ROOT / "docs/calculus-v5-supplement-batch.json"


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
            "id": "calculus_supp_v5_" + key,
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


exp = lambda t: ca("exp", t)
absx = lambda t: ar("abs", t)
Not = lambda p: logic("not", p)
Iff = lambda p, q: logic("equivalent", p, q)


card(
    "difference_quotient_extension",
    "f a u",
    [D(f, a, u)],
    ca(
        "continuous_at",
        ca("update_value", lam(div(sub(at(f, add(a, x)), fa), x)), z, u),
        z,
    ),
    "If f has derivative u at a, assigning value u at zero to t↦(f(a+t)-f(a))/t constructs a function continuous at zero.",
    "Use the derivative hypothesis to obtain the punctured difference-quotient limit u.",
    [
        "Use the derivative hypothesis to obtain the punctured difference-quotient limit u.",
        "Interpret the quotient only off zero when taking this limit.",
        "Replace its value at zero by u.",
        "The continuous-update criterion now proves continuity of the constructed extension.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : ContinuousAt (Function.update (fun t => (f (a+t)-f a)/t) 0 u) 0",
    "apply continuousAt_update_same.mpr\nsimpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using hf.tendsto_slope_zero",
)

card(
    "product_converse_counterexample",
    "a",
    [],
    And(
        D(lam(mul(absx(sub(x, a)), absx(sub(x, a)))), a, z),
        Not(ca("differentiable_at", lam(absx(sub(x, a))), a)),
    ),
    "For every real a, the product |x-a|·|x-a| has derivative zero at a, although each factor |x-a| is not differentiable at a.",
    "Rewrite the product of absolute values as (x-a)².",
    [
        "Rewrite the product of absolute values as (x-a)².",
        "Differentiate this polynomial to obtain derivative zero at a.",
        "Translate the supposed derivative of |x-a| at a back to that of |x| at zero.",
        "The known cusp contradiction shows that differentiability of a product need not imply differentiability of its factors.",
    ],
    "example (a : ℝ) : HasDerivAt (fun x : ℝ => |x-a| * |x-a|) 0 a ∧ ¬DifferentiableAt ℝ (fun x : ℝ => |x-a|) a",
    "constructor\n· have h := ((hasDerivAt_id a).sub_const a).pow 2\n  convert! h using 1 <;> simp [sq_abs, ← sq, Pi.pow_apply, funext_iff]\n· intro hd\n  have hh : DifferentiableAt ℝ (fun x : ℝ => |x-a|) (0+a) := by simpa using hd\n  exact not_differentiableAt_abs_zero (by simpa only [Function.comp_def, add_sub_cancel_right, id_eq] using hh.comp 0 (differentiableAt_id.add_const a))",
)

card(
    "exp_quotient_derivative",
    "f g a u v",
    [D(f, a, u), D(g, a, v), Not(eq(ga, z))],
    D(
        lam(div(exp(fx), gx)),
        a,
        div(sub(mul(mul(exp(fa), u), ga), mul(exp(fa), v)), pow(ga, ni(2))),
    ),
    "If f,g have derivatives u,v at a and g(a)≠0, exp(f(x))/g(x) has derivative (exp(f(a))*u*g(a)-exp(f(a))*v)/g(a)² at a.",
    "Apply the exponential chain rule to f.",
    [
        "Apply the exponential chain rule to f.",
        "Keep the nonzero denominator g(a).",
        "Apply the quotient rule to exp∘f and g.",
        "Substitute both derivative values and retain the squared denominator.",
    ],
    "example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) (h : g a ≠ 0) : HasDerivAt (fun x => Real.exp (f x) / g x) ((Real.exp (f a)*u*g a-Real.exp (f a)*v)/(g a)^2) a",
    "exact hf.exp.div hg h",
)

card(
    "primitives_constant_difference",
    "f g h a b",
    [allD(f, h), allD(g, h)],
    eq(sub(fb, gb), sub(fa, ga)),
    "Two real functions with the same derivative h at every real point differ by one constant: f(b)-g(b)=f(a)-g(a).",
    "Subtract the derivative witnesses at each point.",
    [
        "Subtract the derivative witnesses at each point.",
        "The derivative of f-g is h(x)-h(x)=0.",
        "Differentiability follows from the same witnesses.",
        "The zero-derivative theorem shows that f-g has equal values at a and b.",
    ],
    "example (f g h : ℝ → ℝ) (a b : ℝ) (hf : ∀ x, HasDerivAt f (h x) x) (hg : ∀ x, HasDerivAt g (h x) x) : f b-g b=f a-g a",
    "exact is_const_of_deriv_eq_zero (fun x => ((hf x).sub (hg x)).differentiableAt) (fun x => by simpa using ((hf x).sub (hg x)).deriv) b a",
)

card(
    "quadratic_unique_minimum",
    "a c d",
    [lt(z, c)],
    forall(
        "x",
        And(
            le(d, add(mul(c, pow(sub(x, a), ni(2))), d)),
            Iff(eq(add(mul(c, pow(sub(x, a), ni(2))), d), d), eq(x, a)),
        ),
    ),
    "For arbitrary a,d and c>0, c(x-a)²+d is at least d for every x, and equality holds exactly at x=a; thus the minimum and its unique location are explicitly constructed.",
    "The square (x-a)² is nonnegative.",
    [
        "The square (x-a)² is nonnegative.",
        "Multiplication by positive c preserves nonnegativity.",
        "Equality with d forces the square to vanish.",
        "A real square vanishes exactly when x=a, which also attains the bound.",
    ],
    "example (a c d : ℝ) (hc : 0 < c) : ∀ x : ℝ, d ≤ c*(x-a)^2+d ∧ (c*(x-a)^2+d=d ↔ x=a)",
    "intro x\nconstructor\n· nlinarith [sq_nonneg (x-a)]\n· constructor\n  · intro h\n    have : (x-a)^2=0 := by nlinarith [sq_nonneg (x-a)]\n    nlinarith [sq_nonneg (x-a)]\n  · intro h; simp [h]",
)

card(
    "stationary_not_minimum",
    "a c",
    [lt(z, c)],
    And(
        D(lam(mul(neg(c), pow(sub(x, a), ni(2)))), a, z),
        forall(
            "e",
            Imp(
                lt(z, var("e")),
                exists(
                    "x",
                    And(
                        lt(absx(sub(x, a)), var("e")),
                        lt(
                            mul(neg(c), pow(sub(x, a), ni(2))),
                            mul(neg(c), pow(sub(a, a), ni(2))),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "For a∈ℝ and c>0, -c(x-a)² has derivative zero at a, yet every radius e>0 contains a point x with |x-a|<e and strictly smaller function value than at a.",
    "Differentiate the negative quadratic at a to obtain zero.",
    [
        "Differentiate the negative quadratic at a to obtain zero.",
        "For any positive radius choose x=a+e/2.",
        "Its distance from a is e/2, strictly less than e.",
        "Since c and (e/2)² are positive, the value at this point is strictly negative while the value at a is zero.",
    ],
    "example (a c : ℝ) (hc : 0 < c) : HasDerivAt (fun x : ℝ => -c*(x-a)^2) 0 a ∧ ∀ e : ℝ, 0<e → ∃ x, |x-a|<e ∧ -c*(x-a)^2 < -c*(a-a)^2",
    "constructor\n· convert! (((hasDerivAt_id a).sub_const a).pow 2).const_mul (-c) using 1 <;> simp\n· intro e he\n  refine ⟨a+e/2,?_,?_⟩\n  · simp only [add_sub_cancel_left, abs_of_pos (half_pos he)]; linarith\n  · simp only [add_sub_cancel_left, sub_self, zero_pow (by decide : 2≠0), mul_zero]\n    have : 0 < (e/2)^2 := sq_pos_of_pos (half_pos he)\n    nlinarith",
)

card(
    "convex_stationary_global_minimum",
    "f a",
    [ca("convex", f), D(f, a, z)],
    forall("x", le(fa, fx)),
    "If f is globally convex and has derivative zero at a, then f(a)≤f(x) for every real x: the stationary point is a global minimizer.",
    "For x>a bound the secant slope from below by the derivative zero at a.",
    [
        "For x>a bound the secant slope from below by the derivative zero at a.",
        "Multiply by the positive secant denominator to obtain f(a)≤f(x).",
        "For x<a bound the reversed secant slope from above by zero and obtain the same conclusion.",
        "At x=a equality completes the global comparison.",
    ],
    "example (f : ℝ → ℝ) (a : ℝ) (hc : ConvexOn ℝ Set.univ f) (ha : HasDerivAt f 0 a) : ∀ x, f a ≤ f x",
    "intro x\nrcases lt_trichotomy a x with h | h | h\n· have hs := hc.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ x) h ha\n  rw [slope_def_field] at hs\n  have := (le_div_iff₀ (sub_pos.mpr h)).mp hs\n  linarith\n· simp [h]\n· have hs := hc.slope_le_of_hasDerivAt (Set.mem_univ x) (Set.mem_univ a) h ha\n  rw [slope_def_field] at hs\n  have := (div_le_iff₀ (sub_pos.mpr h)).mp hs\n  linarith",
)

card(
    "scale_integrability_equivalence",
    "f a b c",
    [Not(eq(c, z))],
    Iff(Integrable(lam(at(f, mul(c, x))), div(a, c), div(b, c)), Integrable(f, a, b)),
    "For every c≠0, integrability of x↦f(cx) between a/c and b/c is equivalent to integrability of f between a and b, for either orientation.",
    "Use the nonzero scale to make multiplication by c invertible.",
    [
        "Use the nonzero scale to make multiplication by c invertible.",
        "Transport the interval with endpoints a/c,b/c to the interval with endpoints a,b.",
        "Apply interval-integrability under invertible scaling.",
        "Retain both implications without assuming c positive or endpoints ordered.",
    ],
    "example (f : ℝ → ℝ) (a b c : ℝ) (hc : c ≠ 0) : IntervalIntegrable (fun x => f (c*x)) MeasureTheory.volume (a/c) (b/c) ↔ IntervalIntegrable f MeasureTheory.volume a b",
    "exact IntervalIntegrable.comp_mul_left_iff hc",
)

card(
    "exp_product_ftc",
    "f g h k a b",
    [allD(f, h), allD(g, k), Integrable(lam(mul(exp(fx), add(mul(hx, gx), kx))), a, b)],
    eq(
        Int(lam(mul(exp(fx), add(mul(hx, gx), kx))), a, b),
        sub(mul(exp(fb), gb), mul(exp(fa), ga)),
    ),
    "If f′=h and g′=k everywhere and exp(f(x))*(h(x)*g(x)+k(x)) is interval-integrable from a to b, its integral equals exp(f(b))*g(b)-exp(f(a))*g(a).",
    "Differentiate exp∘f by the chain rule.",
    [
        "Differentiate exp∘f by the chain rule.",
        "Multiply by g using the product rule.",
        "Rearrange the derivative as exp(f)*(h*g+k).",
        "Apply the fundamental theorem with the explicitly assumed interval integrability.",
    ],
    "example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ∀ x, HasDerivAt f (h x) x) (hg : ∀ x, HasDerivAt g (k x) x) (hi : IntervalIntegrable (fun x => Real.exp (f x)*(h x*g x+k x)) MeasureTheory.volume a b) : (∫ x in a..b, Real.exp (f x)*(h x*g x+k x))=Real.exp (f b)*g b-Real.exp (f a)*g a",
    "apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ hi\nintro x hx\nconvert! ((hf x).exp.mul (hg x)) using 1 <;> ring",
)

card(
    "exponential_moment_integral",
    "a b c",
    [Not(eq(c, z))],
    eq(
        Int(lam(mul(x, exp(mul(c, x)))), a, b),
        sub(
            mul(sub(div(b, c), div(o, pow(c, ni(2)))), exp(mul(c, b))),
            mul(sub(div(a, c), div(o, pow(c, ni(2)))), exp(mul(c, a))),
        ),
    ),
    "For all endpoints a,b and nonzero c, ∫[a,b] x*exp(cx) = (b/c-1/c²)exp(cb)-(a/c-1/c²)exp(ca).",
    "Construct the integration-by-parts primitive F(x)=(x/c-1/c²)exp(cx).",
    [
        "Construct the integration-by-parts primitive F(x)=(x/c-1/c²)exp(cx).",
        "Differentiate using product, quotient-by-constant, and exponential chain rules.",
        "Cancel the constant terms using c≠0 to obtain F′(x)=x exp(cx).",
        "The continuous integrand is interval-integrable, so evaluate the primitive at both endpoints.",
    ],
    "example (a b c : ℝ) (hc : c ≠ 0) : (∫ x in a..b, x*Real.exp (c*x)) = (b/c-1/c^2)*Real.exp (c*b)-(a/c-1/c^2)*Real.exp (c*a)",
    "apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ ((by fun_prop : Continuous (fun x : ℝ => x*Real.exp (c*x))).intervalIntegrable a b)\nintro x hx\nhave h1 := (((hasDerivAt_id x).div_const c).sub_const (1/c^2)).mul (((hasDerivAt_id x).const_mul c).exp)\nconvert! h1 using 1 <;> simp only [id_eq] <;> field_simp <;> ring",
)

card(
    "ftc_point_spike_counterexample",
    "a b v",
    [Not(eq(v, z))],
    And(
        D(
            lam(
                Int(ca("update_value", bind("lambda", [("t", "Real")], z), a, v), b, x)
            ),
            a,
            z,
        ),
        Not(
            D(
                lam(
                    Int(
                        ca("update_value", bind("lambda", [("t", "Real")], z), a, v),
                        b,
                        x,
                    )
                ),
                a,
                v,
            )
        ),
    ),
    "For every a,b and v≠0, let f equal zero except f(a)=v. The variable-upper-endpoint integral x↦∫[b,x]f has derivative zero at a and does not have derivative f(a)=v there.",
    "A singleton has Lebesgue measure zero.",
    [
        "A singleton has Lebesgue measure zero.",
        "The point-modified function equals zero almost everywhere on every interval.",
        "Every variable-endpoint integral is consequently zero, so its derivative at a is zero.",
        "Uniqueness of derivatives and v≠0 exclude the claimed derivative v: continuity at a cannot simply be dropped from pointwise FTC.",
    ],
    "example (a b v : ℝ) (hv : v ≠ 0) : HasDerivAt (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) 0 a ∧ ¬HasDerivAt (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) v a",
    "have he : (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) = fun _ => (0:ℝ) := by\n  funext x\n  calc\n    (∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) = ∫ t in b..x, (0:ℝ) := by\n      apply intervalIntegral.integral_congr_ae\n      filter_upwards [MeasureTheory.volume.ae_ne a] with t ht\n      intro _\n      simp [Function.update_of_ne ht]\n    _=0 := by simp\nrw [he]\nexact ⟨hasDerivAt_const a 0, fun h => hv (h.unique (hasDerivAt_const a 0))⟩",
)

card(
    "mvt_endpoint_counterexample",
    "a b",
    [lt(a, b)],
    Not(
        exists(
            "x",
            And(
                opened(x, a, b),
                D(
                    ca("update_value", bind("lambda", [("t", "Real")], z), b, o),
                    x,
                    div(o, sub(b, a)),
                ),
            ),
        )
    ),
    "For every a<b, the function zero everywhere except value 1 at b has no x∈(a,b) with derivative equal to its secant slope 1/(b-a). Thus interior differentiability alone does not imply the mean value theorem.",
    "Every interior x differs from b and has a neighborhood avoiding b.",
    [
        "Every interior x differs from b and has a neighborhood avoiding b.",
        "On this neighborhood the function is constantly zero and has derivative zero.",
        "Its endpoint values are 0 at a and 1 at b, giving nonzero secant slope 1/(b-a).",
        "Derivative uniqueness excludes an interior point realizing that slope; endpoint continuity is the missing hypothesis.",
    ],
    "example (a b : ℝ) (hab : a < b) : ¬ ∃ x ∈ Set.Ioo a b, HasDerivAt (Function.update (fun _ : ℝ => (0:ℝ)) b 1) (1/(b-a)) x",
    "rintro ⟨x, hx, hd⟩\nhave hz : HasDerivAt (Function.update (fun _ : ℝ => (0:ℝ)) b 1) 0 x := by\n  apply (hasDerivAt_const x 0).congr_of_eventuallyEq\n  filter_upwards [eventually_ne_nhds hx.2.ne] with t ht\n  simp [Function.update_of_ne ht]\nhave hn : (1:ℝ)/(b-a) ≠ 0 := div_ne_zero one_ne_zero (sub_ne_zero.mpr hab.ne')\nexact hn (hd.unique hz)",
)

card(
    "quadratic_mean_value_point",
    "a b c d",
    [lt(a, b)],
    And(
        opened(div(add(a, b), two), a, b),
        D(
            lam(add(mul(c, pow(x, ni(2))), d)),
            div(add(a, b), two),
            div(
                sub(add(mul(c, pow(b, ni(2))), d), add(mul(c, pow(a, ni(2))), d)),
                sub(b, a),
            ),
        ),
    ),
    "For every a<b and arbitrary c,d, the midpoint (a+b)/2 lies in (a,b) and is a mean-value point for f(x)=c*x²+d: its derivative equals (f(b)-f(a))/(b-a).",
    "The midpoint lies strictly between the ordered endpoints.",
    [
        "The midpoint lies strictly between the ordered endpoints.",
        "Differentiate the arbitrary quadratic to obtain 2cx.",
        "Evaluate this derivative at the midpoint, obtaining c(a+b).",
        "Factor b²-a² and cancel b-a≠0 in the endpoint secant slope to get the same value.",
    ],
    "example (a b c d : ℝ) (hab : a < b) : (a+b)/2 ∈ Set.Ioo a b ∧ HasDerivAt (fun x : ℝ => c*x^2+d) (((c*b^2+d)-(c*a^2+d))/(b-a)) ((a+b)/2)",
    "constructor\n· constructor <;> linarith\n· have hd := (((hasDerivAt_id ((a+b)/2)).pow 2).const_mul c).add_const d\n  convert! hd using 1 <;> simp only [id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one, mul_one]\n  field_simp [sub_ne_zero.mpr hab.ne']\n  <;> ring",
)

card(
    "mvt_constant_slope_recognition",
    "f a b c",
    [lt(a, b), Cc(f, a, b), forall("x", Imp(opened(x, a, b), D(f, x, c)))],
    eq(sub(fb, fa), mul(c, sub(b, a))),
    "On a nondegenerate interval, continuity of f on [a,b] and derivative equal to a fixed c throughout (a,b) imply f(b)-f(a)=c(b-a). These are the closed-endpoint and open-interior hypotheses needed to recognize the constant-slope mean-value application.",
    "Check a<b and continuity at both endpoints and throughout the closed interval.",
    [
        "Check a<b and continuity at both endpoints and throughout the closed interval.",
        "Supply the constant derivative c at every interior point.",
        "Apply the mean value theorem to equate c to the endpoint secant slope.",
        "Multiply by b-a≠0 to recover the exact endpoint increment.",
    ],
    "example (f : ℝ → ℝ) (a b c : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x, x ∈ Set.Ioo a b → HasDerivAt f c x) : f b-f a=c*(b-a)",
    "obtain ⟨x, hx, he⟩ := exists_hasDerivAt_eq_slope f (fun _ => c) hab hc hd\nexact (eq_div_iff (sub_ne_zero.mpr hab.ne')).mp he |>.symm",
)

card(
    "strong_derivative_growth_minimum",
    "f h a c",
    [
        lt(z, c),
        allD(f, h),
        eq(at(h, a), z),
        forall(
            "x y", Imp(le(x, y), le(mul(mul(two, c), sub(y, x)), sub(at(h, y), hx)))
        ),
    ],
    forall("x", le(add(fa, mul(c, pow(sub(x, a), ni(2)))), fx)),
    "If c>0, f′=h everywhere, h(a)=0, and h(y)-h(x)≥2c(y-x) whenever x≤y, then f(x)≥f(a)+c(x-a)² for every x. A uniformly increasing derivative yields a quantitative global minimum bound.",
    "Subtract the quadratic c(x-a)² from f and call the result g.",
    [
        "Subtract the quadratic c(x-a)² from f and call the result g.",
        "Its derivative is h(x)-2c(x-a).",
        "The assumed slope-growth inequality makes this new derivative nondecreasing.",
        "Hence g is globally convex, and h(a)=0 makes g stationary at a.",
        "Compare both left and right secant slopes against the zero derivative to get g(a)≤g(x).",
        "Expand g and rearrange to obtain the global quadratic growth bound for f.",
    ],
    "example (f h : ℝ → ℝ) (a c : ℝ) (hc : 0 < c) (hf : ∀ x, HasDerivAt f (h x) x) (ha : h a = 0) (hh : ∀ x y, x ≤ y → 2*c*(y-x) ≤ h y-h x) : ∀ x, f a+c*(x-a)^2 ≤ f x",
    "let g : ℝ → ℝ := fun x => f x-c*(x-a)^2\nhave hd : ∀ x, HasDerivAt g (h x-2*c*(x-a)) x := by\n  intro x\n  convert! (hf x).sub ((((hasDerivAt_id x).sub_const a).pow 2).const_mul c) using 1 <;> simp only [id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one, mul_one]\n  <;> ring\nhave he : deriv g = fun x => h x-2*c*(x-a) := funext fun x => (hd x).deriv\nhave hm : Monotone (deriv g) := by\n  rw [he]\n  intro x y hxy\n  have := hh x y hxy\n  dsimp\n  linarith\nhave hg := hm.convexOn_univ_of_deriv (fun x => (hd x).differentiableAt)\nhave hz : HasDerivAt g 0 a := by simpa [ha] using hd a\nintro x\nhave hmin : g a ≤ g x := by\n  rcases lt_trichotomy a x with hi | hi | hi\n  · have hs := hg.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ x) hi hz\n    rw [slope_def_field] at hs\n    have := (le_div_iff₀ (sub_pos.mpr hi)).mp hs\n    linarith\n  · simp [hi]\n  · have hs := hg.slope_le_of_hasDerivAt (Set.mem_univ x) (Set.mem_univ a) hi hz\n    rw [slope_def_field] at hs\n    have := (div_le_iff₀ (sub_pos.mpr hi)).mp hs\n    linarith\ndsimp [g] at hmin\nnlinarith",
)


def main():
    assert len(cards) == 15
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
