# Detached continuity pgvector validation

PFI-009 validates local pgvector storage and self-nearest-neighbour plumbing for the approved
110-card `continuity-v1` catalog. It loads every Draft-card field, including typed OpenMath,
retrieval prompts, Lean targets, proof strategy, Sketch, coverage, and novelty key, then verifies
the exact rows and deterministic test-vector self-nearest-neighbour results. It is not PFI catalog
publication, semantic retrieval, Lean verification, source-review evidence, or a release gate.

From the repository root, the only supported commands are:

```bash
python3 pals-scripts/continuity-pgvector-validation/run.py validate
python3 pals-scripts/continuity-pgvector-validation/run.py teardown
```

`validate` requires the locally cached `pgvector/pgvector:pg16` image. It starts only the fixed
networkless tmpfs Compose project and leaves it running for inspection. `teardown` removes only
that named project and remains available if the catalog or Spec inputs have changed afterwards.

The developer-invoked Docker integration test performs two clean source reloads and then tears
the fixture down:

```bash
bash pals-scripts/tests/continuity-pgvector-validation-integration.sh
```
