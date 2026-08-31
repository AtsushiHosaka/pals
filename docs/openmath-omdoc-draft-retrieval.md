# OpenMath Draft Retrieval

## Decision

PALS stores only the data required to identify, retrieve, and apply a reusable
Draft. The `dsp_drafts` table has six columns:

| Column | Purpose |
| --- | --- |
| `id` | stable Draft identity |
| `canonical_statement` | human-readable theorem statement |
| `openmath_xml` | validated semantic representation of the theorem |
| `proof_strategy` | reusable natural-language proof plan |
| `sketch_steps` | ordered Draft/Sketch steps |
| `embedding` | pgvector representation of canonical OpenMath |

Lean statements, OMDoc wrappers, required Lean fragments, aliases, provenance
labels, lifecycle status, counters, timestamps, and duplicated search documents
are not Draft data and are not persisted in this table. Lean remains a generated
and independently verified artifact, not a retrieval key or trusted harness.

The embedding fingerprint is stored once in
`pals_agent_draft_catalog_metadata`. It is operational compatibility metadata,
not Draft content. Vector search fails closed if provider, model, endpoint,
deployment, revision, dimension, or canonicalizer differs from the stored
fingerprint.

## Runtime Path

```text
natural-language statement
  -> OpenMath structuring role (code-owned gpt-5.4)
  -> validated and alpha-canonical OpenMath 2 XML
  -> OpenMath embedding
  -> pgvector top-k candidates
  -> OpenMath structural reranking
  -> reusable proof strategy and sketch
  -> prove / compile / repair pipeline
```

There is no exact-text, seed-only, alias, or local-only retrieval shortcut.
Malformed or semantically inconsistent OpenMath is an explicit retrieval error.

The final score is 40% vector similarity and 60% OpenMath structural
similarity. Structural comparison covers symbols, node kinds, literals,
argument positions, operator shape, and subtree shape. Similarity selects useful
context; it does not establish theorem equivalence.

## Seed Coverage

The packaged catalog currently contains 31 Drafts: continuity examples spanning
direct Lipschitz estimates, powers and polynomials, absolute-value forms, rational
functions with positive denominators, and rank-nullity.

Three records carry distinct epsilon-delta constructions:

| Draft id | Main construction |
| --- | --- |
| `continuous_affine` | split `a = 0`; otherwise choose `delta = epsilon / abs(a)` |
| `continuous_absolute_value` | choose `delta = epsilon`; use reverse triangle inequality |
| `continuous_reciprocal_nonzero` | keep the denominator away from zero with a local bound |

Every seed passes the same natural-language/OpenMath semantic validator used for
runtime structuring before it can be embedded or persisted.

## Precision Baseline

Removing the retired fields does not change the retrieval input or scoring
formula: both were already OpenMath-only. The expected result is therefore equal
ranking quality with a smaller schema, not an artificial precision increase.

The deterministic retrieval suite covers general power versus square exponent
shape, all three retained epsilon-delta families, approximate cubic-to-square
behavior, threshold handling, and embedding fingerprint failures. The
pre-restoration five-family run is historical only and is not current source or
release evidence.

Future precision reports must preserve the exact natural-language query and its
reviewed canonical OpenMath, and report Hit@1, Recall@5, MRR, score margin, false
positive rate, and OpenMath structuring success separately.

## Migration

Schema version `20260711_minimal_openmath_draft_v5` removes the retired columns
in place. Existing non-active rows make migration fail closed because dropping
`status` must not silently reactivate quarantined data. Existing custom rows are
retained; a fingerprint change is refused until every retained custom row is
explicitly re-embedded.

The separate `pals-draft-admin` application is read-only. Its list shows Draft
identity and canonical statement; details show the OpenMath statement, proof
strategy, and sketch steps. Database credentials remain server-side.
