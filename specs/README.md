# PALS Product Specification

`specs/` は、PALS が学習者に提供する現在の振る舞いと、その振る舞いを損なわないために承認した
内部安全契約を定義する正本です。実装方法、作業計画、構成、運用手順、レビュー結果、変更理由は
ここから導きません。

## Learner-facing behavior

- [pals-product-core](pals-product-core/requirements.md) — 証明要求、回答、検証状態、出力言語、チャット。
- [proof-request-reuse](proof-request-reuse/requirements.md) — 通常送信、前提確認、カタログ再利用と Lean 検証の流れ。
- [draft-addition-candidates](draft-addition-candidates/requirements.md) — 検証済み証明の Draft DB 追加候補と運用者承認。
- [projectless-chat-start](projectless-chat-start/requirements.md) — Project に属さないチャット。
- [chat-navigation](chat-navigation/requirements.md) — チャット検索と新着回答の表示。
- [chat-sharing](chat-sharing/requirements.md) — 固定スナップショットの公開リンク。
- [project-materials](project-materials/requirements.md) — Project 資料・OCR・回答の出典。
- [public-guest-chat](public-guest-chat/requirements.md) — 公開LPとログイン不要のゲストチャット。
- [individual-billing](individual-billing/requirements.md) — 無料枠、有料プラン、利用トークン、課金安全境界。

## Internal contracts

- [lean-recipe-catalog](lean-recipe-catalog/requirements.md)、[recipe-curation-proposals](recipe-curation-proposals/requirements.md)、[draft-catalog-expansion](draft-catalog-expansion/requirements.md) — 証明カタログ。
- [domainless-production-bootstrap](domainless-production-bootstrap/requirements.md) — 本番構成の安全境界。

## Repository-owned specs

- `pals-api/specs/account-notation-preferences`、`pals-api/specs/recipe-proof-candidate-source`
- `pals-webfront/specs/proof-notation-personalization`、`pals-webfront/specs/auth-callback-routing`

コード、テスト、既存の技術文書、または `history/` の内容は、新しいプロダクト要件の根拠に
なりません。過去の仕様・設計・タスクと今回の整理の記録は [history/](../history/README.md) にあります。
