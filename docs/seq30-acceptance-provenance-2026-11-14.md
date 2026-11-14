# seq30の資格確認前に見つかった証跡と契約の不整合

親`8b56f11`・infra`03cc80f`で候補`bc742cae`の署名、ホスト準備、28ファイルの配置と再照合まで完了した。本番の所有権取得、利用停止、admission、有効化は行っていない。以下は有料ローカル取得3回目の前提確認であり、本番受け入れではない。

## ローカルのビルド履歴

最初のローカル準備はWebの実ビルド履歴を再検証できず停止した。以前のローカルWebイメージIDも一致するよう要求した再ビルドは、umask 077と022で各1回失敗した。077ではアーカイブ展開後のディレクトリ権限も変わっていた。022の試行では入力ファイルのバイト列、権限、所有者、サイズと子ディレクトリの権限を照合したが、以前のイメージIDは再現しなかった。両失敗を保存し、合格へ読み替えていない。

Next.js 16.4.5の実ファイルを限定して比較すると、BUILD_IDとプレビュー用3キーが異なった。固定したNext.jsの公式ソースにはそれぞれの乱数生成がある。ただし、イメージ全体の差を乱数だけで説明できたとは主張しない。正式な契約は以前のローカルWebイメージIDの再現ではなく、同一候補ソースと閉じたloopbackビルド引数、実ビルド履歴による証明を要求する。

そのため、正規の`local-web-build.py`で同じWebソース`86c946b`と8個の固定引数から新しいローカル版を作った。実際のBuildKit materialsとinvocation parametersは以前と一致し、新しい実証跡の検証も成功した。9層中の先頭6層は一致した。これは本番Webイメージの変更ではない。

新しいWeb証跡で準備を再開すると、今度は検証器の履歴照合で停止した。実Dockerへの読み取りで、固定した履歴参照が削除済みと確認した。正規の`local-verifier-build.py`で完全なGitアーカイブから作り直すと、以前と同じイメージIDになった。ソース`189b443`、Dockerfile、Lean、Mathlib、コンテキストと実際の全依存パッケージを以前の証跡と照合した。

両方の新証跡を使った正規のローカル準備は`prepared_dependency_ready_not_product_accepted`で完了した。実コンパイラのcanaryは3141ミリ秒で`verified`。未完了の説明を持つ検証済みジョブは0件だった。費用台帳は実使用・予約とも180904マイクロドル、上限700000マイクロドル、52呼び出し、ブロックなしで変わっていない。モデルへ新しい質問は送っておらず、取得3回目は未使用である。

## 認証確認用の契約

旧配置の契約を現在の正規consumerへ渡すと、ブラウザーを開始する前に`executing_runner_changed`で拒否された。生成側の`release_acceptance_contracts.py`は2ファイルからハッシュを計算する一方、親の`release-acceptance.py`は4ファイルから計算していた。親の対象4ファイルは`1ed5fff`と`8b56f11`で同一であり、新しい作業場所への更新による差ではなかった。

旧契約の値は2ファイル式の`51cf7471c19b9060b30cd90f9a982f0ad019ea485ed61127d8be77839b2ab59f`に一致し、実consumerの4ファイル式は`2c21fa1a4ef682bbcc6044cf411d4f798fb2e7b8770cb38ee07039acc4bcd05b`だった。手書きのハッシュ置換は行わない。生成側を実consumerへ合わせ、変更と欠落を拒否する回帰検査と実consumerへの受け渡しを確認してから、正規の生成経路で契約を作り直す。

この失敗ではブラウザー、セッション更新、本番API操作、モデル呼び出しは始まっていない。修正・レビュー・必須検査と新しいリリースの固定が終わるまで、最後の有料ローカル取得と本番切り替えは実行しない。

## 根拠

秘密を含む生ログと証跡は非公開のリリース保管場所に保持する。下表はファイルのSHA-256で、公開のPASS受領書ではない。

| 記録 | SHA-256 |
|---|---|
| 初回local prepare失敗 | `cd6c549302d05370edae70d0ee4e97e719d1d8cb7196fec309b01625deaa8b7e` |
| 旧Web ID再現失敗・各試行の外側ログ | `42ce041f29fdcc770753fa9e5443d0a6f0ebe149cdacd440f96eaab8d7c755e8` |
| 新Web証跡 | `958c00ccae44e44214f9031ee1cda53ce9229c8b80e1ba925e37edc0ff593537` |
| 新Web証跡の検証 | `763016c772b639866cae8f904c9b770d53950f8e6bebd70f7f915c5ac63cde92` |
| Web証跡更新後local prepare失敗 | `304f71a0d5ef69aa52e600be348b551cfdf1aa84e46b60efa5367ebd10cd5edb` |
| 新検証器証跡 | `5ef06ec0db98d0c85b9d13fd7c8818742738a44e6d91685cd17c59554418774a` |
| 検証器再構築のログ | `99674e2d13b8a58b00d05f982b5c9bacbbb19d5c00f0f3971682af407648e851` |
| 両証跡更新後local prepare成功 | `68a5a56802321e60458e7dc4fd9c62c841c425c236710aa1b163de7d8b1bc595` |
| 既存の費用台帳 | `51827baa31c473039b01b79d69fd5fca19cbb32ef52b16a13f55a58622e03bef` |

進行記録は[#378](https://github.com/AtsushiHosaka/pals/issues/378#issuecomment-6876886842)。Next.jsの参照は固定版の[build/index.ts](https://github.com/vercel/next.js/blob/v16.4.5/packages/next/src/build/index.ts)、[generate-build-id.ts](https://github.com/vercel/next.js/blob/v16.4.5/packages/next/src/build/generate-build-id.ts)、[preview-key-utils.ts](https://github.com/vercel/next.js/blob/v16.4.5/packages/next/src/build/preview-key-utils.ts)。ローカル結果は本番認証、AMD64の実行境界、回答の受け入れを証明しない。
