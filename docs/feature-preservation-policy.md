# Preserve existing features

The user requires explicit approval before an existing feature is removed, disabled, hidden, or made inaccessible. This policy applies across PALS and its implementation submodules.

A request to simplify a screen, change its appearance, refactor code, merge a pull request, or deploy a release does not authorize removing features. Preserve each capability and a usable entry point unless the user explicitly approves its removal.

Before removal, describe the exact feature, affected screens, and user impact, then ask for approval. Limit any approved removal to the named feature. If a release contains an unapproved removal, preserve the feature or hold that part of the release while requesting approval.

For example, simplifying Project home must preserve file upload, file listing, and access to existing materials. Removing an upload panel without providing another usable entry point removes the feature even if its backend API still exists.

This rule was requested on October 12, 2026, after Project materials upload was found missing from the deployed interface.

## Selected-answer follow-up questions

Selecting answer text or mathematical notation by dragging and releasing must retain
an accessible follow-up question form in guest and authenticated chats, including
catalog-backed answers and reviewed explanations. Keep the exact original TeX in
the quote, preserve the question after failed submission, and keep quota and
idempotency checks. Restyling, definition popovers, and new answer renderers must
not bypass this entry point. Do not remove it without explicit user approval.

Release checks must include the webfront guest-answer-selection,
proof-request-selection, proof-selection, and guest-chat regression suites.
