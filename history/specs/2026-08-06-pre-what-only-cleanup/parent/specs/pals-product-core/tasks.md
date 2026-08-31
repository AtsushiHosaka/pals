# Tasks: PALS Product Core

- [ ] CORE-T1 (`CORE-001`〜`CORE-004`). 直接的な Red テストを作る。
- [ ] CORE-T2 (`CORE-001`〜`CORE-004`). 問い → 証明生成 → Lean 検証 → 日本語説明の最小経路を実装する。
- [ ] CORE-T3 (`CORE-003`). 同じ検証済み証明に基づく追加質問を実装する。
- [ ] CORE-T4 (`CORE-004`). 失敗時に成功を捏造しないことを統合テストで確認する。
- [ ] CORE-T5 (`CORE-005`). 説明を主表示にし、Lean source を補助表示として確認する。

## Focused Task Ownership

CORE task を開始・検証するときは、`design.md` の対応する focused requirement と、次の
focused task を同じ変更範囲で実行する。

| Core task | Focused tasks |
|---|---|
| CORE-T1, CORE-T2 | API lifecycle task 1; Agent proof-explanation-evaluation tasks 1–2; API proof-job-runtime tasks 1–2 |
| CORE-T3 | Agent proof-explanation-evaluation task 1; API proof-explanations task 1; Webfront task 1 |
| CORE-T4 | Agent proof-explanation-evaluation tasks 1–3; API proof-job-runtime tasks 1–2; Webfront task 1 |
| CORE-T5 | API lifecycle task 1; Webfront task 3 |

各 task は必要な repository で直接進めます。bundle の status、レビュー結果、別 feature
の完了は開始条件ではありません。
