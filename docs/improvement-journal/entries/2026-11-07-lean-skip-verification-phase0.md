# Lean 再検証を避ける方針の Phase 0 測定（2026-11-07）

- 指標: 時間（Lean 検証）
- 仮説: 検証済み補題を再コンパイルしない（型だけのスタブに替える）と、Lean の時間が大きく縮む。
- 変更: なし（測定のみ。モデル呼び出しなし、費用0）。
- 測定の条件: ローカルの Mac 1台、PALS 固定版 Lean 4.32.0-rc1、`lake env lean` を各3回の中央値。AWS 本番の値ではない。
- 結果:

| ファイル | `lake env lean` | `lean` 直接 |
|---|---:|---:|
| import なし | 1.79秒 | 0.41秒 |
| `Mathlib.Algebra.Group.Basic` のみ | 2.48秒 | 1.17秒 |
| `import Mathlib` | 8.03秒 | 7.16秒 |
| カード43件（calculus-v5-batch） | 9.67秒 | 8.83秒 |

  カードの elaboration は、全体から `import Mathlib` を引くと1件あたり約40〜110ミリ秒。`lake env` の起動だけで0.9〜1.4秒かかる。
- 判断: **Lean の時間は elaboration ではなく、起動と import が占める。** スタブ化で省けるのは約1秒で、方針の価値は小さい。環境再利用（`PALS_LEAN_REUSE_LAKE_ENVIRONMENT`）のほうが効く。
- 限界・未確認: ローカル測定。
- 次にやること: `lake env` の除去（pals-agent #75）。
- 出典: [lean-skip-verification-phase0-2026-11-07.md](../../lean-skip-verification-phase0-2026-11-07.md)、台帳の該当行
