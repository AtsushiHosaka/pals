# 図付き回答の実PostgreSQL保存・HTTP再取得確認（2026-11-18）

[#318](https://github.com/AtsushiHosaka/pals/issues/318)の追加検証です。
担当は[このCodexチャット](codex://threads/01a1ed09-2b3d-76c3-91c4-92efa30bdecc)です。
対象は[API #129](https://github.com/AtsushiHosaka/pals-api/pull/129)の
`50a35c2b527f7a696ccf3d3ca98cbfd5f6399113`にある
`tests/integration/test_figure_persistence.py`です。
API #129は`d837a647dc2de8b6004f3ff7e5e1f85ce9e6fb5c`へマージ済みで、
マージ後の同じrevisionに対する必須CIも成功しました。

## 確認した範囲

既存のローカルPostgreSQLを再利用し、この試行専用のDBを作成して実行しました。
認証済み利用者とゲストのそれぞれで、ロルの定理に関する三次多項式の微分図と、
中心Oを明示した円周角の図を扱う4ケースです。図と段落の対応情報を含め、
実repositoryの要求作成・claim取得・回答確定を通しました。

回答確定後は、別の接続からJSONBの保存内容を確認しました。
同じclaimによる回答確定の再実行で結果が変わらないことも確認しています。
さらに、新しいapplicationとTestClientを2回作り直し、公開HTTP経路で再取得しました。
認証済み利用者は単体GETとチャット履歴GET、ゲストはcookie付きGETを検査しています。
図、段落との対応情報、本文を保持し、別の認証主体やcookieでは404になることを確認しました。

| ケース | 保存・再取得・所有者分離 |
| --- | --- |
| 認証済み・三次多項式の微分図 | 成功 |
| 認証済み・円周角 | 成功 |
| ゲスト・三次多項式の微分図 | 成功 |
| ゲスト・円周角 | 成功 |

実行対象は収集時も実行時も4件で、pytestは終了コード0、skipは0件でした。
タイムアウトは発生していません。要求作成から再取得までを1ケースと数え、
再取得2回や所有者分離の各検査を別の試行数へ加算していません。

## 原本と実行後の状態

最初の集計器は、quiet出力の4個の成功記号に数値の集計行がないため、
試行結果を誤って失敗と判定しました。原本を保持したまま、収集件数4、
成功記号4個、終了コード0を照合して判定を補正しました。
この集計器の誤判定を製品の失敗へ算入せず、確認のための再実行もしていません。

前後比較では、既存DB一覧5件、roleの属性32件、membership6件が一致しました。
専用テストDBは削除済みです。既存のサービス、共有roleの属性・membershipは変更していません。

原本はGitに含めず、ローカルの`/private/tmp/pals-318-realpg/`に保持しています。

| 原本 | SHA-256 |
| --- | --- |
| `pytest.log` | `f3def2cfda78a3b80c2ab3b37275bb6a6e17ed1d3709842889fc8baa75bcbacf` |
| `result.json`（補正前の集計） | `1832c78f06ddf611fa175e7f47d8c027feb7e22f54a8f6c73ed0346153bfb927` |
| `result-verified.json` | `b4e1b4b229037a4cd3b2cf35dee58d05f4050ab2b0bacd1c400a5231f34438ee` |

## この検証で確かめていないこと

回答本文と図、生成・審査の入力は、検査用に固定したデータです。
認証主体の検査には既存の`FakeTokenVerifier`を使っています。
repository、PostgreSQLの保存・claim・再実行、HTTP経路と公開serializerは実装を通していますが、
実モデルの生成・独立審査、Lean compiler、Cognito、外部queueは実行していません。
`reviewed_explanation`を扱い、LeanのPASSや`lean_verified`の回答は作っていません。

これは回答JSONの永続化とHTTP再取得の確認です。実ブラウザの描画や操作、
`proof_explanations`を経由する検証済み証明の全工程、現在の本番カタログとの対応を証明しません。
モデル呼出しや新しい本番質問はなく、費用・回答時間・数学一般の成功率は測定していません。

本番の図表示・保存・再読み込みの受け入れは引き続き`NOT VERIFIED`です。
[#433](https://github.com/AtsushiHosaka/pals/issues/433)の復旧と
[#425](https://github.com/AtsushiHosaka/pals/issues/425)の正規リリースを担当するチャットが、
本番の同じ要求を追って確認します。#318はその結果が出るまで閉じません。

品質台帳の行IDは`2026-11-18-figure-postgres-public-readback`です。
