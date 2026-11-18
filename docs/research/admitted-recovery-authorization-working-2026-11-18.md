# 現admitted構成の回復専用承認案

状態はWORKING。対象は[#433](https://github.com/AtsushiHosaka/pals/issues/433)、関連は[#142](https://github.com/AtsushiHosaka/pals/issues/142)、[#410](https://github.com/AtsushiHosaka/pals/issues/410)、[#425](https://github.com/AtsushiHosaka/pals/issues/425)。本書は独立した設計レビュー用の調査記録であり、canonical仕様、実装承認、署名・設置・IAM変更の許可ではない。

主担当はcodex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2、独立設計はcodex://threads/01a1ece3-e675-7492-b366-f972b330540c。親の開始revisionは`922aca6924587e7a232b6306c2eae6984954c2e8`。根拠を読んだ旧frozen infraは`15c54e2645e52942aa759b09562ee29fa1db99c8`、失敗repairの統合sourceは`c2809c3de7c7dc7a56060d0909d8134e730e18a7`。UI用infra PR #188のpreview設定とは別の変更として扱う。source実装・署名・本番操作・有料送信は行っていない。

## 判断の前提

旧manifest、署名、plan、helper、失敗台帳を保持する。通常の期限後拒否と24時間の方針を変えず、新しく署名した別用途の文書で、現在DBが承認している同じ構成だけの回復を許す。通常のrelease-ownerやhealthの条件は弱めない。

既存のmake recovery、assemble/install、final healthは、current manifestの有効期間を要求する。expired candidateをhistoricalに読めても、回復設定の後付けと通常owner解放を完了できない。失敗archiveだけを追加しても、次releaseのobserve_currentが要求する現predecessorの回復設定・unitを満たさない。

今回の全停止復旧は、既存recoverと同じく、所有済みの全containerが停止し、exact container IDsとnetwork境界が保持されている場合を指す。削除済container/networkのcreate、foreign actor、別image/sourceへの再構成は拒否する。新imageのactivate、DB admission、一般のowner executeを許可しない。

DBのepochは、既存のrelease_sequenceとimmutable_values全18項目のcanonical hashである。同一admission内の独立revocation counter・新tableは追加しない。有効なpermitの再起動時再利用は許すが、次または別のadmission、期限切れでは拒否する。同じadmission内で旧permitを即撤回する機能は、この案に含めない。

## 要件

| ID | 必須の振る舞い |
|---|---|
| ARA-001 | permitのschemaとpurposeを閉じ、通常manifestと異なる署名domainを使う。相互利用を拒否する。 |
| ARA-002 | 検証鍵は独立したreview済みbindingのkey ARN・account・SPKI pinから決める。permit自身の鍵指定を信頼の正本にしない。 |
| ARA-003 | 新windowはissued_at以上・expires_at未満、長さは正かつ最大86,400秒。未来発行、期限境界、期限後の再利用を拒否し、自動延長しない。 |
| ARA-004 | 旧manifestのhistoricalな署名真正性と、新permitのcurrentな有効性を別々に検証する。旧bytesや通常loadの期限検査は変えない。 |
| ARA-005 | actual DBの最新admissionが、署名対象の18項目・sequence・canonical hashと完全一致する場合だけ回復を許す。観測不能は拒否する。 |
| ARA-006 | 両hostの実identity、runtime config、image、source、toolchain、環境・mount・network・firewallの境界と、実行する回復専用codeのhashを束縛する。 |
| ARA-007 | 全停止でもserving APIに依存せずfresh DB/TLS/callerの確認を行い、保持されたexact IDsだけを段階的に再開する。missing/foreign IDは拒否する。 |
| ARA-008 | DB確認から効果までの競合を閉じる。canonicalな実行context、host mutation flock、admissionの排他を、対象操作の全区間で扱う。 |
| ARA-009 | 旧owner markerは発行元の来歴として束縛する。archive後に旧active markerが残っていることを要求しない。foreign ownerは無視せず、bootと新controllerのpre-admission restoreを別contextで検証する。 |
| ARA-010 | 新種別のassembly/install/health receiptとunitを実生成し、permit・code・実IDs・unit hashを結び付ける。旧manifestが現在有効だというreceiptへ偽装しない。 |
| ARA-011 | 次releaseのobserve_current、previous-health、restore-check、pre-admission restoreが新種別を明示的に検証する。次admission後は旧permitによる回復を拒否する。 |
| ARA-012 | exact policy削除、IAM不在確認、失敗owner archiveを別closureへ結ぶ。元failed・停止超過・accepted=falseを保持する。 |
| ARA-013 | 応答喪失・途中失敗・再実行は、同じpermitと正規ledgerを観測して調停する。未知の効果を再送せず、処理中workerを強制停止しない。 |
| ARA-014 | 必要な観測権限の寿命も検証する。署名が24時間有効というだけで、24時間のboot復旧可能性を主張しない。 |
| ARA-015 | 本文、token、DB URL、認証情報を文書・journal・例外へ出さない。実再起動をしていなければOS再起動成功と記録しない。 |

## 署名文書と信頼の境界

専用signing CLIと純粋validatorをinfraへ追加する案とする。通常release-prepare signへ新schemaを混ぜない。既存signerのaccount、key種別、SPKI、local Verify、KMS Verifyの検査を維持し、署名対象を専用domain prefixとcanonical JSONの連結にする。prefixの具体bytesとcanonical encodingは、実装前に一意に固定する。

payloadは次の値を持つ。pathから読み込む実private artifactと、そのhashの一致も検証する。

- schema、purpose、permit ID、issued_at、expires_at。
- 旧manifest SHA、旧署名・SPKI・trust参照、最新admissionの全18項目とそのcanonical hash。
- 発行元のexact失敗owner marker、元plan・failed journal、source付きの来歴参照。
- 両hostのidentityと、runtime/config/image/source/toolchain、保持するcontainer IDsとnetwork・mount・firewallの境界。
- 回復専用validator、observer、executor、unit generator、consumer codeのhashと許可stage。

発行時のboot IDは来歴であり、将来も同じ値であることを要求しない。実行時には同じhost identityのfresh boot観測を記録する。新しいboot IDだけを理由に正常なhost rebootを拒否しない。

通常signerはcanonical JSONとkey bindingを検証するが、purposeのallowlistを持たない。このため新permitをそのまま通すのは不十分である。new purposeと署名domainを専用CLIで検証し、通常manifest署名との相互利用を負例で固定する。

## DB観測と実行時の排他

既存admission_observerは、exact API imageのone-shot observerを起動し、serving APIが停止中でもDBを確認できる。native caller、封じたrole URLs、tmpfs、read-only rootfs、固定image/source、TLS、DB identity、完全tuple、advisory lockの前後確認を維持する。

現在の出力はmanifest SHA・lock・時刻だけであり、新permitのtuple/sequenceとの一致を表せない。新purposeの閉じた出力schemaが必要で、旧出力を読み替えない。観測containerは既存の制限と所有ラベル、期限、成功・失敗・取消時の削除を保つ。

現observerの前後読取りは、返答後からactor起動までの競合を防がない。新設計では、正規admissionが使う排他と整合した実行fenceをeffect全区間で保持し、fresh DB一致の確認後にだけ対象操作を進める必要がある。自己保有lockをforeign operatorと誤認しないこと、接続喪失後に次のactorを起動しないこと、途中効果を正規ledgerで調停することも検証する。

**未検証の境界**は、別processのDB observerが返答後も排他を維持する具体的なlease、両hostとcanonical ownerの排他を結ぶ輸送、controllerの既存admit処理とのdeadlock回避である。短命なGET結果だけでARA-008を満たしたことにしない。ここはsource traceと実PostgreSQLの競合検査を終えるまで、実装可能と判定しない。

## 起動とownerの来歴

通常ownerのhistorical config拒否を維持する。historicalなconfigをcurrentへ書き換えて通常executeへ渡さない。新しい専用executorが、historical configと検証済みpermit、fresh DB一致、実行contextを受け取り、保持されたexact IDsの回復だけを行う。

既存recoverのcontrol-core、compute、control-reconcilerという依存順序と、network/iptablesの再確認・限定復元、実mTLS/readinessを保つ。reconcilerは既存recoverで通常ownerのcheck/executeを呼ぶため、そこだけを暗黙に流用できない。新executorが同じreadinessを実行し、permitで許可したexact actorの再開に限定する設計が必要である。

実行contextは次の2種類を明確に分ける。

| context | 検証するauthority |
|---|---|
| systemd boot recovery | native host/root・固定unit/code・current permit・fresh DB・mutation排他。発行元markerはactiveまたは正規archiveの来歴として照合する。 |
| 新controllerのpre-admission restore | 正規の新controller owner、freshな新candidate署名、未admitのrestore stage、対象predecessorとcurrent permit、fresh DB・mutation排他を照合する。 |

archive済み旧markerをlive必須にするとbootが成立しない。一方でforeign ownerを許してよいという意味でもない。現controlのowner情報をcomputeのbootから安全に確認する経路、次controllerが持つ排他からrestoreへ明示委譲する経路は、source上で閉じた設計を確定する必要がある。旧markerだけを任意の実行許可として扱わない。

## 回復設定・receiptと次release

新recovery config、assembly receipt、install receipt、health receiptは別kindとする。`historical_manifest_verified`と`current_recovery_authorization_verified`を分け、permit SHA、code SHA、runtime参照、実IDs、unit hashes、検査時刻を保存する。通常の`strict_manifest_window=true`や古いPASSを流用しない。

installは正規の回復unitを設置・enableした実結果を記録する。設置しただけなら再起動成功や全停止復旧成功を主張しない。healthは毎回freshに観測し、実際の回復試験と履歴を結び付ける。部分install、未知unit、source差替えを拒否し、再実行では正規receiptと実状態を照合する。

observe_currentとrestoreは、旧来kindの検証を維持し、新kindだけに専用validatorを追加する。permitが別admission・期限切れなら、期限内の過去healthがあっても拒否する。admission後の旧runtime復帰は許さず、新candidateの正規forward repairへ進む。

失敗closureはこの回復証拠とIAM不在、exact owner archiveをhashで結び、accepted=falseを記録する。署名済みpermitが回復を許すことと、旧リリースの機能受入が合格することを分ける。

## 観測権限と残る設計判断

既存observerはhost roleでKMS Verify/GetPublicKeyとRDS Describeを実行する。一時権限が45分で失効する、またはcleanupで削除されると、そのままでは24時間有効なpermitのboot検証を継続できない。permit自体はIAM付与を許可しない。

必要なread権限とcleanupの所有・寿命を設計するか、既存ownerと同等のSPKI pinとOpenSSLによる真正性検証を使う新purpose observerを別途レビューする必要がある。後者もDB/TLS/caller/resource identityを省略してよいという意味ではない。具体経路が未検証のため、本書ではどちらかを採用済みとは扱わない。撤回済みの14:40 IAM案を使わない。

## 変更境界と最小工程

実装はinfraを主とし、親は横断仕様・運用・source参照を持つ。APIのadmission schemaやcounterは変更しない。

| 工程 | 所有する入口・成果物 | 要件 |
|---|---|---|
| 1 | 専用authorization schema/validator/signing CLIとnegative tests。既存signerと旧helperは保持する。 | ARA-001〜006 |
| 2 | 新purposeのone-shot/実行fence付きDB observer。実行時ownerとIAM寿命を閉じる。 | ARA-005、008、009、014 |
| 3 | 回復専用executorとconfig/unit generator。保持されたIDs、firewall、readiness、再実行を検査する。 | ARA-006〜010、013 |
| 4 | 新assembly/install/health receiptsと、observe_current/previous-health/restoreへのconsumer接続。 | ARA-010、011 |
| 5 | 失敗repair/owner archive/IAM cleanup/closureのversioned orchestration。元台帳は保持する。 | ARA-012、013 |
| 6 | 対象・広域回帰、独立architecture/security review、exact CI、具体inputの固定。 | 全要件 |
| 7 | 個別のlive承認後に署名・設置・実依存確認・全停止復旧・closureを記録する。次releaseの配備と受入は別に行う。 | ARA-007〜015 |

想定するcodeの境界は、infraの署名CLI/pure validator、回復専用host executor/observer、native generator・registry、config/unit/receipt validators、release-repair/observe/restoreである。新sourceをhash登録して使い、旧frozen adapterのallowlistや古いhelperを密かに変更しない。実装ファイルとbaseは設計review後に固定する。

## 必要な反例と実証

通常loadが旧期限切れを拒否すること、旧bytesが不変であることを独立に検査する。用途/鍵/SPKI/非canonical/署名改変、未来発行・24時間超・期限境界、18項目の各相違、次sequence、別host/config/image/source/toolchain、DB不可、DB確認後のadmission競合、自己lock/foreign lock、owner archive後/foreign owner、接続喪失・応答喪失・部分install・再実行を検査する。

exact IDsの全停止から再開できることと、missing/foreign IDや境界createを拒否することを分ける。新permitが新image、admit、一般activateを許さないことも検査する。boot時に観測IAMが失効する場合を負例に含める。

署名には実際のcryptographic verification、DB排他には実PostgreSQL、actor/network/unitには実Docker/systemdの該当境界が必要である。doubleを使った検査はその境界内のsource回帰だけを示す。実署名・実依存・実停止復旧を未実施のまま、本番の復旧可能性やOS再起動成功へ昇格しない。新たな有料モデル送信はこの設計検査に含めない。

## 独立レビューの判定

#142の方針には条件付きで整合する。新purposeにより旧manifestをhistorical identity、新permitをcurrent authorityとして分離できる。旧署名の延命や通常gateの省略は不要である。

ただしARA-008・009の実行fence/owner委譲と、ARA-014の観測権限の寿命は具体source経路が未検証で、実装着手可能という判定には至っていない。新種別のreceipt/consumer接続も未実装。これらを閉じ、主担当が設計へ同意するまでsource実装を開始しない。live操作はさらに、具体input・tests・review・CIと追加承認を必要とする。

## 根拠source

以下は旧frozen infra `15c54e2`のsource行であり、現在のlive状態を示さない。

| source | 確認した境界 |
|---|---|
| scripts/release_prepare_signer.py:128–161 | key/account/SPKI、KMS/local Verify、purpose未検証 |
| host/private-runtime/admission_observer.py:182–239 | serving不要のone-shot、caller・image・tmpfs・role URLs |
| host/private-runtime/admission_observer_program.py:19–49、69–94 | 完全admission、readonly/TLS、lock前後、KMS/RDS read |
| host/private-runtime/recover_runtime.py:102–104、242–284、351–359 | 通常window、保持IDsの段階再開、ownerと共通のflock |
| host/private-runtime/control_runtime.py:1050、1125 | historical configの通常mutation拒否 |
| host/private-runtime/compute_runtime.py:1093、1165 | historical configの通常mutation拒否 |
| host/private-runtime/release_native/templates/observe_current.py.tmpl:126–169 | predecessor回復configとexact enabled units |
| host/private-runtime/native_safety_restore.py:155–176、257–275 | historical context、expired全停止境界の通常再作成拒否 |

admissionの18項目はAPIの`ReleaseAdmission.immutable_values`を正本とする。field順とencodingを新validatorの一部として固定し、独立epochを存在するものとして扱わない。
