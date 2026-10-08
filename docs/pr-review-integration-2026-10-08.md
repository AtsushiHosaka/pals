# 2026年10月8日のPRレビューと統合

着手時にPALS関連リポジトリで開いていた24件を対象に、サブエージェントでレビューを分担した。差分、依存関係、既存mainとの競合、関連テストを確認した。並行作業で先にマージされたPRは、重複操作せず、最新main上で差分と回帰を再確認した。

| リポジトリ | 対象PR |
|---|---|
| pals | [#2](https://github.com/AtsushiHosaka/pals/pull/2)、[#3](https://github.com/AtsushiHosaka/pals/pull/3)、[#5](https://github.com/AtsushiHosaka/pals/pull/5)、[#6](https://github.com/AtsushiHosaka/pals/pull/6)、[#8](https://github.com/AtsushiHosaka/pals/pull/8)、[#9](https://github.com/AtsushiHosaka/pals/pull/9)、[#10](https://github.com/AtsushiHosaka/pals/pull/10)、[#18](https://github.com/AtsushiHosaka/pals/pull/18)、[#19](https://github.com/AtsushiHosaka/pals/pull/19) |
| pals-api | [#1](https://github.com/AtsushiHosaka/pals-api/pull/1)、[#2](https://github.com/AtsushiHosaka/pals-api/pull/2)、[#3](https://github.com/AtsushiHosaka/pals-api/pull/3)、[#4](https://github.com/AtsushiHosaka/pals-api/pull/4) |
| pals-agent | [#2](https://github.com/AtsushiHosaka/pals-agent/pull/2) |
| pals-webfront | [#1](https://github.com/AtsushiHosaka/pals-webfront/pull/1)、[#3](https://github.com/AtsushiHosaka/pals-webfront/pull/3)、[#4](https://github.com/AtsushiHosaka/pals-webfront/pull/4)、[#6](https://github.com/AtsushiHosaka/pals-webfront/pull/6)、[#7](https://github.com/AtsushiHosaka/pals-webfront/pull/7)、[#8](https://github.com/AtsushiHosaka/pals-webfront/pull/8)、[#9](https://github.com/AtsushiHosaka/pals-webfront/pull/9) |
| pals-infra | [#1](https://github.com/AtsushiHosaka/pals-infra/pull/1)、[#2](https://github.com/AtsushiHosaka/pals-infra/pull/2)、[#4](https://github.com/AtsushiHosaka/pals-infra/pull/4) |

CodeRabbitのSUCCESSには、draftのレビュー省略や利用制限による結果が含まれていた。これを実レビュー完了の証拠にせず、サブエージェントが独立に確認した。CLIの追加レビューは認証待ちで実施していない。

## 統合時に修正した欠落と仕様衝突

Recipe-first経路で失われていたLean反証と数学規約を保持した。catalog失効からDSPへ進む場合も、確定した数学規約を引き継ぐ。古いfrontendのSource表示を現行パネルへ接続し、回答切替・キャンセル・所有者分離を保った。

仕様ではPFR-015の反証要件を残し、数学的照合をPFR-017へ分離した。応答言語の統合でも、CORE-012・CORE-013のRecipe-first方針を保持した。過去の検証記録と今後の未確認項目を分け、親の古いsubmodule参照で後続修正を戻さないようにした。

APIの最終相互回帰187件、agentの関連343件、infraの108件、親デプロイスクリプトの79件が成功した。frontendはSource表示、認証、数学設定、言語、プランの関連回帰、TypeScript、ESLintに成功した。各スイートには重複があるため合計件数は示さない。専用の隔離PostgreSQL 16と実providerを必要とする項目は未実行で、既存の共有DBへ適用していない。

## 自動デプロイを停止した理由と再開条件

親mainの更新はMac miniへのデプロイを起動するため、統合中にリポジトリ変数 `MACMINI_AUTO_DEPLOY` を `false` にした。`MACMINI_DEPLOY_READY` は変更していない。本番DB、保護されたhost authority・policy・Caddy設定、AWS権限、providerへのデータ送信は変更していない。

最終APIのregistryは、guest 26段階、math 27段階、proof-request-lean 28段階、recipe-search 29段階、draft-candidates 30段階、reply-language 31段階の順。現在の閉じた署名更新authorityはこの追加tailを適用できない。古い署名条件を緩めて通す変更は行わない。

自動デプロイの再開には、現ホストのregistry・admissionを読み取り確認し、対象を固定した署名付き更新を整備し、隔離DBで検証したうえで本番適用する必要がある。host更新では自動復旧とguestの既存能力を保持する。マージだけでは公開環境の受け入れ確認は完了しない。最新の本番適用済み状態は、ソースのmainとは別に確認する。
