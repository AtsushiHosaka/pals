# 2026-08-06: Spec scope reorganization

この記録は、PALS の仕様をプロダクトの What だけに戻す前の文書を退避したものです。

## Decision

- 現在のプロダクト正本は `specs/pals-product-core/requirements.md` とする。
- 実装方法、作業タスク、構成、運用、レビューに関する文書は、現在の仕様として扱わない。
- 各実装リポジトリ固有の旧仕様は、そのリポジトリ自身の `history/` に保存する。

## Parent archive

- `parent/specs/` には、親リポジトリにあった設計・タスク・技術的な仕様を元の相対配置で保存する。
- ここに保存した内容は、現行要件の補足・実装指示・受入条件ではない。

## Compatibility-bound implementation cleanup

Project Workspace の v1 release protocol は、旧 Markdown のハッシュを実行時に読む構造だった。
その依存を外し、既存 artifact に埋め込まれた互換識別子を検証する構造へ移した。これは
プロダクトの機能追加・削除ではなく、仕様ファイルが実装を停止させないための整理である。
