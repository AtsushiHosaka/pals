# 資料添付・料金再設計のSDD記録

2026-09-30。初期は資料仕様策定、後続回答でinline画像実装・成功時精算・換算token・設定UIを追加。Chromeとpals-localを再利用し、別環境は作らない。既存dirtyを保持しcommit/pushなし。

基準: parent `02801ca` / API `858dd16` / web `7837f8f` / agent `ab42335` と既存未コミット変更。初期入力hashは `output/project-materials-spec-20260930/baseline.json`。初期45分/2反復の後、ユーザーの追加決定に応じ対象を更新。親上限6時間を維持。

| 反復 | 新しい根拠 | 経路・担当 | 成果・確認 | 残り |
|---|---|---|---|---|
| 1 | Projectに資料処理なし、既存meterは全原価を覆わない | grill/generate、selection/auth調査 | 要件・設計・タスク・料金案を作成、D1–D6質問 | 回答待ち |
| 2 | 原本/命題binding、閲覧境界、容量解放の不足 | review-spec/proof、root修正 | 原本独立照合、閲覧隔離、状態別容量・予約契約を追加、再レビュー | 数値・削除条件 |
| 3 | D1–D10回答：形式限定、全ページ、有料Project、解約後閲覧、画像に応じた負荷、説明提供成功のみ消費 | update-spec、API/Web slice分担 | 15要件/11タスクへ更新。APIがhold案作成後、token steeringで未接続初稿を削除。API稼働変更なし | 全工程meter・token API未実装 |
| 4 | D11/D12回答：換算利用token、全依頼集計、事前上限、失敗0 | architecture/read-only API・agent調査、update-spec | generation-only欠測を確定。quote→hold→stage permit→receipt→actual精算案、価格A/Bを作成。部分質問・原本画像入力・取込失敗精算の3指摘を修正し再レビュー | 価格/付与量の選択待ち、OCR評価・削除期限等。仕様全体の実装準備完了ではない |
| 5 | 設定UIの独立先行実装が可能 | implement/selection、review/auth、root runtime QA | 一般/使用量dialog、account menu、4言語、実残回数率、下書き保持。Pro/Free残量labelのP3を修正。既存webfrontだけ更新、同じChromeタブで実API確認 | token残量と資料UIは未実装。既存回数をtokenと呼ばない |
| 6 | Stripe実装・現行価格の確認と、支払い不要のテストProを追加要望 | BILL-011 working delta、implement/auth・selection、review/proof | 独立した期限付き管理者grant、100回枠、Stripe優先、取消、4言語表示。通常releaseの権限不足とCLI環境照合の指摘を修正し再レビューPASS。API unit962/HTTP429、実PG27＋権限制限upgrade、frontend全unit908成功。rootでローカルCLI→実API→画面→取消→Free復帰、temporaryrole/秘密状態削除まで確認 | Stripe実接続・token制度は未実装/未検証の境界を維持。実利用者への付与は対象と期限未指定 |

## 証拠と境界

- 初期文書hash/旧正本不変確認は初期反復だけの証拠。後続では承認済み変更をBILL作業中仕様へ反映したため、旧hashの不変主張は失効。
- 最新提案は `docs/proposals/project-materials/{requirements,design,tasks,pricing,token-accounting}.md`。最新hashを `output/project-materials-spec-20260930/draft-revision.json` に保存。
- rootがspec/docs、selectionがwebfront設定slice、authがAPI調査/未接続初稿（削除済み）と独立UIreview、proofがmeter調査/独立仕様reviewを担当。ユーザー所有変更を巻き戻していない。
- 設定：関連43テスト＋最終残量ラベル12テスト、typecheck/lint/build成功。直前全体924テスト成功は最終ラベル修正前なので、最終全体成功とは表現しない。独立review関連33テストも成功。
- 実Chrome：account→Usage直接表示、一般保存後dialog保持、APIでen保存/ja復帰、Free used2/limit3と表示残1/33%一致、下書き保持、狭画面導線、console warning/errorなし。既存9serviceのwebfrontのみ更新。新規proof/有料model呼出し/Stripe変更なし。
- [設定確認記録](../output/settings-ui-20260930/result.md)、約22秒の低フレームレート実画面記録とdesktop/mobile画像を保存。token会計・添付・難問成功動画の代替としない。

## 残る具体的作業

料金A/Bと付与枠、取込失敗枠の扱い、保存/削除期限、全ページOCR品質・資源上限を確定。全工程の耐久meterとcall前予算強制、成功実績精算を実装・検証してからtoken UIへ接続する。資料取込/閲覧/出典/削除、画像の実モデル入力と独立QAは未実装。Stripe/Googleの外部設定は依然未設定。難しい可換代数の証明成功も未達。
