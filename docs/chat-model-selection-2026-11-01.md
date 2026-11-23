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
for the API role.

Validation includes all nine model/effort pairs, transport and quote binding,
retry stability, historical compatibility, real PostgreSQL migration/permissions,
server settlement pricing, isolated HTTP generation serialization and local
browser selection/navigation/mobile layout. Local browser fixtures do not prove
an external model run or public production availability.

## Production verification

Sequence 9 restored the original public ALB routing at 2026-11-01 21:53:13 JST.
Its signed manifest is
`a3340a717db963f64e42de8ddea3e10483f32712d4e4b9d2702f0866c95b774c`.
All seven running containers, private TLS, the complete 35-step database contract,
recovery units and unchanged catalog fingerprints passed actual host readbacks.
The temporary KMS/RDS read policy was removed and its absence confirmed. The API
readiness gates accept the exact generation-settings admission carrier; the
software-only sequence-9 update did not repeat the schema migration.

An actual Chromium session at `https://palschat.site` verified all nine choices,
Sol / High selection, persistence across landing-to-guest navigation and a
375-pixel viewport without horizontal overflow or JavaScript page errors. The
browser check submitted no additional proof requests.

One normal public guest request selected Sol / High and asked for continuity of
`x ↦ x^n` on the reals for every natural `n`, including zero. It reached
`answered` with `lean_verified`, using a newly generated proof rather than a
Recipe. The downloaded Lean code matched the stored verified hash
`1d6c321c9100aeece073cfaddb66055e399efee42b2146040240a562b85d7ceb`.
Read-only checks confirmed the selected pair on the request and linked job,
three Sol generation usage records, the approved explanation's canonical output
hash and exact reconstruction of the persisted answer.

| Observation | Seconds |
| --- | ---: |
| Public submission through terminal polling | 137.447 |
| Server request creation through answered state | 135.623 |
| Request assessment before formal job creation | 30.907 |
| Draft / Sketch / Prove stage intervals, combined | 61.618 |
| Compile stage through semantic-review entry | 3.808 |

Stage intervals include surrounding orchestration; they are not isolated provider
or compiler benchmarks. This single Sol / High result does **not** meet the
ten-second target or establish the latency of the default Terra / Medium choice.
The remaining time includes queue/context preparation, review and explanation.

Recorded request-assessment costs matched the deployed versioned pricing
function. These request rows exclude the linked job's separately recorded
generation usage. The guest uses the normal daily preview allowance and has no
paid token operation, so this production smoke does **not** verify an actual
paid-account balance decrement. Server settlement, choice-bound quotes and
model-weighted consumption remain covered by the API tests described above.

OpenAI parameter compatibility follows the
[official model guidance](https://developers.openai.com/api/docs/guides/latest-model#gpt-6-astra-update-api-and-model-parameters).
