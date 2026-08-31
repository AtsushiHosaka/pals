# typed-math-profile-v1 implementation tasks

1. Add isolated typed validation/canonicalization public entry points and
   explicit profile-mismatch rejection, including generic-only XML fixtures.
   (`TYPED-REQ-001`, `TYPED-REQ-004`)
2. Implement typed binder/annotation placement gates, lexical scopes, and the
   exact CD/symbol registry. (`TYPED-REQ-002`)
3. Add the versioned machine-readable CD registry; implement immutable sort
   expressions and bounded dependent inference for the group/ring core.
   (`TYPED-REQ-002`, `TYPED-REQ-003`)
4. Add group/ring positives plus profile, annotation, carrier, equality, and
   numeric-cast hard negatives. (`TYPED-REQ-001`–`004`)
5. Add polynomial signatures/fixtures and only bind a pinned Lean receipt after
   a card-specific statement/OpenMath/Lean review record passes. (`TYPED-REQ-003`, `TYPED-REQ-005`)
6. Add the limited Frechet subset, then the Fubini subset behind its own
   default-off feature flag, with complete signatures and alignment reviews.
   (`TYPED-REQ-003`, `TYPED-REQ-005`)
7. Implement the RFC 8785-canonical typed immutable manifest reader and exact
   UTF-8 evidence-digest binding; make the generic local loader reject typed
   manifests. (`TYPED-REQ-005`)
8. Run generic regression, typed positive/negative tests, canonicalization
   stability checks, and all pinned Lean receipt checks. (`TYPED-REQ-001`–`005`)
9. Do not insert typed cards into `public.dsp_drafts`; start a separate typed
   local generation only after the preceding gates pass. (`TYPED-REQ-005`)
