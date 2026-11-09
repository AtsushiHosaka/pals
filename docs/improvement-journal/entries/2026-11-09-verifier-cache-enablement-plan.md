# x² の検証結果キャッシュ：有効化の段取りの調査（2026-11-09）

- 指標: 時間（x² のコンパイル約9〜10秒の省略）
- 前提: 検証結果キャッシュ本体と測定は[別のエントリ](2026-11-08-x-squared-verifier-cache.md)（代数幾何セッションの記録）。ここでは、有効化の手順を調べた結果だけを足す。
- 変更: なし（調査のみ）。成果物は `docs/verifier-cache-enablement-plan-2026-11-08.md`。
- 調査で分かったこと:
  - フラグは、SHADOW → (SHADOW+REVALIDATE+ENABLED) の順。ENABLED は SHADOW と REVALIDATE が必須（#81）。#80 単体で ENABLED は使わない。
  - 検証器 image は必ず変わる（Dockerfile が pals_agent 全体を wheel にするため）。API と DB の変更は不要。worker は機能変更なし。
  - toolchain hash が pals_agent の source archive 由来なら、全 Recipe の再 admission が要る。本番での導出は未確認。配備中のマニフェストと git archive の SHA を突き合わせれば確定する。
  - 影の実行はプロセス内メモリの比較なので、「配備をまたいだ一致」は確認できない。
  - merge は #80 → #81 の順。squash なら #81 は `rebase --onto` が必要。seq27 の worker との衝突はなかった。
- 見込み（算術）: コンパイル約9秒を省き、22〜24秒が約13〜15秒。ヒット率は未測定。
- 判断: seq29 は worker だけの release にし、検証器 image の変更は別 release にする（リリース担当の判断）。
- 限界・未確認: 実 Lean の確認は macOS のローカルだけで、許可リスト52本のうち4本。本番の隔離・冷たい状態・同時要求は未検証。観測面はログ行のみ（snapshot は本番に出ない）。フラグの渡し先とログ群名は pals-infra から分からなかった。
- 次にやること: 配備中の toolchain hash の導出元を確かめ、再 admission の要否を確定する。
- 出典: pals-agent #80・#81、`docs/verifier-cache-enablement-plan-2026-11-08.md`
