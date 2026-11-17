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

## 認証情報の更新とcanonical送信の再開（同日追記）

ユーザーがConsole操作を明示的に許可した後、native ChromeのConsoleで既存scriptを実行し、新しい認証情報のローカルdownloadを確認した。取得ファイルは約4.5KBで、内容は公開しない。最初のprovisionは、元のsessionが`frozen_files`に含まれることをassertionで検出して拒否され、変更は0件だった。旧sessionや凍結planを上書きして通過させていない。

新しいsessionは永続領域の別ファイルへ保存し、元sessionと`iss`・`sub`・`aud`が同一で有効期限が新しいことを確認した。旧plan・session・凍結対象のhashは不変である。tokenやclaimの具体値、保存先の内部path、account情報は記載しない。

canonical post-requestではsession引数だけを新ファイルへ差し替え、idempotency key・state・scenario・cycle・modelを維持した。結果はexit 0で、post-request journalは4行となった。新しい実行の私有ログのSHA256は`63abd09358fcbe992eb7e949b9db57e8cef962996ff90bff9f8db6391cdfaec8`である。先のexit 2と0行の結果を消さず、認証更新前後の別段階として残す。

この時点では送信した1件のacceptanceを読み取り専用で観測中であり、回答完了・保存内容・画面表示・reload/history・本番受け入れの最終結果は未確認である。exit 0やjournalの4行を、独立した4試行や数学の成功率へ換算しない。追加質問を送信して観測をやり直さず、同じ1件の結果を確認する。

## 後処理sourceの統合（同日追記）

Infra PR #187はmerge `c2809c3de7c7dc7a56060d0909d8134e730e18a7`で統合した。最終head `babf9b7706b1fca9c947a469d5bc3bbf6a109126`の4 CIは成功した。先に記録したCI待ちの状態から進んだsource上の結果であり、liveの後処理成功とは分ける。永続領域でのrepair source準備は進行中で、grantは未実施、live IAM更新・host操作は0件である。

## 単一送信に対する受け入れgateの初回結果（同日追記・診断中）

新しい質問は上記の1件だけで、追加送信は行っていない。canonical acceptanceの初回結果はexit 1、別attempt台帳の最終行はfailed、codeは`observer_attempted_mutation`だった。最後のHTTPは200で、runtime 6 rolesのmetadata照合は済んでいる。traceでは15:48:44.129Zのverifying・revision 2から、15:49:56.514Zのanswered・revision 3へ進んだ。ただし、この2つの観測時刻の差を、正確な実行時間や全体の回答時間へ換算しない。

canonical browserコードはwrite counterの検査で拒否した。sourceの実行順序上、`validateAnswer`、保存内容、render、reload後の比較を通過してからの拒否であるが、この通過だけでgate全体を成功へ書き換えない。別途、rootがChromeの実画面で結論全文の表示とreload後の同じ結論の復元を独立に確認した。これらの観測を保持したうえで、正式なacceptedは不可、元のfailed台帳も不変とする。

拒否されたpathの診断は別担当が進めており、原因は未確定である。`observer_attempted_mutation`を根拠に、実際のアプリデータが変更された、あるいは数学の証明が失敗したとは断定しない。source・read policyを変えてgateを通過させる操作や、結果を得るための追加質問送信は行っていない。

台帳への追加対象はこの1件の受け入れgate失敗で、n=1・成功0とし、数学の成功率とは分ける。先の認証事前確認失敗は同じ受け入れ再開に属する別時点・別指標なので、重複参照を付けて利用者試行数へ合算しない。金額は未取得のためUSD欄は空にする。最終診断と記録の確定・pushは保留する。

## 拒否pathの特定とsource補修の分離（同日追記）

その後の局所診断で、拒否されたのは`POST /cdn-cgi/rum`の3件だけと確認した。元policyで3件すべてをabortしており、質問再送・SSM・IAM更新・host操作はいずれも0件である。[Cloudflareの公式資料](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/)は、Cloudflare経由のサイトでは同一domainの`/cdn-cgi/rum`へWeb Analyticsのbeaconを送ると説明している。診断されたpathはこの計測用endpointに一致するが、元のfailed結果を成功へ書き換えない。

別worktreeでは、正確なWeb originの`POST /cdn-cgi/rum`でquery・fragment・userinfoのない要求だけを、引き続きabortしたままsuppressed counterへ分け、アプリのattemptedWritesへ数えないsource修正を準備中である。他のwriteは失敗扱いを維持する。通信許可・fulfill・回答fixtureでの代替は行わず、旧frozen source・plan・failed recordも変更していない。

この新sourceはCI・独立レビュー前であり、新しいsourceによる正式acceptanceはまだ実施していない。source変更の設計・検証は担当の別engineering noteへ記録する。本記録は元policyによる確定したgate失敗と、そのpathを特定した局所診断までとし、後続sourceやlive実行の結果を先取りしない。

初回acceptanceの私有ログのSHA256は`94a4d5d0bf6dc372338170a765dcb84f8f396e2732e4cc47a565c9efa0e3b161`。今回の品質台帳行は`2026-11-18-canonical-acceptance-observer-write-blocked`とし、先行認証事前確認行を`overlap_with`で参照する。数学・モデルの成功率や費用改善へ換算せず、USD欄は未取得のまま保持する。
