# Live Lean evaluator and rollout evidence — November 9, 2026

Authority: explicit follow-up to implement the missing proof evaluator, deploy, run
actual evaluation and chart results retrieved from CloudWatch. The user selected
their existing PALS account and completed local normal authentication after a
helper defect was repaired. No account was created or credential reset.

## Implementation and verification

- Ordinary owner-scoped chat/quote/request submission preserves the actual queue,
  claim, Recipe and Lean workflow. Catalog and generated-job source bindings are
  independently read and hashed; verification is separate from answer delivery.
- V2 retains pending/unknown submissions and unattempted cases separately from
  terminal failures. Missing/nonterminal evidence remains unavailable, and completion
  latency excludes censored/unsubmitted operations.
- A private fsynced locked journal precedes mutations and supports GET-only recovery.
  Passwords/tokens/raw responses are excluded from CloudWatch records.
- Auth helper debugging reproduced HTTP 403 for Python's default client identity
  and normal HTTP 401 for the explicit PALS client. The request header was corrected.
  Closed step/error diagnostics and private token retention avoid blind repeated
  password prompts. A subsequent real owner, token-capacity and Japanese-language
  preflight succeeded. Credentials remain outside tracked artifacts.
- Latest observability tree: **1,139 passed, 1 credential-dependent Langfuse
  smoke skipped** in 38.96 seconds. Ruff and strict mypy passed. Actual deployed API
  source contracts accepted the request/quote/terminal/source forms in source checks.
  Boundary fixtures do not count as live proof evaluation.
- Actual evaluation source: `f588a0ec16e7af98ce4762089f3b46b97f366ae0`.
- Subsequent language-preflight guard: `a3ab37db2e72b03a7ab64834efbe4a374ea03173`.
- Infrastructure commit including live query repair: `fcad5bbbd883bd42f7cbc9a197974ac815fcc4a7`.

## Actual infrastructure deployment

The standalone `pals-infra/terraform/prompt-quality` root uses the existing encrypted
S3 bucket with a distinct locked key, `pals/prod/prompt-quality.tfstate`.
Provider account guard: 828786775577, ap-northeast-1, existing member profile.
The inspected saved plan added exactly five resources: one 90-day log group,
two unattached scoped policies and two saved queries supporting v1/v2. Apply
completed with **5 added, 0 changed, 0 destroyed**. No application resource, policy
attachment, database schema or running service was changed by this deployment.

Actual AWS query compilation then exposed a saved-query issue that local Terraform
validation did not prove. The summary now flattens cases before aggregation and
uses distinct scalar intermediate aliases. Both candidate queries completed against
the real empty group, without synthetic events. An inspected follow-up plan changed
only the saved summary query: zero creates/deletes and one measurement-query update.
That repair was applied; both deployed queries subsequently completed successfully.
An actual post-deployment plan had already confirmed no infrastructure drift before
the explicit query repair.

Plan SHA-256: `bc91eb3e04e562b2816fb590c72a2a0e711667c8eef56f38dbefe5b9b59d7cc8`.
The log group is `/pals/prod/prompt-quality`. Operator artifacts, plan, source/runtime
attestations and any credentials/results remain in the ignored mode-0700 task output
directory, not this repository's committed evidence.

## Baseline preparation and availability prerequisite

The planned baseline has six proof cases and two concept cases, one repetition,
using the deployed generator and independent provider-available snapshot
`gpt-5.4-2026-03-05`. The account's normal token quota was sufficient at preflight;
the ten-request rolling-hour limit remains enforced. No candidate improvement is
claimed from a single baseline.

An earlier preparation snapshot matched the signed sequence-28 release:
API `14e9bf93c9eece11d8e6f2d316936a519ba00610`, worker
`b27f1d8292391567a2ca15f103eb08b18dc016c4`, with seven protected containers unchanged.
The actual eligible Japanese Recipe catalog had 13 entries and SHA-256
`af905dd6d624a1059289397641816ea326075da84375057e5bed1f66df568a03`, read through
the deployed reader in a repeatable-read, read-only transaction. These are runtime
observations, not local/simulator substitutes.

The first benchmark attempt stopped at owner preflight with public HTTP 503, before
creating any chat or proof request. Public web and API were both 503. Read-only
diagnosis found the HTTPS load-balancer target group empty. CloudTrail records
successful removal of its sole target at **00:06:25 JST on November 9**. The shared
SSO caller identifies an operator session, not which chat/person issued it.
The backend itself remained healthy: internal API health/readiness both 200,
unchanged protected containers, zero restarts/OOMs and ready unexpired credential
brokers. The measurement Terraform apply did not touch load balancing.

This task did not blindly reregister the target or interfere with a release.
Public serving later returned without an application mutation from this task.
Read-back during that preparation again confirmed the same sequence-28 services and catalog.
The user's access token had meanwhile expired: its actual validity is 900 seconds.
The helper now detects expiry and performs normal local sign-in again, with no
long-lived refresh credential stored. Collection deadlines are fingerprinted and
the initial batch is bounded to 780 seconds. These statements describe preparation,
before the actual collection below; they are not the current execution status.

## 初回の実評価

2026年11月9日08:52:58 JSTに、利用者の通常アカウントで実評価を開始しました。
固定した8題のうち、3題は回答・Lean検証・独立した説明採点まで完了しました。
1題は観測終了時に処理中、4題は未送信でした。未完了を数学的失敗や0点には
置き換えていません。完了した3題は、平方関数の連続性、絶対値関数の原点での
微分不能性、平方根2の無理性です。

| 項目 | 初回観測 |
|---|---:|
| 計画した題数 | 8 |
| 送信した題数 | 4 |
| 回答・Lean検証・採点まで完了 | 3 |
| 処理中 | 1 |
| 未送信 | 4 |
| 終端した失敗 | 0 |

採点済み3題の平均は、数学的妥当性0.9933、論理の十分さ0.9600、記号の一貫性
0.9600、学部生への説明の分かりやすさ0.9267、簡潔さ0.9367でした。
いずれも0〜1の独立LLM評価であり、学習者の理解度や数学全般の正答率ではありません。
5題は未採点です。完了3題の所要時間は12.206445秒、216.999681秒、365.152209秒で、
平均198.119445秒、nearest-rankのp50は216.999681秒でした。少数標本の最大値を
代表的なp95として台帳には記録しません。処理中の1題は163.067453秒の観測下限であり、
完了時間には含めません。費用と使用tokenの実測値は取得できていないため空欄です。

### 稼働版の訂正

準備時のsequence 28のmanifestは、実評価開始時には古くなっていました。
稼働中のAPIにマウントされた署名付きmanifestを読み直すと、実際にはsequence 29、
worker source `427caf8abadfc581bf5e33fc587cf2a24ee212ab`でした。
manifest SHA-256は`8a67d8ec7aa0bd1a51c58c83854831c28e1c20fc2f0568ce18d58ae3e4f53e97`で、
API source、verifier source、対象カタログは準備時と同じです。

元の記録・manifest・journalを保持し、別run IDの訂正版を作りました。
版の識別情報だけを訂正し、題材、採点器、点数、検証結果、時刻、所要時間が
変わっていないことを検査しました。既知の本番2ホストで同じ版のworkerだけが稼働し、
全依頼がその起動後に処理され、再起動がないことを確認しました。
これは稼働コンテナと処理履歴による運用上の照合です。各ジョブからコード版への
暗号学的な署名や、未観測の外部consumerの排除は主張しません。
同じ実験の元記録と訂正版を、独立した2回の評価として集計しません。

今回は比較前の初回観測です。プロンプト変更による改善率は測定していません。
認証の更新後は、保存したjournalから処理中の依頼を読み取りで回収し、未送信の題だけを
通常のAPIへ送ります。処理中の証明を重複送信しません。

### CloudWatchの保存・取得とグラフ

訂正版のrun IDは`seq29-ja-baseline-20261109-001-partial-cut1`です。
検証済みの内容を実際の`/pals/prod/prompt-quality`へ保存し、同一内容の読み戻しを
確認しました。その後、CLIの`fetch`で別ファイルへ取得し、保存元と完全に一致することを
再検査しました。正規化した記録のSHA-256は
`daf3c96b28195c3c86b90c98afadf64f8df9fb690a9ed6ed2e008ba018b5f2f7`です。
古い版情報を含む元記録はCloudWatchへ送信していません。

チャット内の3グラフは、取得した記録から確認件数、5指標、題ごとの所要時間を表示します。
全数値を取得原本と照合し、実ブラウザーの通常幅・360px・320pxで描画と文字切れを
確認しました。未送信の時間は空欄で、処理中は完了時間と区別して観測下限を表示します。
JSONL・集計JSON・CSV・訂正の証跡は、認証情報と分けてGit外の非公開領域に保持します。
今回の3件を数学全般の精度や、完成した8件のベンチマークとして扱いません。

## 継続評価と認証設定の変更

再ログイン後、既存の4題目を読み取りだけで追跡しました。189回のGETに対して
PALSへのPOSTは0回で、同じ証明の再送はしていません。観測終了時も依頼はverifying、
最後に確認した関連ジョブはsemantic_reviewでした。観測下限は1660.243879秒です。
未完了なので形式検証の成否と説明の点数は不明のままです。

別journalの残り4題では、2題が受理されましたが、回答言語が想定の日本語から
英語へ変わっていました。条件照合が不一致を検出したため、日本語の採点には含めません。
次の送信は429の`proof_request_rate_limited`で拒否され、最後の1題は送信を止めました。
これらを数学的失敗や0点とは扱いません。利用者の明示的な許可を受け、回答言語を
日本語へ戻し、通常の本人向けAPIで保存と読み戻しを確認しました。

事前確認が不足していた評価器は、今後の新規chat・quote・proof requestの直前に
回答言語を照合するよう修正しました。条件が異なる場合は送信せず、閉じた診断コードを
残します。既に受理された依頼の読み取り回収は妨げません。
実測時の評価器は`f588a0ec16e7af98ce4762089f3b46b97f366ae0`で、
この後続修正を実測時から存在したものとは扱いません。

追加の外部採点を含む回収操作は、自動承認審査で評価内容の外部モデル送信に対する
個別承認を確認できないとして拒否されました。代替として、外部採点器やその鍵を使わず、
本人向けのGETだけで状態を確認する操作が承認されました。実際の回収では外部モデルを
呼んでいません。完了していない説明の点数を補完していません。

### 30分のアクセストークン

利用者から15分ごとの再ログインを30分へ延ばす明示的な依頼を受け、
既存CognitoクライアントのAccessTokenValidityだけを15分から30分へ変更しました。
適用前の取得値と設定差分を固定し、適用後は更新可能な設定すべてを読み戻して、
この1項目以外に差分がないことを確認しました。発行済みトークンの期限は変わらず、
変更後に発行されるアクセストークンが対象です。新しいJWTを実発行して有効期間を
再測定したとは主張しません。

この既存クライアントは現行Terraformで参照だけのため、別stateへの二重importや
古いfoundation全体のapplyはしていません。再利用するguard付きoperatorと8件の
回帰検証をinfraに追加しました。初回のCLI入力搬送エラーはAWS APIへ到達する前に停止し、
0600一時ファイルへ修正後に適用しました。設定の読み戻しで目的の状態を確認しています。
operatorのcommitは`73b60387c9e24423b0722ed465fffa4a39198b25`です。

### 継続観測のCloudWatch取得

GETだけの追跡は`seq29-ja-baseline-20261109-001-recovery-cut2`、条件不一致と
送信制限の継続4題は`seq29-ja-remaining4-20261109-001`として保存しました。
両方とも読み戻しと別ファイルへのfetchを行い、送信元と完全に一致することを確認しました。
前者の正規化SHA-256は`217d913b32116761874c8ab3fe0a57ea6349f66df9350dac9e6b94cd8365977d`、
後者は`b0788ec64894f563b23b4f13587ada429acc77b28082e0cfc40e36866ae3c8ae`です。

チャットのグラフはrecovery-cut2から取得した日本語評価の観測値を表示します。
初回の3題を再採点したものではなく、処理中の1題の観測下限を更新したものです。
英語になった2題のDB上のansweredは、日本語の成功件数へ加えていません。
品質台帳には初回の1行に続き、重複を明示した継続2行と、30分設定operatorの2回の
実行を1行にまとめて追記しました。既存472行を保持した476行で、6グラフを再生成しました。
