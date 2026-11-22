# seq30認証contextの観測（2026-11-16）

新候補b976と新しいsession seedを使った正規認証開始が1/1で成功し、`authenticated_context_observed` になりました。正規helperが、対象として許可したowner GETで認証済みBearerを観測したことを示します。本番APIがその認証を受理したことや、候補の回答・保存・描画・再読み込みの受け入れは未確認です。

この記録は、有料capture3を始める前の認証確認時点を対象とします。親は `24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infraは `ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`、候補SHA256は `b976afec64f31a3d9f3b74a11dbff6b9a9b46d27d32be2d2865e82cf1fc3f59a` です。ローカル予算台帳はこの時点で52 calls・180904/700000 μUSDを維持し、3回目の有料captureは未開始でした。

## 実行と観測の範囲

新しい署名済み候補、実ホスト観測、現source、実runtime pinsを正規factoryへ渡し、preview contractとscenarioを導出しました。現consumerの契約検査とmanifest検査を通し、subjectとの予備照合も完了しています。予備照合は正規freezeや有料資格確認の代わりにはしません。

そのcontractで正規transportの開始処理だけを実行し、終了時にブラウザーを閉じました。結果の `seed_unchanged=true` を確認し、保存されたseedのhashとmode 0600も照合しました。元のseedへの書き戻しは行っていません。

| 観測項目 | 結果 |
|---|---|
| 認証開始の状態 | `authenticated_context_observed` |
| 元seedの不変 | true |
| transportが送ったAPI操作メッセージ | 0 |
| 有料処理の送信 | false |
| 本番API認可の検証 | false |
| 本番候補の受け入れ | false |

API操作メッセージ0件は、transportの質問作成・見積もり・送信・結果照会を呼んでいないという意味です。通常のページ読込に伴うGETまで0件だったとは解釈しません。

正規helperの制限は、通常の読込と許可済みproduct event、fresh policy確認後のcontext当たり最大1回の通常認証更新です。ただし今回は認証更新要求を個別に観測していないため、refreshが実行され成功したとは判断しません。[前回のHTTP 400と認証未観測](seq30-auth-readiness-2026-11-15.md)の根本理由も未確定です。今回の成功で過去の失敗記録を書き換えず、原因が解決済みとも断定しません。

## 根拠のSHA256

生の記録は非公開で保管しています。秘密の内容、質問、内部配置場所、アカウント、ホスト名やIPは掲載しません。

| 記録 | SHA256 |
|---|---|
| 新session seed | `9295fe266124ec3bc00e47e271495a2def50ad89140367de8b85938196bcc636` |
| preview導出結果 | `38c2c237b30b342795450eb77fe09e81a5257c1b2c4d2820025442281fbab8ba` |
| 新preview contract | `e5d99984a96ff9ce9224d93baf068eed33ae961ad0c5f771a92046074b7fcc71` |
| preview入力の結び付け | `728131ef7f9d6f8d17733d79d99d51dfdad487d043032be66dfa85fa3dd30efc` |
| 実認証開始の結果 | `d2204ffdeb71d0184569bb164adc6ab11029e075289ca1ebdfa20d6f46919220` |

品質台帳の `2026-11-16-seq30-auth-readiness-recovered` は、この認証開始1試行を技術確認の1/1として記録します。モデルや数学の精度、一般的な認証成功率、前回との改善率は示しません。[ローカル準備の確認](seq30-resume-readiness-2026-11-16.md)と合わせて、後続の資格確認・本番受け入れとは分けます。進行と判断は [#378](https://github.com/AtsushiHosaka/pals/issues/378) に残します。
