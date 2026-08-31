# Design: Platform Architecture

## Component Boundaries

```text
pals-webfront / pals-draft-admin
              |
           pals-api
              |
          pals-agent
        (Agent + Lean)
```

- ARCH-029: environment ごとに設定と操作対象を分ける。
- ARCH-030: Local は Compose を入口とし、必要な依存をローカルで再現する。
- ARCH-031: Agent/Lean source は `pals-agent` にまとめる。process/container の構成は
  deployment の選択であり、source repository を増やす理由にしない。
- ARCH-032: API と各 UI の責務は repository topology に合わせる。
- ARCH-033: Local inference と Apple Silicon tuning は別用途として扱う。
- ARCH-034〜ARCH-035: secret と生コンテンツを設定・ログ・成果物へ流さない。
- ARCH-036: `pals-infra` が Draft Admin の authentication と network perimeter を所有する。
  `pals-draft-admin` は trusted ingress からだけ到達可能とし、content route は perimeter
  の内側に限定する。readiness は content-free に保ち、外部公開の例外にしない。

Slice 固有の API、schema、認証、transport、AWS resource、migration は、この文書へ先回り
して追加せず、その作業の所有 repository で決めます。
