# seq30の初回admission-status失敗（2026-11-17）

狙いは、#404修正を統合した新候補085d9d03について、利用停止前の正規gateを通して切り替えることだった。親f00e5fae・infra847d515で、計画DATAのpreflight有効期間を1050秒とし、通知1500秒・利用停止上限900秒を維持した。

実applyは初回admission-statusが57.390秒で失敗した。cleanup中の再確認は101.734秒でpassedとなり、owner解放と通常・通知cleanupは完了した。quiesce・通信除外・通知開始・admissionは未実行で、利用停止時間を0秒と測定したとは扱わない。技術bundle n=1、結果0/1を保持する。

保存control応答はexact_native_current_tuple_unresolved、predecessor/contextのFileNotFoundErrorを示した。不足ファイル名と実原因は未確定で、分類はunclassifiedとする。#407のstate削除・復元とreaderのlock不一致は、結果後の静的調査で立てた仮説であり、事前仮説や確定原因とは書かない。以前のf20失敗の原因とも同一視しない。

判断は追加測定で、ローカル再現と修正検証まで配備を止める。同じ実capture7の正規再観測を追加の製品試行にせず、新paid送信0件・既存費用再計上なしとする。総費用と性能改善量は未測定、本番回答の受け入れは未検証である。

[実結果と保存根拠](../../seq30-current-tuple-failure-2026-11-17.md)、[#407](https://github.com/AtsushiHosaka/pals/issues/407)、品質台帳IDは2026-11-17-seq30-current-tuple-failure。
