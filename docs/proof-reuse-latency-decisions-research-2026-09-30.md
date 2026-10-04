# Luna のモデル比較と Lean を待たない証明回答の設計

2026年9月30日。PALS の通常回答は、LLM が既存の証明を選び、必要なら一般定理を具体化して、Lean を実行せず返す設計を提案する。ユーザーへの採用確認は挟まない。質問するのは、会話から確定できず、答えや証明方法を変える前提が欠けた場合だけとする。

ユーザーの実装承認により、通常は **GPT-6 Luna**、数学的な適用判断が解決しない場合だけ **GPT-5.6 Terra** を使う。Solは採用しない。価格は公式資料で確認したが、PALSでの精度・応答時間は別途評価する。実装仕様は [proof-request-reuse](../specs/proof-request-reuse/requirements.md) を参照。

## GPT-6 Luna は GPT-5.6 Luna より安い

標準テキスト料金、100万トークン当たりの USD。比較例は入力3,000・課金対象出力100トークンの判定を1万回実行した場合。推論トークンも出力100に含む仮定で、キャッシュ読み書き、長文割増、再試行、ツール費は含めない。

| モデル | 入力 | 出力 | 比較例の費用 | 今回の位置付け |
|---|---:|---:|---:|---|
| GPT-5.4 mini | $0.75 | $4.50 | $27.00 | 現行の比較基準 |
| GPT-5.4 nano | $0.20 | $1.25 | $7.25 | 前回比較した安価なモデル |
| GPT-5.6 Luna | $0.20 | $1.20 | $7.20 | ユーザー指定の評価候補 |
| GPT-6 Luna | $0.10 | $0.50 | $3.50 | 通常の適用判断・回答の第一候補 |
| GPT-5.6 Terra | $2.00 | $12.00 | $80.00 | Lunaで解決しない数学的判断に1回だけ使用 |
| GPT-6 Astra | $10.00 | $50.00 | $350.00 | 評価用の比較候補。通常経路への採用は推奨しない |
| OpenAI Decisions API | 未確認 | 未確認 | 算出不可 | 価格と利用条件を確認してから比較 |

単価の出典は [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)、[GPT-5.4 nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano)、[GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)、[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)、[GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra)、[公式料金表](https://developers.openai.com/api/docs/pricing)。比較例は独自計算で、PALS の実績ではない。

この仮例では現行 mini に対し、5.6 Luna は約73%、6 Luna は約87%安い。5.6 Luna と nano の差は小さい。6 Luna は5.6 Lunaに対して入力単価が50%、出力単価が約58%安い。安さを理由に5.4 nanoへ戻すより、Lunaを評価する方が有力と考える。

性能にも改善の根拠がある。OpenAI は AutomationBench で、GPT-6 Luna の high effort が前世代より5.4ポイント改善し、タスク当たり費用は58%低下したと報告している。ただし、これは業務操作の評価であり、PALS の定理適用や前提検出の正答率ではない。[GPT-6 Sol and Luna 発表](https://openai.com/index/introducing-gpt-6-sol-and-luna/)

5.6 Luna と6 Lunaはいずれも推論量を設定でき、既定は medium。単純な選別は low、具体化の適用条件を確認する問題は medium を出発点に比較する案とする。これはPALS向けの提案であり、精度が確認済みの設定ではない。max を一律に使うと、単価が低くても推論時間と使用量が増える可能性がある。[5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)、[6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)

TerraはLunaより高価であるため、通常処理には使わない。数学的な判断が未解決のときに限り1回だけ昇格し、通信失敗・料金制限では昇格しない。標準tierの公式単価と、キャッシュ書込費用を含む保守的なアプリ内推計は区別する。現行usage契約では書込トークンの内訳が得られないため、新モデルの推計は入力全量をcache-write単価（Luna $0.125、Terra $2.50 / MTok）で見積もる上限値として記録する。272kを超える入力では公式の長文倍率も適用する。[Terra公式仕様](https://developers.openai.com/api/docs/models/gpt-5.6-terra)

## LLM が使えると判断した証明をそのまま返す

提案する分岐は次の四つ。モデル自身の確信度だけで決めず、採用する定理、前提の充足、置換、要求と結論の対応を構造化して記録する。

| 判断 | 動作 |
|---|---|
| そのまま使える | 保存済みの証明を要求に合わせて提示し、回答を完了する。Leanは実行しない |
| 一般定理を具体化すれば使える | LLMが適用を計画し、変数・型・前提を軽量に検査して証明を返す。Leanは実行しない |
| 重要な前提が不明 | 必要な質問だけ返す。回答後は元の要求に戻って自動継続する |
| 候補だけでは証明できない | 探索・推論を続ける。難しい場合は強いモデルや既存の生成・Lean経路へ進める |

Leanなしの回答も正常完了として扱う。完了状態と検証方法を分離し、例えば `answer_status=completed` と `evidence_kind=llm_assessed` を別々に保存する。検証していない回答に「Lean検証済み」と付けなければよい。形式検証の有無は詳細情報に表示し、証明の採用確認を要求しない。

現在の `verified` は Lean と意味レビューの成功に結び付いている。既存の成功フラグだけを強制設定する変更では、この方針を正しく表せない。Lean済みの保存成果物を再利用する場合は、その検証記録も参照できるようにする。[CORE 要件](/Users/atsushi/Desktop/projects/personal/pals/specs/pals-product-core/requirements.md:13)、[ProofJobState](/Users/atsushi/Desktop/projects/personal/pals/pals-api/app/domain/models/proof_job.py:24)

待ち時間を減らすには呼び出し数も抑える。前提抽出を既存の構造化処理に組み込み、検索後の適用判断と具体化計画を一回にまとめる案とする。理由は短いコードと根拠に限定する。定型の具体化は保存済み本文から構築し、文章を書き直す必要がある場合だけ追加の生成を行う。過去に同じ要求・前提・言語へ返した回答も再利用できる。

## 一般定理の具体化を検索の対象にする

例えば、既知の定理が「任意の自然数 n について、実数上の関数 x↦xⁿ は連続」で、要求が「実数上で x² が連続」であれば、次の適用になる。

1. 指数 n は任意の自然数であることを確認する。
2. n に2を代入し、2が自然数という条件を満たすことを確認する。
3. 定義域・値域・位相が要求と一致することを確認する。
4. 「一般定理に n=2 を適用すると、x² は実数上で連続」と返す。

ユーザーがε–δの定義からの証明を求めている場合は、定理を引用する一文だけでは要求を満たさない。その場合は一般証明の手順も具体化するか、別の証明を選ぶ。自然数指数の定理を n=-1 や n=1/2 にそのまま適用しない。存在量化された変数を任意の値に置き換える操作も認めない。

保存する適用記録には、元の定理IDと版、量化された変数と型、置換 n→2、必要な前提とその根拠、導かれた命題、要求した証明方法、利用した他の定理を含める。置換は文章中の文字列操作ではなく、式の構造上で行い、束縛範囲と変数名の衝突を検査する。こうした検査はLean起動を必要としないが、形式検証と同等の保証を主張するものではない。

検索は完全一致に加えて「この結論を導ける一般定理」を候補化する必要がある。式の主要演算、定義域、結論の種類で候補を広げ、LLMが置換可能性と前提を判断する。最初は全称変数への値の代入から始め、変数名変更、定義域制限、既知の定理の組合せへ広げる。式の見た目が似ているだけでは採用しない。

既存seedには `continuous_power` があり、自然数nと実数上の連続性をOpenMathで表している。ただし内容は証明方針とsketchであり、検証済みの一般定理だと断定できない。さらに `continuous_square` への参照がある。平方の連続性を証明するために、平方の連続性に依存する一般定理を使う循環は避ける必要がある。確立済みの独立した一般定理か、証明に何を仮定したかを依存関係として記録する。[seed](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/seed/dsp_drafts.json:16)

関連Draftへの言及だけで循環とは判定しない。手法を参考にする関係と、真であることを前提として引用する関係を分け、後者で循環を検出する。現sketchも積と帰納法から独立した一般証明へ展開できる可能性がある。

現在の `exact_equivalence` はOpenMath XMLの一致なので、n→2を適用関係として扱えない。型付きASTには束縛変数とbodyの構造があるが、typed-real-analysisの指数は0〜64の自然数リテラルに限定される。一般のnを扱うにはprofileの拡張または一般定理用の表現が必要である。[一致判定](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/proof_flow_evidence.py:46)、[AST](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/typed_openmath_ast.py:99)、[指数の制限](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/typed_real_analysis.py:493)

## 前提不足だけをユーザーに質問する

「この証明でよいですか」という確認画面やチェックボックスは設けない。LLMは会話と問題文から既知の前提を回収し、未確定の前提が答えを変えるときだけ質問する。例えば「xの範囲が未指定です。実数として扱いますか？」。会話でℝと指定済みなら再質問しない。検索が失敗しただけ、モデルが証明を思いつかないだけの場合は、ユーザーへの前提確認にすり替えない。

単に定義域名だけでは足りない場合もある。一般の空間で連続性を論じるなら、定義域・値域と位相を確認する。複数の不足項目は一度に短く聞き、回答後に確定した前提を表示して訂正可能にする。

現UIは入力するたびに新しいproof jobを作り、APIは直ちにキューへ投入する。「実数です」だけを入力しても、元の質問への回答として再開する仕組みはない。既存のclarificationsは証明後の説明に対する質問なので、生成前の前提確認とは別に扱う。[送信処理](/Users/atsushi/Desktop/projects/personal/pals/pals-webfront/components/ProjectDetailScreen.tsx:483)、[job作成](/Users/atsushi/Desktop/projects/personal/pals/pals-api/app/application/services/proof_jobs.py:407)、[説明への質問](/Users/atsushi/Desktop/projects/personal/pals/pals-api/app/api/routes/proof_explanations.py:74)

設計案は、同じchatに属する永続的な証明要求をjobの手前に置くこと。元の問題、確定した前提、質問と回答、要求の版を保存する。状態は `assessing → needs_input → assessing` と進み、適用できれば直接 `answered`、新規生成が必要なら既存jobへ一度だけ接続する。質問への回答は新しい証明要求にしない。再読み込みや重複送信でも、元の文脈と同じ処理を保つ。

回答待ちの間はLeanや証明生成を開始しない。前提判定自体のLLM費用は発生するので、新しい要求IDに紐付けて計測する。現行jobのclaimに限定したusage報告・利用枠判定も見直し対象であり、「Leanを使わないから費用ゼロ」とは扱わない。

## DBには一般定理と適用履歴を分けて蓄積する

n=2、n=3ごとの類似Draftを増やすより、一般定理を一つ保存し、具体化とその利用結果を別に記録する。元定理の版、要求の前提、置換、生成した証明文、判定モデルと設定、利用した根拠を残す。LLMが採用した履歴は、そのまま正解ラベルや形式検証済みの証拠にはしない。

後日、独立レビューや任意のオフラインLean検証で品質を確認し、結果を同じ回答の版に追加する設計が考えられる。これは通常回答の完了を待たせる条件にはしない。現行のRecipe Curation Proposalはverifiedな候補を対象とするため、LLM評価だけの回答を直接Recipeへ昇格させず、候補として別に扱う。[既存候補化処理](/Users/atsushi/Desktop/projects/personal/pals/pals-api/app/infrastructure/recipe_curation_proposals.py:226)

## Decisions API を待たずに Luna で比較できる

OpenAI Decisions APIは有限選択の判定を想定し、公式発表時点では限定プレビュー。9月30日の公開資料では固有の料金と利用条件を確認できない。Luna通常APIの価格をDecisionsの価格とみなさない。[公式発表](https://openai.com/index/devday-2026-recap/)、[料金表](https://developers.openai.com/api/docs/pricing)

「直接使用」「具体化」「前提質問」「探索継続」の判定には適合しそうだが、具体化計画や証明文の生成には通常の生成APIが必要になり得る。まずLunaの構造化出力で一連の判断を比較し、Decisionsに分割することが呼び出し回数・時間・費用の削減になるか後から測る。選択肢が有限でも数学的誤判断は起こり得る。

## 実装前に比較する項目

モデル比較では同一の評価問題を使い、現行mini、5.6 Luna、6 Lunaを判定・具体化・回答まで通す。TerraはLunaで解決しない問題の追加評価に使う。数学的な誤採用率、必要な質問の見落とし、不要な質問率、証明方法の遵守、p50/p95応答時間、推論と再試行を含む費用を測る。モデル自身の確信度を評価の正解には使わない。

最低限の評価例は、一般の自然数指数から2への具体化、負数指数の誤適用、ℝとℂの混同、存在量化の誤適用、証明法指定、循環参照、既に会話にある前提、前提不足からの再開。正解ラベルは独立に確認する。数学的正誤と、ユーザーが求めた証明への適合性を別に評価する。

リリース設定は現在、各役割を `gpt-5.4-mini-2026-03-17` に固定している。採用時には役割ごとのモデル設定、API呼び出しパラメータ、料金レジストリとusage報告を一緒に更新する。新モデルの未知の日付付きsnapshotを推測で作らない。[model_roles.py](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/model_roles.py:27)

現行の生成省略経路でもRecipeは再度Leanへ送られる。通常pipelineはAPI側の検証に委ねる設定で、workerとAPIの二重コンパイルが原因というわけではない。新設するLeanなし回答経路と、既存の形式検証経路を区別して計測する。[既存Recipe経路](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/worker.py:781)、[API検証](/Users/atsushi/Desktop/projects/personal/pals/pals-api/app/application/services/candidate_verification.py:107)、[factory](/Users/atsushi/Desktop/projects/personal/pals/pals-agent/pals_agent/factory.py:45)

この調査段階では実モデル呼び出し、Lean、DB実行は行っていない。実装後の検証結果は別の実装記録に残す。稼働DBの一般定理・Recipeの件数、対応率、既存処理の時間内訳も未確認である。現時点の推奨は、6 Lunaを第一候補に比較し、LLMによる適用判断と前提質問を備えたLeanなし回答経路を追加すること。
