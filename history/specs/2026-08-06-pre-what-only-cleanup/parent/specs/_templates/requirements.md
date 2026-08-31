# Requirements: Feature Name

## Purpose

コードやテストから読み取れない、現在の必須動作だけを書きます。

## Requirements

ID はこの bundle 内でのみ bare form を使う。別 repository から参照するときは、
`specs/README.md` の `<repository>/specs/<bundle>#<local-id>` 形式を使う。

| ID | Requirement |
|---|---|
| REQ-001 | 利用者またはシステムが必要とする観測可能な動作。 |

## Acceptance Criteria

- `REQ-001`: 入力、期待結果、失敗時の扱いを短く検証可能に記述する。

## Non-Goals

- 今回決めない動作や実装詳細。

## Open Questions

- 実装方針を変える未決事項だけを書く。なければ「なし」。
