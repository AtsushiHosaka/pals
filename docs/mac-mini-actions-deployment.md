# Mac miniの自動デプロイを有効にする手順

更新日: 2026年10月5日。対象はPALSの運用者。最初は「有効化の順序」まで読み、設定や更新プログラムを実装するときに後半の契約を参照する。

## 手動更新は成功。常時運転用の機械認証を準備中

親リポジトリの `.github/workflows/deploy-macmini.yml` が、mainへのpushと手動実行を受け付ける。親のコミットと、そのコミットが参照するsubmoduleを取得し、専用のMac mini runnerで `pals-scripts/deploy-macmini.py` を実行する。

runnerは、GitHub Actionsから仕事を受け取る実行プログラム。親 `AtsushiHosaka/pals` はprivate。2026年10月4日、ユーザーがMiniの `~/actions-runner-pals` にARM64 runnerを登録し、LaunchAgentとして起動した。GitHub側でも `pals-macmini` のonlineと、`self-hosted`・`macOS`・`ARM64`・`pals-macmini` の4ラベルを確認した。

登録前のGitHub側検査は [初回Actions run](https://github.com/AtsushiHosaka/pals/actions/runs/37180834429) で成功した。その後、Environment `macmini` をmain限定で作成し、`MACMINI_CHECKOUT_AUTH=host-gh` と、ホスト設定の絶対パス `MACMINI_DEPLOY_CONFIG` を登録した。新しいprivate submodule用secretは作成していない。

登録後、`MACMINI_RUNNER_READY=true` を設定した。[Miniでのrunner-check](https://github.com/AtsushiHosaka/pals/actions/runs/37186033515) は成功し、`Darwin arm64`、Apple Git 2.54.0、Python 3.9.6、Docker `linux aarch64` を確認した。当時、本番更新jobはskipで、`MACMINI_DEPLOY_READY` と `MACMINI_AUTO_DEPLOY` は未設定だった。

ユーザーは自動デプロイのONを許可済み。元のworkspaceでは、途中で止まったcloneがindex未作成・作業ファイルなしの状態で、Gitから全ファイル削除と表示されていた。元の領域を保持し、専用の固定checkout `macmini-deploy` だけを使う。初期化の再開は、Gitのindex lockと既存indexを置き換えない作成処理を使い、作業ファイルを強制上書きしない。実Git・競合・認証helper継承・プロセス終了・出力秘匿を含む30テストが成功した。

Miniの手動接続では保存済みgh認証を使えたが、[実runnerでの診断](https://github.com/AtsushiHosaka/pals/actions/runs/37204088395) ではloginとprivate repository accessがともに利用不可だった。runnerのLaunchAgentを保全して `SessionCreate=false` に変更し、idle状態で再起動した。[変更後のcheckout-check](https://github.com/AtsushiHosaka/pals/actions/runs/37205359405) は成功し、保存済み認証と親・全submoduleのSHA一致を実runnerで確認できた。認証情報の抽出や、新しいGitHub secretの作成は行っていない。

MiniはOrbStackへ移行し、回答2件・利用量10行を含む74テーブル、権限、DB識別子、volume・host marker、署名済みimageの一致と公開復帰を確認した。[移行後のrunner-check](https://github.com/AtsushiHosaka/pals/actions/runs/37203849915) も成功した。Actionsは `/Users/hosakaatsushi/.orbstack/bin/docker` とcontext `orbstack` を使い、通常更新controllerもこのcontextへ接続している。

[実runnerのpreflight](https://github.com/AtsushiHosaka/pals/actions/runs/37205576721) は成功した。これはソース・ホスト設定・Docker接続の検査で、実更新は行わない。通常更新用の3イメージはMiniでbuild済み。controllerの終了時処理と、途中で止まったコンテナ作成の再開処理は独立レビュー後に修正した。

2026年10月4日14:01 UTC、Miniの既存 `pals-prod-member` SSOが期限切れで、資格情報brokerの更新とworkerが停止していることを確認した。本人の再ログイン後、同じAWS identityを確認し、14:24 UTCに既存brokerと旧workerのreadyを確認した。workerのCID・imageは同一で、署名やDB更新は行っていない。現在の認証方式では、SSO失効時に無人での資格情報更新と配備が停止する。

controllerの終了・復旧処理は修正済み。実subprocessでtimeout・SIGTERM・親のSIGKILLを検証し、子孫終了までロックを保持できた。実OrbStackの隔離試験では、同じCIDへの不足networkの補完と、更新結果がunknown・other・観測失敗の場合の公開edge停止を確認した。余分な権限やホスト共有を拒否する試験も成功した。workerの独立policy directoryを読み取り専用で渡し、新workerの認証チェックも成功した。[親15f493fのpreflight](https://github.com/AtsushiHosaka/pals/actions/runs/37209518920) も成功した。

稼働API用roleはKMSのGetPublicKeyを許可していないため、配備専用のnative処理には既存release-signerの900秒STS sessionを使う。認証情報はメモリと専用プロセスの環境変数で扱い、保存・ログ出力・稼働コンテナへの受け渡しをしない。IAMは変更していない。設置controllerのSHA256は `8034a5349376cf7eeed1b74aeebae3e20c94e5000a5a998521e3982a1908807a`、authorityは `99d14e0776db294006cf042f8e0c5718d49b172e6fc32114723d7a3e111b0053`。関連32テストと、既存KMSでの公開鍵取得・旧署名検証が成功した。

[手動の実更新](https://github.com/AtsushiHosaka/pals/actions/runs/37211520009) は親 `fca2dde` の取得を通過したが、配備用Pythonの起動時に停止した。macOSのTCC記録で、同じPython PIDがDocumentsFolderの承認待ちになっていることを確認した。責任主体はrunner起動元の `node`。Miniの画面でも「node」から「書類」へのアクセス許可が表示されており、本人操作を依頼した。検証を中止し、`MACMINI_DEPLOY_READY=false` に戻した。署名・DB更新・サービス切替には未到達だった。

2026年10月5日、本人から「書類」へのアクセスを許可したとの返信を受領した。00:04 UTCの確認では、夜間に既存SSOが再び失効し、brokerの3用途すべてが未ready、旧workerは同じCID・imageのまま停止していた。API・Web・公開edgeは稼働し、DBの現行admissionはsequence1、pending更新はなかった。本人へ同じprofileでの再ログインを依頼した。[親 `cf823eb` の実runner preflight](https://github.com/AtsushiHosaka/pals/actions/runs/37246137103) は成功したが、この検査はnative controllerを起動しない。この時点では `MACMINI_DEPLOY_READY=false`、`MACMINI_AUTO_DEPLOY` は未設定だった。

本人の再ログイン後、同じAWS identityを確認し、旧workerを同じCID・imageで復帰した。`MACMINI_DEPLOY_READY=true` にして再実行した [手動デプロイ](https://github.com/AtsushiHosaka/pals/actions/runs/37247403226) は成功した。実runnerのnative controllerが起動し、親 `ffb84277ddd306092570965260793b059dcd9545` の3image build、実KMS署名、通常v2更新を通過した。MiniではDBのsequence2、3サービスのRunning、pendingなし、同じSHAの `current.json` がhealthyであることを確認した。09:35 JSTの独立照合では、署名admission全18項目、source7・image3、旧73テーブルの全行、旧権限1032項目、回答2件・利用量10行の維持を確認した。worker readyと公開応答200・200・匿名401も通過した。

ユーザーは、定期的な人の再ログインに依存する構成を常時運用の解決として認めていない。`MACMINI_AUTO_DEPLOY` は未設定を維持し、[Mini専用の機械認証](mac-mini-machine-auth.md)を導入する。CA・秘密鍵の永続保存は自動承認レビューが一度拒否したため、保管先・4用途の認証範囲・更新方法を提示した。本人から「設置して良い」と明示許可を受領し、設置と実機検証を進めている。自動デプロイをONにする許可も受領済み。

既存のMac用DB初期化は、空のDBへの初回適用と同一署名の再実行に限定される。通常のAPI・Web・workerを新しいコミットへ継続更新するプログラムは、ホストの入口へ接続し、実runnerからの手動配備が成功した。常時運転用の機械認証とpush連動の検証を残している。初回用の `sign-and-apply-production-release.py` や `--apply-mac` を、自動更新の代わりに呼ばない。

関連する制約は [Mac PostgreSQL admission](../specs/domainless-production-bootstrap/mac-postgres-admission.md) と [10月4日の公開準備](macbook-publication-preparation-2026-10-04.md) にある。Miniの「検証 PALS本番起動」チャットでは、本番の起動・復元試験が進行中だった。設定を追加する前に、同チャットの最新状況を確認する。

この文書はユーザーの自動デプロイ依頼に基づくWORKING契約であり、既存の署名・DB制約を変更しない。今回追加した入口の検証と、実KMS・migration・稼働サービスの更新検証は別に記録する。

## 有効化はrunner、手動検査、手動更新、push連動の順に行う

1. Miniの既存本番検証を終え、既存DB・volume・サービスの識別情報を確認する。更新プログラムは次節の契約に従って実装・実機検証する。
2. 親repoの Settings → Actions → Runners から、Mini用のrunnerを登録する。専用ラベルを `pals-macmini` にする。runnerの作業ディレクトリを、本番ソース・秘密設定・DB volumeと分ける。
3. repository variable `MACMINI_RUNNER_READY=true` を設定し、手動実行のmodeを `runner-check` にする。これはcheckoutやsecretを使わず、MiniのOS・ARM64・Git・Python・Docker接続を読み取り確認する。
4. private submoduleの取得方法を選ぶ。Miniの既存gh認証を使う場合は `MACMINI_CHECKOUT_AUTH=host-gh` を設定し、手動の `checkout-check` で取得と親・submoduleのSHA一致を確認する。専用tokenを使う場合は `repository-token` とし、親と必要なsubmoduleのContents readに絞った `PALS_SUBMODULES_READ_TOKEN` をsecretに登録する。未設定時の方式は `repository-token`。親repoの `GITHUB_TOKEN` だけでは別private repoを取得できない。
5. Miniに保護されたホスト設定と更新プログラムを設置する。repository variable `MACMINI_DEPLOY_CONFIG` に、設定ファイルの絶対パスを入れる。Environment `macmini` の許可ブランチはmainに限定する。
6. Actionsからmainを選び、手動実行のmodeを `preflight` にする。これはホスト設定・ソース・Docker・ロックを検査し、サービスを更新しない。
7. 更新プログラムの実機検証後に `MACMINI_DEPLOY_READY=true` を設定し、modeを `deploy` にして手動実行する。GitHubの成功だけで完了とせず、実認証・質問・保存・利用量・処理中ジョブの扱いも確認する。
8. 手動更新が合格したら `MACMINI_AUTO_DEPLOY=true` を設定する。以後は親mainへのpushが起点になる。

各実装repoを先にpushし、その後、親のsubmodule参照を更新してpushする。各submoduleのmainを個別に追いかけず、親のコミットで反映する組み合わせを固定する。

このworkflowのGitHub側検査は、親の秘密情報・公開repo境界・実行入口のテストと構文を対象にする。各実装repoのアプリテストや本番受入試験の合格を、この検査で代用しない。

| Repository variable | 用途 |
| --- | --- |
| `MACMINI_RUNNER_READY` | `true`のときだけMiniへ仕事を送る |
| `MACMINI_DEPLOY_READY` | `true`のときだけ更新モードを許可する |
| `MACMINI_AUTO_DEPLOY` | `true`のときだけpushから更新を実行する |
| `MACMINI_DEPLOY_CONFIG` | Mini上の保護された設定ファイルの絶対パス |
| `MACMINI_CHECKOUT_AUTH` | `host-gh` または `repository-token`。取得資格情報を明示する |

`host-gh` は、新たなtokenをGitHubへ保存せず、Miniの既存gh認証をGitの内部通信で使う。ユーザーのglobal Git設定を変更せず、runner専用workspace内だけを更新する。既存認証の失効・active accountの変更・runnerからのKeychainアクセスに依存する。取得に失敗しても、別方式へ自動で切り替えない。

自動更新を止めるときは `MACMINI_AUTO_DEPLOY=false` にする。現在進行中の更新はキャンセルしない。同時実行を防ぐGitHubの `concurrency` とMiniのファイルロックを併用し、ロックファイル自体は削除しない。

## ホストの更新プログラムが署名とサービス切替を担当する

`deploy-macmini.py` は、設定で指定した実行ファイルのSHA-256を確認してから、次の引数を渡す。シェルのコマンド文字列は受け付けない。

```text
<controller> --source-dir <checkout> --parent-sha <40文字のSHA> --receipt-file <結果JSONの絶対パス>
```

更新プログラムは、指定ソースからAPI・Web・workerをビルドし、既存のホスト・DB・volumeに結び付いた新しいリリースを実KMSで署名する。通常コード更新のv1はDB構造と既存のartifact registryを維持する。処理中ジョブを完了させ、API・workerなどの書き込み元を停止してから、署名付きの更新admissionを追加し、既存の論理サービスを切り替える。初期化用コマンドの再利用、DB/volumeの削除、localモードへの変更、署名検証の省略は含めない。

DB移行を伴うv2は、旧署名に一致する23段階のregistryを保持し、`project-materials` と `project-materials-ocr` の追加だけを許可する。追加するmanifest・SQLのdigestを新署名に固定し、旧schemaの一致・処理の完了・権限を検査してから、DDLと更新admissionを同じトランザクションで適用する。既存回答の書き換えや任意migrationの実行は許可しない。CIMD childが存在するDBや、新しいDB・volumeへの移行はこの契約で扱わない。

API側の通常更新とDB移行は [pals-api `ddb0c8d`](https://github.com/AtsushiHosaka/pals-api/commit/ddb0c8d9d8f24bcfb8a67184001bdef76faa1865) でpush済み。最新ソースのv1と、旧23段階から25段階へのv2を隔離した実PostgreSQLで検証し、旧データ・ACLの維持、DDLとadmissionの一括rollback、commit後の通信失敗の再観測を確認した。関連unit 230件も成功した。隔離試験の署名は実EC鍵を使うローカル検証。10月5日の手動デプロイでは、Miniの実KMSと3サービスの切替も成功した。CIMD専用のAPI child配備や初回署名スクリプトは、3サービスの継続更新を代用しない。

[継続更新の追加試験 `c616968`](https://github.com/AtsushiHosaka/pals-api/commit/c616968bca527ef6ca0b35e58c0a4e6808b5f5be) では、実23段階からv2 seq2へ進み、さらに新しい親・全ソース・3イメージを持つv1 seq3へ更新できた。同ファイルの19試験が成功し、旧データ・ACL、最終admissionの全18項目一致、v1でDDLがないことを確認した。Docker通信はfixtureを使い、DBとEC署名は実処理で検証している。

controllerは既存の本番用ロックを更新・復旧の全期間保持する。APIの更新・再観測CLIには別の専用ロックを渡す。同じinodeを親と子が別々に取得して待ち合う構成にしない。commit結果が不明な場合は、署名と現行admissionを読み取りで照合する。候補が現行なら候補サービスで復旧し、旧リリースが現行なら旧サービスを再開できる。どちらとも確認できなければ公開を停止したまま運用者へ知らせる。DBのadmissionを旧値へ戻す処理は行わない。

runnerの取得ソースは一時的な作業領域として扱う。稼働コンテナからbind mountしない。必要な資産はイメージまたはホストの管理領域に収録し、次回checkoutで稼働サービスが変わらないようにする。

ビルドする各イメージに `org.opencontainers.image.revision` を所有submoduleのSHA、`site.pals.parent-sha` を親SHAとして付ける。更新結果には実際のDocker image IDを記録する。入口は既存コンテナのImageとイメージラベルを独立して照合する。

更新プログラムは同期的に終了する。サービス起動はDockerの既存サービスを操作し、ホストの子プロセスを残したり切り離したりしない。時間切れ・キャンセル・残存子プロセスがあれば、入口はそのプロセスグループを停止して失敗とする。ログはホストの保護されたstate directoryに残し、GitHubの出力には流さない。runnerのtokenや実行環境のAWS資格情報も渡さない。

更新に必要な署名資格情報の供給・更新、DB互換性に応じた復旧は、ホストの更新プログラムが担当する。入口が後段のイメージ照合やHTTP検査で失敗した場合、更新済みサービスが残る可能性がある。失敗した入口は成功記録を更新せず、DB互換性を無視した自動rollbackもしない。運用者はprivate host logと現行admissionを確認して復旧する。

## ホスト設定は取得ソースの外に置く

設定はJSONで、次のキーをすべて指定する。秘密値は含めない。ファイルはrootまたは実行ユーザー所有、単一link、mode `0600` とし、symlinkを含まない正規化済み絶対パスで指定する。state directoryは同様に所有者を限定し、mode `0700` にする。

| キー | 値・検査 |
| --- | --- |
| `schema_version` | `pals.macmini-deploy-config.v1` |
| `state_dir` | 既存の保護された状態保存ディレクトリ。checkoutの外 |
| `controller` | 実機検証した更新用実行ファイル。checkoutの外 |
| `controller_sha256` | その実行ファイルの64文字SHA-256 |
| `docker_context` | 現在の本番Docker context。移行後のMiniは `orbstack` |
| `containers` | `api`、`web`、`worker`それぞれの既存コンテナ名。3つは別名 |
| `database_identity` | 独立して確認した `database_system_identifier`、`database_volume_id`、`host_binding_sha256` |
| `health_urls` | `api`と`web`の明示的なHTTP loopback URL。APIは `/health` |
| `controller_timeout_seconds` | 30〜3000秒の整数 |
| `health_timeout_seconds` | 1〜300秒の整数 |

Miniの保存済み本番起動ではAPIが `http://127.0.0.1:8000/health`、Webが `http://127.0.0.1:3000/` だった。設定時に現行値を再確認する。公開edgeの計画値13000/18000を、稼働サービスの値として転記しない。HTTP検査はproxyを使わず、redirectを追わない。

設定ファイルだけでは更新プログラムの正しさを証明できない。SHAの照合範囲は実行ファイル本体であり、その依存コード・署名・DB更新・復旧の実機証拠も設置時に確認する。

workerのAWS roleは、公開パッケージへ本番ARNを埋め込まず、独立したホスト設定で固定する。更新用イメージには `/run/credentials-policy/worker-role.json` をread-only mountする。このJSONは `version: 1`、`role_arn`、`session_name: pals-mini-worker` を含む。role ARNは既存IAM設定から確認する。資格情報brokerが更新する `/run/credentials/worker` とは別の保護されたディレクトリに置き、期待値をbrokerのstateから作らない。設定が未設置・不一致なら、workerは資格情報を出力せず起動を拒否する。

## 結果JSONは指定コミットと既存DBに一致させる

更新プログラムは引数で渡された空のmode `0600` ファイルへ、次のキーだけを含むJSONを書く。atomic replaceする場合もファイルの所有者・mode・単一linkを維持する。

| キー | 値・検査 |
| --- | --- |
| `schema_version` | `pals.macmini-deploy-result.v1` |
| `status` | `applied` |
| `parent_sha` | 指定された親SHA |
| `source_commits` | `pals`と6 submoduleの実際のSHA。取得ソースとの完全一致 |
| `manifest_sha256` | 実KMSで検証した新しい署名済みmanifestの64文字SHA-256 |
| `images` | `api`、`web`、`worker`の実際の `sha256:<64文字>` Docker image ID |
| `database_identity` | ホスト設定と同じ既存DB・volume・hostの識別情報 |

入口は結果JSON、稼働コンテナ、イメージラベル、API/Webの200応答を確認し、コンテナを再照合してから `state_dir/current.json` を更新する。この成功記録のstatusは `healthy`。`preflight`の結果は `deployed: false` で、成功記録を更新しない。

API/WebのHTTP応答や結果JSONだけでは、実認証・生成・保存・workerの正常処理を証明できない。初回と更新プログラム変更時には、実サービスの受入試験を別途実行する。

## AWSへ移るときは実行先を追加する

Mac固有の設定・ロック・更新プログラムは `deploy-macmini` に閉じ込める。AWSへ移る段階で `deploy-aws.yml` を追加し、親コミットとsubmoduleでリリースを固定する方針、GitHub側の検査を再利用する。AWSの更新手順やIAMは、採用する実行基盤に合わせて実装する。

未解決の実機設定は、Miniの「検証 PALS本番起動」チャットで確認する。ホスト名は `hosakaatsushinoMac-mini.local`、ユーザー名は `hosakaatsushi`。このMacBookからのSSHは、sandbox外でも名前解決に失敗した。ユーザーの既存Parsec接続画面は確認できたため、runnerの登録はParsec経由で行える。デプロイ時の通信はMiniからGitHubへ接続するので、SSHを公開する必要はない。

公式資料: [runnerの通信要件](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)、[self-hosted runnerの安全性](https://docs.github.com/en/actions/reference/security/secure-use)、[checkoutの認証](https://github.com/actions/checkout)、[同時デプロイの制御](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments)。
