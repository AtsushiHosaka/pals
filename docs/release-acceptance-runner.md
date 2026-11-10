# Live release acceptance runner

`pals-scripts/release-acceptance.py run` is an executable qualification step for the Lean-to-answer journey. It does not accept a caller-written `passed: true`, health result, screenshot, or old receipt as acceptance. The versioned release controller must execute it directly and require exit zero. The deterministic CI job tests the gate's contracts; that CI success is **not** live E2E success. Existing deployments and GitHub branch rules are unchanged by this implementation.

The trusted boundary is the controlled release runner, its reviewed code/dependencies, independently pinned signing public key, reviewed private contract, and approved Docker endpoints. Its state directory must be writable only by that runner. This does not defend against an administrator replacing the interpreter, dependencies, browser, Docker daemon, contract, or evidence directory. Do not import uploaded acceptance JSON into this boundary.

## What the runner observes

1. Verify the exact signed target manifest and independent DER/SPKI public-key pin, validity window, sources, and immutable image digests.
2. Read the six known application containers and image metadata through the pinned Docker contexts. Compare actual images, source labels, runtime configuration labels, exact environment hashes, and API manifest binding. Check the same state again after capture.
3. Reuse one authenticated browser context, seeded from a private session-storage file. Navigate to one explicitly supplied existing chat. Observe the selected request through real API GETs until `answered`. The request **and** formal job must have been created after all candidate containers started. An old saved answer cannot qualify a new candidate.
4. Require a verified job, matching Lean source hash, completed explanation, and a unique final conclusion. The stored answer must contain the complete overview, section summaries, and conclusion. Check model, reasoning setting, and output language.
5. Read the saved answer through both direct GET and chat history. Compare the actual visible answer's ordered prose/math semantics with that saved source, then reload the chat and compare all of them again. Math is read once through the renderer's accessible source and must have a visible KaTeX counterpart; duplicated HTML/MathML text is not used.
6. Hash the JavaScript/CSS actually returned to the browser and independently read those exact files from the pinned Web container. This binds the serving Web assets, not merely an unrelated container's image label.

No proof/chat/billing write or automatic model submission is allowed. Normal passive `POST /v1/product-events` to the exact API origin and token/auth POSTs to the explicitly configured auth origin are counted separately. All other browser writes fail the run. Existing account/session authorization and paid-evaluation limits still apply.

The runner records only hashes, bounded statuses, timings, configuration/release identity, and observed asset paths. It does not save questions, answers, Lean text, tokens, session contents, screenshots, traces, or raw container environments. The contract/session/evidence still belong outside Git and require modes 0600/0700.

## Contract and invocation

Required dependencies: Python 3.10+, OpenSSL, read-only access through approved Docker contexts, Node 20.9+, and an existing Web dependency tree containing Playwright/Chromium, unified, remark-parse, and remark-math. No package, application, database, browser account, or fixture is provisioned by the runner. Missing dependencies produce a failed gate.

The private contract has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | `pals.release-acceptance.v1` |
| `phase`, `target` | `pre_release`/`post_deployment`; `staging`/`production`. Pre-release must target staging. |
| `manifest` | Absolute `path`, exact `sha256`, `signature_path`, `public_key_path` (DER), independent `public_key_spki_sha256`. |
| `runtime` | Exactly `api`, `reconciler`, `web`, `proof`, `assessment`, `verifier`. Each specifies `container`, `config_sha256`, `environment_sha256`, plus either Docker `context`/`endpoint_sha256` or the fixed `ssm` binding below. |
| `runner_sha256` | Output of the `fingerprint` command; binds both executing scripts. |
| `web_root` | Existing Web dependency directory; never install a substitute/shim to obtain PASS. |
| `web_origin`, `api_origin` | Exact HTTPS origins. HTTP is allowed only for loopback staging. Credentials/query/fragment are rejected. |
| `auth_origin` | Exact approved HTTPS auth origin, or null to disallow auth POSTs. |
| `request` | Existing canonical UUID `id` and `chat_id` (both may be null for a frozen post-deployment scenario); `generation_model`, `reasoning_effort`, `output_language`, `required_conclusion_text` and `required_conclusion_math` arrays. At least one unique conclusion fragment is required. |
| `timeout_seconds`, `max_age_seconds` | Bounded observation timeout (30–1800 seconds) and accepted-evidence age (1–3600 seconds). |

`endpoint_sha256` hashes sorted compact JSON of Docker context `Endpoints`. `environment_sha256` hashes sorted compact JSON of the container's sorted `Config.Env` array. Compute these from reviewed target configuration; never copy an unexpected live value into the contract merely to make the gate pass. Configuration labels follow the existing native owner contract. The native controller's admission, mount, TLS, and isolation checks remain mandatory; this runner does not replace them.

SSM-only hosts use `ssm: {profile: "pals-prod-member", region: "ap-northeast-1", account_id: "<exact 12 digits>", instance_id: "<exact instance>"}` instead of Docker context fields. The runner verifies the actual STS account against both contract and signed manifest. It sends only the reviewed fixed read-only observer through `AWS-RunShellScript` and consumes its exact successful invocation/instance result. Full Docker configuration/environment is processed **only on the observed host**; SSM output contains fixed metadata and hashes, never credentials, arbitrary labels, raw environment, or error/traceback contents. Web asset observations return hashes only. This transport changes no service, port, IAM role, queue message, or application data; SSM command history is an ordinary operational side effect. Actual AWS permission/delivery remains unverified until the real authorized observation succeeds.

The private session format is `{"schema_version":"pals.acceptance-session.v1","origin":"<web_origin>","session_storage":{"<existing-app-key>":"<value>"}}`. Provision it through the approved test login, never by requesting a password/token in chat or extracting credentials through an unrelated browser-control tool. Credentials stay in that file and browser memory.

```sh
python3 pals-scripts/release-acceptance.py fingerprint
python3 pals-scripts/release-acceptance.py run \
  --contract /absolute/private/contract.json \
  --session /absolute/private/session.json \
  --state-dir /absolute/private/runner-state
```

For post-deployment capture, a separately authorized test submission may create the request **after** activation. Supply its actual IDs using `--request-id <uuid> --chat-id <uuid>`; the frozen scenario's model/language/conclusion remains unchanged. Both overrides are required together and are rejected for pre-release. The journal records an effective-contract hash binding those IDs; `status` must receive the same overrides. This avoids pre-freezing fictitious future IDs and prevents a different request from reusing an accepted result. The capture itself never creates that request.

The API must return server-owned `X-PALS-Release-Manifest-SHA256` on the observed GETs, matching the contract's manifest. Web must expose `[data-proof-request-id="<id>"] [data-proof-answer]` around only the actual answer body. Old images lacking these bindings cannot qualify and need the corresponding API/Web changes.

Use separate private contracts and state directories for staging and production. Each contract pins that environment's actual signed runtime manifest. The release controller must independently require identical approved image/source tuples between staging and production; different database targets/admissions can require different target manifests. A caller-supplied target label is not proof of environment isolation.

Each invocation appends `running` before checking prerequisites, followed by `accepted` or `failed`. A crash leaves `running` and blocks qualification. The latest failed/incomplete attempt blocks an earlier green result. `status` checks the protected journal's latest matching, fresh result; it does not re-observe the runtime and must not replace direct capture at promotion. Changes to either script or the contract invalidate earlier status evidence. Cleanup and owner release remain independent of this gate.

## Post-deployment request submission

`pals-scripts/release-post-request.py` is the release cycle's `post-request` command. Its command line now uses a live adapter by default; tests still inject a transport through `main()`. The adapter is two versioned files beside the runner, referenced from the entry script as literals joined to `HERE` so the release plan can freeze them by hash:

- `release-post-request-browser.cjs` holds the credential. It reads the same private session file as the observer (regular file, owner-only `0600`, one link, never written), seeds one browser context from it, takes the bearer the product itself sends to `api_origin`, closes the browser, and then serves only these calls on `api_origin`: `POST /v1/chats`, `GET /v1/chats/{id}`, `GET|POST /v1/chats/{id}/proof-requests`, `GET /v1/proof-requests/{id}`. The page may not write (same allowances as the observer). HTTPS only, no redirect is followed, every call has a deadline, and inherited settings that weaken TLS or add a proxy are removed. The bearer and session contents stay in that process.
- `release-post-request-transport.py` holds the policy. Before the paid call it reads the chat and its request list, which proves the account, the chat and `X-PALS-Release-Manifest-SHA256 == manifest.sha256`. A request already in the run's dedicated chat is adopted; otherwise the create is sent once per process with the journal's key in the body field `idempotency_key` (the product's own contract). A 4xx reply is a definitive rejection. A lost reply, timeout, 5xx or 3xx is unresolved: the adapter observes the chat and never sends the create again in that process. A later invocation observes first and sends the same key only when the chat is still empty, relying on the API's replay for that key.

Refusals are fixed codes, an HTTP status and at most the API's bounded `error.code`. Statements, tokens, session contents and response text are not printed, journaled or raised. The adapter does not request a token quote: an account on a token-billed plan is rejected with `create_rejected_http_422:token_quote_required` and nothing is created. An expired session fails closed (`authenticated_context_not_observed` or `session_not_authorized`); renewal works only if `auth_origin` permits it.

`python3 pals-scripts/tests/test_release_post_request_transport.py` runs the real adapter, helper and CLI against a loopback TLS server with a stub browser package. It proves the wire policy only. Seeding a real session, the production API's replay and release header, and the first real submission remain NOT VERIFIED until a production run.

## Verification boundary

Run `bash pals-scripts/tests/release-acceptance.sh` for deterministic contract/signature regressions. These tests include real local OpenSSL signing/verification and real failure when live dependencies are absent. Markdown/browser boundaries in unit tests are isolated explicitly; they do not claim actual service or UI acceptance. A real staging/prod run remains NOT VERIFIED until approved contexts, session, signed target, and a fresh proof fixture exist and the live command exits zero.

With an approved existing Web dependency tree, `PALS_ACCEPTANCE_WEB_ROOT=/absolute/web node --test pals-scripts/tests/release-acceptance-render.test.cjs` also checks the extractor in real Chromium against offline prose/KaTeX fixtures, including absent/hidden conclusions and invisible formulas. It starts one task-owned browser and closes it; it makes no network or model call. This verifies extraction behavior, not the application, saved production data, or a staging/prod journey.
