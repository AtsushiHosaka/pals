# seq30の初回admission-status失敗（2026-11-17）

狙いは、#404修正を統合した新候補085d9d03について、利用停止前の正規gateを通して切り替えることだった。親f00e5fae・infra847d515で、計画DATAのpreflight有効期間を1050秒とし、通知1500秒・利用停止上限900秒を維持した。

実applyは初回admission-statusが57.390秒で失敗した。cleanup中の再確認は101.734秒でpassedとなり、owner解放と通常・通知cleanupは完了した。quiesce・通信除外・通知開始・admissionは未実行で、利用停止時間を0秒と測定したとは扱わない。技術bundle n=1、結果0/1を保持する。

保存control応答はexact_native_current_tuple_unresolved、predecessor/contextのFileNotFoundErrorを示した。不足ファイル名と実原因は未確定で、分類はunclassifiedとする。#407のstate削除・復元とreaderのlock不一致は、結果後の静的調査で立てた仮説であり、事前仮説や確定原因とは書かない。以前のf20失敗の原因とも同一視しない。

判断は追加測定で、ローカル再現と修正検証まで配備を止める。同じ実capture7の正規再観測を追加の製品試行にせず、新paid送信0件・既存費用再計上なしとする。総費用と性能改善量は未測定、本番回答の受け入れは未検証である。

[実結果と保存根拠](../../seq30-current-tuple-failure-2026-11-17.md)、[#407](https://github.com/AtsushiHosaka/pals/issues/407)、品質台帳IDは2026-11-17-seq30-current-tuple-failure。


2026-11-17追記: 最初のmetadata診断は期待mode0755の誤りで拒否され、失敗intentとjournalを保存した。installerどおりの0700を診断側へ指定し、別stateの限定読み取りでread_completeを得た。hostのmode変更はなく、installed broker hashは凍結sourceに一致した。broker実行区間と失敗control inventoryの時刻は重なった。実broker・reader・real flock、偽STSとOS ownership模擬を使った局所再現ではstate.unlink窓のFileNotFoundErrorが成立したが、本番の不足ファイル・因果は未確定である。[追記の保存根拠](../../seq30-current-tuple-failure-2026-11-17.md#2026-11-17追記broker時刻の限定的な読み取り)を追加し、元cycle0/1と分母・費用を維持する。

局所fixtureの初回はtemp親UID模擬不足のsetup failureだった。修正後の有効再現1回で欠損中の失敗とpublish後の成功を確認した。偽STS3呼出し・実provider0・実runtime書込み0で、setup不備を製品REDとせず、元の技術分母を維持する。
