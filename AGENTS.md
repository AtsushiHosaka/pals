# PALS Repository Notes

この親リポジトリは PALS 全体の進行管理、横断ドキュメント、ローカル補助スクリプト、submodule 参照を置く場所です。実装は各 submodule 側に分かれます。

## Skills

- SDD / TDD にはインストール済みの汎用 skill を使います。`.agents/skills` には PALS 固有の Lean
  compile / generation のような、汎用 skill で扱えない能力だけを置きます。

## Repository Topology

- pals-api: private FastAPI backend submodule.
- pals-webfront: private frontend submodule.
- pals-draft-admin: private, read-only Draft catalog operations frontend.
- pals-infra: private Terraform infrastructure submodule.
- pals-datasets: private ingestion/dataset tooling submodule.
- pals-observability: private observability submodule.
- pals-agent: public OSS LangGraph agent and Lean verifier tooling submodule.
- pals-scripts: parent-repo helper scripts. Secrets stay local.

The implementation submodules may be empty until initialized. Parent-level planning docs should be placed in this repository root or docs/, not inside submodules, unless the documentation belongs to that implementation repository.

## Documentation Placement

- Cross-repo Specs belong in specs/. Repository-exclusive Specs belong in the owning implementation repository.
- Cross-repo research notes, cost notes, and operating evidence belong in root-level Markdown files or docs/ so they are tracked by the parent repo.
- Avoid putting parent-project documentation inside submodules when the goal is to publish it with this parent repo.
- Do not commit secrets, credentials, API keys, database URLs, AWS credentials, Langfuse secrets, local environment files, logs, dumps, or generated outputs.

## Working Tree Safety

- 既存の tracked / untracked 変更はユーザー所有です。明示的な許可なしに reset、clean、stash、overwrite、stage、commit してはいけません。
- このプロジェクトの各チャットでは、変更を検証したら、そのチャットで行った変更を随時 commit して GitHub に push する。これをユーザーの継続的な許可として扱い、毎回確認しない。
- 他のチャットの作業が混在する場合は、自分の変更だけを commit する。force push はしない。親リポジトリの submodule 参照は、実装リポジトリへの push が成功してから更新する。

## Existing Feature Preservation

- Obtain the user's explicit approval before removing, disabling, hiding, or making an existing user-facing feature inaccessible. This applies to the parent repository and every implementation submodule.
- Requests to simplify, clean up, restyle, refactor, merge, or deploy do not authorize feature removal. Preserve existing capabilities and their entry points unless the user explicitly approves their removal.
- Before proposing removal, identify the exact feature and affected screens, explain the impact, and ask the user. An approval to remove one feature does not extend to other features.
- During review and release, check for unintended loss of existing capabilities. If a change would remove a feature without approval, preserve it or stop that part of the change and ask the user.
- See [the feature preservation policy](docs/feature-preservation-policy.md) for examples.

## 数学のテスト題材

- 平方展開 `(x+y)^2=x^2+2xy+y^2` の証明問題は、今後のテスト、描画プレビュー、デモ、dogfood では使わない。ユーザーが簡単すぎる題材として使用を禁止したため。
- 数学の代表的なテスト題材には、仮定を明示し、実質的な数学的推論が必要な証明問題を選ぶ。単純な計算や恒等式の展開だけで完了する問題は選ばない。
- 過去の Issue、スクリーンショット、検証記録に残る入力は、当時の証拠として保持する。新しいテストの題材には再利用しない。
