# seq30の4回目のローカル資格確認（2026-11-16）

オーナーが[追加1回を承認](https://github.com/AtsushiHosaka/pals/issues/396#issuecomment-6909758854)した後、正規`make release-local-qualify`を1回実行し、`accepted`になりました。既存の第3回の失敗記録は保持しています。今回の成功はローカル資格確認の1/1であり、本番受け入れや数学全般の精度を示しません。

親は`24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infraは`ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`、候補SHA256は`b976afec64f31a3d9f3b74a11dbff6b9a9b46d27d32be2d2865e82cf1fc3f59a`です。モデル、oracle、意味審査、成功条件は変えていません。追加承認はこの1回に限り、予算台帳のresetやrolloverは行っていません。

## 実測と費用

主担当が初回wrapperの終了時に観測した取得全体の壁時計は138.567秒でした。今回の文書作成時に、この所要時間を保存ファイルから再計算してはいません。providerの内部呼び出しは11件、予算proxy台帳の増分は34660μUSD、0.034660 USDです。これは版管理された料金表に基づく台帳の値で、実請求額ではありません。内部11 callsを11試行として数えず、製品を通した資格確認1件を試行数とします。

取得前は60 calls・220786μUSD、取得後は71 calls・255446μUSDです。後者のactualとreservedはともに255446μUSD、上限は700000μUSD、blockedはfalseで、全71 callsはcompletedです。以前の費用や試行と合算して改善率を作りません。

実PostgreSQL、実Lean、実provider/modelを使い、終端の回答、説明、保存、描画、再読み込みの正規契約を受け入れました。その後、controllerの正規`--verify-existing`が同じ取得を新規送信なしで再照合し、`accepted`を再確認しました。現受領書の`proof_submissions=0`はこの再照合時の値です。最初の取得で送信しなかったという意味ではありません。現受領書ではcompiler canaryが2138msでverified、終端がanswered、表示と再読み込みのsemantics hashが一致しています。

## 受領書と限界

初回受領書のSHA256は、主担当が当時観測した`ad216b1d2bc26f1be2d1dbe3b6568ff9ddb6606e43594d773c95bb90e32b347c`です。正規の再照合で更新されたため、その初回受領書自体は現`latest.json`には残っていません。現在の`latest.json`の開始・終了は再照合区間であり、138.567秒の取得全体とは区別します。再照合を追加の有料取得や独立試行として計上しません。

| 記録 | SHA256 |
|---|---|
| 初回取得のprivateログ | `baaddc2514ec4caf04219730f735e3e285138de3bf5faa14238f71fa3d52c87a` |
| 対象subject | `d082bf09ea964a28ca581010235bbb246346dd10584aa361d7468190b1cc8edf` |
| 正規再照合後の受領書 | `9ff3ba2200c48558af1bb64afdabe2b86c8668d512e9ff0fb83fee805cb9ffac` |
| 同じ取得のsubmission記録 | `a500371ba6c7d0cf5661fedf61a1abf5490ec4d8175e193910b8d7bda20b5aa6` |
| 現browser結果 | `5fa3452234997e76ec5c9606ea529dbbad9d4c2a4af877791bd5d3d3eac634c4` |

生の質問、回答、Lean、session、ログは非公開で保管します。ローカルWebは宣言したloopback用のbuild引数、verifierは同じ本番sourceに基づくnative ARM64 variantです。ローカルの受け入れは、本番AMD64、認証、ネットワークや切り替え後の新規質問の受け入れを証明しません。この記録から本番配備完了とは判断しません。
