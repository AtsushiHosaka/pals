# Counting catalog candidates and usable mathematical problems

Working contract and partial implementation for [#193](https://github.com/AtsushiHosaka/pals/issues/193),
2026-11-04. Parent goal: [#139](https://github.com/AtsushiHosaka/pals/issues/139).
The baseline is the owner's request to inspect actual availability, the existing Recipe
admission/search contracts, and #193's acceptance criteria. This is not a canonical-spec
promotion or completion of #139.

## Counting definition

Keep three quantities separate:

1. **Candidate rows** are authoring records whose actual parser and deterministic source
   materializer accept them. This does not mean Lean compiled, review passed or admission occurred.
2. **Eligible published entries** must belong to the active generation/toolchain and selected
   language, be visible through the production selectable view, and pass the owning API's exact
   source/target/answer/compiler-receipt and independent review-signature checks. Retired and
   inactive rows, superseded publications and unauthenticated review claims do not qualify.
3. **Verified usable problems** additionally require actual retrieval and reuse evidence bound
   to that exact publication snapshot, source, target, toolchain and independently reviewed answer.
   An entry existing in a search table does not establish this result.

The canonical target byte hash in the owning API is exact target-source UTF-8 hashing. A
`lean-proposition-v1:<target hash>` key groups byte-identical target text across Recipe IDs
and revisions. An operational key also includes the toolchain fingerprint. The same target
text can denote different propositions under different imported definitions or bindings.
Neither identical text nor a different toolchain alone establishes mathematical identity.

These groups are syntactic. Bound-variable renaming, logically equivalent propositions,
different encodings, and Draft/Recipe representations may still duplicate the same problem.
There is no universal semantic upper or lower bound implied by these text-group counts, and
they do not establish the 1,100-problem goal. A future reviewed semantic-equivalence map
must bind its decisions to exact input digests and preserve scope, hypotheses and requested tasks.

Unknown is JSON `null`, not zero. `counted_usable_count=0` means this audit admitted no evidence
into its usability count; it does not mean production contains zero usable problems.

## Implemented offline slice

`pals-scripts/audit-usable-catalog.py` inventories one explicitly selected directory of canonical
`pals.recipe-authoring-manifest.v1` JSON files. It uses the selected clean API repository's
`RecipeAuthoringManifestV1.parse`, `RecipeMaterializerV1.materialize`, and
`validate_materialized_recipe` directly. It does not copy or relax those contracts.

The report includes each card's ID/revision, exact source/target/toolchain hashes, text and
operational groups, local older/duplicate revision exclusions, and unverified publication/runtime
reasons. Conflicting contents for the same Recipe ID/revision fail the entire audit. Identical
duplicate files are labeled separately. All-history candidate groups and latest-candidate-only
groups have separate fields; historical revisions cannot shadow another current candidate.
Operational duplicate classification applies only within the exact toolchain fingerprint.

The API commit and admission-parser hash are pinned before code import. A cached module can
be reused only with its recorded import-time pin. Dirty sources or revision/parser changes at
the end of the audit fail closed, rather than labeling cached code with a newer checkout.
A canonical sorted
path/file-hash list pins the source snapshot; `--expected-snapshot-sha256` supports replay against
the same bytes. Re-reading contents and the path set rejects a collection changed during scanning.
Symlinks, empty collections, noncanonical input, unsupported lifecycle fields and parser failures
fail closed. Bounds are 10,000 files and 2 MiB per file.

No source, snapshot, DB or service is modified. The CLI writes JSON to stdout, uses no network,
reads no credentials, and prints only an error type on failure. Do not commit the generated report
or private source snapshots. It has no database flag or unsigned evidence-import format.

```bash
# Use the owning API's Python environment/dependencies; substitute its clean checkout path.
python pals-scripts/audit-usable-catalog.py \
  --api-repository /path/to/clean/pals-api \
  --authoring-directory pals-scripts/tests/fixtures/usable-catalog-authoring-v1 \
  > /tmp/recipe-candidate-inventory.json
```

The parent-owned two-manifest fixture directory is available without changing the parent
submodule pin. Both are exact canonical authoring inputs copied using `git show` from agent
commit `5fad25db1bf3fa87b4ea38517cf8a6d75ab6db00`, under
`testdata/requested-math-seeds-v1/publication/`:

| File | SHA-256 |
| --- | --- |
| `requested.rank_nullity.json` | `153e60c5d31f1f8154bbe68361b7f35e6bd768d3126ae2790eddc2b5bd7050be` |
| `requested.composite_injective_implies_first.json` | `642b8563404ffb75fc6aa17872b3aee4852eefde365201b91bc6fcb82cc10df8` |

These are actual authoring inputs, not verification receipts or invented publication evidence.
The default test suite parses these two files and checks their identities; it does not depend on
the newer agent dataset being present in the parent-pinned `pals-agent` revision.
It also pins both fixture file hashes above. The parent-pinned API
`8bb38aa27e4670b4195c334210e414029c2fcebe` accepts both through its actual parser and
materializer: two candidates, two current candidates, two target-text groups and two operational
groups, with verified usability still `null`. This two-file snapshot has SHA-256
`c300149ece7c1ab4bea8fc642aaeb6b36befecf9a3840297e1fba29fedb7738c`.

A separate observed 20-manifest execution on 2026-11-04 JST used API commit
`e547a1f0fa8ed2f985cef9aa078b4e64ca75f0f3` and the existing requested seed manifests:

| Quantity | Result |
| --- | ---: |
| Parser/materializer-valid candidate rows | 20 |
| All-history exact-target-text groups / operational groups | 20 / 20 |
| Latest unique candidate rows / target-text groups / operational groups | 20 / 20 / 20 |
| Eligible published entries | not checked (`null`) |
| Verified usable problems | not checked (`null`) |
| Rows counted as usable | 0 |

Snapshot SHA-256: `ff3a8c3c51acfd88d29afae77dca7ef3b1aee834e6050292d01378353cb9995d`.
Admission-parser SHA-256: `64f6eb778ef125d19f41d9111ce9752271401d38923dc5daa236b926fc60d6df`.
The 20 offline manifests are not a reproduction of the historical 20 published Recipes: the
populations and evidence are different. This optional dataset is in agent commit
`5fad25db1bf3fa87b4ea38517cf8a6d75ab6db00` at
`testdata/requested-math-seeds-v1/publication/`; it is absent from the parent's older agent pin.
To reproduce that separate measurement, explicitly supply a checkout/export of that source
directory. No compiler or model ran in either audit.

## Remaining work before #193 can close

- Add an authenticated read-only snapshot adapter which captures the actual production
  selectable views and configured active toolchain in one consistent observation, then runs
  the owning API's `checked_recipe` validation. Never substitute unsigned boolean fields for
  review signatures, compiler receipts, publication lifecycle or current runtime authority.
- Bind actual retrieval/reuse observations to that snapshot and relevant language; expose
  excluded card IDs and reasons. A verified publication is still not a verified reused problem.
- Add Draft and typed-generation adapters and reviewed cross-representation equivalence;
  exclude inactive typed generations and unreleased vocabulary.
- Reconcile historical counts against dated observations. The November 2 report described
  Draft 433, published Recipe IDs 20, typed rows 35/active generations 0. The fresh November 4
  aggregate observation in [the learning-context report](learning-context-policy-2026-11-04.md)
  found 33 search entries/20 IDs across toolchains but 13 Japanese current-toolchain rows.
  This offline tool neither reproduces nor authenticates those DB observations.

Tests exercise the real parser/materializer, duplicate target text, conflicting identities,
older/duplicate local revisions, old-target shadowing, differing toolchains, checker provenance,
unreviewed authoring, rejection of true/false lifecycle assertions, source restrictions,
snapshot mismatch, noncanonical data, empty collections and symlinks. They establish offline
inventory policy only. Inactive typed-generation and live cryptographic/retrieval checks remain
unimplemented and unverified; #193 must stay open.
