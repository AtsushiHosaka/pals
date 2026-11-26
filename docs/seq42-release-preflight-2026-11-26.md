# seq42の配備前検証

作業名seq42の前任は、seq41の本番復旧で受入が完了した候補。署名済みマニフェストの番号は38で、今回の次候補は39になる。直近の本番受入記録とアーカイブの署名済みファイルを照合した。本番ホストの現在の状態は読み取っていない。[本番受入記録](https://github.com/AtsushiHosaka/pals/issues/475#issuecomment-7154811126)。

独立レビューと対象headの重いCIを確認し、pals-infra #399、#410、#415をmainへ取り込んだ。infraの `390b1961` を固定した親の準備コミットは `def3692b`。全submoduleを該当コミットで初期化した。[親のソース準備PR #530](https://github.com/AtsushiHosaka/pals/pull/530)。

前任のAPI、Web、worker、verifierのイメージダイジェストをすべて継承し、正規の `release-prepare` で番号39のマニフェストを生成した。署名なしの構成17項目を再検査し、すべて通過した。変更イメージは0件で、ローカル準備ではレジストリへ接続しない設定を明示した。候補ハッシュは `decbaf3399c7766b0572a4c083906d8e9d2882fae5e59dba38ca16d8005fcd48`。署名前の計画入力も `release-run candidate-plan-input` の生成と再検査を通過した。

引き継いだサイトの通知窓は600秒。現行の実装では通常切替の予算552秒と余裕60秒の計612秒で拒否される。補償経路は既知の工程だけで785秒、待機候補に切り替える経路は既知の工程だけで922秒。復旧、前任のヘルスおよび待機切替の実測は未取得。#403の例外はマニフェスト番号42を比較するため、この候補39には当たらない。[配備の承認条件 #509](https://github.com/AtsushiHosaka/pals/issues/509)。

候補39と署名済みの前任を入力にした通常配備のローカル実走では、実イメージを使う前任環境の11検査が202.1秒で通過した。続くホスト準備で `observation_predecessor_state_differs_from_the_plan_input` が出た。通常配備の観測入力に前進修復用の項目が入っていたため、生成したplanによる切替には進まなかった。

通常配備の観測入力を修正して再試行すると、前任環境の11検査は199.0秒で通過した。今回はコントロールホストの準備まで進み、`native_preparation_refused_retain_versioned_files` で停止した。両マニフェストから実際にレンダリングしたホスト準備コードで、イメージをすべて継承する更新を拒否することをオフラインで再現した。直接の前任が稼働中で、スキーマを維持したまま親またはinfraの固定コミットが変わる場合に限り、準備処理と条件をそろえる修正を起こした。[観測入力の修正 #417](https://github.com/AtsushiHosaka/pals-infra/pull/417) · [ホスト準備の修正 #418](https://github.com/AtsushiHosaka/pals-infra/pull/418)。

APIのロックファイルでローカル検査環境を作り直し、正規の署名前ゲートを再実行した。クーポン契約、実APIイメージ、対象コミットのCIは通過した。41項目中6項目が拒否された。通知窓の通常切替予算超過、復旧と前任ヘルスの未計測、ホスト事前検査の未取得、対象環境の設定不足、待機候補の未指定が残った。ゲート実行では本番に接続していない。

配備記録を照合すると、主候補AはAPI `de420ea234fd1a84ef46aa410e2cb13d9cb092f3` を新しいイメージで配備する計画だった。4イメージを継承した上記候補39は、ツール変更の事前検証に使った。主候補Aが組み上がったら、正確なAPIイメージを含む候補の署名前ゲートと通しリハーサルを実施する。[主候補Aの手順](https://github.com/AtsushiHosaka/pals/issues/509#issuecomment-7182300080) · [APIの固定コミットの回帰CI](https://github.com/AtsushiHosaka/pals-api/actions/runs/45594949051)。

主候補AのAPIを正規のpublisherでlinux/arm64向けにビルドした。固定コミットの独立レビューで重大な指摘はなく、関連ユニットテスト222件とクーポン契約4件が通過した。Docker上でも非特権・読み取り専用・ネットワークなしで `app.release.contract` を実行し、17の搬送経路を記述する契約を取得した。APIイメージはローカルにある。親 `303301f`、API `de420ea`、infra `390b196` の組み合わせで `make release-source-checks` は通過し、infraの回帰コーパスは47ケースがすべて有効で55テストが通過した。独立レビューとCIの根拠は [親PR #530](https://github.com/AtsushiHosaka/pals/pull/530) を参照。

窓の30分特例を実装する #403 はマニフェスト番号42だけを許可する。直近の署名済み前任38から作る候補は39なので、実際の候補だけを対象にする修正が残る。補償確認を省かず、復旧の時間、待機候補の署名と切替を別に確かめる。[例外のオーナー承認](https://github.com/AtsushiHosaka/pals/issues/509#issuecomment-7182144771) · [#403の確認結果](https://github.com/AtsushiHosaka/pals-infra/pull/403#issuecomment-7188700432)。

主候補AのローカルAPIイメージを組み込んだ検証専用マニフェスト `10d97f7b…` で、前任38からのOrbStack通常切替が完了した。前任の11検査は205.6秒。両ホストの準備、配置、計画の再検証を通過し、切替コントローラの30工程は349.6秒で完了した。通信先の再登録、オーナー解放、後片付けはいずれも成功。リハーサルの通知窓は1,500秒、クラウドと受入ランナーは隔離環境用だった。実際の本番通知窓、障害時の復旧、本番ブラウザ受入には対応する証跡が要る。[通常配備のリハーサル #417](https://github.com/AtsushiHosaka/pals-infra/pull/417) · [承認前後の復旧診断 #419](https://github.com/AtsushiHosaka/pals-infra/pull/419)。

承認前の復旧試験の初回は、PostgreSQLのロックを先に保持していたため、通信切離しより前の安全確認が `predecessor_not_idle_and_current` を返した。切替も復旧も走らず、復旧時間の計測には含めない。承認要求の時点で障害が起きるよう、試験の仕掛けを調整する。[復旧診断 #419](https://github.com/AtsushiHosaka/pals-infra/pull/419)。

承認後の初回は、候補の承認後に `finalize` の一度限りの障害が発生し、コントローラはオーナー権限を保持した。現行コードの `owner_retained_no_standby` 経路では、候補の承認が確認済みなので補償前の追加観測を行わない。診断が旧経路の追加観測を要求したため、`--reconcile` には進んでいない。この初回は前進復旧の通過に数えない。[復旧診断 #419](https://github.com/AtsushiHosaka/pals-infra/pull/419)。

承認前の障害を承認要求に絞った再試行は成功した。実APIが隔離PostgreSQLのロックで承認を拒否し、ロックを解除した後、前任のDB状態、両ホストの元のコンテナID、通信先の再登録、通知窓と一時ポリシーの解除、切替ロックの解放を確認した。切替コントローラは402.2秒、通信切離しから再登録までは255秒、補償全体は198秒。生のジャーナルと凍結計画のハッシュを照合し、計測記録 `4fc58dfb1e6d59a87100e0ac4fda80e2b06842686ca628cdab6233023407d796` を正規ツールで再現した。`restore` は142,139ミリ秒、`previous-health` は7,363ミリ秒だった。隔離環境の実測を署名ゲートの予算へ反映する変更は #398 でレビュー中。[復旧診断 #419](https://github.com/AtsushiHosaka/pals-infra/pull/419) · [測定値の接続 #398](https://github.com/AtsushiHosaka/pals-infra/pull/398)。

承認後の障害を起こした再試行も通過した。`finalize` の一度限りの失敗とオーナー権限の保持を177.0秒で確認し、同じ試行の `--reconcile` は221.0秒で前進復旧を完了した。候補AのDB承認、両ホストの新しいコンテナ、正常な通信先、切替ロック・一時ポリシー・通知抑止ルールの後片付けを個別に読み戻した。検証対象 `77d04f7` でローカル回帰251件と重いCIの4ジョブが通った。現行のコントローラは自動の待機候補切替を行わず、今回は同じ主候補へ前進復旧した。[診断PR #419](https://github.com/AtsushiHosaka/pals-infra/pull/419) · [回帰CI](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45800434852)。

本番切替の前には、実候補に対応する通知窓の特例、復旧計測を使う署名判定、待機候補Sの作成・署名・切替、本番環境とホストの確認が残る。Sが前任のAPIとAの親コミットを同時に使う場合、現行の候補準備が親のsubmodule固定と一致せずに拒否する。配備条件を満たすまでは、イメージ公開、署名、本番切替は未実施。[待機候補の確認 #402](https://github.com/AtsushiHosaka/pals-infra/pull/402#issuecomment-7189103153) · [配備Issue #509](https://github.com/AtsushiHosaka/pals/issues/509)。

## 11月26日夜の追試

現行の通知窓の条件を取り込んで承認前の復旧を再実行した。初回は前任のAPIソースを参照できず、PKI検証で停止した。正確なコミットを持つチェックアウトを指定した再試行では、実APIが隔離PostgreSQLのロックで承認を拒否し、前任への復旧が完了した。[診断PR #424](https://github.com/AtsushiHosaka/pals-infra/pull/424)。

切替コントローラは367.5秒。通信先の切離し完了から再登録までは227.9秒、補償の決定から再登録までは198.0秒だった。DBの承認が前任のままであること、両ホストのコンテナIDが元に戻ること、通信先が正常になることを確認した。切替ロック、一時ポリシー、通知抑制も解除された。

再試行の `restore` は148,338ミリ秒、`previous-health` は8,418ミリ秒。凍結計画とログのハッシュを照合し、生ジャーナルから計測記録 `e9c6a99ccbf7bfb1b0a3a8fc1dd39d0fcf09efb1cb042aa960b12f2dab8c5141` を再現した。現行の換算は隔離環境の受入検査で最大798倍となり、換算した復旧時間は30分の例外枠を超える。待機候補Sへの切替時間も未計測。[計測と自動切替の統合PR #426](https://github.com/AtsushiHosaka/pals-infra/pull/426)。

Sが同じ実イメージを保持する場合のホスト準備の修正をmainに取り込んだ。独立レビューと必須CI4件が通過した。Sの署名前に使うP・A・Sの照合と、製品ソースを実際に動かす検証は個別にテストした。本番用のSの通し受入と、Aの署名前にSの実走を照合する工程が残る。[ホスト準備 #423](https://github.com/AtsushiHosaka/pals-infra/pull/423) · [署名前準備 #425](https://github.com/AtsushiHosaka/pals-infra/pull/425) · [ソース検証 #427](https://github.com/AtsushiHosaka/pals-infra/pull/427)。

待機候補Sをローカル鍵で署名し、稼働中の前任Pの実イメージを使って両ホストに配置した。前任の構築204.4秒で11検査が通過し、最終計画の再検証はドライバー起動から89.1秒で完了した。配置後もDBはPを承認し、通信先と元のコンテナIDは変わらなかった。この実走は配置までを確認した。[待機候補の配置診断 #428](https://github.com/AtsushiHosaka/pals-infra/pull/428)。

本番の読み取り事前検査は、設定済みのAWS SSOセッションが期限切れのため開始できなかった。seq42、seq43の本番切替はいずれも未着手。
