# Requirements: Platform Architecture

## Purpose

PALS の環境とコンポーネントの大きな境界だけを定義します。AWS resource、認証、
secret carrier、network protocol、file hash、release gate の詳細はここでは定義しません。

## Requirements

| ID | Requirement |
|---|---|
| ARCH-029 | `.local`、`.dev`、`.prod` を分離し、production 操作は明示的に選択する。 |
| ARCH-030 | Local 開発は Docker Compose とローカル互換依存を使って再現できる。 |
| ARCH-031 | Agent と Lean verifier の source/tooling は `pals-agent` が所有する。実行 process の分離は source ownership を変えない。 |
| ARCH-032 | Product API は `pals-api`、通常 UI は `pals-webfront`、Draft 運用 UI は `pals-draft-admin` が所有する。 |
| ARCH-033 | `.local` の LLM 実験は Ollama を基本とし、Apple Silicon の fine-tuning は MLX/MLX-LM を使う。 |
| ARCH-034 | credential、API key、database URL、production configuration を repository に保存しない。 |
| ARCH-035 | Observability は運用に必要な最小情報に限定し、秘密情報や不要な生コンテンツを記録しない。 |
| ARCH-036 | Draft catalog inspection の production access は `pals-infra` 所有の認証済みかつ network-restricted な perimeter の内側に置く。Draft content route を直接 public に公開せず、read-only database role を HTTP access control の代替にしてはならない。readiness は Draft content を返さず、外部公開しない。 |

## Acceptance Criteria

- 各環境の設定が混ざらず、production 操作は暗黙に実行されない。
- Local の基本サービスを documented command で起動・停止できる。
- Lean 関連 source が独立した別 repository に重複しない。
- 秘密情報が tracked file、log、generated artifact に含まれない。
- production 外部から未認証または network policy 外の caller が Draft content または readiness に到達できない。

## Open Questions

具体的な hosting、認証、network、queue、database、release 構成は、実装する slice ごとに
決定します。
