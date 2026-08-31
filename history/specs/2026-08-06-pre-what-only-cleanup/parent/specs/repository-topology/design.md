# Design: Repository Topology

## Placement Rules

- REP-001〜REP-003: implementation は責務表の repository に置く。
- REP-004: Lean verifier を別 process/container で動かしても source は `pals-agent` に置く。
- REP-005: 横断 Spec は親、repository 固有の設計は所有 repository に置く。
- REP-006: public/private 境界は package と secret scan で確認する。

Ownership key、Spec hash、review status、approval lifecycle を runtime や開発開始条件として
管理しません。重複が見つかった場合は、実際の実装責務を基準に配置を直します。
