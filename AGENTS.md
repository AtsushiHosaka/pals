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
