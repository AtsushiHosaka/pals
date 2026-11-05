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

## クーポン候補の準備結果

自動承認レビューは、新Web imageを既存の非公開レジストリへ保存する操作を、明示承認の不足により拒否した。ローカルbuildと独立照合を完了して対象を示した後、オーナーは「このimageのECR保存を承認する」と回答した。[判断#261](https://github.com/AtsushiHosaka/pals/issues/261)に承認範囲を残した。具体的な保存先・非公開artifact識別子の公開記録も拒否されたため、本書には含めない。

承認後、照合済みimageを再buildせず新規タグで保存し、実digestと再取得後の実体を確認した。一時認証cacheは削除済み。cleanな5リポジトリのsource capture、4役割のOCI実体、正式receipt、seq20保存署名、APIの正規validatorと35→36の1段階append・専用planを照合し、**未署名のseq21候補**を作成した。親担当もcanonical bytes、正確な変更field、不変のworker/verifier・runtime binding・platform、4役割のID・構成・layerを独立照合した。

[source固定PR#263](https://github.com/AtsushiHosaka/pals/pull/263)は、前候補のsource branchに対するWeb gitlinkだけの差分で、mainへ統合していない。候補の期限は**2026年11月6日16:40:50 JST**。これは未署名候補の期限であり、稼働中seq20の期限を延長したものではない。正確な候補・receipt・image識別子と原本は、Git外の0700/0600領域で保持する。最初のsource captureは担当生成のbytecodeを検出して拒否し、その生成物だけを除いた再実行が成功した。不完全な初回出力は採用していない。

freshな本番predecessor・排他とnative readinessは未確認。KMS署名、IAM変更、追加SSM読取、DB受理・本番切替・コード発行は0回。旧#255への承認を新候補へ流用しない。ECR保存の承認を、これらの操作へ広げない。

クーポン条件は[#240](https://github.com/AtsushiHosaka/pals/issues/240)・[#241](https://github.com/AtsushiHosaka/pals/issues/241)で回答済みの、上限100人・1人1回・引換後Plus1か月・発行から30日以内の引換を維持する。発行は0件のままである。

## 並列実装と独立レビュー

| 範囲 | 実装・検証・統合 | 未検証 |
|---|---|---|
| 品質ファイル出力 #217 | [Agent#57](https://github.com/AtsushiHosaka/pals-agent/pull/57)。非blocking排他・部分appendの回収・inode/権限の再検査。担当199件と別のworker等94件、親の独立112件が通過。品質統合PR#51へ`aedef030`で通常merge | 永続outbox、OS停止後配送、本番collector・CloudWatch抽出・通知。coupon36の固定workerには追加しない |
| 支払周期処理 #250 | [API#67](https://github.com/AtsushiHosaka/pals-api/pull/67)。既存の回収・13か月削除を有限周期で実行し、資格情報を分離。同じDBを要求し、deadline/停止時に子processとDB sessionを解放。担当33単体・契約と47実PG、独立26単体と5実PG、親33単体・契約が通過。統合PR#52へ`5daf8ec`で通常merge | 実Stripe、production37受入、配備された定期実行、操作tracker・CloudWatch。本番captureの拒否を保持 |

両差分の独立レビューにP0–P2の指摘はなかった。APIの最初の実PG/CLI5ケースは4/5で、interval待機中のSIGTERM後に次周期の停止結果を余分に出した。次の子processは起動していない。周期開始前の停止検査を加え、同じ5ケースが5/5になった。別担当も5/5を確認した。この局所的な運用試験を、支払全体・本番稼働・モデル精度の成功率へ読み替えない。

初回JUnitのSHA-256は`754e771e35a3be7028d2d847920ea9b69da43b4f92dba1ea833742a1c8384722`、修正後の47件JUnitは`73cc6114a63a2fee88d3a651a56f58f311a91c40c53696930cf7e37e01678fe6`。台帳には同じ5つの運用ケースの初回・修正後を別行で残し、単体・既存回帰の通過件数を加算しない。

既存の試験PostgreSQLを再利用し、元の3DBと38roleのflag行が前後で一致、他client0を確認して正常停止した。データとログは保持する。Agentの実ファイル・実socket試験のprocessも終了した。既存mypyの無関係なunused-ignoreとStarlette/httpxの警告は残り、限定mypy・Ruff・diff検査は通過した。
