# Live proof and explanation evaluation

The November 8 follow-up authorizes completing the proof evaluator, deploying the
measurement infrastructure and running actual evaluations. The selected account is
the user's existing PALS account. This workflow creates private benchmark chats and
normal proof requests; it does not impersonate a worker or bypass claims, billing,
Recipe admission, Lean verification or independent answer review.

## Authentication

Use the existing app's Cognito client and a private token file. With `PYTHONPATH`
pointing to `pals-observability/src`, invoke `python -m
pals_observability.prompt_quality_login --client-id <actual-public-client-id>
--output <private-token-path>`. Enter credentials only in the local terminal.
The password is never stored or passed as a shell argument. A Cognito access token
is stored in a mode-0600 owner-private file; the normal PALS `/v1/auth/me` check
then verifies owner access. If this later check fails, the token remains private
and a retry checks it without asking for the password again. Challenges and password
changes remain on the normal website. Neither passwords nor tokens belong in chat.
New Cognito access tokens last 30 minutes following the owner's explicit
November 9 request; tokens issued before that change retain their original expiry.
If a token expires, the helper
prompts for normal local sign-in and atomically replaces the expired private token;
it does not store a long-lived refresh credential. Start collection promptly after
sign-in. Collection deadlines are fingerprinted, and the initial batch is bounded
to 780 seconds so it can finish within the short session. Pending work remains
resumable rather than being relabelled failed.

The API client identifies itself as PALS-PromptQuality. The original helper's default
Python client received an HTTP 403 at the API boundary. This was reproduced without
credentials, repaired, and followed by successful owner/quota preflight using the
user's local token. Diagnostics now expose only the failing step and closed error
code, not the Cognito message, email, password, token or raw response.

### アクセストークンの30分設定

2026年11月9日の依頼に基づき、評価に使う既存Cognitoクライアントの
AccessTokenValidityを15分から30分へ変更し、設定を読み戻して確認しました。
この設定は変更後に発行されるトークンから適用されます。
IDトークンの15分、refresh tokenの1日、その他の設定は変更していません。

既存クライアントは現行のprivate-runtime Terraformでは参照だけで再利用しています。
別stateへ二重importしたり、古いfoundation全体をapplyしたりせず、
`pals-infra/scripts/update-web-access-token-validity.py`で設定を取得し、
差分とplanのhashを確認してから適用します。AWSの更新APIは省略した項目を
既定値へ戻すため、更新可能な既存設定をすべて保持し、直前の再取得と適用後の
読み戻しが一致しなければ停止します。planと結果はGit外の0600ファイルに保存します。

同じアカウントを別の操作でも使う場合は、回答言語と新規送信の上限に注意します。
今回の継続評価では英語設定への変更と429を実際に観測しました。
条件が一致しない回答は日本語の比較データへ入れず、送信上限を迂回しません。

分割した継続処理では、各題にどのrunを採用したかを残します。別journalで既に受理された
題を、元journalの未送信状態から再び送らないでください。収集コードの版が変わった場合は
元のheaderを書き換えず、新しいrunと出典の対応を作ります。再採点は同じ回答のhashを
確認し、生成と区別します。最新の8題集計は7題完了・1題未完了の現状把握用で、
時間枠の異なる回収を含むため、そのまま単一条件の改善比較には使いません。

## Infrastructure

Use `pals-infra/terraform/prompt-quality`, independent of the application Terraform
root. Initialize S3 with the existing encrypted bucket and the separate key
`pals/prod/prompt-quality.tfstate`, `encrypt=true` and `use_lockfile=true`.
The provider guards account 828786775577 in ap-northeast-1 using the existing
`pals-prod-member` profile. Inspect the saved plan before apply: it must contain
only one log group, two unattached scoped policies and two saved query definitions.
No application resource or IAM attachment is needed.

The reviewed plan was applied successfully: five added, zero changed/destroyed.
The group is `/pals/prod/prompt-quality`, with 90-day retention. Both saved queries
recognize v1 and v2 records. Actual publication/read-back is a separate live check.

## Dataset and deployment identity

`pals-observability/datasets/undergraduate-live-ja-v1.json` contains six proof cases
and two concept cases. Its closed live-dataset schema includes the original request,
expected outcome, reviewed reference and explicit `requires_lean` flag. References
are sent only to the independent judge. Current live submission supports text-only
initial requests; supplied clarification turns/material attachments are rejected
before spending rather than silently omitted. One run uses at most ten cases and
does not bypass the normal rolling-hour request limit or account credits.

A private `pals.prompt-quality-deployment.v1` manifest records the actual API origin,
deployment/source/configuration/catalog digests, selected generator and every
generation/QA/intent model. Build it from deployment read-back, not local HEAD.
Hash the nonprompt implementation, real model/reasoning/quote configuration and
toolchain separately from prompt-owning sources. Do not include secrets or user IDs.
Check the deployed image/source and catalog identities before and after collection;
the collector cannot freeze a remote release or detect hidden provider alias drift.
All runtime model identities must be listed so the judge can be independent.

## Execute and resume

```bash
python -m pals_observability.prompt_quality_live \
  --dataset pals-observability/datasets/undergraduate-live-ja-v1.json \
  --deployment-manifest /private/evaluation/deployment.json \
  --access-token-file /private/evaluation/access-token \
  --run-id seq28-baseline-001 \
  --output /private/evaluation/baseline.json \
  --journal /private/evaluation/journal.jsonl \
  --judge-model gpt-5.4-2026-03-05 --judge-revision gpt-5.4-2026-03-05 \
  --generation-reasoning-effort medium --environment prod --max-cases 8
```

The selected judge snapshot was available in the configured provider account and
is distinct from deployed generation/online-review/intent models. The judge uses
4,000 output tokens and low reasoning, fingerprinted with its rubric and code.
The first run establishes a baseline; there is no improvement claim without a
separate candidate under matching controls and a defensible holdout.

The locked mode-0600 append-only journal records intent before POSTs and stores
returned IDs, terminal responses and measurements privately. Uncertain submission
is recovered through GET-only lookup. Authorization/rate failures stop further new
submissions. A timeout leaves a real pending task; it never claims cancellation or
terminal failure. An unattempted case is `not_submitted`. Use the same journal/run
identity for explicit resume; missing judging can be retried without generation.
Keep API errors and partial-run evidence private and inspect them before retrying.

## Formal evidence and interpretation

For `lean_catalog`, fetch the owned historical Lean-source endpoint and verify
request/chat/Recipe/revision/entry/compiler/toolchain bindings. Recompute Lean-source
and displayed-answer hashes. For `lean_verified`, inspect the matching linked job,
require its state/status/stage to be verified, fetch its owned source and recompute
the Lean hash. Answered or QA approval alone never establishes verification.

A generated proof can be verified while its explanation fails. V2 records retain
that distinction. Missing/nonterminal evidence is unavailable; observed terminal
failed/canceled proof jobs are not verified. Required-proof counts remain the fixed
denominator. Completion latency excludes pending/unsubmitted work; pending elapsed
time is a censored lower bound. Quality scores remain independent LLM estimates.

Use the ordinary `prompt_quality_cli publish`, `fetch` and `summarize` commands.
Publish only the intended final immutable collection: the same run ID with changed
data is a conflict, not an update. Confirm identical read-back, fetch JSONL from
CloudWatch, then build graphs from those fetched records. Show sample sizes, missing
scores, incomplete observations and the distinction between formal verification and
answer delivery. Do not replace missing results with synthetic examples.
