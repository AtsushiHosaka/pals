# Release reliability contract

Shared operating rules for Claude, Codex, and human contributors. Rationale and known gaps: [November 8 audit](release-reliability-audit-2026-11-08.md), [#309](https://github.com/AtsushiHosaka/pals/issues/309). These rules specify required evidence; they do not imply that missing automation already exists.

The executable paths are `make release-source-checks` (actual changed-source GitHub CI), `make release-local-qualify` (the approved real local journey), `make release-qualify` (authenticated live capture where a dedicated session exists), and `make release-cycle` (versioned native sequencing). See [the runner contract](release-acceptance-runner.md) and `pals-infra/host/private-runtime/RELEASE_CYCLE.md`. Cutover blocks without real qualification of the declared profile, exact source/image bindings and executable native recovery adapters. Passing deterministic controller/parser tests does not fill those prerequisites.

On November 9 JST, the user selected local real DB/Lean/model before release and the currently logged-in Chrome account for one production request after deployment. No AWS staging environment is required; honor the explicit US$1 model budget. The local profile retains exact API/worker images; its Web build uses the exact candidate source with declared loopback public bindings. AMD64 emulation on Apple Silicon cannot establish the observed Landlock boundary, so the closed native ARM64 verifier variant retains the exact production source archive, Dockerfile, Lean version and Mathlib manifest with actual build provenance. Its full compiler sandbox must pass a live readiness compile before a paid submission. This is not production AMD64 byte parity. Local auth/queue emulation, bootstrap DB privileges, the budget forwarding proxy and network guard are explicit boundaries. They are not evidence for production auth/network/AMD64 readiness. The controller uses `local-qualification.py --verify-existing` for fresh dependency/browser/DB reads of the fixed one-submission capture; it may not import a prior PASS value or submit a replacement job automatically. Production acceptance must separately establish the actual deployed candidate and the new authorized Chrome journey through completion, persistence and reload.

For seq30, the owner clarified on November 14 that the US$1 limit applies to local qualification; the authorized production acceptance, mean–median question and figure checks use a separate budget. Preserve the local ledger and cap. The initial three-capture limit is historical: the November 17 JST decision below supersedes it for seq30. Record production costs separately and state any incomplete usage coverage; do not automatically resubmit failed paid questions. This clarification does not change application sources, model settings or production permissions. See [the recorded decision](https://github.com/AtsushiHosaka/pals/issues/392).

## Start from observable behavior

Before implementation, record the issue, owning repository, exact starting revision, expected user outcome, affected cross-repository contracts, failure/recovery cases, and non-goals. Inspect the existing behavior rather than treating a bug report or prior completion claim as established fact. Use one release owner; give parallel agents disjoint write ownership or read-only scopes.

For a defect, write a behavioral regression that fails on the pinned bad revision and passes after repair. Review what tests assert. Mocks establish the declared boundary only; they do not establish a real provider, database, queue, compiler, browser, or deployed result.

## Evidence required for promotion

| Gate | Required evidence |
| --- | --- |
| Source and contracts | Clean task-owned source snapshot; exact parent/submodule commits; immutable image digests; schema, catalog, prompt/model/config versions; preserved existing features |
| Deterministic checks | Changed-repository unit/static/build checks, cross-repository contract tests, actual database integration where affected, host/controller/recovery suites where affected |
| Product journey | Realistic input through the production-equivalent API/queue/worker/Lean/explanation path to the expected terminal outcome; all learner-visible fields survive persistence, rendering, and reload |
| Failure and time | Required transient GET failure/reconnect, auth expiry, long-running job, timeout/cancel/redelivery, migration/recovery cases; prove no duplicate results or charges where applicable |
| Release rehearsal | Same reviewed driver and operation order as production; prerequisites before traffic removal; bounded outage; compensating action for every safe pre-admission failure; compatible post-admission forward repair |
| Production acceptance | Actual deployed digests/config; authorized bounded critical-path check; terminal result, rendered answer, and history after reload; telemetry fresh; no unresolved critical regression |

Select checks by the changed behavior and dependency boundaries; do not rerun unrelated expensive suites mechanically. Required skipped, unavailable, stale, wrong-revision, or mock-only evidence yields `BLOCKED` or `NOT VERIFIED`, never a green gate. Any approved deferral must identify the exact gap, impact, owner, expiry/resume condition, and user decision; it must not silently weaken a required check. Honor existing paid-evaluation limits and authorization for production data/lifecycle operations.

Bind evidence to the candidate actually promoted. Changing code, images, schema, prompts/model configuration, catalog, driver, or relevant runtime settings invalidates affected evidence. Keep prior failures. Accept the latest successful rerun only after addressing a failed prerequisite; never search backward past an unresolved latest failure.

## Deploy safely and distinguish outcomes

Use `prepared` → `verified` → `deployed_unverified` → `accepted`, with explicit `failed`/`blocked` states. `accepted` requires the production-acceptance evidence above. Merge, image publication, admission, startup, health, empty queues, or “preparing response” alone is insufficient. Do not close a functional issue or promote an unrelated next release while a required critical acceptance remains unresolved.

Cleanup, traffic restoration where safe, temporary-access removal, and canonical-owner release must remain possible after a failed check. Keep safety cleanup separate from functional acceptance; never retain expired privileges or deadlock the release owner to obtain an acceptance result.

Before removing traffic, verify all prerequisites and a workable recovery plan. Prefer serving capacity that remains available; if the architecture requires maintenance, declare and measure a bounded maintenance window with a useful user response. On pre-admission failure, restore and verify the exact baseline ingress/runtime where compatible. After irreversible admission, use the reviewed schema-compatible repair path. Never bypass admission, signatures, authorization, or identity checks to make health green.

Reusable release code belongs in the owning repository. Freeze the exact executing driver revision/hash and arguments, not only generated artifacts. Changing it during a cutover requires renewed affected verification; a comment claiming approval is not approval evidence.

For a planned sole-target cutover, the v2 controller requires its frozen notification-window helper and contract. It targets only the exact incident 5xx alarm, verifies the actual account/configuration and active one-time mute, and fixes an AWS-enforced expiry of at most ten minutes. It retains metrics, alarm evaluation and all other alarms; no open-ended disable/re-enable is allowed. Failure attempts early cancellation. Healthy restoration may shorten the remaining tail to at most three minutes without extending the original deadline. Overrun restores notifications and fails acceptance, while compatible, independently checked recovery can continue. Local fault injection and dedicated notification probes must not manufacture production ALB failures. See [the observed causes and limits](release-5xx-cause-and-control-2026-11-09.md); code/CI success does not establish live AWS activation, expiration or notification delivery.

2026-11-14のオーナー承認により、seq30に限り、指定した5xxアラームの通知抑制の上限を1500秒（25分）とする。seq29の利用停止実測847秒と引き継ぎの計画を踏まえ、600秒を維持する案は今回採用しない。AWSによる期限の強制、適用前の有効状態の確認、失敗時の早期取消、生メトリクス・評価・他のアラームの維持は引き続き必須とする。利用停止15分以内という受け入れ条件は変更しない。seq31以降への包括承認ではない。判断の記録は[pals#379](https://github.com/AtsushiHosaka/pals/issues/379#issuecomment-6870562063)にある。

## Treat recovery as a product requirement

Specify behavior after a transient network error, reconnect/focus, access-token expiry, provider/queue failure, worker exit, and host reboot. Recover observation of the same request rather than resubmitting work. Preserve account isolation, unsent drafts, idempotency, billing, and terminal-state integrity.

Deployment authorization and recovery of the exact currently admitted runtime need explicit, reviewed lifetime rules. A short-lived release signature must not leave unattended recovery dependent on an unplanned manual feature deployment. Do not broaden credential storage or enable unrestricted restart policies as a shortcut.

## Observe and close the loop

Record privacy-minimized lifecycle events correlated to release/config and request: accepted, stage transitions, terminal outcome, bounded error code, duration, and retry reason. Reconcile accepted/terminal/in-flight work and alarm on missing telemetry, old active work, stopped consumers/outboxes, and DLQ growth. Health and answer-quality metrics have separate meanings.

One attempt may have multiple observations. Preserve raw observations and count its final outcome once; retain failures and unknowns. Unit-test counts are not product success rates, and load-balancer requests are not unique users.

For an incident, restore safely, identify the failure mechanism, add a regression at the boundary that missed it, and update only the necessary code/runbook/rule. Record what was observed, what was inferred, what remains unverified, and the exact follow-up owner. Documentation changes alone do not close implementation or production-recovery work.

2026-11-16の追加承認は、seq30のローカル資格確認を既存の予算上限内で4回目に限り1回実行するものだった。根拠は[#396の判断](https://github.com/AtsushiHosaka/pals/issues/396#issuecomment-6909758854)。その1回は実行済みでacceptedとなり、台帳のリセット、上限変更、5回目以降の取得は承認に含まれない。通常の3回上限を他のリリースへ広げない。

2026-11-17 JST追記: オーナーは「何回でも許可しますよ」と回答し、seq30のローカル資格確認の回数上限を解除した。[最新の判断は#398](https://github.com/AtsushiHosaka/pals/issues/398)。同じ問題、生成モデルgpt-6.1-terra / medium、oracle、意味審査と合格条件を維持し、回数だけを理由に承認を取り直さない。上記の3回上限と第4回だけの追加承認は、それぞれ当時の判断として保持する。この例外は他のリリースへ広げない。

累積1 USDの上限は維持し、過去の未確定callも予約額で数える正規proxy、既存台帳、各期上限と履歴を保持する。reset、予算増額、健全な台帳のrolloverは許可しない。各captureは新しい専用stateと単一送信markerに固定し、不明な結果は同じIDの観測を回復して重複送信しない。次のcaptureへ進む際も同一条件、残予算、署名・freshness・実依存先・source checksを再確認し、合格前には切り替えない。正規controller、dry run直後のapply、本番での保存・描画・再読み込みの受け入れは従来どおり必要で、本番QAは#392の別予算を維持する。

## 失敗の診断と報告の区分（#458、#450の再発防止）

### 失敗時に残す診断

失敗したリリース工程は、診断コードを後から足さなくても原因と再開点が分かるように、次の項目を残す。値はすべて閉じた語彙か固定形式の文字列とし、例外メッセージ、パス、トークン、利用者の内容は出さない。

- 失敗した工程（phase）と、外向きの失敗コード
- 非秘密の下位理由（detail）。外向きのコードが複数の原因をまとめている場合に、その内訳を示す。内訳が既知の固定コードにも例外クラス名にも当てはまらないときは `*_other` とする。
- 実行を一意に指す run ID と、署名済みジョブの SHA-256
- cleanup の状態。残骸の一覧が空なら `clean`、残りがあれば `residual`、記録から判断できなければ `unknown` とする。
- 安全な再開方法。cleanup の完了、読み取り専用の確認、新しい権限の要求、人への引き継ぎのいずれかで示す。`unknown` と表にない理由は、必ず人への引き継ぎにする。

実装は [pals-infra の診断文書](https://github.com/AtsushiHosaka/pals-infra/blob/claude/458-diagnostics/docs/release-diagnosis.md)（`scripts/release_diagnosis.py`）にある。診断が出ていても、`accepted` は常に偽のままとする。診断が出ることは、機能受入の成功ではない。

### 報告の区分

リリースの報告は、次の4つの状態を別々に書く。上の状態の証拠だけで、下の状態を名乗らない。

| 状態 | 言ってよい条件 | 必要な証拠 |
| --- | --- | --- |
| source準備 | 候補の固定、署名、配置、検査が済んだ | 候補の識別子と検査結果 |
| 本番切替済み未検証 | 本番の入口と実行環境を新しい候補へ切り替えた | 切替の記録。この時点では `deployed_unverified` |
| 本番受入済み | 本番で回答・保存・表示・再読込が確認できた | 本番受入の記録と、依頼された実画面のキャプチャ |
| 後処理完了 | 一時権限の撤去と所有者の解放が済み、残骸がない | cleanup 状態が `clean` である記録 |

- 「リリース完了」と書けるのは、本番受入済みと後処理完了の両方がそろったときだけにする。
- 報告には、現在の状態を先頭に1行で書き、続けて未完了の状態を挙げる。テスト件数、署名、配置、ローカル受入の成功は、状態の根拠として並べない。
- 利用者がキャプチャを求めた場合は、本番受入済みの報告に、実画面のキャプチャを添付する。実装の説明やテスト結果で代えない。キャプチャに秘密や利用者の内容が写っていないことを、添付する前に確かめる。
- 残り時間の見積もりは、未接続の工程がない場合に限って書く。
