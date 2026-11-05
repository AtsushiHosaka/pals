# seq21の本番配備準備

担当はCodex。[担当チャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)、進行は[#234](https://github.com/AtsushiHosaka/pals/issues/234)・[#244](https://github.com/AtsushiHosaka/pals/issues/244)。前段の[候補準備記録](priority-resume-2026-11-05.md)とsource固定PR#263を引き継ぐ。本番はseq20、候補は署名済みseq21で、DB受理・本番切替・クーポン発行は未実施である。

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

一時検証policyの案は既存control roleに対する、既存鍵のVerify/GetPublicKey、既存Aurora clusterと1 memberのDescribeだけである。resourceと東京regionを限定し、wildcardとSignを含めず、付与要求から45分で失効する。既存の同名policyは上書きせず、使用後に対象文書を照合して削除し、`NoSuchEntity`で不存在を確認する。roleの全sessionに影響するため、単一processだけの権限とは説明しない。

別のprefix検査は、既存の限定されたrelease principalとruntime/PFI readerの資格を内部で使う。masterは使わない。`default_transaction_read_only=on`、statement timeout10秒、lock timeout1秒で既存35段階・現seq20受理・追加schema未存在を検査する。以前のruntime-only読取範囲を超えるため、新しい承認が必要である。runtimeだけでrelease側のappend権限まで確認できたとは扱わない。

native準備・一時権限・このDB読取はまだ実行していない。DDL・admission・drain・停止・再起動・本番切替は、実際の正の準備結果と具体的な復旧条件をそろえた後の別判断にする。DB append/admissionのcommit後は、旧35のimageへ戻すだけでは復旧できない。

## 並列実装と追加レビュー

| Issue | 結果と範囲 | 残る条件 |
|---|---|---|
| #232/#236 | [Agent#58](https://github.com/AtsushiHosaka/pals-agent/pull/58)の4行のclaim互換修正を独立117件・親35件で確認し、元worker branchへ通常merge。実API DTOはnullable/supported languageの5ケースを基準版がすべて拒否し、修正版がすべて受理。関連API5ファイルは現本番と候補でbyte一致 | 既存障害の修正。seq21のworkerは変更していない。後続worker image・候補・実追加質問の受入が必要 |
| #217 | [infra#100](https://github.com/AtsushiHosaka/pals-infra/pull/100)のmetadata検査にshared lockと現在inode/pathの再検査を接続。担当・独立担当がactual Agentを含む49件・0skipで確認し、collector準備branchへ通常merge | 内容のread/write・activationは追加しない。CloudWatch配送・rotation/cursorは未検証 |

統合後の別環境レビューで、infra#100のテスト側にF19が見つかった。置換hookがdirectory openとleaf openの2回動き、元inodeを解放して再利用できるため、期待する拒否が不安定になる。[infra#101](https://github.com/AtsushiHosaka/pals-infra/pull/101)でleaf open時に一度だけ置換し、元inodeの保持と全descriptor閉鎖を検査するよう修正した。担当の49件・実ファイル1000回反復と、親の独立49件・0skipを確認してcollector準備branchへ通常mergeした。製品側と拒否assertionは不変。元の失敗filesystemでの監視側の再レビューは別に残る。

配備operatorの追加レビューでは、Dockerコマンドの応答喪失時に検証containerを残すP2を隔離adapter試験で再現した。実際の本番containerを残した観測ではない。旧templateから引き継いだ不足であり、全終了経路の所有確認・停止・削除・不存在確認を追加している。修正と独立レビューの完了前にnative実行や一時権限の付与は行わない。
