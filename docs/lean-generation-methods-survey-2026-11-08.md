# Lean コードの通過率を上げる手法の調査 2026-11-08

調査だけの文書です。実装も評価の実行もしていません。コミットもしていません。論文とリポジトリの一次資料を読み、数字は出典にあるものだけを書きました。確認できなかった点は「未確認」と書いています。

## 読む前の注意

- 論文の数字は、モデル、ベンチマーク、サンプル数、Lean や Isabelle の版、評価の予算がそれぞれ違います。PALS にそのまま当てはまる数字はありません。表では、同じ条件の中での「足す前、足した後」だけを並べています。
- 多くの大きな向上は、基線が極端に低い環境の数字です（例: o4-mini の miniF2F が 7.0%）。PALS の Terra medium は最終成功が 10/12 と 21/24 で、同じ幅の向上は期待できません。
- 数字の取得方法は 2 種類あります。PDF 本文から転記したものと、取得ツールの要約を介したものです。後者には転記ミスがありえます。意思決定に使う前に、原文の表で再確認してください。
- 2026 年の論文が多く含まれます。いくつかは arXiv に存在することだけ確かめました（ProofGap、Fix Not Just Resample、MAGE、Compile to Compress、MechGeo、Faults、LongCat-Flash-Prover、Goedel-Architect、APRIL、Burton、Klingner）。内容は各調査員が取得したページに基づきます。
- 手法を作った本人が自分の手法を評価している数字が多くあります（GEPA、ReForm、CriticLean、FormalRx など）。独立した検証は少数です。

## 0. PALS の現状（この調査の前提）

| 項目 | 値 | 出典 |
|---|---|---|
| Terra medium / Terra low / Luna low | 21/24（212 秒/枚）/ 16/24（100 秒/枚）/ 12/24 | `docs/model-call-latency-measurement-results-2026-11-07.md` |
| 初回の Sketch が Lean に通る割合 | 同じ 12 カードで 6/12 | 本調査の依頼文。使ったモデルは未確認 |
| Lean 検査に失敗した Sketch | 47 試行中 36（通信失敗 10、sorry 残り 1、真の空応答 0） | model-call-robustness の引き継ぎ（親リポジトリ外のメモ） |
| 失敗後の連鎖 | 修復指示、経路選択、再 Sketch の 3 呼び出し | 同上 |
| 補題名ヒントと Recipe の few-shot | Terra medium で効果なし（成功 10/12 のまま。修復 26→24） | proof-pipeline-speed の引き継ぎ（PR #79） |
| 命題の食い違い | 同じ 12 カードの Terra medium 基線（有効な 12 件）で、`lean.formal_harness_mismatch` が 3 件の最初の試行に出た。最終失敗の 2 枚は、どちらもこの診断が 2 回以上出ている | `proof-pipeline-speed-results/pf-base*.jsonl` を本調査で集計 |
| 失敗した Sketch の本文 | 結果の JSONL には保存されていない（診断コードだけ） | 同上 |

最後の行が重要です。決定的な修復処理を、既存データだけでオフライン検証することはできません。

## 1. 結論

### 1.1 先に、批判的な見立て

1. 「初回の Sketch の通過率」だけを上げても、目的は達成されません。問題は、落ちたあとの 3 呼び出しの連鎖と、通過後に命題が変わっていないかの検査です。通過率、壁時計、費用、命題の一致を分けて測る必要があります。
2. 12 カードでは、効果を測れません。通過率 0.5 の二値で、標準誤差は 24 枚で約 0.10、12 枚で約 0.14 です（私の計算）。補題名ヒントと Recipe few-shot の「効果なし」は、効果がないことの証明にはなりません。文献の効果量（+1〜+5 点）は、この標本では検出できません。
3. 文献で一貫して大きい向上は、プロンプトの工夫ではなく「診断を返すループ」「sorry 骨格からの分解」「決定的な部分修復」の側にあります。この傾向は、PALS で補題名ヒントや few-shot が効かなかった事実と矛盾しません。
4. Lean が通ることは、問いを正しく証明した証拠になりません。人手で不忠実と判定された形式化の 43 件のうち 17 件が、証明に成功した報告があります（MechGeo、幾何に限る）。命題の固定と一致検査は、通過率を上げる施策とは別に必要です。

### 1.2 効果の大きい順の上位 5 手法

「PALS の期待効果」は私の推測です。文献の数字から PALS の数字は導けません。実測で決めるべき項目は検証計画（第 4 章）に回しています。

| 順位 | 手法 | 文献での向上（条件つき） | PALS の期待効果（推測） | 費用 | 実装難度 | 根拠の強さ | 今日着手できる順 |
|---|---|---|---|---|---|---|---|
| 1 | 決定的な部分修復。誤り行を `sorry` に置換し、自動 tactic の列で穴を埋め、残りの穴だけ LLM に戻す | APOLLO: o4-mini 7.0→46.7%（miniF2F-test、サンプル予算 15）。DSP+: 誤り行マスクを抜くと 74.2→71.3%（pass@128）。Lyra: 失敗 tactic の自動置換を足すと、エラー再生成の効果が +0.4 から +5.3 点に | 3 呼び出しの連鎖を、モデル呼び出しなしで一部省ける可能性。省ける割合は未測定 | モデル呼び出しは増えない。Lean 時間は増える（tactic 1 分岐あたり平均 25〜77ms、ただし別の報告） | 中。Lean REPL で誤り箇所を特定する処理が必要 | 中。複数の論文で一致。ただし基線が低く、単独の寄与は小さい（APOLLO では組合せで効く） | 3 位 |
| 2 | 命題の固定と一致検査。モデルには証明本体だけを書かせ、確定した命題はテンプレートで差し込む。最終検査は型の一致、許可公理、カーネル再検査（`lake comparator` または SafeVerify 型） | 通過率の向上ではなく、偽の成功の除去。LongCat の RL では、構文検証のみ 97.9%、定理名の一致検査を足しても 97.6%、AST 検査を足すと 27.9% | `formal_harness_mismatch` で落ちている試行（12 件中 3 件が最初から）と、最終失敗 2 枚の一部が救える可能性。同時に「弱い補題だけで verified」を防ぐ | モデル呼び出しは増えない | 低〜中。検査器は既製品がある。古い Lean での動作は未確認 | 実務では強い（複数の事例）。プロンプトの制約文の効果を単独で測った報告は見つからなかった | 1 位 |
| 3 | 修復の入力の作り直し。エラーを該当行にインラインで挿入、tactic state、未知識別子は検索結果つき。修復は 1 回で打ち切る | Baldur: 計算量を揃えると +1.5 点（34.8→36.3%）、2 回目の修復はさらに小さい。Compile to Compress: インライン挿入 284 問、末尾追加 246 問（miniF2F 477 問、生成 1＋修復 1）。Goedel-V2: エラーメッセージを除くと明確に悪化 | 3 呼び出しを 1 呼び出しにまとめれば、修復 1 回あたりの時間が縮む。通過率への効果は +1〜2 点程度が文献の水準 | 呼び出し数は減る方向 | 低〜中 | 中。修復の上積みが 1 回目に集中することは、Baldur、Leanabell、Fix-not-resample、Goedel-V2 で一致 | 4 位 |
| 4 | 失敗した葉だけの再分解。落ちた `have` を独立した定理として切り出し、別の呼び出しで証明する。深さは 1〜2 に限る | Hilbert: 分解の深さ D=0 で約 75%、D=2 で 98.36%（miniF2F-test、Gemini 2.5 Pro＋Goedel-V2-32B）。Delta Prover: 同じ予算 16,384 で、Best-of-N 49.1→95.9%。Goedel-Architect: 直接生成 67.6%、ツール統合 97.1% | 初回の Sketch 全体を直し続けるより効く可能性。PALS の難問ほど効く見込み | 大きい。Hilbert は難問で 1 問 22.8M〜27.0M トークン | 高 | 強い（複数の独立した報告）。ただし D=0 は証明器のみの基線で、PALS の修復連鎖とは対応しない | 5 位 |
| 5 | 並列 n 本＋最初の成功の採用。言い換えではなく、骨格や方針を変えて多様化する。または Terra low で始めて、失敗したら medium に上げる | Burton: 同じ入力の独立サンプルは 32→64 で追加の解がゼロ（DeepSeek-Prover-V1.5-RL、温度 0.6）。tactic の骨格を指示に入れると pass@16 が 38→55。PALS 内: low から medium への昇格（方式 D）は 189 秒で、方式 A との差は 95% 区間 [-19, 69] 秒 | 壁時計を max にできる。通過率への効果は未知 | 呼び出しが n 倍 | 低〜中 | 弱い（OpenAI 系モデルでの測定はない） | 2 位 |

次点（条件つき）は GEPA による Sketch の指示文の最適化です。評価カードが 140 枚程度あり、先に基線のばらつきを測れるまで着手しません（第 3 章）。

### 1.3 PALS で今日できる順

1. 命題の固定（順位 2）。診断コードと検査の仕組みが既にあり、モデルの変更が要りません。
2. 並列 n 本、または low→medium の昇格の再測定（順位 5）。既存のハーネスで測れます。
3. 決定的な部分修復（順位 1）。先に失敗した Sketch の本文を保存する必要があります。
4. 修復入力の作り直し（順位 3）。
5. 失敗した葉だけの再分解（順位 4）。

## 2. 手法ごとの表

列の「差」は、足す前→足した後です。出典は arXiv ID で示し、論文名・著者・年・URL は第 6 章にまとめています。

### 2.1 (A) Draft, Sketch, and Prove とその後継

| 手法 | 報告された差（条件） | 前提 | PALS への適用 | 費用・難度 | 根拠の強さ・リスク |
|---|---|---|---|---|---|
| DSP 原法 (2210.12283) | 完全証明の直接生成 32.8/30.3 → 42.6/39.3（miniF2F valid/test、Isabelle、Codex、予算 100）。コメントの除去 -4.9/-2.8、非形式証明の除去 -3.7/-5.3 | Isabelle と Sledgehammer。Codex は使えない | 穴つきの骨組み＋自動証明器という構造そのものに約 9 点の価値。Lean では aesop、omega、nlinarith などで穴を埋める発想になる | 難度は PALS が既に実装済みの構造 | Lean での再現値は原論文にない |
| DSP+ (2506.11487) | 誤り行のマスクと仮説の明示を各々抜くと 74.2→71.3（pass@128）。Draft の追加 71.7→74.2。人手の非形式証明を足すと 70.9 に下がる。Sketch の翻訳率（誤り行を除いて残る割合）の中央値は V3 が 100% | Lean 4.17.0-rc1。証明段に BFS-Prover-7B を使う | マスク規則は実装が軽く、寄与は小さいが安定。型注釈（`(1:ℝ)/2`、ℕ の引き算）や `(n)!` の注意をプロンプトに入れる根拠 | 低 | 差は図からの読み取り。分散は不明 |
| Baldur (2303.04910) | 修復あり 36.3% と生成のみ 34.8%（計算量を揃えた比較）。コスト 2 で 24.9、修復をもう 1 回で 26.2、生成のみコスト 3 は 25.4 | Isabelle、微調整した 8B。miniF2F ではなく PISA の 6,336 定理 | エラーメッセージを入れる根拠。2 回目以降の修復の価値は低い | 低 | 微調整が前提 |
| LEGO-Prover (2310.00656) | 補題ライブラリあり 50.4%、なし 47.1%（miniF2F valid、50 試行） | Isabelle。100 試行で約 300 ドルの見積り | 長期の効果型。PALS の Recipe の蓄積と同じ発想の裏付け。初回の通過率は上げない | 高 | Lean 版なし |
| Lyra (2309.15806) | 人手草稿で、失敗 tactic の置換（TC）のみ 45.9、エラー再生成（CC）のみ 43.0、両方 51.2（test、200 試行、GPT-4）。基線は 42.6 | Isabelle | 再生成の前に、機械的に fallback の tactic を当てる設計の根拠 | 低 | CC だけでは valid で下がる場合がある |
| Subgoal-based demonstration (2305.16366) | 部分ゴール列の例で 44.3/40.6 → 48.0/45.5（miniF2F valid/test） | Isabelle、gpt-3.5-turbo | few-shot を使うなら、証明器の状態に揃えた部分ゴールの粒度にする | 中 | 例の選択に拡散モデルの学習が要る部分は使えない |
| ProofAug (2501.18310) | Lean: pass@1 44.3→50.4%（Kimina-Distill-1.5B）。Isabelle: 28.7→36.5%（1 サンプル） | 小型モデル。Lean 版の詳細は付録の 1 段落のみ | 失敗ブロックを `sorry` にして、Aesop、omega、norm_num/field_simp/ring_nf/nlinarith の列を当てる。LLM 呼び出しなしの修復 | 低〜中 | Lean 版の根拠が薄い |
| APOLLO (2505.05758) | o4-mini 7.0→46.7%、o3-mini 3.3→40.2%（miniF2F-test）。要素ごと: Syntax のみ 7.4、AutoSolver のみ 7.0、LLM 再呼出のみ 8.2、Syntax＋AutoSolver 20.5、全部 46.7。Kimina-7B は 63.1→75.0（Syntax の寄与は 0） | Lean 4。汎用推論モデルでも使える | 順位 1 の最も直接の資料。Syntax Refiner は、PALS のモデルが Lean 3 構文を出すかどうかで効果が決まる（未確認） | 中 | 基線が極端に低い。単独の寄与は小さく、組合せで効く |
| Delta Prover (2507.15225) | Gemini 2.5 Pro の Best-of-N 49.1% → 95.9%（miniF2F-test、同じ予算 16,384） | 再学習なし。呼び出しは 1 問で数百〜数千回 | 初回プロンプトに「Lean 4 であること、戦術の docstring、書式規約」を入れ、エラー時に「tactic state つきエラー＋未知識別子の検索結果」を戻す設計が低コスト | 高（逐次で遅い） | 修復と Best-of-N の差は図のみ。数値は未確認 |
| Hilbert (2509.22819) | 分解の深さ D=0 約 75%、D=2 98.36%、D=3 98.7%。検索あり/なしは 99.2/97.9 と 98.4/97.1 | Lean 4.15.0。Reasoner は Gemini 2.5 Pro/Flash、gpt-oss-120b。証明器は DeepSeek-Prover-V2-7B か Goedel-V2-32B | 構造が PALS に最も近い。`sorry` 骨格の葉を独立した定理に切り出し、深さ 1〜2 に絞る | 高。難問で 22.8M〜27.0M トークン | 強い。初回の Sketch が通る確率は報告されていない |
| Prover Agent (2506.19923) | Goedel-V2 構成: 1 サンプル 64.3 → 直接 50 サンプル 84.4 → 修復込み 85.7 → 補題込み 86.5（miniF2F-test）。補題の上積みは +0.8〜+1.4 | 小型モデルの証明器 | 補助補題の追加の効果は 1 点前後。修復は、最初の N 個の質が一定以上のときだけ効く | 中 | 中 |
| Ax-Prover (2510.12787) | Sonnet 4 単体 5% → 51%（NuminaMath-LEAN、pass@1）。Abstract Algebra 8→64% | lean-lsp-mcp。1 問で平均約 100 回のツール呼び出し | 診断メッセージと検索ツールを修復段に足す案の根拠。全面採用は時間の目的に合わない | 高 | ツール単独の寄与は分離されていない |
| Seed-Prover 1.0/1.5 (2507.23726、2512.17260) | 洗練（コンパイラ出力による修正）なしでは IMO 2022 P2 に pass@8192 が必要で、洗練ありは light 設定で解けた | 強化学習した専用モデル。非公開 | PALS では使えない。1.5 のスケッチ審査の「全部を 1 つの sorry に隠す退化は却下」は、モデルを使わずに真似できる | 低 | 洗練 1 回あたりの上積みは未報告 |
| Goedel-Architect (2606.06468) | DeepSeek-V4-Flash のみ。miniF2F-test の直接生成 67.6%、ツール統合 97.1%。PutnamBench 200 問の部分集合で 6.5→54.5→76.0（ブループリント方式） | オープン重みのモデル。1 問 $0.44（Putnam 全体） | 汎用モデル＋Lean ツール＋骨格の分解が現在の水準を作っている、という傾向の確認 | 中〜高 | 要約経由の数字。原文で再確認が必要 |

### 2.2 (B) DSPy とプロンプト最適化

条件の注意: 下の数字は HotpotQA や AIME などのタスクで、Lean ではありません。Lean に DSPy の最適化器を適用した公開事例は、見つかりませんでした（検索は網羅的ではありません）。

| 手法 | 仕組みと必要データ | 報告された差（条件） | Lean への適用 | 費用・難度 | 根拠の強さ・リスク |
|---|---|---|---|---|---|
| BootstrapFewShot | 通ったトレースを few-shot にする。公式の目安は約 10 件から | GSM8K、GPT-3.5: 25.2→61.7（DSPy 原論文、訓練 200 件） | 通過した例を集めるだけで、Recipe の few-shot が効かなかった実績と重なる | 低 | 古いモデルの数字。推論モデルでの挙動は未確認 |
| BootstrapFewShotWithRandomSearch | 候補プログラムを valset で選ぶ。公式の目安は 50 件以上 | 第三者: jailbreak 検出 82.90→93.18%（GPT-4o-mini、評価 50 件） | 同上 | 低 | 評価 50 件の差はノイズの範囲 |
| COPRO | 指示文の座標上昇。breadth=10、depth=3 | 公式の数字は未確認 | スカラーの metric しか見ず、エラー文を使えない | 低 | GEPA の下位互換として扱うのが妥当 |
| MIPROv2 (2406.11695) | 指示とデモの組合せをベイズ最適化。公式の目安は 200 件以上、40 試行以上。valset が 50 件以下だとミニバッチが無効 | Llama-3-8B で ScoNe 69.1→79.4、HotPotQA 36.1→46.4（訓練 500、開発 500） | スカラーのみ。12〜24 枚では対象外 | 中 | GEPA 論文の中で AIME が 27.33→20.00 に悪化した例がある |
| SIMBA | ばらつきの大きい例からルールを足す。`trainset ≧ bsize`（既定 32）が必須 | 公式の数字は未確認 | 確率的に通る Sketch の考え方には合う。24 枚では既定値で動かない | 中。1 ステップ約 416 呼び出し（ソースの構造から） | 評価が未確認 |
| GEPA (2507.19457) | 指示文を反省で進化。コンパイラのエラー文を feedback にする設計が論文の核。ミニバッチ 3。論文のデータは train 111〜150、val 111〜300 | Qwen3 8B 平均 45.23→54.85（MIPROv2 は 47.84）。GPT-4.1 mini 平均 53.03→65.22（MIPROv2 は 58.67）。GEPA+Merge の IFBench は 36.90→28.23 に悪化 | 本命だが、小データでの安定性は未検証 | 論文の費用は GPT-4.1 mini で GEPA 86 ドル（6 タスク）。反省 LM の呼び出しは 1 回の最適化で 17〜92 回 | 著者が DSPy 側で自陣営の評価。MAGE（単著、再実装）は Ntrain=30 で 62.4→34.0% に悪化したと報告 |
| BootstrapFinetune | 通ったトレースで重みを微調整 | 平均で、重みのみより最大 60%、プロンプトのみより最大 6% 上（要旨） | PALS は自前学習をしないため対象外 | 高 | OpenAI の gpt-6.x に微調整が提供されているかは未確認 |
| TextGrad (2406.07496) | 批評を勾配として、解答やプロンプトを更新 | LeetCode Hard、gpt-4o: ゼロショット 0.26、Reflexion 0.31、TextGrad 0.36（完了率、5 シード平均） | 修復の連鎖に近い。ただし Lean ではない | 中 | 別の第三者再現で、分割だけで 91.9→84.5 に動いた例がある |
| OPRO (2309.03409) | 過去の指示とスコアを並べて新しい指示を提案 | GSM8K 71.8→80.2（PaLM 2-L） | スカラーのみ。エラー例を入れても改善しなかったと著者が報告 | 低 | 訓練が数十件だと過学習が深刻、とも書かれている |

### 2.3 (C) 検索・補題選択・自動化 tactic

| 手法 | 報告された差（条件） | 前提 | PALS への適用 | 費用・難度 | 根拠の強さ・リスク |
|---|---|---|---|---|---|
| ReProver / LeanDojo (2306.15626) | 検索を足すと Pass@1 が +3.6（random 分割 47.6→51.2）、+3.1（novel_premises 23.2→26.3）。retriever 単体の R@10 は 38.4/27.6 | 自前の小型モデル | retriever 部分の流用のみ。R@10 が 3〜4 割の水準は、LLM が選別する前提でないと使いにくい | 高 | 古い設定 |
| LeanSearch v2 (2605.13137) | FATE-H（n=100）で検索なし 4.0% → 通常 14.0%、推論モード 20.0%（Sonnet 4.5 の反省ループ、8 ラウンド）。Kimi K2 では 1.0→8.0/12.0% | 公開 API（利用制限は未確認） | 大学院の代数のように Mathlib 依存が強い問題向け | 1 ループ約 1.10 ドル | 競技問題には当てはまらない |
| REAL-Prover (2505.20613) | 検索あり/なし: ProofNet 23.7/22.6、FATE-M 56.7/44.7 | 自前のモデル | 同上 | 高 | miniF2F では効かないと著者が説明 |
| Lean Finder (2510.15940) | 下流の証明で miniF2F は 0〜+1.3 点、ProofNet は最大 +3.8 点（予算 32） | ウェブサービス | 競技系の葉には効きにくい | 低 | 全証明型は微増 |
| Hilbert の検索 (2509.22819) | 98.4/97.1 と 99.2/97.9。Reasoner 呼び出し 862→548 | 飽和した条件 | 検索の価値は精度より呼び出し数の削減に出た | 低〜中 | 飽和条件の数字 |
| 補題名ヒント（PALS 自身の実験） | 効果なし（10/12 のまま） | Terra medium | 文献でも、競技系では検索の効果が出にくい | 低 | n=12 では判定不能 |
| LeanHammer (2506.07477) | 前提選択なし 16.9% → LeanPremise 付き 30.1%（Mathlib test の再証明）。正解前提を与えた上限 43.0% | README の対象は安定版 v4.20.0〜v4.35.0。PALS は 4.32.0-rc1 で未確認。外部バイナリ（Zipperposition、cvc5）が必要 | まず grind と aesop の範囲で試す方が低リスク | 中 | 対象は Mathlib 定理の再証明で、Sketch の葉と分布が違う |
| `grind`（Lean 本体） | 一次の定量評価は見つからなかった。コミュニティ自己申告: LeanHammer が miniF2F-test で Lean v4.27.0 は 13.1%、v4.33.0 は 37.3%（91 本中 58 本が grind を使用） | 4.22.0 で導入。`+suggestions` は 4.26.0 から。4.32.0-rc1 で使える | 決定的カスケードの先頭候補。外部依存なし | 低 | 自己申告のモデルカードで、査読なし |
| `aesop` | MIL 168 定理の 24.4%（Lean Copilot）、Mathlib 再証明 31.6%（Lean-Auto、前提つき）、textbook 由来ギャップ 9.67%（ProofGap） | Mathlib 固定版と整合 | 条件で 10〜32% と幅が大きい。「どの分布の葉か」で決まる | 低 | 分布依存 |
| 標準 tactic の和集合（ProofGap、2609.29296） | textbook 由来 26,116 ギャップを 8 種の tactic で 11.20%（grind、exact?、decide、positivity は未評価） | Lean v4.29.0-rc6 | 葉の分布は PALS の Sketch に近い可能性があるが、grind が未評価で、下限の目安にとどまる | 低 | 推測を含む |
| `try?`（Lean 本体） | 定量報告なし。複数の戦略を並列に試し、`grind` の `+suggestions` も含む（master のソース。4.32.0-rc1 で同一かは未確認） | 4.32.0-rc1 で使える | 自作のカスケードの前に、`try?` を 1 回呼ぶだけで大半が賄える可能性 | 低 | 未測定 |
| `exact?` / `apply?` / `rw?` | 定量報告なし | 組み込み | 1 手で刺さる葉には安い。成功率は自前で測る | 低 | 未測定 |
| `polyrith` | 使えない（Sage Cell の停止） | なし | 対象外 | なし | なし |
| `hint` | 定量報告なし。閉じないとき `admitGoal` を呼ぶので、sorry 入りの証明を返す場合がある | Mathlib | 検査で `sorry` を必ず拒否する前提なら使える | 低 | リスクあり |
| `canonical` (2504.06239) | Natural Number Game 74 問で 62 問（84%）。Aesop は 27 問（36%） | Lean 4.16.0 | 型レベルの葉向き。解析的な不等式には向かない（推測） | 低 | Mathlib での評価なし |

### 2.4 (D) 修復・フィードバック

| 手法 | 報告された差（条件） | 前提 | PALS への適用 | 根拠の強さ・リスク |
|---|---|---|---|---|
| エラーメッセージを入れる | Goedel-V2: 除くと「明確に悪化」（数値は図）。Baldur: 除くと計算量を揃えて生成のみを超えない | 専用に学習した修復モデル | 必須 | 汎用モデルでの単独測定は未確認 |
| インライン挿入（2604.18587） | 生成 1＋修復 1: インライン（epoch2）284、独立 2 サンプル 277、末尾追加（epoch2）246（miniF2F 477 問） | Kimina-7B 系 | 入力の作り方次第で、修復が独立サンプルに負ける | 1 論文の結果 |
| tactic state を渡す | DeepSeek-Prover-V1.5 の RMaxTS で、tactic state 抜きが 4×6400 で 58.4 → 59.6（full） | 小型モデル。+1.2〜+1.6 点で標準誤差に近い | 効果は小さい。全証明修復での単独比較は見つからなかった（未確認） | 弱い |
| 修復回数の上積み | Goedel-V2: pass@32 で +2.1〜+2.3、pass@1024 で +0.8〜+1.4。Leanabell: 反復 2 回目以降は +0.4 以下。Fix-not-resample: R=1 で R=3 の増分の 84〜96% | 専用に学習したモデル | 1 回目に集中する。1 周で打ち切る設計と整合 | 中。汎用モデルの外挿には注意 |
| 修復の失敗種別 | Fix-not-resample（K=8、R=1）: simp 系の進展なし 14.6%、rfl 失敗 11.0%、型不一致 1.8%、型クラス合成 2.0% | tactic 単位の小型生成器 | 失敗種別で修復の見込みが違う。修復に回す前に診断コードでルーティングできる（推測） | 弱い |
| 構文・識別子の機械修復 | APOLLO: Syntax Refiner は o3-mini の 100%、o4-mini の 94.7% の問題で発動。専用モデルでは 0% | 汎用モデルは初回で Lean 3 構文などを書く | PALS のモデルで同じ頻度かは未確認 | 中 |
| 修復 vs 並列サンプル | Refine@32 − pass@32: miniF2F 平均 +7.7 点、miniCTX 平均 -1.4 点（汎用モデル、n=50）。Delta Prover は修復が Best-of-N を上回ると述べる（数値は図のみ） | 汎用モデル | 結論が割れている。PALS の実測で決める | 弱い（n=50、符号がモデルでばらつく） |
| 計算量を揃えた比較 | Baldur: 修復 +1.5。Compile to Compress: 修復 +7/477 | 微調整モデル | 同上 | 弱い |

### 2.5 (E) サンプリングと推論時の計算量

| 手法 | 報告された数字（条件） | PALS への示唆 |
|---|---|---|
| pass@k のスケーリング（専用証明器） | DeepSeek-Prover-V2-671B（CoT）pass@1 61.9、@32 82.4、@1024 86.6、@8192 88.9（miniF2F-test）。pass@1→32 で +15〜20 点、32→1024 で +4〜6 点、1024→8192 で +1〜3 点 | 収穫逓減が明確。初回の確率が高い問題では飽和が早い |
| 同じ入力の n 並列 | Burton (2601.16172): DeepSeek-Prover-V1.5-RL（温度 0.6）で pass@32 と pass@64 がどちらも 42 問。tactic の骨格を指示に入れると pass@16 が 38→55。指示の言い換えは 38 のまま | n 並列にするなら、温度ではなく骨格や方針を変える。OpenAI 系での検証は未確認 |
| best-of-n と検証器 | Lean の検証は完全なので、Best-of-N は「最初に通ったものを採る」と同じ（Large Language Monkeys、2407.21787）。coverage は 4 桁のサンプル数にわたり対数線形に伸びることが多い（図のみ） | 多数決や報酬モデルは要らない |
| 過程報酬 | 推論時に Lean 向けの PRM を使った研究は、見つからなかった（未確認） | 対象外 |
| reasoning effort | 固定して Lean 通過率を比べた公表値は見つからなかった（未確認）。間接証拠: DeepSeek-Prover-V2 の CoT あり/なしで、pass@32 が +6.6〜+7.6 点、出力トークンは約 9 倍 | PALS 内の実測（Terra medium 21/24 と low 16/24）が最も直接の根拠 |
| 汎用 API モデルのサンプル数と修復 | o3-mini 32 サンプル 24.59%、Gemini 2.5 Pro（preview 03-25）37.70%（miniF2F、Kimina Preview の表）。Gemini 2.5 Pro 05-06 の Best-of-N 16,384 で 49.1% | 汎用モデルは、サンプルを増やすより構造（分解、機械修復）を足す方が効く |
| 温度 | Lean 3 の tactic 単位で 0.7 → 1.4 に上げると 27.87→29.10%（bChatLean、miniF2F test）。Lean 4 の全証明生成には外挿できない | 推論モデルは温度が固定のことが多い |
| 同一入力の重複排除 | 全証明生成での効果を測った研究は見つからなかった（未確認） | 対象外 |

### 2.6 (F) 証明用に学習されたモデルと汎用 API モデル

結論は、差を決めるのはモデルの種類よりも、診断を返すループの有無です。

| モデル・方式 | スコア（条件） | PALS で使えるか |
|---|---|---|
| Kimina-Prover Preview 72B / Gemini 2.5 Pro / o3-mini | miniF2F-test の 32 サンプルで 68.85 / 37.70 / 24.59%（単発生成） | 学習済みは重みのみの配布で、自前ホストは対象外 |
| Delta Prover（汎用 Gemini 2.5 Pro に診断・分解・修復を付与） | 49.1→95.9%（予算 16,384） | 方式として再現可能（API のみ） |
| DeepSeek-Prover-V2-671B | miniF2F-test pass@8192 88.9%（CoT）。PutnamBench 47/658（pass@1024） | 重みのみ。OpenRouter 掲載の記録はあるが、現在の提供は未確認 |
| Goedel-Prover-V2-32B | pass@32 88.1%、自己修正ありで 90.4%。PutnamBench 86/644（pass@184、自己修正あり） | 重みのみ。対象外 |
| Seed-Prover 1.0/1.5 | miniF2F-test 99.6%。PutnamBench 331/657、580/660 | 非公開。対象外 |
| StepFun-Prover / Leanabell-Prover-V2 | 7B で pass@32 68.4〜76.6%（Leanabell） | 重みのみ。差は +1〜5 点 |
| Leanstral 1.5（Mistral） | PutnamBench 587/672（pass@8、1 試行 4M トークン、Mistral の自己報告）。API ID `leanstral-1-5` | 無料枠の期限、価格、レート制限は未確認。独立評価は見つからなかった |
| Aristotle（Harmonic） | ArXivLean（41 問、2026-03）で GPT-5.4 と同じ 17.07% | API の価格と条件は未確認 |
| MA-ProofBench（Mathlib 4.28.0、解析学、Level I の pass@8） | GPT-5.5 16.00、Gemini 3.1 Pro 13.00、DeepSeek-Prover-V2-671B 6.86、Goedel-V2-32B 5.05 | 新しい Mathlib では、専用モデルは強い汎用モデルに負ける。ただし原因は検証されていない（学習が Lean 4.9 前後であることが一因の仮説） |

PutnamBench の 2026 年の結果では、上位は汎用またはオープン重みの LLM を使うエージェントです。専用モデル単体（Goedel-V2 が 86、DeepSeek-Prover-V2 が 47）と、GPT-5 の ReAct（ツール 10 回、28）を大きく上回ります。予算の単位がそろっていないため、比較は参考です。PALS の Lean 4.32.0-rc1 に対して、専用モデルは Lean 4.9〜4.20 付近で学習・評価されています。版差の影響を直接測った論文は見つかりませんでした。

### 2.7 (G) プロンプトの形式

| 項目 | 報告された内容（条件） | PALS への示唆・未確認 |
|---|---|---|
| 命題の書き方 | 専用モデルの標準形式は、`import Mathlib` などのヘッダ、非形式の問題文の docstring、`theorem ... := by sorry`。docstring の単独効果を測った実験は見つからなかった | 未確認 |
| Lean 3 構文の混入 | GPT-4 は「Lean 4 で書け」と明示しても begin/end を出した（TheoremLlama、2407.03203）。Delta Prover も同種の注意を記述 | PALS の gpt-6.x が出すかは未確認。出るなら、禁止リストを添えるか、機械的な Syntax Refiner を入れる |
| Mathlib の新旧の名前 | 幻覚は失敗の 7.7%（Klingner、2606.05632。32 サンプル、各 50 問）。Goedel 32B 約 2.5%〜GPT-OSS 15.1%。旧名と捏造名は区別されていない | 旧 API 名の誤用率は未確認（定量報告なし）。診断（`unknown identifier`）を修復に戻す手段が文献の一般解 |
| 思考の連鎖 | DeepSeek-Prover-V2-671B: CoT ありの pass@32 が 82.4%、なしが 73.8%。ただし CoT 形式で強化学習したモデル。DSP+: 人手の非形式証明を足しても改善しなかった | 汎用 API モデルに、同じ形で当てはまるとは限らない。OpenAI の公式ガイドは、推論モデルへの「ステップごとに考えて」を不要とする |
| few-shot（推論モデル） | DeepSeek-R1 論文は「few-shot は一貫して性能を下げる」と書く。From Harm to Help (2509.23196): デモ 1〜3 個で AIME2025 が最大 35 点低下。反対の報告もある (2503.19602) | どれも Lean ではない |
| few-shot（Lean） | ProofEvolve (2608.26334): 関連検索で選ぶと +3.9 点（K=8）、ランダムは +0.1 点（非推論の Qwen3.5、ゼロショット 49.5%） | モデルの余地が大きい条件の数字 |
| 「命題を変えるな」の制約文 | 単独の効果を測った報告は見つからなかった。実例（ArXivLean、Goedel-Architect）は、提出物の命題を原文に差し替えるか、署名をバイト一致で検査している | プロンプトではなく、検査側の構造で解く方向が一貫している |

#### 補題名ヒントと Recipe の few-shot が効かなかった理由の仮説

どれも仮説です。PALS で検証された事実ではありません。

| 仮説 | 根拠（文献） | PALS で確かめる方法 |
|---|---|---|
| H0 標本が小さく、効果を検出できない | 文献の効果量は +1〜+5 点（ProofEvolve +3.9、Hilbert の検索 +1.3）。n=12 の標準誤差は約 14 点 | 検出力の計算（第 3 章） |
| H1 補題名は失敗の主因ではない | 幻覚は失敗の 7.7%。tactic 14.4%、構文 14.2%、unsolved goals 13.3% の方が大きい（Klingner） | PALS の失敗ログを同じ分類で集計する |
| H2 推論モデルは例を内部の推論と競合させる、または例を写して失敗する | R1 論文、From Harm to Help（文面が似るほど途中式を写す） | Recipe の類似度ごとの成否を見る |
| H3 Terra は既に天井近く（10/12）で、足せる余地が小さい | ProofEvolve の効果は、ゼロショット 49.5% の余地がある条件 | Luna low など余地のあるモデルで再測定 |
| H4 失敗の主因が証明の知識ではなく、Lean 上の機械的な整合（構文、型の昇格、命題の改変）で、例では直らない | PALS 内の `formal_harness_mismatch`。Klingner の構文エラー | 診断コードごとに集計 |
| H5 Recipe の証明が現行の Lean/Mathlib や命題の形とずれている | From Harm to Help の「戦略の転用失敗」からの類推 | Recipe の証明が現行版でそのまま通るかを確かめる（PALS 側の事実確認） |
| H6 ヒントでプロンプトが長くなり、散漫になる | Klingner: 文脈が長いと refine が劣る例がある（直接の証拠は弱い） | ヒント数を変えて測る |

### 2.8 (H) 自動形式化の品質

| 手法・報告 | スコア・内容（条件） | PALS への適用 | 根拠の強さ・リスク |
|---|---|---|---|
| 形式化の誤り率 | ProofNet の Lean 4 移植版 371 件中 118 件（31.8%、Poiroux、2406.07222）。ProofNet 38.5%、miniF2F 16.4%（ReForm の ConsistencyCheck、859 件、2510.24592）。miniF2F-v2 は、形式文と自然言語文の不一致が半数超の問題にあると報告（2511.03108） | 人が書いた形式化にも誤りが多い。LLM の出力は、さらに誤りうる前提で扱う | 注釈者と基準で数字が変わる |
| 逆翻訳＋LLM 判定 | miniF2F-v2: 自動判定が Herald の形式化を 95〜98% 正しいとしたのに、Lean 専門家の判定は 54〜70%（@128）。FormaRL: 判定器の特異度が pass@8 で miniF2F 52.31%、ProofNet 16.25% まで低下 | N 個作って通ったものを採る運用では、偽陽性が増える | 単独では門番にならない |
| LLM-as-judge | CriticLeanBench（誤り 250/正解 250）で誤形式化の検出率（TNR）は Gemini-2.5-Pro 82.8%、Qwen3-32B-RL 85.6%、GPT-4o 40.0%（2507.06181） | 推論モデルを判定器にする。OpenAI gpt-6.x での実測は文献になし | 作った本人の評価 |
| 分解型の採点（LeanScorer、2506.07047） | 適合率 94%、再現率 89%。単純な LLM 判定は適合率 73%、再現率 100% | 元の問いを項目に分解して採点する。実装は軽い | 別データの合成誤りでは正解率 0.666 と低い（FormalRx）。標本数は未確認 |
| BEq / BEq+ | BEq: 適合率 100%、再現率 72.86%（ICLR 2025、200 対）。BEq+: 適合率 98.0%、再現率 48.3%（2406.07222） | 参照の形式化が必要で、PALS では直接使えない。独立に作った 2 つの形式化の比較には使える | 再現率が低い |
| 反例探索・非空虚性テスト | MechGeo: 人手で忠実とされた 157 件のうち 22 件（14.0%）が反例で反駁された。人手で不忠実とされた 43 件のうち 17 件は証明に成功した（幾何） | `plausible` による反例探索、仮定が成り立つ例と成り立たない例の義務の機械生成（AutoIP、2611.06962） | 幾何・研究数学以外への一般化は未確認 |
| 命題の固定（`lake comparator`、SafeVerify） | challenge の命題と solution の型の一致、許可公理（`propext`、`Quot.sound`、`Classical.choice`）のみ、カーネル再検査。LongCat の RL では字句・AST 検査が必要だった（97.6%→27.9%） | statement を確定後に固定する設計はそのまま取れる | `lake comparator` は Lean v4.35.0 以降。古い toolchain での動作は未確認。サンドボックスは Linux のみ |
| Lean の落とし穴 | Nat の減算の切り捨て、0 での除算、`Real.sqrt` の負数、`tsum` の発散、`Finset.range n` が `{0..n-1}`、autoImplicit（Lean community の pitfalls） | 静的検査器（Faults、2606.29493）で一部を自動検出できる。形式化のプロンプトに明示する | 一次情報あり |

## 3. DSPy の具体設計案

### 3.1 先に、批判的な前提

- 公式の推奨データ量に照らすと、現在の 12〜24 枚は、MIPROv2（200 件以上）、RandomSearch（50 件以上）、SIMBA（既定で 32 件以上）のどれにも小さすぎます。GEPA は件数の公式推奨がなく、README の「3 件から動く」は自己申告です。
- 少データでは、反省型の最適化が基線より悪化した報告があります（MAGE、Ntrain=30、62.4→34.0%）。単著で再実装という弱い証拠ですが、方向は警告として妥当です。
- Lean 検査という検証可能な指標は、GEPA の feedback に向いています。ただし PALS では、補題名ヒントと Recipe few-shot が効かなかった事実があります。GEPA が見つける改善も、同種の情報なら効かない可能性があります（推測）。
- 評価の対象を絞らないと、最適化は「命題を弱める」方向に進みます。metric に命題の一致の門を入れる必要があります。

### 3.2 各ステージの扱い

| ステージ | DSPy のモジュール案（入力→出力） | 最適化するか | 理由 |
|---|---|---|---|
| Draft | 問い→簡潔な部分ゴール列 | 後回し | DSP+ では、Draft の寄与は +2.5 点（71.7→74.2）で小さい |
| Sketch | 確定した命題＋部分ゴール列→`sorry` 骨格の Lean コード | 最優先 | 初回の通過率が低く、飛び道具の改善余地がここに集中。単独で測れる |
| Lean 検査と部分修復 | （決定的処理） | しない | モデルを使わない。順位 1 の手法の実装対象 |
| Repair | 失敗した Sketch＋診断→修復後の Sketch | 後回し | 1 回目に効果が集中する。先に入力の作り方を直す |
| Route（経路選択） | 診断→次の経路 | しない | pals-agent #76 で、経路選択の呼び出しは 26→8 に減った。ルールで代替できるか先に確かめる |
| Prove（葉） | 葉の命題＋文脈→tactic 列 | 後回し | 葉が小さく、自動 tactic で閉じる割合が先に決まる |

### 3.3 Sketch に GEPA を使う場合の設計

- 実装の選択肢は 2 つです。`dspy.GEPA` を使うか、独立ライブラリ `gepa` を使うかです。後者ならパイプラインを DSPy に書き換えなくて済む可能性があります（README の記載のみ。PALS では未検証）。
- OpenAI 系の推論モデルの制約: DSPy の判定式は o1〜o5 と gpt-5 系までしか列挙していません。gpt-6.x が該当するかは未確認です。該当する場合は `temperature=1.0`、`max_tokens≧16000` が必要です。`reasoning_effort` は追加の引数として渡され、受け付けられるかは未確認です。
- 最適化後の指示文を DSPy の外で使うと、スコアが動く報告があります（Lemos et al.: DSPy 形式 83%、単純な system message 90%）。最終評価は、本番で使う形式で行います。
- 反省 LM は強いモデルを使います（DSPy の例は gpt-5）。反省 LM の呼び出しは 1 回の最適化で 17〜92 回（論文）で、費用の大半は採点用の Sketch 呼び出しと Lean 検査です。

#### 指標（設計案、出典なし）

初回の Sketch の通過（修復前）を測ります。修復後の成否を混ぜると、修復の出来のよさでシグナルが消えます。

| 順 | 条件 | スコア |
|---|---|---|
| 門 | 確定した命題と一致しない、`axiom` を含む、構文解析できない | 0 |
| 部分点 | Lean エラーがある | 0.5 × (1 − min(1, エラー数/5)) |
| 満点 | 骨格として Lean に通る（`sorry` の警告のみ）で、`sorry` が葉に局所化されている | 1.0 |

feedback の文は、診断コード、先頭 3 件のエラーとその行の前後 2 行、「命題が変わった」旨の注意に限り、長さを切り詰めます。Prove 段のエラーは混ぜません（反省 LM が帰属を誤るため）。

#### データ分割と必要な評価カード数

| 用途 | 枚数（案） | 根拠 |
|---|---|---|
| 最適化の訓練 | 40 | DSPy 公式チュートリアルは train 45〜66 件。論文は 111〜150 件 |
| 最適化の検証（候補の選択） | 40 | チュートリアルは val 45〜66 件。論文は 111〜300 件 |
| 最終報告（一度も見せない） | 60 以上 | 下の検出力の計算 |
| 合計 | 約 140 | 既存の 24 枚は、基線のばらつき測定に使う |

検出力の計算（私の計算、通過率 0.5 の二値、正規近似、独立な 2 群の比較）は次のとおりです。10 点の差を 95% 水準で検出する検出力 50% には約 190 枚/群、検出力 80% には約 390 枚/群が必要です。カードごとに複数回走らせる、または同じカードで対応を取ると、必要枚数は減ります。減る量は未計算です。したがって、60 枚で見えるのは大きな差（+20 点前後）だけです。

#### 費用の概算

| 項目 | 値 | 根拠 |
|---|---|---|
| 1 枚あたりの全パイプラインの推計費用（上限として使う） | 約 $0.050 | 方式 A（Terra medium、修復込み）。`docs/model-call-latency-measurement-results-2026-11-07.md` |
| GEPA の評価呼び出し回数 | 約 560〜1,643 回 | DSPy 公式チュートリアル（AIME 約 560 回、施設サポート情報の抽出 約 1,643 回） |
| 上限の費用 | $28〜$82 | 560〜1,643 回 × $0.050。Sketch と Lean だけなら下回るが、単価は未測定 |
| 逐次の所要時間 | 約 2〜6 時間 | (Sketch 8.2 秒 + Sketch の Lean 検査 4.9 秒) × 560〜1,643 回。1 回の実測（x² の連続性）に基づくため参考値 |

1 回の実行が 1 ドルを超えるため、実行前に確認が必要です（メモリの「有料評価の予算」の方針）。

#### 過学習の対策

1. 最適化の前に、シードの指示文のままで、複数回走らせた通過率の幅を測ります。幅より小さい改善は、採用の根拠になりません。
2. 検証集合で選んだ候補のスコアは楽観的です。最終報告は、一度も使っていないカードだけで行います。
3. 判断基準は事前に登録します（このリポジトリの既存の測定計画と同じ方式）。基線との差の 95% ブートストラップ区間が 0 をまたぐなら、採用しません。悪化したカードがあれば、その内容を確認します。
4. 推論モデルは温度が固定のため、同じカードでも通過と失敗が揺れます。ミニバッチ 3 件での採否は偶然の影響を強く受けます。1 カード 1 回の採点には限界があります。

### 3.4 他の最適化器の扱い

- MIPROv2、SIMBA、COPRO は、現在の枚数では対象外です。評価カードを 200 枚以上に増やせるまで見送ります。
- BootstrapFewShot は、few-shot が効かなかった実績があるため見送ります。
- BootstrapFinetune は、自前学習をしない前提のため対象外です。

評価カードの増やし方は決まっていません。カタログ追加が停止中の方針との関係を、別途確認する必要があります。

## 4. 検証計画

測る順序は、費用が安く、判定しやすいものからです。各段階の実行結果は、AGENTS.md の方針どおり、docs か PR 本文に書き、品質台帳に 1 行を足します。判定基準は、事前登録として実行前に固定します。

| 段階 | 検証すること | 方法 | 指標（スコア） | カード数・反復 | 推計費用 | 判定の目安 |
|---|---|---|---|---|---|---|
| 0 | 失敗の内訳と、保存されていないデータの補充 | 既存の 24 カードの結果を診断コード別に集計。失敗した Sketch の本文を保存して再実行 | 診断コード別の件数、最初の試行の `formal_harness_mismatch` の割合 | 24 枚、1 回 | 約 $0.6 のモデル呼び出し（Terra medium の 12 枚、過去の計画と同水準） | 費用が $1 未満で、確認は不要 |
| 1 | 命題の固定（順位 2） | 命題をテンプレートで差し込む版と現行版を、同じ 12 カードで比べる | 成功数（現行 10/12）、`formal_harness_mismatch` の件数 | 12 枚 × 2 方式 × 3 回 | 約 $3.6（上限、1 枚 $0.05） | 事前登録。最終失敗の 2 枚が通るか |
| 2 | 決定的な部分修復のオフライン閉鎖率（順位 1） | 段階 0 で保存した失敗 Sketch に、`try?` と `first \| grind \| aesop \| simp_all \| omega \| nlinarith \| positivity \| bound` を当てる | 穴の閉鎖率、Lean 秒、重複 | 失敗した葉すべて | モデル呼び出しなし（Lean 時間のみ） | 閉鎖率が低ければ、順位 1 は後回し |
| 3 | 修復入力の作り直しと 1 回での打ち切り（順位 3） | 現行と新しい入力（インライン、tactic state、検索結果）を比べる | 成功数、呼び出し数、壁時計 | 24 枚 × 2 方式 | 約 $2.4（上限） | 呼び出し数と壁時計の差で判断 |
| 4 | 並列 n と low→medium 昇格の再測定（順位 5） | 既存の方式 D（昇格）の再現、骨格を変えた並列 n=3 | 壁時計、$/枚、成功数 | 24 枚 × 2 回 | 約 $2.4〜$4.8（上限） | 既存の探索結果の再現を確認 |
| 5 | 失敗した葉の再分解（順位 4） | 深さ 1 の再分解を、難問のみに足す | 成功数、トークン数、壁時計 | 難問 12 枚 | 未見積り（Hilbert の費用が大きい） | 段階 2〜3 の後 |
| 6 | Sketch の GEPA（条件つき） | 3.3 節の設計 | 初回通過率の差（本番形式で評価） | 約 140 枚 | $28〜$82（上限） | 評価カードが増えてから |

費用は 1 枚 $0.050 の上限を使った私の計算です。段階 3 以降の一部は 1 回 $1 を超えます。実行前に確認してください。

## 5. 未確認の点

### 5.1 PALS 固有

- 失敗した Sketch の本文。結果の JSONL に保存されておらず、決定的な修復の効果は既存データでは測れません。
- 初回の Sketch が通る確率 6/12 の測定に使ったモデルと条件。
- PALS が使う gpt-6.x が Lean 3 構文を出すか、旧 API 名を使う頻度。
- `formal_harness_mismatch` が、モデルによる命題の書き換えだけを指すのか、ハーネス側の不一致も含むのか。
- 評価カードの増やし方（カタログ追加が停止中）。

### 5.2 文献

- reasoning effort を固定した Lean 通過率の公表値。
- Lean に DSPy の最適化器を適用した公開事例。SIMBA と COPRO の公式の数字。GEPA の `auto` が何回のフル評価に当たるか。
- gpt-6.x が DSPy の推論モデル判定に一致するか。プロンプトキャッシュとの相性。
- `grind` の一次の定量評価。`exact?`、`apply?`、`rw?`、`try?` の成功率。Sketch の葉に対するカスケードの閉鎖率。
- 全証明修復で tactic state の有無を単独で比べた研究。
- docstring の単独効果。「命題を変えるな」という制約文の単独効果。旧 API 名の誤用率。
- OpenAI gpt-6.x を判定器・形式化器にした場合の誤り率。日本語入力での形式化の誤り率。
- `lake comparator` を古い Lean toolchain で使えるか。`proof_wanted` が Lean 本体の機能か Mathlib のものか。
- Leanstral 1.5 と Aristotle の API の期限、価格、レート。Seed-Prover 1.5 の 88% と公式結果 581/672 の食い違い。
- 取得ツールの要約経由の数字（Delta Prover、Goedel-Architect、DSP+ の図の値、MA-ProofBench、PutnamBench の結果ファイルなど）は、原文での再確認が必要です。DSP+ の miniF2F-valid の値は見つかりませんでした。

## 6. 出典

論文は題名、著者、年、URL の順です。

### DSP と後継

- Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs. Jiang, Welleck, Zhou, Li, Liu, Jamnik, Lacroix, Wu, Lample. 2022（ICLR 2023）. https://arxiv.org/abs/2210.12283
- Reviving DSP for Advanced Theorem Proving in the Era of Reasoning Models（DSP+）. Cao, Song, Li, Le, Zhang, Xue, Yang. 2025. https://arxiv.org/abs/2506.11487
- Baldur: Whole-Proof Generation and Repair with Large Language Models. First, Rabe, Ringer, Brun. 2023. https://arxiv.org/abs/2303.04910
- LEGO-Prover: Neural Theorem Proving with Growing Libraries. Wang ほか. 2023. https://arxiv.org/abs/2310.00656
- Lyra: Orchestrating Dual Correction in Automated Theorem Proving. Zheng ほか. 2023. https://arxiv.org/abs/2309.15806
- Decomposing the Enigma: Subgoal-based Demonstration Learning for Formal Theorem Proving. Zhao, Li, Kong. 2023. https://arxiv.org/abs/2305.16366
- ProofAug: Efficient Neural Theorem Proving via Fine-grained Proof Structure Analysis. Liu, Sun, Li, Yao. 2025. https://arxiv.org/abs/2501.18310
- APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning. Ospanov, Farnia, Yousefzadeh. 2025. https://arxiv.org/abs/2505.05758
- Solving Formal Math Problems by Decomposition and Iterative Reflection（Delta Prover）. Zhou ほか. 2025. https://arxiv.org/abs/2507.15225
- Hilbert: Recursively Building Formal Proofs with Informal Reasoning. Varambally ほか. 2025. https://arxiv.org/abs/2509.22819
- Prover Agent: An Agent-Based Framework for Formal Mathematical Proofs. Baba, Liu, Kurita, Sannai. 2025. https://arxiv.org/abs/2506.19923
- Ax-Prover: A Deep Reasoning Agentic Framework for Theorem Proving in Mathematics and Quantum Physics. Breen ほか. 2025. https://arxiv.org/abs/2510.12787
- Seed-Prover: Deep and Broad Reasoning for Automated Theorem Proving. ByteDance Seed. 2025. https://arxiv.org/abs/2507.23726
- Seed-Prover 1.5: Mastering Undergraduate-Level Theorem Proving via Learning from Experience. ByteDance Seed. 2025. https://arxiv.org/abs/2512.17260
- Goedel-Architect: Streamlining Formal Theorem Proving with Blueprint Generation and Refinement. Chung ほか. 2026. https://arxiv.org/abs/2606.06468
- DeepSeek-Prover-V2: Advancing Formal Mathematical Reasoning via Reinforcement Learning for Subgoal Decomposition. Ren ほか. 2025. https://arxiv.org/abs/2504.21801

### DSPy とプロンプト最適化

- DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines. Khattab ほか. 2023. https://arxiv.org/abs/2310.03714
- Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs（MIPROv2）. Opsahl-Ong ほか. 2024. https://arxiv.org/abs/2406.11695
- GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning. Agrawal ほか. 2025. https://arxiv.org/abs/2507.19457
- DSPy のソースとドキュメント. https://github.com/stanfordnlp/dspy 、https://dspy.ai/current/api/optimizers/GEPA/overview/
- MAGE: Understanding Stability-Performance Trade-offs in Multi-component Prompt Optimization. Singh. 2026. https://arxiv.org/abs/2607.11944
- Is It Time To Treat Prompts As Code? A Multi-Use Case Study For Prompt Optimization Using DSPy. Lemos, Alves, Ferraz. 2025. https://arxiv.org/abs/2507.03620
- TextGrad: Automatic "Differentiation" via Text. Yuksekgonul ほか. 2024. https://arxiv.org/abs/2406.07496
- Large Language Models as Optimizers（OPRO）. Yang ほか. 2023. https://arxiv.org/abs/2309.03409
- Fine-Tuning and Prompt Optimization: Two Great Steps that Work Better Together. Soylu, Potts, Khattab. 2024. https://arxiv.org/abs/2407.10930

### 検索・自動化 tactic

- LeanDojo: Theorem Proving with Retrieval-Augmented Language Models. Yang ほか. 2023. https://arxiv.org/abs/2306.15626
- Lean Copilot: Large Language Models as Copilots for Theorem Proving in Lean. Song ほか. 2024. https://arxiv.org/abs/2404.12534
- A Semantic Search Engine for Mathlib4（LeanSearch）. Gao ほか. 2024. https://arxiv.org/abs/2403.13310
- LeanSearch v2: Global Premise Retrieval for Lean 4 Theorem Proving. Gao ほか. 2026. https://arxiv.org/abs/2605.13137
- REAL-Prover: Retrieval Augmented Lean Prover for Mathematical Reasoning. 2025. https://arxiv.org/abs/2505.20613
- Lean Finder: Semantic Search for Mathlib That Understands User Intents. 2025. https://arxiv.org/abs/2510.15940
- Premise Selection for a Lean Hammer（LeanHammer）. Zhu, Clune, Avigad, Jiang, Welleck. 2025（ICLR 2026）. https://arxiv.org/abs/2506.07477
- Lean-Auto. Qian, Clune, Barrett, Avigad. 2025. https://arxiv.org/abs/2505.14929
- Canonical for Automated Theorem Proving in Lean. Norman, Avigad. 2025. https://arxiv.org/abs/2504.06239
- ProofGap: Benchmarking Step-Level Formal Reasoning with Local Obligations Derived from Natural-Language Solutions. 2026. https://arxiv.org/abs/2609.29296
- Lean の `grind` のリファレンス. https://lean-lang.org/doc/reference/latest/The--grind--tactic/
- 自己申告のモデルカード（grind と LeanHammer の miniF2F）. https://huggingface.co/ChristianZ97/satp-policy-v4.27

### 修復・サンプリング

- Compile to Compress: Boosting Formal Theorem Provers by Compiler Outputs. Li, Tian, Wang. 2026. https://arxiv.org/abs/2604.18587
- Fix, Not Just Resample: Bounded Compiler-Guided Repair in Lean 4. Deng ほか. 2026. https://arxiv.org/abs/2610.26942
- Learning to Repair Lean Proofs from Compiler Feedback（APRIL）. Wang ほか. 2026. https://arxiv.org/abs/2602.02990
- Inference-Time Diversity in RL-Trained Lean Theorem Provers: A Diagnostic Study. Burton. 2026. https://arxiv.org/abs/2601.16172
- Evaluation of LLMs for Mathematical Formalization in Lean. Klingner ほか. 2026. https://arxiv.org/abs/2606.05632
- Large Language Monkeys: Scaling Inference Compute with Repeated Sampling. Brown ほか. 2024. https://arxiv.org/abs/2407.21787
- DeepSeek-Prover-V1.5. Xin ほか. 2024. https://arxiv.org/abs/2408.08152
- Goedel-Prover-V2: Scaling Formal Theorem Proving with Scaffolded Data Synthesis and Self-Correction. Lin ほか. 2025. https://arxiv.org/abs/2508.03613
- Kimina-Prover Preview. Wang ほか. 2025. https://arxiv.org/abs/2504.11354
- Leanabell-Prover-V2. Ji ほか. 2025. https://arxiv.org/abs/2507.08649
- StepFun-Prover Preview. Shang ほか. 2025. https://arxiv.org/abs/2507.20199

### プロンプト形式・学習済みモデル

- DeepSeek-R1. DeepSeek-AI. 2025. https://arxiv.org/abs/2501.12948
- From Harm to Help: Turning Reasoning In-Context Demos into Assets for Reasoning LMs. 2025. https://arxiv.org/abs/2509.23196
- Innate Reasoning is Not Enough: In-Context Learning Enhances Reasoning Large Language Models with Less Overthinking. Ge ほか. 2025. https://arxiv.org/abs/2503.19602
- ProofEvolve. Ye ほか. 2026. https://arxiv.org/abs/2608.26334
- TheoremLlama. Wang ほか. 2024. https://arxiv.org/abs/2407.03203
- MA-ProofBench: A Two-Tiered Evaluation of LLMs for Theorem Proving in Mathematical Analysis. 2026. https://arxiv.org/abs/2606.13782
- PutnamBench の結果ファイル. https://github.com/trishullab/PutnamBench（`docs/results.json`）
- Leanstral 1.5. Mistral. 2026. https://mistral.ai/news/leanstral-1-5/
- OpenAI, Reasoning best practices. https://developers.openai.com/api/docs/guides/reasoning-best-practices

### 自動形式化の品質

- Reliable Evaluation and Benchmarks for Statement Autoformalization（ProofNet#、BEq+）. Poiroux ほか. 2024. https://arxiv.org/abs/2406.07222
- ReForm（ConsistencyCheck）. Chen ほか. 2025（ICLR 2026）. https://arxiv.org/abs/2510.24592
- miniF2F-Lean Revisited（miniF2F-v2）. Ospanov, Farnia, Yousefzadeh. 2025. https://arxiv.org/abs/2511.03108
- CriticLean. Peng ほか. 2025. https://arxiv.org/abs/2507.06181
- FormaRL. Huang ほか. 2025. https://arxiv.org/abs/2508.18914
- Mathesis（LeanScorer）. Yu ほか. 2025. https://arxiv.org/abs/2506.07047
- Rethinking and Improving Autoformalization（BEq）. Liu ほか. ICLR 2025. https://proceedings.iclr.cc/paper_files/paper/2025/hash/d630537fc4402cfa3ebbc7450a0cac91-Abstract-Conference.html
- MechGeo. Shen ほか. 2026. https://arxiv.org/abs/2608.02295
- LongCat-Flash-Prover. 2026. https://arxiv.org/abs/2603.21065
- Faults in Our Formal Benchmarking. Ammanamanchi, Bhat, Biderman. 2026. https://arxiv.org/abs/2606.29493
- Formalizing inverse problems in the age of AI: possibilities, pitfalls, and an invitation（AutoIP）. Clason, Helin, Nursultanov, Oksanen. 2026. https://arxiv.org/abs/2611.06962
- Formal Conjectures. Firsching ほか. 2026. https://arxiv.org/abs/2605.13171
- `lake comparator`（Lean v4.35.0 リリースノート）. https://lean-lang.org/doc/reference/latest/releases/v4.35.0/
- SafeVerify. https://github.com/GasStationManager/SafeVerify
- Lean community, Pitfalls. https://leanprover-community.github.io/extras/pitfalls.html
