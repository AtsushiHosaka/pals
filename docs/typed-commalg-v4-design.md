# Prime spectra, integral extensions and dimension: commalg-v4

`typed-commalg-v4` is an independent authoring-only profile. Its initial batch has 33 general theorems: 15 about zero loci and Zariski topology, 7 about spectrum maps and localization/quotients, 8 about integral extensions and going down, and 3 about Krull dimension. The language and pinned evidence do not modify or activate any previous runtime profile. The batch is validated and compiled locally; retrieval selection, XML-to-Lean translation and publication are separate capabilities, not claims of this work.

## Mathematical novelty audit

The six existing v1 commutative-algebra manifests and the ideal-reuse, modules-v2 and commalg-v3 batches were inspected. Their ideal arithmetic, elementary integral-element closure, valuation-ring closure, module quotients, tensor/Hom and chain-condition statements are not repeated here. Existing ideal-localization statements cover extension/contraction and prime disjointness, but not the induced Zariski topology. This batch therefore proves topological embedding/open embedding and nil-quotient homeomorphism rather than recopying ideal correspondence.

Going up, lying over, incomparability, maximal-ideal transport, normal-domain and flat going down, the polynomial dimension formula and local dimension/height are new represented capabilities. These results are related, but have different conclusions or materially different hypotheses. The batch does not multiply the number of cards by renaming variables, fixing a numerical exponent or repeating symmetric versions. In particular, no separate card is counted for the special case that the spectrum itself is quasi-compact once basic-open quasi-compactness is available.

Completion, adic topology, general dimension equality for integral extensions, principal ideal/height bounds, finite presentation and arbitrary indexed spectrum constructions remain outside this batch. No textbook-completeness claim is made.

## Dependent carriers and exact semantics

The cdbase is `urn:pals:openmath:typed-commalg:v4`, with `typed1` binders and the closed `spectrum4` symbol inventory. Every proposition has explicit quantification. The registry documents each symbol's ordered signature and mathematical/Lean meaning; its schema, complete symbol set and entry shapes are independently fixed in the executable validator.

A `CommRing` binder introduces a new ring identity. An `Algebra(R)` binder introduces a new commutative ring S **with a specified R-algebra structure**. Its base-ring identity is retained, so another bound base cannot silently supply an algebra structure. `Ideal(R)`, `Element(R)`, `Prime(R)`, `SpecSet(R)` and `Submonoid(R)` all retain R. `Prime(R)` is `PrimeSpectrum R`, including its prime-ideal proof, while an `Ideal(R)` needs an explicit `is_prime` hypothesis when a theorem requires primality.

`RingHom(R,S)` retains both rings. Its induced `spec_comap(R,S,f)` has type `SpecMap(S,R)`, reversing direction. Thus `continuous(S,R,spec_comap(R,S,f))` is correctly typed, and the forward-direction variant is rejected. Extension takes an ideal of R to S; contraction takes an ideal of S to R; spectrum preimage takes a subset of Spec R to one of Spec S. Their operand slots cannot be exchanged.

Constructed ring carriers `quotient(R,I)`, `localization(R,M)`, `away(R,x)`, `at_prime(R,p)` and `polynomial(R)` retain their exact operands. Changing the ideal, multiplicative subset, element or prime changes the carrier. They cannot be forged as independent binder sorts. Canonical maps have these exact constructed targets. No equality of ring declarations or implicit transport between different carriers is admitted.

`zero_locus(R,I)` means primes containing I; `vanishing_ideal(R,T)` is the intersection of the primes in T; `basic_open(R,x)` means primes not containing x. `closure`, `is_closed`, `is_clopen`, `is_compact` and `is_irreducible` use the Zariski topology. Compact here means quasi-compact and does not assert Hausdorffness. Irreducibility includes nonemptiness. `idempotent` means x*x=x, and uniqueness in the clopen card is restricted to idempotents.

`integral(R,S)` is `Algebra.IsIntegral R S`; `ring_integral(R,S,f)` is `f.IsIntegral`. `flat(R,S)` is `Module.Flat R S` for the specified algebra. These are mathematical properties, not opaque theorem-name predicates. The language does not define a going-down predicate that merely hides the theorem: the going-down conclusion explicitly quantifies the lower prime, its inclusion, primality and contraction equation.

`dimension(R)` is `ringKrullDim R : WithBot ℕ∞`. The zero ring has dimension ⊥ and infinite dimension is allowed. `height(R,I)` explicitly coerces `I.height` from ℕ∞ to this same dimension type. `dimension_successor(d)` is d+1 in WithBot ℕ∞, so neither the polynomial formula nor local dimension/height presupposes finite dimension.

## Material assumptions

- Lying over for **every** base prime requires an injective integral ring map.
- Going up needs integrality and prime ideals with contraction(J)⊆I; it does not additionally require injectivity.
- Incomparability keeps the smaller ideal prime; the larger ideal need not itself be prime in the strengthened compiled statement.
- Maximality equivalence keeps the upstairs ideal prime and the map integral.
- A proper ideal remains proper under an integral map when it contains the map's kernel; this permits noninjective maps while retaining the necessary obstruction.
- Normal-domain going down explicitly assumes both rings are domains, the base is integrally closed, the extension is integral and its algebra map injective. Injectivity is converted to `FaithfulSMul` only within the witness.
- Flat going down explicitly assumes `Module.Flat R S`, with no integrality or domain claim. Both going-down cards also retain both downstairs primality proofs, upstairs primality, contraction equality and ideal inclusion.
- The polynomial dimension formula keeps Noetherianity. The local dimension/height formula needs only a prime of the base ring.

## Validation, evidence and limits

The validator enforces bound variables, unique binders, exact arities, namespaces/cdbases/attributes, parent structure, and dependent carrier compatibility. Limits are 65,536 UTF-8 bytes, 4,096 nodes, depth 64, 1–256 declarations per binder, and 2–32 arguments for conjunction/disjunction. The full symbol set is fail-closed even if the registry file is extended. Canonical validation compares exact alpha-normalized XML bytes.

The generator constructs the exact anonymous-example Lean bundle, runs the existing pinned Lean/Mathlib workspace with a 180-second timeout and emits JSON only after success. Evidence pins the witness, validator and registry SHA-256 hashes, actual toolchain and actual mathlib revision. Type validation proves well-formedness, and Lean compilation proves the Lean statements; alignment among natural text, XML and Lean still requires independent semantic review.

The unit suite checks cross-ring ideals/points/subsets/elements, algebra base mismatches, contravariant spectrum maps, extension/contraction/preimage slots, forged constructed carriers, mismatched quotient/localization targets, bad scopes and arities, registry drift, resource bounds and critical theorem assumptions. The negative dataset gives concrete mathematical counterexamples, including explicit failures of going down without injectivity, domain target or normal base. These negatives cover every card but have not been evaluated through runtime retrieval.
