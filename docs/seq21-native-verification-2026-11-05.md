# seq21のnative準備と読取検証

担当はCodex。[担当チャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)。進行は[#234](https://github.com/AtsushiHosaka/pals/issues/234)・[#244](https://github.com/AtsushiHosaka/pals/issues/244)、今回の承認は[判断#271](https://github.com/AtsushiHosaka/pals/issues/271)に対応する。[署名と準備の前段記録](coupon21-production-preparation-2026-11-05.md)を引き継ぐ。

## 今回の結果

両ホストのnative準備と、署名済みseq21に対する読取検証が成功した。本チャットではDB書込・新schemaの受理・admission・drain・サービス停止や再起動・本番切替・クーポン発行を実施していない。19:47の検証後checkpointでは本番seq20を確認した。その後、別チャットの#265が本番更新の所有権を保持してdrain中だと判明したため、クーポン側の切替準備は最新predecessorの確定待ちへ変更した。

API imageのcache準備は、実際のsource・classic config・RootFSの一致と、今回取得した認証cacheの削除まで確認した。両ホストの準備結果は`prepared_not_admitted_not_activated`であり、受理済み・起動済みとは扱わない。環境設定とTLS秘密鍵は同じホスト内の新領域へ複写し、外部へ出していない。

19:45 JSTに、正規APIを使う検証containerが次を確認した。

- 実KMSで前提と候補の署名を検証し、正規のseq20からseq21への遷移を検証した。
- 現Auroraが候補の対象と一致した。DBの最新admissionは検証したseq20と全項目一致した。
- READ ONLYの接続で、既存35段階のrelease検査とruntime検査がともに一致した。
- クーポン用namespaceは存在せず、新しい36段階目は受理されていなかった。

35段階を二つの経路で調べた1回のpreflightであり、70件の独立した成功には数えない。この結果は本番切替中の排他、DB appendの成功、新36のreadinessを証明しない。

## 失敗と修正

最初のnative検査は、source確認用containerの実行ユーザーがimage内の対象ファイルを読めず、`PermissionError`で停止した。資格ファイルの読取とDB接続より前の失敗だった。同じローカルimageで再現し、network・mountなし、read-only・capability全削除を保って検査ユーザーを変更すると、期待するsource hashが一致した。CPU上限も1へ固定した。署名済み候補とimageは変更していない。

次のnative検査はsource確認を通過したが、前提署名のKMS検証で`ClientError`になり、DB接続前に停止した。この回では承認済みの保護された資格ファイルを内部で読み、一時RAMへ必要な設定を置いている。「秘密入力を読んでいない」とは記録しない。AWSの詳細なエラー種別を保存していなかったため、原因は未確定である。

その後のtoolでは、AWSのエラー種別だけを長さと文字種を制限して出力できるようにした。生のエラーメッセージや資格は出力しない。同じ権限文書を使い、15秒待って再検証した結果、preflightが成功した。この成功だけで、前回の原因を権限伝播の遅れと断定しない。

toolの各修正版は新しい領域へ配置し、旧版を保持した。独立担当は差分、固定source、失敗応答の検査、実際の終了記録を照合した。合成応答を本番の成功receiptとして使っていない。

## 権限と後始末

一時権限の起点は19:31:37 JST、最初に固定した期限は20:16:37 JSTである。各再検証でも同じ文書と期限を使い、45分の起点を更新していない。各回の使用後に自身の文書だけを削除し、不存在を確認した。

| 検証 | 結果 | 権限の不存在を確認した時刻 |
|---|---|---|
| 初回 | source確認で停止、DB接続前 | 19:31:45 JST |
| 2回目 | 前提署名検証で停止、DB接続前 | 19:39:19 JST |
| 3回目 | 読取preflight成功 | 19:45:32 JST |

検証用containerは初回1個、以後各2個の計5個について、所有を限定した終了処理の2回の不存在確認と、後続の実daemon読取で不存在を確認した。一時RAM領域も存在しない。秘密を含むRAMを残したまま完了と扱っていない。

後始末の読取toolにも一度不備があった。Dockerが不存在時に返すstdoutの空配列を誤拒否したため、空配列と対象名を含む正規の不存在エラーを検査するよう修正した。最初の読取失敗を保存し、修正後に実際の不存在を再確認した。

生の結果、承認対象、内部参照、署名、各toolのhashはGit外の非公開領域に保存する。公開する記録へ資格構造、内部ホスト、保存先の詳細や新しいartifact識別子を載せない。

19:47:13 JSTには、両ホストの署名・config・actor labelを再照合し、controlの4サービスとcomputeの3サービスが既存seq20に一致した。環境値とDBは読んでいない。これは本番未切替のmetadata確認であり、新36のreadiness確認ではない。

## 並列修正

[#250](https://github.com/AtsushiHosaka/pals/issues/250)の追加レビューで、処理期限に達したbatchが未処理invoiceまで試行済みにすると、同じ1件への回収を繰り返す問題を再現した。[API#73](https://github.com/AtsushiHosaka/pals-api/pull/73)は実際に処理へ進む対象だけ試行時刻を確定し、未処理対象の順序を保つ。既存の排他・schema・ACL・本番capture拒否は維持する。

固定した2運用ケースは基準版0/2、修正後2/2だった。実PG・実子processと、provider入口の明示fixtureを使った検査である。関連49件・単体と契約33件に加え、独立担当の同じ2件も通過した。これらをモデル精度に加算しない。独立レビュー後、後続37用の既存統合branchへ通常mergeした。seq21には混ぜていない。

再利用した検証用PGは、元の3DB・38role設定が不変、他clientが0であることを確認して正常停止した。実Stripe・本番capture・scheduler配備・操作tracker・CloudWatch集計は未確認である。

## 次の判断

本番入口の読取確認では、前回のカード配備と同じtarget groupに登録targetが0だった。別チャットの[#265](https://github.com/AtsushiHosaka/pals/issues/265)の記録を確認すると、既存targetを外し、通常drain後の未期限切れclaimを待っていた。保存済みの正常な登録状態を根拠に、こちらからtargetを戻していない。配備の排他を取得したとも扱わない。

さらに[#273](https://github.com/AtsushiHosaka/pals/issues/273)のロゴ修正も、オーナー承認済みで#265の完了後に配備する予定である。両リリースの実admission・runtime・復旧設定・所有権解放を確認してから、最新predecessorを前提にクーポン候補を準備する。新admissionが入れば、seq20を前提とする今回の署名済みseq21は適用できない。新しいdigestの署名や必要な操作は別に具体化し、古い承認を流用しない。

DB appendと本番切替は別承認を要する。既存actorの通常drain、正規6段階receiptを使うfinalize、段階順の起動とreadiness、復旧設定のtoolを調査した。独立レビューでは、compute旧構成のcleanup前に新controlのreadinessが必要な順序を確認した。長いdrainには、loopだけでなく引き継いだ180秒のowner deadlineと外側の期限も合わせる必要がある。起動の応答喪失時には、返却mapだけに頼らず、実際の所有名とlabelから状態を照合する。

predecessorの待機が判明した時点で、作成途中のtoolは未レビューのまま停止し、非公開の作業資料として保持した。構文解析を受入試験の成功と呼ばない。使える手順は保持するが、未確定のpredecessorに対する実行packageを完成扱いにしない。旧Web-only adapterで全actorの更新を代替しない。

DB appendとseq21 admissionのcommit後は、旧35段階のimageへ戻すだけでは復旧できない。応答喪失や最後の読取失敗が起きても、rollback済みとは推定しない。実DBの受理状態を照合し、36と互換性のある構成で復旧する手順を先に固定する。

検証時点の本番seq20の期限は11月6日15:03:04 JST、候補seq21の期限は同日16:40:50 JSTのままである。今回の準備と検証は本番の期限を延長していない。既存workerの追加質問claim互換修正は後続imageでの受入が必要であり、切替成功だけでクーポン発行可能とは扱わない。
