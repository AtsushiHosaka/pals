# 問題の蓄積とプロンプトの反復評価

問題一覧は[初回の登録](prompt-quality-problems-2026-11-09.md)、進行は[Issue #316](https://github.com/AtsushiHosaka/pals/issues/316)に記録します。ここでは、問題の追加から比較までの手順を示します。コマンドは親リポジトリから実行します。秘密や生成回答を含む作業ファイルは、コミットしないローカルの出力ディレクトリに保存します。

## 問題を追加する

作成した評価問題は、参考解答を点検してからデータセットに追加します。既存の問題を修正するときは新しいIDを付けます。既存のIDで問題文や参考解答を変更すると、レジストリの検証は失敗します。一般の利用者の非公開の質問を、作成した評価問題として公開したり、今回の承認で外部採点に送ったりしません。

```bash
PYTHONPATH=pals-observability/src pals-observability/.venv/bin/python \
  -m pals_observability.prompt_quality_registry \
  --registry pals-observability/datasets/benchmark-problems-ja-v1.json \
  --dataset pals-observability/datasets/undergraduate-regression-ja-v3.json
```

新しい問題を登録するときは、同じコマンドに`--register-case 問題ID --dataset-commit 完全なコミットID --topic-group 分野ID --split regression`を追加します。データセットを保存した正確なコミットを指定します。今後用意する検証用問題は、調整前に`prospective_holdout`として分離し、関連する問題を同じ側にまとめます。結果を見て調整に使ったら、その問題は以後の未知の検証には使いません。

観測は内容を含まないJSONにし、`--append 観測ファイル.json`で追記します。形式は初回レジストリの`episodes`を参照します。採点の低さだけなら`observation.score_hint`とし、確認した説明上の指摘や数学的誤りと分けます。回復や再採点では、元の観測IDと同じ試行IDを指定します。変更前の観測は削除しません。

## 説明プロンプトを比較する

実行前に、問題、参考解答、検証済みLeanソース、元の正式な評価記録、実装ソースをマニフェストに固定します。Leanファイルのハッシュが、元の検証記録と一致しない場合は実行できません。プロンプトの候補は版付きのポリシーファイルで指定できます。基準条件の追加指示は空とし、候補条件だけに一般的な説明方針を追加します。参考解答は採点だけに使います。

```bash
PYTHONPATH=pals-observability/src:/固定したagentソースのルート \
  pals-agent/.venv/bin/python -m pals_observability.prompt_quality_replay \
  --manifest /非公開の作業場所/replay-manifest.json \
  --agent-source-root /固定したagentソースのルート \
  --api-source-root /固定したAPIソースのルート \
  --journal /非公開の作業場所/replay-journal.jsonl \
  --output-dir /非公開の作業場所/空の既存ディレクトリ \
  --namespace replay-20261109-pilot1 \
  --judge-model gpt-5.4-2026-03-05 \
  --judge-revision gpt-5.4-2026-03-05 \
  --repetitions 2 --timeout-seconds 360 \
  --total-timeout-seconds 4200 --maximum-calls 16 --environment prod
```

認証は通常のモデル用環境変数から読みます。環境ファイル全体を読み込んだり、認証情報をコマンドや出力に表示したりしません。この説明段階の実験は、PALSへの再ログインや新しい証明リクエストを必要としません。外部呼び出しの結果が不明な場合は自動再送せず、その試行を欠測として残します。実行途中の条件変更も拒否します。

実行は本番と同じ生成・構文検証・公開レビュー・修正ループを使います。両条件を新しく生成し、同じAPIの本文への変換を通して採点します。`baseline.json`と`candidate.json`は内容を含まない測定値、`evidence.json`は条件と対象範囲の記録です。新しいLean検証や、本番へのプロンプト反映を表すものではありません。

## CloudWatchの結果を比較する

[既存の運用手順](prompt-quality-operations.md)の`publish`で両方の測定記録を保存し、同一内容の読み戻しを確認します。`fetch`で取得したJSONLを、次の比較に使います。送達が不明な書き込みは、取得を確かめてから判断します。

```json
{
  "schema_version": "pals.prompt-quality.trend-manifest.v1",
  "iterations": [
    {
      "iteration_id": "iteration-1",
      "label": "undergraduate-v2",
      "stage": "explanation_replay",
      "baseline_run_id": "replay-20261109-pilot1-baseline-v1",
      "candidate_run_id": "replay-20261109-pilot1-undergraduate-v2"
    }
  ]
}
```

ラベルと実行IDには、記録された英数字の識別子を使います。説明段階と証明全体の実験を分け、比較する順序を明示します。

```bash
PYTHONPATH=pals-observability/src pals-observability/.venv/bin/python \
  -m pals_observability.prompt_quality_trend \
  --runs /非公開の作業場所/cloudwatch.jsonl \
  --manifest /非公開の作業場所/iterations.json \
  --output /非公開の作業場所/trend.json \
  --csv /非公開の作業場所/trend.csv
```

問題、試行数、モデル、採点、取得元などが違えば比較を拒否します。条件の異なる実験を一本の改善曲線につなぎません。同じ条件でも、未採点や生成失敗を含む分母、問題単位のばらつき、悪化した問題を確認します。新しい反復では、同じマニフェストの末尾に比較を加えます。取得した値でグラフと品質台帳を更新し、変更したポリシーと根拠を一緒に保存します。


## 追加した証明問題の再評価

この追加時点の問題一覧は11題です。元の8題を保持し、新規3題を`undergraduate-regression-ja-v2.json`に追加しています。入力のLeanソースはobservabilityの`datasets/lean/`に置き、コンパイルの生出力はローカルに保存します。

新しい3題の説明比較は、`prompt_quality_replay`の代わりに`prompt_quality_local_replay`を使います。マニフェストに処理系の出典、各ソースと実コンパイル記録のハッシュ、対象定理を指定します。コマンドは実際に再コンパイルし、元と同じ生成・公開レビュー・採点へ進みます。環境はPATH、LEAN_PATH、LANG、LC_ALL、TMPDIRだけで、モデルの認証情報はコンパイラに渡しません。本番の証明記録を偽造しません。

次回も同じ追加問題集を比較するときは、今回作った`local-compile-authority.json`の原本を変更せず、次の空の出力ディレクトリへコピーして使います。入力や処理系、読み込み実装が一致すれば、実際の再コンパイルを経て同じ出典を再利用できます。一致しなければ拒否します。ハッシュや実行IDを編集して比較を成立させないでください。ソースや読み込み実装を変える場合は、別の比較系列として扱います。

## QA・表示処理を変える実装比較

Issue #319の比較は、両条件とも同じv4の生成指示を使い、QAの指示とAPIの結論追加だけを変更します。`pals_observability.prompt_quality_treatment`で、2条件のソース・固定した6題・モデル・採点器・反復数を契約に記録します。`--preflight-only`は実コンパイルと実factoryの条件を照合し、モデルは呼び出しません。

条件ごとに独立したプロセスとジャーナルを使います。実装が違うため実際の設定ハッシュも異なり、元のプロンプト比較器へ通すために書き換えません。取得した2記録は`compare_treatment_runs`で、許された変更と固定条件を照合して比較します。欠測や回答失敗を含む12組すべてを確認し、採点できた組の差だけで改善と判断しません。

[今回の結果](prompt-quality-qa-conclusion-fix-2026-11-09.md)に、CloudWatchの読み戻しハッシュ、改善・悪化・同点、問題ごとの差、採点器の不確かさを記録しました。本番反映には別のリリース検証が必要です。

## 修正済み実装で生成指示だけを変える

v5・v6以後の実験には`pals_observability.prompt_quality_policy_experiment`を使います。QA・APIを両側で同じ修正済み実装に固定し、識別子付きの非空の基準方針と候補方針を比較します。古い空の基準方針用ローダーや厳密比較器は変更しません。今回のデータセットはv3の14題で、元のv2の11題と履歴も保持しています。レジストリのデータセットのコミット・パス・内容SHAは、実際に登録した版へ合わせて点検します。

```bash
PYTHONPATH=pals-observability/src pals-agent/.venv/bin/python \
  -m pals_observability.prompt_quality_policy_experiment \
  --manifest /非公開の作業場所/experiment.json \
  --population fixed6 \
  --output-dir /非公開の作業場所/空の既存ディレクトリ \
  --preflight-only
```

実ソース、生成と修正時の指示、factory、APIの結論追加、Leanの出典を照合した後、最後のフラグを外すと明示した比較を実行します。問題・証明の内容を含まない一覧で、調整用と追加群の重複を拒否します。追加群の本文は調整時に読み込まず、候補を凍結してから専用ジャーナルと開封記録へ結び付けます。一度開いた追加群で候補を変更し、未知の検証に成功したとは扱いません。

未採点や拒否は元の分母に残し、修正稿の条件や論理も確認します。一般的な正答率、理解度、本番の動作と、LLMによる説明の採点は区別します。特に、採点器の満点でも条件の書き換えを見逃したため、[実文分析](prompt-quality-v6-analysis-2026-11-09.md)を併用します。

AWS認証が切れたときは、確定した記録を保持して送信だけを待ちます。通常の`aws sso login --profile pals-prod-member`で認証が回復した後、保存・同一読み戻し・再取得を行います。数学の評価や不明な外部呼び出しは再送しません。未取得の図には「ローカル計測値・CloudWatch取得待ち」を表示し、CloudWatchを出典にした図とは別の名前で保存します。
