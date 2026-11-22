# seq30再開時の準備確認（2026-11-16）

通常ログイン後に作業を再開し、ローカル依存先の正規prepareを1回完了しました。実Lean compiler canaryは2455msで `verified`、状態は `prepared_dependency_ready_not_product_accepted` です。この時点では新候補manifestをまだ生成しておらず、headlessブラウザーの認証と本番受け入れも未確認です。AWS SSOの通常ログインを待つ段階の記録として残します。

## 再開時の入力と期限

親 `24d8f9574d732ce909c2c00198b9a6772d61d7e2` と6つのsubmoduleは、固定した参照に一致し、作業差分がありませんでした。infraは `ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf` です。旧候補C20eeは2026-11-15 15:28:59 UTCに期限が切れているため、その署名済みmanifestで新しい認証確認や切り替えへは進みません。

新しいsession seedはprivateな通常ファイルとして保存し、mode 0600・リンク数1を確認しました。担当は元のdownloadを除去済みと報告しています。秘密の内容は記録せず、seedのSHA256だけを下表へ残します。通常ログインとseed保存だけでは、headless contextの認証成功や本番APIの認可を証明しません。

新bindingは旧C20eeのbindingとsource・公開記録・reviewed pathsが一致しています。verifierの本番digestを保持したbase DATAから正規prepareを実行し、生成後のnative variantも同じ本番digestを参照することを確認しました。新候補manifestそのものは未生成のため、新候補との一致は後続の正規検査で確かめます。

## TLS更新とローカル準備

保存されていたローカルprovider TLS証明書は期限切れでした。正規bootstrapで12時間の証明書を発行し直した結果、残存43198秒で `valid` になりました。prepare完了記録では43093秒残り、読み取り確認時点でも約43000秒ありました。prepare開始時に必要な6300秒と、完了時に必要な4500秒を満たしています。これはその時点の値であり、後のcapture前には正規検査が改めて確認します。

正規prepareはWebとnative verifierのbuild receiptを再検証してから、依存先・runtime・compilerの確認を終えました。両receiptと参照するbuild recordの実ファイルhashも一致しています。今回の独立確認ではDockerやcompilerを再実行せず、正規prepareの終了結果と、その処理が検証する参照を照合しました。

native verifierは宣言されたBF image・ARM64・固定sourceと一致し、本番digestは署名済みC20eeのものと一致しました。実compiler canaryのimageとtoolchainも一致しています。leftoverのjobとrequestは各0件、検証済みだが説明が終わっていないjobも0件でした。

ローカル予算台帳は52 calls、`actual_microusd=180904`、`limit_microusd=700000`、`reserved_microusd=180904`、`blocked=false` を維持しています。prepare前のbackupとcalls全件が一致し、台帳で変わったのは正規再開処理の `resumed_from_sha256` だけです。subjectのcheckpoint参照と台帳の再開先hashもbackupに一致しました。台帳を空にしたり、予算をresetしたり、新しいrolloverを行ったりしていません。

3回目の有料captureは未実行で、既存のcallsと費用値は増えていません。この金額は予算台帳の累積値であり、今回の費用や実請求額としては扱いません。課金処理前の依存先確認が通ったことを、数学の回答成功や本番受け入れへ換算しません。

## 根拠のSHA256

生の記録と配置場所は非公開で保管しています。秘密、質問、アカウント、内部ホスト名、IPは掲載しません。

| 記録 | SHA256 |
|---|---|
| 新session seed | `9295fe266124ec3bc00e47e271495a2def50ad89140367de8b85938196bcc636` |
| 旧署名済み候補C20ee | `20ee79570a111b71028544858419df47f80943c71dd7c4e52dc119d3eb57eccf` |
| 新binding DATA | `ad823d564674662b5dab5a6281e5b61eba56e78229dffc5a14463a3b8da90e60` |
| TLS期限切れの確認 | `751d3a803e925355154ba30c989384c379d6eb85e5d58eab1687dc8ad3d01ac1` |
| TLS正規更新・更新後確認 | `92cd4ed862e0d2c59a6a545b658c5ea0e95c0cd01bf345b353eba3acb7bb941f` |
| 正規prepare結果 | `4856d868c136b49a5ef2728d54e1653585160911b43d3e5b97c5ae69561ba786` |
| 再生成subject | `d082bf09ea964a28ca581010235bbb246346dd10584aa361d7468190b1cc8edf` |
| 再生成local環境ファイル | `ed8ad14185446804705cd770b8ecff2b475ae0c606149d60ebd5119c95e938fa` |
| 再開後予算台帳 | `85170132962301d87c8809b1ce8eafda863840f9a3c74ca1c027d12037704417` |
| prepare前の予算台帳 | `93f299b71875c5b3dcb624d7ca48683af4f8f8375f93a07e8cc0fbd10b48f04c` |
| Web build provenance | `958c00ccae44e44214f9031ee1cda53ce9229c8b80e1ba925e37edc0ff593537` |
| native verifier build provenance | `5ef06ec0db98d0c85b9d13fd7c8818742738a44e6d91685cd17c59554418774a` |

品質台帳の `2026-11-16-seq30-resume-local-readiness` は、この正規prepare全体を技術準備の1/1として数えます。canaryやreceiptの数を別々の成功試行には足しません。[前回の認証失敗記録](seq30-auth-readiness-2026-11-15.md)は保持し、今回のローカル準備成功で書き換えません。進行と判断は [#378](https://github.com/AtsushiHosaka/pals/issues/378) に記録します。
