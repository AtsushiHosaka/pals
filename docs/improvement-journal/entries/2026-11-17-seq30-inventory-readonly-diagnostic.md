# seq30の実native inventory読取診断（2026-11-17）

live source13be88fcで、読み取り専用probeを三つの専用stateから実行した。各journalのintent・send・resultは1組、SSM command IDは異なり、三つともprobe_completed・code/error class none・app/DB変更なしだった。閉じたJSONが同じhashになるため、結果hashだけで実行回数を判定していない。

判断は、読み取り診断の結果を採用し、元のtuple拒否の根因は未確定として追加調査へ進むこと。過去StartedAtがなく再起動は否定できず、既存CloudWatchのlogStreams0件から当時の正常性も証明できない。release acceptedや本番受け入れではない。

最終e4adbffのoffline検査は5 suites・220 unique testsが通過した。CLI bytesはliveと同じだが、Hの有限語彙とCI groupingは後追加であり、最終head全体のlive検証とは区別する。PRの統合・必須CI・レビューも別に確認する。

実読取bundle1件の1/1を記録し、中の3観測や220 testsを製品・数学の試行へ加算しない。新しいpaid/model callsは0、local台帳は83 calls・292673μUSDを保持。実費総額と診断全体時間は未測定。source、限界と証拠hashは[診断記録](../../seq30-inventory-diagnostic-2026-11-17.md)、品質台帳IDは2026-11-17-seq30-inventory-readonly-diagnostic。

仮説に当たる狙いは、切り替え・有料質問・host配置変更なしで既存の保護済みprobeを実行できるか確かめることだった。これは実施後の説明であり、事前登録した比較実験ではない。モデル・修復上限・カード数は対象外である。
