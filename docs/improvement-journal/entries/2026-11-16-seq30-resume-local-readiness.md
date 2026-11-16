# seq30再開時のローカル依存先準備（2026-11-16）

- 指標: 有料処理前の依存先準備。数学の精度・本番成功率・時間短縮は測定していない。
- 仮説: 期限切れTLSを正規更新し、既存予算台帳と正しい本番digestを保持してprepareをやり直せば、認証確認や課金の前に依存先の状態を確認できる。
- 変更: 親24d8f95・infra ce084f3を使用。正規TLS更新と正規prepareを実行し、subjectと環境を再生成した。製品sourceや既存台帳は手修正していない。
- 測定の条件: local macOS、正規prepare全体をn=1。Web/native verifierの実build記録と固定sourceを再検証し、実Lean canaryを実行した。質問と有料モデルは使っていない。
- 結果: 技術準備1/1。compiler canaryは2455msでverified、leftover job・request・説明未完了jobは各0。状態はprepared_dependency_ready_not_product_accepted。
- 判断: ローカル準備の完了を記録し、後続の認証・新候補・有料captureの検査を別に続ける。旧C20eeは期限切れのため使わない。
- 費用: 台帳は52 calls、180904/700000 μUSDを維持。新しい有料captureはなく、実請求額は未確認。
- 限界・未確認: TLS残存はprepare完了時43093秒。時間の経過後は再確認が必要。新候補manifestは未生成、headless認証・本番API認可・回答の保存と再読み込みは未確認。SSOの通常ログインを待つ時点の記録であり、改善率は作らない。
- 次にやること: 新しい署名済み候補・実観測・認証contextを結び付け、課金前の検査を終えてから有料captureを行う。
- 出典: [再開時の準備確認](../../seq30-resume-readiness-2026-11-16.md)、品質台帳 `2026-11-16-seq30-resume-local-readiness`、[pals#378](https://github.com/AtsushiHosaka/pals/issues/378)。根拠hashは確認記録に掲載し、生データは非公開で保持する。
