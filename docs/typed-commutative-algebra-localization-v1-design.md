# typed-commutative-algebra-localization-v1

## Purpose and boundary

`typed-commutative-algebra-localization-v1` is an isolated OpenMath profile for
the elementary ideal theory of a localization of a commutative ring.  It has a
different cdbase from `typed-commutative-algebra-v1`; it does not relax or
reinterpret that earlier ideal-lattice profile.

The profile represents four dependent carriers explicitly:

- `R : CommRing`;
- `M : Submonoid(R)`;
- `L : Localization(R,M)`;
- ideals and elements over either `R` or the particular localized ring `L`.

`loc_map(R,M,L,x)`, `extend(R,M,L,I)`, and `contract(R,M,L,J)` record their
source and target carriers in every occurrence.  `Localization(R,M)` is a
typed authoring assertion that `L` is the chosen localization carrier; the
sealed Lean receipt independently binds the statement to parameters with
`[Algebra R L] [IsLocalization M L]`.  This is not an OpenMath-to-Lean
translation claim.

## Included v1 core

The core is deliberately restricted to statements that use only a single
commutative ring, one submonoid, and its localization:

- algebra-map preservation of `0`, `1`, addition, and multiplication;
- denominators from `M` becoming units;
- membership tests for the extension of an ideal;
- monotonicity and the Galois inequalities for extension and contraction;
- the equality `extend(contract(J))=J`, order reflection, lattice operations,
  radical commutation, and the properness/prime-ideal correspondence.

All propositions are closed, use direct typed cdbases, and are rejected if a
submonoid, localization, ideal, or element is attached to the wrong carrier.
The profile allows only `forall`, equality, `and`, `or`, `implies`, and
`equivalent` at proposition level.  It does not silently infer a missing
membership proof for a denominator: `SubmonoidElem(R,M)` is a distinct sort.

## Hard rejects and deferrals

The following are rejected rather than represented by a weak predicate:

- a localization whose base ring or submonoid is not explicit;
- a ring homomorphism between two unrelated localizations;
- fraction fields, quotients, modules, localized modules, tensor products,
  spectra, local rings, and stalks;
- localization in which a denominator is merely an `Elem(R)` rather than a
  `SubmonoidElem(R,M)`;
- localization-specific claims that need an unexpressed hypothesis such as
  injectivity, disjointness, primality, finite generation, or Noetherianness.

Those require separate dependent profiles and corresponding Lean evidence.

## Evidence and admission

The sealed proposal records exact source XML and C14N-v4 XML, their hashes,
the design, registry, validator, pinned Lean toolchain, and a local witness
bundle.  Every candidate has 4--8 proof-sketch steps and a local alignment
review.  The proposal is not a generic Draft, PFI seed, embedding index, or
database row.  It remains not admitted until independent project review.
