# Tasks: Platform Architecture

- [ ] ARCH-T1 (`ARCH-029`). Local / dev / prod の設定境界を実装と文書で一致させる。
- [ ] ARCH-T2 (`ARCH-030`). Local Compose の起動・停止と主要 dependency を smoke test する。
- [ ] ARCH-T3 (`ARCH-031`, `ARCH-032`). Agent / Lean source ownership の重複がないことを確認する。
- [ ] ARCH-T4 (`ARCH-034`, `ARCH-035`). tracked secret とログへの秘密情報混入を検査する。
- [ ] ARCH-T5 (`ARCH-033`). Local inference と Apple Silicon tuning の接続経路を確認する。
- [ ] ARCH-T6 (`ARCH-036`). `pals-infra` の deployment perimeter で Draft Admin の
  authenticated/network-restricted ingress と content-free non-public readiness を検証する。

具体的な architecture slice は、選択された作業だけを focused task として追加します。
