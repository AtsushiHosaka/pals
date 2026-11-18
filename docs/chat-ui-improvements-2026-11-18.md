# チャットUI改善の実装・実API確認（2026-11-18）

オーナー指定の4項目を別PRに分けた。toggle配置は対応済みとして変更しない。撮影には固定状態・固定応答を使わず、実APIで動く画面だけを使う。

担当はCodex。担当チャットはcodex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2。

| 対象 | 変更 | Issue | PR |
|---|---|---|---|
| 新規チャット | 不要な案内文を削除 | [#417](https://github.com/AtsushiHosaka/pals/issues/417) | [Web #85](https://github.com/AtsushiHosaka/pals-webfront/pull/85) |
| 進捗 | PALSアイコン、状態、時計を整列 | [#418](https://github.com/AtsushiHosaka/pals/issues/418) | [Web #86](https://github.com/AtsushiHosaka/pals-webfront/pull/86) |
| 途中表示と動き | Lean全体のフェードイン、タイトル上の光、ゲスト対応 | [#419](https://github.com/AtsushiHosaka/pals/issues/419) | [Web #87](https://github.com/AtsushiHosaka/pals-webfront/pull/87) |
| チャット移動 | 一覧と既知のプランを保持して再取得 | [#420](https://github.com/AtsushiHosaka/pals/issues/420) | [Web #88](https://github.com/AtsushiHosaka/pals-webfront/pull/88) |

Web #87は#86をbaseにした積み上げPR。ゲストの途中表示には[API #121](https://github.com/AtsushiHosaka/pals-api/pull/121)とworkerの有効化が必要で、APIを先に配備する。ゲスト用のチャット一覧は新設しない。本番には未反映。ゲストAPIはcookieによる本人所有確認とclaim期限の検査を維持し、opt-in時だけ途中内容を返す。要求とjobを同じSQL snapshotで読み、終端後の途中表示や内部context・claim IDの返却を防ぐ。

## 実装とローカル環境

Webの開始ソースは`6dea87e`、APIは`eebb1ab`。APIの変更は`9829110`、Webの最終統合ソースは`ad93192`。各PRは独立した範囲を保ち、#87への取り込みは通常のmergeで行った。force pushはしていない。

時計は要求のサーバー作成時刻を使い、段階切替でリセットしない。途中内容は未検証と明示し、compile/repair中は直近の内容を保持して、終端・所有権喪失で消す。動きを減らす設定・強制色では光を止め、生成中の静止アイコンを出す。チャット移動の保持データはアカウント・認証epochで分け、永続ストレージへ保存しない。既知のプランがあっても、最新の利用枠の再取得まで送信を許可しない。

最初の実API確認では通常ログインが失敗した。ローカルCognitoのpoolとclientが0件で、実認証APIもResourceNotFoundExceptionを返した。オーナーは、ローカル復旧と途中表示の接続・有効化、モデル費用合計US$1以内で証明1件を生成して撮影することを承認した。

既存ヘルパーで認証を復旧し、APIを標準Dockerfileで更新した。記法設定503は未作成テーブルが原因で、正規の限定マイグレーション後に200を確認した。期限切れのmTLS・provider TLSも正規ヘルパーで更新し、実sandbox経由のLeanコンパイルが9,801msで成功した。workerは実ソース`146ecf2b`で途中表示が有効であることを確認した。

既存のローカルWebサービスも`ad93192`のgit archiveと標準Dockerfileで更新し、配信JSの公開認証設定・実API接続先・ソースrevisionを照合した。再読み込み後も通常認証で保存チャットと入力欄を表示できた。追加サービスは作らず、一時Webプロセスは停止した。過去の資格確認subjectや本番を変更せず、古いmanifestヘッダーを今回の検証へ流用しない。復旧前の私用バックアップは保持した。

## 実APIで確認したこと

題材は「すべての元の二乗が単位元になる群は可換である」。Luna lowで新規提出は1回だけ。同じ要求がanswered、Leanがverified、説明がcompletedまで進み、保存された結論と実画面の日本語の結論が一致した。回答と検証attestationのLean hashも一致し、再読み込み後も保存回答を表示した。

予算guardの全予約解放後の差は8,579µUSD、計測費用はUS$0.008579。10回のprovider呼び出しは、この証明1件の内訳である。請求額とは区別する。過去使用量のリセットやguardの緩和は行わず、承認上限より厳しい既存の残枠を保持した。

生成中に、薄い未検証Leanとタイトル上の光を実画面で確認した。動画は45撮影フレームから作った8.76秒の抜粋で、全生成時間の記録ではない。新規チャットへの移動も撮影し、45観測すべてで元のチャットが一覧に残り、一覧の読み込み表示は0回だった。不要な案内文は0件で、入力欄・モデル選択・添付・数式・共有・削除の入口を保持した。1回の操作を45独立試行には数えない。

| 撮影成果物 | 内容 |
|---|---|
| `new-chat-real-api.jpg` | 復旧したローカルWebの新規チャット |
| `new-chat-real-api.mp4` | 一覧を保持した新規チャットへの移動、9.40秒 |
| `real-lean-preview-before-alignment-fix.mp4` | 生成中のLeanと光。下記の整列修正前 |
| `verified-answer-after-reload.jpg` | 実検証済み回答の再読み込み後 |

成果物は`output/playwright/chat-ui-20261118/`に保存して担当チャットへ掲載し、Gitにはコミットしない。動画は撮影時刻差から長さを決めたH.264、1,414×964、46符号化フレームで、いずれも復号を確認した。

## 撮影で見つけた不具合と修正

進捗のPALSアイコンが状態行の上へずれていた。会話全体の汎用CSSが、ProcessingStatusのflexをgridへ上書きしていたためである。境界をdivからsectionへ変更し、全アプリCSSとChromiumで変更前の失敗を再現した。修正後はPC・375px、思考中・コンパイル中の4条件で、同じ行の配置・14px間隔・本文列の整列・横溢れなしを確認した。別担当の独立レビューと独立実行も成功し、この回帰を必須Web CIへ追加した。

この配置試験は表示用データを使う分離試験であり、修正後の実API撮影の代用にはしない。最初の実API録画は整列修正前と明示して保持する。完了済みの要求を巻き戻したり、固定表示へ置き換えたりして撮影しない。

## 検証結果と残る範囲

統合作業ソースのWeb回帰2,195件、typecheck、lint、build、全CSSのブラウザ回帰が成功した。元の3hooksではチャット移動の新規回帰4件が全件失敗し、修正後は対象35件が成功した。APIは実HTTP・専用PostgreSQL5件を含む35件を担当と親担当が独立確認し、一時DB一覧は前後一致した。保存ジョブ状態がfixtureのAPI試験を、実モデル画面とは扱わない。

再実行する基本コマンドは、Webの`npm test -- --maxWorkers=2`、`npm run typecheck`、`npm run lint`、`npm run build`、配置の`npx vitest run --config tests/browser/processing-status.config.ts`。APIは専用一時DBを指定し、`python -m pytest tests/unit/test_guest_progress_preview.py tests/unit/test_guest_proof_request_sources.py tests/integration/test_guest_progress_preview.py`を実行した。APIのRuffと対象ソースのmypyも成功した。

最終CI途中のWeb #86の`84f61f2`は、既存の節質問テスト1件で失敗した。正確なPRソースの単独16件では成功し、別の全体実行でも同じ失敗は再現しなかった。本体の選択処理は同期であり、原因は未確定。同じ期待入力欄をfindByRoleで取得する1行だけを追加し、タイムアウト・期待値・送信内容・製品コードは変えていない。製品不具合の修正とは扱わない。最新の`b626934`は全必須CIステップが成功した。#87の最新head`471ec42`も、全CSSの配置回帰を含む全必須CIステップが成功した。#85・#88・API #121の変更していないheadも成功済みで、実装5PRの最新CIはすべて成功している。

初回ローカル試験のloopback制約は、権限のある同じ試験で解消した。別の全体試験での環境制約や既存テストの失敗もログへ保持した。APIの既存POST answersテストのnotifier不足は開始ソースでも再現し、今回解消したとは扱わない。単体テスト・CI件数は品質台帳の評価行へ加算しない。

整列修正後の生成中の実API撮影と、ゲストの実モデル画面は未確認。オーナーには、合計US$1の上限を保ち追加1件だけ撮り直すか、追加生成せず現在の録画と修正内容を確認するかを質問した。回答まで追加送信しない。AWSと本番の変更は0回。

終了時は既存のローカル10サービスと専用PostgreSQLの計11コンテナがhealthyで、停止済みhelperとverifierの一時要求ディレクトリは0だった。scoped networkは2、volumeは3で、追加サービスはない。費用確定後のprovider呼び出しと費用の増加も0。既存サービスの期限ラベルには古い値が残っており、今回の期限保証とは扱わず変更していない。
