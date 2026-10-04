# 可換環論の実行検証 — 2026-09-30

ユーザー指示に基づき、単純な数値行列を超える3題を、通常のpublic APIから日本語で実行した。生成へ渡したのは下記の自然言語依頼だけで、期待解答や手書きLeanを注入していない。既存worker/verifierを使用し、追加Chrome・追加コンテナは起動していない。

**初回3題はすべて失敗。修正後の根基問題の再試験も失敗。各13候補・12回修復で上限に達し、意味QA・説明生成には到達しなかった。難問対応は未合格。** 成功判定はLeanの完走だけでなく、元の仮定・結論の保持、独立意味レビュー、説明の完了と論理を確認した後に行う。

| 問題 | 初回の結果 | 主な未解消点 |
| --- | --- | --- |
| 根基イデアルの積・共通部分 | failed | 根基所属・積イデアルへの包含の形式化と修復 |
| 局所化と素イデアル | failed | 予約語の構文エラー、分母を落とした命題 |
| 中山の補題による生成元の持ち上げ | failed | Mの有限生成仮定の欠落、局所環と商写像の誤形式化 |

## radical_product_intersection

単位元を持つ任意の可換環 R とその任意のイデアル I, J に対して、√(IJ) = √(I ∩ J) = √I ∩ √J を証明してください。整域性やネーター性は仮定しません。説明では両方向の包含を示し、x^m ∈ I と x^n ∈ J からどのべきが IJ に入るかを明記してください。既知の根基公式の名前を挙げるだけで終わらず、各仮定をどこで使うか説明してください。

Job: `daec9230-355a-47a9-bbd9-68d89218b084`

確認項目：arbitrary commutative ring with identity; no domain/noetherian assumptions added; x^(m+n) in IJ from x^m in I and x^n in J; IJ subset I intersection J; all inclusions and equality chain without circular use of goal

## localization_prime_extension_contraction

R を単位元を持つ可換環、S を R の乗法的部分集合、P を S と交わらない R の素イデアルとします。λ:R→S⁻¹R を局所化写像、P^e を λ(P) が生成するイデアルとします。任意の a∈R と s∈S について a/s∈P^e と a∈P が同値であることを示し、P^e が S⁻¹R の素イデアルであること、および λ⁻¹(P^e)=P を証明してください。R が整域であることや λ が単射であることは仮定しません。零因子があっても成立する論理を説明し、分数を無条件に約分しないでください。

Job: `6a36b214-d253-4bb9-b9d8-8d2f846f00a5`

確認項目：retain commutative ring with zero divisors allowed; retain prime proper ideal and disjoint S; localization membership clears denominators using u in S; use primeness and S disjoint P to infer numerator in P; extension proper and prime; contraction equals P; no assumption of injective localization

## nakayama_generators_lift

R を単位元を持つ可換局所環、m をその唯一の極大イデアル、M を有限生成 R 加群とします。有限個の元 x₁,…,xₙ∈M の像が M/mM を剰余体 R/m 上のベクトル空間として生成するとき、x₁,…,xₙ が M を R 加群として生成することを証明してください。M が自由加群であることや R がネーター環であることは仮定しません。説明では中山の補題を何に適用するか、有限生成性と局所性がどこで必要かを明記し、補題名の引用だけで終わらせないでください。

Job: `3241e394-716b-4b76-ba8b-ca222fc2d493`

確認項目：finite generated module, no freeness or noetherian hypothesis; N span of supplied elements, M=N+mM from quotient generation; apply Nakayama to finite Q=M/N with mQ=Q, or an equivalent submodule form with its hypotheses justified; maximal ideal is Jacobson radical for local ring; deduce N=M without circularly assuming that x_i already generate M

## 判定上の注意

中山の補題のケースは現typed registryに局所環・有限生成・商加群・生成元の表現がない。no_match後に元の入力を保持して通常生成する経路を試すもので、typed retrieval成功ではない。局所化の3結論は既存profileに表現可能で、独立に作ったLean命題は既存mathlibでコンパイルできた。この手書き確認をアプリの生成成功とは数えない。

中山の補題の仮定は [Stacks Project, Lemma 10.20.1](https://stacks.math.columbia.edu/tag/00DV) と既存mathlibのNakayama APIを参照して点検した。問題文と期待する確認項目はこの試験用に作成した。

## 実試験で検出した修復境界の不一致

APIの閉じたコンパイラ診断は `lean.unknown_identifier` と引用符なしの固定文面を返す一方、generatorは旧 `lean.unknownIdentifier` とバッククォートだけを読むため、次候補で避けるべき識別子リストを作れていなかった。両形式を認識する修正を追加し、ASCII最大128文字の既存境界を維持した。verifier→API→repairの実シリアライズ回帰と関連テストを通過した。これは代替のmathlib定理を検索する機能の追加ではなく、難題の完走は別途実測する。

最初のradical試験は修正前workerで終了した。途中で候補や履歴を書き換えず、通常の停止処理を待って修正workerへ移行済み。局所化と中山の補題は更新後workerが処理する。配置した `generator.py` のSHA-256は `7c967a2f914c71d4bfece93617c22c38b6a34ba82392db7424efa3180906b727`。

## 根基イデアルの実測結果

2026-09-30 02:53:54 UTCに `failed` / `repair_budget_exhausted`。13候補・12回修正でLeanを通過できなかった。一般の可換環と3者の等式は保持していたが、存在しない根基所属補題、べきの存在証明の組の誤り、共通部分への所属から積イデアルへの所属を同じべきのまま導こうとする誤りなどが残った。

独立意味QAは0件、説明生成も未到達。「不正な証明をQAが承認した」例ではなく、証明生成・修復が完走しない例である。最終候補 `7e955097-6a8b-4469-af34-d027a6202ac4`、source SHA-256 `ae89dcd59554f559310a7516f1227e8398727487ac46c9ed732a572aaa7b6c99`。ローカル詳細証拠は `output/commutative-algebra-runtime-20260930/radical-independent-review.json` と `radical-final-candidate.lean`。

## 継続して使う試験入力

`tests/e2e/fixtures/commutative-algebra-v1.json` に同じ3問と評価項目を保存した。既存public API E2E runnerの `--fixture` で読み込める。入力は自然言語のみで、手書きLean harnessや期待解答は生成へ送らない。fixture loaderとrequest serializerで3問の一致・期待解答の非送信を確認済み。今回の実測は前述のjob IDに対応し、fixtureを追加しただけで再実行・成功扱いにしていない。

評価項目は数学的妥当性を確認する観点であり、例示した解法との文章一致を求めない。中山の補題の同値な部分加群版を使うなど、元の仮定と結論を保持する別証明も認める。fixtureの独立レビューで入力保持・解答非送信・数学条件を確認済み。

将来の再試験は、利用枠が残るローカルQAアカウントの既存認証設定で次を実行できる。通常の課金admissionを通し、枠の書換えは行わない。難問は3題合計で標準の30分待機を超えるため、下記は90分で打ち切る設定としている。既存の実試験の再送コマンドではない。

```sh
python3 tests/e2e/run_public_api_e2e.py \
  --fixture tests/e2e/fixtures/commutative-algebra-v1.json \
  --overall-timeout-seconds 5400
```

## 修復位置の見直し

局所化の実候補は命題中の `let λ` がLeanの予約語と衝突していた。verifierの閉じた `lean.syntax_error` は行・列付きで届いていたが、selectorが生成済み命題を正しいと判断し、証明本体の修復を繰り返した。独立ローカルLeanでも同じ構文エラーを再現した。

モデルに診断位置と実ソースの前後を照合させ、生成されたSketchの命題を正しさの根拠にせず、命題側の誤りならdraftまで戻す汎用指示を追加した。経路を固定するheuristicや問題固有の正解コードは追加していない。user supplied harnessと元の数学的主張は引き続き保持する。

修正後のgenerator/pipeline/repair-runtime関連117件、agent単体全体1,812件、対象Ruff/mypyが成功。これは実モデルの修復改善を証明しない。局所化には新指示を途中適用せず、通常終了を待って既存workerを更新した。03:15 UTCの読取り確認でsource SHA-256 `9b6ae25b013b013865684e4bdee1e59d0981bd4324b608a19fe57fe026313dbc` が一致し、9container/6network/10volume不変、全healthyだった。中山の補題はこの新指示で処理する。

## 局所化の実測結果

03:14:29 UTCの終端確認で `failed` / `repair_budget_exhausted`、13候補・12回修復、有効claimなし。最後まで予約語 `λ` を変数名にした `lean.syntax_error` が残った。形式化も分母 `s` を使わず、要求した `a/s` が `λ(a)` に変わっており、元の命題を満たさない。

独立意味QA・説明・説明QAはいずれも0件。誤承認ではなく、その前段階での失敗である。型付き検索は局所化profileを選んだが、分母にSubmonoidElemでなくSubmonoidを使って構造化が2回失敗し、`typed_structuring_invalid` のno_match。validatorを緩めず、元文による通常生成へ進んだ。最終証跡は `output/commutative-algebra-runtime-20260930/localization-final-independent-review.json`、全体snapshotは `commalg-final.json`。

## 今回確認した能力の限界

実workerは固定モデル `gpt-5.4-mini-2026-03-17` を使用している。今回モデルを入れ替えてはいない。生成・修復はDraft/Sketch/直前候補と閉じた診断を受けるが、使用中のmathlibから宣言名・型を検索するtool loopは実装されていない。存在しないAPIや誤った型を繰り返す原因の一つとして区別して記録する。難問失敗を単なるUI不具合やQA誤承認と総括しない。

中山の補題の初候補では、M有限生成が有限個のxのspanのFGへ変わり、商での生成条件が別のrank条件へ変わっていた。Lean失敗の時点で非公開であり、最終候補まで追跡した結果を次に記す。

## 中山の補題の実測結果

03:32:39 UTCに `failed` / `repair_budget_exhausted`、13候補・12回修復、有効claimなし。新しい修復位置ガイドは実promptへ渡り、draftへ戻す選択もされた。入力由来でない初候補をharnessとしてコードが固定する挙動はなく、8候補目で実際に命題が変わった。それでもMの有限生成仮定が戻らず、商・局所環・商写像の誤形式化が残り、最終候補は `lean.compile_error` line 4:32 で失敗した。

意味QA・説明・説明QAはすべて0件。13という数はstatus/eventsと各候補の保存sourceから確認したattempt数であり、候補DBに13行残っているという意味ではない。現候補テーブルは最新failed候補1件を保持する。

## API経由で失われていた修復履歴

実際のAPI-reconcile経路は候補ごとにpipelineが終了するため、メモリ内だけにあった3回連続の診断検知がリセットされていた。今後のAPI検証失敗eventにだけ非公開の出所情報を付け、同job・同source・連続attemptが確認できる最大3件をworker専用GETへ投影するよう修正した。古いeventを信頼済みとして補完しない。公開API/SSEとgeneration claimの形式、修復予算・検証条件は維持する。共通の `verifier_compile_failed` を除き、同じ具体診断signatureが3回続いた場合だけselectorへ警告する。

agent全体1,845件、API全体934件と追加HTTP回帰、実PG3件、実PG→API serializer→worker→警告の結合が通過した。実PG試験のコンパイラ結果は明示したfixture入力であり、実モデルの成功とは数えない。テスト専用DBは前後0件で残留なし。[境界レビュー](../output/repair-stagnation-20260930/architecture-review.md)。既存API/reconciler/workerへ反映後、レビュー済みsource hashの一致・全9サービスhealthy・6network/10volume不変を確認した。

元の根基問題を変更せず、通常APIから新job `36c7ad68-909f-4e82-aaed-24d031db7e20` として1回再試験した。正解Leanや期待解答は送信していない。初回失敗の履歴は保持し、再試験の証跡は `output/commutative-algebra-repair-rerun-20260930/` に分けた。

再試験の6候補目では、保存済みの実モデル入力のroute promptとgenerated promptの両方に `pals.repair_stagnation` の実診断が入った。説明用の定型文が存在するだけでなく、3回連続で共通する `lean.tactic_failed` の通知がAPI履歴から再構成されていた。一般化された同じ診断であり、数学的原因まで同一とは判定しない。selectorは通知を受けてもproveを選択したため、通知到達と証明成功を区別する。証拠は `attempt-6-stagnation-evidence.json`。

## 修正後の根基問題の最終結果

04:01:37 UTCに `failed` / `repair_budget_exhausted`、13候補・12回修復で終了した。有効claimなし。独立意味QA・説明・説明QAはすべて0件。11候補目でLeanに不適切な連鎖等式へ変わったが、12–13候補目では元の二つの等式の連言に戻った。最終候補は任意の可換環とイデアルという仮定・元の結論を保持していた。

それでも正の指数を含む根基所属の同値を `rfl` で示そうとする誤り、存在しない `Ideal.le_left` / `Ideal.le_right`、型不一致が残った。途中候補には積イデアルの元を単一の積に分解する誤りもあった。最終source SHA-256は `b0c362936cdce4c0fc87be9705b41b15232deedf7990722691878df39c1bf7dc`。

今回の修正で、実診断の取り込みとAPIをまたぐ修復履歴・停滞警告の接続は確認できた。一方、正しい命題の形式化とmathlibの実在する宣言・型に基づく証明生成は未解決である。難問の成功動画は作成できていない。既存の簡単な問題のUI動画をその代替とはしない。[独立最終レビュー](../output/commutative-algebra-repair-rerun-20260930/final-review.md)。
