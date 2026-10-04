# 現行実装と仕様の監査 — 2026-09-29

## 判定と対象

**FAIL：仕様全体を実装・検証済みとは言えない。** 未実装、仕様との相違、実行証拠不足を区別する。

対象は root `02801ca`、webfront `7837f8f`、API `858dd16`、agent `ab42335` の main と現在の未コミット変更。したがって、この報告は公開済み main 単体の監査結果ではない。実装ファイルは変更していない。本報告のみ追加した。

正本一覧 `specs/README.md` の product-core / lean-recipe-catalog / recipe-curation-proposals / individual-billing に加え、projectless-chat-start、notation、recipe-proof-candidate-source、draft-catalog-expansion、domainless-production-bootstrap の仕様・実装・テストを照合した。全要件の実環境での再実行はしていない。

## 確認した問題

### 1. P1：本番DBリリースに説明再試行の必須migrationがない

DPB-005。本番hostは `pals-infra/terraform/production/templates/host-user-data.sh.tftpl:438` から production_database_release を実行する。`pals-api/app/release/production_database_release.py:165` のstep registryに説明再試行migrationがない。一方、`pals-api/app/infrastructure/bootstrap.py:412` は起動時にそのschemaのpreflightを必須にしている。新規DBをこの自動リリース経路だけで構築するとAPIが起動できない。ローカルrunnerへの追加は本番配線を代替しない。実AWSでは未再現、経路の静的照合による指摘。

### 2. P1：無料枠・生成回数制限・作成冪等性が未接続

BILL-002/003。Free 3回、Pro 100回の予約・作成を同一トランザクションで行う要件だが、`pals-api/app/api/routes/proof_jobs.py:189` はIdempotency-Keyを受けず、`app/application/services/proof_jobs.py:385` は毎回UUIDを生成してjob/outboxを保存・送信する。billing repositoryはread-only foundation。証明作成時のquota admission・予約がない。秘密情報の設定不足ではなく実装不足。

### 3. P2：課金の画面とStripe lifecycleが未実装

BILL-001/004/005/007/010。`pals-webfront/components/BillingCard.tsx:15` とgetBillingSummaryは実アプリから利用されていない。API routerにもbilling routeがなく、Checkout、Portal、署名Webhook、残回数・upgrade導線、usage ingest・worker送信が未完。billing migrationも本番release registryにない。

### 4. P2：説明再試行がアイドル時にもDBを15秒ごとに読む

DPB-009の「候補作業なしでは周期的なapplication-originated DB scanなし」に違反。`pals-api/app/application/services/explanation_retry.py:67` のloopは空でもclaim queryを実行し、`app/main.py:118` が常時起動する。Aurora自動休止を妨げる経路。DPB-013だけを例外扱いするコメントではDPB-009との不一致は解消されない。実AWSの請求・休止挙動は未測定。

### 5. P2：部分質問QAから選択文章が欠落

CORE-003/006。`pals-agent/pals_agent/worker.py:1028` はselected_textを生成へ渡す一方、`:1038` のQA呼出には渡さない。`explanations.py:1118` のQA payloadにもない。別々の式を選択して同じ「なぜですか」と質問すると、QAは選択対象の違いを識別できない。QAは存在するが、対象本文との対応を十分に検査できる入力になっていない。

### 6. P2：補足回答への再質問で親回答の本文が欠落

CORE-003/006。APIは選択文章が親回答にあることを検査するが、workerへ親回答の全文を渡さない。`pals-api/app/application/services/proof_explanations.py:386,498`、`app/schemas/proof_explanations.py:801`、`pals-agent/pals_agent/explanations.py:1057`。親情報はIDで、生成・QAが新しく導入された記号や仮定の文脈を参照できない。ドラッグ操作の成立は、この文脈保持の証拠ではない。

### 7. P2：i18nに未対応箇所と正本仕様との相違が残る

- 数式表記の衝突警告が `pals-webfront/lib/notationPreferences.ts:195`、安全に置換できない場合の警告が `lib/learnerRichText.ts:606` で英語固定。通常のJSX以外の生成テキストが翻訳対象から漏れた。
- CORE-004/006/008は失敗・状態表示を保存チャット言語に指定するが、`components/ProjectDetailScreen.tsx:125`、`components/ProofExplanation.tsx:310,834` はUI言語を使う。直前のi18n修正で切り替えた実装と正本が未整合。ユーザーのi18n依頼だけでこの言語ポリシー変更まで明示承認されたとは扱わない。画面操作とチャット内容・状態の言語方針を確定し、仕様・コード・テストを揃える必要がある。

### 8. P1：自然言語から一致Draftを使うRecipe選択がworkerに未接続

LRC-006/007。API/plannerにはaligned-Draft modeがあるが、`pals-agent/pals_agent/worker.py:902` はformal_declarationのみ渡し、draft_revisionとproof_method_tagを渡さない。自然言語要求から該当Draftの登録済みRecipeを選ぶ実経路が成立しない。

### 9. P2：Recipeを選ばなかった理由が保存されない

LRC-008/009。`pals-agent/pals_agent/worker.py:905` がNoRecipeAttemptV1.exclusionsをNoneへ落とす。APIの選択receipt保存だけでは、未選択時の候補と除外理由のattempt証跡を残せない。

### 10. P2：内部APIの不正認証ヘッダーが500になる

LRC-007、RCP-003/006。`pals-api/app/api/routes/lean_recipe_selection.py:38` と `recipe_curation_proposals.py:138` のcompare_digest(str,str)へ非ASCIIが入りTypeError。ネットワークなしTestClientでヘッダーbytes `b'\xff'` を送り両routeの500を再現。認証突破ではないが、401等の閉じた失敗契約を満たさない。

### 11. P2：本番Googleログインの配線がない

BILL-008。`pals-infra/terraform/production/data_plane.tf:141` はproviderをCOGNITOだけに固定。既存provisionerの存在だけではproductionのHosted UI domain、Google有効化、frontend build配線を満たさない。passwordフローの実装と区別する。

### 12. Recipe評価・Draft拡充は未完

LRC-011/012の実square admission witnessとversioned評価corpus・release gateを確認できない。DCEのrepository inventoryは学校36/321、大学25/500がfilled、admittedはいずれも0。これはrepository上のinventoryであり稼働DB内の公開件数を表さない。typed authoring/loaderはあるがproduction candidate API・profile別公開検索・変更family全体のruntime metrics gateが未完。DCE-003/004/009/010/011/015等に残件。

### 13. 完了記録と検証証拠が一致しない

`docs/recipe-curation-proposals-spec-loop-ledger.md:22` は全要件Verifiedとするが、現行 `pals-api/tests/integration/test_recipe_curation_proposals.py:73,186` は1件のv1ケースで手組みdigestを使い、Recipe schemaがないことを確認する。RCP-T003のv2-model、既存catalog/alignment/receipt/traceの前後不変を証明しない。DPBには逆に実装が存在するのに未チェックのtaskもある。チェック欄・テスト名を完了証拠にできない。

### 14. 課金specと本番インフラspecが衝突

BILL-009はSecrets Manager、billing designはNATを要求。一方、承認済みDPB-008/010はno NAT・SSMを要求。コードはDPB側。課金を実装する前に正本間を整合させる必要がある。

## 要件ごとの残件分類

「未検証」は未実装の断定ではない。実装・unitがあっても、要求する現在のDB/Lean/本番統合証拠が不足する場合を含む。

| 範囲 | 判定 |
|---|---|
| CORE-002/005 | 禁止コード拒否、同一source Lean検証、semantic QA、明示source表示はコードと既存成功例で確認 |
| CORE-003/006 | 部分実装：選択対象・親補足文脈がQA/生成から欠落。QA承認前公開を防ぐ境界は存在 |
| CORE-004/008 | 相違：保存チャット言語の失敗・状態表示と現UI言語表示が不一致 |
| CORE-001/007/009/010、PCS、PNP、APNP | 入力・設定・移行・表示の実装/テストを確認した範囲では、上記以外の新規確定不具合なし。全言語実生成、別端末、移行を含む全AC再実行はしていないため包括的PASSではない |
| BILL-001/006/007/008/010 | 部分実装：独立基盤からアプリ/本番への接続不足 |
| BILL-002/003/004/005 | 未実装：quota、冪等性、Stripe lifecycle |
| BILL-009 | 相違：インフラ仕様衝突、billing runtime設定未完 |
| DPB-005/012/013 | 部分実装：本番migration欠落、全体運用の検証不足 |
| DPB-009 | 相違：idle DB scan |
| DPB-001/003/007/008/010/011/014/015 | 実装・静的テストあり、実AWS plan/deploy/TLS/権限/運用は今回未検証 |
| DPB-002/004/006 | retired、現行完了判定の対象外 |
| LRC-006/008/009 | 部分実装：Draft選択経路と未選択trace不足 |
| LRC-007 | 相違：不正認証500 |
| LRC-011/012 | 未実装：指定実例・評価corpus/gate |
| LRC-001–005/010/013 | 実装あり、現在のPG/Lean/authority/retirement統合実証不足 |
| RCP-003/006 | 相違：不正認証500 |
| RCP-001/002/004/005 | 実装あり、実v1/v2証拠、競合、rollback、既存catalog不変の統合実証不足 |
| RPCS-001–007 | 実装あり、現行PG＋Lean＋reviewおよびRecipe-backed出力の完走証拠不足 |
| DCE-002–007/009/010/012/014–016 | 部分実装：網羅、admission/publication/evaluation、typed runtime等が残る |
| DCE-011 | 未実装：変更family全体のruntime metrics release gate |
| DCE-001/008 | 拡張release/rollbackの現行実証不足 |
| DCE-013 | 不明：全本文の原著性照合は今回未審査 |

## 検証と限界

- frontend notation・language status：3 files / 30 tests PASS。
- agent explanation/shape/deadline/Lean：110 tests PASS。
- API billing foundation/migration/release/startup：14 tests PASS。
- Recipe関連：API 25、agent 47、coverage 13 tests PASS。
- production-cost-boundary.sh、repository-only inventory：PASS。
- これらのPASSは上記残件を否定しない。例：migration単体テストは実registryへの登録を見ず、cost-boundaryテストは新retry loopを見落とす。先行ターンのfrontend全863 tests PASSも仕様全体の完了証拠ではない。
- 今回は外部モデル、Stripe、AWS、DB変更、ブラウザ追加起動、コンテナ追加起動を行っていない。過去の二項平方成功例は参照したが、任意の証明品質や4言語すべての実生成を保証しない。

修正順序は、本番起動阻害とidle DB scan、部分質問の文脈/QA、言語ポリシーと翻訳漏れ、課金/Recipe接続、評価gateと証拠の更新。仕様変更だけで実装欠落を完了扱いにしない。
