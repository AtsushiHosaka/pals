# Lean 検証の待ち時間の短縮 2026-11-08

Lean 検証の待ち時間を減らす変更を [pals-agent#75](https://github.com/AtsushiHosaka/pals-agent/pull/75) にまとめました。ローカルの1台の Mac（固定版 Lean 4.32.0-rc1、ネイティブ toolchain）での測定です。AWS 本番の値ではありません。モデル呼び出しはなく、費用は0です。配備とフラグの有効化は行っていません。

## 変更

- **`lake env` の起動を避ける。** 環境再利用フラグ（`PALS_LEAN_REUSE_LAKE_ENVIRONMENT`、pals-agent#24）は main にあり、初回の検証で `lake env` の結果を解決して以降は `lean` を直接起動します。今回、起動時に1回だけ環境を解決するウォームアップと、準備が拒否された設定の再試行抑制（60秒）を足しました。既定値は `false` のままです。
- **再利用は監査にも効く。** 受理された証明では、コンパイルの後に信頼できる監査（`lake env lean --run`）が走ります。フラグが有効なら、この2回の起動の両方で `lake env` を省きます。pals-agent#24 の測定は監査の追加前でした。
- **Lean 結果のポーリング間隔を詰める。** worker の待ちを 1.0 秒固定から、0.25 秒（最初の30秒）、0.5 秒（90秒まで）、1 秒に変えました。API 側の検証開始はイベント駆動で、直す箇所は worker だけでした。

## 測定

### `lake env` あり/なし

同じ4ソース（狭い import）を5回ずつ、順序を交互にして検証1件の壁時間を測りました。フラグ有効側は暖機済みです。他のセッションが同じマシンで動いていたため、絶対値は揺れます。

| ソース | フラグなし 中央値 | フラグ有効 中央値 |
|---|---:|---:|
| group-kernel-injectivity | 4955 ms | 3322 ms |
| sequence-limit-addition | 5870 ms | 4124 ms |
| coprime-product-divisibility | 5196 ms | 3461 ms |
| linear-kernel-sum | 5866 ms | 3593 ms |
| 全体（n=20） | 5752 ms | 3571 ms |

全体で中央値2.2秒の短縮です。同じ入力で組にした差の中央値は1.77秒で、20組すべてで速くなりました。`import Mathlib` の既存カードでは検証が10〜15秒かかり、短縮は1〜2秒です。import が支配的なためです。ウォームアップ自体は、初回が747 ms、2回目が3 msでした。

結果の同一性は、`testdata/mathematical-breadth-v1` の既存カード8件と、各カードに誤り（偽の定理、型エラー）を足した16件の計24件で確認しました。成否と診断（severity、code、message）は24件すべて同じでした。

### ポーリング待ち

`pals-agent/tools/latency/poll_lag.py` で、worker の実際の待ちと HTTP 転送をローカルのスタブ API に対して測りました。20回を3セット行った結果です。

| | 変更前 | 変更後 |
|---|---:|---:|
| 検証完了から worker が気づくまでの中央値 | 635〜836 ms | 335〜447 ms |
| 同 p95 | 1261〜1344 ms | 704〜755 ms |
| API 呼び出し（待機中の worker 1台あたり） | 約1.0回/秒 | 約1.5〜1.75回/秒 |

## 測っていないこと

- AWS 本番（Linux、Elan プロキシ、TLS）での値。Elan 経路は単体テストで模擬し、実機の値は pals-agent#24 の測定（1.18秒の短縮）を参照しています。
- 2026-11-02 の本番計測では、1回の待ちが Lean 検証時間より1.6〜2.1秒長くなっていました。ポーリングの遅れ（約0.65秒）はその一部です。残りは import から API の反映までの区間で、未測定です。
- 1回の呼び出しが新規プロセスで約0.35秒かかるため、間隔を詰めても0.35秒付近で頭打ちになります。それ以上は、API 側で `worker-input` が状態変化まで待つ長いポーリングが必要です。pals-api の統合先は `main` ではなく `codex/initial-aurora-bootstrap` で、internal ルートの信頼境界に触るため、今回は実装していません。
- 受理された検証では、コンパイルと監査の両方が `import Mathlib` を読み込み、検証時間の約半分を占めます。監査の import を減らせるかは未検討です。

## 有効化の手順（未実施）

1. pals-agent#75 を main にマージし、親リポジトリの参照を更新して verifier イメージを作る。
2. リリース手順の step 2 で作る verifier の環境（Git 管理外）に `PALS_LEAN_REUSE_LAKE_ENVIRONMENT=true` を入れる。
3. 起動ログの `lean_environment_reuse status=miss` と、以降の `environment_cache=hit` を確認する。`fallback` なら効いていない。
4. 本番で短縮を確認してから、コードの既定値を `true` にするか判断する。戻すときは `false` にして再起動する。
