"""Compile general calculus witnesses before emitting an exact typed OpenMath batch.

No profile extensions: variable natural exponents, integral values, sequences,
and transcendental function symbols are deliberately outside this batch.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_real_analysis import (
    canonicalize_typed_real_analysis_openmath_xml,
    validate_canonical_typed_real_analysis_openmath_xml,
)

BASE = "urn:pals:openmath:typed-math:v1"
WITNESS = ROOT / "docs/calculus-reuse-batch-20260930.lean"
OUTPUT = ROOT / "docs/calculus-reuse-batch-20260930.json"
WORKSPACE = ROOT / "pals-agent/lean-workspace"


def sym(cd, name):
    base = BASE if cd in ("typed1", "realanalysis1") else "http://www.openmath.org/cd"
    return f'<OMS cdbase="{base}" cd="{cd}" name="{name}"/>'


def var(name):
    return f'<OMV name="{name}"/>'


def app(operator, *args):
    return "<OMA>" + operator + "".join(args) + "</OMA>"


def ra(name, *args):
    return app(sym("realanalysis1", name), *args)


def op(name, *args):
    return app(sym("arith1", name), *args)


def rel(name, *args):
    return app(sym("relation1", name), *args)


def logic(name, *args):
    return app(sym("logic1", name), *args)


def bind(kind, variables, body):
    typed = "".join(
        "<OMATTR><OMATP>"
        + sym("typed1", "type")
        + sym("realanalysis1" if typ == "RealFunction" else "typed1", typ)
        + "</OMATP>"
        + var(name)
        + "</OMATTR>"
        for name, typ in variables
    )
    return (
        "<OMBIND>"
        + sym("realanalysis1" if kind == "lambda" else "typed1", kind)
        + "<OMBVAR>"
        + typed
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


def lam(body):
    return bind("lambda", [("x", "Real")], body)


def integer(n):
    return ra("of_int", f"<OMI>{n}</OMI>")


def at(f, x):
    return ra("apply", f, x)


def deriv(f, a, d):
    return ra("has_deriv_at", f, a, d)


def diff(f, a):
    return ra("differentiable_at", f, a)


def cont(f, a):
    return ra("continuous_at", f, a)


def integ(f, a, b):
    return ra("interval_integrable", f, a, b)


cards = []


def add(
    key, variables, premises, conclusion, statement, strategy, steps, target, proof
):
    body = conclusion
    for premise in reversed(premises):
        body = logic("implies", premise, body)
    xml = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind(
            "forall",
            [(v, "RealFunction" if v in ("f", "g") else "Real") for v in variables],
            body,
        )
        + "</OMOBJ>"
    )
    canonical = canonicalize_typed_real_analysis_openmath_xml(xml)
    validate_canonical_typed_real_analysis_openmath_xml(canonical)
    cards.append(
        {
            "id": "calculus_reuse_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": canonical,
            "lean_target": target,
            "lean_witness": "by\n  " + proof,
        }
    )


f, g, x, a, b, c, u, v = map(var, ("f", "g", "x", "a", "b", "c", "u", "v"))
fx, gx, fa, ga = at(f, x), at(g, x), at(f, a), at(g, a)
zero = integer(0)
volume = "(MeasureTheory.volume : MeasureTheory.Measure ℝ)"

# Derivative calculus: slopes are quantified real parameters, never inferred
# from a total derivative operator at a potentially nondifferentiable point.
for key, symbol, lean_symbol, slope, lean_slope, method, explanation in [
    (
        "derivative_sum",
        "plus",
        "+",
        op("plus", u, v),
        "u + v",
        "hf.add hg",
        "Add the two first-order approximations; their remainders remain little-o.",
    ),
    (
        "derivative_difference",
        "minus",
        "-",
        op("minus", u, v),
        "u - v",
        "hf.sub hg",
        "Subtract the first-order approximations and subtract their slopes.",
    ),
    (
        "derivative_product",
        "times",
        "*",
        op("plus", op("times", u, ga), op("times", fa, v)),
        "u * g a + f a * v",
        "hf.mul hg",
        "Use continuity of both differentiable factors to control the product remainder.",
    ),
]:
    add(
        key,
        ["f", "g", "a", "u", "v"],
        [deriv(f, a, u), deriv(g, a, v)],
        deriv(lam(op(symbol, fx, gx)), a, slope),
        f"For real functions f,g, if their derivatives at a are u,v, then the derivative of x ↦ f(x) {lean_symbol} g(x) at a is {lean_slope}.",
        explanation,
        [
            "Fix arbitrary real functions, a point, and the two derivative values.",
            "Use the assumed first-order approximation for f.",
            "Use the assumed first-order approximation for g.",
            explanation,
            "Read off the stated derivative coefficient.",
        ],
        f"example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f x {lean_symbol} g x) ({lean_slope}) a",
        f"exact {method}",
    )
add(
    "derivative_quotient",
    ["f", "g", "a", "u", "v"],
    [deriv(f, a, u), deriv(g, a, v), rel("neq", ga, zero)],
    deriv(
        lam(op("divide", fx, gx)),
        a,
        op(
            "divide",
            op("minus", op("times", u, ga), op("times", fa, v)),
            op("power", ga, "<OMI>2</OMI>"),
        ),
    ),
    "If f and g have derivatives u and v at a and g(a) ≠ 0, then f/g has derivative (u*g(a)-f(a)*v)/g(a)^2 at a.",
    "Differentiate inversion on a neighborhood where the denominator is nonzero, then apply the product rule.",
    [
        "Fix f,g,a,u,v with the stated derivative hypotheses.",
        "Derive continuity of g at a from differentiability.",
        "Use g(a) ≠ 0 to justify local inversion.",
        "Apply the quotient differentiation rule.",
        "Identify its numerator and squared denominator.",
    ],
    "example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) (hne : g a ≠ 0) : HasDerivAt (fun x => f x / g x) ((u * g a - f a * v) / (g a)^2) a",
    "exact hf.div hg hne",
)
add(
    "derivative_chain",
    ["f", "g", "a", "u", "v"],
    [deriv(f, ga, u), deriv(g, a, v)],
    deriv(lam(at(f, gx)), a, op("times", u, v)),
    "If g has derivative v at a and f has derivative u at g(a), then f ∘ g has derivative u*v at a.",
    "Compose the inner and outer first-order approximations at their correctly matched points.",
    [
        "Fix the inner point a and its image g(a).",
        "Use the derivative v of the inner function at a.",
        "Use the derivative u of the outer function at g(a).",
        "Compose the approximations by the chain rule.",
        "Multiply outer and inner slopes in that order.",
    ],
    "example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u (g a)) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f (g x)) (u * v) a",
    "exact hf.comp a hg",
)
add(
    "derivative_scalar_multiple",
    ["f", "a", "u", "c"],
    [deriv(f, a, u)],
    deriv(lam(op("times", c, fx)), a, op("times", c, u)),
    "Multiplication by any real constant c sends derivative u of f at a to derivative c*u of c*f at a.",
    "Multiply the derivative approximation and its remainder by the fixed scalar.",
    [
        "Fix f,a,u and an arbitrary real scalar c.",
        "Start from the derivative hypothesis for f.",
        "Multiply the first-order term by c.",
        "Use closure of little-o remainders under constant multiplication.",
        "Conclude the derivative is c*u, including c=0.",
    ],
    "example (f : ℝ → ℝ) (a u c : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => c * f x) (c * u) a",
    "exact hf.const_mul c",
)
add(
    "derivative_unique",
    ["f", "a", "u", "v"],
    [deriv(f, a, u), deriv(f, a, v)],
    rel("eq", u, v),
    "Two derivative values u and v of the same real function at the same point a are equal.",
    "Use uniqueness of the first-order derivative at a non-isolated point of the real line.",
    [
        "Fix one function f and one point a.",
        "Assume both u and v satisfy the derivative condition there.",
        "Apply uniqueness of the real derivative.",
        "Conclude u=v.",
    ],
    "example (f : ℝ → ℝ) (a u v : ℝ) (hu : HasDerivAt f u a) (hv : HasDerivAt f v a) : u = v",
    "exact hu.unique hv",
)
add(
    "derivative_implies_differentiable",
    ["f", "a", "u"],
    [deriv(f, a, u)],
    diff(f, a),
    "A real function with an explicit derivative value u at a is differentiable at a.",
    "Forget the specified slope while retaining existence of a derivative.",
    [
        "Fix f,a and its proposed derivative u.",
        "Use HasDerivAt as evidence of a first-order derivative.",
        "Retain existence while discarding the selected derivative value.",
        "Conclude differentiability at a.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : DifferentiableAt ℝ f a",
    "exact hf.differentiableAt",
)
add(
    "differentiable_implies_continuous",
    ["f", "a"],
    [diff(f, a)],
    cont(f, a),
    "Every real function differentiable at a is continuous at a.",
    "A first-order approximation tends to the function value as the increment tends to zero.",
    [
        "Fix a real function and evaluation point.",
        "Use differentiability at that point.",
        "Apply continuity of a differentiable map at its base point.",
        "Conclude continuity of f at a.",
    ],
    "example (f : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) : ContinuousAt f a",
    "exact hf.continuousAt",
)

for family, pred, lean_pred in [
    ("differentiable", diff, "DifferentiableAt ℝ"),
    ("continuous", cont, "ContinuousAt"),
]:
    for key, symbol, lean_symbol, method in [
        ("sum", "plus", "+", "add"),
        ("product", "times", "*", "mul"),
        ("quotient", "divide", "/", "div"),
    ]:
        premises = [pred(f, a), pred(g, a)] + (
            [rel("neq", ga, zero)] if key == "quotient" else []
        )
        extra = " (hne : g a ≠ 0)" if key == "quotient" else ""
        add(
            f"{family}_{key}",
            ["f", "g", "a"],
            premises,
            pred(lam(op(symbol, fx, gx)), a),
            f"If f and g are {family} at a"
            + (" and g(a) ≠ 0" if extra else "")
            + f", then x ↦ f(x) {lean_symbol} g(x) is {family} at a.",
            f"Apply the {key} closure rule for {family} real functions at one point.",
            [
                "Fix f,g and their common evaluation point a.",
                f"Use the assumed {family} property of f.",
                f"Use the assumed {family} property of g.",
            ]
            + (["Check the explicit nonzero value of g at a."] if extra else [])
            + [f"Apply the {key} rule and conclude the required pointwise property."],
            f"example (f g : ℝ → ℝ) (a : ℝ) (hf : {lean_pred} f a) (hg : {lean_pred} g a){extra} : {lean_pred} (fun x => f x {lean_symbol} g x) a",
            f"exact hf.{method} hg" + (" hne" if extra else ""),
        )
    add(
        f"{family}_composition",
        ["f", "g", "a"],
        [pred(f, ga), pred(g, a)],
        pred(lam(at(f, gx)), a),
        f"If g is {family} at a and f is {family} at g(a), then f ∘ g is {family} at a.",
        f"Compose {family} functions after matching the inner image to the outer base point.",
        [
            "Fix g at the point a.",
            "Identify the outer base point as g(a).",
            f"Use both {family} hypotheses at these respective points.",
            "Apply the composition rule.",
        ],
        f"example (f g : ℝ → ℝ) (a : ℝ) (hf : {lean_pred} f (g a)) (hg : {lean_pred} g a) : {lean_pred} (fun x => f (g x)) a",
        "exact hf.comp a hg" if family == "differentiable" else "exact hf.comp hg",
    )
    extra = family == "differentiable"
    add(
        f"{family}_absolute_value",
        ["f", "a"],
        [pred(f, a)] + ([rel("neq", fa, zero)] if extra else []),
        pred(lam(op("abs", fx)), a),
        f"If f is {family} at a"
        + (" and f(a) ≠ 0" if extra else "")
        + f", then |f| is {family} at a.",
        "Compose with absolute value, using the nonzero value to avoid its corner."
        if extra
        else "Compose with the globally continuous absolute-value map.",
        [
            "Fix f and its evaluation point.",
            f"Use the {family} hypothesis for f.",
            "Use f(a) ≠ 0 to avoid the corner of absolute value."
            if extra
            else "Use global continuity of the absolute-value map.",
            "Apply composition to conclude the result.",
        ],
        f"example (f : ℝ → ℝ) (a : ℝ) (hf : {lean_pred} f a)"
        + (" (hne : f a ≠ 0)" if extra else "")
        + f" : {lean_pred} (fun x => |f x|) a",
        "exact hf.abs hne" if extra else "exact hf.abs",
    )

for key, symbol, lean_symbol, method in [
    ("sum", "plus", "+", "add"),
    ("difference", "minus", "-", "sub"),
]:
    add(
        "interval_integrable_" + key,
        ["f", "g", "a", "b"],
        [integ(f, a, b), integ(g, a, b)],
        integ(lam(op(symbol, fx, gx)), a, b),
        f"If f and g are interval-integrable for real volume from a to b, then f {lean_symbol} g is interval-integrable from a to b.",
        f"Apply closure of interval integrability under {key}, with no ordering assumption on endpoints.",
        [
            "Fix arbitrary real endpoints a,b.",
            "Use interval integrability of f on those endpoints.",
            "Use interval integrability of g on the same endpoints.",
            f"Apply the integrability {key} rule.",
        ],
        f"example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f {volume} a b) (hg : IntervalIntegrable g {volume} a b) : IntervalIntegrable (fun x => f x {lean_symbol} g x) {volume} a b",
        f"exact hf.{method} hg",
    )
add(
    "interval_integrable_scalar_multiple",
    ["f", "a", "b", "c"],
    [integ(f, a, b)],
    integ(lam(op("times", c, fx)), a, b),
    "If f is interval-integrable for real volume from a to b, then c*f is interval-integrable for any real c.",
    "Constant multiplication preserves integrability on the underlying unordered interval.",
    [
        "Fix endpoints a,b and a real scalar c.",
        "Use the given interval integrability of f.",
        "Multiply by the fixed scalar c.",
        "Apply preservation of integrability under constant multiplication.",
    ],
    f"example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f {volume} a b) : IntervalIntegrable (fun x => c * f x) {volume} a b",
    "exact hf.const_mul c",
)
add(
    "interval_integrable_reverse",
    ["f", "a", "b"],
    [integ(f, a, b)],
    integ(f, b, a),
    "Interval integrability of a real function from a to b implies interval integrability from b to a.",
    "Reverse the endpoints; the underlying unordered integration interval is unchanged.",
    [
        "Fix arbitrary endpoints a,b.",
        "Use interval integrability on their unordered interval.",
        "Observe reversing endpoints preserves that interval.",
        "Conclude interval integrability from b to a.",
    ],
    f"example (f : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f {volume} a b) : IntervalIntegrable f {volume} b a",
    "exact hf.symm",
)
add(
    "interval_integrable_join",
    ["f", "a", "b", "c"],
    [integ(f, a, b), integ(f, b, c)],
    integ(f, a, c),
    "If f is interval-integrable from a to b and from b to c, then it is interval-integrable from a to c, for any real endpoints.",
    "Combine integrability across two intervals meeting at a common endpoint.",
    [
        "Fix arbitrary real endpoints a,b,c.",
        "Use integrability between a and b.",
        "Use integrability between b and c.",
        "Apply transitivity of interval integrability; no endpoint order is needed.",
    ],
    f"example (f : ℝ → ℝ) (a b c : ℝ) (hab : IntervalIntegrable f {volume} a b) (hbc : IntervalIntegrable f {volume} b c) : IntervalIntegrable f {volume} a c",
    "exact hab.trans hbc",
)
add(
    "continuous_implies_interval_integrable",
    ["f", "a", "b"],
    [bind("forall", [("x", "Real")], cont(f, x))],
    integ(f, a, b),
    "A real function continuous at every real point is interval-integrable for real volume between any real endpoints a,b.",
    "Convert pointwise continuity to global continuity and use integrability on compact intervals.",
    [
        "Fix f and arbitrary endpoints a,b.",
        "Assume continuity at every real point.",
        "Assemble global continuity from the pointwise hypothesis.",
        "Apply continuous-function interval integrability for real volume.",
    ],
    f"example (f : ℝ → ℝ) (a b : ℝ) (hf : ∀ x : ℝ, ContinuousAt f x) : IntervalIntegrable f {volume} a b",
    f"exact (continuous_iff_continuousAt.mpr hf).intervalIntegrable (μ := {volume}) a b",
)

# Four reusable normalization/base principles with arbitrary real parameters.
add(
    "derivative_affine_parameters",
    ["a", "b", "c"],
    [],
    deriv(lam(op("plus", op("times", b, x), c)), a, b),
    "For any real a,b,c, the affine function x ↦ b*x+c has derivative b at a.",
    "Differentiate the identity, scale by b, and add the constant c.",
    [
        "Fix arbitrary coefficients b,c and evaluation point a.",
        "Use derivative one of the identity function.",
        "Scale the derivative by b.",
        "Adding c leaves the derivative unchanged.",
    ],
    "example (a b c : ℝ) : HasDerivAt (fun x : ℝ => b * x + c) b a",
    "simpa using ((hasDerivAt_id (x := a)).const_mul b).add_const c",
)
add(
    "derivative_reciprocal_function",
    ["f", "a", "u"],
    [deriv(f, a, u), rel("neq", fa, zero)],
    deriv(
        lam(op("divide", integer(1), fx)),
        a,
        op("divide", op("unary_minus", u), op("power", fa, "<OMI>2</OMI>")),
    ),
    "If f has derivative u at a and f(a) ≠ 0, then 1/f has derivative -u/f(a)^2 at a.",
    "Compose f with inversion, whose derivative is defined at nonzero values.",
    [
        "Fix f,a,u satisfying the derivative hypothesis.",
        "Check f(a) ≠ 0.",
        "Apply differentiation of inversion composed with f.",
        "Rewrite inversion as division of one by f.",
    ],
    "example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) (hne : f a ≠ 0) : HasDerivAt (fun x => 1 / f x) (-u / (f a)^2) a",
    "have hfun : (fun x => 1 / f x) = f⁻¹ := by\n    funext x\n    exact one_div (f x)\n  rw [hfun]\n  exact hf.inv hne",
)
add(
    "interval_integrable_constant",
    ["a", "b", "c"],
    [],
    integ(lam(c), a, b),
    "Every real constant function c is interval-integrable for real volume between arbitrary real endpoints a,b.",
    "Use global continuity of a constant function and compact-interval integrability.",
    [
        "Fix arbitrary endpoints and a real constant c.",
        "The constant function is continuous everywhere.",
        "Restrict this continuity to the finite interval.",
        "Conclude interval integrability for real volume.",
    ],
    f"example (a b c : ℝ) : IntervalIntegrable (fun _ : ℝ => c) {volume} a b",
    f"exact continuous_const.intervalIntegrable (μ := {volume}) a b",
)
add(
    "continuous_epsilon_delta",
    ["f", "a"],
    [cont(f, a)],
    bind(
        "forall",
        [("u", "Real")],
        logic(
            "implies",
            rel("lt", zero, u),
            bind(
                "exists",
                [("v", "Real")],
                logic(
                    "and",
                    rel("lt", zero, v),
                    bind(
                        "forall",
                        [("x", "Real")],
                        logic(
                            "implies",
                            rel("lt", op("abs", op("minus", x, a)), v),
                            rel("lt", op("abs", op("minus", fx, fa)), u),
                        ),
                    ),
                ),
            ),
        ),
    ),
    "If f is continuous at a, then for every ε>0 there exists δ>0 such that |x-a|<δ implies |f(x)-f(a)|<ε for every real x.",
    "Expand metric continuity and identify real distance with absolute difference.",
    [
        "Fix f continuous at a.",
        "Take an arbitrary positive ε.",
        "Apply the metric characterization to obtain a positive δ.",
        "Rewrite distances on the real line as absolute differences.",
        "Apply the resulting bound for every x in the δ-neighborhood.",
    ],
    "example (f : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) : ∀ ε : ℝ, 0 < ε → ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |f x - f a| < ε",
    "intro ε hε\n  obtain ⟨δ, hδ, h⟩ := Metric.continuousAt_iff.mp hf ε hε\n  refine ⟨δ, hδ, ?_⟩\n  intro x hx\n  simpa only [Real.dist_eq] using h (by simpa only [Real.dist_eq] using hx)",
)


def main():
    ids = [c["id"] for c in cards]
    assert len(ids) == len(set(ids))
    assert len({c["openmath_xml"] for c in cards}) == len(cards)
    text = (
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
    WITNESS.write_text(text)
    result = subprocess.run(
        ["lake", "env", "lean", str(WITNESS)],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    manifest = json.loads((WORKSPACE / "lake-manifest.json").read_text())
    mathlib = next(p for p in manifest["packages"] if p["name"] == "mathlib")
    output = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": "typed-real-analysis-v1",
        "cards": cards,
        "evidence": {
            "witness_path": str(WITNESS.relative_to(ROOT)),
            "witness_sha256": "sha256:"
            + hashlib.sha256(WITNESS.read_bytes()).hexdigest(),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": mathlib["rev"],
            "validator_sha256": "sha256:"
            + hashlib.sha256(
                (ROOT / "pals-agent/pals_agent/typed_real_analysis.py").read_bytes()
            ).hexdigest(),
            "registry_sha256": "sha256:"
            + hashlib.sha256(
                (
                    ROOT
                    / "pals-agent/pals_agent/content_dictionaries/typed-real-analysis-v1-registry.json"
                ).read_bytes()
            ).hexdigest(),
        },
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"cards={len(cards)} openmath=validated lean=compiled output={OUTPUT}")


if __name__ == "__main__":
    main()
