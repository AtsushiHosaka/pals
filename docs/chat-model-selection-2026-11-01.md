# Explicit model selection in chat

The composer lets the user select GPT-6.1 Terra, GPT-6.1 Sol or GPT-6 Luna, with
Low, Medium or High reasoning. The default is Terra Medium. This applies to new
Lean Draft, Sketch, Prove and Repair calls. It does not add automatic model
fallback. Existing explanation, intent and independent review roles retain their
configured models. Reusing an already verified Recipe may not call the selected
Lean generator at all.

The native, keyboard-accessible dropdown appears in guest chat, public landing,
home, project chats and projectless chats. Public drafts carry the selected pair
through navigation. Browser storage contains only a validated preference; the
server remains responsible for supported choices, request ownership and usage.

New requests send both `generation_model` and `generation_reasoning_effort`.
The API persists effort in an immutable per-request settings table. Historical
requests with no effort retain their previous behavior. Premise continuations,
repair attempts, checkpoint restoration and retries do not change the submitted
pair. A guest's failed send retains its settings and idempotency key even when
the composer preference later changes.

Paid token quotes bind the selected pair into the exact request. Existing
server-side usage records and versioned model prices determine utilization-token
consumption. Output tokens already include reasoning tokens, which are not added
again. The existing price estimator conservatively includes cache-write upper
bounds; it is not an exact provider invoice. The anonymous three-request daily
preview remains unchanged. No client-supplied price, multiplier or balance is
trusted.

The additional table is admitted only by the separate
`pals.production-runtime-update.aurora-generation-settings.v1` signed profile.
The previous 34-step registry is frozen, and the new 35th migration cannot be
admitted under the older model migration profile. Runtime settings are insert-only
for the API role. This document describes the implementation; it is not itself a
production deployment receipt.

Validation includes all nine model/effort pairs, transport and quote binding,
retry stability, historical compatibility, real PostgreSQL migration/permissions,
server settlement pricing, isolated HTTP generation serialization and local
browser selection/navigation/mobile layout. Local browser fixtures do not prove
an external model run or public production availability.

OpenAI parameter compatibility follows the
[official model guidance](https://developers.openai.com/api/docs/guides/latest-model#gpt-6-astra-update-api-and-model-parameters).
