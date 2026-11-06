# 説明生成失敗の緊急調査（2026年11月6日）

担当はCodex。[障害Issue #223](https://github.com/AtsushiHosaka/pals/issues/223)、[担当チャット](codex://threads/01a1ae34-04ec-7050-b060-e31d0be7ad3b)。関連は[#222](https://github.com/AtsushiHosaka/pals/issues/222)、品質監視の[#217](https://github.com/AtsushiHosaka/pals/issues/217)、署名更新の[#142](https://github.com/AtsushiHosaka/pals/issues/142)。

本番ログと読み取り専用DB照会で、今回の失敗経路を特定した。平方専用Recipeは本番検索の公開一覧に存在せず、一般の自然数冪のRecipeは特殊化の再利用を認めない照合で却下された。新規証明はLean検証を通ったが、説明は`x_squared_epsilon_delta`検査で3回とも拒否された。旧修正候補は追加レビューの指摘により停止した。新たな承認後、R2を本番seq22へ反映し、全7サービスのreadiness、公開入口の復元、一時権限の削除、所有権の解放を確認した。後続の新しい数学依頼も説明生成で失敗し、公開UIの復旧受入は未達である。

AWS SSOは当初期限切れだったが、オーナーの再認証後に調査を再開した。以下では、実機確認、保存済み配備記録、オフライン再現を区別する。

## 確認した事実

2026年11月6日09時台JST、既存Chromeのゲスト画面で、利用者が送った画像と同じ説明生成失敗を確認した。新しい質問の送信、利用枠の変更、再試行は行っていない。

同じ時間帯の公開入口の読み取りでは、ホームはHTTP 200、`https://api.palschat.site/health`はHTTP 200で、`status=ok`、`environment=prod`だった。公開`/health/ready`はHTTP 404で、非公開にする設計と一致した。これらは説明の完走や、内部readinessの成功を証明しない。最初に調べたWebホストの`/api/health`はHTMLを返したため、APIの健全性の根拠には使っていない。

画面の`lean_explanation_failed`は説明失敗の集約コードである。生成時の検査、プロバイダー、期限、独立審査、参照不一致のどれが原因かは、この表示だけでは区別できない。実配備として記録されたworkerには、`explanation_generation_failed`の`reason`で区別するログがある。[固定workerソース](https://github.com/AtsushiHosaka/pals-agent/blob/6e5c58dec2459962b2df498385d47cd8d6abe3a2/pals_agent/worker.py#L2688)。

## 保存済み配備記録との照合

調査開始時の[統合リリース記録](logo-production-v2-2026-11-05.md)はseq21だった。保存manifestのSHA-256を独立計算し、記録にある`02ca35de2e2d128b83ffa52996f357189cc13343f9fd5b2d4e3651b82a2bb945`と一致した。worker sourceは`6e5c58dec2459962b2df498385d47cd8d6abe3a2`、Web sourceは`120cb477911b89ad2b8487f968fc0187f7d85496`。

調査開始時のseq21 manifestの期限は**2026年11月6日23:44:56 JST**だった。古いIssueにあるseq20の15:03:04 JSTを現行期限とは扱わない。これは保存済みの原本と配備記録の照合であり、現在のホストが同じ構成で稼働していることや、今回の説明失敗が署名に起因することを示さない。

09:24 JSTのSSM読み取りで、両ホストの現行設定とmanifestを保存原本へ照合した。seq21と同じsource、実ECDSA署名、公開鍵pin、有効期限を確認し、所有する7サービスは稼働中、OOMによる停止はなかった。この検査は内部readinessの全項目や負荷時の容量を検証するものではない。

期限後の起動・復旧では正規validatorが拒否する設計のため、署名更新は別の継続運用課題として確認する。初期の原因調査は読み取りで行った。その後の旧修正候補の署名、一時権限、事前検査と停止は後述する。この前段の調査ではDB更新と本番切替を行っていない。後述のR2反映では正規admissionと切替を実施した。

## 本番で確認した失敗経路と時間

対象のDB保存文を、画像の質問とリモート側で比較し、一致を確認した。質問本文は取得結果へ出していない。リクエスト、linked job、説明失敗ログは、既存の相関ハッシュで一致した。

| 段階 | 観測結果 |
|---|---|
| DBの作成から失敗確定まで | 09:03:03.326から09:06:48.749 JST、約225.42秒 |
| Recipe判定 | 約27.26秒。検索は約0.43秒で8候補を返した |
| 新規生成へ進んだ理由 | `dsp_scope_mismatch`。選択Recipeはnull、独立照合も不承認 |
| 新規証明と説明のworker処理 | 約196.39秒。sketch約54.86秒、prove 2回の合計約47.87秒などを含む |
| Lean検証 | 計測された検証時間は約6.59秒。DBのjobは`verified` |
| 説明生成 | 3回の呼び出しはすべてHTTP 200、通信失敗0件。計約50.09秒 |
| 説明の失敗理由 | `validation:x_squared_epsilon_delta,x_squared_epsilon_delta,x_squared_epsilon_delta` |
| キュー待ち | 判定14ms、linked job 13ms。各受信回数は1 |

段階の計時は入れ子や並列処理を含むため、表のすべての値を足して総時間にはしない。今回の225.42秒はDBの作成から終端までの1件の値で、クリックから画面表示までの測定やp95ではない。

説明本文は検査の失敗時に保存されておらず、今回の3出力のどの表現・数学的条件が拒否されたかまでは特定できていない。専用検査が終了理由だったことと、次節で再現した表記による過剰拒否を、同一の事実とは扱わない。

## Recipeをそのまま返さなかった理由

本番の専用catalog selector接続を、既存の権限のまま読み取り専用トランザクションで使用した。検索公開viewには日本語33 entryがあり、複数toolchain・revisionを含んでいた。33を現在の利用可能問題数には換算しない。既知の平方専用ID`continuity.square.explicit-epsilon-delta`は0件だった。

今回の8候補には`requested.natural_power_continuous`と`requested.rational_power_continuous`が入った。通常照合はobjects・assumptions・quantifiers・conclusionをfalseとし、Recipeを選択しなかった。先行するsemantic照合も、一方は`needs_input`、他方は`miss`で、再利用の合意が成立しなかった。

現行実装は、一般定理の特殊化や代入を同一命題の直接再利用として認めていない。このため「任意の自然数nでxⁿが連続」という保存済みRecipeを、そのまま「x²が連続」の回答に使わなかった。Recipeから直接再利用できた場合には、保存済みanswerを返し、説明を生成し直す経路には進まない。

本番の不足を修正するには、平方専用Recipeを正規の証拠・審査・公開手順で追加するか、一般定理の適用条件・代入・証明の結び付けを検証する再利用を実装する必要がある。照合を無条件で承認する修正は行わない。ローカルのDraftやfixtureの存在を本番公開の証拠には使わない。

最初のカタログ照会では一般API接続から専用roleへ切り替えようとして`InsufficientPrivilege`で拒否された。権限は追加せず、製品が元から使う専用selector接続に切り替えて成功した。DBの更新は0回だった。

## AWS監視の実設定

同じ本番アカウント・東京regionで`/pals`配下のCloudWatchロググループを列挙した。既存はhost用とPostgreSQL用の2グループで、仕様の`/pals/prod/quality-events`は存在しなかった。取得した10件のmetric alarmは既存machine-auth系で、`PALS/ProofQuality`のalarmはなかった。

`PALS/ProofQuality`の`list-metrics`も0件だった。証明関連キューの読み取りでは、通常キューの可視・処理中・遅延はすべて0件、DLQには証明20件・要求1件があった。メッセージの受信、再配信、削除は行っていない。

したがって、説明失敗をCloudWatchの品質イベント・アラームで検知できる本番構成は、この読み取りでは確認できなかった。hostのlivenessやmachine-authの正常表示を、回答品質の正常と扱わない。ログ収集先の保持日数だけを変えても、説明失敗の検知は追加されない。

## オフラインで再現した専用検査の過剰拒否

日本語の「x²の連続性」に対して、実装は専用のε–δ検査を行う。[固定説明ソース](https://github.com/AtsushiHosaka/pals-agent/blob/6e5c58dec2459962b2df498385d47cd8d6abe3a2/pals_agent/explanations.py#L1527)。

固定ソースのGit blob `eb0061b730b15f3482009b913a515c92ca8dcf46`と、ファイル全体のSHA-256 `0149d5ed641ca95cd8c473425e5b5d845aacdbac295fa11efe57ec7f0c13b67e`を照合した。ASTから`_has_x_squared_epsilon_delta`と`_is_sufficient_x_squared_delta_choice`を変更せず取り出して実行した。モデルやAWSは呼び出していない。

合成入力の基本形は、任意の実数aと正のεに対し、δを`min(1, ε/(2|a|+1))`に取り、`|x-a|<δ`から`|x²-a²|<δ(2|a|+1)≤ε`を示すものである。

| 入力の変更 | 専用検査 |
|---|---|
| 基本形 | 受理 |
| 点の変数をすべてaからbへ変更 | 拒否 |
| 分母の項順を`1+2|a|`へ変更 | 受理 |
| δをさらに小さい`min(1, ε/(4|a|+2))`へ変更 | 受理 |
| δの式の直後を`>0。`から`>0とおく。`へ変更 | 拒否 |

変数の改名と日本語の接続表現の変更で、数学的意味を保存したまま受理結果が変わった。オフラインで確認した過剰拒否は2件である。現行mainとして取得・Git object照合した`25442febf4d21f4714fc7efba1819930c3fbcfb6`でも、関連する3関数のASTは同一だった。

これは専用検査の挙動の再現であり、全体parser、独立審査、API、画面までの再現ではない。今回の本番出力を取得していないため、今回の直接原因とは断定しない。5入力中3件の受理を、モデル精度・本番成功率とは扱わない。

ローカルの再現一式はGit外の`/tmp/pals-incident-20261106-validator/`に保存した。親担当も`python3 /tmp/pals-incident-20261106-validator/reproduce.py`を実行し、同じ5件の挙動を再確認した。入力は合成した証明文で、本番の質問・応答・ログではない。

## 旧修正候補の停止と一時権限の削除

[Agent PR #60](https://github.com/AtsushiHosaka/pals-agent/pull/60)の初版`0b340f8877f93bfb4ac9c94c926eeb673018c113`では、変数名・数式の同値な順序・完結した日本語の定義句・正のεで始まる同値表現を扱う修正を準備した。

初回の独立レビューで、日本語の演算修飾による誤受理と、別文で同じ積を評価する説明の過剰拒否を発見し、修正した。当時の43回帰、関連255件、独立109件と追加5例は通過したが、追加レビューで、正しい連結等式の評価と先行する一般恒等式を含む説明を拒否する回帰が判明した。これらの追加正例では実配備基準は受理し、初版は拒否したため、初版の配備をHOLDにした。初回の通過結果は当時の範囲の記録として保持し、最終受入の根拠には使わない。

初版を含むseq22候補のmanifestは`917eb3eb7cf1b23ee8d83b2cb7a21af46d6763ed93aeb5d659f103aa21e92ca1`で、署名と照合は完了した。しかし本番admission、drain、サービス切替は0回である。署名済みであることを、本番に反映済みという意味には使わない。

既存の承認範囲で、一時検証権限を11月6日10:04:47 JSTに付与した。10:23:56–10:24:06 JSTの読み取り専用preflightは、schema35の35段階についてrelease計画とruntime確認を通過した。これは複合事前検査1回であり、35回の配備成功ではない。結果の`database_apply_executed`と`drain_or_activation_executed`はともにfalseで、既存の稼働サービスは保持された。

HOLD後、10:32:55 JSTに一時権限を削除し、`NoSuchEntity`で不存在を確認した。この権限を新候補の検証へ流用しない。付与から削除確認までの28分8秒を、モデルの処理時間や本番回答の所要時間へ加算しない。

## R2の修正と公開済み資産

追加修正は固定commit[`cc75c3fb2d4ec18b2e30b1f4eea9fa0c304ea171`](https://github.com/AtsushiHosaka/pals-agent/commit/cc75c3fb2d4ec18b2e30b1f4eea9fa0c304ea171)で公開した。δが依存する点と近傍・因数分解・ε評価の変数を字面のまま結び付け、適切な変数組と後続の因数分解を探索する。連結等式を経た評価を受理し、先行する一般恒等式だけに固定しない。全本文をa/xへ置換することによる、無関係な点・変数の混入も防いだ。δの十分条件、Lean参照、独立QA、試行上限は保持する。

同じ最終62回帰を実行した結果は、実配備基準`6e5c58d`が39成功・23失敗、初版`0b340f8`が51成功・11失敗、R2が62成功だった。関連8suiteは274成功、Ruff・sourceのstrict mypy・差分検査も通過した。最終差分の独立確認は128件と26正負例が成功し、追加P0〜P2指摘はなかった。62、274、128には重複があるため合算せず、単体テスト件数をモデル精度の台帳へ加算しない。

worker storyは43成功・1失敗だった。失敗は合成clockの330と既存reconciliation timeoutの2000の不一致で、実配備基準でも同じ失敗を確認した。この失敗と本番timeoutは変更していない。

[Infra PR #103](https://github.com/AtsushiHosaka/pals-infra/pull/103)のR2固定commitは`eb5a3536f7bdeaa988bb4d74bbe78de388aa79c6`、親のsource captureは`57ea82521152a1076fdf37c3ba314eebec8a0126`である。worker image `sha256:99d290e7b7197c03db494b9cd3bc63e9d72d942fa5855567fca76e8e22ea9cf3`の正式な公開receiptは、公開時点を`published_not_deployed`として記録した。後述の反映でもAPI・Web・verifier・schema35を保持した。

親担当はR2固定Infraでもcompute・recoveryの2suiteを再実行し、280件成功を確認した。必要なsibling checkoutへの一時リンクは実行後に削除した。この件数もモデル精度や本番受入の成功数には加算しない。

R2候補のmanifest `0a7d1267d08665dec24e7e37afcec709bf1b3e2791e535fc8db7e08c5a51b311`は署名済みで、実manifest・正式receipt・OCI・事前image読込資産を独立照合した。新しいhost所有者の配置をSSM送信しようとした際、自動承認審査が、旧承認では新候補のhost変更が明示されていないとして拒否した。この拒否された試行のSSM送信は0回で、本番を変更しなかった。

新候補の配置、4項目の一時検証権限を最大45分間付与すること、検証後の切替を含む操作について、オーナーから新たな明示承認を得た。旧候補の承認や削除済み権限を流用せず、R2候補と現在の本番状態を照合してから反映した。

旧Infra `e7cc50c`のcompute・recoveryの2suiteは280件成功したが、これは初版workerの許可に対する当時の証拠である。初回の10失敗はsiblingのAgent checkout不在によるもので、既存の正確なGit objectへの一時リンクを使って解消し、そのリンクは削除した。これらをR2の本番受入に読み替えない。

## R2の本番反映と確認範囲

11月6日11:15 JST、両ホストのnative準備が成功し、computeで新workerの事前image読込を確認した。実OCIのimage・manifest・config・21 layer・source commitと、native Dockerの値を照合した。一時ECR認証の削除を確認し、この段階ではruntimeを起動していない。

準備state全体の取得は、自動承認審査が秘密値の転送可能性を理由に拒否し、SSM送信は0回だった。その後、固定path・権限・実SHAを確認する読取器に変更し、既知の値に一致する7項目だけを取得した。出力はstatus、role、manifestとhelperのSHA、旧設定の参照、native準備stateの参照、canonical jobのSHAである。環境変数・TLSファイルの参照先は開かず、全stateを取得済みとは主張しない。後続helperには、この実native参照のSHAを渡し、選択metadataのSSM応答ファイルのSHAと混同しなかった。

一時検証権限は11:26:49 JSTに付与した。操作は既存と同じresourceに対する`kms:Verify`、`kms:GetPublicKey`、`rds:DescribeDBClusters`、`rds:DescribeDBInstances`の4読取項目で、期限は12:11:49 JSTだった。11:27:17–11:27:26 JSTのread-only preflightは、schema35の同じ35段階についてrelease計画とruntime確認を通過した。DB applyとdrain・activationは未実行で、稼働actorは変わらず、検査containerと一時RAMは回収された。35は1回の複合検査の段階数で、配備試行数ではない。

新候補のcanonical所有権を取得し、ALBの入口を登録解除して排出を待った。両ホストの処理中件数0を確認し、旧writerを正常停止した後、11:37:39–11:37:51 JSTに正規operatorが`released`を返した。実native receiptには、DB identity、既存schemaとrole、排他とquiescence、署名済みreleaseのadmission、既存DBの保持の5段階が記録された。続いて両ホストでfinalize、旧資源の限定cleanup、新runtimeの起動、reconcilerの起動、復旧設定の生成と導入を実施した。

11:54:10 JSTのcompute、11:54:21 JSTのcontrol最終healthは、ともに`seq22_actual_health_verified`、`readiness=passed`だった。全7サービスの稼働、署名manifestと同じsource・image、finalizeと同じruntime設定SHA、実組立結果と同じ復旧設定SHA、firewallの一致を確認した。controlの最新DB admissionはseq22と新manifestに一致した。API・Web・verifier・schema35、TLSとruntime bindingを保持し、クーポンやschema36/37を混ぜていない。最終health検査によるDB変更とモデル呼出しは0回で、実再起動試験は行っていない。

ALBは元と同じ単一targetをhealthyへ戻し、14項目の設定値を維持した。一時検証権限は11:55:50 JSTに削除し、`NoSuchEntity`で不存在を確認した。実存続窓は29分1秒で、モデルの処理時間へは算入しない。11:59:08 JSTの所有権解放は`canonical_card_release_completed_and_released`で成功した。

現行seq22 manifestのSHA-256は`0a7d1267d08665dec24e7e37afcec709bf1b3e2791e535fc8db7e08c5a51b311`、signatureのSHA-256は`ece7dfcb7155cb7ae14444a3aa15b0726c5b89bd94f7aeddd3d05a1a7aea2ecf`である。有効期限は`2026-11-07T01:52:38Z`、日本時間では2026年11月7日10:52:38。旧seq21の期限や、停止した旧917候補の署名を現行の根拠に使わない。

実応答原本はGit外に保持し、公開記録には質問本文・応答全文・秘密・内部host識別子を載せない。下表のSHA-256は原本ファイルを区別する先頭16桁であり、manifestの完全SHAとは別の値である。

| 実証拠の原本名 | SHA-256先頭16桁 | 確認内容 |
|---|---|---|
| `r2-native-prepare-control-result.json` / `r2-native-prepare-compute-result.json` | `13ed7273305cea75` / `768fd4afa35c0970` | 両ホストのnative準備成功 |
| `r2-prewarm-worker-result.json` | `f95c6fbfef46d519` | 新workerの実image照合と一時認証削除 |
| `r2-preflight-approved-policy-result.json` | `fb4fe781d25d2c1d` | 読取専用35段階と検査資源の回収 |
| `operator-apply-result.json` | `0283d2d491f645a0` | 正規5段階のrelease receipt |
| `final-health-control-result.json` / `final-health-compute-result.json` | `292043bab8a45f05` / `3950c3143ec485d9` | seq22の実readinessと全7サービス |
| `restored-ingress-readback.json` | `7adfc3bd3c001b1b` | 単一target healthyと14設定値 |
| `cleanup-result-7f32289c46dc497baa39f0db9d4eeca0.json` | `d1d768021f974dc5` | 一時権限の削除と不存在 |
| `owner-release-result.json` | `0faa9de9ed00b1f1` | canonical所有権の完了解放 |

## R2反映後の公開依頼は説明生成で再失敗

公開UIでは12:00:35–12:00:55 JSTの間に、元の障害と同じ数学依頼を新規に1回送信した。署名有効・seq22の実runtimeに結び付けた読み取り専用metadataで、このゲストchatの現行jobとの対応を確認した。DBのrequest作成は12:00:50.518790 JST、失敗確定は12:07:11.394797 JSTで、差は約380.88秒だった。これは単発のDB作成から終端までの値である。クリックから表示までの時間やp95は測定していない。

linked jobは`verified`で、最終更新は12:06:17.065551 JSTだった。説明stateは12:07:04.148938 JSTに`failed`となり、診断コードは`pals.explanation_failed`、`output_review_approved=false`だった。requestの終端コードは`lean_explanation_failed`である。

後続の固定log抽出で同じ現行jobとの対応を照合し、理由は`validation:x_squared_epsilon_delta,x_squared_epsilon_delta,x_squared_epsilon_delta`と確定した。日本語の平方専用検査が有効で、説明候補は3回とも固定ルールの専用検査で拒否された。独立QAによる却下とは扱わない。記録された説明処理時間は46.431秒、Leanコードは66行だった。生成に失敗した説明本文は保存されておらず、どの式・表記・数学的条件が拒否されたか、生成文の欠陥か検査の誤拒否かは特定できない。このため失敗分類は`unclassified`を維持する。

固定理由の実原本は`guest-recheck-failure-reason-result.json`、SHA-256先頭16桁は`9de89c5e301fc52f`である。raw logは転送せず、この診断によるモデル呼出しと変更操作は0回だった。3回の拒否を、独立した3件の利用者試行に増やさない。

実原本`guest-recheck-metadata-2-result.json`のSHA-256先頭16桁は`26a139475e20b8c4`で、SSMの実行自体はSuccess・exit 0だった。metadata取得の成功を数学回答の成功には数えない。説明の完走・保存・再読み込みの受入は未達であり、runtime切替の成功と元の説明障害の復旧を分けて扱う。今回の1件は、冒頭の実配備基準の失敗1件とは別の実試行である。

## 承認済みの隔離再現で確認した過剰拒否

オーナーの承認後、同じ検証済み66行のLeanと関連チャット文脈を使い、現workerの説明生成だけを1回実行した。実factoryの`gpt-6-luna / low`を保持し、診断用に生成回数を1回へ制限した。APIは対象2件のGETだけで、claim・upsert・独立QA・回答公開は行っていない。新しいモデル出力であり、失われた本番の3候補を復元したものではない。

生成文は、任意の実数点`a`と正のεに対し、`C=2|a|+1`、`δ=min(1,ε/C)`と置く証明だった。三角不等式から`|x+a|<C`を得て、平方差を`|x-a||x+a|`へ分解し、`|差|≤|x-a|C<(ε/C)C=ε`と結んでいる。独立した数学確認で、量化・正のδ・厳密不等式に問題がないことを確認した。

現判定は`δ`の式の中から点を直接探すため、`min(1,ε/C)`では点の候補が0となり拒否した。診断用コピーだけで`C`を展開しても、同じ量の別文の評価と、最後の約分の等式連鎖で拒否が残った。この新sampleでは、数学的に妥当な説明に対する製品側の過剰拒否を確認できた。元の本番3候補や公開再検証の失敗出力は、引き続き未保存である。

生成は14.400秒、保存usageは入力5,415・出力1,648 tokenで、出力の内数としてreasoning 170 tokenを記録した。請求額や完全な費用は算出していない。数学JSONのSHAは`04b8f8c3f7151c4562380174a516e60f983f5b9409e2e3146d039caa7c589678`、private診断記録のSHAは`13ab8d95a7e1b555d49aa2ce93e740183b5f670c7447c848d747f3fa4589f73e`。認証値、provider raw、reasoning本文は出力せず、稼働中containerの継続も確認した。

別の読取専用inventoryでは、現fingerprintに対応するtoolchainは既に存在する一方、平方専用IDと同一sourceのrevision・公開Entryは0件だった。既存release loginのcatalog owner membershipを確認した。vector storageは未配置で、現APIは字句検索へfallbackする設計である。DB更新やDDL追加は行わず、隔離containerとRAM設定の削除を確認した。本番Recipe審査鍵の所在は未確認で、公開準備と説明判定の修正を分けて進めている。

## R3の修正と署名済み候補

[R3の検証記録](incident-square-validator-r3-preparation-2026-11-06.md)に、正しい表記14通り、数学的な誤り42通り、評価の結び方に関する対照14通りを固定して比較した結果を記録した。最終Agentは`210ece8912b65e9bbb023b3341f7a1af9de09ae4`、Infraは`d3661e3b69ccb9b277a99703a59d3e76db198a6d`。関連526テスト、Infraのcompute・recovery 282テスト、独立レビューが通過した。新しい隔離sampleは、実66行Leanの全参照を含むparserでも通過した。本番の元3出力を再現した結果ではない。

workerを固定baseから実ビルドし、二つのimport先のsource・Lean child・21 layerを照合してECRへ保存した。新imageは`sha256:221d2c3fe7ba05a110a68b25a2ecd43c87e53bfaa07d7dc8065e4d93a5853d02`。実OCIのindex、amd64 manifest、configとrootfsも別途照合した。新parent capture `741afc844899e3456c4a770881f1d2ea0e77de62`はseq22 sourceの直接の子で、AgentとInfraのgitlinkだけを変えている。正式な四役割のpublication receiptは`dbf36b83d8c62d519d96dfeced540eaf0fd36484a9c64b2620db96275724c6c3`で、API・Web・verifierのimageを保持した。

seq23候補のmanifestは`3f8e3dd94323d13d41292cf4f7594c68363a31235e1e73cb7536f7370c809d11`。既存KMS鍵で新たに署名し、公開鍵による検証とKMSの検証が成功した。signatureのSHAは`dc9b0a217d876cd4e7712fc77a5e571ab5350325ec902b5b351872a3045949a1`、候補の期限は2026年11月7日13:29:39 JSTである。schema35、API・Web・verifier、toolchain、TLSとruntime bindingはseq22と同一で、変更imageはworkerだけである。

署名済み候補から配備準備用の20出力を再生成し、全bytesの一致と独立レビューの通過を確認した。事前image読込用の検査で旧sequence条件を1か所検出し、実行前に23へ修正した。対象はv2 helperのSHA `ddf0f3f7049a3ae34fdbd4fe1dd8b4fa2331c5bfc558ed96b639517c6740fb51`だけで、旧生成物は実行していない。実packetと型の正負条件を含む40オフライン検査が成功した。

13:39:48 JSTのIAMシミュレーションでは検証用4操作がすべて`implicitDeny`だった。regionと現在時刻を指定した読取評価で、実EC2のcontextや実preflightを再現したものではない。`MissingContextValues`は保存していないため、拒否原因をこの記録だけでは確定しない。権限変更は0回である。

この時点ではR3の本番ホスト配置、一時IAM権限、DB admission、切替、公開画面の受入を行っていない。現在の本番は引き続きseq22で、期限も11月7日10:52:38 JSTのままである。前の承認は別候補を対象としていたため、新候補の配置・検証用一時権限・条件付き切替を改めて確認する。

Recipeについて、現APIのモデル呼出し0回の対応は、固定した一般べき乗の日本語2文とEntry等の完全一致条件に限られる。平方専用Recipeを公開するだけで、今回の入力や言い換えを即時に返せるとは保証できない。専用Entryの公開と、対応する入力の安全な照合を分けて検証する。

## 本番反映の残作業

残る作業は次のとおり。

1. R2反映後の説明生成失敗を固定された段階・理由で調べ、必要な修正後に公開UIの説明完走・Lean参照・保存・再読み込みを受け入れる。今回のruntime切替とreadinessだけで、説明障害の復旧済みとはしない。
2. 次の署名期限までに正規更新を行う。再起動を伴う復旧の実試験は未実施で、導入済み復旧設定の検証と区別する。
3. [平方専用RecipeのIssue #287](https://github.com/AtsushiHosaka/pals/issues/287)で、現toolchainのcompiler証拠・独立審査・署名に結び付けて公開し、保存回答を返すことを確認する。現vector storageは未配置のため、既存の字句検索による公開と、将来のvector導入を分ける。日本語回答は著作草稿で、Recipeは未公開である。旧localのcompiler receiptは本番へ流用しない。公開後も意味対応の審査は残るため、モデルを呼ばず即時に返す経路は別途検証する。
4. DLQの時刻・失敗種別と、品質監視の実収集・抽出・警報を確認する。再配信・削除は原因調査と分ける。

## 再発防止の実施計画

| 対策 | 担当領域 | 完了の根拠 |
|---|---|---|
| 専用検査で数学的条件と表記の好みを区別する | Agent／#223 | 変数改名・日本語・同値なδ構成を受理し、誤ったδや量化・不等式の欠落を拒否する回帰を確認する。独立審査とLeanの条件を保持する |
| 説明生成の終端失敗を、固定された段階・理由で記録する | API・Agent／#217 | 成功と失敗の永続記録へ対応付け、再配信を重複計数せず、未分類を可視化する |
| 専用品質イベントの収集をCloudWatchまで接続する | Infra／#217 | 実ログ受信、EMF抽出、メトリクス、アラーム遷移、欠測検知を実測する。全アプリログの外部転送で代用しない |
| 低トラフィック時の説明失敗も見落とさない | 品質監視／#217 | 件数・率・最小標本数の条件を明示し、少数の失敗が率アラームの条件未達で放置されない運用を確認する |
| 配備後に利用者の操作を通した完走確認を行う | リリース運用 | ゲストと認証済み利用の説明・Lean参照・保存を確認し、失敗があればリリース完了としない |
| 署名期限の監視と正規更新を継続する | Infra／#142 | 現行期限、更新責任、期限前更新、失効後の正規復旧を確認する |

既存liveness監視の対象はコンテナのhealth、worker再起動、SQS接続不可で、説明失敗の監視とは異なる。#217の最新記録でも品質collectorは本番の受信・抽出・アラームが未確認だった。再発防止の完了は、実装やmergeと、本番での監視稼働を分けて報告する。
