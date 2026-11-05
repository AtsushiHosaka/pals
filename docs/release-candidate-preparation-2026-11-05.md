# 次期クーポン配備の準備と検証

別チャットの#228/#253の記録では、14時台にshared-cardのseq19が本番適用済みである。以下は本チャットの旧seq18を前提としたクーポン候補の準備記録で、使用を停止した。本チャットから新schemaの署名・DB適用・サービス切替は実施していない。進行は[#244](https://github.com/AtsushiHosaka/pals/issues/244)、機能配備は[#234](https://github.com/AtsushiHosaka/pals/issues/234)、ソースの固定は[親PR#249](https://github.com/AtsushiHosaka/pals/pull/249)を参照する。

## 前提変更による停止

オーナーは#255で候補fa94への「署名と全読み取り検証を承認」と回答した。しかし回答直前に、本番がmanifest1630bc127e6281b6a7a5bd75d51bee80df7f1445b7710686c1439ef86055caa7のseq19へ進んだことを確認した。旧candidateはseq18をpredecessorとするため署名せず保全する。policy付与・追加SSM/native・DB/サービス操作も0回。#255は判断記録として閉じ、異なるdigestへ承認を流用しない。新predecessorの保存原本を既知の独立SPKIでECDSA検証し、manifest1630bc12・署名349dc425と期限11月6日11:10:57 JSTを照合した。新たなlive SSM確認はしていない。次候補は少なくともseq20以降とし、進行中の#248と調整する。

## F16反映時点の履歴

14:27 JSTに、タイトルのF16を反映したsourceから正式receiptと未署名seq19候補を再生成した。API#48は5c1a2fd791b63228c60376527cbf9f5c18014939、Web#40は11b629673a70b39bfdbf2faf315f6cc9ea696aef、親#249のsource snapshotはf514ffed0fa8cf03053ece37e8e36d374de5bb5dである。infra fb9d224・worker6e5c58d・verifier189b443を保持し、後続37やruntime診断修正は含めない。

| 成果 | SHA-256 |
|---|---|
| 未署名候補 | fa94cf782cbb20c2ffcac4134b725ff34ee813389d0a3746cd6cc526f2f9eb51 |
| 正式v2 receipt | a372af8d76076a7d307f0742e7e512184466ea1489aae7e221447f10a4a04bda |
| API image | 0b7a06b3c1e6a47c21d050d17d87d055d2f2ee5292a78ac8f10214c0fde3edc8 |
| Web image | 25e493e49c82d44a922709b64041c1bccc76660bd2b993fefa9473573ac2c753 |

候補の発行時刻は2026-11-05T05:27:36Z、期限は翌日の同時刻、JSTでは11月6日14:27:36で24時間。まだ署名していないため、稼働中のseq18の期限11月5日23:53:01 JSTを更新したものではない。

新API/Webは既存の非公開registryへ保存し、再pull後のRepoDigest・platform・source labelを確認した。APIはapp/docs/scripts/pyprojectの全ファイルと実imageのcopy・実行bitが一致した。コピー確認用の未起動containerと認証cacheは削除済み。全4役割のOCI実体を確認したが、これはoffline builder自身の外部検証ではなく、別のpublication証拠である。

旧60f8cd2/e63bc50とF15時点の42680595/6c7abd98、候補54105f7aは履歴snapshotとして保持し、署名・本番適用の対象へ流用しない。以下の初回構築記録もその時点の履歴である。

## 初回sourceとimageの履歴

独立したrelease作業ツリーを既存Git object storeから作成し、親と4つの子をcleanな状態にした。追加のアプリ・PGは起動していない。親のrelease commitは`bb33688da12b369d29109da86fa2b9941dc2a9fd`で、調査文書のPR#243のbranchとは分けた。

| 役割 | source | immutable image digest | platform |
|---|---|---|---|
| API | `60f8cd216bb33be542b155f76b8a9c9bec8ccc0a` | `sha256:7327327bf686e8394213f6a1c298c625ece21edb4441691a0e7f7b03d6e84001` | linux/arm64 |
| Web | `e63bc50ed4c7410260888ad87a202bec19565bd7` | `sha256:c639122ea63e42bf25b4e11b627009fcf8688a9badc688083e0ab22205a939a1` | linux/arm64 |
| worker。現行を維持 | `6e5c58dec2459962b2df498385d47cd8d6abe3a2` | `sha256:6f3067ba698abaa7d74e1d00200eb723266b6513d7c66b482b17e7f0f7e95890` | linux/amd64 |
| verifier。現行を維持 | `189b44378e6e63e5ab7c92d9c5b7d6507acd80f0` | `sha256:9c0a2724d2daa0b5763ce9f1d1f3472d79b999247b5db8ab17c069c5b1be4124` | linux/amd64 |

infraは`fb9d2249330670f6eae530e5f5a21757c4be0960`を固定した。新API/Webは既存の非公開ECRへ保存し、4役割の実imageのRepoDigestsとplatformを照合した。新API/WebのOCI revision labelは上表のsourceに一致した。worker、verifier、実効verifier source、toolchainはseq18から変更しない。この候補にはagent#48の新プロンプトを含めない。

## 構築と照合の証拠

APIは[統合PR#48](https://github.com/AtsushiHosaka/pals-api/pull/48)の正確なGit archiveから、既存の固定baseにoverlayを作った。コピーした全source、baseとlayer、platform、revision label、起動commandを照合し、公開前後のDocker ID・layers・不変URIの一致を確認した。source archive SHA-256は`8e2d832c8cac667fb52d28cb3c54e840e8d7c4358dc1a25ae27a976c396acdf2`。統合後の関連602テストは通過した。

Webは[PR#40](https://github.com/AtsushiHosaka/pals-webfront/pull/40)のGit archiveと既存Dockerfileから構築した。source archive SHA-256は`34f0f60862ed5e4909f0b0579b91a4073a3bb61ade936fbbd636d0384adfb7d5`。公開する認証設定は、既存Terraform出力、現行seq18の結び付け、実Cognito clientのGoogle・Hosted UI・callback/logoutで照合した。正規publisherと同じ設定を使い、Googleを暗黙のfalseへ落としていない。設定JSONのSHA-256は`7b485ce536b0ffd17a8a49b1234ca7b617ba83c936d535a3fdb5d91e66003876`。現在配信されるcompiled JSから逆照合した値ではない。認証設定の具体値は本書に掲載しない。

Webのplatform・revision label・非root user・起動commandと、公開前後のID・layers・不変URIを照合した。最新のOGを取り込んだ後の関連214テスト、型、lint、通常buildも通過している。Cognitoを使った本番の引換・実利用は別の未確認事項である。

正規のsource capture CLIは5つのcleanなrepositoryから成功し、source-commits JSONのSHA-256は`69bed65ca94b509af95909c16eb0dc282e25b4f796bc93de3ec4c7bedacd6469`だった。現行seq18の実署名をローカルECDSAで検証し、鍵pinも現行manifestが指すKMS公開鍵への認証済みGetPublicKeyで独立確認した。KMS署名や権限追加は行っていない。

## 限定読取の完了と次の承認範囲

オーナーの明示承認とSSO認証後、11:13:35 JSTに指定1項目を正規経路で読んだ。manifest・署名・SPKI、設定と環境参照のhash/所有/modeを再検査し、値は非公開で保管した。以前の読取承認待ちは解消済みである。13:51 JSTのfresh metadataでも参照先は一致し、追加の値の抽出は0件だった。

以下は承認を受領したが未実行となった、候補fa94cf78のKMS署名と読取検証の案である。未適用の一時policyはSHA-256 d5bda1541297ad3fd23cd58f2e6cbc9864f248858011cc61bb0a61854d8883b4。Tokyoの既存release keyへGetPublicKey/Verify、既存Aurora clusterと1 memberへDescribeを許可し、11月5日16:10 JSTに失効させる。KMS Sign・DB書込・wildcardをpolicyへ追加せず、同名があれば上書きを拒否し、最後に自分の文書だけを削除して不在を確認する。同じroleの全sessionに作用し、特定processへ隔離するpolicyではない。

完全な現行native検査には、正規の検証処理内で環境設定、TLS鍵、既存AWS資格情報を内部照合する範囲も必要になる。現35段DBの読取は既存の制限runtime principal・CAを内部利用し、READ ONLYと10秒のstatement timeoutを使う。master/release資格は使わない。これらはembedding1項目の承認から広げず、明示範囲として確認する。値を画面・Issue・ログへ出さない。

この段階に本番切替・DDL・DB admission・drain/停止/再起動は含めない。未配備36のadmission receiptは作らず、現35の検査を新36のnative起動成功とは扱わない。既存の追加質問のclaim不一致も候補に残り、初期クーポン発行前に実Plus機能の受入を行う。

## 続きの手順と復旧の条件

旧候補のsource・実image・正式receiptは保全済み。次は現行seq19の原本と進行中のWeb修正を確認して、新しいpredecessorに対する候補を具体化する。旧fa94候補への署名・検証は実行しない。完全な新36schema・Aurora・PKI・native controllerを通す正の起動と、実Cognito→引換→Plus機能はまだ確認していない。候補の署名だけで配備済みとはしない。

DB appendとadmissionのcommit前失敗では旧状態を保持する。commit後は36段階へ進むため、旧35imageへ戻すだけでは復旧できない。36互換imageと正規の後続software releaseで修復する。appendを再実行して署名期限だけを延ばさない。

初回coupon→software36の候補準備は[infra#95](https://github.com/AtsushiHosaka/pals-infra/pull/95)に専用offlineツールを実装した。headは`92a14a3d680391c1f9a5ec9f8dedf3582520523c`で、freshな署名済みcoupon36だけを受け入れ、schema・専用planの除去・5つのmetadata以外を不変にする。新規38件と既存44件の計82件が通過し、独立レビューでも新規38件が通過した。ローカル実ECDSAとAPI60f8cd2のvalidator互換までの確認であり、実際の本番更新ではない。初回の正規署名・適用・再起動、失効後OS復旧、自動更新は配備前の未了条件として残る。

その後、具体的な署名・本番適用の承認、正規drain、DB・両側readiness・復旧、Cognito→引換→実Plus利用を確認する。発行数・コード形式・引換期限・配布方法は#240の別判断であり、コード発行は0件のままである。

## 原本の保存

構築・公開receipt、build log、公開鍵pinの照合、source capture、未承認待ちrunbookは、元repositoryのGit対象外`pals-scripts/outputs/codex-takeover-20261104-01a1a6ef/release-image-preparation-20261105/`へ保存した。ディレクトリ0700・ファイル0600で複写前後のhashが一致した。10原本のmanifest SHA-256は`c52d334d39dadb06976d33bdf805a28d2e9f407a0fad1aac6fb93feb906703cd`。本書にregistryのaccount ID、内部host、認証情報、生応答を転記していない。
