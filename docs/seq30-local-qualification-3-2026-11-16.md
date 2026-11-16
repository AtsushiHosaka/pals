# seq30の3回目のローカル資格確認（2026-11-16）

3回目の正規ローカル資格確認は、実Leanコンパイルを通過した後、意味審査で不合格になりました。候補b976は有効化しておらず、本番はseq29のままです。最終freeze、dry run、release-cycle、利用停止は実行していません。成功条件や審査条件を変更せず、この失敗を保持します。

対象は親 `24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infra `ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`、候補SHA256 `b976afec64f31a3d9f3b74a11dbff6b9a9b46d27d32be2d2865e82cf1fc3f59a` です。進行と判断は [#378](https://github.com/AtsushiHosaka/pals/issues/378) に記録します。

## 実測と失敗の切り分け

正規処理全体の壁時計は118.602秒でした。これは回答の所要時間やAPIの応答時間ではありません。実行時のMac負荷は未記録のため、処理速度の評価や比較には使いません。有料送信のmarkerが残っており、自動再送はしていません。

課金前の実compiler canaryは2429msで `verified` でした。今回生成されたLeanについても、保存された検証結果は `compile_success=true`、verifier attestationは成功を示し、正規のDB結合predicateもtrueでした。意味審査は同じLean hashに対する1件の `rejected` で、修復は0回、設定上限は6回です。保存された検証所要時間は3823msでした。

| 確認した項目 | 結果 |
|---|---|
| request状態 | `failed` |
| job状態 | `failed` |
| 終了理由 | `semantic_review_failed` |
| job診断コード | `pals.proof_semantic_review_failed` |
| 実Lean検証・attestation結合 | true |
| 意味審査 | 同じLeanに対して1件、`rejected` |
| 修復回数と上限 | 0 / 6 |
| requestへ返されたコード | `lean_verification_failed` |
| ローカル受け入れ | failed |

終端の `attempt.verification.diagnostics` には意味審査のerrorが1件投影されています。意味審査以外の投影errorは0件ですが、元のcompiler診断数は独立に保存確認できていません。そのため「compiler error総数0」とは記録しません。生の意味審査理由、質問、Lean、IDは掲載せず、限定証拠v2の固定コード・bool・hash・件数を根拠にします。古い要約の `compile_error_count` は終端に投影された意味審査errorを数えていたため、compiler診断数の根拠には使いません。

意味審査が誤判定だったか、生成証明の意味に問題があったかまでは独立確認していません。runtime故障も証明されていません。今回確認できたのは「コンパイル通過・意味審査不合格・APIの汎用コードへの変換」です。原因調査でモデルを再送したり、compilerを再実行したりしていません。

## コード上の境界

APIの `app/infrastructure/repositories/postgres.py:4266` 以降で、意味審査の不合格を診断コードとjobの失敗状態へ保存します。`app/domain/models/proof_job.py:877` 以降はコンパイル成功を保持して意味審査の終了理由を付けます。同ファイル975行付近では、成功boolを維持したまま渡された診断を投影するため、終端の意味審査errorはcompiler errorと区別する必要があります。

APIの `app/infrastructure/repositories/proof_request_lean.py:261` は、失敗したjobをrequestの汎用 `lean_verification_failed` へ変換します。親の `pals-scripts/local-qualification-browser.cjs:87` がそのfailed requestを受け入れ条件から外し、保存結果には `browser_journey_failed:terminal_answer_required_failed_lean_verification_failed` が残りました。ブラウザーの表示するコードだけでコンパイル失敗とは判断できません。

## 費用と次の判断

proxy予算台帳は52 calls・180904 μUSDから、60 calls・220786 μUSDへ変わりました。差分は8 calls・39882 μUSD、0.039882 USDです。これはproxy台帳に基づく費用差分であり、実請求額ではありません。残高のresetや新たなrolloverはしていません。

終了時は60 callsすべてが `completed`、actualとreservedはともに220786 μUSD、上限700000 μUSD、`blocked=false` でした。台帳上の上限に余裕があることは追加試行の許可を意味しません。承認済み3回の範囲を使い切ったため、4回目の有料取得は未承認です。期待値、oracle、モデル、審査flagを変えず、追加取得の条件と根拠を提示して判断を求めます。

## 根拠のSHA256

生の証拠は非公開で保管しています。限定証拠v2以外のDB全体snapshotは保存していません。

| 記録 | SHA256 |
|---|---|
| 限定forensic証拠v2 | `745f84919357c9c8733270e173a850085a7ddc2502ed0d9d3597561a291aaca4` |
| 資格確認の保存結果 | `2f608e378bd1b1d720a88b2376920d98017fe7be4f8be15b42d67aaf9a0f37dd` |
| 正規captureの記録 | `d4562a61b41821d2b504d6354925616edf93ba12bdeb7934807f526f6e156678` |
| attestationと意味審査が参照するLean | `f8587f501a0042e0fdefd1be3abed21af2d26b90c138798bfa19f94e483e572d` |
| 意味審査理由の保存hash | `eb5df39fc6339e5ddfa14ea20d4d441817f2e39fb9746fcd5dc88c50b4046842` |
| 実行前の予算台帳 | `85170132962301d87c8809b1ce8eafda863840f9a3c74ca1c027d12037704417` |
| 実行後の予算台帳 | `74641caeb5728b671b28a0f6fd0ed3a4e06a00554b42f7ae6d1e75a7762e1bf9` |

品質台帳の `2026-11-16-seq30-local-qualification-3` は、有料資格確認全体を1試行・成功0、失敗分類 `review.rejected` として記録します。8回のprovider呼び出しやcanaryを別の試行へ加算せず、数学全般や本番の成功率、過去との改善率は作りません。[認証開始の成功記録](seq30-auth-context-observed-2026-11-16.md)も、その確認範囲を保ったまま残します。
