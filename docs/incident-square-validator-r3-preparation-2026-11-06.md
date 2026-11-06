# 平方連続性の説明検査R3の準備記録

R3 sourceは[Agentのcommit 210ece8912b65e9bbb023b3341f7a1af9de09ae4](https://github.com/AtsushiHosaka/pals-agent/commit/210ece8912b65e9bbb023b3341f7a1af9de09ae4)へpush済みです。比較元は本番R2のworker source `cc75c3fb2d4ec18b2e30b1f4eea9fa0c304ea171`です。この記録の時点でR3は本番未配備で、利用者への説明の正常表示・保存・再読込は確認していません。進行は[#223](https://github.com/AtsushiHosaka/pals/issues/223)、変更内容は[Agent PR #60](https://github.com/AtsushiHosaka/pals-agent/pull/60)で追跡します。

## 修正と確認範囲

R3は標準LaTeXのdelimiter・alignment表記と、一意に定義された正の補助定数を扱います。別cellや別行のatomを積へ連結せず、定数の再定義・変数の衝突を拒否します。誤差評価の打消しは、十分性検査を通った同一分母またはその別名に限定します。固定点・近傍・因数分解・strictな評価の対応、正確なLean参照、独立QA、試行上限を保持しています。

最終sourceのblobは`b6cbe29867ccaaecb54b10d1d88a23480a9f3b33`、ファイルのSHA-256は`6c14877d987bed9e3c498d7c10654bf1d4c0d136dfc9dd64e58865dcc0310b35`です。比較元のsource blobは`a266e07de6a2478511f34da54711bf390edf8c78`、SHA-256は`ecce4823a29adc0cbce8e5e7b7c970d7e0d5a3ae51a5aa94e9029f7130f264a7`です。

## 固定70件の比較

既存の妥当なε–δ証明を14通りに表記し、同じ表記変換を3種類の数学的不正な説明と、弱い終端の対照へ適用しました。変形後のmarkupを戻すと各元入力に一致することを、gateとは別の処理で確認しています。入力・判定の原本はGitへ含めず、公開可能な合成回帰は[Agentの専用テスト](https://github.com/AtsushiHosaka/pals-agent/blob/210ece8912b65e9bbb023b3341f7a1af9de09ae4/tests/unit/test_x_squared_validator_notation.py)にあります。

| 群 | 成功の定義 | 件数 | baseの成功 | R3の成功 | gate受理数 base→R3 |
|---|---|---:|---:|---:|---:|
| 正しい同一証明 | 表記を変えても受理する | 14 | 5 | 14 | 5→14 |
| 数学的不正な説明 | 誤delta・別の点・誤った積を拒否する | 42 | 42 | 42 | 0→0 |
| 弱い終端のgate対照 | 必要なεへの橋渡しを欠く対照を拒否する | 14 | 13 | 14 | 1→0 |

最後の群は、正しいdeltaと補助評価を保持したまま、評価の終端を弱めた対照です。数学的に偽の命題や証明だとは扱いません。表記によって結論文を評価の橋渡しとして拾うかを見る、gateの構造検査です。3群の率を合算して数学全般やモデルの精度改善率にはしません。

品質台帳にはこの3群をbaseとR3へ分けた6行を追加しました。successesは上表の成功数です。baseの正例9件の誤拒否と、弱い終端対照1件の受理は、モデルQAではなく製品の固定検査の欠陥として`infra.app_defect`に分類しています。単体検査526件は分母へ加えていません。既存456行のbytesを保持し、費用・latency欄は空欄です。この局所比較による追加モデル呼出しは0です。

## 新sampleと実Lean参照の確認

別途承認された1回の隔離診断で新しく生成された説明を、実際に保存された66行のverified Leanと組み合わせ、R3のfull parserへ渡しました。3 sectionsの4件の正確な参照、日本語、専用gate、末尾条件を通過しました。これは追加モデル呼出しを伴わない保存入力の局所再実行です。元の本番3出力は未保存のままで、その内容や拒否理由の詳細を復元したものではありません。このsampleの独立モデルQAや、R3配備後の公開E2Eも未実施です。

## その他のsource検証

既存incident回帰62件と新しい表記・別名回帰154件を含め、関連9ファイルの526 testsが成功しました。Ruff、sourceのstrict mypy、差分検査も成功しています。HTTP期限検査は一時的なloopback listenerの起動だけに必要な権限を使い、外部API・AWS・モデル・DBへ接続していません。worker storyは43成功・既知のbaseline失敗1件で、合成clockの期待330に対して変更していないtimeoutが2000になる差を保持しています。

最終sourceの独立レビューでは216回帰、9件のguard対照、11件のliteral denominator対照、実66行とのfull parserを確認し、追加P0〜P2の指摘はありません。これらはsourceの検証であり、配備や本番説明成功の証拠とは分けます。

詳細な検査条件・限界は[Agentの検証記録](https://github.com/AtsushiHosaka/pals-agent/blob/210ece8912b65e9bbb023b3341f7a1af9de09ae4/docs/verification/x-squared-validator-notation-alias-2026-11-06.md)にあります。この文書と台帳へprivate sample、Lean全文、host、IP、tokenは転記していません。
