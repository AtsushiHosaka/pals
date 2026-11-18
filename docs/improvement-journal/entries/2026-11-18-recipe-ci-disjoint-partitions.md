# Linux全体検査とMacの実Lean検査を分ける（2026-11-18）

Agent150 f82をMacで全体検査すると、75 failed・7748 passed・221 skipped・34 errors、682.41秒となり、実Lean5件のうち3件がtimeoutだった。OpenSSLのオプション差によるsetup errorも観測した。anchor比較より前に停止したため、75件を新しい製品欠陥とは数えない。メモリが原因とも断定しない。

[Agent151](https://github.com/AtsushiHosaka/pals-agent/pull/151)の653c4b0で、元のLinux環境の全体検査とanchor比較、無料標準Macの実Lean5件、最後の必須gateに分けた。テストは同sourceの重複しないpartitionで実行し、Mac側のtest deadlineは変えていない。両jobの成功と、同source・同workflow runの実JUnitが必要になる。

gateは元のoutcomeを結合するだけでPASSを作らない。登録した5件の欠落・重複・別module・失敗・skipと、sourceやrunの不一致・metadata不足を拒否する。既存のbaseline比較や許容skip一覧は変更しない。関連gate unit21件が成功・スキップ0、4.120秒。actionlint・Ruff・独立レビューも成功した。

全体CIは確認中で、時間短縮率はまだ測定していない。GitHubの無料標準ランナーだけを使い、新しい自前runner・有料枠・支払い設定・本番は変更していない。最終gateが通るまではqualifiedと扱わない。
