# Stacks Project 形式化(AxiomMath/Stacks)の取り込み試験 2026-11-07

Axiom が 2026-11-04 に公開した [AxiomMath/Stacks](https://github.com/AxiomMath/Stacks) を、PALS に取り込めるかを測った記録です。モデル呼び出しはなく、費用は0です。実測はすべて 1 台のローカル Mac（18コア、128GB）で行いました。

## 対象

- コミット: `5ed82d1`（2026-11-06）。Lean `v4.35.0`、Mathlib はタグ `v4.35.0`（`56a0058`）。ライセンスは Apache-2.0。
- PALS の固定版は Lean `v4.32.0-rc1` と Mathlib のコミット `8b62164`（`pals-agent/lean-workspace`）。

## 結果

### 1. 規模と信頼度の内訳

| 層 | ファイル数 | 行数 | 内容 |
|---|---|---|---|
| `StacksCore`（人間レビュー済み） | 445 | 37,374 | 多くは Mathlib の既存宣言への `add_to_stacks` タグ付け |
| `StacksFrontier`（AI 生成、レビュー前） | 62,527 | 18,018,675 | 代数幾何の本体はすべてこちら |

「Stacks が形式化された」と言われる内容の実質は `StacksFrontier` にあります。カーネルは通っていても、定義や文の忠実度は人間が見ていません。

### 2. 利用コスト（1 定理を使うために必要なビルド）

- `lake exe cache get`（Mathlib のコンパイル済みキャッシュ 9,031 ファイル）: 2分33秒。`.lake` は 7.2GB。
- Stacks 側のキャッシュは未提供で、依存はソースからビルドします。
- 依存の大きさ（`AlgebraicGeometry` 配下の400モジュールを無作為抽出、Stacks 内の import 閉包）: 中央値 1,243 モジュール・約45万行、最大 24,406 モジュール。
- 実ビルド:

| 対象 | 実時間 | CPU(user) | 最大メモリ | ビルドジョブ数 |
|---|---|---|---|---|
| 葉モジュール `Crystalline.DividedPowerEnvelope.FlatRelation`（116行、依存なし） | 16.7秒 | 7.0秒 | 1.25GB | 少数 |
| `Spaces.AffineEtaleQuasicoherentModules`（AG 内の閉包は321モジュール） | 3,571秒 | 13,791秒 | 3.2GB | 6,701 |

2 件目は他のコンパイル（カード再検証2本）と同時に動かしたため、実時間は上限です。CPU 時間のほうが目安になります。AG 内の import だけ数えた321モジュールに対し、実際は RingTheory など他分野を含む6,701ジョブになりました。依存の大きさは AG 内の import だけでは見積もれません。成果物は `.lake/build` が 5.7GB です。

### 3. Lean/Mathlib の版差による既存カードの壊れ方

PALS の `docs/*.lean` 42ファイル（宣言744件）を、同じ手順で `lake env lean` により再コンパイルしました。

| 環境 | 失敗ファイル | エラー数 |
|---|---|---|
| PALS 固定版（Lean 4.32.0-rc1） | 0 / 42 | 0 |
| Mathlib `v4.35.0`（Lean 4.35.0） | 2 / 42 | 4 |

失敗は `commalg-reuse-batch-20260930.lean:74` と `typed-commutative-algebra-v1-authoring-witnesses.lean:17,21,25` で、どれも `Ideal.mul_le_right` / `Ideal.mul_le_left` を使う箇所の型不一致です。原因（シグネチャ変更かどうか）は未確認です。デプリケーション警告の件数は集計していません。宣言744件のうち4件（約0.5%）が壊れた見積もりで、直前の版との差ではなく3バージョン分の差です。

## 判断

- Stacks を PALS にそのまま依存追加することはできません（Lean 4.35 と 4.32.0-rc1 の差）。
- 全体を載せるのは非現実的で、モジュールの閉包ごとの切り出しと、Stacks 側キャッシュの提供待ちが必要です。
- 初期に使うなら `StacksCore` までで、`StacksFrontier` は定義の忠実度を確認できる工程ができてから。
- 版を上げた場合の再検証コストは、PALS が Recipe を検証器の digest に結びつけていることに由来します。Lean 自体の非互換は上の通り小さい（0.5%）。結びつけ方の緩和は別の設計課題です。

## 再現手順

```bash
git init repo && cd repo
git remote add origin https://github.com/AxiomMath/Stacks.git
git fetch --depth 1 origin 5ed82d14634e8d9576bb844c7bd4e3da66d450e7   # 測定したコミット（5ed82d1）
git checkout FETCH_HEAD
lake exe cache get
lake build StacksFrontier.AlgebraicGeometry.Crystalline.DividedPowerEnvelope.FlatRelation
```

試験に使った一時ファイル（clone、`.lake`）は終了後にすべて削除しました。
