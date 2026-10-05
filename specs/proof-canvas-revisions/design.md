# Reviewed section revisions

Clarifications remain the durable aggregate. Their JSON content adds an optional pair: `replacement_text` (1–4000 code points) and `revised_section` (1–12000). Legacy payloads omit both, preserving their canonical hashes. Revised answers may be brief; legacy detailed answers retain their 40-character minimum. No database migration is required.

The worker obtains the current source from the original section or the parent's `revised_section`. It requires one exact selected occurrence, generates a replacement, and derives the full section with a single splice. The separate reviewer sees both resulting texts and their surrounding proof context. Content and context hashes include revision fields when present. Settlement independently checks the splice and latest parent under the existing explanation lock. A stale candidate cannot overwrite another completed revision.

The frontend replays only completed revisions whose parent matches the currently displayed section and whose complete text matches the exact splice. It renders one revised section with the saved revision ID as selection provenance. Its CSS Custom Highlight retains a cloned DOM range independently of textarea focus. Unsupported browsers still show the quotation. The composer disappears during dispatch; a rejected request restores its question and quotation. A busy-section rejection renders this draft inline. Saved question bubbles and brief responses follow the proof in transcript order.

New share projections replay the same exact section splices and additionally verify stored output, parent and Lean review hashes. Linked proof jobs must match both request owner and chat. The existing flat shared-message DTO contains one final proof, quoted questions and brief confirmations. Already published snapshots retain their frozen content and digest.

The Lean source remains the original verified source. Revised prose is independently reviewed against that theorem; it is not a new Lean compilation. The reviewer receives the original other sections and the current selected section. Replacements must preserve the same claims and remain coherent with that context.
