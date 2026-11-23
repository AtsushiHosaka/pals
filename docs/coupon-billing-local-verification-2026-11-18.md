# クーポン準備処理と支払記録のローカル検証

[担当チャット](codex://threads/01a1aa9a-9621-7a10-a10b-5a2c46083d1a)。関連は[#240](https://github.com/AtsushiHosaka/pals/issues/240)・[#244](https://github.com/AtsushiHosaka/pals/issues/244)・[#250](https://github.com/AtsushiHosaka/pals/issues/250)。初期配布は[判断#436](https://github.com/AtsushiHosaka/pals/issues/436)の個別100個（受入検証1＋配布99、各1回）を維持する。

## 正規ローカル準備への接続

[親PR#444](https://github.com/AtsushiHosaka/pals/pull/444)のheadは`4231c89a0de5e69f5695f79ac873af90bc9a1e9a`。既定offの`--enable-plus-coupons`を、既存prepareから実際のDB bootstrap呼出しへ渡した。未対応・不一致のAPI sourceや設定は、stack停止前に拒否する。候補のlocal installer/currentをcallerのtransaction内で呼び、APIへ検証済みのliteral flagを渡す。既定のCompose出力は変更前とbyte一致し、従来のtoken設定を変えていない。

新14件と独立27件のsource/driver検査、最終headの必須CI2件が成功した。隣接検査の49件成功には新14件を含み、API submodule未初期化による既存skipが1件ある。件数を足して独立試行にしない。

追加で、実API `93f6bb0`のinstaller/currentへつながる新しい`apply_coupon_storage` callbackを、実PGの所有UUID DBで調べた。full mainの専用`/pals`接続条件は変更していない。

| 実callbackで検査した境界 | 結果 |
|---|---|
| transaction未開始での呼出し | 拒否 |
| 追加後にcallerが例外を返す | schema追加をrollback |
| commit後のcanonical current | 成功 |
| 同じ追加の再実行 | 既存状態を保持 |
| transaction内のdrift | 拒否し、caller rollbackで元へ復帰 |
| commit済みdrift | 自動修復せず拒否 |

6件すべて成功、skipなし。1.453984秒はcase内部の合計で、setup・cleanupを含むE2E時間ではない。新roleは作らず、元の3DB・32roleの属性と設定・membership・他client0を前後比較して完全一致を確認した。所有UUID DBだけを通常DROPし、process環境も復元した。

これは実callbackとSQLの接続検証である。full prepare、既存アプリの入替、起動後のクーポンschema/ACLの読取freeze、Cognito引換、実Plus利用、releaseの`local_pre`は確認していない。既存stackは別sourceなので置換していない。

## 支払receiptと定期処理の限定port

[API PR#131](https://github.com/AtsushiHosaka/pals-api/pull/131)は、クーポンAPI#125をbaseにした別branchのdraftである。現行系統に未統合だった旧receipt/report/maintenanceの依存一式を8新規sourceへ移した。現Webhook・`billing_operations`・通常route・production manifest・クーポンprofile・nativeの既存app bytesを保持した。公開captureやseed入口、新tracker、未確定の集計窓は追加していない。

最初の固定head `cd2a0c7adecc21da2c7aab0aeb55d7caa6633283`で、unit36件と実PG46件がskipなしで成功した。実PG46件はreceipt33、追加の原子的な保存1、maintenanceと公平性12である。実署名Webhookによる既存資格更新と、fixtureによるreceipt pending入力を分けた。provider照会はfixtureで隔離し、実Stripeや実支払の成功とは扱わない。

実PGでは、支払の同時保存・再送・binding、正の額のlive Stripe Plusと0円/test/手動入金の区別、unknown/pending、公平な1件ごとのclaim、同時排他、期限とSIGTERM後の子process/session/lock回収、13か月保持とACLを確認した。新role0、所有UUID DBのみを使い、各phaseの前後は元の3DB・32role・membership・他client0と完全一致した。共有PGやアプリは停止していない。

hostからの接続は、PGが観測するserver addressがloopbackではなく、旧local installerが本当に拒否した。条件を緩めず、既存API imageを使う一時Python検証containerを既存PGのnetwork namespaceへ接続し、本当の127.0.0.1で実CLIを実行した。アプリserverや新PGは起動していない。実applyとreplayの2呼出しが成功し、schema fingerprintとobject identityは再実行前後で一致した。これは一つの複合検証であり、2人の利用者試行とは数えない。

初回は、Dockerの小文字の不存在応答を検査用parserが認識できず、cleanup確認の記録に失敗した。installer本体の成功とは分け、`infra.result_parse_failure`で残した。所有nameの不存在、DB client0を再確認し、そのUUID DBを通常DROPした。parser修正後の再検証でも実apply/replayが成功し、container・所有DB・一時資格ファイルの不存在と元のinventoryへの復元を確認した。

最初のLinux CIは既存535件とそのgateが成功し、新82件は75件成功・7件失敗だった。最小の環境で起動したPythonのライブラリ解決に問題があった。正規interpreterの単一・絶対・実在するライブラリだけを渡し、不正な設定はspawn前に拒否する処理を追加した。親の任意のLD/PYTHON設定や無関係な資格情報は引き継がず、照合側にだけ明示した既存のbilling設定を渡す。途中の案では外側の検査CLIへ届かないP2を独立レビューが発見し、同じ処理を内外の起動へ接続した。

次の`376874e`でも既存535件は成功したが、新91件のうち11件はライブラリの厳格なpath検査でspawn前に停止した。どの配置条件が不成立だったかは、この時点の出力だけでは未確定である。local45件と独立45件の成功を、Linuxでの成立に読み替えない。

最終固定候補は`1781185486be54b3c358600e2b24898b18a52965`。実行中Pythonのbase prefix配下の閉じたlibraryだけを検査し、実配置の読取診断を加えた。最終CIではcompile-timeのlibrary directoryは不存在、runtime側の宣言libraryは存在すると実測し、最終候補の起動が成立した。local50件と独立の変更対象7件がskipなしで成功した。前候補の独立45件とは別証拠で、件数を加算しない。SQLと既存appの不変を照合し、先のMac実PG46件の証拠を継承する。両方の失敗原本を保存した。[最終Linux exact CI](https://github.com/AtsushiHosaka/pals-api/actions/runs/44265116602)は既存535件と新96件がすべて成功し、failure・error・skipはいずれも0、必須ケース名の検査も通過した。これはlocal限定の処理をLinuxで確認した結果で、本番captureの受入ではない。

## 本番との境界

クーポンの35→36と、将来の支払receipt用36→37はschema registryの段数であり、release sequenceではない。今回の支払portではregistryを36のまま保持し、local以外のcapture拒否も保持する。schema37だけを置いて本番収集や周期サービスを始めることはできない。

本番の正規復旧と切替は[#433](https://github.com/AtsushiHosaka/pals/issues/433)→[#425](https://github.com/AtsushiHosaka/pals/issues/425)の唯一のlive担当へ集約する。native共有hookのHOLD、正規36互換の復旧、freshなadmission/DB照合、実Cognito引換・Plus利用・保存/reloadは残る。今回のモデル呼出し、実Stripe、本番コード発行、本番切替はいずれも0である。

unit・CI件数は台帳の評価分母へ足さない。実callback6件、支払実PG46件、installer複合検証の初回記録失敗と最終確認を別々に記録し、数理モデルの精度や本番受入の成功率へ読み替えない。
