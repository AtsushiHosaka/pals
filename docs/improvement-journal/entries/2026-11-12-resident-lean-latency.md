# 常駐 Lean の検証 1 回の時間: cold 対 常駐、Mac と Linux イメージ (2026-11-12)

- 指標: 時間(検証 1 回 = 方針検査 + コンパイル + 信頼監査)。
- 仮説: 常駐の子なら、検証 1 回は 2 秒未満で、cold と判定が変わらない。
- 変更: [pals-agent#120](https://github.com/AtsushiHosaka/pals-agent/pull/120)(既定 off)。
- 測定の条件: Lean 4.32.0-rc1。Mac: 共有機、負荷平均 11〜21、16 件(通る 12、拒否 4: 誤った主張、未解決のゴール、`variable`/`include`、記法の再定義)、各 1 回、cold は `lake env` の環境再利用なし。Linux: 本番検証器と同じローカルイメージ(aarch64)、8 CPU、メモリ 24 GiB の一時コンテナ、`LeanVerifier` を通さず `ResidentLean` を直接。n は件数(Linux は 3〜10)。モデル呼び出しなし、費用 0。
- 結果:
  - Mac、`LeanVerifier.verify` 全体: 単独 p50/p90 は cold 15.8/17.0 秒、常駐 1.33/1.41 秒。10 並行(20 件を 10 スレッド)は cold 35.9/36.8 秒(全体 57.8 秒)、常駐 1.80/2.04 秒(全体 3.3 秒)。**判定(成功と error 診断コード)は 16 件すべて一致**。
  - Linux イメージ: zygote 起動 6.1 秒、コンパイル 0.76〜0.82 秒(`.olean` 出力あり)、監査 0.48 秒、10 並行は最大 1.09 秒(全体 1.11 秒)。cold の `lake env lean` コンパイルは 2.9〜3.0 秒(1 回目 5.5 秒)。
  - メモリ(Linux): zygote の RSS 8.3 GB(読み取り専用の `.olean` 6.3 GB、private 2.0 GB)、`exact?` の索引つきで 10.1 GB(起動 14 秒)。子 1 つの private は索引なしで 200〜220 MB、索引つきで 6〜14 MB。`exact?` を子で初回に実行すると 20.7 秒・2.0 GB、索引つきなら 0.18 秒。10 並行の cgroup ピークは約 5.0 GB。暴走した確保は子だけが約 6 秒で打ち切られた。
- 判断: 採用(既定 off)。固定費は消えた。
- 限界・未確認: 本番の実機ではない。Mac の負荷で絶対値は上振れしている。cold の「本番相当」の値(環境再利用あり)は測っていない。常駐の `.olean` と cold の `.olean` のバイト一致は見ていない(判定の一致のみ)。
- 次にやること: 本番の `lean_child.py` で包んだ状態の測定、`http_runtime.py` への接続(担当と調整)。
- 出典: [pals-agent#120](https://github.com/AtsushiHosaka/pals-agent/pull/120)、`docs/verification/resident-lean-2026-11-12.md`、生データ `docs/improvement-journal/data/2026-11-12-resident-lean/`。
