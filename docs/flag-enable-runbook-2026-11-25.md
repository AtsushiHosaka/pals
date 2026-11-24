# フラグの有効化と戻し方（1ページ版、2026-11-25）

pals#385（cheap-first ほか）、pals#318（図）、[pals#370](t2-cheap-first-enable-runbook-2026-11-14.md)（cheap-first の手順書）、[意味審査の作り直し](semantic-review-reformalize-rollout.md)を統合した。数値と危険は各原典のまま。この文書は有効にする判断を代行しない。リリース担当が「3. 前提」を確かめてから進める。

## 1. 仕組み（pals-infra の `runtime_flags`）

- plan input に `"runtime_flags": {"PALS_…": true}` を書く。許可されるのは下表の名前だけ（閉じた集合）。bool は JSON の真偽値で、文字列は拒否される。未知の名前、認証情報・URL・DB 名、空の object も拒否される。
- 宣言した値だけが、その対象の env に届く。宣言がなければ従来どおり（既定は無効）。次の release は前の release の env から始まり、宣言した名前だけを上書きする。**宣言した値は、後の release で別の値を宣言するまで残る。**
- 保存先: `api` は制御ホストの api コンテナ、`proof` は計算ホストの proof ワーカー。ホスト側のローダーも、閉じた値以外と、別の対象のフラグを拒否する。
- 実装: pals-infra の `release_plan.py`（plan）、`release_native/binding.py`（binding）、`render.py` と `native_prepare.py.tmpl`（render・template）、`compute_runtime.py`・`control_runtime.py`（ホスト側）。

## 2. フラグ一覧

| 機能（出典） | 変数と値 | 対象 | 測定された効果 | 危険 | 戻し |
|---|---|---|---|---|---|
| cheap-first（pals-agent#129） | 次の7つを `true`: `PALS_T2_CHEAP_FIRST_ENABLED`、`PALS_T2_SOURCE_HYGIENE_ENABLED`、`PALS_T2_NAME_SAFETY_ENABLED`、`PALS_T2_PATCH_REPAIR_ENABLED`、`PALS_T2_NO_DRAFT_ENABLED`、`PALS_T2_PARALLEL_EXPLANATION_ENABLED`、`PALS_T2_PARALLEL_REVIEW_ENABLED`。`PALS_T2_HETERO_RACE_ENABLED`・`PALS_T2_PARALLEL_CANDIDATES_ENABLED`・`PALS_T2_NO_SKETCH_ENABLED` は `false` のまま。`PALS_T2_FIRST_EFFORT` は省略（既定 low） | proof | 30秒以内 9→12〜13/20、1問の費用 約0.032→0.012〜0.016 ドル | 整形が提出の header を書き換える。`lean.formal_harness_mismatch`・`lean.statement_mismatch` が増えたら戻す。1ジョブの費用 US$0.03 超でも戻す | 7つを `false` と宣言する |
| 解説の新しい経路（pals-agent#127 ほか） | `PALS_EXPLANATION_V2_ENABLED`、`PALS_EXPLANATION_FALLBACK_ENABLED`、`PALS_EXPLANATION_COVER_ALL_LINES_ENABLED`（いずれも `true`）。`PALS_EXPLAIN_EFFORT` は `none` か `low`（省略で release 束縛のまま） | proof | 新しい解説の経路で 3/9→9/9 | v2 は Draft が無い依頼では v1 に戻る。解説の審査の却下率を見る | `false`（`PALS_EXPLAIN_EFFORT` は省略に戻せないため、直前の値を宣言） |
| 意味審査の作り直し（pals-api#108、#124） | `PALS_SEMANTIC_REVIEW_REFORMALIZE_ENABLED`=`true`（api は `"true"` 完全一致以外を黙って無効とみなす） | api | 回答が返る 9/12→12/12、費用 +27% | 却下された依頼だけ +100〜160 秒、約 US$0.04〜0.07/件。`PALS_PROOF_UNVERIFIED_DEADLINE_SECONDS` の設定時は「期限−150秒」が残る依頼だけ対象。作り直し後の `answered` 率が低い、または増分が却下件数×約 US$0.05 を超えたら戻す | `false`。進行中の作り直しは通常のジョブとして完了し、DB の巻き戻しはない。旧版 API へ戻す前に、画面が `lean_semantic_review_*` の `error_code` を扱えるか確かめる |
| 検証済みを先に表示（pals-api#109、pals-webfront#72） | api: `PALS_VERIFIED_FIRST_ENABLED`=`true`（`true`/`false` 以外は起動拒否）。web: ビルド引数 `NEXT_PUBLIC_PALS_VERIFIED_FIRST_ENABLED=true`（**実行時の変数ではなく、web イメージの再ビルドが要る**） | api と web ビルド | 10秒以内に表示される依頼 4/20（表示の体感の短縮） | 表示の順序が変わる（オーナーの判断が要る）。api だけ on なら変化はない（ヘッダを送る web が無い）。web だけ on なら再取得が2秒間隔になるだけ。**api を先に有効にする** | api は `false`。web は `false` で再ビルド |
| 信頼の水準の返却（pals-api#107） | `PALS_LIBRARY_TRUST_FIELD_ENABLED`=`true` | api | 未レビューの形式化への依存を表示できる | web は常に受理するので安全。応答に `library_trust` が増える | `false` |
| 図（pals#318）・代数幾何（pals-agent#128・#134・#136） | **フラグなし（常時有効）**。図の検証と登録表は、図を含む候補の worker/api イメージに入っていれば動く。代数幾何の案内はスキーム論の質問にだけ効く | — | — | `PALS_DIAGRAMS_ENABLED`（図の描画ルート）は別機能で、描画サービスの URL・token と専用プロセスが要る。閉じた集合に入れていない | 戻すにはイメージを戻す |

## 3. 前提

1. 配線を含む release（pals-infra の `runtime_flags`）が accepted になっている。それより前は、宣言しても届かない。
2. API は `#124` を含む候補、web は `#94` の表示（意味審査の不合格と利用不可の区別）を含む候補であること（作り直しを有効にする場合）。
3. cheap-first は本物の API でのカナリアと、本番の検証器に対する整形後の提出の確認を、有効にする前に済ませる（pals#370 の「事前に確かめること」。未実施）。
4. `compute_runtime.py` と `control_runtime.py` の内容が変わるため、署名・配置・cutover は通常どおり release 担当が行う。

## 4. 有効にする順序

一度に有効にするのは1つの機能まで。各段で下の「5. 監視」を見て、問題がなければ次へ。

1. 信頼の水準（api）。害が最も小さい。
2. 検証済みを先に表示（api を先、web のビルドは別の release）。
3. 意味審査の作り直し（api）。
4. cheap-first の7つ（proof）。
5. 解説の新しい経路（proof）。

宣言を plan input に書いた release が accepted になるまで、有効にはならない。env だけを変える release（イメージが同じ）の cycle の扱いは、実機担当に確かめること（未確認）。

## 5. 監視と有効化後の測定

- 共通: CloudWatch で `failure_reason`、回答が返る割合、依頼の所要時間 p50/p90、1依頼あたりの生成費用を、有効化の前後で比べる。
- 作り直し: `failure_reason=semantic_review_failed` の件数、`proof_request_lean_jobs` が2件の依頼数、作り直し後の `answered` 率。
- cheap-first: `lean.formal_harness_mismatch`、`lean.statement_mismatch`、初回の成功率、1ジョブの費用 p50/p90。
- 有効にしたフラグごとに、本番の構成で同じ題を1回測り（各 US$1 以下）、手元の測定と同じ向きか確かめる。逆なら、そのフラグを `false` と宣言する release で戻す。

## 6. 戻し方（共通）

後の release の plan input で、そのフラグを `false`（`PALS_EXPLAIN_EFFORT` は直前の値）と宣言する。env の行を消す方法はない。状態の移行はなく、データの巻き戻しは要らない。cutover に失敗した場合は、通常の復旧（直前の release の env に戻る）に従う。
