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

## 候補固定後の変更と担当（#455、#450の再発防止）

根拠は[#433の遅延分析](https://github.com/AtsushiHosaka/pals/issues/450)。ここは運用ルールの定義であり、CIやscriptによる強制は未実装である。実装済みと扱わない。安全検査・署名・認可・受入の省略は含まない。

### 候補の固定と変更

- 候補固定とは、承認された候補のリリース実行を依頼した時点で、parent・submodule・image・schema・catalog・model設定・実行driverのexact revisionを記録することをいう。
- 固定後に取り込めるのは「配備を妨げる修正」だけである。具体的には、必須checkの失敗、配備・復旧・cleanupの失敗、安全性やデータ破壊の欠陥、期限切れの再準備で、その修正がなければ候補を署名・配置・受入できない場合に限る。
- 次は取り込まない。機能追加、見た目の改善、別Issueの修正、リファクタ、ついでの整理。配備を妨げないなら次便へ回す。利用者が候補への追加を明示したときだけ例外とし、その依頼を記録に引用する。
- 候補を変えるたびに、変更前後のrevision、影響を受ける証拠（署名・転送・検査）、再実施する工程を記録する。変更した候補で無効になる証拠は、既存ルールどおり再取得する。
- 記録場所は、そのリリースのIssue（例: #433）のコメントとする。秘密・ID・利用者の内容は書かない。

候補変更の記録様式:

| 項目 | 内容 |
| --- | --- |
| 変更前→後 | 変更したrepositoryごとのcommit |
| 理由 | 妨げていた失敗（check名・run ID・診断コード）。上記の「妨げる修正」に当たる根拠 |
| 依頼者 | 変更を依頼した人、または発見した担当 |
| 担当 | 修正を書いたチャットと、取り込みを実行する実機担当のチャット |
| 無効になった証拠 | 再実施が必要な署名・転送・検査 |
| 取り込まなかったもの | 同時期に提案され、次便へ回した変更 |

### 実機操作の担当

- 実機・本番・共有リソースを操作する担当は1チャットとし、リリースのIssueに「実機担当」としてチャットのリンクを1つだけ書く。担当の交代は、元の担当が引き継ぎ記録を残してから、Issueのコメントで行う。
- 実機担当のチャットが引き継ぎ記録なしに終了した場合は、利用者（または利用者が指名した人）が、Issueのコメントで代わりの実機担当を指名する。指名の前に、前の操作がもう実行中でないこと（実行中のSSMコマンド、保持中のロックと実行権、一時権限の有無）を読み取りだけで確認し、結果をコメントに残す。実行中のSSMコマンドがなく、前の操作が終了したと確認できた場合は、ロック・実行権・一時権限が残っていても「前の操作はもう実行中でない」と扱い、指名された代わりの担当が、cleanup、一時権限の削除、canonical ownerの解放を、正規の入口（署名済みの手順と台帳）だけで行ってよい。担当は、実施前後の状態、実行したコマンドと結果、残った項目を、Issueのコメントに残す。確認できないうちは、cleanup・一時権限の削除・canonical ownerの解放を含め、実機を書き換えない。期限切れの権限を残し続けないため、確認できない状態が続くときは、その理由と次の確認時刻を同じコメントに書く。代わりの担当が決まるまで、状態は「担当不在・未検証」として記録し、受入済みとは扱わない。
- 他のチャットは、実機担当の状態を繰り返し確認しない。実機・本番への読み取りも含め、必要な情報は実機担当またはIssueの記録に依頼する。
- 並列にしてよいのは、独立した調査、source修正、回帰作成だけである。書き込む範囲を重ねない。
- 「リリース完了後に停止」のような指示は、完了まで実行を続けるという意味で、中止ではない。解釈が分かれるときは、実行を止める前に利用者へ確認する。

### 共有CIと自前ランナー

- 自前ランナーは1台で、runは直列に処理される。待ちのrunを増やす操作（再push、再実行）の前に、`gh run list`で実行中・待機中のrunとそのheadSHAを確認する。
- 取り消してよいのは、自分が起動したrunだけである。起動者、branch、headSHAを確認してから`gh run cancel`を使う。同名のcheckが別のbranchやPRにあっても取り消さない。他担当のrunは完了を待つか、そのrunを起動した担当に依頼する。
- 候補固定中、実機担当は必須checkの実行を最優先とする。他の担当は、候補の必須checkが完了するまで、自前ランナーを使うPR・pushを控える。docsだけの変更は、自前ランナーを使わない場合に限り続けてよい。
- 実機担当は、必須checkを待つ間の占有状況をリリースのIssueに書く（実行中のrun ID、待機中のrun、見込みの完了）。これが所有者表示を兼ねる。
- workflowの`concurrency`による自動のqueueや、所有者の自動表示は未実装である。必要になったら別Issueで設計する。

### 並行開発の範囲

| 区分 | 対象 | 扱い |
| --- | --- | --- |
| 並行してよい | webfront・apiの機能PR、docs、評価・台帳の記録、調査 | 候補に合流させない。mainや統合先へのマージは、必須checkが済み、実機担当の占有を妨げない時期にする |
| 触らない | release・recoveryのscript（`pals-infra/scripts/release-*`、native adapter、`pals-scripts/release-*`）、実行driver、承認済み候補の入力・hash対象 | 実機担当の承認なしに変更しない。変更が必要な欠陥は、実機担当へ「配備を妨げる修正」として依頼する |
| 触らない | 親repoのsubmodule pointer | 候補を固定した担当だけが更新する。`git add -A`を使わず、pushの前に`git diff --cached --submodule`を確認する |
| 触らない | 凍結中のworktree（`/private/tmp/pals-*`など、リリースIssueが凍結と示すもの） | 読み取りのみ。凍結の解除はリリース担当がIssueに記録する |
| 触らない | 本番・AWS・共有CIの設定、branch protection | 利用者の既存の承認の範囲に従う。実機担当だけが操作する |

### PRの積み方とmainの遅れ

- 新しいPRのbaseは原則mainとする。PRを積むのは深さ2までとし、それより深くしない。
- 本番へdeployしたcommitは、速やかにmainへ入れる。merge commitで入れ、force pushはしない。
- 統合先branchがmainと別になる場合は、期限を決めてmainへ統合し、期限をIssueに記録する。
- 使い終えた積みは、土台から順にマージするか、すぐに閉じる。放置しない。
- pals-apiは、#96のリリース後に`claude/seq28-api-response-language`をmainへmergeする予定である。pals-webfrontとpals-infraも、同様に統合先とmainの乖離を解消する。これは予定であり、完了を意味しない。

実測による確認は、次回以降のリリースで行う。確認する項目は、候補変更ごとの記録の有無、実機・本番操作の重複の有無、他担当のrun取消しの有無である。

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

## CI lanes, release branches and PR lifetime (decided 2026-11-22, [#467](https://github.com/AtsushiHosaka/pals/issues/467))

A single shared runner let release CI queue behind ordinary PR checks and stretched the #433 release. The rules below remove that contention without weakening any gate and without paid GitHub Actions.

**Two runner lanes.** Self-hosted runners run in OrbStack machines on the owner's Mac and are registered per repository ([`pals-scripts/ci-runner-add.sh`](../pals-scripts/ci-runner-add.sh) adds one; it never touches an existing runner). `pals-ci-runner` is the release machine (label `pals-release`, runners `pals-ci-{api,web,infra}-rel`); `pals-ci-runner-2` is the ordinary-PR machine (label `pals-pr`, runners `pals-ci-{api,web,infra}-pr`). Workflows select the lane with `runs-on: [self-hosted, pals-release]` or `[self-hosted, pals-pr]`. Never put release-gate jobs on `pals-pr`, and never stop, restart or reconfigure a runner or OrbStack while release CI or a cutover is running; add runners instead. The legacy `pals`-labelled runners are removed only after a release completes and every workflow uses the new labels. `pals-agent` and the parent use GitHub-hosted runners, which are free for these public repositories.

**Light on PRs, heavy once.** A pull request runs only the light `pr-light` check on `pals-pr`. The full suites (`api-regression`, `web-regression`, `release-cycle-regression`, `agent-regression`, plus the parent's release checks) run on push to `main` and `release/**`, on `pals-release` except `agent-regression`, which stays on its GitHub-hosted `ubuntu-24.04` runner. The file paths and job names that `release-source-checks.py` requires do not change, and a candidate still needs its own exact-commit result, so `make release-source-checks`, `release-qualify` and `release-cycle` are not weakened: a candidate that has no heavy result from a `release/seqNN` or `main` push is `BLOCKED`. **Pending:** the parent's `repository-safety` and `release-acceptance-contracts` currently run on `ubuntu-latest` and push only on `main` (`pals-scripts-pr.yml`); moving them to `release/**` on `pals-release` is a separate workflow change. Until it lands, a `release/seqNN` push does not produce those results and the gate stays `BLOCKED`. Likewise `require_check` in `pals-scripts/release-source-checks.py` still accepts a successful run of any event, so a parent PR run can satisfy it; until the gate records the triggering event and branch and accepts parent checks only from a `push` on `main` or `release/*`, the release owner confirms by hand that the parent results come from such a push.

**`release/seqNN` branches.** Cut `release/seqNN` from current `main` in each repository and pin the candidate commits there; push it so the heavy CI runs on the exact candidate. Development continues on `main` during the release; the candidate changes only through the freeze rules above. **Applicability.** Today `AGENTS.md` records `claude/seq28-api-response-language` (API) and `codex/sidebar-inline-math-20261031` (Web) as the protected production sources, and `main` of those repositories is stale; never cut a candidate from stale `main`. For those two repositories, cut `release/seqNN` from the recorded production branch until the approved production commits are reconciled into `main`, `main` has equivalent branch protection, and `AGENTS.md` baselines are updated; only then does "cut from `main`" apply to them. Do not create a separate staging or integration branch: it recreates the drift between `main` and production this rule exists to prevent. Once production acceptance and cleanup have finished, merge the commit that is actually in production into `main` within 24 hours (resolve conflicts by merge, never force push). The release is closed only after this merge; a release whose production commit is not on `main` stays open.

**PR lifetime.** Every PR ends as merged or closed within 7 days of creation. When closing, leave the useful points in an Issue; if the work must be redone, assign an owner and open one PR against `main`. Stack at most two levels deep (a PR whose base is another open PR's branch counts as one level). Working notes go in Issues, not in PRs; do not keep long-lived drafts. A PR that must outlive 7 days needs a dated reason in its Issue.

**Weekly review.** [`pals-scripts/pr-weekly-review.sh`](../pals-scripts/pr-weekly-review.sh) lists open PRs across all PALS repositories, oldest first, and marks those older than 7 days, drafts and stacks. It reads the GitHub API only (zero cost) and writes `~/pals-pr-review/YYYY-MM-DD.md`. It runs from this Mac's cron every Monday 09:00 (`0 9 * * 1 /bin/bash $HOME/pals-pr-review/pr-weekly-review.sh`, using a copy of the script in `~/pals-pr-review/`; refresh the copy when the script changes). Whoever owns the unresolved PRs reports them to the owner the same day.
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
