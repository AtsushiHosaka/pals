# セキュリティ修正のレビュー対応記録

対象は[親PR #274](https://github.com/AtsushiHosaka/pals/pull/274)と[Web PR #51](https://github.com/AtsushiHosaka/pals-webfront/pull/51)です。モデルの数学的な品質と、ソフトウェアの回帰テスト結果を分けて記録します。

## 品質台帳から検証記録への移動

親PRの初期版では、次の11行を品質台帳へ追加しました。[台帳規約](../quality-ledger/ledger.schema.md)は単体テストやCIの通過件数を評価対象から除外しているため、この追加は不適切でした。実DBやLinuxの動作を含む行も、記録した数値はテスト項目数や準備試行の合計で、独立した運用測定の分母を定義していません。

全11行を[元のCSV形式の検証記録](security-regression-runs-2026-11-05.csv)へ移しました。ID、成功数、失敗数、分類、再実行との関係、注記は変更していません。台帳に元からあった370行は保持し、グラフを再生成しました。移動した行に含まれる31件の環境関連イベントと77件の未分類イベントは、品質グラフの集計対象から外れます。

下表のIDには共通の接頭辞`2026-11-05-security-`があります。数値は当時の実行結果です。後続の成功で初回の失敗を書き換えていません。

| IDの末尾 | 元の成功数／項目・実行数 | 記録の種類 |
|---|---:|---|
| linux-first | 22/24 | 実Linux境界と通常処理を含む回帰スイート。実行用一時領域の設定で2件失敗 |
| linux-fixtures | 2/2 | 上記2項目の実Linux再確認 |
| api-final | 157/157 | API・署名契約などの回帰テスト件数 |
| upload-dependency-first | 2/9 | 実DB添付の統合スイート。ローカルの依存不足で7件失敗 |
| upload-final | 13/13 | 実DB添付の統合スイート |
| signed-chain | 1/6 | 1つの署名付き実DB統合ケースの実行履歴。準備・比較で5回失敗し、最後に成功 |
| tls-sandbox-first | 30/52 | 実ソケット・TLSとテスト用検証器を含むスイート。サンドボックスのbind拒否で22件失敗 |
| tls-final | 56/56 | 通信・TLS・実行環境の回帰スイート |
| web-parallel-first | 1625/1697 | フロントエンドの単体スイート。UI待機やSSEのタイムアウトを含む72件失敗 |
| web-bounded | 1697/1697 | 同時実行数を2にした単体スイートの再実行 |
| web-parent-integrated | 1805/1805 | 親の先行機能を保持した後の単体スイート |

実ブラウザ、実DB、Linuxなどの境界を通った観察結果は、引き続き各PRと検証記録の証拠です。テスト項目の合計を、モデルや運用の品質測定に読み替えません。既存の非公開検証記録と、Web最終テストのJSON原本も変更していません。

## 数学記号を保持する共有タイトル

共有ページは保存済みのタイトルを`plainTitle`で変換します。従来の一括削除では、双対空間の`V^*`や畳み込みの`f*g`から星が消えました。旧Web側の既存修正と同じ契約を新しい変換へ引き継ぎ、数式と演算子の星を保ちながら、対応するMarkdown強調の区切りだけを除去します。

回帰テストは変換関数に加え、保存済み共有データの取得、正規化、匿名表示と、所有者の保存済みプレビューが対象です。MathLive、入力、設定、共有操作とセキュリティ修正は維持します。検証結果と公開コミットは対応PRに追記します。

本番配備、実アカウント、実ブラウザでの受入は今回の確認に含めていません。

## 今回の確認結果

タイトル修正前に追加した回帰例は、23件中21件が失敗して欠落を再現しました。修正後はタイトル、保存済み共有表示、既存OGの関連78件が成功しています。Webのlintと型検査も成功しました。数学starの処理は既存修正`b2abc6b`の関数を移植し、それ以外のLaTeX変換を変更していません。

台帳は370行で検査エラー0件です。台帳ツールの22テストも成功しました。移動した11行は旧台帳からCSVのバイト列を照合し、残る370行も元の順序と内容が変わっていないことを確認しています。既存の6グラフは同じ集計スクリプトで再生成しました。

実行したコマンドは次のとおりです。これらのテスト件数は品質台帳に追加していません。

```sh
# pals-webfront
npx vitest run tests/unit/plain-math.test.ts tests/unit/chat-sharing.test.tsx tests/unit/og-problem-text.test.ts --maxWorkers=2 --reporter=dot
npm run lint
npm run typecheck

# 親リポジトリ
python3 docs/quality-ledger/audit_ledger.py --json
python3 -m unittest discover -s docs/quality-ledger -p 'test_*.py'
python docs/quality-ledger/make_charts.py
git diff --check
```
