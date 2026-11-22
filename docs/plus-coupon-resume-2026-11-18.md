# Plusクーポンの本番対応再開

担当は[このCodexチャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)。進行は[#240](https://github.com/AtsushiHosaka/pals/issues/240)・[#244](https://github.com/AtsushiHosaka/pals/issues/244)・[#234](https://github.com/AtsushiHosaka/pals/issues/234)へ更新した。11月5日の候補と承認は履歴として保持し、期限切れのseq21を使わず再開した。

## 条件と担当

11月18日にオーナーは、個別100個、受入検証用1個と配布用99個、各コード1回を選んだ。[判断#436](https://github.com/AtsushiHosaka/pals/issues/436)に回答を記録した。認証済みアカウント単位で1回、引換後はPlusをUTC暦月1か月、各コードの発行から30日以内に引換できる条件である。コードは非公開保存し、外部へ送信しない。

本番操作は[唯一のlive担当](codex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2)へ集約する。先行は[#433](https://github.com/AtsushiHosaka/pals/issues/433)の正規復旧・所有権解放と、[#425](https://github.com/AtsushiHosaka/pals/issues/425)のUI配備である。今回の11月18日の再開作業では、別schema適用・本番切替・SSM・IAM・モデル呼出しを行っていない。共有US$1を消費していない。

## 実装を再開した理由

現行と次候補の固定API sourceにはPlusクーポン実装が未統合で、Webにも引換入口がなかった。通常のnativeリリース経路はsoftware-onlyのartifact同一性と5段階receiptを要求していた。古いPRやimageを配備するだけでは、現在の機能と正規更新条件を保てない状態だった。

保存された現admitted manifestと、今回のlive担当が用意した新sourceの場所を受領して照合した。source上のregistryは既存35段階と一致した。ただし、保存manifestやmainのgitlinkだけで、現在の本番DB・flag・クーポン件数を観測したとは扱わない。

## sourceごとの結果

| 領域 | PRと確認した範囲 | 本番に残る条件 |
|---|---|---|
| API | [API#125](https://github.com/AtsushiHosaka/pals-api/pull/125)。実Plus資格、暦月期限、発行・取消・引換、既存有料資格の保持、初期発行用CLI、専用schema profileを現在のsourceへ限定port。機能とrelease境界の独立レビュー、最終headの535件のexact CIが成功 | 正規nativeへの接続、実Cognito引換・Plus利用 |
| Web | [Web#93](https://github.com/AtsushiHosaka/pals-webfront/pull/93)。使用量設定の引換入口、有限Plus表示、既存4画面の利用枠再取得を接続。独立38件とexact CIが成功 | 現API/schemaとの同時受入、実アカウントの表示と保存・reload確認 |
| infra | [infra#189](https://github.com/AtsushiHosaka/pals-infra/pull/189)。35→36追加と、その後のsoftware更新を区別する閉じたprofileと検査を追加。専用CIの純粋14件はskipなしで成功 | #433と共有する正規consumer・fenceへの接続は調整待ち。未接続のためdraftを維持 |

APIの最終headは`93f6bb0a06cfca30821c1435c5944e470286243a`で、[exact CI](https://github.com/AtsushiHosaka/pals-api/actions/runs/44255799331)の535件・skipなし・必須ケース検査がすべて成功した。APIとWebはsourceレビューのready、未mergeである。

Webの先行baseへ追加されたCIと図のbrowser検査は、通常mergeでbyte一致のまま保持した。既存の引継ぎ質問のguard、認証epoch、navigation cacheを上書きしていない。クーポンのHTTP応答は閉じた形で検査し、コードをURL・browser storageへ残さない。資格は本当のbilling summaryを再取得し、画面だけでPlusを作らない。

初期発行用CLIは、1〜100人の上限、UTC暦月1か月、30日以内の引換期限を検査する。一般の発行SQLが持つ範囲は維持した。100個を各1回で発行する今回の計画と、DB全体に100人という上限を埋め込むことは区別する。

## 実DB回帰と後始末

新しいPostgreSQL serviceは起動せず、既存のDocker/Linux上のPG16を再利用した。テストprocessはmacOS上で実行した。最終の限定回帰は35件、failure・error・skipはいずれも0だった。実CLIによるテスト用100個別コードと100アカウントの引換、同じアカウントによる2個目の拒否、共有コードの100/108並行上限、暦月・期限、取消、権限、実admission拒否時のrollbackを含む。認証は既存のHTTP試験境界で隔離しており、実Cognitoの証明ではない。

検証前の3DB・32roleとmembershipを保存した。必要な一時roleとUUID名のテストDBだけを作り、終了後に回収した。最終inventoryは元の状態と全項目一致し、他clientと本チャットの残留資源はいずれも0だった。共有PG自体は停止していない。

別担当も、個別100コード、競合、既存Research、取消後の既存hold、UTC暦月、制限付きmigrationの6件を実PGで確認し、skipなしで通過した。元のinventoryへ完全復元し、共有PGは停止していない。途中で別担当のDB/clientを検知した際には触らず待機し、空いた後に再確認して検査した。この独立6件や535件のCIを足して、機能35件の分母を増やしていない。

途中の失敗も保存した。初回の不足artifact、ローカル認証方式に合わない試験接続、canonical model設定が足りないfixtureを、それぞれsource・環境の問題と分けた。Proの4件は未変更baseでも同じ失敗を再現した後、実canonical migrationを使うfixtureを整備して通過した。runtimeの条件や期待する結果は緩めていない。

広い535件の一括回帰は150秒でtimeoutしたため、全体成功とは記録しない。テストprocessの終了後に残った所有確認済みのDBを通常DROPで回収し、journalの一時roleだけを削除した。FORCE削除や、所有者が不明な資源の削除は行っていない。その後、残りと変更対象を分割して前述の35件を通した。局所の成功を未完の全体へ加算しない。

Webのexact CI初回は、2,229件成功・未変更のmaterial story 1件失敗だった。条件・assertion・timeoutを変えずに同じheadの失敗jobを1回再実行し、2,230件、appearance、processing stylesheet、先行の図browser gate、型、lint、production buildがすべて成功した。失敗原因を一過性の負荷と断定していない。単体・CI件数はモデル精度へ加算しない。

## 本番受入までの残り

#433のauthority consumerと競合するnative共通ファイルは編集を保留している。専用profileの純粋テストや実API byte契約が成功しても、canonical renderer・finalize・receipt予測・観測・復旧が接続済みとは扱わない。通常software更新の5段階検査を緩めて、6段階のクーポン追加を通すこともしない。

現在のローカル資格確認は、通常のproofを通せてもクーポンstorageを作る設定がない。正規local setupの後・API起動前に、検証対象のlocal DSNへcanonical coupon storageを明示適用し、localの機能flag・status・引換も調べる必要がある。production startupでDDLを実行して代替しない。

local helperは、接続を開くだけでなく`with connection.transaction():`の中で呼ぶ。実際のtransactionが開始済みであることをhelperが検査しており、この条件を省略しない。

本番受入には、過去にPlusクーポンを引換しておらず、有効な有料・無償上位資格もない実CognitoのFreeアカウントを使う。既存の有料資格を取り消して検証条件を作らない。検証用1個を引換し、実Plus枠・期限・Plus限定機能・保存とreloadを確認する。実際の証明・説明・追加質問の完了は、live担当が既存予算とrequest IDを管理し、二重実行しない。

本番コードは本チャットで発行していない。残り99個の配布を勝手に送信しない。DB appendとadmissionのcommit後は、旧35段階のimageへ戻すだけでは復旧できないため、正規の36互換の起動・復旧経路と実receiptをそろえて進める。

発行CLIはコードを一度だけstdoutへ返すため、実行時はhost内の非公開ファイルへ直接保存する。SSMの応答や公開ログへコードを出さず、件数・期限・一回性の検証結果だけを返す。結果が不明な発行を自動再試行せず、実際の保存結果とDBを照合する。
