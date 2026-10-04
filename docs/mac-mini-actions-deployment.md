# Mac miniの自動デプロイを有効にする手順

更新日: 2026年10月4日。対象はPALSの運用者。最初は「有効化の順序」まで読み、設定や更新プログラムを実装するときに後半の契約を参照する。

## GitHub側の実行入口を追加した。実機の更新は未接続

親リポジトリの `.github/workflows/deploy-macmini.yml` が、mainへのpushと手動実行を受け付ける。親のコミットと、そのコミットが参照するsubmoduleを取得し、専用のMac mini runnerで `pals-scripts/deploy-macmini.py` を実行する。

runnerは、GitHub Actionsから仕事を受け取る実行プログラム。親 `AtsushiHosaka/pals` はprivate。2026年10月4日、ユーザーがMiniの `~/actions-runner-pals` にARM64 runnerを登録し、LaunchAgentとして起動した。GitHub側でも `pals-macmini` のonlineと、`self-hosted`・`macOS`・`ARM64`・`pals-macmini` の4ラベルを確認した。

登録前のGitHub側検査は [初回Actions run](https://github.com/AtsushiHosaka/pals/actions/runs/37180834429) で成功した。Environment・デプロイ設定・private submodule用のsecretは未登録であり、本番更新はまだ実行しない。

既存のMac用DB初期化は、空のDBへの初回適用と同一署名の再実行に限定される。通常のAPI・Web・workerを新しいコミットへ継続更新するプログラムは、まだこの入口に接続されていない。初回用の `sign-and-apply-production-release.py` や `--apply-mac` を、自動更新の代わりに呼ばない。

関連する制約は [Mac PostgreSQL admission](../specs/domainless-production-bootstrap/mac-postgres-admission.md) と [10月4日の公開準備](macbook-publication-preparation-2026-10-04.md) にある。Miniの「検証 PALS本番起動」チャットでは、本番の起動・復元試験が進行中だった。設定を追加する前に、同チャットの最新状況を確認する。

この文書はユーザーの自動デプロイ依頼に基づくWORKING契約であり、既存の署名・DB制約を変更しない。今回追加した入口の検証と、実KMS・migration・稼働サービスの更新検証は別に記録する。

## 有効化はrunner、手動検査、手動更新、push連動の順に行う

1. Miniの既存本番検証を終え、既存DB・volume・サービスの識別情報を確認する。更新プログラムは次節の契約に従って実装・実機検証する。
2. 親repoの Settings → Actions → Runners から、Mini用のrunnerを登録する。専用ラベルを `pals-macmini` にする。runnerの作業ディレクトリを、本番ソース・秘密設定・DB volumeと分ける。
3. repository variable `MACMINI_RUNNER_READY=true` を設定し、手動実行のmodeを `runner-check` にする。これはcheckoutやsecretを使わず、MiniのOS・ARM64・Git・Python・Docker接続を読み取り確認する。
4. private submoduleを読む資格情報を `PALS_SUBMODULES_READ_TOKEN` というrepository secretに登録する。親と必要なsubmoduleのContents readに絞る。親repoの `GITHUB_TOKEN` だけでは別private repoを取得できない。
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

自動更新を止めるときは `MACMINI_AUTO_DEPLOY=false` にする。現在進行中の更新はキャンセルしない。同時実行を防ぐGitHubの `concurrency` とMiniのファイルロックを併用し、ロックファイル自体は削除しない。

## ホストの更新プログラムが署名とサービス切替を担当する

`deploy-macmini.py` は、設定で指定した実行ファイルのSHA-256を確認してから、次の引数を渡す。シェルのコマンド文字列は受け付けない。

```text
<controller> --source-dir <checkout> --parent-sha <40文字のSHA> --receipt-file <結果JSONの絶対パス>
```

更新プログラムは、指定ソースからAPI・Web・workerをビルドし、既存のホスト・DB・volumeに結び付いた新しいリリースを実KMSで署名する。更新admissionとmigrationを適用し、処理中ジョブを完了させてから、既存の論理サービスを切り替える。既存の本番用デプロイロックとも連携する。初期化用コマンドの再利用、DB/volumeの削除、localモードへの変更、署名検証の省略は含めない。

この通常更新用プログラムは未接続で、実機検証も未実施。CIMD専用のAPI child配備は別の契約であり、3サービスの継続更新を代用しない。現在の初回署名スクリプトを設定に指定しても、この更新契約を満たさない。

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
| `docker_context` | 現在の本番Docker context。Miniの保存済み記録では `desktop-linux` |
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
