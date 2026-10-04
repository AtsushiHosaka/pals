# CORE / RCP / RPCS 修正・検証記録 — 2026-09-29

## 対象と判定

`docs/spec-audit-2026-09-29.md` の指摘後に実施した限定スコープの記録。API `858dd16`、agent `ab42335` を基点とする現在の未コミット変更を含む。公開済み main 単体の結果ではない。正本仕様は変更していない。**プロジェクト全体の完了判定ではない。** 実行済みローカル依存テスト、モデルを代替した単体テスト、未実行の実アプリ確認を区別する。

## CORE-003 / CORE-006：選択文章と親補足文脈

- API は保存済みの親補足から id / question / answer / key_points を取得し、所有者、同じ証明・section、completed 状態、選択文章との対応を確認する。
- worker は選択文章と親補足本文を生成と独立 QA の両方へ渡す。親補足は文脈であり、新しい数学的公理として扱わない。
- 新しい補足の公開には `pals.proof-output-review.v3` が必要。section、質問、選択文章、親 ID と親本文の canonical digest を出力・QA 証跡へ結合し、保存 transaction 内で DB から再構築して照合する。説明全体の receipt は v2 のまま。既存 completed v2 の読み取り・同一 replay は維持する。
- API / worker の同時更新が必要。旧 worker は v3 文脈証跡のない新しい補足を公開できない。

主な実装：`pals-api/app/domain/models/proof_explanation.py`、`app/application/services/proof_explanations.py`、`app/schemas/proof_explanations.py`、`app/infrastructure/repositories/postgres.py`、`pals-agent/pals_agent/explanations.py`、`worker.py`、`api_client.py`。

検証：agent 関連 198 checks PASS、API 関連 171 checks PASS。単体のモデル/transport double は入力伝搬と fail-closed を証明し、モデル回答品質の証拠にはしない。実 PostgreSQL の output-review migration gate は誤選択 digest、親本文差替え、旧 v2 新規公開拒否、有効 v3 完了・replay・証跡保存を確認。実 agent serializer → transport validator → API Pydantic validator も実行済み。

その後、AIR / outbox / generation claims / semantic review / final repair / explanation retry / output review / explanation claims の実 PostgreSQL 合計 **109 tests PASS (34.13s)**。BILL の固定 schema FK と衝突した従来 search_path fixture は、checked-in billing SQL をそのまま適用する専用 disposable DB に変更した。production SQL を書き換えず、共有アプリ DB のデータを利用していない。

## DPB-009 関連の再確認

親担当の retry recovery は startup scan + 仕事がある間の bounded retry + event wakeup へ変更された。HTTP cancellation 後も受理処理の所有者を保持し、曖昧な commit は同じ owner / idempotency key で再照合する経路を独立レビューした。アイドル中の周期 DB scan を再導入する経路は確認しなかった。

runtime readiness は同じ restricted-role connection で説明 retry / private failure の必要権限を検査する。private failure INSERT 欠落と retry state UPDATE 欠落を実 PostgreSQL で拒否。関連 recovery/readiness unit **7 PASS**。実 AWS の Aurora 自動休止、権限配布、運用挙動はこの記録では未検証。

## RCP-001 / 004 / 005：実カタログ不変性

`pals-api/app/infrastructure/recipe_curation_proposals.py` で二つの不具合を修正した。

- historic attestation の schema と artifact URI の型・非空を検査する。無効な historic 行から proposal/event を作らない。
- candidate → origin → proposal ID の順で共有 advisory lock を取得する。異なる origin が同一 proposal ID を同時使用した際、修正前の created + persistence_failed を、created + proposal_conflict へ修正。decision は proposal lock のみで逆順取得を導入しない。

新しい `tests/integration/test_recipe_curation_catalog_invariance.py` は、実 pinned Lean と一時 mTLS listener で `import Mathlib\n\nexample : True := by trivial\n` を admission し、alignment・selector receipt・no-Recipe trace を保存する。三つの catalog/alignment/trace schema の全 relation を snapshot し、v1 / v2-model の API nomination・replay・decision の前後で完全一致を確認。curation role に catalog schema access がないことも確認する。

最終 RCP integration/unit と retry checks 合計 **22 PASS (15.23s)**。同一 proposal ID 競合は実 PostgreSQL で red → green を確認。v1/v2 の semantic origin records は canonical fixture であり、ライブ LLM が作成した審査記録とは主張しない。Lean admission は実行済み。

## RPCS-T007：実 candidate API → Lean → 独立審査 → 保存

新しい `pals-api/tests/integration/test_recipe_candidate_runtime.py` による実 PostgreSQL / pinned Lean / mTLS gate：

1. 実 selector receipt から exact source binding を作り、内部 candidate API を通す。
2. 実 isolated verifier で同一ソースをコンパイルし semantic_review_pending へ進む。
3. reviewer 専用 GET で authoritative source/target/binding を取得する。通常 worker credential と誤 binding は拒否する。
4. 専用 reviewer credential の v3 POST で verified へ進み、canonical 証跡と独立 actor principal を保存する。公開 DTO には Recipe 内部情報を出さない。
5. 同じ admission の別 job を、Mathlib を利用できない実 compiler 環境で処理する。実コンパイル失敗後は `recipe_verification_failed`、claim 解放、failed event 一件、semantic review なしとなる。同じ claim の model repair 追加は 409 で拒否する。

審査内容は親担当が独立に承認した上記 `True` / `by trivial` の正確な source に限定する。モデル生成を模倣した成功を実モデル品質の証拠にしていない。失敗側は「依存 Mathlib 不在の fault injection」であり、通常稼働 Mathlib の不具合とは扱わない。

runtime gate / RPCS migration / candidate units / dedicated-auth units 合計 **32 PASS (39.51s)**。候補 source がある model v2 も v3 の binding 照合対象とする repository 修正を含むが、この実 Lean gate の成功対象は Recipe である。

## 専用 reviewer actor と HTTP 境界

`pals-agent/pals_agent/recipe_semantic_reviewer.py` は worker から job ID / candidate ID のみ受ける。ソースと binding は reviewer credential で API から取得する。fresh independent reviewer session の結果を dedicated credential で v3 POST する。一般 worker API credential、selector/curator credential の同居を起動時に拒否する。通常 worker の `PalsApiClient` から v3 を POST することも拒否する。

別 worker 側 dispatcher は reviewer 応答を成功判定として信用せず、API を再取得して durable terminal 状態を確認する。失敗・timeout なら元 SQS receipt を残す。処理中の SQS visibility は延長される。actor は同一 job の重複と上限超過を 503 にし、完了後の再配信は terminal read により再審査しない。親担当の settings / dispatcher / worker / Compose / production env 配線を独立レビューし、重大な追加指摘なし。

HTTP は requester header 一個、Content-Length 一個、Content-Type 一個、1024 bytes 以下の閉じた JSON だけを受理する。Transfer-Encoding、重複 key、曖昧な framing を拒否。handler thread 作成前に接続数を 16 に制限し、超過は 503。socket header/body read timeout は 5 秒。実 loopback socket テストで部分 header 接続による飽和、timeout 後の枠解放、正常リクエストの復帰を確認した。これは HTTP boundary test であり actor double は外部モデルを呼ばない。

actor / transport unit **41 PASS (0.56s)**。actor module mypy / Ruff PASS。API internal routes / schema / config の mypy PASS。API workspace contract 120 PASS、candidate/schema/source 39 PASS は前段で実行済みで、重複集計して総件数にはしない。

## 実行環境と残る確認

既存 localhost PostgreSQL と既存 pinned Lean を再利用した。専用テスト DB の作成・削除と、直列化した一時 mTLS listener / ephemeral loopback HTTP listener のみ使用。新規コンテナ、ブラウザ、外部モデル呼出し、共有アプリ DB の状態注入は行っていない。秘密はメモリでのみ読み込み、文書・出力へ保存していない。

実アプリの再 deployment、fresh model での説明・親補足再質問の品質、Recipe reviewer service のコンテナ間接続、AWS deployment attestation は親担当の現在進行中の検証と区別する。この記録の PASS だけで、それらや仕様全体を完了とはしない。最新の shared OpenAPI snapshot と全 suite の最終統合結果も親担当の記録を参照する。

## 追補：全 production registry 結合検証で判明した問題

正規 PJR / PEX artifact をそのまま適用する disposable DB fixture と、新しい非 superuser runtime login で、全 registry をまとめて検証中。production admission / KMS 署名を偽造する fixture は使用していない。

- `release_admission_bootstrap.py` は canonical PJR の incoming FK により PostgreSQL が追加する内部 RI trigger まで禁止し、正しい foundation を mixed と判定していた。正確な FK・列・参照アクション・pg_catalog 関数・有効な内部 trigger 二個だけを認めるよう修正。未知 user trigger、別の incoming FK、無効化された正規 trigger の実 PostgreSQL 負例 **3 PASS**。
- `production_database_release.py` の長い status transaction は、別 connection の migration が commit した新規 relation を直後に認識せず、installed 後の再確認で absent を返した。orchestrator の読み取り connection を autocommit に変更。各 migration 自身の transaction 境界は保持する。
- project-chats step は存在しない `_catalog_state` を参照していた。`_chat_catalog_state` と `_binding_catalog_state` の両方を確認する明示 predicate に修正。

この時点の readiness / release units **11 PASS**、上記二 production modules の mypy / Ruff PASS。全 registry は explanation-retries まで進行したが、次の billing owner に public schema USAGE がなく、実 PostgreSQL で `permission denied for schema public` を確認した。課金担当へ修正を依頼済み。**全 registry の実 PG PASS はまだ主張しない。** 最終結果は追記する。

全 registry 検証の続報：課金担当が immutable 既存 SQL を保持したまま billing owner の public USAGE prerequisite を追加し、全 **17 migration steps のインストールが実 PostgreSQL で成功**した。制限付き runtime 側の検証は続行中。

- runtime の PEX predicate は、公開権限を持たない隔離済み質問本文を読もうとしていた。release 側の quarantine 検査を維持し、runtime はデータ本文を除く同じ catalog / ACL / readable row 検査を使う。quarantine SELECT を runtime に与えていない。
- billing / typed reader の narrow role grants は PostgreSQL 16 の `WITH INHERIT TRUE` を明示し、readiness は MEMBER でなく実効 USAGE を確認する。独立した NOINHERIT test role で、通常 GRANT は MEMBER=true / USAGE=false、明示 inheritance は USAGE=true になることを実 PostgreSQL で確認。
- Lean Recipe catalog の metadata 確認は、runtime から意図的に読めない private table を `information_schema.columns` で探していた。同じ列名集合の検査を `pg_attribute` / `pg_class` / `pg_namespace` に変更し、内容への権限は追加しない。

上記は fixture 上の実依存検証であり、AWS signed bootstrap の実行証跡ではない。

### 全 registry gate 最終結果

`pals-api/tests/integration/test_production_runtime_readiness.py` **10 PASS / 4.08 秒**。

- 正規 artifact を verbatim 適用した専用 DB に全 17 registry steps が導入される。
- 実際に接続した unique LOGIN は NOINHERIT / NOSUPERUSER / NOCREATEDB / NOCREATEROLE。各 step の runtime predicate と `runtime_database_is_ready` が true。closed gate と exact open gate の両方で確認し、open 中の migration release は拒否する。
- runtime は quarantine SELECT、private alignment schema USAGE、Recipe receipt SELECT をいずれも持たない。information_schema に private receipt の列は表示されないまま、pg_catalog metadata 検査が成功する。
- private failure INSERT を失う、private catalog の必須列が変わる、未知 trigger / incoming FK が増える、正規内部 trigger が無効化される場合は fail closed。
- NOINHERIT role の通常 membership と実効 USAGE が異なる負例、および explicit INHERIT による最小 role grant を実 PostgreSQL で確認した。

追加 metadata 修正は `lean_recipe_catalog_migration.py`、`recipe_candidate_admission_migration.py`、`recipe_curation_proposals_migration.py`。名前から regclass を解決する際の private schema 権限要求を避け、同じ schema / table / function の pg_catalog OID で構造・ACL を検査する。データアクセス権は追加していない。production registry の manifest は child manifest の digest を持ち、Python adapter 自体の digest ではない。途中の adapter hash refresh という説明は誤りであり、metadata-only Python 修正による manifest 更新は不要だった。

この gate の migration installer は test admin 接続。**NOCREATEROLE production release login を使う signed bootstrap 全体の実行を証明するものではない。** その bootstrap の役割作成・所有権・AWS admission の検証は別記録とする。テスト DB と unique test roles は fixture の finally で削除し、共有 canonical role identities は変更・削除しない。
