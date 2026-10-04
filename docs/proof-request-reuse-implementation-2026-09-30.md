# Leanを待たない証明回答の実装記録

2026-09-30。ユーザー承認に基づくローカル実装・検証。本番にはデプロイしていない。既存の未コミット変更を保持し、stage／commitはしていない。

## 実装した動作

- 通常処理はGPT-6 Luna。数学的判断が未解決の場合だけGPT-5.6 Terraへ1回昇格。Solは使わず、通信・構文エラーで上位モデルへ昇格しない。
- 実DraftをLLMが評価し、直接利用、一般定理の具体化、独立した導出を選んで回答する。Leanは実行しない。回答は`llm_assessed`で、形式検証済みとは表示しない。
- 前提が欠ける場合だけ質問する。「この証明でよいか」の確認操作はない。質問・回答・元の要求を同じrequestに保存し、再読込後も続けられる。
- APIは所有者、冪等性、lease、outbox、使用量、共有利用枠を管理する。質問待ち・失敗ではholdを解放、再開時に再取得、回答完了で1回消費する。
- プロジェクト内／外の通常チャットを新経路へ接続。既存の形式証明履歴は読める。出典と具体化の記録は、正式なRecipeやLean検証済み証拠へ自動昇格しない。

仕様は [requirements](../specs/proof-request-reuse/requirements.md)、[design](../specs/proof-request-reuse/design.md)。モデル単価・Decisions APIの調査は [調査記録](proof-reuse-latency-decisions-research-2026-09-30.md)。Decisions APIは公開価格・利用条件を確認できておらず、導入していない。

## 最終版の実測

既存ローカルサービス、実PostgreSQL、実Draft431件、実モデルを使用。固定回答・seed注入・HTTPモックは使っていない。

| 検証 | 結果 | 処理時間 | 費用推計USD |
|---|---|---:|---:|
| 実数上でx²が連続 | answered、continuous_squareを引用 | worker 17.091秒、受付から17.760秒 | $0.001391 |
| fと定義域が未指定 | needs_input | 4.738秒 | $0.000099 |
| f=x²、定義域・値域がℝと回答 | 同じrequestがansweredへ再開 | 15.094秒 | $0.001250 |
| 一般定理を検索しn=2に具体化 | continuous_powerを取得、instantiate | 22.297秒 | $0.001526 |

- 直接回答ID：`848537fc-8986-4557-945b-83187206e972`。rev2で完了、出典hash `97ca6dd7…8fce87`。
- 質問・再開ID：`1cd1e598-411e-44a1-877d-f8326117d4d2`。needs_input rev2→回答送信→answered rev4。Q/A1件を保持。両requestとも消費は1回、outbox完了、同チャットの旧Lean jobは0件。
- 一般定理のprobeは実worker内でruntimeを直接呼んだ検証で、保存済みユーザーrequestではない。`continuous_power`の実際の束縛名`v1`へ整数2を代入し、Nat型と`2∈N`の前提を保持した。出典SHA256は`d132d6183073f113f986b1cb981bc45091964ad7b60ec7ac77aec95d4a81a3d8`。独立した帰納法で一般定理の根拠を再構成し、平方の場合を仮定する循環はなかった。証拠種別は`structural_instantiation_only`、回答は`llm_assessed`。
- 具体化はLuna3回（入力5274・出力1714）、embedding389トークン。推論トークンは出力に含む。TerraとLeanは0回。
- 金額はcache-write単価を用いる保守的なアプリ内推計で、実請求額ではない。数件のスモーク結果であり、p50/p95、精度の母集団評価、旧経路との同条件比較は未実施。

ブラウザは「通常回答→再読込→前提質問→再読込→回答→同request再開→再読込」の全行程を48.8秒で通過。承認checkboxなし、旧proof-job作成なし、ページ／console／対象HTTPエラーなしを検査した。画面も目視確認した。

生成証跡はgit対象外の`output/proof-request-reuse-20260930/`に保存：`proof-and-premise-resume.png`、`browser-public-results.json`、`general-theorem-instantiation.json`。認証情報や生HTTP traceはこの保存物に含めない。

## 検査と実行中に直した問題

- Web：全984テスト、型検査、ESLint成功。古いcallback対策の追加を含む20件と、最終ブラウザ変更後の型検査も成功。
- Agent：最終282テスト、Mypy 8モジュール、Ruff成功。最終の自然検索境界は独立レビュー79件も成功。
- API：実PostgreSQL10件、契約6件、既存関連133件、自然候補／releaseの単体・契約49件が成功。Ruff/Mypy、manifest整合も成功。
- 実DBチャット検索のdesktop/mobileと実プロジェクト作成のブラウザ2件も成功。
- 実行時に発見した、不要な3回の検索式修復、一部の古いDraftによる検索全体の失敗、生XMLの閉じタグ欠落、検索profile外の演算子、binderの誤用を修正した。
- 検索hintはstrict JSON treeから決定的にXMLへ変換し、実indexに一致するv2正規化を使う。出典はv4検査・内容hashを維持。自然検索専用の証跡には実cosine distanceを記録し、PFIの形式的同値性スコアは流用しない。
- モデル生成検索式のローカル不正だけは失敗・使用量を保存し、既定の最終判断で独立導出できる。コードで出典と置換を空に制限する。出典必須ならsource-free成功を禁止し、DB／provider障害・metadata／source整合性エラーには適用しない。
- 無料枠を使い切った既存QAアカウントでは402を確認。枠を変更せず、通常のローカルCognito登録による専用QAアカウントで最終検証した。

## DB権限とリリース条件

実DBには従来のDraft431件がある一方、新PFI／typed公開世代は未配置だった。自然言語回答専用の読み取りAPIを追加し、正式カタログの公開条件は変更しない。

専用NOLOGIN/NOINHERIT役`pals_natural_draft_reader`には、Draftの内容・embeddingと検索metadataのSELECTだけを付与した。当初の自動承認拒否後、具体的SQLへのユーザーの「許可」を受けてローカルに適用。[対象SQL](../pals-api/docs/api/natural-draft-reader-grants.sql) を参照。実権限検査で管理flags、Draft INSERT/UPDATE/DELETE/TRUNCATE/列UPDATE、chatsアクセスはすべてfalse。再bootstrapも成功。実候補APIは200、検索27ms、返却source hash再計算一致（この27msはLLM時間を含まない）。

最終時点で既存pals-localの9サービスがhealthy。新しい常設コンテナは作らず、別タスクのAPI更新と重なった後はworkerだけを更新した。並行作業中の任意token-accounting変更は保持し、通常claimに追加operation IDがない経路で検証した。その別機能の認定は本記録の範囲外。

本番は旧worker停止→migration→API→新worker→webの既存一括手順で更新する必要がある。新UIだけの先行公開は不可。本番releaseへ専用reader DSNを渡す修正とproduction cost/isolation boundaryテストは成功したが、本番権限変更・デプロイは行っていない。旧mini専用PFI評価はLunaを旧miniと誤記録せず`runtime_incompatible`で拒否する。旧形式経路をLunaで再認定する場合は別の評価証跡が必要。
