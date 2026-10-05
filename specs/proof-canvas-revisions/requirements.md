# One evolving proof with quoted follow-ups

Status: IMPLEMENTED — authorized by the user's 2026-10-05 request and clarification: retain the selected range, keep quoted question history, and update only the requested part of one displayed proof, as in a Canvas. Validated implementation branches are pushed; the running application has not been redeployed.

| ID | Requirement |
| --- | --- |
| PCR-001 | Focusing the question field must keep the selected proof range identifiable. The composer and saved user message show the exact selected source as a rendered quotation, including math. |
| PCR-002 | Sending moves the question into the conversation immediately. Accepted requests close the floating field; pending, failed and completed states appear beside their saved question. Rejected submissions retain the draft and quote, with no automatic redispatch. A busy-section rejection keeps the draft inline rather than hovering over the proof. |
| PCR-003 | A successful selected-proof follow-up produces a replacement for the selected excerpt. The worker derives the updated section by an exact splice. Both replacement and complete revised section must pass the independent review bound to the original verified theorem, source, selected text and parent context. Longer and shorter replacements are allowed. |
| PCR-004 | Display the proof once, using the latest reviewed section revisions. Preserve unselected source text exactly. Quoted user turns and brief assistant replies remain below the proof in saved chronological order; do not duplicate revised proof sections as assistant messages. |
| PCR-005 | Selecting updated proof prose, including updated and untouched text together, must target the current saved revision. API admission and atomic settlement reject stale parents, concurrent branch revisions, ambiguous repeated excerpts and off-target splices. Failed or unreviewed output cannot alter the proof. |
| PCR-006 | Reload reconstructs the same proof and question history from stored completed revisions. Keep the initial proof and review provenance immutable. Legacy supplemental answers remain readable and selectable. Owner/chat/proof changes keep the existing observation isolation. |
| PCR-007 | Newly created shared snapshots include the current reviewed proof and quoted question history, including proof jobs linked to proof requests. Existing published snapshots remain frozen. Invalid or unreviewed revisions cannot change shared proof content. |

The current selection contract covers one explanation section at a time and up to 800 selected source code points. A repeated excerpt must include enough surrounding text to identify one occurrence. Editing theorem premises or the formal claim still requires a new proof request.
