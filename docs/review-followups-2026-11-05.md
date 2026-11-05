# 11月5日の追加レビューと検証

担当はCodex。[担当チャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)、全体の進行は[#237](https://github.com/AtsushiHosaka/pals/issues/237)に記録する。3つのサブエージェントと親担当が、実装・独立レビュー・統合を分担した。本書は局所検証と本番受入を分けた記録である。

## 保護設定の限定読取

オーナーの明示承認とSSO認証後、11:13:35 JSTに正規SSM経路から指定した1項目だけを読んだ。直前に現行manifest・署名・公開鍵pin、設定と環境参照のhash・所有者・modeを検査した。SSM実行1回、IAM追加・KMS署名・DB更新・サービス変更は0回だった。値は公開せず、Git外の保護領域へhash一覧とともに保存した。

API5c1a2fd7・Web11b62967の正式image receiptと未署名seq19候補を固定した。receipt SHA-256はa372af8d76076a7d307f0742e7e512184466ea1489aae7e221447f10a4a04bda、候補はfa94cf782cbb20c2ffcac4134b725ff34ee813389d0a3746cd6cc526f2f9eb51。旧sourceのimage・receiptは履歴として保持する。親担当が前署名・全4imageの対応・保持する資源とSQL/registryを独立照合し、local-only checkも成功した。[#255](https://github.com/AtsushiHosaka/pals/issues/255)で署名・全読取検証の承認を受領したが、直前に別チャットがshared-card seq19を本番適用済みと確認した。旧seq18を前提とする候補は使用停止し、署名/IAM/追加SSM/native/DB/サービス操作は0回のまま保全する。承認を新digestへ流用しない。現行seq19の原本と進行中#248を確認し、新候補を具体化する。進行は[#234](https://github.com/AtsushiHosaka/pals/issues/234)と[#244](https://github.com/AtsushiHosaka/pals/issues/244)を参照する。

## 再現した問題と修正先

| 対象 | 確認した問題 | 修正と現在の範囲 |
|---|---|---|
| API#47のTLS fixture | 削除済みクラスタのCA・固定principalに依存していた | 明示した所有クラスタとTLS設定を使う修正を統合済み。後述のquery user問題も追加修正した |
| API/Webのタイトル | 全starの除去で双対空間や積の記号を失った | 数式区間を保護。初回修正後に見つかった長文・入れ子も修正し、元のAPI#44/Web#40へ統合済み |
| Agent#49の品質分類 | lean.not_found・lake.not_foundをruntimeに分類していなかった | Agent#54を#49へ統合。#51にも通常mergeした |
| Agent#49の実parser | lean.error・lean.unknownIdentifierを取りこぼした | 同じ修正で閉じた対応表と共有Schemaへ追加した |
| API#49の保存済み診断 | verifier_compile_failed・pals.proof_semantic_review_failedが未対応だった | API#56を#49へ統合。#52への反映を検証中 |
| 支払receiptの回収 | 古い失敗行が小さいbatchを占め、後続が進まなかった | API#53で試行時刻の確定と公平な順序、排他を実装。#57/#59で元の#50/#51へも反映した |
| Agent#52の評価記録 | parse・serialize失敗時にraw responseを保存できなかった | e46a6fcで先にraw envelopeを保存。親担当も8件を独立検証した |
| 保存済み親説明 | 引用の改行を復元すると不変な親ハッシュと一致しなかった | Agent#55/API#60でモデル用引用と保存済み親のidentityを分けた。新規引用・親差替えの拒否は維持した |
| 追加質問のclaim | 現APIのnullableなoutput_languageを旧workerの閉じたDTO検査が拒否した | Agent#55で実際に対応する4言語・null・省略だけを許可。未知の値や項目は拒否する |
| 回答QA | 実在しない欠陥を正しい段階へ追加した | 最初の改善案は失敗。唯一の追加修正を別の固定群で評価し、結果を下記へ分けた |
| runtime診断のHTTP経路 | 元のruntime診断をcompileへ集約していた | API#64/Agent#56で閉じた2コードを保持し、API/DBで修復不能として終端。独立実PG/mTLS16件も通過し、後続統合branchへmergeした |
| TLSのquery user | authorityのactorよりqueryのuserが優先された | API#61を#47へ統合。実libpq・実接続で指定actorとTLS1.3を確認した |
| 長いタイトル | regexの後方走査が入力増加に対して急増した | 線形stackへ変更。下記の同一入力による局所測定を残した |
| タイトルの入れ子 | 外側のitalicと内側のboldを併用すると末尾starが残った | 同じstackで修正し、API/Web/OGの回帰を追加した |

API#56のcodeは1a69a129、元#49のmergeは02c992b。Agent#54のcodeは0091159c、元#49のmergeはcda8e32。Agent#51の統合head58de877では関連562件が通過した。共有品質SchemaのSHA-256は675641f307a49e01cbee376e0a24339cb0046813971574198e2c7ab4a5e7155aである。

親参照・claim互換性は、Agent0f68acfbとAPI3b41a04aから実worker・実API route/認証/DTO/サービス・実Postgresへ通して独立検証した。5種類の改行、保存親の不変性、親ハッシュの差替え409、新回答のLF引用409、呼出側互換flagの422を含む10件が通過した。生成器・QA・検証済みジョブは明示したfixtureで、実モデル・Lean・SQS・本番を通す試験ではない。

TLSの追加修正e920777dは、局所29件と実PG接続3件、計32件を親担当も独立検証した。query userの単数・重複・encoded keyを除去し、接続先を変えるqueryは拒否する。TLS・認証設定のpercent encodingとliteral plusは保持する。新しい空の専用DBだけを作成・削除し、role・schemaは変更していない。共有サーバーの停止も行っていない。独立した両検証のログSHA-256は8527dde53f0ca7faab113e9a90a9c204c178e3c38ea453113b7c86a60d045d53である。

支払回収の実PG検証では、失敗・取消後も試行時刻が残り、後続へ進むこと、実処理中は同時回収を拒否することを確認した。親担当の独立5件も通過した。定期runner、本番Stripe capture、全体の実行期限、保持期間後の定期削除は別の残作業である。

## タイトル変換の局所測定

同じmacOS・Python3.14で、文字列の変換だけを各1回測定した。入力は公開可能な人工文字列の反復で、モデル・DB・ネットワークを使わない。すべてで期待する出力を得た。所要時間は各1回の経過時間であり、中央値・p95・利用者の応答時間ではない。

| 入力文字数 | 変更前の秒 | 変更後の秒 |
|---:|---:|---:|
| 750 | 0.002000083 | 0.000122041 |
| 1,500 | 0.007719625 | 0.000216542 |
| 3,000 | 0.029157041 | 0.000553333 |
| 12,000 | 0.409642500 | 0.001744500 |

変更後の測定source SHA-256は3ab871f5b263623b03dcbccbd7af86df7b41a3c6a5f0e0815bf06449c950ec37。rawの測定結果と前後のsourceはGit外へ保存した。両版で測った4つの長さを、それぞれ台帳1行に記録する。数学の成功率や本番の速度改善へは加算しない。

独立レビューでも同じ実sourceを使い、1,000・4,000・16,000反復のCPU時間を各3回測った。各条件の中央値は0.000498・0.002001・0.007484秒だった。これは前表と異なるCPU時間の測定であり、前表へ混ぜない。64段の入れ子、未閉script、Unicode・emoji、連続starも確認した。これらの回帰テスト件数は精度台帳へ加えない。

## QAの失敗案を保持する

根拠形式を強めた最初の案は受入未達だった。同じ4入力を旧版・候補へ各3回渡す24QAを事前登録し、生成・修復・再試行は行わなかった。厳格な成功は次のとおりで、拒否に別の誤った理由を付けた場合も失敗に含めた。

| 固定入力 | 旧版 | 最初の候補 |
|---|---:|---:|
| Coprime正例 | 3/3 | 3/3 |
| Energy正例 | 2/3 | 2/3 |
| 結論欠落 | 3/3 | 0/3 |
| 未証明の同一視 | 1/3 | 3/3 |

結論欠落の誤承認3件が残ったため、この候補は採用しなかった。旧新版で別の問題を指摘する場合も、実際の入力とLeanの行へ対応させた。全24件のraw verdict・rationale・保存結果を再照合し、採点変更は0件だった。指摘形式が整っていても数学的に誤った拒否は成功にしない。

入力92,070・出力5,044 token、推論2,851は出力の内数だった。usageは24/24で欠損なし。予算用の見積もりは0.02553950 USDであり、請求額ではない。結果outcomesのSHA-256はa8e20673e95e79e9dbc1f67e37f663607eff22acd1dbfa50778872d25de35a43、採点は269373805f3ae042e17a94c525095e3e51e108deb668d875534fa8d371778da0である。[Agent#53の失敗案の記録](https://github.com/AtsushiHosaka/pals-agent/blob/580ef9033d324803d82743d57ab1550e4c8c7289/testdata/qa-grounded-rationale-v1/README.md)を根拠として、入力4種類×版2種類の8行を台帳へ追記する。過去の評価を上書きしない。

## 唯一の追加修正と固定QAの結果

最初の失敗を受け、具体的な結論を説明の結論欄そのもので確認し、全判定に実在する短い引用と要件への対応を書くよう修正した。追加質問には別のanswer用の確認指示を使い、存在しない結論欄を要求しない。候補sourceはfc7e58b5857921d5fbe3124fec04a547600024c9、moduleのSHA-256は82310b14357c55524edf70ec09cc68b0531dfb834f2f3308e9e83e12f244b8b6である。

同じ4入力・順序・旧版23e903fを保持し、各3回、計24QAを03:03:05〜03:06:00 UTCに実行して停止した。再試行・修復・追加生成・測定中のsource変更は0回。preregのSHA-256はb8e892c09b1f38db9e4d40060a872e1d2047f9e6e8f2eeb243636f3da6f2b903である。

| 固定入力 | 旧版の厳格成功 | 追加修正の厳格成功 |
|---|---:|---:|
| Coprime正例 | 3/3 | 3/3 |
| Energy正例 | 3/3 | 3/3 |
| 結論欠落 | 3/3 | 3/3 |
| 未証明の同一視 | 1/3 | 3/3 |

旧版の負例2件は、実際の参照範囲に含まれる宣言の見出しを欠落と誤指摘した。拒否自体は正しくても厳格成功から外した。親担当は全24の理由を読み、固定入力hashと実Leanの見出し・参照を独立照合した。候補の結論証拠12/12、拒否6件の欠陥の引用と理由も、数学的正否とは別に確認した。

入力96,138・出力5,141 token、推論2,556は出力の内数。usage・raw・固有response IDは24/24で欠損なし。予算用見積もりは0.02660500 USD、最初の失敗群との合計は0.05214450 USDである。[OpenAI公式標準料金](https://developers.openai.com/api/docs/pricing)の確認に基づく全入力0.25 USD/百万token・出力0.50の保守値で、請求額ではない。応答のcache保持表記と請求料金の対応は未照合のまま残す。

[Agent#53の最終報告](https://github.com/AtsushiHosaka/pals-agent/blob/bf7a7bac15bb2554e8aa647023babd9ddc11295c/testdata/qa-semantic-priority-v1/README.md)を根拠として、8行を別群で台帳へ追記した。採点SHA-256はbc91a484af46062c2961bf05bd681a2ab7d7441793eb9a4f574f272b90cebb5f、metricsはe5f1d0f869617147e50d8f83676799db086be42d39ede1c986289ac9a8ad3bb1である。Agent#53は限定受入後に#51へ通常mergeし、関連574件とraw保存16件、計590件の回帰が通過した。同名の評価用testを同時指定した初回の収集エラーは記録し、raw保存の組はimportlibモードで分離した。

この4入力は同じ保存出力の反復で、一般の数学的精度・本番の不具合率・生成全体を証明しない。追加質問のpromptは静的回帰だけで、今回の実モデル測定には含めていない。最初の失敗群と合算して改善率を作らず、追加の有料反復も行わない。

## 本番で残ること

新sourceの実image・receipt・未署名候補、schemaの正規適用、公開画面・Cognito引換・実Plus機能、CloudWatchの収集・抽出・アラーム遷移を確認する。クーポンは未発行、価格は未変更、AWSの縮小も未実施である。局所検証やmergeだけで、対応する本番受入Issueを閉じない。

タイトル修正では追加レビューのたびに、括弧付き積、既存italicの閉じ側、italic内の単語間の積を確認した。F15の修正がF16の回帰を残したため、API#65/Web#46で積の保護とitalicの条件を分けた。最終統合はAPI#48の5c1a2fd791b63228c60376527cbf9f5c18014939、Web#40の11b629673a70b39bfdbf2faf315f6cc9ea696aef。API対象66件、Web対象91件を親担当・別担当が確認し、API統合122件、Web全145ファイル1,891件、型・lintも通過した。既存の線形性・script・Unicodeの期待値は弱めていない。

Web全体の過去2回は110秒でtimeoutした。単独検査と残存processの不存在を確認後、並列数4で全件を完了した。timeoutの原因は断定しない。前述の局所速度測定は3ab871f5のsnapshotであり、最新F16や本番の速度として読み替えない。

## 後続のruntime・試験分離・取り込み

API#64とAgent#56は実mTLSのverifier HTTPからAPI・PGへ、lean.not_found/lake.not_foundの閉じた診断を保持する。元のpath/message/symbolを公開eventへ出さず、修復不能の終端とhold解放を確認した。model/recipe/refutation経路、telemetry無効、既存usage、再配信、通常のcompile修復と否定fallback、同時reconcileとCOMMIT応答損失を検査した。親担当は製品差分を読み、独立担当の実PG16件・Agent HTTP38件・API単体112件を確認した。受理済みrequest・catalog・生成・正常compileの一部は明示fixtureで、実モデルや生成全体の試験ではない。

API#66では試験用DSNのquery dbnameがURL pathより優先する問題を修正した。queryのencoded/repeated keyを実libpqで解釈し、接続前とSELECT current_database()で自分のUUID DBへの接続を検査する。既存の他の接続設定は保持し、失敗したCREATEの後にはDROPせず、正常に作ったDBだけをplain DROPする。親担当の14単体・11実PGも通過し、前後の全DB名とrole flagsが一致した。実際の試験DSNにquery dbnameはなく、既存DBを破壊した事実は確認していない。API#52は6985402、Agent#51は74a6d5eとなった。coupon36のsourceは変更していない。

親PR#254の取り込みCLIは、既存2群のraw・人手採点・usageから候補CSVを作る。独立レビューで、保持表記24hを未照合で固定する不足を修正し、両schemaで原本との一致を必須にした。22件と、既存2群8行ずつの全20field照合が通過し、親#243へ統合した。自動採点・台帳append・将来の全schema対応は含まない。

新Agentのproject metadataに対応するinfra#98は、明示profileだけでdev依存のjsonschemaと共有schemaのwheel同梱を許可する。旧default・runtime依存・canonical source tarは維持する。独立レビューで、docker create直後のtimeout時の所有物回収と、publish直前のcanonical archive再照合に不足2件を再現した。修正・再レビューが終わるまで採用しない。ここまでのDocker/ECRは境界fixtureであり、このprofileでの実image build・publicationは0回である。

## mainの本番検証台帳との統合

別チャットがmainへ公開した共有カード本番検証19行を、こちらの314行へ追加して333行とした。双方に同じidで値の違う行はなく、こちらの314行はbyte単位で保持し、両側の全20fieldとidを照合した。出典内訳はdocs203・Agent PR80・Issue22・親PR28、AWS39・local macOS220・不明34・その他40である。台帳監査エラー0、6グラフを再生成して目視確認した。別の測定群の率を合算して精度改善としない。

独立確認でREADMEの3分類だけが295行時点のままと判明したため、333行の実集計へ訂正した。台帳の値とグラフは一致しており、CSVの再変更や再生成は不要だった。統合後の関連単体は専用14件とaudit8件の計22件が通過した。
