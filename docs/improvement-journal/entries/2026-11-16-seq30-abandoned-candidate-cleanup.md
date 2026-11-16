# seq30の放棄候補の配置回収（2026-11-16）

有効化していない候補b976を、親24d8f95・infra ce084f3の正規observeとhost-cleanで回収した。直前観測のownerなし・製品とDBの変更なし・前版pin一致を確認し、実prepare受領書から導出したcontrol4・compute3ディレクトリだけを対象とした。

前版の参照先を保護する正規検査を通し、各roleの別readbackでgone_verified=trueを確認した。journalの各clean/readbackはintent・send・result各1組で、再送はない。受領書のapplication_mutatedとdatabase_mutatedはfalseだった。

品質台帳には配置回収の技術確認1件として1/1を追加する。ディレクトリ数や4工程を独立試行にはしない。費用と精密な全体wall時間は未測定。新しい有料質問や本番受け入れは実行していない。以前のapply失敗を成功へ変更しない。

実受領書のhashと、cleanup後のowner・製品動作を再観測していない限界は[配置回収記録](../../seq30-abandoned-candidate-cleanup-2026-11-16.md)に残した。
