# 11月17日の受付復旧とIssueの修正

担当セッションは`codex://threads/01a1e863-d84c-7e82-bedb-156dd25d871e`。既存の未コミット変更は保全し、実装と記録には独立worktreeを使った。本番への追加配備は行っていない。

## seq30の受付復旧（#410）

[緊急復旧の記録](https://github.com/AtsushiHosaka/pals/issues/410#issuecomment-6941642990)に、前セッションでの承認と実行結果を記した。オーナーが承認した提案はSHA256 `a7d6562f24758ca6926dabbf55cd1ca4dd261e54fccec0f9c70fc9f4c8de1698`、対象候補は`1be72c60b705328c30b61c198fa037f6b6ef14dfd0f9ed92aa118914bf543f15`。

設定済みproof・assessment・verifierと接続先の実診断成功を確認し、既存の受付先1台だけを再登録した。読み戻しで1件・healthy、公開トップページでHTTP 200を確認。既存Chromeタブを再読み込みすると公開ホーム画面と入力欄が表示された。

この1回の復旧観測を台帳へavailabilityとして記録する。healthy、HTTP応答、画面表示を別々の独立試行には数えない。署名・認証・稼働設定・release台帳・凍結driver・IAM権限は変更していない。元のhealth-light失敗と停止15分超過を保持する。回答生成から保存・表示・履歴までの受け入れ、release ownerの解放と正規cleanupは未完了であり、acceptedとは扱わない。

## モバイル設定のフォーカス復帰（#285）

開始点はWebの承認済みブランチ`codex/sidebar-inline-math-20261031`の`86c946b34ebb14fa9b0f8742d6de2d17ab55aa70`。修正は[Web PR #83](https://github.com/AtsushiHosaka/pals-webfront/pull/83)、候補は`0c6d8b5`。

Settingsを開く処理が、mobile drawerの閉鎖と同じ更新にまとめられていた。SettingsがSidebarより前に配置される実際の画面では、drawer内の消えるボタンがopenerとして記録される。`runMobileCommand`で閉鎖を同期確定し、既存のinert解除とworkspace triggerへの復帰が完了してから次の画面を開くようにした。デスクトップの経路と設定機能は保持している。

実ChatSidebarとModalを本番と同じ配置順に置いた一時ローカル画面を、Chromeで操作した。Settingsの内容と認証・APIはこの確認の対象外で、実ログイン済みSettings全体の検証とは区別する。旧コードの375×812・Escape終了では`document.activeElement.tagName === "BODY"`を再現。修正後は同じ幅のEscapeと閉じるボタンの両方でworkspace triggerへ戻り、inert属性が解除された。通常幅では従来のaccount menuへ戻った。旧1件の失敗と修正後3経路の成功を、それぞれ別行に記録する。小規模なUI操作の観測であり、数学の精度や継続的な成功率ではない。

`vitest run tests/unit/chat-sidebar-mobile.test.tsx tests/unit/modal-accessibility.test.tsx`は17/17成功。新規mobile回帰2件は旧コードで失敗した。独立レビューは指摘なし、sidebar unit14/14も別途再実行された。`npm run typecheck`と`npm run lint`も成功。単体テスト件数は品質台帳へ加算しない。

依存はlockfileどおりに`npm ci --ignore-scripts --no-audit --no-fund`で準備した。最初に再利用を試みたnode_modulesは候補とバージョンが異なり、Turbopackのsymlink制約でも起動できなかったため採用しなかった。ローカル確認画面とNextが変更した生成型定義は成果物から除き、サーバーを終了、確認用タブを閉じ、viewportを元に戻した。

Webの既存workflowはGitHub-hosted指定のため、有料枠を使わない指示に従いcommitにskip指示を付けた。PR作成後のbranch run一覧は0件。自前runner移行PR #71は未統合であり、この候補のrequired CI、native 200% zoom、本番確認は未実行。PRは下書きのまま、merge・deploy・Issueの完了扱いはしていない。

## 回答反映とキュー送信の分離（API #111、親#380）

開始点は承認済みAPIブランチ`claude/seq28-api-response-language`の`08cf8acc6f6ea9059445bdd4e82e5c160e99cc5f`。修正は[API PR #118](https://github.com/AtsushiHosaka/pals-api/pull/118)、候補は`c999de02ab3333d4c08cd7eccb2e64c68f238034`。詳細は同PR内の`docs/engineering-notes/dispatch-apply-isolation-20261117.md`にある。

要求の送信、linked jobの送信、完了結果の反映を3つのタスクへ分けた。通知と待機を分離し、送信の遅延・通常例外が反映を止めないようにした。送信は各recover呼び出しにつき最大4並列で、既存DBのclaim・token・lease条件を保持する。終了時には所有タスクをcancelしてawaitする。timingには反映件数、反映処理時間、前回の処理終了からの待ちを記録する。ジョブ完了から画面表示までの遅延とは区別する。

新規スケジューリング回帰4件は旧ソースで失敗した。修正後の最終確認はuv.lockへ揃えた専用venv、Python 3.12.13、FastAPI 0.140.2で行い、unit77件と実PostgreSQL9件が成功、失敗・skipは0。ruffと対象2sourceのmypyも成功した。実PostgreSQLの新規3件は結果反映、request claim、job tokenの競合防止。残る6件は既存の結論保存回帰である。rootは最終XMLの86件・失敗0・error0・skip0と実venvのFastAPI版を照合した。

実DBの初期検証はfixture不足で失敗し、正規migration chainへ修正してから成功した。既存の共有venvは変更していない。独立レビューは指摘なし。ただし、完了jobはfixtureで準備し、queueのテスト境界を制御している。実SQS・Lean・モデル・認証・本番画面の通し検証ではない。単体・統合テスト件数を品質台帳の製品評価へ加算しない。

Issueの性能条件「20秒の送信遅延時にも、反映p95の増加が1秒未満」は未測定。PRは下書きで、正確なheadのself-hosted CIは作成直後に実行中・待機中だった。merge・deploy・Issueの完了扱いはせず、p95の実測と本番受け入れを後続作業として残す。本作業では新規コンテナ・有料モデル呼び出し・AWS変更を行っていない。
