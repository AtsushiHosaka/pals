# #410の再開と認証診断（2026-11-18）

担当セッションは`codex://threads/01a1e863-d84c-7e82-bedb-156dd25d871e`。[前日の確認記録](410-380-verification-2026-11-17.md)を統合した親PR #413のmergeは`f2b48c662cf293ec4d7c452cd0355ebd644add49`である。本記録は、その後の再開時に確認した到達性と、質問送信前に止まった認証確認を追記する。#410・#380全体の完了記録ではない。

## 到達性と通常ログイン

AWSの通常SSOログインが成功し、指定された正確なtarget 1台がhealthyであることを確認した。curlでは認証前APIがHTTP 401を返し、server-owned releaseヘッダーは候補`1be72c60b705328c30b61c198fa037f6b6ef14dfd0f9ed92aa118914bf543f15`と一致した。urllibではHTTP 403となる既知の差があるが、この差だけを製品不具合と断定しない。これらは到達性と候補識別の確認であり、回答生成・受け入れ・owner解放・cleanupの成功を示さない。

通常のChromeではPALSへのログインが完了し、homeを確認した。一方、以下のcanonical受け入れ経路では認証済みcontextを観測できなかった。通常利用のログイン成功と、凍結済み経路が使う認証contextの確認を同一の成功として扱わない。

## canonical post-request 1回の結果

凍結済みの正規post-request argvを、plan SHA256 `8807d098d93df78b85ae2fdb04e24c7d7271c69093ab3e44c75d40837578e388`と照合した。凍結対象のhashもすべて一致することを確認してから、正規の実行を1回行った。planのhashは、本記録作成時にも元ファイルから独立に再計算して一致した。

結果はexit 2、`authenticated_context_not_observed`で、`post-request.jsonl`は0行だった。質問送信と有料送信はいずれも0件である。数学問題を送信して失敗した試行とは分け、質問送信前の認証事前確認1試行として数える。既存の失敗分類に認証専用コードがなく、HTTP 400の詳細原因も不明のため、台帳には`unclassified: 1`を記録する。モデル費用総額や回答時間は測っていないので空欄にする。

続いて正規の認証診断を行い、次を観測した。

| 診断項目 | 結果 |
|---|---:|
| goto | HTTP 200 |
| owner_get | 0 |
| refresh要求の観測数 | 6 |
| refreshのHTTP結果 | 400 |
| failed requests | 6 |
| auth | false |
| paid submission | false |

refresh要求の観測数6件は、6回の実refresh送信を意味しない。canonical経路が送信を許可するrefreshは最大1件で、上限外の要求は中断した。failed requestsの6件も独立した利用者試行や数学失敗へ数えず、post-requestの1試行と診断要求数を合算しない。

使用したseedのaccess・idは11月16日のもので、再開時点では期限切れだった。ただし、期限切れだけをHTTP 400の確定原因とはしない。詳細原因は未確認である。ユーザーには既存の`session-export.js`をログイン済みChromeのConsoleで手動実行し、新しいseedをローカル保存するよう依頼し、返答を待っている。tokenやseedの内容をチャット・公開資料へ貼るようには求めていない。新しいseedでの再実行結果は本記録に含めない。

根拠の私有ログはローカルだけに保持し、本文や内容をGitへ入れていない。post-requestログのSHA256は`9053150401f2a7957c553dd69d1f1a03096528ae35861bfd06b1ca83cc7c6227`、認証診断ログは`bd13623db7b3f112aadf6804977d67c3ab2c61121577aa83919b2a1c54de6edb`。公開記録にはtoken、account、内部host・IP、質問本文、ユーザーの個人情報を含めない。

## 後処理sourceの追加修正

[Infra PR #187](https://github.com/AtsushiHosaka/pals-infra/pull/187)は、旧head `30a51da`の4 CI成功後、fresh healthをcacheから再利用してしまうP2が見つかった。新候補`babf9b7`では両hostを毎回`fresh=True`で確認するよう修正した。旧版で関連2件がRED、新版で関連47件がGREENとなることを独立に確認した。これはsourceの回帰検証であり、47件を製品評価や利用者試行の分母へ加えない。

引継ぎ時点で新候補の[CI run `44112797938`](https://github.com/AtsushiHosaka/pals-infra/actions/runs/44112797938)はqueued／in progressで、旧pushのrunはcancelされていた。旧headの成功を新候補の成功へ引き継がない。liveのIAM更新・host操作は0件である。元releaseのfailed・accepted=falseを維持し、owner解放・権限削除・別closureのlive完了や、認証付き本番受け入れを宣言しない。未完のCI・新seed・再実行・後処理の結果は、担当が確認後に別途追記する。
