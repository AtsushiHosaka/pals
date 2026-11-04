# 失敗分類(提案)

`ledger.csv` の `failures_json` と、今後の評価記録で使う失敗コードの一覧です。リポジトリの docs、PR 本文、Issue に実在した文字列を出発点にしています。分類の名前と通知方針は提案であり、通知の仕様は #215 と #217 でオーナーが決めます。

## 使い方

- コードは `<tag>.<name>` の形です。`tag` は `infra` / `verifier` / `model` / `review` / `policy-refusal` のどれかです。
- 1つの失敗は1つのコードにだけ数えます。迷ったら下の「判定の順序」に従います。
- 原因が出典に書かれていないものは `unclassified` にします。推測でコードを選びません。元の文字列は `failures_raw_json` に残します。
- 「通知」列の意味は次のとおりです。**即時** は1件でも運用者に知らせる。**率** は一定時間の件数または失敗率がしきい値を超えたときに知らせる。**集計** は通知せず、台帳とダッシュボードで推移を見る。**なし** は正規の挙動で、通知しない。

## 判定の順序

1. 利用者の入力や数学の内容に関係なく起きた失敗は `infra`(基盤、ネットワーク、容量、配備、計測の仕組み)。
2. Lean 検証器が結果を返した失敗、または検証器が信頼できないと判定した失敗は `verifier`。
3. モデルの出力が原因の失敗は `model`(証明を書けない、形式が不正、選択が不正)。
4. 審査(再利用の判定、回答QA)が却下または誤承認した失敗は `review`。
5. 仕様上の正規の拒否は `policy-refusal`。障害ではない。
6. 上のどれにも当てはまらず原因が不明なら `unclassified`。

## 基盤の失敗(infra)

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `infra.timeout` | 時間制限を超えた(検証のコンパイル、診断の30秒、有界チェックの45秒) | `exceeded 45 s bounded check`、`30秒でタイムアウト` | 率 | 3 / 3 |
| `infra.http_5xx` | 経路が 5xx を返した | `guest_network_unavailable (HTTP 503)` | 即時 | 1 / 1 |
| `infra.capacity_or_quota` | プロバイダーの上限、メモリ、プロセス数、スレッド数の不足 | `insufficient_quota`(HTTP 429)、`failed to create thread`、保持PID | 即時 | 4 / 5 |
| `infra.network_or_dependency` | 依存先の切断、ポート競合など | `BrokenPipeError`、`EADDRINUSE` | 率 | 3 / 3 |
| `infra.verifier_interrupted` | 検証のコンパイルが OOM、fork 拒否、監督プロセスの死亡で中断された | `lean.compile_interrupted`、503 `verifier_compile_interrupted` | 即時 | 0 / 0(pals-agent#30 の記述のみ) |
| `infra.cache_fallback` | 環境キャッシュを使えず元の経路に戻った | `lake_env_cache_fallback` | 集計 | 1 / 36 |
| `infra.result_parse_failure` | 計測や診断の出力を読み取れなかった(検証自体は成功) | `結果読み取り失敗(診断出力解析)` | 集計 | 1 / 1 |
| `infra.app_defect` | 製品側の欠陥(設定の読み込み、共有プレビュー、再開処理など) | `Mathematics settings could not be loaded.` | 率 | 9 / 18 |
| `infra.monitoring_gap` | 監視が異常を検知できなかった | `monitor false healthy`、`alarm_not_transitioned` | 即時 | 2 / 2 |
| `infra.queue_auth_unavailable` | キュー確認の AWS 認証が使えない | `queue_aws_authentication_unavailable` | 即時 | 0 / 0(配備記録のみ) |
| `infra.deploy_subprocess_failed` | 配備の子プロセスが失敗した | `edge_subprocess_failed`、`scoped_host_subprocess_failed_private_log_retained` | 即時 | 0 / 0(配備記録のみ) |

## 検証器の失敗(verifier)

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `verifier.trusted_audit_failed` | 検証器の信頼監査(成果物、`.olean`、axiom の検査)に通らなかった | `lean.trusted_audit_failed` | 即時 | 0 / 0(pals-agent#30 のテスト記述と #215 の記述のみ) |
| `verifier.runtime_unavailable` | Lean の実行環境が使えない | `Lean verification is not available right now` | 即時 | 1 / 1 |
| `verifier.lean_compile_error` | Lean のコンパイルエラー(型の不一致、`no_goals`、宣言の重複など) | `lean.compile_error`、`lean.type_mismatch`、`lean.no_goals` | 集計 | 4 / 6 |
| `verifier.statement_mismatch` | 証明された命題が依頼の命題と一致しない | `lean.statement_mismatch`、`statement type changed under narrower imports` | 集計 | 2 / 7 |
| `verifier.formal_harness_mismatch` | 形式化の枠(harness)と入力の成果物が一致しない | `lean.formal_harness_mismatch` | 集計 | 1 / 7 |
| `verifier.theorem_alignment_failed` | 最上位の定理が複数あるなど、単一ターゲットの検査に通らない | `pals.theorem_alignment_failed` | 率 | 1 / 2 |
| `verifier.heartbeat_limit` | `maxHeartbeats` の上限に達した | `maxHeartbeats limit` | 集計 | 1 / 10 |
| `verifier.statement_format_error` | 古い形式の命題で `exact?` がエラーになった | `statement error (old format)` | 集計 | 2 / 34 |
| `verifier.exact_not_closed` | `exact?` の事前チェックで閉じなかった。失敗ではなく通常の結果 | `exact? not closed` | なし | 1 / 84 |

## モデルの失敗(model)

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `model.could_not_prove` | 修復の上限までに証明を完成できなかった | `repair_budget_exhausted`、`修復12回を使い切って失敗` | 集計 | 15 / 34 |
| `model.invalid_response` | 出力が不正(形式、引用、トークン上限による途中切れ) | `proof_reuse_invalid_response`、`material_citation_invalid` | 率 | 7 / 34 |
| `model.selection_invalid` | 応答が選択の規則に反する | `response_nonreuse_selection_invalid` | 率 | 1 / 5 |
| `model.preflight_misjudgment` | 事前判定が反例や選択肢を見落とした、または過剰に質問した | `preflight_missed_counterexample` | 集計 | 6 / 15 |
| `model.structuring_fidelity_error` | 型付き構造化が元の命題と食い違った | `structuring_fidelity_error` | 集計 | 2 / 3 |

## 検索の失敗(retrieval、タグは model)

検索(埋め込みや BM25 などの検索部品)側の失敗です。モデル部品の品質として扱うので、タグは `model` です。

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `retrieval.index_miss` | 検索が正解の前提やカードを返さなかった | 日本語の要求文での前提検索が 0 件 | 集計 | 1 / 16 |
| `retrieval.unmatched_recipe` | 同値な入力が既存の Recipe に結び付かなかった | `equivalent input not accepted` | 集計 | 0 / 0(重複する行へ統合済み。出典は pals#128、#129) |

## 審査の失敗(review)

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `review.rejected` | 再利用の判定や回答QAが却下した | `対応確認で再利用拒否`、`The answer did not pass the required review` | 集計 | 8 / 13 |
| `review.false_accept` | 審査が誤ったカードの再利用を承認した(誤再利用)。正しさの回帰を見る指標 | `false reuse of 2-D card`、`誤再利用` | 評価で1件でも出たら即時(回帰検知) | 9 / 192 |
| `review.unavailable` | 独立した審査が完了しなかった | `review_unavailable` | 率 | 1 / 1 |

## 正規の拒否(policy-refusal)

| コード | 定義 | 出典での文字列の例 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|---|
| `policy.guest_formal_unavailable` | ゲストは新規の Lean 証明生成を使えない。カタログで答えられない質問は生成前にこのコードで止める | `guest_formal_unavailable` | なし(件数は製品指標として集計) | 0 / 0(specs/public-guest-chat の記述のみ) |
| `policy.unsupported_request` | 要求が再利用の評価の対象外で、Lean の検証前に止まった | `proof_reuse_unsupported` | 集計 | 1 / 1 |

## 分類に入れないもの

| コード | 意味 | 通知 | 台帳での行数 / 件数 |
|---|---|---|---|
| `audit.coverage_gap` | 機能監査で「未検証」「部分確認」「ブロック」だった項目。失敗ではなく、確認できていないという状態 | なし | 3 / 12 |
| `unclassified` | 出典に原因が書かれていない失敗 | 集計(四半期ごとに分類を見直す) | 6 / 17 |

## 通知の方針案(#215、#217 の入力)

- **即時に通知する**: `infra.*` のうち上表で「即時」のもの、`verifier.trusted_audit_failed`、`verifier.runtime_unavailable`。1件でも検証器や基盤の健全性に関わるためです。
- **率で通知する**: `infra.timeout`、`infra.app_defect`、`model.invalid_response` など。同種を一定時間内で1通にまとめ、失敗率がしきい値を超えたときだけ知らせます。しきい値は、このコードの台帳の履歴から決めます。
- **集計だけにする**: 数学的に証明が成立しなかった失敗(`model.could_not_prove`、`verifier.lean_compile_error` など)と審査の却下です。利用者の質問ごとに起きるため、1件ずつ通知すると洪水になります。
- **通知しない**: `policy.*` の正規の拒否、`verifier.exact_not_closed`、`audit.coverage_gap`。
- 「台帳での行数 / 件数」は、重複を除いた行のうち`overlap_with`が空のものを数えた、2026-11-04時点の値です。件数は同じ質問を繰り返した実行も数えるため、行数と一緒に読みます。
