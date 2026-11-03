# Proof Quality Observability Design

Status: WORKING proposal. 要件は [requirements.md](requirements.md)、作業は [tasks.md](tasks.md) にある。調査した版は pals-agent `3477695`、pals-api `8bb38aa`、pals-infra `d70b125`（いずれも main）。この文書は実装、`terraform apply`、本番配備を承認しない。

## 現状（調査で確認した事実）

AWS の認証情報がなかったため、AWS 上の実在は確認していない。以下は Terraform とコードの記述による。

### CloudWatch とインフラ（pals-infra）

- `terraform/production/` は単一の flat なルートモジュールである。CloudWatch 関連は次の3つだけである。
  - `aws_cloudwatch_log_group.host`（`/pals/<env>/host`、保持30日）。ホストの IAM ロールに `logs:*` の許可がなく、CloudWatch エージェントの導入もないため、書き込む主体が見当たらない。
  - Aurora の `enabled_cloudwatch_logs_exports = ["postgresql"]`。
  - `aws_budgets_budget.monthly_cost`（月100 USD、実績が20・50・100 USD を超えたときにメール）。
- メトリクスフィルター、アラーム、ダッシュボード、SNS トピックは Terraform にない。
- 別系統として、`cloud/machine-auth-monitor/provision.py` が CloudFormation スタックを作る。Lambda が名前空間 `PALS/MachineAuth` にメトリクスを出し、9個のアラームを持ち、SNS トピック `pals-macmini-auth-alerts` を使う。これは Mac mini 時代の Roles Anywhere 監視であり、serving の Terraform とは別管理である。この仕様は触らない（PQO-025）。
- ホストの Docker ログドライバは `local`（10 MB × 3 ファイル）で、コンテナのログはホストの外へ出ていない。
- IAM:
  - ホストのロール `pals-<env>-host` は、SSM のコア権限と、SSM パラメータの読み取り、ECR の pull、SQS、S3、KMS の検証などに限られる。`cloudwatch:PutMetricData` も `logs:*` もない。
  - ワーカーのロール `pals-<env>-worker` は、SQS の受信、`s3:PutObject` だけで、それ以外を持たないことを `production.tftest.hcl` の PFI-AG-006 が検査している。
  - `PutMetricData` を持つのは、machine-auth モニターの Lambda ロール（名前空間を条件で限定）だけである。
- SQS には `proof-jobs`（可視性タイムアウト900秒）と DLQ `proof-jobs-dlq`（`maxReceiveCount = 3`）がある。AWS ネイティブのキューメトリクスは、追加の仕組みなしで使える。
- ホストの user data を変えると、`user_data_replace_on_change = true` によりインスタンスが置き換わる。

### ログとコード（pals-agent、pals-api）

- ワーカー（`proof_request_worker.py`）は、要求の確定後に `proof_request_settled request_id=… status=… assessment_phase=… error_code=… review_approved=…` を出す。`error_code` は許可リスト `_RESULT_ERROR_CODES` にあるものだけで、それ以外は `unrecognized` に置き換える。例外メッセージは出さない。
- 段階別の時間計測 `latency_stage`（pals#149）は `runtime_latency.py` にあり、JSON の `proof_request_latency` イベントを stderr に1行出す。要求 ID は正規形の UUID の SHA-256 で相関する。
- API のログは `%(asctime)s %(levelname)s %(name)s %(message)s` の平文で stdout に出る（`app/core/logging.py`）。検証器は `%(message)s` だけの形式である。
- 失敗の語彙は4か所にある。
  - 要求レベル（`proof_requests.error_code`）: `proof_reuse_*`、`material_*`、`token_budget_exceeded`、`token_usage_unknown`、`proof_request_delivery_exhausted`、`lean_flow_unavailable`、`lean_verification_required`、`lean_verification_failed`、`lean_explanation_failed` など。
  - Lean 試行の診断コード（`pals_agent/lean.py` など）: `lean.compile_error`、`lean.unsolved_goals`、`lean.type_mismatch`、`lean.tactic_failed`、`lean.syntax_error`、`lean.unknown_identifier`、`lean.declaration_uses_sorry`、`lean.disallowed_*`、`lean.timeout`、`lean.output_limit`、`lean.statement_mismatch`、`lean.trusted_audit_failed`、`lean.sandbox_setup_failed`、`lean.project_not_found`、`lean.prlimit_not_found`、`lean.verifier_timeout`、`lean.compile_interrupted`、`lean.compile_deadline_interrupted` など。
  - 検証候補のジョブ（`proof_verification_candidates.failure_code`）: `verifier_not_ready`、`verifier_unavailable`、`verifier_timeout`、`verifier_transport_failed`、`verifier_request_invalid`、`verifier_release_binding_mismatch`、`verifier_compile_failed`、`semantic_target_invalid`、`semantic_review_failed`、`semantic_review_unavailable`、`sqs_send_failed`、`dispatch_outcome_uncertain` など。
  - ゲストの拒否: `guest_quota_exhausted`、`guest_session_rate_limited`、`guest_global_daily_limit`。
- Lean ジョブの終端は API 側で確定する（`proof_request_lean.py`）。失敗時は `status='failed'`、`error_code='lean_verification_failed'` とし、同時に詳細な失敗コードは上のジョブ表に残る。
- Langfuse は、本番の実行経路にない。`pals-observability` が評価履歴（JSONL）を明示的に Langfuse へ書き出す。`pals-scripts/fetch/langfuse-traces.sh` は手元で読むだけである。
- 評価は `pals_agent/evaluation.py` の `EvaluationRun`（ステージごとのメトリクス）として、ローカルの JSONL に追記される。

## Decisions

### D1 メトリクスの作り方

3案の比較:

| | EMF | メトリクスフィルター | `PutMetricData` |
|---|---|---|---|
| 発行側の権限 | ログの書き込みだけ | ログの書き込みだけ | `cloudwatch:PutMetricData`（ワーカーのロールは固定） |
| ディメンション | 自由（イベントごとに複数の組） | 平文では不可。JSON ログで最大3つ。コードごとにフィルターが要る | 自由 |
| 分類の追加 | アプリ側の語彙を足すだけ | Terraform のフィルターを足す | アプリ側の語彙を足すだけ |
| 詳細の記録 | 同じイベントがログに残り、Logs Insights で引ける | ログが別途必要 | 詳細は残らない |
| 要求経路への影響 | ローカルへの書き出しだけ | ローカルへの書き出しだけ | 同期のネットワーク呼び出し。失敗時の扱いが要る |
| 注意点 | 1行が有効な EMF でなければ抽出されない。過去2週間・未来2時間の時刻のみ | 既存の平文ログの形に依存する | 1回 1,000件まで。呼び出しごとの費用 |

決定: **EMF** を採る。ワーカーのロールを広げず、要求から取り出した許可リストの項目だけを1つのイベントにして、メトリクスと詳細ログを同時に得られる。メトリクスフィルターは、既存の平文ログに後から足す補助にとどめ、この仕様では使わない。

### D2 イベントの運び方

要件は運び方に依存しない（PQO-010）。候補は3つある。

| 案 | 内容 | 長所 | 短所 |
|---|---|---|---|
| T1 | コンテナから、ホストの CloudWatch エージェントの EMF 受信口（UDP/TCP）へ送る | 送るのは品質イベントだけ。ファイルとローテーションが要らない | エージェントの導入と、ブリッジネットワークからの到達設定が要る。設定は未確認 |
| T2 | コンテナが専用ファイルに書き、エージェントが追う | 送るのは品質イベントだけ。書き込みが同期的でない | 読み取り専用のコンテナにマウントが要る。ローテーションが要る |
| T3 | stdout を Docker の `awslogs` ドライバで送る | 設定が最小 | **全アプリログがホストの外へ出る**。PQO-010 を満たすには、全ロガーの監査が要る |

決定: 候補は **T1 を第一、T2 を代替** とする。T3 は PQO-010 に反するため採らない。ただし T1・T2 とも、EMF の抽出が実際に動くことを、使い捨てのロググループで確かめてから確定する（tasks の PQO-T006）。確かめるまで、本番ホストの設定は変えない。

どの案でも、ホストのロールに必要な権限は、専用ロググループへの `logs:CreateLogStream` と `logs:PutLogEvents` だけである。`PutMetricData` は要らない。

### D3 アプリ側のフック

共通部品: 品質イベントの組み立て、許可リスト、禁止項目の検査、運び方の抽象（エージェント、ファイル、無効化）を持つ小さなモジュール。pals-agent に `pals_agent/quality_events.py`、pals-api には同じ契約の薄い実装を置く。両者の契約は、同じイベントのスキーマ（JSON Schema）を、各リポジトリのテストで共有する。

| フック | 場所 | 出すもの |
|---|---|---|
| 要求の終端（ワーカー） | `ProofRequestProcessor.process` の、`settle_proof_request` が受理された後（`proof_request_settled` を出す箇所）。再配信で `claim["status"] == "terminal"` を見つけた分岐では出さない | `ProofRequestsSettled`、`ProofRequestsSucceeded`、`ProofRequestsFailed`、`ProofRequestsRefused` |
| 要求の終端（Lean ジョブ） | pals-api `proof_request_lean.py` の、`status` を `answered` か `failed` へ更新する分岐。遷移した場合だけ出す（`return False` の経路では出さない） | 同上。失敗コードは、ジョブ表の `failure_code` と、最後の Lean 診断コードから分類する |
| ゲストの拒否 | pals-api のゲストの制限判定（3種のコード）の箇所 | `ProofRequestsRefused` |
| Lean の試行 | pals-agent の Lean コンパイル結果を受ける箇所（`lean.py`、`pipeline.py` の試行ループ）。検証器側の失敗（`http_server.py`）も含める | `LeanAttempts`、`LeanAttemptsFailed`、`LeanVerifyDurationMs`。診断コードは、ログの項目 `diagnostic_code` にだけ置く |
| ハートビート | `worker.py` のメインループ。5分ごと | `WorkerHeartbeat`、`QualityEventsDropped` |
| 評価の実行 | #216 の台帳への追記関数（`EvaluationRun` の保存の直後） | `EvalSuccessRate` ほか |

重複の扱い: 同一要求の終端は、ワーカーと API のどちらか一方だけが確定する（`formal` の要求は、ワーカーが `verifying` を確定し、終端は API が確定する。ワーカーは `verifying` では `ProofRequestsSettled` を出さない）。発行はコミット後の最善努力であり、プロセスが発行前に落ちると1件欠ける。これは件数のずれとして許容する。

### D4 分類とメトリクスの対応

分類の正本は #216 の `docs/quality-ledger/taxonomy.md` である。その文書が main にない間は、次の暫定の分類を使う。分類が確定したら、正本の識別子に合わせてこの表を更新する（PQO-004）。

| `FailureClass`（暫定） | 意味 | 暫定の対応コード | アラーム |
|---|---|---|---|
| `infra` | 基盤の失敗 | `proof_request_delivery_exhausted`、`proof_reuse_provider_unavailable`、`proof_reuse_recipe_unavailable`、`proof_reuse_catalog_invalid`、`proof_reuse_token_accounting_failed`、`token_usage_unknown`、`material_context_unavailable`、`lean_flow_unavailable`、`sqs_send_failed`、`dispatch_outcome_uncertain`、`proof_reuse_deadline` | 件数 |
| `verifier` | 検証器の失敗 | `verifier_not_ready`、`verifier_unavailable`、`verifier_timeout`、`verifier_transport_failed`、`verifier_request_invalid`、`verifier_release_binding_mismatch`、`lean.verifier_timeout`、`lean.sandbox_setup_failed`、`lean.project_not_found`、`lean.prlimit_not_found`、`lean.trusted_audit_failed`（暫定） | 件数 |
| `proof` | モデルが証明を書けなかった失敗 | `lean.compile_error`、`lean.unsolved_goals`、`lean.type_mismatch`、`lean.tactic_failed`、`lean.syntax_error`、`lean.unknown_identifier`、`lean.declaration_uses_sorry`、`lean.disallowed_*`、`lean.timeout`、`lean.output_limit`、`lean.statement_mismatch`、`lean.already_declared`、`verifier_compile_failed`、`lean_verification_failed`、`proof_reuse_invalid_response`、`proof_reuse_invalid_instantiation`、`proof_reuse_invalid_source`、`proof_reuse_recipe_invalid` | 率 |
| `review_rejected` | 審査の却下 | `semantic_review_failed`、`semantic_target_invalid`、`proof_reuse_answer_review_failed`、`lean_explanation_failed` | 率 |
| `policy_refusal` | 正規の拒否 | `guest_quota_exhausted`、`guest_session_rate_limited`、`guest_global_daily_limit`、`token_budget_exceeded`、`proof_reuse_unsupported`、`lean_verification_required`、`material_*` の入力不備 | なし |
| `unclassified` | 対応表にないコード | 上のいずれにも載らないもの | 件数（PQO-015） |

判断が分かれるコードを、#216 で確定させる:

- `lean.trusted_audit_failed` は、監査の成果物をコンパイルできないか、完了しないときに出る（`lean.py` の3か所）。検証器の不具合のほかに、候補が早期終了して監査を妨げた場合もありうる。暫定で `verifier` とし、誤検知が多ければ `proof` へ移す。
- `lean.timeout` は、候補が重い場合に出るため `proof` とした。検証器が遅い場合と区別できないときは、`lean.verifier_timeout` との差で判断する。
- `token_budget_exceeded` と `proof_reuse_unsupported` は、失敗ではなく利用上の制限として `policy_refusal` に置いた。
- `lean_verification_failed` は API の集約コードであり、詳細は `failure_code` と最後の診断コードにある。集約コードのままなら `proof` とし、詳細が取れる場合はその分類を優先する。

メトリクスの一覧（名前空間 `PALS/ProofQuality`）:

| メトリクス | 単位 | ディメンションの組 | 数（期待 / 上限） |
|---|---|---|---|
| `ProofRequestsSettled` | Count | `[Environment]`、`[Environment, Route]` | 3 / 5 |
| `ProofRequestsSucceeded` | Count | 同上 | 3 / 5 |
| `ProofRequestsFailed` | Count | `[Environment, FailureClass]`、`[Environment, FailureCode]` | 20 / 51 |
| `ProofRequestsRefused` | Count | `[Environment, FailureCode]` | 3 / 8 |
| `LeanAttempts` | Count | `[Environment]` | 1 / 1 |
| `LeanAttemptsFailed` | Count | `[Environment, FailureClass]` | 4 / 6 |
| `LeanVerifyDurationMs` | Milliseconds | `[Environment]` | 1 / 1 |
| `WorkerHeartbeat` | Count | `[Environment]` | 1 / 1 |
| `QualityEventsDropped` | Count | `[Environment]` | 1 / 1 |
| `EvalSuccessRate` | Percent | `[Suite, ModelConfig]` | 8 / 12 |
| `EvalCases` | Count | `[Suite, ModelConfig]` | 8 / 12 |
| `EvalFailed` | Count | `[Suite, FailureClass]` | 8 / 24 |
| 合計 | | | 約60 / 約127 |

`Route` の値（暫定）: `catalog_recipe`、`semantic_reuse`、`lean_generation`、`chat_answer`。`ModelConfig` は、モデル構成の登録名（モデル、推論量、Recipe 設定を表す非秘密の識別子）で、#216 の台帳の「構成」欄と同じ値にする。上限が150を超えそうなときの縮小順は、`FailureCode` の組、`Route` の組、評価の `EvalFailed`、の順とする（詳細はログに残るため、情報は失われない）。

ログの項目（EMF の `_aws` 以外）: `event`（`proof_request_terminal`、`lean_attempt`、`worker_heartbeat`、`eval_run`）、`request_hash`、`revision`、`route`、`model_config`、`failure_class`、`failure_code`、`diagnostic_code`、`attempts`、`repairs_used`、`duration_ms`、`suite`、`ledger_id`、`cases`、`succeeded`、`cost_usd`。メッセージ本文、診断メッセージ、利用者に関わる項目は持たない。

### D5 アラームの根拠

| アラーム | しきい値の根拠 |
|---|---|
| 検証器の失敗（1件、1/3） | 検証器の失敗は利用者の誤りではなく、1件でも再現の可能性がある。トラフィックが少なく、率では検出できない。 |
| インフラの失敗（1件、2/3） | 一過性の DB やネットワークの揺れで1件出ても通常は直る。2期間（10〜15分）続いたときだけ警報にする。 |
| ジョブキューの滞留（900秒） | 可視性タイムアウトと同じ。これを超えると、配信がやり直されるか、ワーカーが止まっている。 |
| DLQ（1件） | 3回配信されて処理されなかったメッセージであり、必ず調べる。 |
| ホスト（`StatusCheckFailed`） | 単一ホスト構成のため、ホストの停止がそのままサービス停止になる。 |
| モデルの証明失敗率（60%、最小10件） | モデルの失敗は難問で通常起きる。警報にするのは、品質が崩れたとき（モデル、Recipe、プロンプトの退行）だけにする。初期値は根拠となる実測がなく、配備から14日で `実測の p95 × 1.5` を目安に置き換える。 |
| 審査の却下率（30%、最小10件） | 却下が増えるのは、審査器か生成器の変化の兆候である。初期値は暫定。 |
| ハートビート（15分欠測） | 5分ごとのイベントが3期間途絶えたら、ワーカーの停止かログ経路の停止である。欠測を異常（`breaching`）として扱う。 |
| `unclassified`（1件、1時間） | 新しいコードが分類されずに出ている。分類表の更新漏れを検出する。 |

率のアラームは、メトリクス計算 `IF(total >= 10, 100 * failed / total, 0)` で最小サンプルを守る。`alarm_actions` は空で作る（PQO-016）。

評価の退行（`EvalSuccessRate` が台帳のベースラインを下回る）のアラームは、台帳に基準値ができてから追加する。この仕様の初期スコープには含めない。

### D6 Terraform とホストの IAM

`pals-infra` の既存の構成に合わせ、`terraform/production/` に次のファイルを足す（モジュールには分けない）。

| ファイル | 内容 |
|---|---|
| `observability_logs.tf` | `aws_cloudwatch_log_group.quality_events`（`/pals/<env>/quality-events`）。保持期間は変数 `quality_log_retention_days`（既定30） |
| `observability_alarms.tf` | `aws_cloudwatch_metric_alarm`（D5 の9本。キューと EC2 は AWS ネイティブのメトリクス） |
| `observability_dashboard.tf`、`templates/proof-quality-dashboard.json.tftpl` | `aws_cloudwatch_dashboard.proof_quality` |
| `observability_reader.tf` | 読み取り用の IAM ロールとポリシー（D7） |
| `iam.tf` | ホストのロールに、専用ロググループへの `logs:CreateLogStream`、`logs:PutLogEvents` を追加 |
| `variables.tf` | `quality_log_retention_days`、`observability_alarm_actions`（既定 `[]`）、`observability_reader_principal_arns`（既定 `[]`） |
| `templates/host-user-data.sh.tftpl` | CloudWatch エージェントの導入と設定（D2 の確定後）。**この変更はホストの置き換えを伴う** |
| `tests/production.tftest.hcl` | 新しい `run`: ワーカーのロールが不変であること、ホストの `logs:*` が専用ロググループに限られること、アラームの `alarm_actions` が空であること、読み取りロールの許可が一覧どおりであること |

ワーカーのロールには触れない。`tests/production-cost-boundary.sh` の禁止リソース（ALB、ECS、NAT、VPC エンドポイント、SSM パラメータ）にも該当しない。ただし CloudWatch エージェントの設定を SSM パラメータに置く案は、`aws_ssm_parameter` の禁止に触れるため採らない。

### D7 読み取りの経路

外部の読み取り機能は ChatGPT の dot である。確認できているのは第三者の記事の範囲に限り、AWS へのコネクタ、MCP やカスタムコネクタ、API、ポーリング間隔は確認できていない（[Open questions](#open-questions)）。3案を比べる。

| 案 | 内容 | 必要な権限 | 長所 | 短所 |
|---|---|---|---|---|
| (a) 既存のプラグイン | dot が、CloudWatch を読める既存の ChatGPT プラグインで読む | プラグインが要求する権限（未確認） | AWS 側の作業がほぼ要らない | プラグインの存在と、行為単位の絞り込みが未確認。存在しても、権限が広い可能性がある |
| (b) コンソールを読む | dot が、クラウドのブラウザから、読み取り専用の主体で AWS コンソールにログインし、CloudWatch のダッシュボードを読む | 本仕様の読み取りポリシー（カスタム。D7 の下に記載）をもつ IAM Identity Center の許可セット、または IAM ユーザー | AWS 側に新しい実行コードが要らない。確認できている dot の能力（ブラウザ、プライベートなログインフォーム、定期実行）だけで成り立つ | dot が AWS のログイン資格情報を保持する。MFA とセッション失効の扱いが未確認。コンソールの画面に依存して壊れやすい。IAM ユーザーなら長期の資格情報になる |
| (c) 要約を書き出す | EventBridge の定期実行で Lambda が CloudWatch を読み、日次・時間単位の JSON と Markdown の要約を S3 に置く。dot はそれを読む | 要約を読むための S3 の1オブジェクトか、署名付き URL。CloudWatch への権限は Lambda だけが持つ | dot に与える権限が最小。内容は集計値だけで、ログ本体に触れない。dot が AWS を操作できなくてもよい | Lambda、S3、スケジュールが増える。署名付き URL は有効期限が短く、dot に安定した URL を渡せない（認可つきの配布経路が未確認）。費用と保守が増える |

決定: 次の順で進める。

1. (a) の有無を、費用なしで確認する（PQO-T010）。あり、かつ権限を読み取り専用に絞れるなら採る。
2. なければ **(b)** を初期の推奨とする。ただし資格情報を最小にするため、IAM Identity Center の許可セット（セッション時間を短く）を優先し、使えなければ、コンソールのログインだけを許すカスタムポリシーの IAM ユーザーとする。いずれも `ReadOnlyAccess` は使わない。
3. dot がコンソールを安定して読めない、または資格情報の失効・監査の扱いが受け入れられないときは、**(c)** に移す。(c) は初期スコープに含めず、必要になった時点で別の仕様として追加する。

読み取りポリシー（(b) の本体。(a)(c) でも、必要な許可の上限として使う）:

- `cloudwatch:GetMetricData`、`GetMetricStatistics`、`ListMetrics`、`DescribeAlarms`、`DescribeAlarmHistory`、`GetDashboard`、`ListDashboards`。
- `logs:StartQuery`、`GetQueryResults`、`StopQuery`、`DescribeLogGroups`（リソースは `/pals/<env>/quality-events` のロググループに限る）。
- コンソールの表示に必要な最小限の `cloudwatch:Describe*`、`List*`。`logs:GetLogEvents` と `FilterLogEvents` は、必要が確認できるまで許可しない。

信頼ポリシーは、変数 `observability_reader_principal_arns` の主体だけを許し、外部 ID を条件にし、セッションは1時間以内とする。IAM Identity Center を使う場合は、許可セットとして Terraform の外で管理する可能性があり、その扱いを未確認事項に置く。

### D8 Langfuse と #216 の台帳との関係

- Langfuse は本番の実行経路に入れず、この仕様でも入れない。`pals-observability` による評価履歴の書き出しは、そのまま残る。要求の相関は、`request_hash` が Langfuse 側のトレースを引くときの手がかりになりうるが、紐づけは行わない。
- 台帳（#216）は、長期の正本である。CloudWatch は、運用の監視と直近の推移を担う。評価イベントは、台帳への追記と同じ関数から出す（PQO-017）。台帳の行 ID をイベントに入れ、CloudWatch の点から台帳へ戻れるようにする。
- 分類は #216 の `taxonomy.md` が正本であり、この仕様の対応表は、それに合わせて更新される従属物である。両者が食い違った場合は、#216 に従う。

### D9 ダッシュボードの配置

ダッシュボード `pals-<env>-proof-quality`、リージョン `ap-northeast-1`、メトリクス50以下（無料枠）。

| 段 | ウィジェット |
|---|---|
| 1 | アラームの状態（全アラーム）、24時間の成功率（数値）、24時間の失敗数（分類別の数値） |
| 2 | 分類別の失敗数（積み上げ。`SEARCH` で `FailureClass`）、成功率の推移（1時間） |
| 3 | 失敗コードの上位10（積み上げ。`SEARCH` で `FailureCode`）、Lean 試行の失敗の分類別 |
| 4 | 正規の拒否（`policy_refusal`）の件数、Lean 検証時間の p50 と p95 |
| 5 | 精度: `Suite` × `ModelConfig` ごとの `EvalSuccessRate`（折れ線）、`EvalFailed` の分類別（積み上げ） |
| 6 | 基盤: ジョブキューの滞留と DLQ、EC2 のステータス、ハートビート、`QualityEventsDropped` |
| 7 | ログ: 直近の失敗イベント20件（Logs Insights。コードと分類だけ） |

### D10 費用の縮小手順

月の実測が上限を超えそうなときは、メトリクスの数を減らす。順序は D4 の末尾に従う。ログの量は費用に効かないため、減らさない。

## Test strategy

- 単体: 全コードの対応の完全性（語彙から対応表へ。対応表にないコードは `unclassified`）、EMF のスキーマ、許可リスト外の値が `unrecognized` になること、禁止項目の検査（質問本文、Lean ソース、利用者識別子のダミー文字列を流し、イベントのどこにも出ないこと）、再配信で二重に出さないこと、発行先が使えなくても要求が成功すること。
- 統合（ローカル）: 要求の終端、Lean の試行、評価の実行から、期待した件数のイベントが出ること。LocalStack は EMF の抽出を再現しないため、ここでは出力の形だけを検査する。
- AWS（使い捨て、オーナー承認）: `Environment=probe` のイベントで EMF の抽出を確かめる（PQO-T006）。アラームは、`cloud/machine-auth-monitor/acceptance.py` と同じ方針で、本番と同じ比較・しきい値・欠測の扱いをもつ一時アラームを、短い期間で作り、`SetAlarmState` を使わずに、実際のイベントで `ALARM` と `OK` を確かめ、後で削除する。
- 本番（オーナー承認後）: 配備後に、分類ごとの擬似失敗を1件ずつ `Environment=probe` で発行し、実測を記録する。本番のメトリクスと本番のアラームを汚さない。

## ロールアウトと危険

1. アプリ側（イベントの発行。運び方は無効）を先に配備する。ホストの設定は変わらない。
2. ホストへのエージェント導入は user data の変更を伴い、ホストが置き換わる。配備の時期と手順はオーナーの承認で決める。
3. `terraform apply` は、新規リソースの作成だけを示す `plan` をオーナーが確認してから行う。

## Open questions

1. **dot の資格情報の扱い**: dot が AWS のログイン情報（または署名付き URL、API キーなど）をどこに保持するか。プライベートなフォームに入れた値の保存場所、暗号化、削除の手段。
2. **失効時の挙動**: Identity Center のセッション切れや、IAM ユーザーのパスワード変更・MFA 要求のとき、dot の定期実行は失敗として見えるのか、黙って止まるのか。再認証を誰が行うか。
3. **監査**: dot の読み取りを、AWS 側（CloudTrail、Identity Center のサインインログ）と dot 側（実行履歴「Scheduled」）のどちらで追えるか。
4. **dot が使える経路**: AWS への直接のコネクタ、CloudWatch のプラグイン、MCP やカスタムコネクタ、API の有無（第三者の記事には書かれていない）。ポーリングの間隔と、イベントでの起動が使えるか。dot が使えるプラン。
5. **読む内容**: dot に何を読ませたいか（アラームの状態だけか、ダッシュボードの数値か、ログのクエリ結果か）。これにより、(b) のポリシーを `logs:StartQuery` 抜きに狭められる。
6. **分類**: #216 の分類との差、特に `lean.trusted_audit_failed`、`lean.timeout`、`token_budget_exceeded`、`proof_reuse_unsupported` の扱い。
7. **保持期間**: 品質イベントのログを30日（暫定）とするか、90日にするか。メトリクスは15か月で固定である。
8. **アラームの動作**: 当面なしのままでよいか。将来 SNS を足すとき、Mac mini 時代の `pals-macmini-auth-alerts` を使い回さず、新しく作るか。このトピックと machine-auth モニターは、Mac mini が使われなくなった今も残してよいか。
9. **ホストの置き換え**: エージェント導入によるホスト置き換えの許容と、時期、手順（リリースの窓）。
10. **費用の上限**: 月の上限を、見積もりの約20 USD（上限44 USD）のままでよいか。AWS Budgets に、CloudWatch 専用の予算を足すか。
11. **環境**: 本番以外に、注入テストを行える環境があるか。なければ `Environment=probe` と一時アラームで行う前提でよいか。
12. **精度の定義**: どの評価（`Suite`）を成功率の対象にするか、成功の定義（Lean の検証通過か、審査の通過までか）。#216 と合わせる。
13. **運び方**: D2 の T1 が使えるか（エージェントの EMF 受信口と、ブリッジネットワークからの到達）。使えなければ T2 にする。
