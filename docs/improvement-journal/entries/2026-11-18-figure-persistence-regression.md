# 図付き回答の実DB保存・HTTP再取得（2026-11-18）

- 指標は、図付き回答の保存と再取得の正しさです。回答時間やモデル費用の改善は測定していません。
- 仮説は、serializerの単体検査に加え、実PostgreSQLと公開HTTP経路で図と段落の対応情報が残ることを確かめられる、というものです。
- 変更は[API #129](https://github.com/AtsushiHosaka/pals-api/pull/129)の`50a35c2b527f7a696ccf3d3ca98cbfd5f6399113`です。新規の回帰検査を追加し、製品の処理や本番設定は変更していません。
- API #129は`d837a647dc2de8b6004f3ff7e5e1f85ce9e6fb5c`へマージ済みで、マージ後の同じrevisionに対する必須CIも成功しました。
- 条件は、既存ローカルPostgreSQL上の専用DB、認証済み／ゲストと三次多項式／円周角の組み合わせ4ケースです。生成・審査の入力とCognitoの認証主体は固定した検査用データで、DB・repository・HTTP経路は実装を使いました。
- 結果は4件成功、skip 0件、pytest終了コード0です。図・段落の対応・本文を保存し、新しいTestClientによる2回のGET、認証済み履歴、別主体の404を確認しました。
- 初回の集計器はquiet出力に数値の集計行がなく誤判定しました。原本を保持し、収集4件・成功記号4個・終了コード0から補正しました。製品の失敗とは数えず、再実行していません。
- 前後比較ではDB一覧5件、role属性32件、membership6件が一致し、専用DBも削除済みです。
- 判断は、この境界の回帰検査を採用し、本番確認を続けることです。実モデル、Lean、Cognito、ブラウザ、本番は今回の成功に含めません。
- 費用は測定していません。モデル呼出しや新しい本番質問はありません。
- 出典は[検証記録](../../figure-persistence-regression-2026-11-18.md)、[#318](https://github.com/AtsushiHosaka/pals/issues/318)、台帳の`2026-11-18-figure-postgres-public-readback`です。本番の受け入れは`NOT VERIFIED`のままで、復旧は[#433](https://github.com/AtsushiHosaka/pals/issues/433)に記録します。
