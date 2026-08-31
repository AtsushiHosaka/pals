# Requirements: Repository Topology

## Requirements

| ID | Requirement |
|---|---|
| REP-001 | 親 `pals` repository は横断文書、ローカル補助 script、進行管理、submodule 参照を所有する。 |
| REP-002 | `pals-api` は FastAPI backend、`pals-webfront` は通常 frontend、`pals-draft-admin` は read-only Draft 運用 UI を所有する。 |
| REP-003 | `pals-infra` は infrastructure、`pals-datasets` は dataset/ingestion、`pals-observability` は observability 実装を所有する。 |
| REP-004 | `pals-agent` は public OSS Agent と Lean verifier の source/tooling を所有する。別の Lean verifier source repository は作らない。 |
| REP-005 | 横断的な意思決定は親に、単一 repository の実装詳細はその repository に置く。 |
| REP-006 | private prompt、private dataset、credential、production endpoint/configuration を public artifact に含めない。 |

## Acceptance Criteria

- 実装 file は一つの所有 repository に置かれる。
- 親 repository は implementation repository 固有の実装を重複所有しない。
- Agent/Lean source は `pals-agent` に一意に存在する。
- 親文書を submodule 内へ、submodule 固有文書を親へ重複配置しない。

## Current Repository Map

| Repository | Responsibility |
|---|---|
| `pals` | coordination, cross-repository docs, local helpers, submodules |
| `pals-api` | private backend |
| `pals-webfront` | private product frontend |
| `pals-draft-admin` | private read-only Draft operations frontend |
| `pals-infra` | private infrastructure |
| `pals-datasets` | private ingestion and dataset tooling |
| `pals-observability` | private observability implementation |
| `pals-agent` | public Agent and Lean verifier tooling |
