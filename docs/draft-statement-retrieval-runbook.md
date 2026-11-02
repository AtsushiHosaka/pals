# Draft の文検索の投入手順

大学数学と入試の Draft 1,061件を、英語の命題文の embedding で検索できるようにする手順です。本番 DB への投入はありません。行と embedding は封緘ファイル `pals-api/app/domain/draft_statement_catalog_v1.json` として API イメージに含めます。

## 仕組み

worker は依頼文を Luna で英語の命題文に直し、その embedding を API の `/v1/internal/proof-requests/statement-draft-candidates` へ送ります。API はファイル内の全行とコサイン距離で比べ、上位8件を返します。署名済みの `public.dsp_drafts`、従来の XML 検索、Draft の追加候補の表は変更しません。

`PALS_NATURAL_DRAFT_STATEMENT_SEARCH_ENABLED=true` のときだけ、worker はこの経路を使います。未設定なら従来の XML 検索のままです。有効にすると、preflight が `profile_id` を null にした依頼でも検索します。この場合は検索に失敗しても依頼は失敗せず、候補なしとして続きます。

## 表ではなくファイルにした理由

本番の DDL は、変更ごとに専用の署名付き手順を必要とします。`aurora_generation_settings_update.py` は step 数と最終 step を固定しているので、step を足すとこの手順にも手が入ります。Draft の本文は不変で、語彙が増えれば worker と API の再配備がどのみち必要です。そのためイメージに含めても配備の回数は増えません。

トレードオフが2つあります。

- Draft を1件足すだけでも API の再配備が必要です。
- `pals_draft_candidates.published_drafts` の行は、ファイルを作り直すまで文検索に出ません。

## カタログが変わったときの更新

カードを追加したら、親リポジトリのルートで次の順に実行します。`PYTHONPATH` は `pals-agent/testdata/textbook-catalog-v1/README.md` の指定に従います。

1. カタログを生成します。

```bash
(cd pals-agent/testdata/textbook-catalog-v1 && PYTHONPATH=../../../pals-api:../.. uv run --project ../../../pals-api --with pyyaml python catalog.py build)
```

2. 語彙の登録とすべての固定ハッシュを更新します。worker と API は同じ版を同時に配備します。

```bash
python3 pals-scripts/reseal-openmath-v4.py
```

3. 手順2で `pals_agent/openmath.py` が変わるので、新しい語彙を `tier: generic_now` として反映するためにもう一度生成します。

```bash
(cd pals-agent/testdata/textbook-catalog-v1 && PYTHONPATH=../../../pals-api:../.. uv run --project ../../../pals-api --with pyyaml python catalog.py build)
```

4. 封緘ファイルを更新します。既存の embedding は文のハッシュで再利用します。`--embed` がなければプロバイダを呼ばず、足りない行数と概算費用を表示して終了コード3で止まります。

```bash
(cd pals-api && PYTHONPATH=. uv run python -m app.release.draft_statement_catalog_build --drafts ../pals-agent/testdata/textbook-catalog-v1/generated/drafts.json)
```

5. 表示された費用をユーザーに確認してから、`--embed` を付けて同じコマンドを実行します。全1,456行を作り直しても概算で0.1セント未満です。

語彙の登録は増やす方向にだけ変更できます。既存の記号の引数や戻り値を変えると `reseal-openmath-v4.py` が止まるので、別の名前を登録します。同義語は `aliases.yaml` に足せますが、引数の順序と数学的な範囲をカードの使い方で確かめてからにします。たとえば `module_over` は `M R`、`is_module` は `R M` の順です。

## 配備と有効化

1. pals-agent と pals-api の PR を、フラグを付けずに配備します。この時点では動作は変わりません。
2. `published_drafts` の行数を読み取り専用で確認します。結果が0件なら手順4へ進みます。

```sql
SELECT count(*) FROM pals_draft_candidates.selectable_drafts;
```

3. 1件以上あれば、次の形の JSON に書き出して `--drafts` に追加し、封緘ファイルを作り直して再配備します。`{"drafts": [{"id", "canonical_statement", "openmath_xml", "proof_strategy", "sketch_steps"}]}`
4. 本番の worker の環境変数に `PALS_NATURAL_DRAFT_STATEMENT_SEARCH_ENABLED=true` を追加します。`PALS_TYPED_CATALOG_ENABLED` は `pals-infra` の `host-user-data.sh.tftpl` で渡しているので、同じ経路を使うかは配備時に確かめます。
5. 群論の依頼と既存語彙の依頼を1件ずつ送り、記録の `retrieval.query_statement` と候補を確認します。

## 戻し方

フラグを外して worker を再起動すれば、従来の XML 検索に戻ります。DB には何も書いていないので、データを戻す作業はありません。

## 確認済みの内容と未確認の内容

確認済みの内容は次のとおりです。

- 既存の Draft 552件（基底433、seed 31、既存語彙の新規88）は、新旧の検証器で正規化バイト列が一致しました。
- 新規を含む1,062件は、worker と API の両方の検証器で保存値と一致しました。
- 基底433件のうち38件は従来から v4 検証を通らず、従来の検索でも返せません。文検索にも含めていません。
- 実験で保存した56問の英語クエリを実装に通すと、recall@8 は元文 23/23、言い換え 21/23、対照 10/10 でした。モデルは呼んでいません。

- 基底395件から無作為に選んだ20問を Luna と embedding の実物で検索すると、hit@1 は 15/20、recall@8 は 20/20 でした。問題文は正解の Draft を見て作成しました。
- 負例20問でも、検索は常に8件を返します。正解 Draft の距離は76問の中央値が0.209、95パーセンタイルが0.386でした。負例の1位の距離は、カードにない定理が0.333〜0.440、仮定や結論を変えた命題が0.093〜0.331、数学以外の文が0.605〜0.728でした。
- 距離のしきい値では、数学以外の文しか安全に除けません。0.45なら正解を落としませんが、除けるのは数学以外の2問だけです。0.40にすると、正解を3問失い、カードにない定理は10問中3問しか除けません。そのためしきい値は入れていません。

未確認の内容は次のとおりです。

- 負例の候補を受け取った preflight と判定器の動作は測っていません。誤検索を防げるかは、この2つの動作で決まります。
- API を経由した通しの動作は、本番と同じ構成で確認していません。
- 別セッションが作業中のカードは、封緘ファイルに含まれていません。
