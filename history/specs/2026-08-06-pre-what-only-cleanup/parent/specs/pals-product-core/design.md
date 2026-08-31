# Design: PALS Product Core

## Core Flow

```text
math question
  -> proof generation
  -> Lean verification
  -> Japanese explanation
  -> optional clarification
```

## Design Decisions

- CORE-001: 入力は自然言語問題または形式的命題として受け取る。
- CORE-002: Agent が証明候補を作り、Lean verifier の実結果を成功判定に使う。
- CORE-003: 説明と追加回答は、同じ検証済み証明を参照する。
- CORE-004: 各段階の失敗は失敗として終了し、生成済みの固定回答で置き換えない。
- CORE-005: 学習画面は説明を中心にし、Lean source は補助的に参照できるようにする。

## Cross-repository Traceability

Cross-repository IDs use the form defined in `specs/README.md`.

| Core requirement | Owning focused requirements | Focused task ownership |
|---|---|---|
| CORE-001 | `pals-api/specs/proof-job-lifecycle#APILC-002` | API lifecycle task 1 |
| CORE-002 | `pals-agent/specs/proof-explanation-evaluation#PAE-016`, `pals-agent/specs/proof-explanation-evaluation#PAE-017`; `pals-api/specs/proof-job-runtime#PJR-001`–`pals-api/specs/proof-job-runtime#PJR-003` | Agent tasks 1–2; API PJR task 1 |
| CORE-003 | `pals-agent/specs/proof-explanation-evaluation#PAE-001`; `pals-api/specs/proof-explanations#PEX-001`, `pals-api/specs/proof-explanations#PEX-003`, `pals-api/specs/proof-explanations#PEX-004`; `pals-webfront/specs/proof-explanation-clarification#PEX-001`–`pals-webfront/specs/proof-explanation-clarification#PEX-005` | Agent task 1; API PEX task 1; Webfront task 1 |
| CORE-004 | `pals-agent/specs/proof-explanation-evaluation#PAE-001`, `pals-agent/specs/proof-explanation-evaluation#PAE-007`, `pals-agent/specs/proof-explanation-evaluation#PAE-010`, `pals-agent/specs/proof-explanation-evaluation#PAE-016`, `pals-agent/specs/proof-explanation-evaluation#PAE-017`; `pals-api/specs/proof-job-runtime#PJR-003`, `pals-api/specs/proof-job-runtime#PJR-007`, `pals-api/specs/proof-job-runtime#PJR-009`; `pals-webfront/specs/proof-explanation-clarification#PEX-004` | Agent tasks 1–3; API PJR tasks 1–2; Webfront task 1 |
| CORE-005 | `pals-api/specs/proof-job-lifecycle#APILC-002`; `pals-webfront/specs/proof-explanation-clarification#PEX-004`, `pals-webfront/specs/proof-explanation-clarification#UI-PEX-007` | API lifecycle task 1; Webfront task 3 |

API schema、永続化、transport、認証、deployment の具体方式は、所有 repository の実装と
その作業に必要な focused Spec で扱います。
