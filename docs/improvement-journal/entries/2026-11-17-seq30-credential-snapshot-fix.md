# seq30の資格snapshot読み取り修正（2026-11-17）

狙いは資格brokerのstate公開中にreaderが欠損区間を読む競合を防ぐこと。実brokerとreaderの局所再現で成立した競合に対し、既存lockの共有取得と、旧ownerに対する限定的なguarded loadで安全に読むという仮説を検証した。本番の実missing filenameやf20失敗の原因は未確定のままとする。

infra185の15c54e2でsource3か所と専用testを修正し、正規goldenを更新した。bad847の純archiveでは同じ新12件がRED、修正版は新12・native123・render63の合計198件が2.167秒でGREEN、skip0だった。実flockと模擬STS/ownershipの境界で、provider・AWS・本番hostを使った検証ではない。

判断は対象技術検証の成功を採用し、child通常merge・必要なexact CI・親統合と実リリースgateの確認へ進むこと。台帳は技術bundle n=1の1/1を追加し、unit件数を数学や製品成功率の分母にしない。元cycle0/1と初回fixture setup failureは保持する。未使用候補085dの正規cleanupは後続運用の事実として根拠を併記し、別の製品試行に数えない。

本番はseq29のままで、利用停止工程は未開始。新paid取得はなく、費用・時間短縮量は未測定、全7予行の10分未達も保持する。根拠hashと残る確認は[修正記録](../../seq30-credential-snapshot-fix-2026-11-17.md)。品質台帳IDは2026-11-17-seq30-credential-snapshot-fix。
