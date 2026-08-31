# `typed-probability-v1` design

## Status and decision

This document preserves and revises the earlier local design at
`/private/tmp/pals_probability_profile_v1_design.md`.  It is a **design-only**
proposal: it changes neither the generic validator, the base typed-math
implementation, any manifest, nor the Draft DB.

Probability cannot enter generic-v1 merely by adding `pals1:probability` or
`pals1:variance`.  Generic validation checks XML shape, symbol role, arity,
and a coarse term/proposition distinction; it cannot establish that an event,
measure, and random variable share the same sample space.  Such an extension
would accept semantically ill-typed statements.

Adopt a sibling profile instead:

```text
profile id: typed-probability-v1
typed CD base: urn:pals:openmath:typed-math:v1
profile-local proposed CD: probability1
```

`typed-probability-v1` reuses the `typed1:forall` / `typed1:exists` binders,
`OMATTR(typed1:type, SortExpr)` declarations, XML resource limits, exact-sort
equality rule, canonicalizer, Lean receipt contract, and profile isolation
defined by [the base typed-math design](pals-typed-math-v1-minimal-design.md).
It does **not** add probability symbols to generic-v1 or to the base
`typed-math-v1` group/ring profile.

The previous design's `pals1:forall_event`-style implicit binders are replaced
by the base typed binder plus dependent `SortExpr`.  This avoids a parallel
typed-binding convention and makes the sample-space dependency explicit in
every `OMBVAR` declaration.

## Profile boundary

| Selected profile | Accepted CD subset | Explicitly rejected |
| --- | --- | --- |
| `generic-v1` | Existing generic allow-list only | `typed1:*`, `probability1:*`, and typed `OMATTR` declarations |
| `typed-math-v1` | Base `typed1` plus its admitted group/ring modules | `probability1:*`; a probability document is not a base typed-math document |
| `typed-probability-v1` | `typed1`, `probability1`, exact `logic1`/`relation1`, and the profile's scalar arithmetic subset | generic `quant1`/`fns1`, unregistered `algebra1`/`analysis1`/`measure1` symbols, and unknown CDs |

The caller supplies `openmath_profile`; XML content must never auto-select a
profile.  A profile mismatch fails before embedding, persistence, Lean receipt
creation, or release preparation.  Canonical bytes are valid only after the
selected profile's validator succeeds.

`typed-probability-v1` is intentionally a sibling rather than an append-only
base typed-math module: group/ring admission must not make probability
operators available, and probability hard negatives must not expand the
group/ring core's trusted surface.

## Scope and mathematical convention

The first probability slice covers the 17 authored candidates currently marked
`requires_pals_probability_profile_v1` in
[`probability-ode-draft-candidates.json`](probability-ode-draft-candidates.json):

- six natural-number binomial-coefficient identities;
- four conditional-probability identities;
- three variance identities and one constant-expectation identity;
- three binomial-PMF identities.

The first sample-space slice permits one active sample-space declaration in a
closed statement.  This is sufficient for these cards and prevents accidental
mixing of `Event(Ω)` with `ProbabilityMeasure(Ω₂)`.  Product spaces,
independence across two spaces, Markov kernels, conditional expectation,
densities/CDFs, general finite-set element sorts, and product measures are
out of scope.

### Probability values

For the introductory/probability-measure statements, the XML meaning is a
`Probability` value in `[0,1]`, with an explicit conversion to `Real` before
real arithmetic.  The profile deliberately does not silently identify this
with Mathlib's `ENNReal` measure values.

This exposes a real issue in the old 17-card Lean witnesses: the four
conditional-probability witnesses use `Measure Ω` and `ENNReal`, while the
binomial witnesses use a real-valued mass expression.  They are useful
preliminary witnesses, but are **not** evidence that one common typed XML
semantics has been reviewed.  Conditional cards require a fresh lowering
review (typically through a verified `ENNReal.toReal` bridge with its finite
and nonzero premises), or they remain proposed.

For v1's ordinary division formulas, conditioning events have strictly
positive probability.  `conditional_probability` is therefore treated as a
partial mathematical notion at card level: every formula containing its
quotient expansion must state its required nonzero denominator premises.  Do
not rely on a totalized-zero convention to erase those premises.

## Sorts

`Probability` is not implicitly a `Real`; `Nat` is not implicitly a `Real`.
All cross-sort arithmetic uses an explicit operator.  This follows the base
typed-math rule that forbids coercion search and makes Lean lowering reviewable.

| SortExpr | Meaning | v1 status |
| --- | --- | --- |
| `typed1:Nat` | Natural number | admitted |
| `typed1:Real` | Real scalar | admitted |
| `probability1:Probability` | Scalar probability in `[0,1]` | admitted |
| `probability1:SampleSpace` | A carrier with its fixed measurable structure | admitted |
| `probability1:Event(Ω)` | Measurable event on `Ω` | admitted |
| `probability1:ProbabilityMeasure(Ω)` | Total-mass-one probability measure on `Ω` | admitted |
| `probability1:RealRandomVariable(Ω)` | Measurable `Ω → ℝ` random variable | admitted |
| `probability1:DistributionNat` | Distribution on natural-number outcomes | admitted for binomial cards |
| `probability1:FiniteMeasure(Ω)` | Finite measure on `Ω` | deferred: needed only by the old, broader conditional-card wording |
| `probability1:FiniteSet` | Opaque finite set | deferred: no typed element/cardinality API in this slice |

Annotations may refer only to an outer or preceding declaration in the same
`OMBVAR`.  Thus `μ : ProbabilityMeasure(Ω)` and `S : Event(Ω)` are well
formed only after `Ω : SampleSpace` is bound.  A second `SampleSpace` binder
in one closed v1 statement is rejected.  This restriction is not a general
limitation of dependent sorts; it is a deliberate v1 boundary.

### Typed binder example

The base `typed1` form expresses all dependencies; there is no
`forall_event` special binder.

```xml
<OMBIND>
  <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
  <OMBVAR>
    <OMATTR><OMATP>
      <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
      <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="SampleSpace"/>
    </OMATP><OMV name="Omega"/></OMATTR>
    <OMATTR><OMATP>
      <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
      <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="ProbabilityMeasure"/><OMV name="Omega"/></OMA>
    </OMATP><OMV name="mu"/></OMATTR>
    <OMATTR><OMATP>
      <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
      <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="Event"/><OMV name="Omega"/></OMA>
    </OMATP><OMV name="S"/></OMATTR>
  </OMBVAR>
  <!-- Prop body -->
</OMBIND>
```

## Exact v1 signature set

The type checker uses exact signatures.  `relation1:eq` requires identical
inferred sorts, and all `logic1:*` arguments must infer to `Prop`.

### Naturals and explicit scalar conversion

| Symbol | Signature | Decision |
| --- | --- | --- |
| `probability1:nat_add` | `Nat × Nat → Nat` | `choose`/Pascal arithmetic |
| `probability1:nat_sub` | `Nat × Nat → Nat` | Truncated natural subtraction |
| `probability1:nat_div` | `Nat × Nat → Nat` | Truncated natural division; used by `choose(n,2)` |
| `probability1:choose` | `Nat × Nat → Nat` | Total, with `choose(n,k)=0` for `k>n` |
| `probability1:nat_to_real` | `Nat → Real` | Required in real-valued PMF formulas |
| `probability1:real_of_int` | `OMI → Real` | Only finite integer literals |
| `probability1:prob_to_real` | `Probability → Real` | Required before real arithmetic |
| `probability1:real_add/mul/sub/div` | homogeneous `Real` operations | `real_div` requires a nonzero denominator premise in any quotient theorem |
| `probability1:real_pow_nat` | `Real × Nat → Real` | Used by binomial and variance formulas |

### Events, measures, and random variables

| Symbol | Signature | Required card-level condition |
| --- | --- | --- |
| `probability1:event_intersection` | `Event(Ω) × Event(Ω) → Event(Ω)` | Same exact `Ω` |
| `probability1:probability` | `ProbabilityMeasure(Ω) × Event(Ω) → Probability` | Same exact `Ω` |
| `probability1:conditional_probability` | `ProbabilityMeasure(Ω) × Event(Ω) × Event(Ω) → Probability` | Arguments are `(mu, target, given)`; any quotient identity records nonzero `P(given)` |
| `probability1:integrable` | `RealRandomVariable(Ω) × ProbabilityMeasure(Ω) → Prop` | Required for an expectation claim unless a profile rule derives it |
| `probability1:square_integrable` | `RealRandomVariable(Ω) × ProbabilityMeasure(Ω) → Prop` | Required for a variance claim |
| `probability1:expectation` | `RealRandomVariable(Ω) × ProbabilityMeasure(Ω) → Real` | Integrability review required |
| `probability1:variance` | `RealRandomVariable(Ω) × ProbabilityMeasure(Ω) → Real` | Square-integrability review required |
| `probability1:constant_rv` | `SampleSpace × Real → RealRandomVariable(Ω)` | The explicit `Ω` avoids an ambient-space ambiguity |
| `probability1:rv_add_constant` | `RealRandomVariable(Ω) × Real → RealRandomVariable(Ω)` | Same exact `Ω` |
| `probability1:rv_scale` | `Real × RealRandomVariable(Ω) → RealRandomVariable(Ω)` | Same exact `Ω` |

### Binomial distribution

| Symbol | Signature |
| --- | --- |
| `probability1:binomial_distribution` | `Nat × Probability → DistributionNat` |
| `probability1:pmf` | `DistributionNat × Nat → Probability` |

The real-valued binomial mass expression is constructed only after applying
`prob_to_real` to the PMF and parameter and `nat_to_real` to `choose(n,k)`.
No real literal, raw natural literal, or `Probability` term may enter a
`Real` operator without that explicit conversion.

## Complete conditional-probability positive shape

The following is the core shape for the reviewed statement
`P(T | S) = P(S ∩ T) / P(S)`, including the nonzero denominator premise.  It
uses the binder declaration convention above; all `probability1:*` symbols
have cdbase `urn:pals:openmath:typed-math:v1`.

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">
  <OMBIND>
    <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
    <OMBVAR>
      <OMATTR><OMATP><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="SampleSpace"/></OMATP><OMV name="Omega"/></OMATTR>
      <OMATTR><OMATP><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/><OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="ProbabilityMeasure"/><OMV name="Omega"/></OMA></OMATP><OMV name="mu"/></OMATTR>
      <OMATTR><OMATP><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/><OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="Event"/><OMV name="Omega"/></OMA></OMATP><OMV name="S"/></OMATTR>
      <OMATTR><OMATP><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/><OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="Event"/><OMV name="Omega"/></OMA></OMATP><OMV name="T"/></OMATTR>
    </OMBVAR>
    <OMA><OMS cd="logic1" name="implies"/>
      <OMA><OMS cd="relation1" name="neq"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="prob_to_real"/>
          <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="probability"/><OMV name="mu"/><OMV name="S"/></OMA>
        </OMA>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="real_of_int"/><OMI>0</OMI></OMA>
      </OMA>
      <OMA><OMS cd="relation1" name="eq"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="prob_to_real"/>
          <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="conditional_probability"/><OMV name="mu"/><OMV name="T"/><OMV name="S"/></OMA>
        </OMA>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="real_div"/>
          <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="prob_to_real"/>
            <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="probability"/><OMV name="mu"/>
              <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="event_intersection"/><OMV name="S"/><OMV name="T"/></OMA>
            </OMA>
          </OMA>
          <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="prob_to_real"/><OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="probability1" name="probability"/><OMV name="mu"/><OMV name="S"/></OMA></OMA>
        </OMA>
      </OMA>
    </OMA>
  </OMBIND>
</OMOBJ>
```

## Validator and test plan

Implement a separate `typed_probability_profile.py` only after the base typed
profile is available.  It reuses the base XML parser, typed declaration gate,
lexical sort environment, exact C14N helper, and resource limits; it must not
mutate generic `_SUPPORTED_SYMBOLS` or base typed-math's fixed registry.

The probability validator adds `Probability1SortExpr` parsing and bottom-up
signature inference.  It rejects a type mismatch at the first offending
operator, argument index, expected/actual sort, and binder path.

Minimum positive fixtures:

1. The conditional-probability shape above.
2. Pascal's identity with only `Nat` operations.
3. Variance scaling with an explicit `square_integrable(X,mu)` premise.
4. Binomial PMF with explicit `Probability → Real` and `Nat → Real` casts.
5. Alpha-renamed copies of each fixture with identical canonical bytes.

Required hard negatives:

| Invalid intent | Required rejection |
| --- | --- |
| `Event(Omega2)` supplied to `probability(mu : ProbabilityMeasure(Omega), ...)` | carrier mismatch |
| A second sample space declaration in a closed v1 statement | v1 multiple-sample-space gate |
| `probability(S,mu)` | argument 1 must be `ProbabilityMeasure(Omega)` |
| `choose(p,k)` with `p : Probability` | argument 1 must be `Nat` |
| Binomial distribution with `p : Real` | argument 2 must be `Probability` |
| `real_mul(p,...)` with `p : Probability` | explicit `prob_to_real` required |
| `expectation(X,mu)` conclusion without reviewed integrability support | missing integrability premise/derivation |
| `variance(X,mu)` conclusion without `square_integrable(X,mu)` | missing square-integrability premise |
| Conditional quotient formula without `P(S) != 0` | missing denominator premise |
| `OMI 0` directly compared to `Real` or used in `Real` arithmetic | `real_of_int` required |
| `quant1:forall`, `fns1:lambda`, or an `OMATTR` outside declared `OMBVAR` | typed profile gate |
| `probability1:*` sent to generic-v1 or base typed-math-v1 | profile/CD gate |

## Typed manifest and evidence

Probability cards use an immutable, profile-specific manifest; they do not go
through `ProofDraft`, `prepare-local-draft-batch.py`, the six-column
`dsp_drafts` loader, or a generic retrieval generation.

Each `pals.typed-probability-v1.manifest.v1` record must contain at least:

- `id`, `source_candidate_id`, `openmath_profile = typed-probability-v1`;
- reviewed `canonical_statement`, exact typed canonical XML, and their hashes;
- `probability1_cd_bundle_sha256`, validator version, and canonicalizer version;
- exact Lean target and witness hashes, pinned toolchain digest, and a
  `status = verified` compiler receipt digest;
- a reviewed statement/OpenMath/Lean alignment record;
- an assumptions-and-conventions record: probability codomain lowering,
  denominator/nonzero requirements, integrability source, and any source-card
  wording change.

The embedding/fingerprint preimage contains at least
`typed-probability-v1 || canonical_xml`.  Typed probability rows have a
profile-separated catalog, endpoint, embedding namespace, and retrieval index.
They may not be mixed with generic-v1 or base typed-math-v1 candidates in a
single generation.

## Review matrix for the existing 17 candidates

Every row below is a blocking semantic-review checklist, not a statement that
the old XML or Lean witness is already admitted.  “Rewrite” means regenerate
typed XML and a matching Lean witness; do not merely relabel the old XML.

| Source card | Typed XML mapping | Blocking review items |
| --- | --- | --- |
| `prob_choose_zero` | `n : Nat`; `choose(n, OMI 0) = OMI 1` | Confirm literals are `Nat`, no real cast is introduced, and the Lean target is exactly `Nat.choose n 0 = 1`. |
| `prob_choose_self` | `n : Nat`; `choose(n,n) = 1` | Confirm both uses of `n` share the same `Nat` binding and the result literal is `Nat`. |
| `prob_choose_one` | `n : Nat`; `choose(n,1) = n` | Confirm boundary convention `choose(n,1)` for `n=0` agrees with the Lean theorem. |
| `prob_choose_pascal` | `n,k : Nat`; `choose(nat_add(n,1),nat_add(k,1)) = nat_add(choose(n,k),choose(n,nat_add(k,1)))` | Confirm successor syntax, all additions are natural addition, and the candidate retains no hidden `k≤n` premise. |
| `prob_choose_symmetry` | `n,k : Nat`; premise `k≤n`; `choose(n,nat_sub(n,k))=choose(n,k)` | Preserve truncated natural subtraction and the explicit `k≤n` premise needed by the cited Lean theorem. |
| `prob_choose_two` | `n : Nat`; `choose(n,2)=nat_div(nat_mul(n,nat_sub(n,1)),2)` | Do not map `/` to real division. Confirm the theorem is natural truncated division and that both literal `2`s are natural. |
| `prob_conditional_definition` | `Omega`, `mu : ProbabilityMeasure(Omega)`, `S,T : Event(Omega)`; quotient form with `P(S)≠0` | Replace old independent `finite_measure`/`measurable_event` predicates with dependent sorts; confirm `(mu,target,given)` order; select and prove the Real/`ENNReal.toReal` lowering. |
| `prob_conditional_self` | Same scope; `P(S)≠0 → P(S\|S)=1` | Replace “positive finite probability” with the exact probability-measure/nonzero conditions; confirm no `∞` premise remains under the selected lowering. |
| `prob_conditional_multiplication_rule` | Same scope; `P(T\|S)·P(S)=P(S∩T)` | Decide whether the operator is partial or total outside positive conditioning. If totality is not proved in the selected lowering, add `P(S)≠0`; verify event-intersection order. |
| `prob_bayes_formula` | Same scope; Bayes quotient with explicit denominator assumptions | The old wording omits denominator conditions. Add and review at least `P(S)≠0`; under the ordinary conditional definition also require `P(T)≠0` before writing `P(S\|T)`. Rebuild the Lean target accordingly. |
| `prob_variance_nonnegative` | `Omega`, `mu : ProbabilityMeasure(Omega)`, `X : RealRandomVariable(Omega)`; `square_integrable(X,mu) → 0≤variance(X,mu)` | Tighten from untyped/general finite measure; use `real_of_int(0)`; identify the exact Mathlib variance and integrability theorem. |
| `prob_variance_scaling` | Add `c : Real`; `variance(rv_scale(c,X),mu)=real_mul(real_pow_nat(c,2),variance(X,mu))` | Require square integrability and same `Omega`; ensure `c^2` is real-power-by-natural, not a generic power; review whether Mathlib's theorem needs a stronger measurability premise. |
| `prob_variance_translation` | Add `c : Real`; `variance(rv_add_constant(X,c),mu)=variance(X,mu)` | Require source square integrability or prove its preservation; retain `ProbabilityMeasure(Omega)`; align the Lean `AEStronglyMeasurable` hypothesis with typed `RealRandomVariable`. |
| `prob_expectation_constant` | `Omega`, `mu : ProbabilityMeasure(Omega)`, `c : Real`; `expectation(constant_rv(Omega,c),mu)=c` | Record the derivation that a constant is integrable under a probability measure, rather than silently omitting integrability; align integral codomain and normalization `mu(univ)=1`. |
| `prob_binomial_pmf` | `n,k : Nat`, `p : Probability`; `prob_to_real(pmf(binomial_distribution(n,p),k))` equals the explicitly cast real binomial expression | Remove separate `0≤p≤1` premises because the sort carries them; require `nat_to_real(choose(n,k))`, `prob_to_real(p)`, `real_of_int(1)`, and real power-by-natural; review `k>n` convention. |
| `prob_binomial_zero_success` | `n : Nat`, `p : Probability`; real PMF at `0` equals `real_pow_nat(1-p,n)` | Confirm PMF codomain conversion and zero-success `Nat` literal; re-prove against the exact distribution lowering. |
| `prob_binomial_all_success` | `n : Nat`, `p : Probability`; real PMF at `n` equals `real_pow_nat(prob_to_real(p),n)` | Confirm the outcome is the same `Nat n`, PMF is converted exactly once, and the Lean witness uses the reviewed binomial model. |

No row becomes publishable until all its blocking items are recorded as
approved in its immutable manifest evidence.  The old `pals1` predicate XML
remains an authoring proposal and is not a typed-profile input.

## Ordered rollout

1. Complete the base `typed-math-v1` parser, declaration gate, exact C14N,
   profile dispatch, and group/ring hard-negative suite.  Do not broaden the
   base registry for probability.
2. Add the typed-manifest and receipt infrastructure required by
   `TYPED-REQ-005`, still with only local fixtures and no DB publication.
3. Implement `typed-probability-v1` sort parsing and the isolated
   `probability1` CD gate; admit only sort/signature positive and negative
   fixtures.
4. Admit the six `choose` cards after their Nat-only XML/Lean alignment
   reviews.  They do not depend on sample-space semantics.
5. Resolve the Probability-to-Real/Mathlib-`ENNReal` lowering and conditional
   convention before admitting any of the four conditional cards.
6. Add integrability derivation rules and exact Lean lowerings before the
   variance and expectation cards.
7. Add binomial distribution/PMF plus explicit casts, then review the three
   binomial cards.
8. Only after complete card receipts, introduce a profile-separated local
   fixture catalog and retrieval experiment.  Shared/prod DB insertion and
   generic catalog migration remain out of scope.

At every step, generic-v1 canonical fixtures, the base typed-math group/ring
fixtures, seed digests, and profile-mismatch tests are regression gates.
