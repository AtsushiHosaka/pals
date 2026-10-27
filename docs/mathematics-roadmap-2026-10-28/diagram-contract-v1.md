# Inline diagram contract v1 (WORKING)

T3 owns transport/schema files. MRD-004/005/010; parent base ca84e6f,
API 25a5faf, frontend 020f688. This contract authorizes a bounded implementation,
not a claim of mathematical verification or deployment. Producer T2 can consume
this contract without editing transport files.

`ProofExplanationContent.diagrams` is optional, defaults to [], maximum 4.
Nonempty diagrams are included in the existing reviewed output digest and JSONB
persistence. Empty lists are omitted from that digest for historical compatibility.
Each diagram is a closed object with `schema_version: "pals.diagram.v1"`, unique
`id` (ASCII letter followed by at most 39 ASCII letters/digits/underscores),
`kind: "geometry" | "commutative"`, `alt` (1–1000 plain Unicode characters),
and `evidence_refs` (at most 16 closed objects with `claim_id` (same ID grammar),
`source_sha256` (64 lowercase hex), `declaration` (1–160 ASCII Lean name characters)).
References are supplied claims; render success never checks or admits them.

Geometry adds `points` (1–32 `{id,label,x,y,role}`), `segments` (0–64
`{id,start,end,role}`), `circles` (0–16 `{id,center,radius,role}`). Coordinates
are finite numbers in [-10,10], radii in (0,10]. All coordinates/radii are
**display only**, never hypotheses. `role` is `given`, `derived`, or
`display_only`; derived constructions still need separate proof evidence.
IDs are unique across primitives; references resolve to point IDs.

Commutative adds `objects` (1–16 `{id,label,row,column}`), `arrows` (0–32
`{id,start,end,label}`). Rows/columns are integers 0–3, cells unique, endpoints
resolve, self arrows excluded in v1. Arrows may be diagonal. No relation is
certified by a picture. Empty labels are allowed on arrows only.

Labels are at most 80 ASCII characters, with balanced braces (depth <=4),
letters/digits/spaces and `_^{}()+-=,./:|` plus a finite command allowlist:
`alpha beta gamma delta epsilon theta lambda mu pi rho sigma tau phi psi omega
Gamma Delta Theta Lambda Pi Sigma Phi Psi Omega mathbb mathrm mathcal operatorname
bar overline hat tilde prime circ times otimes oplus infty partial nabla`.
No dollar signs, percent, ampersand, newline, arbitrary commands, paths, styles,
imports, HTML, SVG, URLs, TeX documents or raw code are accepted.

Owner-scoped `GET /v1/proof-jobs/{job}/explanation/diagrams/{id}/render` renders
only a persisted diagram from a completed accessible explanation. Response is
`{schema_version: "pals.diagram-render.v1", diagram_id, source, source_sha256,
image_png_base64, width, height}`. Source is generated deterministically from
the accepted object, is a complete TikZ/tikz-cd document, and can be copied or
saved as .tex. Failures return 503; existing prose/source controls remain usable.
Frontend shows “Illustration; rendering does not verify mathematical claims.”
Evidence references remain inspectable, without a verified badge.

The API calls a dedicated configured render service; it does not run TeX or
receive a Docker socket. The trusted supervisor accepts declarative JSON, builds
source itself, and runs one credential-free pinned image without host mounts,
network, shell escape or privilege; bounded stdin/stdout/deadline/memory/CPU/PIDs,
a temporary capped work filesystem, output signature/dimension/size checks and
forced container cleanup apply. Missing worker configuration fails honestly.

Initial acceptance examples: an isosceles triangle with midpoint and altitude;
a quotient vector-space square induced by a linear map preserving a subspace.
Their display coordinates and rendering are not proof evidence. Real DB,
provider, browser, reload and deployed verification remain separate checks.
