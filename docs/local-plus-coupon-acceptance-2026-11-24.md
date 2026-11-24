# Plus クーポンのローカル資格確認（記録）

2026-11-24。[local-plus-coupon-bootstrap-2026-11-18.md](local-plus-coupon-bootstrap-2026-11-18.md) の「Remaining gates」のうち、起動後の schema/ACL 読取と、認証付き引換を実行できる状態にした。
モデル、Stripe、AWS、SSM、本番には接続していない。

## 結論

実 PostgreSQL 16 と実 API プロセス（HTTP）とローカル Cognito で、次の3点を実行し、通った。

1. クーポン専用 append の適用（実 `bootstrap_database.py --enable-plus-coupons`）。
2. API 起動後の schema/ACL 読取と、その freeze 用の独立キー。
3. 認証付き引換（発行 CLI → ログイン → 引換 → 2個目の拒否 → DB 読取）。

これは `make release-local-qualify` の結果ではない。凍結済みの runner（`local-qualification.py`、ブラウザ runner）は変更していない。本番 Cognito、本番 DB、ブラウザ UI の証拠でもない。

## 追加したもの

| 場所 | 内容 |
|---|---|
| `pals-scripts/local-qualification/database_readiness.py` | `inspect_plus_coupons`。読取専用。API 自身の `current`/`fingerprint` が署名済み manifest の hash と一致することに加え、関数の owner・SECURITY DEFINER・search_path・EXECUTE 付与、表の ACL と実効権限（`pals_api_runtime`、`pals_billing_test_admin`）を観測する。既存の `inspect` と `schema_fingerprint_sha256` は変えていない。 |
| `pals-scripts/local-qualification-prepare.py` | `--enable-plus-coupons` のときだけ、API 起動後に読取り、`database_contract.plus_coupons_schema_fingerprint_sha256` として別キーで freeze する。API の再作成後にもう一度読み、一致を要求する。既定（opt-in なし）の subject は byte 変化なし。 |
| `pals-scripts/local-plus-coupon-acceptance.py` | 認証付き引換の確認。`--subject` を渡すと freeze 値との一致も要求する。 |
| `pals-scripts/tests/test_local_plus_coupon_acceptance.py` | 22件の単体・契約テスト。DB、HTTP、Cognito、発行 CLI だけを偽物に差し替える。 |

確認スクリプトの手順は次のとおり。コード本体と token は、メモリ内だけに置く。ファイルにも標準出力にも出さない。

1. schema/ACL を読む（`--subject` があれば freeze 値と照合）。
2. 使い捨てのローカル Cognito アカウントを2つ作ってログインする。
3. 引換前は無料プランで、Project 作成が `project_plan_required`（403）になることを見る。
4. 署名済みの operator role に属する一時ログインを作り、API の `issue-initial-campaign` で上限1回のコードを2個発行し、一時ログインを削除する。
5. アカウント1が1個目を HTTP で引換える。応答、`/billing/summary`、DB の行が一致し、期間が「UTC 暦月1か月」であることを見る。Project 作成が 201 になる。
6. アカウント1の2個目の引換と、同じコードの再引換が 409 `plus_coupon_existing_entitlement` で拒否され、2個目が消費されていないことを DB で見る。
7. アカウント2が使用済みのコードを引換えると 422 `plus_coupon_invalid`。2個目のコードは引換えられる（1回性）。
8. アカウント1が再ログインしても、Plus と grant が同じであることを見る。
9. schema/ACL を読み直し、最初と同じ fingerprint であることを見る。一時 role とアカウントを削除する。

## 実行結果（実行した環境）

独立した stack を使った。共有 stack、共有 runtime、既存のポート公開は使っていない。

- PostgreSQL: `pgvector/pgvector:pg16`（16.14）。ホストへポートを公開せず、コンテナ内で 55432 を待ち受ける。既存の `validate_local_dsn`（127.0.0.1:55432/pals）を変えずに通すため、同じ network namespace で他のコンテナを動かした。
- Cognito: `jagregory/cognito-local:5.3.0`。`pals-infra` の設定を読み取り専用で mount。
- API: pals-api `67e1156`（`full-api-67e1156cb6e7` の依存と、同じ commit の clone を読み取り専用で mount）を `uvicorn app.main:app` で起動。ローカル compose と同じく、本番用の起動スクリプトは通さない。
- driver: psycopg 3.3.9。

| 項目 | 結果 |
|---|---|
| クーポン append（実 `bootstrap_database.py`） | 初回 `installed`、再実行 `current` |
| 起動後の schema/ACL 読取 | 関数6、表4。連続2回で同一。既存の Draft `inspect` も同じ DB で成功 |
| 手で ACL を壊す（PUBLIC へ EXECUTE、runtime へ `codes` の SELECT、`issue` を runtime へ、`redeem` を SECURITY INVOKER） | 4件すべて検出。戻すと元の fingerprint に一致 |
| 認証付き確認 | 4回実行して成功（`--subject` ありの1回を含む）。不一致の freeze 値は、アカウント作成前に拒否 |
| 1回の確認の内訳 | 発行2、成功した引換2、拒否された引換3、failure 0、skip 0 |
| 後始末 | 一時 operator role 0、使い捨てアカウント削除。クーポンと引換の行は append-only のため残る |
| 単体テスト | 新規22件成功、skip 0。既存 `test_local_qualification.py` 125件成功、skip 3（`pals-api`/`pals-infra` submodule 未初期化による既存の skip） |

`prepare` の新しい関数（`freeze_plus_coupons`、`require_plus_coupons_unchanged`）も、同じ実 PG に対して直接呼んで成功した。

品質台帳（`docs/quality-ledger/ledger.csv`）には、認証付き引換の確認4回（`2026-11-24-plus-coupon-local-acceptance`）とACL破壊4種の検出（`2026-11-24-plus-coupon-schema-acl-freeze`）の2行を足し、グラフを再生成した。単体テストの件数は台帳に入れていない。

## NOT VERIFIED（実行していない、または証拠にならないもの）

- `local-qualification-prepare.py --enable-plus-coupons` の通し実行。共有 stack、compose、guard、TLS、予算台帳は使っていない。上の2関数を実 PG で動かしただけである。
- 共有 stack の API image に対する確認。共有 stack の API は 7b2fd405 で、クーポンのコードを持たない。
- API の構成は `PALS_PROOF_CAPABILITY=natural-only`。SQS、worker、verifier、Recipe selector は起動していない。引換と課金の経路は動くが、証明の生成と取得の経路は動かしていない。
- API の DB ログインはローカル compose と同じ単一の bootstrap user。本番の `pals_api_runtime` ログインでの引換は確認していない。`redeem` は SECURITY DEFINER で動くため、権限の欠落はこの確認で見つからない可能性がある。runtime role の権限は、カタログ照会でだけ確認した。
- 本番の起動確認（`production_database_release --check`、署名済み admission）は、ローカルでは成立しないため通していない。
- 本番 Cognito、Stripe、ブラウザ UI、保存と reload の画面表示、100人同時の引換。同時引換は pals-api 側の実 PG テストが対象である。
- 読取関数の ACL 分岐は、実 PG では API の fingerprint 検査が先に拒否するため、単体テスト（偽 DB）でだけ到達する。

## 共有 stack で使うとき

1. `local-qualification-prepare.py --enable-plus-coupons` を、クーポン入りの API source（`67e1156` 以降）に対して実行する。subject に独立キーが入る。
2. API 起動後に、次を実行する。`<env>` は `PALS_HOST_DATABASE_URL`、`PALS_COGNITO_APP_CLIENT_ID`、`PALS_COGNITO_USER_POOL_ID`、`PALS_ENV=local`、`PALS_PLUS_COUPONS_ENABLED=true` を含む private な env ファイル（mode 0600）。

```sh
python3 pals-scripts/local-plus-coupon-acceptance.py \
  --environment-file <env> --api-source <api-checkout> \
  --api-python <api-venv>/bin/python --api-base-url http://127.0.0.1:<port> \
  --subject <runtime>/subject-native.json
```

使い捨てアカウントだけを使い、reviewer アカウントには触れない。確認の PASS を `make release-local-qualify` の結果として扱わない。
