# T3 inline diagram implementation evidence

2026-10-28 JST. WORKING implementation of MRD-004/005/010, scoped by
[diagram-contract-v1.md](diagram-contract-v1.md). Runtime acceptance remains
incomplete; neither a security pass nor deployment readiness is claimed.

## Revisions and review

| Repository | Refreshed base | Proposed revision | Draft review |
| --- | --- | --- | --- |
| pals | ca84e6fe1a87fa019368f16e4af8c7cbec759a82 | This branch; gitlinks below | Parent T3 PR |
| pals-api | 25a5faf81753b14a85a13ab0a254708790de9b94 | e8c71a730dbb721a6d91817a5dbc56164d8466b6 | [API #26](https://github.com/AtsushiHosaka/pals-api/pull/26) |
| pals-webfront | 020f688497d51c82553be45e5947dd95a9ab711f | 2e41313f9ada09febc47b45c3f11b14115a9add8 | [Frontend #26](https://github.com/AtsushiHosaka/pals-webfront/pull/26) |

Both child revisions were pushed before parent gitlink updates. No merge,
release, repository-visibility change, catalog admission or deployment occurred.
The shared primary checkout and its existing changes were not edited. Only
API/frontend submodules were initialized in a task-owned managed worktree.

## Actual changes

- Closed versioned geometry and commutative models bound IDs, primitive counts,
  coordinates, roles, labels and supplied evidence references. Coordinates and
  radii are display-only. A finite macro subset excludes arbitrary TeX/HTML/SVG,
  paths, styles, imports and TeX `^^` character escapes.
- Existing explanation JSONB serialization retains optional diagrams. Nonempty
  diagrams participate in the reviewed output digest; absent/empty diagrams keep
  historical hashes and public response shapes. No database migration is needed
  for this additive JSONB payload. Live PostgreSQL persistence is unverified.
- Owner-scoped source and render GET routes load only completed, accessible
  explanations. Source generation is independent of worker availability.
- The ordinary API calls an authenticated literal-loopback supervisor only, with
  no redirects, proxy inheritance or compressed responses. It bounds transport,
  regenerates source for exact comparison, checks its digest and fully decodes
  PNG output. It does not receive a Docker socket or execute TeX.
- A separate supervisor generates deterministic TikZ/tikz-cd and defines a
  credential-free immutable-image worker: no host mounts/network/shell escape,
  read-only root, non-root UID, capability drop, resource limits, bounded pipes
  and deadlines, full PNG decoding, labeled cleanup with absence readback, and
  a circuit breaker after unconfirmed cleanup. Dockerfile package inputs still
  require build provenance/pinning review. These controls have not run in Docker.
- Normal chat explanations show inline PNGs with accessible descriptions,
  explicit illustration status, textual geometry roles/legend, and unverified
  evidence disclosure. TikZ copy/download survives render failure. Source/render
  mismatch, failed images and malformed diagram metadata retain ordinary prose
  and existing source/clarification controls. Shared-snapshot diagram rendering
  and the T2 producer integration remain outside this completed code slice.
- Acceptance inputs depict an isosceles triangle with midpoint/altitude and an
  induced quotient-vector-space square. These are substantive rendering inputs,
  not checked proofs or evidence of admitted mathematical support.

## Executed checks

API: **227 passed, 2 skipped**, 12 dependency deprecation warnings, 15.47 seconds.
The two skipped cases explicitly require a real configured diagram supervisor.
Run from the API repository with its normal Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m pytest tests/test_explanation_diagrams.py tests/unit/test_diagram_render_client.py tests/unit/test_diagram_contract.py tests/test_pex_path_codec.py tests/test_proof_explanations.py tests/test_proof_explanation_openapi.py tests/unit/test_proof_explanation_schema.py tests/unit/test_postgres_proof_explanations.py tests/unit/test_diagram_renderer.py tests/unit/test_diagram_worker_boundary.py tests/integration/test_diagram_worker_runtime.py -o addopts='' -q -p no:cacheprovider
```

This includes real task-owned subprocess output-overflow, timeout, cancellation
and exited-parent descendant termination probes; schema/malicious-input checks;
PNG corruption/source checks; owner/auth/failure routes and existing explanation
regressions. Repository/HTTP test doubles isolate boundaries and do not prove a
real database, TeX renderer, provider, browser or deployment integration.

Strict mypy passed seven changed production source files; targeted Ruff,
`python scripts/generate_openapi.py --check`, and whitespace checks passed.
Frontend: **126 files / 1,594 unit tests passed**, TypeScript typecheck,
changed-file ESLint and whitespace checks passed. Full suite command was
`npm run test:unit`; the added source/render tests are in
`tests/unit/inline-diagrams.test.tsx`.

Independent read-only sandbox/architecture review found and remediation tests
covered output-drain deadlock/repeated kill, corrupt PNG acceptance, descendant
cleanup, unconfirmed Docker cleanup, and inaccessible role presentation. The
combined regression run also found an empty-stdin child-exit race; the helper
now drains stdin only when bytes are actually supplied. No remaining material
ownership defect was identified in source review. This is not an isolation pass.

Inspected runtime: Python 3.12.13; FastAPI 0.140.2; Starlette 1.3.1; Pydantic
2.13.4; HTTPX 0.28.1; Next 16.2.9; React 19.2.7. Pydantic>=2.12 is now explicit
because historical empty-field omission uses `exclude_if`; locked2.13.4 did not
change. No new application stack/container was launched. Frontend dependencies
were temporarily reused via a task-owned symlink, then the symlink was removed.

## Missing evidence and continuation

The existing OrbStack Docker socket did not respond to a bounded five-second
`/_ping` request (curl exit28); inventory commands were interrupted after no
output. No worker image was built, no container was created, and no actual TeX
render was obtained. A bundled Tectonic executable exists, but its mere presence
was not treated as an isolated execution boundary or replacement runtime proof.
Existing services were not restarted.

1. Restore a responsive existing Docker daemon. Build/review/pin the worker
   image and follow `pals-api/worker/diagram-renderer/README.md`. Run the two
   opt-in real-worker tests and inspect the actual geometry/square PNGs/source.
2. Verify containment with harmless host sentinels, denied network/host writes,
   memory/CPU/PID/file bounds, failure cleanup and final labeled-container
   inventory. A configured flag or unit test is not this evidence.
3. Integrate the T2 diagram producer using this contract without editing T3
   transport files. Bind actual checked geometry/equality/CommSq evidence through
   the owning verifier; rendering does not validate supplied references.
4. Exercise an actual owner-authenticated API and PostgreSQL write/read/reload,
   then real desktop/mobile browser display, accessible interactions, TikZ
   copy/download/source consistency, reload, honest failure and all existing
   explanation/Lean-source/clarification controls. No provider/DB/browser pass
   was obtained here. Add shared-snapshot rendering only with its access policy.
5. Review the local-only loopback transport before a split-container/cloud
   deployment. The automatic approval review rejected arbitrary external
   forwarding; this implementation instead restricts the destination to local
   literal loopback origins. No external renderer data transfer occurred.

All review PRs remain draft until the relevant real acceptance evidence exists.
