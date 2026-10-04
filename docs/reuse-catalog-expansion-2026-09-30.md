# 一般命題のDraft追加 — 2026-09-30

ユーザーの「大学1年の線形代数・微積分と、アティヤ＝マクドナルド水準の可換環論を増やし、OpenMath標準化を維持する」という依頼に基づく初回追加。既存のDCE-001、005–007、012、014を作業基準とし、既存の型付きprofileとDraftの取得用フィールドを維持した。網羅性や公開完了を宣言するものではない。

続く[一般定理Draftの拡充v2](math-expansion-v2-20260930.md)で、可変指数・次元と基底・商加群と中山の補題など77件を追加し、型付きローカル保管庫は368件になった。以下の件数と不足領域は初回追加時点の記録である。

## 新規作成

| 分野 | 件数 | 内容 | 作成物 |
|---|---:|---|---|
| 微積分 | 29 | 一般関数の微分則、合成・商、微分値の一意性、連続性、区間可積分性、ε–δ | [manifest](calculus-reuse-batch-20260930.json)、[Lean](calculus-reuse-batch-20260930.lean) |
| 線形代数 | 24 | 核と単射、像と全射、合成、片側逆、分裂・冪等写像による分解、完全性 | [manifest](linear-algebra-reuse-batch-20260930.json)、[Lean](linear-algebra-reuse-batch-20260930.lean) |
| 可換環論 | 16 | 根基、互いに素なイデアル、素イデアルへの包含、極大存在、根基の素イデアルによる特徴付け | [manifest](commalg-reuse-batch-20260930.json)、[Lean](commalg-reuse-batch-20260930.lean) |

計69件。線形代数は体上の場合を含む可換環上の一般の加群・線形写像として記述した。数値や変数名だけを変えた追加はない。新規69件と従来の型付き222件の間でcanonical OpenMathの衝突はなく、既存監査の変数名・定数だけの違いを検出する検査でも、新規分に関連する重複候補はなかった。全件4–10段階のSketchを持つ。

初年級線形代数の基底・次元・階数・固有値・直交化、微積分の任意自然数指数・級数・積分値・平均値定理、可換環論のテンソル積・平坦性・中山・完備化等は、今回の既存profileで正確に表現できず未追加。今回の件数をこれらの網羅率に換算しない。

## 検証と標準化

- 新規69件と既存未登録59件（整拡大20、準素分解22、鎖条件・次元17）の証明を、既存のLean workspaceで実コンパイルした。
- 環境：`leanprover/lean4:v4.32.0-rc1`、Mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`。
- 新規manifestは既存の型検査・canonicalizationを通す。Lean本文全体、toolchain、Mathlib、validator、registryの実ファイルをhashで対応付ける。
- Draft取得用データにLeanコードや審査結果を混ぜず、作成manifest側に証拠を残す。新規loaderの状態は `local_authoring_evidence_bound_not_admitted`。hash一致だけでコンパイルや意味審査の成功を推定しない。
- 微積分と可換環論は互いに別の担当が全件の自然文・OpenMath・Leanを照合した。線形代数は親担当が全24件の命題、型付きXML、Lean、反例を照合した。
- 誤適用の評価用に、微積分16・線形代数24・可換環論8、計48件の反例付き質問を作成。これは検索試験の成功結果ではない。
- loader、既存profile、routing、structuringに関する対象テスト120件が成功。追加の微分引数対応・カバレッジ監査テスト24件、対象Ruff、新loaderのMypy、diffの空白検査も成功。

意味レビューで、モデル向けguidanceの `has_deriv_at` が既存sealedデータと異なる引数順になっていることを発見した。既存契約は **OpenMath `(f, point, slope)` → Lean `(f, slope, point)`**。guidanceをこの順序へ修正し、新規10微分カードの引数対応とguidanceを検査する回帰テストを加えた。型が同じ二つの実数引数の交換は、型検査・Lean証明単独では検出できない。既存のXML、registry、validatorの意味とbytesは変更していない。

## 登録状況

作業前の読み取り確認では、通常Draft431件、型付きauthoring163件・embedding163件、型付き公開中0件だった。今回のファイル追加で型付き作成物は222件から291件になった。DBに未登録の既存59件と新規69件、合計128件を登録対象とする。

OpenAIへのembedding送信は当初自動承認レビューに拒否されたが、その後ユーザーが外部送信・ローカルDB追加を明示承認した。[継続承認の記録](../承認リスト.md)を保存し、128件すべてで実際のembeddingを生成した。送信内容は `output/draft-expansion-20260930/embedding-inputs.json` に保存。入力は既存契約どおり形式の版・profile ID・canonical OpenMathのみで、自然文、証明コード、秘密情報は含めない。送信先は `https://api.openai.com/v1/embeddings`、モデルは `text-embedding-3-small`、384次元。

128件と対応するembeddingを、既存の `pals_local_typed_catalog` に単一トランザクションで追記した。型付きDraft・embeddingは各163件から291件、manifestは14件から20件、profileは13件から16件になった。全128件を読み戻し、命題・OpenMath・hash・証明方針・Sketch・canonicalizer版・manifest対応・authoring状態・embedding固定設定が入力と一致することを確認した。ベクトルは全件384次元かつ非零。通常Draft431件と型付き公開中0件は変更していない。

証跡は `output/draft-expansion-20260930/` の `before-insert.json`、`after-insert.json`、`insert-128.log`、`persisted-verification.json`。登録SQLのSHA-256は `2eeab60428aee2299031a68fb7864bcdcb9809b9aee9fb3438ac0ab87ca07a5a`。既存コンテナを再利用し、権限やスキーマを変更せず、新規サービスを作成していない。

署名付き公開、実際の検索・適用精度の評価、本番への反映は未実施。authoring保管庫への追加であり、回答時に取得できることや精度向上を証明する結果ではない。既存ファイルの変更を保持し、stage・commitは行っていない。
