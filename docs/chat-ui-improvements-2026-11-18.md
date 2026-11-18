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

1件目の題材は「すべての元の二乗が単位元になる群は可換である」。Luna lowで新規提出は1回だけ。同じ要求がanswered、Leanがverified、説明がcompletedまで進み、保存された結論と実画面の日本語の結論が一致した。回答と検証attestationのLean hashも一致し、再読み込み後も保存回答を表示した。

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

## 修正後のゲスト実API撮影

オーナーが追加1件を承認したため、[判断記録 #422](https://github.com/AtsushiHosaka/pals/issues/422)の範囲でゲストから1件だけ送信した。題材は「すべての元が自分自身の逆元である群は可換である」。Luna lowを使い、固定状態や固定応答は注入していない。Web・API・workerのソースと、既存のより厳しい予算guardは変更していない。

270撮影フレームのうち進捗がある219観測で、rootはすべてflex、アイコンと状態の間隔は13.99px、上端の差は最大2.33px、プレビューと本文列の左端の差は0pxだった。思考中、実際のdraft_plan、sketch_lean、コンパイル中を観測した。Draftではopacityが0.03から1へ変わる全体フェードも記録した。Leanが現れ始める瞬間は撮影区間外で、Leanの表示遅延や立ち上がり時間は測定していない。

同じ要求がanswered、Leanがverified、説明がcompletedになり、保存された回答・Leanソース・実検証receiptの結び付きが一致した。再読み込み前後の描画テキストhashも一致し、可換群の結論を表示した。終端のプレビューと時計はともに0件だった。追加分の計測費用はUS$0.010426、14provider呼び出し。2件の合計はUS$0.019005、24provider呼び出しで、予約額と実費は一致した。3件目は送信していない。

修正後の画像は`corrected-guest-thinking.jpg`、`corrected-guest-lean-preview.jpg`、`corrected-guest-answer-after-reload.jpg`。動画は`corrected-guest-generation.mp4`（15.64秒、81符号化フレーム）と`corrected-guest-fade-in.mp4`（6.28秒、33符号化フレーム）。それぞれ連続撮影区間の抜粋で、観測していない時間を補間していない。H.264、1,414×964で復号を確認した。219フレームを219試行には数えず、同じゲスト要求1件の観測とする。

撮影で実行したのは計2件で、合計US$1の承認範囲内。AWSと本番の変更は0回。

終了時は既存のローカル10サービスと専用PostgreSQLの計11コンテナがhealthyで、停止済みhelperとverifierの一時要求ディレクトリは0だった。scoped networkは2、volumeは3で、追加サービスはない。費用確定後のprovider呼び出しと費用の増加も0。既存サービスの期限ラベルには古い値が残っており、今回の期限保証とは扱わず変更していない。

## 追加の画面指摘と決定

オーナーは修正後の画像を見て、状態文と時計の微小な縦ずれを指摘した。Web #86の`52dc036`で状態行を中央揃えにし、PALSアイコン・状態文・タイマー・時計SVG・時刻の中心差を0.5px以内で検査した。旧CSSは2px差で失敗し、修正後はPC・375pxと2状態で成功した。折り返し時の重なりも検査した。typecheckと対象eslintは成功。これは分離ブラウザ回帰で、最新修正を実APIで撮影した証拠にはしない。

担当チャットで追加仕様を確認し、Leanは全体フェードに加えてコード全体がゆっくり明滅する方式を選んだ。文字を上下に動かす波と、Lean上を光が流れる方式は選ばなかった。生成中のチャット名は既存の光を維持する。完了ドットは未読の検証成功だけに付け、チャットを開くと消す。既読の恒久バッジや失敗時の色違いは追加しない。判断はIssue #419にも記録した。

チャット名の動きが分かるよう、1件目の実API録画からサイドバーだけを拡大した`sidebar-title-animation-real-api.mp4`を担当チャットへ掲載した。新しい生成や映像の補間は行っていない。この録画は中央揃えとLeanの明滅を追加する前の版である。

ブラウザを閉じても、サーバーが受理した検証は継続する実装である。要求を保存して永続outboxへ追加し、ブラウザ接続と独立した処理がキュー配送と結果反映を進める。切断はlong-pollの待受だけを終了する。ログイン利用者は保存したチャットから要求を再取得できる。ゲストの要求IDはsessionStorageに保存するため、同じタブの再読み込みは復元するが、タブ・ブラウザを閉じた後の復帰は保証しない。Cookieの48時間の有効期限だけでは要求を再発見できない。API `9829110`とWeb `ad93192`のコード確認による結論で、検証中にブラウザを閉じる実試験は行っていない。

拡大映像を見たオーナーは、チャット名にもっと滑らかに光が流れる動きを求めた。Web #87の`86a12f7`では、灰色の基底に柔らかい局所的な光を重ね、3秒の一定速度で流す。文字全体のopacityは1に固定し、周期の境目では光を可視範囲の外へ出す。Leanは表示時の全体フェードを維持し、コードだけをopacity 0.65〜1、3.2秒周期でゆっくり明滅させる。Draftと未検証ラベルは静止する。reduced motionと強制色では両方を止める。

この追加はChromium回帰で変更前の失敗と変更後3件の成功を確認し、対象unit 23件、typecheck、対象eslintも成功した。Web #86の`52dc036`は最新CI成功。Web #87の`86a12f7`はCI待ち。新しい実API生成は行わず、最新修正の撮影には追加1件の承認を確認している。既存の5fps程度の録画を、変更後の滑らかさを測る証拠にはしない。

ドットの既存API条件は「回答完了」で、未検証説明も含んでいた。オーナーが指定した「検証成功だけ」への絞り込みはIssue #423で別API PRとして実装する。チャットを開いて既読にする挙動は維持する。#88の質問引継ぎに関するレビュー指摘は、オーナーが連携を指示した別の担当チャットへ引き継いだ。同じ経路を並行編集しない。

## 本番反映への移行

オーナーの本番デプロイ依頼を受け、親Issue #425と候補PR #426で正規リリースを準備している。Web #85〜#89は通常mergeで統合した。merge後の`a163b43`で既存認証回復テストが1件失敗したため、PR #90で今回のprovider contextと初期化状態を同時に待つよう修正した。期待値やtimeoutは緩めず、製品コードも変更していない。`c585c60`のmerge revision自身の必須CIまで成功した。API #121/#122は`a3191b4`へ統合し、merge revision自身の必須CIも成功している。

APIの正規production画像は公開済み。Webも最終revisionに合わせて正規の再build・公開を行った。画像公開を本番反映とは扱わない。productionのcompute環境が途中表示の設定キーを許可しておらず、旧設定のコピーだけでは有効化できないことも確認した。infra PR #188で、strict booleanの明示設定をplanからproof workerだけへ渡す正規経路と回帰を追加中である。

前回 #410の保持ownerを正規read-only観測で確認し、具体的な4 read actions・3 resources・14:12:17 JST失効の後処理をオーナーが承認した。初回の`release-repair.py --operation grant --apply`は`exception_ReadTimeoutError`で拒否された。新しい台帳にはcycle行だけがあり、renewal intentもSSM dispatch記録もない。後続のexact IAM GETでは元の期限切れpolicyと同一で、新policy未適用を確認した。この1試行は失敗として品質台帳へ記録する。実サービス・traffic・DB admissionの変更は0である。

待ち時間の間に、正規grantが要求する残存900秒を切ったため、期限を黙って延ばさない。同じ範囲で14:40 JST失効の案を別ファイルとして検査し、オーナーの追加承認を待っている。元のplan・署名・failed記録は不変である。

この確認で、ローカル認証復旧時に変更した`local.env`が前回の凍結対象だったことが分かった。真正バックアップのhash一致を独立照合し、現行envを永久の候補専用pathへbytes保持、UI helperの参照を変更した後、旧凍結pathを真正bytesへ戻した。元の79参照は全件一致し、全33稼働containerのID・StartedAt・Env hash・mountと他runtimeファイルは前後不変だった。現在の認証設定や予算履歴を旧値へ上書きしていない。新しい資格確認用ディレクトリも同じサービスと台帳を再利用するための設定コピーとして準備し、停止後の正規continuity確認はまだ実行していない。
