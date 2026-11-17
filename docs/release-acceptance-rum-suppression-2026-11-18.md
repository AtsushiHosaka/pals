# Acceptance観測でのCloudflare RUM抑止

親Issue #410の既存回答を2026年11月18日に読み直したところ、凍結済みのcanonical observerは回答検証、保存内容、画面表示、reload後の比較を通った後、`observer_attempted_mutation`で失敗した。独立診断では、元のroute handlerがabortした通信は`POST /cdn-cgi/rum`の3回だけだった。body、header、token、query値は記録していない。旧失敗記録、凍結source、planは保持する。

診断ではWebと同一origin、credentialsとfragmentなしを確認した。当初はquery delimiterもないURLだけを抑止対象にする案だったが、実通信には末尾の単独`?`があり、query keyは0件、重複もなかった。raw URLが既知のWeb originと`/cdn-cgi/rum?`の連結に完全一致することと、URL長34がその文字列長と一致することをbooleanで確認した。originの値や認証情報は公開しない。

[Cloudflare公式の収集方法](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/)では、Cloudflareでproxyするサイトのbeacon送信先を同一domainの`/cdn-cgi/rum`と説明している。この資料はendpointの意味を確認する根拠であり、本観測の通信内容を検証した証拠ではない。

今回の変更は、POSTかつraw URLが`${web_origin}/cdn-cgi/rum`または`${web_origin}/cdn-cgi/rum?`に完全一致する場合だけ、元と同じabortを続け、`suppressed_cloudflare_rum_posts`へ件数を分ける。bodyは読まず、送信、fetch、fulfillは行わない。API origin、他origin、userinfo、query key/value、余分なdelimiter、fragment、別path、末尾slash、encoded path、PUT/PATCH/DELETEは従来どおり拒否し、applicationのattempted writesに数える。従来のGET/HEAD/OPTIONS、既存product telemetry、単一の認証refresh境界は維持する。

抑止件数は観測結果に残す。抑止件数を、証明の正しさ、課金、アプリケーションの書込みを免除する根拠には使わない。回答・Lean・保存・描画・reloadの検査は変えず、通常のアプリ機能や本番telemetry設定も変更しない。今回のsource変更だけでは本番acceptance成功を示さない。新sourceの独立レビューとexact CI、レビュー済みsidecar contractによる既存回答のread-only再観測は別に必要である。新たな質問送信は行わない。

## 検証記録

基準は親mainの`f2b48c662cf293ec4d7c452cd0355ebd644add49`。route回帰はネットワークを使わず、実handlerのabort/continue/fetch/fulfillとcounterを検査するunit境界である。本番回答やCloudflareへの送信成功を代替しない。

- `node --test pals-scripts/tests/release-acceptance-refresh.test.cjs`。新26件を基準sourceへ適用すると25件成功・1件失敗。実際に見つかった末尾単独`?`も含む抑止回帰が失敗した。途中のquery delimiterなし限定実装でも25件成功・1件失敗だった。
- `node --test pals-scripts/tests/release-acceptance-refresh.test.cjs pals-scripts/tests/release-acceptance-browser.test.cjs`。修正後33件成功、失敗・skipなし。2種類のraw URL、bodyによる免除の拡大がないこと、他の書込み拒否、既存readの維持を含む。
- `python3 pals-scripts/tests/test_release_acceptance.py`と`python3 pals-scripts/tests/test_release_acceptance_refresh.py`は計16件成功。続く`bash pals-scripts/tests/release-acceptance.sh`は、初回sandbox内でloopback bind権限によりtransport 44件中43件がerrorとなった。この失敗は保持し、loopback通信を許可して同じbundleを再実行した。
- 再実行bundleはPython 3.14.7の8suite計214件、Node 22.22.3の3suite計37件が成功し、exit 0。失敗・skipなし。既存post-request suiteでunclosed fileのResourceWarningを4件記録した。単体・境界テスト件数を本番成功率や製品評価へ加算しない。
