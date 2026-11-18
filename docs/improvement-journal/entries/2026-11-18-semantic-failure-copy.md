# 意味審査の終端理由を表示する（2026-11-18）

対象は[#382](https://github.com/AtsushiHosaka/pals/issues/382)。APIが既に返す意味審査の不合格・利用不可を画面で区別し、利用者が一般的なLean失敗と取り違えないようにする。[Web PR #94](https://github.com/AtsushiHosaka/pals-webfront/pull/94)の候補は`d11e7a9171d9ba5f46bf1504e6cd8cccffdf32b4`である。

既知の型付き理由だけを表示し、未知値・型違い・別error_codeとの不一致は従来表示へ戻す。既存の4言語と再試行を保持した。ローカルの追加32回帰・関連138件・全体2233件と、型検査・lint・buildが成功した。実コンポーネントのnetwork遮断fixtureを375px・1024pxで確認した。これは表示契約の検査で、実モデルの回答率や本番履歴の検査ではない。

新規有料呼出・本番設定変更は0件。exact CIと配備後の保存・描画・reloadは未完了で、製品の精度改善率や所要時間・費用の変化は未測定である。実装候補として保持し、本番受け入れを別に確認する。

出典: [実装候補と検証範囲](../../382-answer-quality-candidate-2026-11-18.md)、Web PR #94内の検証note。
