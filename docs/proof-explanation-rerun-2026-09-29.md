# 説明の再発確認：実アプリでの再実行（2026-09-29）

## 結果

**追記：ユーザーの明示承認後、新規説明5件の再発確認を完了した。**

実アプリの全経路1回と、既存の検証済みLeanを使う説明生成＋production QA 4回を実施した。
5本文とも、以前の「冒頭で証明を完結し、後続段落で同じ導出を再度行う」重複は再発しなかった。
QAは4件承認・1件拒否。拒否理由には数学的な誤判定があり、QAの安定性が完全に解決したとは言えない。
詳細・全候補・拒否理由は [承認後の再検証報告](proof-explanation-approved-rerun-2026-09-29.md) を参照。

以下は承認前の失敗と修正の記録である。

既存Chromeの同じPALSタブから、元と同じ二項平方の問題を再送信した。
新規ジョブ `57b778ad-b76b-4448-bca5-669ca5f6b003` が作られ、実際の生成・Lean検証・修復経路が動いた。
しかし、生成された定理名がMathlibと衝突し、説明生成へ進めなかった。
説明が出なかったことを「重複が再発しない」証拠には数えない。

修復を12回使い切る境界にも不具合があり、最終候補が受け付けられず「コンパイル中」のまま残った。

## 発見した不具合

生成コードは次のとおりだった。

```lean
import Mathlib

theorem add_sq (x y : ℝ) : (x + y) ^ 2 = x ^ 2 + 2 * x * y + y ^ 2 := by
  ring
```

Mathlibには既に `add_sq` が存在する。保存された候補を既存verifierでローカルコンパイルし、
3行目8列目の `` `add_sq` has already been declared `` を再現した。
修復は同じ宣言名を残して `ring` / `nlinarith` を入れ替えていたため、この原因を解消できなかった。

isolated verifierのHTTP応答は内容を含まないエラーコードに制限されており、修復側へは具体的な名前衝突の診断が渡っていない。
詳細診断を渡すには、verifier→API→永続化→worker間の契約を変更する必要がある。この経路の変更は今回未実施。

## 修正とローカル検証

- 新規の自然言語要求から作る定理には、要求IDと問題文に由来する安定した `pals_target_<hash>` 名を使うよう、生成・修復の共通指示を追加した。
- API上の要求IDが `custom_statement` に固定される場合も、異なる問題文には異なる名前を割り当てる。
- ユーザーが定理名・形式的harnessを明示した場合はそれを維持する。命題・引数・型や既存Mathlib定理への参照を勝手に書き換えない。
- 関連60テスト、型チェック、lintに合格。同じ命題で名前だけを変更した候補はローカルLeanでコンパイル成功した。
- これは生成指示の修正であり、実モデルが指示に従い、最後まで完了することの検証は別途必要。
- APIの修復境界を修正し、初回に加えて指定回数の修復候補を受け付け、最終候補のLean失敗を永続的な `failed` として終了するよう変更した。
- 旧候補のエラーを新しい候補に適用しないよう、生成コード・ハッシュ・試行ごとの `result.json` / `result.lean` の対応を確認する。読み取りAPIだけで未保存の失敗を作り出さない。
- API関連83テストと、既存Postgresを使った最終候補の取り込み→失敗永続化→再処理無変更の2テスト（修復上限1／12）が成功。型チェック・lint成功。
- 同じローカルAPI・reconciler・workerへ反映した。スタック・Chromeを追加起動していない。

## 停止したジョブの正規経路での再処理

保存済みの最終候補を、まだ有効な元のclaimで内部の候補取り込みAPIへ1回だけ再送した。
送信直前に対象問題、attempt 13／修復12回、DBとS3のコード・ハッシュ・成果物の一致を検証し、APIはHTTP 200で受け付けた。
名前衝突する既知のコードそのものに固定し、新たな生成・外部モデル呼び出しや直接DB更新を行っていない。
成功した証明へ差し替える操作ではなく、実際のLean失敗が正しく終了するかの確認である。

再処理後、公開APIで `failed` の永続化を確認した。API再起動でブラウザの状態接続が切れたため、
画面の「Retry status connection」を押して再接続し、「証明を検証できませんでした。」への切り替わりも確認した。
この時点では修復終了処理の実経路を確認し、新規生成・説明の再発検証は承認待ちだった。その後の実施結果は上記の追記を参照。

## 追加の実モデル検証

新規説明を5回生成してQAへ渡す検証を準備したが、自動承認審査が外部送信を拒否した。
送信対象が一般的な二項平方の問題・4行のLeanコード・生成説明だけであることを確認し、再審査しても拒否された。
その時点では、この追加バッチの外部モデル呼び出しは0件。ユーザーへ具体的な内容・OpenAIの送信先・回数の承認を質問した。
準備したバッチを実施済み・成功済みとして数えていない。

## 証跡（ローカル生成物、コミット対象外）

- `output/explanation-rerun-20260929/app-run-1.json`: 新規ジョブのAPI応答と観測履歴。
- `output/explanation-rerun-20260929/job-57b778ad-verification.json`: 候補・修復イベント。
- `output/explanation-rerun-20260929/job-57b778ad-current.lean`: 保存された生成候補。
- `output/explanation-rerun-20260929/job-57b778ad-local-compile.json`: 既存verifierでの名前衝突の実コンパイル結果。
- `output/explanation-rerun-20260929/runtime-before.json`: サービス稼働・キュー・有効claim等の読み取り記録。
- `output/explanation-rerun-20260929/generation-batch.json`: 追加バッチの未実行・承認ブロック記録。
- `output/explanation-rerun-20260929/app-run-1-state.png`: 同じChromeタブの実画面。
- `output/explanation-rerun-20260929/replay-final-candidate-preflight.json`: 再送前の整合性確認（秘密情報なし）。
- `output/explanation-rerun-20260929/replay-final-candidate-submit.json`: 正規APIが最終候補を受け付けた記録。
- `output/explanation-rerun-20260929/app-run-1-terminal.png`: 再処理後、失敗として終了した実画面。
- `output/explanation-rerun-20260929/final-repair-fix-validation.json`: APIの単体・実Postgres検証結果。
