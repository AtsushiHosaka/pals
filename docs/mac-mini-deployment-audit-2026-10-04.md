# Mac miniのビルド・DB検証は完了。公開には実サービスの確認が必要

2026年10月4日、Mac mini関連の過去チャット、MacBook上のソース、GitHubのmain、公開DNSを照合した。MiniではARM64のv4 APIビルドとPostgreSQL 16の13テストが成功している。本番の認証・リリース署名・質問送信・外部公開は未完了だった。今回、検証済みv4を回収してAPIとworkerへ統合し、既存のMacBook側の変更も保持した。次は同期したコミットをMiniへ渡し、本番接続を確認する。

U-22通過は今回のユーザー申告による。審査通過と本番環境の稼働確認は別に扱う。

## 過去チャットでは、ビルドとDB検証まで進んでいた

| チャット名 | 確認できた到達点 | 残っていた作業 |
| --- | --- | --- |
| Lightsailの費用を試算 | Mac miniとCloudflare Tunnelを使う方針、Cloudflareへのドメイン追加・既存CNAME移行 | DNS委任の変更完了、Web/API公開 |
| Prepare Mac mini uptime | リモート運用の制約を整理。FileVault有効を観測 | 再起動後の無人復旧 |
| Build PALS on Mac mini | M1・16GB、電源設定、ARM環境を確認。後任へ移管 | 初期のGit clone・ビルド確認は後任に引継ぎ |
| Deploy PALS through Tunnel | 実Cognito、SQS/DLQ、非公開S3、署名用KMS、用途別IAMロールを作成・設定確認 | 実資格情報の供給、Miniの本番接続、Tunnel・DNS公開 |
| Prepare PALS local demo | MacBookのローカルデモを維持。公開用ソースとの差分を確認 | Mini修正の回収とMacBookへの統合 |
| Verify PALS runtime code | v4までのDB起動修正、単体検証、ソースアーカイブ作成 | 主リポジトリへの統合、別作業の初回パスワードUI修正 |
| Diagnose Mini build stall | Docker Desktopでv4 APIビルド成功。実PG16の13件成功。ソース・イメージ照合成功 | 本番KMS、実認証、実質問送信、公開ブラウザ確認 |
| 確認 Mac mini常時稼働 | 10月3日23:43〜23:44 JST、画面なしでシェル応答。AC時のsleep=0・displaysleep=0・autorestart=1、電源予約なし | コンテナとTunnelを含む再起動復旧試験 |

古いOrbStackの障害記録だけを読むと、ビルドが止まったままに見える。後の記録ではDocker DesktopでビルドとDB試験が成功しているため、OrbStackの復旧を公開の必須作業としてやり直す根拠はない。現在のコンテナ稼働状態は今回照会していない。

10月4日の読み取り依頼に対し、Mini担当は589ソースファイルとAPIイメージ収録対象294ファイルの一致を再確認した。PG16の保存済み結果は11件と2件、計13件が成功し、失敗・エラー・skipは0件だった。これは実PG16の検証用DBでの結果であり、本番KMSや外部サービスを含む運用環境の合格を意味しない。

## 公開URLはrootとAPIの契約に合わせる

10月2日の確定した公開先は、`https://palschat.site`と`https://api.palschat.site`。Mac側の接続先は、それぞれ`127.0.0.1:13000`と`127.0.0.1:18000`だった。Cognitoのcallbackはrootサイトの`/auth/callback`を使う。9月30日の[手順書](mac-mini-public-hosting-runbook.md)にある`app.palschat.site`は旧案なので、そのまま設定を転記しない。

既存Tunnel名は`mac-mini-m1-2020`。新しいTunnelを重複して作る必要はない。PALSの進捗通知はSSEを使うため、SSE非対応のQuick Tunnelは使えない。[Cloudflare公式の制約](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

10月4日のDNS照会では、`palschat.site`の委任先はRoute 53の4件だった。rootのAレコード応答はなく、`api`と`app`はNXDOMAINだった。公開切り替え完了の証拠はない。Cloudflare管理画面の現在の状態は今回確認していない。

## 公開までの順序

1. **Miniを同期したコミットへ揃える。** reviewed v4の回収と主リポジトリへの統合は今回実施した。Miniでは既存変更を保護して差分を照合し、親と各submoduleを同期版に揃える。同期後のイメージを再ビルドし、公開設定SHA検査とPG16試験を再実行する。
2. 本番設定を仕上げる。既存のOpenAIキーとTunnelトークンをMiniの保護された入力経路へ設置する。APIとworkerの共有秘密、6種のDB資格情報、用途別AWS資格情報の更新を設定する。秘密値はチャットやGitに渡さない。
3. 実機の識別情報を使ってリリースに署名し、本番DBを起動する。ソース・イメージ・ホスト・volume・DBの識別情報を揃え、実KMSの署名で起動を検証する。検証用の署名や古いmanifestを流用しない。
4. 通常ユーザーの初回認証と質問送信を確認する。実Cognitoでログインし、質問送信、AI生成、独立QA、利用量の記録、保存、再読込、他ユーザーへのアクセス拒否を確かめる。非公開のloopback接続で先に確認できる。
5. originの合格後、既存Tunnelを接続してroot/APIルートとDNS委任を切り替える。外部回線でHTTPS、認証、SSE、結果の保持を確認する。継続運用には、外部バックアップの復元試験、再起動復旧、死活・容量・キュー滞留の監視も必要になる。

Miniの停止時点では、最後に追加した公開設定SHA検査の再実行も残っていた。AWS資源はすでに作成済みなので、EC2・Aurora向けTerraformをそのままapplyしたり、CognitoやS3を再作成したりしない。初回CloudFormationはROLLBACK_COMPLETEで、既存資源を安全に管理へ戻す作業が別途残っている。

## v4の修正を回収し、既存実装と統合した

Miniのreviewed v4アーカイブは`pals-app-source-reviewed-v4-20261002.tar.gz`、SHA256は`7506436f1c31aa79a6769768b07eebe7efe6ab39e49ffa5d12e911b57988232e`。APIイメージの保存済みIDは`sha256:832fd697d01f2f0402fafd8b1328af09037378db25bc165f6fd4974b3edf75e0`。今回、取得したアーカイブのSHAを照合した。主リポジトリには独自の追加実装もあるため、全体をv4そのものと同一とは扱わない。

MacBook上に残るv2の[引継ぎ](</Users/atsushi/Documents/Codex/2026-10-02/task/production-fix-v2/08時引き継ぎ.md>)と主リポジトリを比較すると、433件の自然言語カタログ、23段階のmigration registry、初回Recipe移行の限定権限などが未統合だった。v4にはreaderのschema USAGE、OIDによる権限確認、DB接続URLの正規化も含まれる。実v1のアーカイブと現在の対象ファイルが一致することを確認してから、v4の差分を適用した。selectorのpublic USAGEは付与せず、OIDで権限を確認する契約を保った。workerの資格情報更新と起動スクリプトも取り込んだ。

Webのパスワード再設定は実装済みだが、Cognitoの`NEW_PASSWORD_REQUIRED`は[AuthProvider](../pals-webfront/components/AuthProvider.tsx)でエラーとして扱われている。招待ユーザーの初回パスワード変更には別の対応が必要。Mini側の未完成のUI修正を、検証済みv4と混ぜない。

## GitHubへ最新実装を同期した

GitHubのmainを直接照会し、次の2リポジトリの既存コミットをfast-forwardでpushした。push後のGitHub SHAも照合済み。その後、明示した候補リストに沿って未コミットの実装・テスト・仕様をcommitし、通常のpushで反映した。

| リポジトリ | 今回の同期 | GitHub main |
| --- | --- | --- |
| pals-infra | 既存4コミットと未コミットの14ファイルを反映、SHA照合済み | `063dfece859b05895a33c1938579cc0bf20fb3b3` |
| pals-observability | 既存2コミットと依存lockを反映、SHA照合済み | `fa121a88d5cd04c39a097a9b3e8bc80e515fb1e8` |
| 親pals | 仕様・補助スクリプト・本報告とsubmodule参照を同期 | 本報告を含む同期コミット |
| pals-api | 最新実装とv4をcommit・push、SHA照合済み | `c0062c38eb6bef3b470cb827a2ded869700fd051` |
| pals-webfront | 最新UI・認証・課金・共有をcommit・push、SHA照合済み | `07505884bb5388d3d92f51619ab3e9313cc10cde` |
| pals-agent | 最新Agentとv4 workerをcommit・push、SHA照合済み | `e4814d0a052126efa218cc4ecd19adad80447d97` |

同期前、親はGitHub未反映のInfraとObservabilityの6コミットを参照していたため、先にその6件をpushした。その後、各実装をcommit・pushし、親のsubmodule参照を更新する順序で同期した。

同期対象には実装、テスト、仕様、実行時のregistry・migration資産を含める。数学のbatch・negative-case・Leanファイルにはテストやauthoringの入力として直接参照されるものがあり、一括除外すると参照が不足する。一方、Playwrightの生成結果24ファイル、監査の生成JSON、秘密設定、キャッシュ、ログ、dumpは除外した。除外した監査JSONを参照する履歴文書も残るため、その証跡はローカル保管であり、GitHubだけでは再取得できない。`pals-draft-admin`は独立Git管理もsubmodule登録もない76ファイルのディレクトリだった。GitHubの同名リポジトリも現アカウントから見つからず、既存repo一覧にもなかった。内部画面のためprivateの保存先が必要で、新規作成の回答待ちとして今回は同期対象から外している。元ソースは保持した。候補確定後に別チャット「Lean検証のAI連携を設計」で作成された提案文書と`specs/external-lean-integration/`も、同チャットが作業中のため今回の同期には含めていない。

## 今回の検証では、公開可能な状態とは判定していない

Webは107ファイル・1,171テスト、TypeScript、ESLintが成功した。APIはv4統合後にunit 1,587件、直下のroute等437件が成功した。startup gateのfakeにsettingsを設定し、testsのpackage化に対応したimportを修正した。変更対象のRuffとsource 6ファイルのmypyも成功した。親の補助スクリプトは139件、Draft管理画面は92件と型・ESLintが成功した。InfraはPython 5件、dry-run契約、shell構文、Terraformのfmt・validate・mock plan 5件が成功した。実AWSへのapplyは実施していない。Observabilityのlockは構文・依存条件を照合したが、clean installは試していない。

Agentはv4統合後の全unitで2,854件が成功した。実Lean witness compileの2件を除外し、全moduleのcollectionを確認した。候補内PythonのRuffとlauncherのshell構文も成功した。mypyは28件残り、未変更baselineの17件と、source hashで検証するvalidatorの冗長cast 11件に分かれる。validatorのbytesを変えると既存証跡が無効になるため、型診断の解消より保存済みSHAの維持を優先した。

調査にはチャットの完了報告と保存済み証跡を使い、ソース差分、GitHub mainのSHA、DNSを現在の読み取りで補った。Miniの公開サービス、実KMS、実Cognito、質問送信、バックアップ復元は今回実行していない。次の作業は、Miniを同期版へ揃え、実資格情報・署名・認証・質問送信を確認すること。
