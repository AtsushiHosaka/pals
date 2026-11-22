# 検証済みの命題を解説より先に表示する(verified-first)の実装と測定(2026-11-14)

- 指標: 質問から、検証済みの命題(Lean が証明した命題)の表示までの秒(10 秒以内の題数)。10 秒目標は [pals#137](https://github.com/AtsushiHosaka/pals/issues/137)。
- 仮説: [ten-second-budget](2026-11-14-ten-second-budget.md) で、cheap-first の初回通過題は「検証済みまで」p50 9.3 s だが「表示まで」19.7 s で、差は解説の待ちと出力レビュー。検証済みの内容を先に表示すれば、解説を待たずに 10 秒に近づく。
- 変更(すべて既定無効、有効化はオーナー判断待ち):
  - pals-api #109(マージ済み、`claude/seq28-api-response-language`): `PALS_VERIFIED_FIRST_ENABLED` + ヘッダー `X-Pals-Verified-First: 1` のときだけ、追加項目 `verified_preview`(Lean が証明した命題、`explanation_state: generating|failed`)を返す読み取りモデル。出すのはジョブが検証済みで、その `lean_code` に承認済みの意味審査の行があるときだけ。解説の出力レビューは従来どおり公開前。無効時は本文・ヘッダー・request_version が不変(テスト)。ゲストは対象外。DB 移行なし。
  - pals-webfront #72(ドラフト、マージ保留): `NEXT_PUBLIC_PALS_VERIFIED_FIRST_ENABLED`(既定 false)。「Lean で検証済み」バッジ、「Lean が証明した命題」、解説は「作成中…」/「生成できませんでした」(再試行つき)。画面案のスクリーンショット 16 枚。
  - pals-agent: 変更なし(worker はすでに、検証後に解説を generating/failed の別資源として書く)。
- 測定(既存の cheap-first の記録からの計算。検証済みまでの秒 + 意味審査の待ち。UI のポーリング遅延(新UIは 2 s)と API 往復は別): 現行の表示(解説の後)で 10 秒以内は dev_unseen 0/20、tuning 0/14。verified-first では dev_unseen 4/20(p50 14.4 s)、tuning 5/14(p50 13.2 s)。初回 none を併せた構成は dev 6〜7/20、tuning 8/14。負荷平均 4.7〜17。n 小・1 回。
- 判断: 表示の順序が変わるため有効化はオーナー判断待ち。**この構成でも 10 秒以内は dev 4/20 で、目標には届かない**(残りは初回 Prove の 7.5 s と意味審査・検証)。
- 限界: 実 API・実画面でのエンドツーエンドは未確認(画面案は API をモックした開発用ハーネス)。API の統合テストは一時 Postgres で通過、出荷版の完全なスキーマでは未実行。UI のポーリング(2 s)と API の通知は含まない計算値。
- 出典: [pals-api#109](https://github.com/AtsushiHosaka/pals-api/pull/109)、[pals-webfront#72](https://github.com/AtsushiHosaka/pals-webfront/pull/72)、[ten-second-budget](2026-11-14-ten-second-budget.md)。
