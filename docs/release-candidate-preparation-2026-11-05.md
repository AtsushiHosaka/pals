# 次期クーポン配備の準備と承認待ち

現在の本番は同一構成へ更新したseq18である。以下は次の機能・schema候補を具体化するための準備で、本番の署名・DB適用・サービス切替は実施していない。進行は[#244](https://github.com/AtsushiHosaka/pals/issues/244)、機能配備は[#234](https://github.com/AtsushiHosaka/pals/issues/234)、ソースの固定は[親PR#249](https://github.com/AtsushiHosaka/pals/pull/249)を参照する。

## 実際に固定したsourceとimage

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

## 未生成のものと、承認が必要な読み取り

正式な`pals.production-images.v2` receiptと、新しいunsigned manifestはまだ生成していない。receiptに必須の`draft_embedding_revision`が保存済みのpublication receiptやworker imageのENV・labelでは確認できなかったためである。ローカルimage receiptや推測した版を代用しない。

現行seq18の保護されたcompute設定と2つの環境ファイル参照のSHA・所有者・modeを照合し、`PALS_DRAFT_EMBEDDING_REVISION`という1項目だけを読むSSM操作を準備した。自動承認レビューは、本番の保護設定を読む操作が、01:30 JSTまでの同一構成更新に限った先の承認を超えるとして拒否した。操作は未実行であり、別経路で回避していない。

オーナーへ、この単一項目の読み取りを承認してよいか質問した。環境全体や認証情報の表示、書換、サービス操作、権限追加を含めない。回答待ちの内容と理由は#241/#244に記録した。読み取りが承認されても、それ自体は新schemaの署名・適用を承認したことにはならない。

## 続きの手順と復旧の条件

欠けた1項目を正規の根拠で確定した後、sourceを再確認し、正規CLIで4imageのv2 receiptを生成する。専用offline builderは、署名済みseq18・独立hash/key pin・exact35 registry・新API sourceを使い、36への1段階だけのappend候補を作る。44件の独立検証は、API・infraのpure validatorとの互換までで、実Aurora・PKI・OCI内容や本番更新をこのツールだけでは証明しない。

予定していた発行時刻は`2026-11-04T16:46:43Z`、期限は翌日の同時刻である。ただし現時点で候補digestは存在せず、承認待ちが続いた場合も古い候補を有効だと扱わない。再開時に実時刻と24時間方針を検査し、必要なら新時刻で候補を作り直す。

DB appendとadmissionのcommit前失敗では旧状態を保持する。commit後は36段階へ進むため、旧35imageへ戻すだけでは復旧できない。36互換imageと正規の後続software releaseで修復する。appendを再実行して署名期限だけを延ばさない。

初回coupon→software36の候補準備は[infra#95](https://github.com/AtsushiHosaka/pals-infra/pull/95)に専用offlineツールを実装した。headは`92a14a3d680391c1f9a5ec9f8dedf3582520523c`で、freshな署名済みcoupon36だけを受け入れ、schema・専用planの除去・5つのmetadata以外を不変にする。新規38件と既存44件の計82件が通過し、独立レビューでも新規38件が通過した。ローカル実ECDSAとAPI60f8cd2のvalidator互換までの確認であり、実際の本番更新ではない。初回の正規署名・適用・再起動、失効後OS復旧、自動更新は配備前の未了条件として残る。

その後、具体的な署名・本番適用の承認、正規drain、DB・両側readiness・復旧、Cognito→引換→実Plus利用を確認する。発行数・コード形式・引換期限・配布方法は#240の別判断であり、コード発行は0件のままである。

## 原本の保存

構築・公開receipt、build log、公開鍵pinの照合、source capture、未承認待ちrunbookは、元repositoryのGit対象外`pals-scripts/outputs/codex-takeover-20261104-01a1a6ef/release-image-preparation-20261105/`へ保存した。ディレクトリ0700・ファイル0600で複写前後のhashが一致した。10原本のmanifest SHA-256は`c52d334d39dadb06976d33bdf805a28d2e9f407a0fad1aac6fb93feb906703cd`。本書にregistryのaccount ID、内部host、認証情報、生応答を転記していない。
