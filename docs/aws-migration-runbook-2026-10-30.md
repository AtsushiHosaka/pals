# PALSのMac miniからAWSへの移行手順書

開始日 2026年10月30日。ユーザーの指示により、本番移行、必要なAWS構成変更、DNSの向き先変更、draw.io図の作成を実施対象とします。Web・APIはt4g.medium、計算ノードは通常r8a.large、大会時r8a.xlargeを使う方針です。作業を完了した段階だけを実施済みとし、コード・ローカル試験・AWS配備・DNS切り替えを区別します。

当初は回答生成の確認後にDNSを切り替える計画でした。その後、ユーザーが旧サービスの停止と公開接続の先行復旧を許可したため、AWS APIの正常性を確認してDNSを切り替えました。回答生成の成功は別途確認します。Cloudflareのネームサーバーは維持し、ドメイン移管は行いません。

## 現在の実行状況

型付きDraft35件を、正式な登録関数でAuroraへ非公開登録しました。内訳は線形代数5件、加群22件、微積分3件、整数論5件です。独立した内容審査の署名を検証し、全件の本文・構造・埋め込みを読み戻して一致を確認しました。登録記録は順にSSM `cb77de59-2ff5-4d0d-9392-ca2530fb942f`、`ae1e2d10-96f9-489f-8dc4-a18db6f5d7e4`、`ae98c4ed-89d3-46e8-a547-da71879e09d7`、`8bdc99f5-a110-450e-81a3-a42c43cd18b0`です。公開検索対象はまだ増えていません。専用の内部評価APIから線形代数5件を取得できることもSSM `32a07d4b-07a8-4253-b4b4-cd2917a3967e`で確認しました。これは登録済み埋め込みを使った接続診断であり、AIを通した検索評価とは区別します。

実際の検索評価の初回実行は、公開CAの親ディレクトリが既存ワーカー所有の0500であることを許容しない検査で止まりました。AI呼び出し前の停止で、一時鍵の削除はSSM `a9f71d6f-fbbb-4c8b-8dcf-1d2533d574cb`で確認済みです。実機の所有者・権限をSSM `caa123f8-ec5f-4c48-ac2e-e0b51ff585ee`で確認し、公開CAだけを既存ownerの検証関数で読むV2へ修正しました。資格情報の保護条件は維持しています。

追加候補744件のうち700件は、修正後の再審査を含め、内容審査を通過しました。却下記録も保持しています。重複の除外と分野ごとの実行評価が未完了のため、この700件を公開件数や1,100件達成の根拠には使いません。

公開画面からの追加試験では、導関数が常に0の関数が定数であることの証明と、互いに素な自然数に対するBézoutの等式がLean検証で失敗しました。失敗したjobは順に`dac57140-1fdc-4243-85ce-5300966f153f`、`6577346c-0f36-44e5-81ff-ddaf591fa101`です。失敗記録を保持し、成功率には含めません。導関数の問題は、使う補題を明示した別要求`b2e18051-7064-4314-9a7d-8179411c78e4`で回答まで完了しました。job`c2727827-9723-4f97-bf0f-ab1dbf3b8e55`のLeanコードと検証署名の対応を確認し、画面にも回答とコードが表示されています。最終コードは`import Mathlib`を使い、待ち時間と修正を含む回答時間は337.208秒でした。確認記録はSSM `484f5752-f6b7-4168-9b27-dd3c1b4ba21d`です。元の失敗要求の結果は変更しません。Bézoutの問題も、必要なimportを指定した別要求`cb418281-d7fb-445f-a32c-e931f2ca7cb0`では、job`8722377f-5385-4147-a64f-96eaf26b236e`が検証を通過し、88.461秒で回答しました。Leanコードと検証署名の対応はSSM `3785d807-e48d-489f-84bd-aa8cc4bb8810`、回答とコードの表示は公開画面で確認しています。

21:39 JST、型付きカタログの追加に必要なAPI・ワーカーの更新を配備しました。manifestは`32e03a841b2834f821a6d16af15b2ddd5f1a952abb9c918630552bfce76440dd`、APIは`a264385f9886a66e249c77b169a576ab1b0ed34f`、workerは`eb90a68c05499d3716a835e2a0cb1ff96da1faa4`です。verifierのイメージは維持しています。処理中のclaimとLean子プロセスが0であることを確認し、4つの書き込みコンテナを正常停止してから、正式なAurora更新処理を実行しました。DB更新5項目の成功記録はSSM `6271faeb-4124-439b-940e-cf1ee5942839`です。

更新後は7コンテナ、private TLS接続、復旧用unit3本を実機で確認しました。Draft433件、登録済みRecipe102件、承認済み検索entry20件を保持し、20件は正規の`checked_recipe`でも照合しています。型付きDraftの公開はまだ有効化していません。ALBの設定とルールを保存済みの状態へ戻し、公開チャットの読み込みとALB targetの`healthy`を確認しました。署名検証・RDS参照の一時IAM権限も削除済みです。確認記録はcontrolのSSM `e7722408-337e-4f5c-b0aa-2f29bb10ca74`、computeの`3aec2a73-7015-45f2-a03a-677208a7b526`です。

21:41 JST、新構成でも自然数冪の連続性の回答とLeanコードを公開画面で確認しました。要求`1f1fb9f5-a091-47e7-9b98-014f1babe3a8`は`answered`、job`2a0b9968-98cc-43a3-90db-94dd631bd1cf`は`verified`で、attestationを保持しています。今回は検索候補が0件で、証明を1回修正して生成し直しました。回答確定まで127.442秒、最後のLean検証は3.499秒でした。以前のRecipe再利用試験とは入力文が異なるため、更新による速度変化を示す比較ではありません。確認記録はSSM `8ba5ba15-59a8-43a5-bdb4-03b98564776e`です。その後の読み取り確認で、この要求は回答言語`en`、既存の公開Recipe20件はすべて`ja`であり、言語フィルターによって候補が0件になったと確認しました。同じ検索語を`ja`として照会すると、自然数冪を含む8件が候補に出ます。これは診断用の読み取りであり、元の要求や設定は変更していません。照会記録はSSM `00364e77-b758-498b-9ea6-776d51011c94`です。回答言語は画面の言語とは別のアカウント設定で、未設定時は英語になります。質問に明示した「日本語で」などの指示は、この設定より優先されます。

21:57 JST、「日本語で」と明示した自然数冪の連続性の問題で、公開画面の回答とLeanコードを確認しました。要求`40f78ed9-df4d-4144-bb20-eeda139fc7f6`は`ja`で保存され、8件の候補から`requested.natural_power_continuous`を選び、`catalog_reuse`で回答しました。独立した対応審査の承認と保存回答のハッシュ一致も確認済みです。回答確定まで39.677秒で、新規の証明jobは作成していません。これはRecipeの再利用成功であり、1秒回答や30人同時利用時の10秒以内完了を示す結果ではありません。照会記録はSSM `946de6b6-f1e5-492f-93da-fbd1725d11fd`です。

22:03 JST、公開画面から送った階数・退化次数の定理が回答まで完了しました。要求`98778298-e673-4fae-9d67-b7b2bd819e51`、job`de8d84b5-e6d7-4157-850c-6bb5a9832ef2`で、最終Leanコードとattestationの結び付きを確認しました。修正10回を含み、回答まで659.528秒かかっています。22:06 JSTには商加群の標準射影の核の証明もjob`eca2b2ef-5beb-4a01-972f-8fbcd5a14c3d`で検証を通過し、回答とLeanコードを確認しました。確認記録はSSM `a5bb17ef-fd1b-41e9-9385-1a2a00f08351`です。

証明workerの並列化コードはAgentの`f04caf5d61525106b132eb0833beea6f28d796de`へpush済みです。既定値1を保ち、明示的に指定した場合だけ独立した2〜8プロセスでproof laneを処理します。178件のローカル試験と履歴を含む秘密値検査は通過しましたが、本番のworkerは引き続きseq4の旧imageです。実機のメモリ・PID上限・配送処理の終了確認を行う前に同時実行数は増やしません。

不足したimportを未知の定理と誤認していた修正指示を見直し、Agentの`8aa699b5397da6333930675b8b4cb3701ea9388b`へpushしました。補題を定義するファイルを確認し、不明な場合は一度だけ`import Mathlib`で再コンパイルする指示です。証明の仮定や結論、Lean検証条件は変えません。46件の試験と静的・秘密値検査は通過しましたが、本番配備と修正回数の改善確認は未実施です。このcommitのworkerイメージをECRへpushし、OCI manifest・config・実イメージ内のソースファイルが一致することまで確認しました。新しいimageは`pals-prod-worker@sha256:965852c3c1baa74aeadef78213c1c3f8049f8727af02841e88a58c4771eb7a4b`です。稼働中サービスは引き続きseq4です。上記2件の失敗コードは、同じLean・Mathlib版でimportだけを修正すると、証明本体を変えずにコンパイルできました。

現行署名の期限は**11月1日20:50:31 JST**です。復旧unitは新しい実コンテナIDと設定で有効化しましたが、実再起動試験は未実施です。期限後の運用ツールによる再起動・再構築には正規の次リリースへの更新が必要です。これは、下記の検証用Pro枠の有効期限とは別の条件です。

21:18 JST、ユーザーが指定した検証用アカウント1件に、正式な管理機能で期限なしの無償Pro枠を付与しました。枠はUTCの暦月ごとに300万利用トークン、1要求の上限は30万です。購入や請求は発生させず、他アカウントやゲストの枠は変更していません。付与後、画面で「有効期限はありません」と利用可能枠を確認しました。付与に使った一時DBログインと一時IAM権限は削除済みです。付与記録はSSM `8c6c343e-8f67-4fe4-a6c3-235e16f04a7a`です。

この枠で「穴あき近傍での有限極限と、点の値を補った関数の連続性の同値」を公開画面から送信し、証明の説明とLeanコードの表示を確認しました。実要求`b7f977e3-5dc2-4c42-9b31-c092245698f1`は`answered`、証明job`712c4f22-3718-4c7c-b588-bf2446c0d177`は`verified`で、Leanコードとattestationを保持しています。サーバー上の要求作成から回答確定までは155.822秒でした。これは検証枠を使った本番の実証明成功であり、型付きDraftの公開や速度目標の達成を示す結果ではありません。読み取り確認はSSM `419f3233-8210-47d3-8940-8af40abd7e62`です。

20:32 JSTの読み取り集計では、検索対象Draft 433件、登録済みRecipe 102件、承認済み検索entry 20件、型付きDraftの有効件数0件を確認しました。新しい82件はAWSの実Lean検証とAuroraへの登録・読み戻しまで完了しています。日本語説明の独立審査と検索公開は未完了です。既存20件のLeanソース・コンパイル記録・レビュー署名・toolchainの対応も保持されています。集計記録はSSM `2bc71a15-453f-4442-a722-45923eba3a05`、82件の登録完了記録は`b27d0166-a304-4a86-8b12-29f1fbbbc860`です。

744件の型付きDraft候補はローカルの実Lean検証と使用公理検査を通過しましたが、本番公開済みには数えません。1,100件以上を利用可能にする目標は未達成です。AuroraのTLS必須化と実接続検証も完了しましたが、writerは`pending-reboot`を示しており、再起動は行っていません。設定確認の範囲、残るセキュリティ課題、件数の区別は[別記録](aws-security-and-catalog-check-2026-10-31.md)にまとめています。

公開ブラウザでの更新後試験は成功しました。同じ自然数冪の連続性の質問に対し、検証済みRecipe `requested.natural_power_continuous`から回答とLeanコードを表示しています。実リクエスト`1ee9b16d-fd6b-493a-8fcd-3c3e344830f2`は`answered`、証拠は`lean_catalog`です。異なる2セッションによる対応関係の確認、保存した回答のhash一致、実コンパイル記録との一致も通過しました。この質問では証明jobを新規作成していません。

サーバー上の作成から回答確定までは25.003秒でした。前回の154.333秒とは、同じ問題に対する各1回の測定です。今回は検証済み証明を再利用しているため、API修正だけの効果を分離した比較ではありません。ブラウザの通信・描画まで含めた厳密な時間測定でもなく、1秒回答と30人全員10秒以内の目標は未達成・未検証です。

19:43 JSTの更新時にも、再起動復旧用の3つのsystemd unitを当時の7コンテナの実IDと設定へ更新しました。有効化前後でコンテナの稼働状態が変わらないことを確認しています。当時の署名の期限は11月1日19:19:25 JSTでした。現行の期限は上記21:39 JSTの記録を参照してください。稼働中APIが署名の時刻だけで停止する実装ではありません。

容量切り替えは、`normal = r8a.large`、`event = r8a.xlarge`の設定と、同じEC2のサイズだけを変更するplanの検査まで実装しました。この検査ツールはAWSへ変更を適用しません。既存EC2のサイズ変更は通常の配備コマンドで拒否し、受付停止・処理終了の確認・サイズ変更・正規復旧をまとめる操作は未実装です。実機は引き続き`r8a.large`、Leanは1枠で、自動スケールは導入していません。新しいサイズ設定とIMDS照合コードも本番へは未配備です。

応答時間の各処理と、1秒を目指す次の契約案は[Recipe再利用の実測](aws-recipe-reuse-latency-2026-10-31.md)にまとめました。単なる検索順位で回答を選ばず、問題と証明の対応確認を保つ設計が必要です。

ゲスト枠は従来どおり、セッションと同じネットワークのそれぞれで1日3回、サービス全体で1日100回です。今回の公開試験で作業端末のネットワーク枠を使い切りました。大会で同一ネットワークから30人がゲスト利用するには、この制限の変更が必要です。現時点では変更していません。

19:43 JST時点で、回答の保存完了を処理待ちループへ即時通知するAPI修正版への切り替えが完了しました。新manifestは`e929f91d3a456521bb3b472d0609a29767bdd8cbda0ea298a41c8424e57a882b`、API commitは`897cae738beedc9792ccfd1475058914b68e2154`です。DB更新の5項目、全7コンテナ、実mTLS接続とAPI再起動後の正常性を確認し、ALBの公開受付を元の設定へ戻しました。署名検証・RDS参照の一時権限は削除済みです。更新後も、正規の`checked_recipe`で検索entry 20件の内容保持と4検索すべての1位一致を確認しています。実行記録はDB更新`13a29a63`、接続確認`64634643`、20件保持・検索`0ac34852`です。

19:31 JST時点で、追加20問すべてがAWSのLeanコンパイルと独立レビューを通過し、Auroraの検索用entryへの登録も完了しました。実DBから20件を読み戻し、正規の`checked_recipe`で各証明・レビューとの結び付きを確認しています。実行記録はSSM `4ca1905a-bd92-4395-96d2-4f1d337d0fcc`、公開用索引のSHA-256は`07a8ac480709f7784b1f31c4bc28d04d6e7d70dff0e58755f66e281acdf3abed`です。独立レビューで指摘された量化条件や説明を修正したうえで承認を受けており、不承認結果の強制上書きはしていません。

対象は、自然数冪の連続性、`tan 1°`の無理性、`π > 3.05`、右極限と原点での不連続性、微分公式、階数・退化次数、単射と核、行列式、連立方程式などです。右極限の問題では負の側の値を仮定せず、定義域に沿って`x → 0+`を扱います。`π > 3.05`はMathlibの既存下界から導く証明です。検索登録の成功と、公開回答での再利用成功は別に記録します。

続く読み取り試験では、自然数冪・円周率・tan 1°・右極限の4検索すべてで目的のRecipeが1位に出ました。前後の本番readiness 33項目も通過しています。実行記録はSSM `96e6a4da-9255-4c2b-8fbc-9f9183fee099`で、この試験では質問作成、LLM呼び出し、Leanコンパイル、DB更新を行っていません。

19:14 JST時点で、既存サービスの再起動用systemd unitをcontrolに2本、computeに1本配置し、有効化しました。全7コンテナのID・稼働状態・restart policyが前後で変わらないことを確認しています。実際の再起動試験は未実施で、署名の有効期間内に限る復旧処理です。現行署名の期限は11月1日18:33:58 JSTであり、期限後の運用ツールによる再起動には正規の次リリースへの更新が必要です。

本番がAuroraを使うことと接続0件を確認し、未使用の旧方式DB EC2 `i-041db5930304ef5d1`を停止しました。データ用EBSと専用endpointは保持しているため、それらの料金は引き続き発生します。稼働中のcontrol・compute・Auroraは変更していません。

19:05 JST時点の状態は次のとおりです。後続の時刻付き記録と「方針変更前の実行記録」は、各時点の状態を残した履歴です。

| 対象 | 現在の確認結果 |
| --- | --- |
| 公開Web・API | 両ドメインをAWSへ切り替え済み。公開ブラウザからゲスト質問と回答表示を確認 |
| Lean回答 | 自然数冪の連続性で実証明・attestation・Leanコード表示を確認。回答確定まで154.333秒 |
| 本番DB | Auroraで稼働。初期化seedのDraft 433件に加え、新しいRecipe 20件をAWS実verifierで検証して登録 |
| Recipe検索 | 独立レビューは3件承認、1件不承認、16件未実施。検索用entryの登録はまだ0件で、20件すべてが回答に再利用できる状態ではない |
| 料金通知 | 本番アカウントの5通知を設定・読み戻し済み。メールの実配信は未検証 |
| 運用と性能 | 再起動復旧、通常・大会モード、自動増減は準備中。1秒回答・30人の最終待ち時間10秒以内は未達成・未検証 |

20件の実コンパイル記録は`pals.math-seed.compiler-receipt-index.v1`、索引のSHA-256は`29aa5a8ccb7dde17c2ab9fa5bcc7cd120fadf7a35a52c698706f0d9e9f45d3ae`です。問題文と説明の独立レビューは別段階で、不承認のentryを公開検索へ追加しません。旧Mac miniの履歴は抽出していません。

18:56 JST時点で、公開ブラウザから送った自然数冪の連続性の問題に、回答とLeanコードが表示されることを確認しました。実リクエスト`8bf7b7ed-b672-4cac-a48d-6f29e2039746`は`answered`、証拠は`lean_verified`、証明jobは`verified`でattestationと解説を保存しています。サーバー上の作成から回答確定までは154.333秒、最終Lean検証は3.499秒、コード修正は2回でした。これは回答復旧の証拠であり、1秒回答の達成ではありません。数学20問のAWS登録を続けます。

再起動への備えは未完了です。実コンテナのrestart policyは契約どおり`no`で、ホストにはDockerと認証brokerの起動設定はありますが、アプリ復旧用unitはありません。現在の署名の有効期間が過ぎても、Aurora APIの既存readiness処理が時刻だけで停止する実装ではありません。一方、インフラ運用ツールによる再構築には有効な署名が必要です。失効後は直前の署名を履歴として検証し、連番を進めた正規の更新が必要になります。

18:52 JST時点で、修正版の全サービスが起動しました。control・computeの正規起動処理、reconcilerの実mTLS、新リリースとDB接続の再検証が通過しています。実起動の記録はSSM `ea13b8ca`・`55503b38`、control設定のSHAは`de5e7e62c2d29e5297fc8bbb1f139b60e2dc65c94419680be6be70f960486c07`です。公開ブラウザから自然数冪の連続性を送信し、回答を確認中です。20問の問題データはAWSへ配置済みですが、検証枠の競合を避けるため登録は公開質問の終了後に実施します。一時的なKMS検証・RDS参照権限は削除し、削除結果も確認しました。

18:46 JST時点で、既存Auroraに対する署名付きソフトウェア更新が成功しました。DB識別・既存schema/role・接続停止・新リリース登録・既存DB保持の5項目を通過しています。実行記録はSSM `60176488-d467-4045-bdc9-63fd9ca095b9`、新manifestは`5a75bfe652ba03c94f02c2655fb1dfb34c39e32294417d7328b769c1477a53f8`です。更新専用ツールのrole検査を修正したイメージと、署名済みの稼働用APIイメージは分けています。サービス再起動と公開回答は続けて確認します。

18:45 JST時点で、旧API・reconciler・評価worker・証明workerの4コンテナを実IDで照合して停止しました。新しい署名構成の更新処理は、署名検証用の一時権限不足と、運用アカウントでアプリ用権限制約を検査する不備により停止しています。DB変更はロールバックされ、新リリースは未登録です。後者は実DBで運用用33項目・アプリ用33項目を読み取り検査して全通過を確認し、更新専用ツールだけを修正しました。稼働用APIの署名・イメージは維持し、修正版ツールによる再実行を準備しています。

18:37 JST時点で、修正候補のAWS隔離試験が成功しました。HTTPと同じ専用scratchで自然数冪の連続性をコンパイルし、同じUIDで事前に読めたTLS隣接ディレクトリ内の試験ファイルが、Landlock適用後にEACCESで拒否されることを確認しました。初回40.088秒、続く試行4.385秒でしたが、後者の環境キャッシュはfallbackであり、キャッシュによる高速化や1秒回答の達成を示す測定ではありません。本番サービスへの更新と公開回答は未確認です。

18:35 JST時点で、修正版API・worker・verifierをECRへ公開し、既存Auroraを初期化しないソフトウェア更新構成に署名しました。DB更新は未適用です。既存releaseアカウントについて、全108テーブルの必要権限とschema ownerへの切り替え権限を実DBで確認し、権限追加が不要なことを確認しました。

Lean修正のローカル隔離試験では、修正版ソースの読み込みと専用scratchの検査が通りました。その後、Mac上のAMD64エミュレーションがLandlock ABIを提供せず、`ENOSYS`で停止しました。これはAWS実機の成功を示すものではありません。修正版のAWS隔離試験を実行中です。

### 10月31日、履歴を移さず新規DBで起動する方針への変更

ユーザーはチャット履歴を抽出しないこと、Draft・Recipeは後から再生成して追加してもよいことを指示しました。これ以降は既存DBの抽出を起動の前提にせず、用意済みの空の本番Auroraを正規の初期化処理で起動する経路を実装・検証します。旧Mac miniのDBは削除しません。既存の全データ移送を前提とする下記の手順と記録は、この方針変更前のものです。

直近の実記録では旧DBだけが稼働し、API・Web・workerなど他の7コンテナは停止しています。AWSのWeb表示とゲスト接続は確認済みですが、回答生成の復旧は未確認です。抽出処理はスキーマ確認先の誤りを修正後、専用Draft読取接続の入力不足で停止しました。追加の抽出実行は依頼しません。

10月31日17:25 JST時点で、本番Auroraの新規初期化は成功しました。空DBを実測した後、新規初期化専用の署名を検証し、33段階の本番マイグレーションと専用アカウントの接続確認を完了しました。実DBにはDraftが433件、Recipeが0件あります。433件は初期化用seedから登録したもので、旧チャット履歴の抽出は行っていません。API・Leanの起動と公開チャットの回答確認はまだ完了していません。

10月31日18:06 JST時点で、AWSのAPI・Web・Caddyと、計算側のLean verifier・評価worker・証明workerは実機で起動を確認しました。API targetはhealthyとなり、`api.palschat.site`を既存のCloudflare proxyを維持したままAWS ALBへ切り替えました。公開APIのゲストsession作成と、ブラウザで質問欄が入力可能になることを確認しました。reconcilerのmTLS起動確認は失敗しており、回答生成の完了はまだ確認できていません。controlのDocker networkは、既存の本番APIの固定peer要件に合わせて`172.30.0.0/24`へ修正しています。

今回の数学20問はローカルの実Leanコンパイルとaxiom検査を通過し、閉じたRecipe manifestから生成した20個のソースも別途コンパイル済みです。AWSの実verifierによる登録、独立した回答照合、検索・公開回答の確認は未完了です。

18:19 JST時点で、reconcilerの実mTLS接続と全コンテナの稼働確認は通過しました。正常時に空ファイルを作るready markerの仕様に対し、配備側が非空を要求していた誤りを修正しています。Webも本番CaddyのHTTPS 443へ統一し、一時Webのコンテナ・専用network・firewall、8080のsecurity groupルール2件とtarget groupを削除しました。公開ブラウザの質問欄は利用可能です。

公開試験の自然数乗の連続性はworkerで処理されましたが、Leanコンパイルに失敗して修復生成を繰り返し、約4分の監視期間では回答に至りませんでした。数学20問の実登録も最初のコンパイルで失敗し、登録0件を実DBで確認しました。実機で、HTTP用の`/run/pals-verifier-requests`と、Lean子プロセスの`/run`拒否条件の不一致による`lean.sandbox_setup_failed`を再現しました。専用scratchだけの修正と、稼働済みAuroraを維持した正規のソフトウェア更新を進めています。検証を省略した登録は行っていません。

実配備のrelease IDは`a3705124-066c-4301-8e4e-a0713d014034`、manifest SHA-256は`4dd5c0657746cbc1eb33673e6cb17690dec7d52d100a9689b0fb6ff15da4620f`です。初期化SSM実行`5834b0e9-0dad-426d-8269-37b997c904fe`は成功し、専用の一時master読取権限は削除済みです。既存データの復元記録を新規DBの成功記録として流用していません。

復旧後は実DBのLean関連構造、Draft・Recipeの件数と内容を確認します。追加対象には「tan 1°は有理数か」「π > 3.05を示せ」、自然数nについてのx^nの連続性、線形代数・微積分の証明・判定・計算問題を含め、問題文と証明を照合し、実際のLean検証に通ったものを登録します。登録済み問題の再現試験と、未登録問題への一般化の評価は分けます。f(0)=1、x>0でf(x)=0という問題は、定義域を明示した右極限0として扱い、負の側の定義を補いません。

### 方針変更前の実行記録

2026年10月31日15:45 JST時点。13:00までのAWS切り替えには間に合っていません。Webを先行し、`palschat.site`はCloudflare経由でAWSのprivate controlから配信しています。実トップページと静的ファイルの200、ALB targetのhealthy、公開URLへの一意なリクエストの200と`CF-Cache-Status: DYNAMIC`、ブラウザ表示を確認しました。Cloudflareのフル（厳密）も保存後に読み戻しました。APIの`api.palschat.site`はMac miniを向いたままで、AWSのAPI・LeanとDB復元は未完了です。Webの表示を回答生成や30人の負荷確認の代わりには扱いません。

Web先行公開では、ALBのHTTPS listenerに`palschat.site`だけの優先順位10の経路を追加し、専用target groupのHTTP 8080へ転送します。controlへの入口とALBの出口は、互いのsecurity groupだけを8080で許可しました。private control上の一時Webは固定image、読み取り専用filesystem、UID1000、capabilityなしで起動し、新規の外向き通信を遮断しています。ブラウザからのAPI呼び出し先は既存の`https://api.palschat.site`です。本番APIのHTTPS 443用target groupは変更していません。先行WebはAPIの本番経路への切り替え後、所有する一時コンテナとnetwork・firewallだけを片付けます。

13:51の準備は既存ロックの競合で停止しました。14:07の読み取り診断で、保持者は開始から4秒のauto_recoveryで、前回とは別のPIDと確認できました。設定とcontroller/watchdogの既知ハッシュは一致しています。同じ既存descriptor・inodeのロック取得を最大30秒待つ修正をpushし、実POSIX競合テストで取得・期限・ファイル差し替え拒否を確認しました。ロックの削除や保持者の強制終了は行いません。

ユーザーは旧サービスの停止と一時的な利用不能を明示的に許可しました。追加バックアップを省略し、必要なデータ移送を進める方針です。既存watchdogのメンテナンスに入り、秘密値5件の転送・照合、設定取得、ツール読込、SDK接続、MacとDockerの独立した実ロックの確認まで通過しました。15:30の失敗記録では、移行スクリプトがDB識別ボリュームの取り付け方を誤って要求していたことを特定しました。8コンテナはすべて稼働中で、最終取得のjournalは未作成でした。既存controllerと同じ独立した読み取り専用の観測方法へ修正し、pushしました。修正後の実取得はまだ確認できていません。

Parsecで入力先が別アプリへ移った経緯があり、自動承認レビューがEnter送信を拒否したため、Mac miniでのコマンド実行はユーザーへ依頼しています。右側の既存未実行入力は保持しています。ユーザーはさらに、AWS公開を優先し、既存ユーザーデータを新規作成してよいと指示しました。空DBからの既存起動経路も確認しますが、数学用catalogや証明・配備の検証を通過したことにはしません。

AWSのcontrol/computeでは、公開コード9ファイルと固定イメージ5件を事前配置し、実機のhash・所有者・mode・image config bytes・RootFSを照合しました。ECR用の一時認証ディレクトリが残っていないこと、実行中のアプリコンテナが0件であることを読み戻しました。これらは起動準備の完了であり、本番の復元・受理・起動を示しません。13:53のCloudflare管理画面でも、Web/APIとも既存Mac mini tunnelを向いています。

さらに入力組み立て用の公開コード2ファイルを両hostへ事前配置し、native Pythonでcompile/importを確認しました。実handoff資料とsource設定を用いた組み立て・起動は未実施です。DB用SSMトンネルを再接続し、実CloudTrailとActive session、TLS1.3・空DB・build/localeを読み戻しました。Cloudflareの現在のTLS設定は自動モードのフルで、AWSへの切り替え時にはACM証明書を検証するフル（厳密）へ変更します。

| 段階 | 状態 | 実際に確認したこと |
| --- | --- | --- |
| 対象と接続 | 実施済み | pals-prod-memberのSSOをユーザーが更新し、本番アカウントとの一致をSTSで確認 |
| 現行の公開サービス | 実施済み | WebとAPI healthのGETが200、未認証projectsが401。DNSはCloudflare経由 |
| AWS資源の棚卸し | 実施済み | 開始時点のCognito・S3・SQS・署名KMS・state bucketを特定。移行先EC2・Aurora・ECRは後続の基盤作成で追加 |
| 移行元への接続 | 練習用バックアップ取得済み | 同一snapshotのdump・schema・metadataと既存の配備署名資料を非公開S3へ転送。作業端末で6ファイルのハッシュを照合し、既存配備記録のKMS署名と固定公開鍵の検証に成功 |
| 基準環境への復元 | 実施済み | 移行元と同じimageで全108テーブル・6,390行のCOPY内容、role・membership・取得済みACL、schema構文木とsequenceを比較して一致 |
| Aurora互換性試験 | 既存データの実アプリ比較は通過、追加の文字検索は不一致 | 全108テーブル・6,390行、全24 role・18 edge、ACL・schema・sequence・vectorと全433件のvector検索が一致。実一覧・検索・ページ送りと3,828行の文字変換/FTS成分も一致したが、default照合順序と公開Unicode文字の検索条件に差が残る。本番用clusterは空のまま保持 |
| ACM証明書 | 発行済み | 現在のWebとAPIを対象に申請。Web/APIの検証に成功し、AWS ACMのISSUEDを確認 |
| private network実装 | 基盤作成済み・検証中 | 8 subnet、NAT、S3 endpoint、ALB、Auroraを作成。ALBログ書込みと経路を読み戻し済み。未使用legacy SGからのDB許可を除去し、controlだけに限定 |
| 既存資源の再利用 | 基盤で確認済み | 現在のCognito・S3・SQS・署名KMSを読み取り参照する経路を実装・試験済み。実planの独立照合中 |
| private control接続 | 実施済み | t4g.mediumを公開IPなしで起動。SSM Online、cloud-init完了、PG16.15 client、アプリ未起動markerを確認 |
| private compute接続 | 実施済み | r8a.largeを公開IPなしで起動。SSM Online、cloud-init完了、native x86 DockerとAMD EPYC 9R45、起動時のアプリ未配備markerを確認 |
| 短期AWS資格情報 | 実機検証済み | API/workerと各host supervisorの4 roleを分離。実STS認証とtimerによる更新、API image内のread-only mountからの資格情報検査に成功。アプリactorにはparameter・master・署名権限なし。supervisorには承認済みの完全一致GetParameterだけ追加 |
| AWS料金アラート | 設定済み | 本番アカウント全体の月額予算をUSD650へ更新。実費USD20・50・100・650、月末予測USD520超過の5通知とメール宛先をAWSから読み戻して照合。自動停止actionなし |
| Lean単体の測定 | 実施済み | largeで48件の実コンパイルに成功。必要なimportとLake環境再利用で中央値0.805秒。アプリ全体の遅延は未測定 |
| private EC2 DB | 起動・実接続確認済み | m7g.large、暗号化80 GiBの保持data EBS、専用SGと6 endpoint。実TLS1.3・PG16.15・locale/libc2.36・vector0.8.7を確認。空DBで、本番復元・受理は未実施 |
| 公開入口のWAF | 適用・読戻し済み | 実送信元がCloudflare公式15 IPv4 CIDRの場合だけ許可。default BLOCK、sampling無効。DNSとアプリ公開は未変更 |
| AWS runtimeと容量モード | アプリ未起動・容量制御未実装 | 別ホストmTLSによる本番接続、pool配送、drain、通常・大会モードの切り替えは未実施。largeからxlargeへの安全な切り替えには処理中ジョブのdrain確認と再開処理が必要 |
| runtimeイメージ | AWS実機へ事前配置済み | controlのAPI・Web・derived Caddy、computeのworker・verifierの固定digest/platform/config bytes・RootFSを照合。公開コード9ファイルも照合。一時ECR認証は削除済み、アプリコンテナは未起動 |
| runtime秘密値の引き継ぎ | 転送・実機読取確認済み | 固定5件を転送・照合済み。実controlの4件、computeの3件について、各host roleの実GetParameter・復号・固定metadata照合に成功。値はRAM内だけで処理し、公開出力は件数のみ |
| DNS切り替え | Webのみ実施済み | palschat.siteのCNAMEをAWS ALBへ変更し、proxyを維持。公開Webを実確認。api.palschat.siteは既存Mini tunnelを維持 |
| 移行後の受け入れ | 未実施 | ログイン、履歴、資料、生成、共有、ゲスト、負荷試験が必要 |

移行元はpgvector0.8.7、Auroraの提供版は0.8.2で、localeと文字検索にも差が残りました。ユーザーは10月31日、13:00の大会稼働に向け、現行と同じDBイメージのprivate EC2方式と追加費用を承認しました。Auroraは保持します。[EC2方式と運用責任](aws-postgresql-ec2-alternative-2026-10-31.md)、[実機の検証記録](aws-migration-verification-2026-10-31.md)を参照します。

上流のpgvector 0.8.7にはIVFFlat index作成時の脆弱性修正が含まれます。Auroraの管理版に同じ修正が取り込まれているかは未確認です。公式SQLで実測したAuroraの版は16.15.1でした。版番号だけで安全性を判断せず、AWSの該当buildについて根拠を確認します。[上流の修正情報](https://github.com/pgvector/pgvector/issues/1036)を採用前の確認対象に加え、[具体的な問い合わせ文案](aws-aurora-pgvector-security-inquiry-2026-10-31.md)の送信許可を待っています。

移行先ALB用のACM証明書、VPC・subnet・NAT・ALB・Aurora・ECR・必要なIAMと専用ALBログbucketを作成しました。Web/APIや計算runtimeはまだ起動していません。Cloudflareには証明書検証用CNAMEを1件追加しました。ACMの申請は配信先を変更しません。追加資源を作成した場合は、この表と秘密値を含まない実行記録を更新します。

## 移行する対象と保持する情報

Webの公開名は`palschat.site`、APIは`api.palschat.site`です。既存ログインのcallbackは`https://palschat.site/auth/callback`、logoutは`https://palschat.site`を維持します。使用中のCognito pool/client/issuerはそのまま使い、ユーザーやパスワードの移し替えは行いません。

アプリDBの全schema・行・sequence・所有者・ACL・署名付きadmission履歴を移送対象とします。資料の原本にはPostgreSQLのbyteaもあるため、S3だけを移せば完了するわけではありません。既存S3の成果物と参照、SQSのジョブ、ゲスト用hash key、provider接続、課金・利用枠・共有・継続質問の状態も維持します。

既存バックアップbucketには10月4日のphysical base backupが3件あります。10月30日には、新しい一貫したsnapshotに基づく練習用pg_dumpを取得しました。次に復元試験を行い、本番切り替え用には書き込み停止後のsnapshotを改めて取得します。

raw dump、DB接続先、鍵、provider token、Terraform plan/state、SSO cacheはGitに含めません。ローカルの作業記録はignoredの`.local/aws-migration/`に置き、ディレクトリ0700・機密ファイル0600を使います。クラウド上は既存の非公開backup bucketの専用prefixへ暗号化して保存し、許可した移送roleだけが取得します。

## 移行先のネットワーク

![AWS移行先の設計図](diagrams/pals-aws-private-target.png)

[draw.io元ファイル](diagrams/pals-aws-private-target.drawio)は編集可能で、PNGは実際のdraw.ioで出力しています。図の8 subnetとCIDRは基盤作成後に読み戻して照合しました。アプリ、計算poolと容量制御を含む図全体は、引き続き移行先の設計図です。

公開ALBは2つのpublic subnetに置き、ACMでTLSを終端してprivate controlのHTTPSだけへ接続します。Web・APIと計算ノードにはpublic IPを付けません。採用したPostgreSQL EC2はインターネット向けdefault routeのないDB subnetへ置き、controlのsecurity groupからの5432だけを許可します。

外部LLMへの通信が必要なため、private workloadの外向きHTTPSにはNATを使います。S3はgateway endpointを使います。初期のNATは1台で、AZをまたぐ通信と単一障害点を含む費用・可用性の選択です。EC2にはSSHを開かずSSMで管理します。verifierはさらにコンテナ単位で外向き通信を遮断し、DB・AWS・provider資格情報を持たせません。

次の約4.5万円は、10月30日のAurora方式の見積もりです。現在のEC2 DB追加、専用endpoint、保持中のAuroraと検証clusterの重複稼働費は含みません。採用したDB部分の見積もりは[EC2方式](aws-postgresql-ec2-alternative-2026-10-31.md)を参照します。通常のEC2本体約2.6万円に、NAT・ALB・Aurora最低容量などを加えて計算しました。2026年10月30日のAWS Price List APIで、東京のZonal NATは$0.062/時、ALBは$0.0243/時、Aurora PostgreSQL Standard Serverless v2は$0.15/ACU時と確認しました。月730時間、Aurora平均0.5 ACU、public IPv4最低3個を$0.005/IP時、1ドル150円と置くと、本体とこれらの合計は約4.5万円です。mediumとlargeは準備用として起動済みで、金額は通常構成の月額見積もりです。ストレージ、I/O、LCU、NAT処理量、通信、ログ、税、LLM利用料と移行中の重複稼働は別途かかります。[VPC料金](https://aws.amazon.com/vpc/pricing/)、[ALB料金](https://aws.amazon.com/elasticloadbalancing/pricing/)、[Aurora料金](https://aws.amazon.com/rds/aurora/pricing/)を参照します。

料金アラートは、既存の`pals-prod-monthly-cost`を再利用しています。private構成の月額予算はUSD650で、実費がUSD650を超えた場合と、月末の予測費用がUSD520を超えた場合に`hosaka2917+pals@gmail.com`へ通知します。設計時の固定換算1ドル150円では、それぞれ約9.75万円・7.8万円です。為替への自動追従や円建ての支出制限は行いません。既存の実費USD20・50・100の通知と、別管理の旧予算は保持しました。

対象は本番AWSアカウント全体で、外部LLM providerからの直接請求は含みません。AWSの請求集計には遅れがあり、予測通知は利用履歴にも依存します。料金による自動停止actionは設定していません。5件すべての閾値とメール宛先を実際のAWSから読み戻して確認しましたが、メールの実配信試験は行っていません。[AWS Budgetsの更新と通知の説明](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)を参照します。

## 実施手順

### 1 接続と現状の固定

`aws sso login --profile pals-prod-member`で接続を更新し、`aws sts get-caller-identity --profile pals-prod-member`で対象を確認します。別アカウントのpals-prod-adminを本番の代わりに使いません。CLIで確認した実際のCognito・bucket・queue・KMS identityを、ignoredの移行設定に保存します。

CloudflareのWeb/API origin、proxy状態、TTL、TLS設定、証明書検証レコードを読み取り保存します。既存Miniの稼働revision、image、DB identity、volume、現在の署名付きadmissionを読み取り記録します。秘密値を画面・ログに出さず、fingerprintや一致/不一致だけを残します。

### 2 証明書とAWS基盤の準備

ACMのWebルートとAPI用証明書を申請し、Cloudflareに検証CNAMEだけを追加します。これはWeb/APIの配信originの変更とは分けます。ISSUEDをAWS側で確認するまでALBの公開HTTPSを完了扱いにしません。

Terraformは既存データ平面をdata sourceとして参照します。新しいCognitoや代替bucketを作成するplan、既存ユーザーの設定変更、既存資源のdelete/replaceを含むplanは適用せず、差分の原因を解消します。backend、account、region、provider lock、source revision、plan digestを固定してから保存済みplanを適用します。

VPC、public/control/compute/DB subnet、route、NAT、S3 endpoint、ALB、Aurora、ECRと必要なIAMを準備します。この段階ではDNS originを変えません。runtimeのbootstrapが未実装のASGを、稼働する計算poolの代わりに作成しません。

### 3 最新バックアップと移送証拠

初回のsnapshotは移行練習用として取得し、最終切り替え用とは区別します。実行中の旧DBに対して、read-only exported snapshotと同じsnapshotのpg_dumpを使い、table/catalog/sequence/role/ACLの比較記録を作ります。DB内容を標準出力へ流さず、保護されたファイルへ書きます。

最終snapshotは、旧API、worker、reviewer、reconciler、OCRなど全書き込み元の処理をdrainし、新規書き込みを止めてから取得します。既存の停止・起動制御と署名ロックを使い、別の更新と競合させません。既存サービスの停止を、データやvolumeの削除で代用しません。

sourceの実DB/host/volume identity、現在のKMS署名付きadmission、dump digest、catalogとroleの比較記録、保持するguest key fingerprintと外部resource identityを新しい移送証拠に結び付けます。旧署名のpayloadを編集せず、元のadmission履歴も残します。

### 4 DBへの復元と受理

採用したEC2用には独立した`pals.production-database-restore.ec2.v1`を使います。実EC2/EBS/ECR/SSM/CloudTrailとTLSを結び付け、空DB、sourceと同じbuild・locale、全role・権限・行・sequenceを照合します。復元と本番受理は分け、直前の旧DB停止証拠を再確認してから受理します。既存Aurora用profileは変更しません。

以下はAuroraを採用する場合の条件として保持します。

移行先Auroraは本番と同じengine系統、非公開接続、TLSとCA検証で照合します。AWSのcluster/resource identityと実PostgreSQLの観測を結び付けます。RDSの管理roleはMacのtrue SUPERUSERと同じではないため、所有者・ACL・role mappingの差を明示して検証します。superuser向けglobalsを無条件にrestoreしません。

現在は本番受理の前に、互換性の検証を行います。roleはcluster全体に存在するため、本番用に確保した空DBとは別のprivate検証clusterを使います。同じsnapshotを移行元と同等のPG16環境とAuroraへ復元し、全table・sequence・large object・所有者・ACL・制限付きroleを照合しました。vectorの値と距離、検索順位、既存データの実一覧・検索・ページ送りも一致しました。追加Unicode文字では検索条件の差が実測され、資料の選択・抜粋を含む残りの機能比較も未完了です。[API側の検証計画](../pals-api/docs/aurora-compatibility-review.md)に対象を記録しています。

現在の本番復元v1はextensionとlocaleの一致を要求しており、観測した組み合わせを拒否します。互換性の検証で通過しても、この検査や元の署名情報を書き換えません。採用する場合は、証拠に基づく別の復元profileを実装・審査し、最後に書き込みを停止したsnapshotで本番復元を行います。

復元は検証対象の空の移行先へ行い、元のDBを上書きしません。行・sequence・catalog・資料原本・参照・権限を比較し、署名付きのsource→target移行admissionを専用経路で確定します。prepared_not_admittedの計画だけでは、復元・受理・本番readyの証拠になりません。旧Mac用bootstrapや更新validatorの同一host検査を外す変更では対応しません。

### 5 runtimeと容量モードの配備

arm64のWeb/APIとx86のworker/verifierを、固定したソースとtoolchainからbuildしてECR digestで配布します。reconcilerと別ホストverifierのmTLS、registry、claim、実行先のbinding、drainと再配送を実装・確認します。workerはDB資格情報を持たず、verifierはproviderやAWS資格情報も持ちません。

現行verifierは2 CPU・4GiBの上限検査があるため、提案の8GiBは契約と検査を改訂してから使います。Lean常駐化などの高速化も、Linuxの実メモリと隔離を測って有効化します。速さのためにLeanや独立レビューを省きません。

normalはlarge 1台、eventは指定したxlarge容量へ、新規ノードの準備→配送先変更→旧ノードdrainの順で切り替えます。待ち行列に基づく自動台数制御、上限、1時間超の処理、起動失敗、監視欠落、重複結果を確認します。単なるEC2の起動を、poolの準備完了とは扱いません。

### 6 DNS切り替え前の受け入れ

本番host名・TLS・Cognito callbackの条件を保った検証経路でAWS側を確認します。DNS切り替え前に少なくともログイン、既存履歴と資料、質問の前提確認、実際のモデル呼び出しとLean検証、回答保存、共有、ゲスト、課金・利用枠の表示を確認します。実課金・新たな購入は試験の範囲に含めません。

代表問題は、仮定を明示した実質的な推論が必要な題材を使います。禁止された単純な平方展開は使いません。再利用・初見・難問を分けて測り、単発と30件同時送信の全体時間、失敗、OOM、LLM制限を記録します。healthの200だけでは移行完了にしません。

### 7 最終同期とDNS originの切り替え

旧環境をdrainして書き込みを止め、最終snapshot・差分照合・受理をやり直します。AWS側の書き込みを開始する前に、一意の書き込み先を決めます。DNSの伝播だけでは旧側へ届く利用者を止められないため、旧APIの書き込み停止または新側への安全な転送を維持します。

Cloudflareの既存Web/APIレコードのoriginだけをALBへ向け、既存NSや不要なレコードを変更しません。対象レコードを変更前後で読み取り照合し、TLS、Cognito、SSE、既存データ、新規要求の確定を公開経路から再確認します。旧Tunnelは検証完了まで消しません。

### 8 監視と移行完了

公開経路の失敗率、各段階の待ち時間、API/worker/Leanの資源、DB、provider、費用を確認します。AWSへの新規書き込みがある場合、DNSを旧DBへ戻すだけの切り戻しは行いません。書き込み停止と逆同期または復旧手順を使い、二重書き込みとデータ欠落を防ぎます。

全機能と実データの照合、最新バックアップからの復旧、manual/auto容量制御、秘密情報と通信制限の確認を終えた後、不要な旧writerとTunnelを停止します。旧DB・volume・バックアップの削除はこの移行で自動実行しません。最後にAWS構成をread-backし、draw.io図を設計図から実配備図へ更新します。

## 完了判定

移行完了は、AWS上の実runtime、移送データと認証、公開DNS、実際のLean回答、既存機能、復旧と監視を確認した状態です。手順書、Terraform test、図、準備用CLIだけが完成しても移行完了とはしません。残った作業はこの表に残し、未実行・未配備を明記します。

## 基盤適用の記録

2026年10月30日23時24分ごろ、Mac miniから練習用バックアップの転送が完了しました。private S3の7 objectを確認し、移送manifestに指定した6ファイルをVersionIdで固定して取得しました。S3のAES256暗号化、サイズ、SHA256 checksumとmetadata、ローカルのSHA256を照合しました。dumpは4,353,802 bytesで、SHA256は`8ce5ae7517b1c843117d99a67be118eb055dd7e200d8aca69145c69859a38539`です。DBや旧サービスの停止・変更は行っていません。

23時36分、既存の配備manifest・DER署名・履歴registryを、APIの正式な`verify_predecessor`で検証しました。AWS KMS Verify、独立して固定した公開鍵SPKIとローカルP-256署名検証が通過しました。配備manifestのSHA256は`6718ad3f1d8fcc17cc463759bd7673f2438db3624a65c84bd7696ab2824921c3`です。この結果は履歴資料の署名検証であり、最終移送の受理や稼働中DBの書き込み停止を証明するものではありません。取得・検証receiptとraw資料はignoredの保護領域に保存しています。

2026年10月30日、初回planは新規74件、既存資源の更新・削除0件でした。Auroraなどの作成後、ALBのログ保存先の権限チェックで一部適用が失敗しました。ALB自体はactiveで同じARNと確認できたため、Terraformの交換マークだけを解除して保持しました。

ログ配送のSourceArn条件をAWS公式の同一リージョン・アカウント範囲へ修正しました。修復planはlistener新規2件、作成済みALBと専用ログbucketポリシーの更新2件、削除・交換0件です。適用後、access_logs=trueと、ELBAccessLogTestFileの実保存・AES256を確認しました。初回planや失敗したplanを再利用していません。

Aurora 16.15はavailable、暗号化・削除保護・7日バックアップ・0.5〜2 ACUと読み戻しました。VPCの8 subnetはいずれもpublic IP自動付与なしで、DBのroute tableにdefault routeはありません。private computeからDBへの許可もありません。続くoperator用planで未使用legacy host SGからのDB許可を除去し、実際の5432 ingressをcontrol SGだけに限定しました。

東京のStandard On-Demand上限は16 vCPUでした。大会用xlarge 4台とmediumには18 vCPU、最大8台の切り替え中併存には34 vCPUが必要なため、40 vCPUへの増枠を申請しました。申請直後はCASE_OPENEDでしたが、10月31日に実際のService Quotasから40 vCPUへ増えたことを読み戻しました。上限の確保は、計算poolの配備や大会の負荷試験の完了には含めません。

private controlのoperator用planは新規5件、DB SG更新1件、削除・交換0件で適用しました。mediumは公開IPなし、暗号化40GiB gp3、IMDSv2必須・hop1、SSM通信5操作だけのinstance profileです。SSM実行でcloud-init完了、アプリ未起動・ALB未登録marker、PG16.15 clientを確認しました。

compute用planは新規5件、既存資源の更新・削除・交換0件で適用しました。largeはprivate compute subnetに置き、暗号化80GiB gp3、IMDSv2必須・hop1、SSM通信5操作だけのinstance profileです。実機のcloud-init完了、Docker linux/x86_64と2 CPU、AMD EPYC 9R45、アプリとbenchmarkが未実施であるmarkerをSSMで確認しました。

実Auroraへの読み取り試験は、SSM転送とAWS公式CA、元のRDS hostnameを使うverify-fullで成功しました。続いて正式なAPIのtyped transportとAurora・空DB検査でも成功しました。TLS1.3、palsadminは非SUPERUSERでCREATEROLE/CREATEDBあり、UTF8/en_US.UTF-8/provider c、collationの記録値と実値は2.26-59.amzn2でした。この初期試験の時点では、localeの互換性、role mappingの実能力、実復元、署名付き受理と全機能は未確認でした。後続の分離clusterでの結果は、上記の実行状況と[検証記録](aws-migration-verification-2026-10-31.md)へ記載しています。

Lean childのファイル隔離は、verifierのTLS秘密鍵へ到達する可能性がある規則を修正しました。実鍵を使わないLinux canary、実Lean・Mathlib、Elan/nativeとsymlink拒否の試験が通過し、独立したLinux再実行13件も通過しました。[agent PR #22](https://github.com/AtsushiHosaka/pals-agent/pull/22)はdraftで、本番verifierサービスの起動はまだです。

その後、同じ修正を含むx86 imageをbuildして非公開ECRへpushし、large自身のECR権限で取得しました。アプリと資格情報を渡さない隔離コンテナで48件の実Lean測定に成功しました。実cgroupと隔離検査、標本・cache状態・メモリの限界は[測定記録](aws-native-lean-benchmark-2026-10-30.md)に残しています。HTTP/mTLSの本番runtime起動は別途確認します。

IAM分離のplanは新規11件、既存2 hostのinstance profile更新だけで適用しました。4 roleのtrustと全inline policyを読み戻し、host ID、非公開IP、parameter読み取り0件を照合しました。controlからAPI、computeからworkerの専用STS sessionを実際に発行し、各5分の更新timer起動を確認しました。これは資格情報更新の確認であり、アプリやpoolの稼働確認ではありません。

続いて両hostのtimerが実際に短期資格情報を更新したことを確認しました。API imageは固定digestで取得し、networkなし・read-only root・権限削除の一時コンテナで、別々にread-only mountしたpolicyと資格情報を既存readerが受理しました。アプリは起動しておらず、DB接続や生成処理の成功を示す試験ではありません。

private computeの初回起動helperは、AL2023のDocker25に合わせたimage検査、actorからhostへのINPUT通信制限、起動期限後にもSIGTERMを送る処理を修正しました。独立レビューで追加の指摘はなく、rootによる再実行も171件通過しました。これらはコードと隔離した試験の結果で、実機のfirewall・mTLS・queue drainは未検証です。起動helperの本番実行も行っていません。

料金通知のplanは予算1件の更新、新規・削除0件でした。既存3通知が保持され、予算額と2通知の追加以外に差分がないことを保存済みplanから独立に照合して適用しました。適用後も予算額・全通知・全宛先・自動停止actionなしをAWSから確認しました。Terraform validateと既存production試験13件は通過しています。
