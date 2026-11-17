# 別プロセスの確定通知（2026-11-17）

指標は時間。検証を確定する別processのcommitからAPIへの合図がないため、従来の巡回まで待つ経路を減らす試み。[API PR #120](https://github.com/AtsushiHosaka/pals-api/pull/120)でtransaction内の内容なしNOTIFYとAPI専用listenerを配線した。DBを状態の正本とし、認可と既存の15秒/5秒fallbackを保持する。idle時は接続を持たず、active long-poll時だけprocessあたり1接続に制限した。

基準producerで別processの実reconcilerの通知回帰がRED、候補でGREEN。locked unit108件・実PG83件が成功したが、件数を製品成功率へ換算しない。既存natural-only fixture不足と初期fixture失敗、初回の不正確な計時はPRの記録に保持する。

別processの完了job/説明fixture更新前からsignal・DB反映・long-poll helper観測までの上限を20件測り、p95 0.066105750秒、中央値0.054540813秒、最大0.069458375秒。初回のreturn後起点の20件は厳密なcommit性能には不採用とし、方法修正後の20件だけ採用した。load4.895/3.624/3.455、CPU18。fixture SQLとhintは別transaction、production同一transaction配線はcompiler拒否を制御した別試験で確認している。

この局所境界では1秒未満だが、実Lean、意味審査・説明待ち、認可済みHTTP、render、本番の性能は未確認。画面のplain pollではlistenerが起きないため、Web側の配線は別sliceとして進める。比較可能な本番before/afterはなく、速度改善率や#380全体の達成を宣言しない。新有料モデル・AWS・コンテナなし、費用総額は未測定。一時DBとlistener接続は回収した。

[詳細と全20sample](../../410-380-verification-2026-11-17.md)。採用raw hashはd2685183989281b343e17e8185546a72ad84dc4ba59b905ef069b99afc7a295b。
