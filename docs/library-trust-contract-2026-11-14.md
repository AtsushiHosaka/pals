# 信頼の水準（library_trust）: API と画面に渡す契約

2026-11-14。agent 側の実装は pals-agent#128（`ProofRunResult.library_trust`）。API と画面は未実装で、この文書はその契約案である。方針: 人手で未レビューの形式化に依存した回答も出し、信頼の水準を利用者に表示する。

## 何を表すか

Lean が検証した回答が、人手でレビューされていないライブラリのコードにどこまで依存するか。Lean の検証（カーネルの検査）は、未レビューの補題を使った証明も正しいと判定する。信頼の水準が示すのは、**命題の意味が人手で確かめられているか**であり、証明の正しさではない。

## フィールド

回答のデータ（API の回答と成果物）に、次のオブジェクト `library_trust` を持たせる。検証済みでない回答では `null`。

| フィールド | 型 | 意味 |
|---|---|---|
| `trust_level` | `"mathlib"` \| `"core"` \| `"frontier_proof"` \| `"frontier_statement"` | 下の表。複数の定理があれば最も弱い水準 |
| `recorded` | bool | 検証器が信頼の診断を記録したか。`false` は既定のプロファイル（Mathlib のみ）で、診断が無いことを意味する。`false` のとき `mathlib` は「記録なし」であり、監査済みの主張ではない |
| `human_unreviewed` | bool | `trust_level` が `frontier_*` のとき `true` |
| `frontier_modules` | string[]（最大 32） | 命題が届いた未レビューのモジュール名 |
| `frontier_statement_constants` | string[]（最大 32） | 命題が届いた未レビューの定数名 |

| `trust_level` | 意味 | 画面の表示（案） |
|---|---|---|
| `mathlib` | Lean と Mathlib だけに依存 | 表示しない（現状どおり） |
| `core` | レビュー済みの StacksCore に依存 | 「Stacks Project（人手レビュー済み）」 |
| `frontier_proof` | 証明だけが未レビューの Frontier 補題を使う。命題は Lean、Mathlib、StacksCore の定数だけ | 「証明に、人手で未レビューの補題を使用（Lean が検証済み）」 |
| `frontier_statement` | 命題の定義が未レビューの Frontier に届く。意味が依頼と一致する保証はない | 「人手で未レビューの形式化に依存」を目立つ警告として表示 |

## どの段で決まるか

1. 検証器の信頼済み監査プログラム（`lean_audit`）が、検証の最後に、命題が届く定数のルートと証明が使うルートを数え上げる。`stacks-frontier-4.35` 系のプロファイルだけが記録し、診断 `lean.library_trust`（`metadata` に水準、モジュール、定数）を返す。既定のプロファイルは診断を出さない。
2. agent は、検証結果の診断から `library_trust` を作る（`pals_agent.models.library_trust_of`）。複数の診断は最も弱い水準を採り、未知の水準は `frontier_statement` に倒す（弱い側）。
3. 成果物のメタデータに `library_trust` を保存し、`ProofRunResult.library_trust` で返す。

## 本番でまだ足りないもの（実装は別の作業）

- 本番の worker は検証せず、API 側の検証器（`api_reconcile`）が検証する。worker の `library_trust` は `null` のままなので、**正本は API の検証結果**にする。API は検証器の診断 `lean.library_trust` を保存し、`library_trust` を同じ規則（上の 2）で作って回答のデータに載せる。
- worker が API に送る診断の形（`pals_agent/api_client.py` の `_diagnostic_payload`）は `metadata` を落とす。API の検証結果から作るなら変更は要らない。worker の値を使うなら `metadata` を許可項目に足す。
- 本番の検証器は既定のプロファイルだけを提供しているので、今は `frontier_*` が実際に出る回答は無い。質問から検証環境を選ぶ振り分けと、Stacks 用の検証器の配備が前提になる（配備は別の判断）。
- 画面: `library_trust` が `null` か `mathlib` のとき従来どおり。`human_unreviewed=true` のとき上の表示を足す。履歴の再読み込みでも同じ値を出すため、回答と一緒に永続化する。

## 注意

- `trust_level` は命題の忠実さ（依頼どおりか）を保証しない。忠実さは、固定した形式化（`formal_statement`）と意味レビューで別に見る。
- `recorded=false` の `mathlib` を「信頼済み」と書き換えない。Frontier のプロファイルで監査の記録が失敗した場合も `recorded=false` になりうる。
