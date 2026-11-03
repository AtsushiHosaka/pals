# Learning context, angle units, and catalog readiness

Working implementation record, 2026-11-04. Tracks [#183](https://github.com/AtsushiHosaka/pals/issues/183)
and the owner's [angle/context decision #224](https://github.com/AtsushiHosaka/pals/issues/224).
Session: `codex://threads/01a1a258-3e8e-7aa0-b2f0-6a2c91477ba8`.
Implementation: draft [pals-agent#45](https://github.com/AtsushiHosaka/pals-agent/pull/45),
initial commit `80c61b5b21b26b28e75b332efbcdc2a292c8de5a`, updated by prerequisite correction
`272dd3a355702430dd238a651bc433dc0d792f53`. No deployment or committed parent
submodule-pin update is included in this documentation change.

## Implemented contract

The explicit unit request takes priority. Otherwise elementary/lower-secondary problems and
degree-based school courses use degrees; other problems retain explicit units, with radians
as the general default. Language does not identify a country, curriculum, age or grade.
Conversions preserve exact quantities, including the scaling of trigonometric derivatives.
The occurrence of pi in an area or length is not a radian-unit instruction.

Explanations respect stated prior knowledge and within-course prerequisites. An unfamiliar
auxiliary result must be derived from available tools or introduced explicitly. If the requested
tools are insufficient, the answer must expose that limitation rather than silently assuming a
later theorem, changing a definition or using a circular argument. This applies to university
problems too, without inventing one universal university course sequence.

The agent has one shared policy and a versioned trusted reference registry. Sources are pinned
in `pals_agent/curriculum_guidance.py`:

| Profile | Scope and primary references |
| --- | --- |
| JP-MEXT | MEXT 2017 lower-secondary and 2018 upper-secondary commentary: [lower-secondary](https://www.mext.go.jp/component/a_menu/education/micro_detail/__icsFiles/afieldfile/2019/03/18/1387018_004.pdf), [upper-secondary](https://www.mext.go.jp/content/20230217-mxt_kyoiku02-100002620_05.pdf). |
| GB-ENG-NC | England's national curriculum, including degree-based KS4 trigonometry; not a UK-wide profile: [official programme](https://www.gov.uk/government/publications/national-curriculum-in-england-mathematics-programmes-of-study/national-curriculum-in-england-mathematics-programmes-of-study). |
| US-CCSS | Common Core only when identified; not all US curricula: [grade 4 measurement](https://www.thecorestandards.org/Math/Content/4/MD/), [high-school trigonometric functions](https://www.thecorestandards.org/Math/Content/HSF/TF/). |

These are partial source-backed summaries, not complete national syllabuses. An explicit account
of the learner's prior study takes priority. An unknown curriculum is not fabricated; ask for
course/textbook context only when it materially affects the solution.

## Runtime wiring and preservation

- Shared task interpretation preserves unit, level and method constraints during preflight and
  Draft generation. Chat intent extraction is also instructed to retain them.
- Formal explanations, clarifications and their independent reviewers use the same policy.
- Ordinary concept explanations and their reviewer receive it too.
- Both semantic-batch and search-based stored-answer reviews check the verbatim answer's units
  and prerequisites. Equivalent mathematical targets alone do not establish suitable exposition.
  A mismatch uses the existing miss/DSP route; sealed answers are never edited in place.
- Existing immutable originating-chat bindings retain the request across asynchronous proof
  delivery, clarification and retry. Confirmed material propositions remain exact.
- Lean targets, source excerpts, compiler/axiom checks, admission signatures, stored answer bytes,
  public schemas and existing feature entry points are preserved. Advanced internal Lean lemmas
  do not by themselves violate a beginner-facing explanation's prerequisites.

This is prompt-based enforcement plus existing independent review. It is not a deterministic
validator of educational suitability. No learner-profile database or unsupported-country
curriculum is fabricated. The source references and policy add prompt input; latency and cost
impact are unmeasured.

## Verification

Implementation base: agent `5fad25d` (remote main); parent `3abed58`.
Local checks use the existing Python environment, with `PYTHONPATH` pointing at this checkout.

```text
python -m pytest tests/unit/test_curriculum_guidance.py tests/unit/test_learning_policy.py
  tests/unit/test_explanations.py tests/unit/test_generator.py tests/unit/test_chat_runtime.py
  tests/unit/test_recipe_semantic.py tests/unit/test_linked_chat.py
  tests/unit/test_proof_reuse.py tests/unit/test_recipe_exact_input.py
346 passed in 2.50s
ruff check [all changed Python files]: passed
git diff --check: passed
```

The existing semantic prompt golden hashes were intentionally updated after qualifying the
unit-equivalence rule and adding the shared policy. JSON schema and role hashes remain intact.
The initial run had 249 passes and one golden-prompt mismatch; the final run above includes
the corrected prompt hashes. These are regression checks, not model-compliance evidence.

Independent static review found one conflicting old unit-equivalence instruction, repaired by
separating target equivalence from presentation requirements. A suspected material-context loss
was withdrawn after tracing the immutable linked-chat source through public runtime paths.

`tools/evaluate_learning_policy.py` provides eight real-model probes with a separate judge:
Japanese lower-secondary geometry, explicit degrees, explicit school-level radians, general
radian default, England GCSE degrees, pi in sector area, university prerequisites, and no
language-to-curriculum inference. It has no mock client, compiler bypass, automatic retry or
credential-file loader. Automatic approval review initially rejected the credential-backed paid
probe. The owner subsequently authorized API evaluations expected to cost less than $1 in total;
an evaluation expected to reach $1 requires advance confirmation. This is not deployment or
publication authorization.

The first real two-call v1 probe was rejected by the independent judge: it used induction for a
Japanese junior-high polygon problem and asserted an invalid arbitrary-diagonal decomposition.
The source-backed registry was revised to v2: mathematical induction belongs to upper-secondary
Math B, not an assumed junior-high prerequisite. A general-n claim need not use induction when
direct decomposition suffices. The official upper-secondary source above supports that placement.

| Run | Cases approved | Calls | Input / output tokens | Pinned-rate upper-bound estimate |
| --- | ---: | ---: | ---: | ---: |
| v1 junior-high probe | 0 / 1 | 2 | 3,715 / 1,398 | $0.001163375 |
| v2 full probe set | 6 / 8 | 16 | 29,358 / 7,281 | $0.007310250 |

The total estimate is $0.008473625, using the repository's conservative Luna snapshot of
$0.125/million input tokens and $0.50/million output tokens, with no cache discount. This is not
an invoice. Usage is recorded for every call; no model, compiler or transport was replaced.
The two runs are different populations and must not be treated as an accuracy improvement.

The v2 passes cover explicit degrees, explicit school-level radians, the unspecified radian
default, England GCSE degrees, preserving pi in a sector area, and a university kernel proof
without rank-nullity. Two Drafts remain rejected: the junior-high polygon answer misdescribes
the angle partition at non-fan vertices; the sine-derivative answer uses an undeclared auxiliary
inequality instead of deriving it from the requested starting facts. These are actual rejected
raw Drafts, not successfully verified/released answers. No criterion was relaxed to pass them.
The final v2 unit check is 346 passed in 2.60s. Full production E2E, stored-answer orchestration,
latency impact, deployment and educational outcomes remain **not verified**. Agent#45 stays draft.

## Catalog audit: quantity is not availability

Independent local inspection of draft [pals-agent#27](https://github.com/AtsushiHosaka/pals-agent/pull/27),
head `b9db8d5245097b6b7cf29292a70e93f50e9b7d29`, found **2,480 generated cards across 45 domains**,
with matching manifest, Draft-candidate and search-candidate counts. Index SHA-256:
`a3fe6bfeea9e8635504209411472416922fb82c72f157a059fccfa8f648d91ca`.
The PR body still describes the earlier 1,062-card batch. This is an offline candidate inventory,
not a production count. Its README explicitly lacks AWS admission, DB insertion, embedding,
signed publication and runtime retrieval evidence for the batch.

Draft eligibility is 450 new generic candidates, one existing duplicate, and 2,029 requiring
unpublished vocabulary. Another 486 nonempty cards exist in concurrent untracked university
YAML files and are absent from generated artifacts; they are not counted as compiled or ready.
An additional functional-analysis YAML file is empty. These concurrent files were not edited.

All 2,480 narrow-import records match their generated source hashes. Of these, 2,464 adopted
narrow imports; ten statement-type differences and six compile failures retain `import Mathlib`.
These are sufficient-import results, not proof of minimality. Admitted materialization still uses
`import Mathlib`, so offline import trimming does not prove production compile-time improvement.

Two representative commutative-algebra cards were independently recompiled on the pinned
Lean 4.32.0-rc1 / Mathlib `8b62164d` workspace, using their recorded narrow imports:

| Card | Imports | Result | Wall time |
| --- | --- | --- | ---: |
| `prime_avoidance` | `Mathlib.RingTheory.Ideal.Operations`, `Mathlib.Tactic.SetNotationForOrder` | exit 0; allowed axioms only | 9.16 s |
| `radical_of_product_and_intersection` | `Mathlib.RingTheory.Ideal.Operations` | exit 0; allowed axioms only | 7.05 s |

Command: `lake env lean <temporary source constructed from the recorded imports and exact
generated lean_code>`, followed by the source's axiom report. Both used only `propext`,
`Classical.choice`, and `Quot.sound`; provider cost was zero. Temporary sources were removed.
This two-card replay does not independently validate the full 2,480-card batch or all prose.

## Production observation and next work

Fresh AWS read-only aggregate observation at **2026-11-04 02:06:45 JST**:

| Category | Observed count |
| --- | ---: |
| Natural Draft rows / rows with embeddings | 433 / 433 |
| Approved Draft additions | 0 |
| Admitted Recipe revisions / distinct Recipe IDs | 206 / 102 |
| Admitted revisions matching the active toolchain / IDs | 102 / 102 |
| Selectable search entries across toolchains / distinct IDs | 33 / 20 |
| Selectable entries matching the active toolchain / IDs / target hashes | 13 / 13 / 13 |
| Languages of those 13 active-toolchain entries | Japanese only |
| Typed rows / generations / active generations | 35 / 4 / 0 |
| Admitted revisions containing `import Mathlib` | 206 |

These categories overlap and must not be summed. The historical
[November 2 count](aws-recipe-semantic-benchmark-2026-11-02.md) of 20 searchable Recipes must
not be presented as 20 currently usable active-toolchain entries. The fresh count of 13 measures
eligibility only; signature revalidation, actual retrieval and successful reuse were not run.
The concurrent release may affect counts, so this is a timestamped observation, not a stable
capacity promise.

The observer used existing AWS SSO and SSM to inspect the existing API instance, validate the
current admitted release and unchanged container identity, and run aggregate SELECTs in a
read-only repeatable-read TLS database session. It did not change the DB or service lifecycle
and read zero chat/history rows. No hostnames, credentials or personal data are published.
Release manifest SHA-256:
`fc702c2375024ba81e2f8d34f34ab6bcf0efd1867e8aa16bd99d972589fb9095`.
Active toolchain SHA-256:
`eb9f9cafef74a0d426e86f804e30884c93ee0840eee3b007f208a29a2a384de7`.
Observer SHA-256:
`f771ddb1234fc10c8193f9a70b1f066781e02e018850684e7e17b4245b9f8d5f`.
The aggregate results are also recorded in [#183](https://github.com/AtsushiHosaka/pals/issues/183).
The historical/current eligibility difference is also recorded in
[#139](https://github.com/AtsushiHosaka/pals/issues/139). Local owning API source `e547a1f`
filters both language and toolchain; the deployed reader source hash and live view definitions
were not independently compared. Reproducible aggregate predicates (bind the observed active
toolchain hash as the parameter):

```sql
SELECT count(*), count(embedding) FROM public.dsp_drafts;
SELECT count(*), count(DISTINCT recipe_id)
FROM pals_local_lean_recipe_catalog.selectable_recipe_revisions;
SELECT count(*), count(DISTINCT recipe_id)
FROM pals_recipe_search.selectable_entries;
SELECT output_language, count(*), count(DISTINCT recipe_id),
       count(DISTINCT target_c14n_sha256)
FROM pals_recipe_search.selectable_entries
WHERE toolchain_sha256 = %s
GROUP BY output_language ORDER BY output_language;
```

Existing unmerged work must be integrated rather than duplicated:
[agent#26](https://github.com/AtsushiHosaka/pals-agent/pull/26) replaces the 32-entry search cap,
[agent#32](https://github.com/AtsushiHosaka/pals-agent/pull/32) improves semantic-scope review,
and draft [agent#33](https://github.com/AtsushiHosaka/pals-agent/pull/33) handles sentence
retrieval and sealed vocabulary. Their existence is not production evidence.

The immediate priority is reviewing and admitting existing pedagogically suitable candidates,
then proving actual retrieval/reuse coverage. Additional beginner proofs and prerequisite/unit
metadata are more useful than indiscriminate count growth. Candidate gaps by generated card-ID
inspection include sheaves, stalks, schemes, singular homology, depth and regular local rings;
this is not a complete semantic coverage audit. Check concurrent drafts before adding them.
The older #186 commutative-algebra gap list is stale: the newer generated 148-card domain already
includes prime avoidance, local-global principles, determinant tricks, integrality transitivity,
heights and regular sequences.

## Remaining #183 decisions

No area-definition or convexity-definition change, home-stage reclassification, mass card rewrite,
or choice of separate advanced cards versus `proof_method_tag` is approved by the angle decision.
Existing advanced proofs are preserved. Those decisions and a full university ordering audit
remain open; #183 must not be closed as fully implemented by this slice.
