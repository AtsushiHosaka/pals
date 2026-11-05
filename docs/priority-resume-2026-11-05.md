# 高優先度Issueの再開記録

担当はCodex。[担当チャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)、全体の進行は[#237](https://github.com/AtsushiHosaka/pals/issues/237)に記録する。親の基準は`98cd28c50d14a2b233f3c35343bbd8d9b32c567f`。今回は保存原本の照合、未署名のクーポン候補準備、独立した実装2件を並列で進める。

## カード配備の確認

[#248](https://github.com/AtsushiHosaka/pals/issues/248)と判断[#256](https://github.com/AtsushiHosaka/pals/issues/256)は完了し、[記録PR#259](https://github.com/AtsushiHosaka/pals/pull/259)もmainへ統合済みである。[配備・X検証記録](og-footer-x-clearance-2026-11-05.md)では、seq20の本番適用、両ホストの7サービス・復旧設定、DB受理、一時権限の削除、公開PNGと版付き共有リンクの実X下書きを確認している。元リンクの古いpreviewは別の失敗観測として保持する。

今回、保存されたmanifestをSHA-256で照合し、従来の独立した公開鍵pinと同じ鍵でECDSA署名を再検証した。保存済みの両ホストの完了応答も、実行成功・対象manifest・公開済み証拠hashに照合した。新たなlive SSM確認ではなく、現在の稼働を再測定した結果ではない。

| 照合対象 | SHA-256・結果 |
|---|---|
| seq20 manifest | `2c7b96baa2d0b7577f52d5793fe5fb849639bdf688a5a86ef9814a17c2da6afa` |
| 保存済みcontrol最終確認 | `a42d87abe1a58a9ad5c43a31e53cd97124c77073de2c4751c2b1698da2be99ec` |
| 保存済みcompute最終確認 | `accfc2543ca8c43eff1612085a252315fbb6c4b1d008fb0c8106ab931189370d` |
| 今回の保存原本照合 | 署名と2応答が一致。新しい本番操作0回 |

署名の期限は**2026年11月6日15:03:04 JST**である。署名更新・期限後の復旧・実OS再起動の未了は[#142](https://github.com/AtsushiHosaka/pals/issues/142)で継続する。

## 作業範囲と受入

| Issue | 固定する基準と今回の範囲 | 残る境界 |
|---|---|---|
| [#234](https://github.com/AtsushiHosaka/pals/issues/234)・[#244](https://github.com/AtsushiHosaka/pals/issues/244) | API`5c1a2fd7`、Web`a91cf9ee`、infra`fb9d2249`、worker`6e5c58de`、verifier`189b4437`。seq20保存原本を前提にclean sourceと新Web imageを照合し、次候補を具体化する | 旧fa94・#255承認は使用しない。freshな本番前提・排他、署名・検証権限、schema36受理、本番の引換・Plus機能は別受入 |
| [#250](https://github.com/AtsushiHosaka/pals/issues/250) | API#52の`6985402`から、既存の支払回収と13か月保持削除を有限周期で実行するCLIを準備する | 本番のcapture拒否を保持。定期実行の配備、実Stripe、操作tracker、CloudWatch集計は未完了 |
| [#217](https://github.com/AtsushiHosaka/pals/issues/217) | Agent#51の`74a6d5e`から、通常ファイルへの品質event部分書込と並列appendの整合性を修正する | best-effortの欠測・OS停止後の永続配送、本番collector稼働は保証しない |

各担当は別の作業領域を使い、既存の依存環境・停止済み試験DBを再利用する。単体試験の件数を数学の精度へ加算しない。実装後は別担当が差分と根拠を確認し、親担当が結果・未検証範囲を照合する。

## クーポン準備で判明した制約

自動承認レビューが、新Web imageを既存の非公開ECRへ保存する操作を拒否した。この保存先への非公開source由来成果物の送信について、今回の明示承認がないことが理由だった。同じ送信を別経路で再試行せず、ローカルbuildと検査を継続する。未送信のimageに本番のpublication証拠があるとは記録しない。送信するimageと保存先を特定し、必要な承認を求める。

クーポン条件は[#240](https://github.com/AtsushiHosaka/pals/issues/240)・[#241](https://github.com/AtsushiHosaka/pals/issues/241)で回答済みの、上限100人・1人1回・引換後Plus1か月・発行から30日以内の引換を維持する。発行は0件のままである。
