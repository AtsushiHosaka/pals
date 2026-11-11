# 関所の effort と短い出力: 誤受理・誤却下・遅延 (2026-11-12)

- 指標: 時間(関所は命題が出た後の直列)と、誤受理 0 の維持。
- 仮説: 関所の待ちは出力トークンと effort で縮み、`checks` 欄を省いた短い review でも精度は落ちない。
- 変更: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)の `terse_review`(`faithful` と一行の `issue` だけ)と `terse_roundtrip`、`run_gate_fast.py`。既存の review/往復の文言は変えていない。
- 測定の条件: Luna、敵対 19 組(弱めた命題 19 + 忠実な形 19、各 2 回 = 38 件)、effort none と low、並列度 4、2026-11-12。n=38(各群)。
- 結果:

| 関所 | effort | 誤受理 | 誤却下 | p50 / p90 |
|---|---|---|---|---|
| review(現行) | none | 2/38 | 2/38 | 3.4 / 4.1 s |
| review(現行) | low | 1/38 | 1/38 | 5.0 / 6.6 s |
| 往復の 1 呼び | none | 0/38 | **11/38** | 2.8 / 4.2 s |
| 往復の 1 呼び | low | 1/38 | 4/38 | 4.2 / 7.1 s |
| 往復の 1 呼び(出力を短く) | none / low | 1/38 / 0/38 | 10/38 / 4/38 | 2.5 / 4.3 s(縮まず) |
| **terse review** | none | **0/38** | **0/38** | **2.1 / 2.9 s** |
| terse review | low | 1/38 | 0/38 | 2.8 / 3.5 s |

  別の初回走(各 1 回)では往復の 2 呼び(none): 誤受理 1/19、誤却下 0/19、p50 4.9 s。
- 判断: terse review(none)を関所の主力に採用。往復は none で誤却下が多すぎ、low では時間が縮まない。
- 注意: terse の文言に「斜体は体ではない」など、敵対セットの失敗の型を入れている。**未知の型への検出力は未測定**で、この 38 件への当てはめ以上のことは言えない。往復を使わないと「命題を見ずに言い換える」独立性を失う。
- 次にやること: 敵対セットの外の弱い命題(held-out の型)での誤受理の測定。
- 出典: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)、生データ `data/2026-11-12-fast-answer/gf-gate_*.jsonl`、`rt_*-variants.jsonl`(診断文は除去)。
