# seq30 認証準備の確認記録（2026-11-15）

seq30の候補は署名・ホスト準備・配置まで進みましたが、受け入れ確認に使うブラウザーで認証済みの状態を観測できず、切り替え前で停止しています。本番はseq29のままです。今回の2試行では質問・見積もり・証明生成を送信していません。3回目の有料ローカル資格確認も未実行です。

親 `24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infra `ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`、候補SHA256 `20ee79570a111b71028544858419df47f80943c71dd7c4e52dc119d3eb57eccf` を対象に確認しました。進行と判断は [#378](https://github.com/AtsushiHosaka/pals/issues/378) に記録しています。

## ローカル準備の入力修正

最初の準備では、すでにnative ARM64用へ変換済みのsubjectを、正規prepareのbase入力に指定していました。prepareはbaseの `images.verifier.image_id` を本番digestとして保存するため、生成された `verifier_variant.production_image_digest` にローカルnative image IDが入りました。そのため、予備照合の結果は `closed_native_local_verifier_variant_required` でした。認証や課金の処理へは進んでいません。

生成済みsubjectは証拠として保存し、別の入力DATAを作りました。変更はverifierのimage ID・image reference・platformを署名済み候補と実公開記録の本番値へ戻し、既存の `verifier_variant` を除く範囲です。他のfixture、model、予算、API・Web・workerの値は保持しました。生成出力のJSONを直接直さず、このbaseから正規prepareを再実行しています。古い未変換subjectは現在のアプリsourceと一致しないため使っていません。

修正後は `prepared_dependency_ready_not_product_accepted` になりました。本番verifier digestとの一致、宣言されたnative ARM64 imageとの一致を確認し、実Lean compiler canaryは2109msで `verified` でした。これは依存先の準備確認であり、質問への回答や本番受け入れの成功ではありません。

予算台帳は52 calls、`actual_microusd=180904`、`limit_microusd=700000` のままです。再開前checkpointとcalls全件が一致し、台帳の差分は正規prepareが記録する `resumed_from_sha256` だけでした。この金額はローカル予算台帳の値で、今回新たに発生した費用や請求額としては扱いません。

## 認証確認2試行

1回目は新候補・署名・実ホスト観測・現runnerへ結び付けた正規preview contractから、正規transportの開始処理だけを実行しました。開始待ちの後、`closed_dependency_or_input_failure` で停止しました。この一般コードだけでは原因を特定できません。

2回目は、正規 `bearerFromBrowser` の経路制限・認証更新・seed読込を変えず、ブラウザー処理へ件数とHTTP statusの観測を加えました。console、HAR、trace、URL、token、応答本文や生の例外は記録していません。

| 観測項目 | 結果 |
|---|---|
| 診断コード | `authenticated_context_not_observed` |
| ページ遷移のHTTP status | 200 |
| 対象となるowner GETの件数 | 0 |
| refresh要求の発行試行数 | 6 |
| 観測したrefresh HTTP status | 400 |
| failed requestの件数 | 6 |
| 認証済みcontextの観測 | false |
| 有料処理の送信 | false |
| 本番API認可の検証 | false |

`refresh_count=6` はブラウザーから発行しようとした要求の数です。正規routeが実際に許可する認証更新はcontext当たり最大1回であり、6回の認証更新を実行したという意味ではありません。HTTP 400とfailed requestの件数から、失敗の根本理由や各要求との対応までは確定していません。ページのHTTP 200も、ログインや本番API認可の成功を証明しません。

記録時点ではChromeのPALSログイン画面で、ユーザーの通常ログインを待っています。認証が回復したとは判断していません。元のprivate session seedは変更せず、今回の診断を本番回答・保存・描画・再読み込みの受け入れへ流用しません。

## 根拠のSHA256

生の記録と配置場所は非公開で保管しています。公開文書には識別用のhashだけを残します。

| 記録 | SHA256 |
|---|---|
| 修正前subjectの保存記録 | `6042e4f39bea3eab2281d3e1775466c9b4a6d78bd379849d491e2affdebdf591` |
| 修正base入力 | `fe95e8974074908b489a8807a4bdd14fe0dfc0d8b1c4f4bc9411f385264e133c` |
| 正規prepare結果 | `c8369d360c28cc99b77614161747c2d5fec7b14dfcd7ac618d6c98ae2607df14` |
| 再生成subject | `841967f2bd2e4adcc9dc213fc0c13af4d7bb654f19efe50436b453e2fb55fa85` |
| 再開後予算台帳 | `93f299b71875c5b3dcb624d7ca48683af4f8f8375f93a07e8cc0fbd10b48f04c` |
| ホスト準備受領書 | `687bfbffcf2ddb7ebcc7bf4ad431fd4c7d98634303d79f5a544cfe67de786edf` |
| ホスト配置受領書 | `e72ca3c4662290c41f6e5ecf82e204e709804fc8b1f8c23a22e56ebb0a3edbbc` |
| preview入力の結び付け | `f5a2ca53966052ab1e4bc7fbce29b0162a6f9aaba29620fe41b1ed62b1ef126d` |
| preview contract | `5874a912f35fc44ebc56bdfaeae677051402312bfe6ac6b907d7e8a7a6cfb5cf` |
| 1回目の認証開始結果 | `1aac37c12e591e3ea6c3cb1338aa99cb73f185295fb8e1bb12ef58658104cd09` |
| 2回目の観測診断結果 | `6010b226d518cc36752f0ea8e83dd61f744031c0de3c5895a70441268a014d1b` |

両ホストの受領書は同候補を示し、`application_mutated=false`・`database_mutated=false` です。準備と配置の完了を、候補の有効化や受け入れ完了とは区別します。

品質台帳には認証確認2試行をそれぞれ `availability` の0/1として追加しました。原因は未確定なので分類は `unclassified` です。同じ認証経路の追跡診断であり、独立した利用者集団の稼働率、数学の精度、課金モデルの性能や改善率は示しません。
