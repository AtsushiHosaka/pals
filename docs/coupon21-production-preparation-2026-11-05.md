# seq21の本番配備準備

担当はCodex。[担当チャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)、進行は[#234](https://github.com/AtsushiHosaka/pals/issues/234)・[#244](https://github.com/AtsushiHosaka/pals/issues/244)。前段の[候補準備記録](priority-resume-2026-11-05.md)とsource固定PR#263を引き継ぐ。17時台のcheckpointでは本番seq20と署名済み候補seq21を確認し、本チャットでのDB受理・本番切替・クーポン発行は未実施である。

19時台に#271の承認を受領し、両ホストのnative準備と読取preflightが成功した。一時権限は削除し、不存在まで確認済みである。その後、別チャットの#265が本番更新の所有権を取得し、#273の配備も予定されていると確認した。現在は最新predecessorの確定待ちである。失敗した2回の経路と後始末を含む最新の結果は[実行記録](seq21-native-verification-2026-11-05.md)を参照する。以下の「承認待ち」「未実行」は実行前のcheckpointを保持した記述である。

## 実行した確認と署名

17:12:38と17:20:46 JSTに、両ホストの現在のconfig・manifest・署名・独立SPKI pinとactorの設定ラベルを読み取り照合した。各回ともcontrol4・compute3の既存actorが一致した。4回のhost照合であり、7サービスそれぞれを独立試行とは数えない。環境値・TLS秘密鍵・AWS資格・DBは読み取っていない。native readinessや排他を確認した結果ではない。

[判断#267](https://github.com/AtsushiHosaka/pals/issues/267)で、チャットにdigestを提示した候補の1回署名・正規検証をオーナーが承認した。直前のhost照合後、既存KMS鍵で1回だけ署名し、17:21:21 JSTに実KMS VerifyとAPIの署名・schema・遷移検査を通過した。自動再試行は0。IAM・DB・サービスは変更していない。署名と結果は非公開の0600領域に保持する。

17:22:35 JSTには、既存セッションの読取権限で、検証policyの対象clusterと現在の単一memberが一致することを確認した。DB接続は0。この確認は権限付与やDB受理ではない。

本番seq20の期限は**2026年11月6日15:03:04 JST**、署名済みseq21候補の期限は**同日16:40:50 JST**である。候補への署名は本番の期限を更新していない。

## imageの本番互換性

Macのcontainerd image storeが返す`Id`は、今回のimageではOCI indexのdigestだった。本番Linuxのclassic Dockerで必要なconfig digestとは区別する。既存ECRの不変indexから単一のlinux/arm64 manifest、configをたどり、各段階のSHA-256とsource label・RootFSを検証した。APIとWebの2役割で実体の一致を確認した。正確な保存先・新しいartifact識別子・一時URLは公開しない。

この照合は正しいnative image pinを準備した証拠であり、本番ホストでの新image起動成功ではない。必要なimageのcache準備・起動検査は別に記録する。

## native準備と承認の境界

旧Web-only/software35のadapterでcoupon36の受理を代替しない。固定されたcoupon profile、35段階から36段階への1段append、既存worker/verifierを保持したowner sourceを使う。新しいhelperは既存actorの環境・TLSを同じhostの新version領域へ複写し、古いadmission参照を外して`prepared_not_admitted_not_activated`を返す。既存の評価資格はAPIだけに保持する。finalizeには正規ownerが検証する実6段階receiptを要求する。契約試験の合成receiptを本番受理の証拠にはしない。

次の準備・検証は[判断#271](https://github.com/AtsushiHosaka/pals/issues/271)で承認待ちである。正確な対象、必要な検証権限、保護情報の内部利用、期間と後始末を承認質問と非公開証拠に固定した。内部の資格構造や権限範囲の詳細は、自動承認レビューが公開Issueへの記載を拒否したため、本書にも記載しない。

検証権限の有効期間は付与要求から最大45分とし、使用後に自身の文書だけを照合して削除し、不存在を確認する。読取検査にはREAD ONLYと短いtimeoutを設定する。以前の限定読取範囲を超える内部利用を含むため、新しい承認を求めた。未確認の範囲まで受入済みとは扱わない。

native準備・一時権限・このDB読取はまだ実行していない。DDL・admission・drain・停止・再起動・本番切替は、実際の正の準備結果と具体的な復旧条件をそろえた後の別判断にする。DB append/admissionのcommit後は、旧35のimageへ戻すだけでは復旧できない。

## 並列実装と追加レビュー

| Issue | 結果と範囲 | 残る条件 |
|---|---|---|
| #232/#236 | [Agent#58](https://github.com/AtsushiHosaka/pals-agent/pull/58)の4行のclaim互換修正を独立117件・親35件で確認し、元worker branchへ通常merge。実API DTOはnullable/supported languageの5ケースを基準版がすべて拒否し、修正版がすべて受理。関連API5ファイルは現本番と候補でbyte一致 | 既存障害の修正。seq21のworkerは変更していない。後続worker image・候補・実追加質問の受入が必要 |
| #217 | [infra#100](https://github.com/AtsushiHosaka/pals-infra/pull/100)のmetadata検査にshared lockと現在inode/pathの再検査を接続。担当・独立担当がactual Agentを含む49件・0skipで確認し、collector準備branchへ通常merge | 内容のread/write・activationは追加しない。CloudWatch配送・rotation/cursorは未検証 |

統合後の別環境レビューで、infra#100のテスト側にF19が見つかった。置換hookがdirectory openとleaf openの2回動き、元inodeを解放して再利用できるため、期待する拒否が不安定になる。[infra#101](https://github.com/AtsushiHosaka/pals-infra/pull/101)でleaf open時に一度だけ置換し、元inodeの保持と全descriptor閉鎖を検査するよう修正した。担当の49件・実ファイル1000回反復と、親の独立49件・0skipを確認してcollector準備branchへ通常mergeした。製品側と拒否assertionは不変。元の失敗filesystemでの監視側の再レビューは別に残る。

配備operatorの追加レビューでは、Dockerコマンドの応答喪失時に検証containerを残すP2を隔離adapter試験で再現した。実際の本番containerを残した観測ではない。旧templateから引き継いだ不足を修正し、全終了経路の所有確認・停止・削除・不存在確認を追加した。停止を確認できなければ、秘密を含む一時RAM領域を保持して停止する。8境界試験と元の失敗経路の独立再検証を通過したが、実daemon上の成功とは扱わない。

cache回収の追加レビューでもF20を検出した。未知の隣接ファイルを見つけると、自身の資格ファイルを消す前に停止する不足だった。所有とmetadataが一致する自身のファイルを先に消し、未知のファイルは保持して報告するよう修正した。実一時ファイルを使う10境界ケースの独立確認が通過した。root所有・特定パスの部分は試験fixtureであり、本番の資格取得やcleanupを実測した結果ではない。

SSMへ送る入力は、sourceを分割して各段階でhashを検査し、host内で元の署名済みpacketへ復元する。独立decodeで両hostの元packetと同じ内容に復元でき、最大commandは53,694byteで63,000byte未満だった。後続operatorの入力は実際のnative準備成功receiptからだけ作り、仮のreceiptやadmissionを使わない。実行wrapperには本番適用のactionを設けず、読取検査を固定した。

ここまでのnative・cache・wrapperの検証はofflineである。承認待ちの段階で、権限付与、保護された本番資格の読取、DB接続、native準備は実行していない。次の作業は、#271への回答を受けてから再開する。

## 他チャットの記録との統合

記録PR#269の統合前に、mainへ設定画面の検証4行が追加された。mainの356行をrawのprefixとして保持し、今回の4行も全20fieldを保って足した360行へ統合した。設定画面の文書とsubmodule参照も保持する。6グラフを同じ台帳から再生成し、監査エラー0を確認した。これは記録の統合であり、署名済み候補のsourceやimageを変更していない。
