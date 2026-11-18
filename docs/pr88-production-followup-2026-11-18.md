# PR #88の本番反映追跡

2026年11月18日、オーナーはPR #88の修正について、デプロイ担当チャットと連携し、本番の動作確認まで完了させるよう依頼した。進行管理は[Issue #425](https://github.com/AtsushiHosaka/pals/issues/425)、今回の機能は[Issue #420](https://github.com/AtsushiHosaka/pals/issues/420)で追跡する。本記録の時点では本番反映・受入は未完了である。

実行担当はcodex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2、独立確認はcodex://threads/01a1ece3-e675-7492-b366-f972b330540c。以前のリリース担当codex://threads/01a1e863-d84c-7e82-bedb-156dd25d871eからも読み取りだけの引継ぎを受けた。本番の変更操作と有料送信は実行担当へ一元化し、独立確認側から重複実行しない。

## 本番切替前の確認

Web統合PR #89の`de12f13a8e6fa0b337066f4c16de8a3e2e96d40f`から、利用枠の`refreshing`公開と、質問を取り出す前の待機条件を独立取得して確認した。PR #89は本番用ソース系統へ`a163b43a7c28e37a5a51f6a48f64a1a2bbb9821f`として統合された。ソースの統合と配備は区別する。

以前のリリースは、元台帳でfailed、owner_released=false、cleanup_completed=falseだった。別契約の再観測によるacceptedは、元リリースの失敗や管理ロック解放の証拠へ流用しない。

最初のAWS読み取りは、SSOの期限切れで失敗した。通常ログイン更新後、元の凍結済みsourceと設定を照合し、正規adapterのowner-checkだけを1回実行した。2026年11月18日13:40:11 JSTの観測で、旧candidateの管理ロックが保持され、markerが正規repair入力と一致した。targetの読み取りでも、想定した1台がhealthyであることを確認した。一時権限policyは存在し、全statementの期限が失効していた。これらは本番回答の受入やfull healthの合格を示さない。

独立確認側は、権限更新、管理ロック解放、回復設定の設置、サービスの再起動、trafficの変更、有料送信を行っていない。新しい正規後処理の開始後は、並行するowner/healthのdispatchも行わない。

## 以前の凍結入力と現行設定の分離

元担当が全frozen filesを照合したところ、ローカル設定1ファイルだけが元のhashと異なっていた。safety frozen files 27件と元台帳の参照は一致していた。UI復旧前の保全コピーを探し、元の期待hashと完全一致する4,107bytesのコピーを発見した。秘密の内容は出力していない。

実行担当は、現在の4,145bytesの設定を新しい永続pathへ保存し、現行Compose helperのCLI `--env-file`だけを新pathへ固定した。その後、以前の凍結pathを真正な保全コピーへ戻した。元planのpinや古い資格確認結果は変更していない。

独立確認側は前後の保存証拠を再計算し、33コンテナのsnapshotと他のruntimeファイルのsnapshotが等しいこと、退避した現行設定と復旧した元設定のhashがそれぞれ一致することを確認した。実行担当は再起動0件・provider呼出し0件を記録した。予算履歴とTLSの既存mountを保持し、新しい候補は改めて資格確認する方針である。

## 統合後CIの認証テスト失敗

Web統合merge `a163b43`の[CI](https://github.com/AtsushiHosaka/pals-webfront/actions/runs/44239198794)は2,200成功・1失敗だった。パスワード確認のInvalidPasswordExceptionを検査した後、テストが使う認証contextはloadingのままで、期待するunauthenticatedと一致しなかった。

AuthProviderと対象テストは、このmerge前後で変わっていなかった。テストは画面の状態だけを待ち、認証contextは別のeffectで外部変数へ反映していた。そのため、使用するcontextの反映前に操作する可能性があると判断した。ただし、変更前の単独ローカル実行は7件成功し、CIの競合自体はローカルで再現していない。同期不足は原因の推論として扱う。

[Web PR #90](https://github.com/AtsushiHosaka/pals-webfront/pull/90)では、画面と今回のproviderのcontext、認証状態がそろうまで同じwaitForで待つようにした。既存の3例外の確認ではHTTP応答を保留し、要求内容と、拒否前後の状態・認証epochが変わらないことも検査する。製品コード、timeout、retry、期待する状態と例外は変更していない。

修正head `96953962d7f6f0776c7ad40c19bd5f98557c41d3`は、ローカル159ファイル2,201テスト、typecheck、lint、独立レビューが成功した。[exact-head CI](https://github.com/AtsushiHosaka/pals-webfront/actions/runs/44240206444)も全項目成功した。PR #90のmergeは`c585c60c31e5b45c4615babaf7e7b7273ff8790b`で、merge自身の[CI](https://github.com/AtsushiHosaka/pals-webfront/actions/runs/44241476632)は確認中である。元CIの失敗記録は保持する。単体・CI件数は品質評価の分母へ加算しない。

## 本番で確認する経路

ログイン済みの本人のChromeで、利用枠を取得したホームから一度だけ質問を送る。新規chatへ移動した後、再送操作なしで同じ質問の要求が始まり、重複要求がないことを確認する。APIへの直接投稿だけでは、この引継ぎ経路を確認したことにしない。

得られた同じrequest・chatの識別子を正規の受入へ結び付け、Lean検証、説明完了、完全な結論の保存、実描画、履歴と再読み込みまで確認する。通信が中断しても、同じ依頼を再観測し、別の有料依頼は送らない。本番で遅延応答の順序が自然には起きなければ、通常経路の本番成功と、競合順序のコンポーネント回帰を分けて記録する。
