# リアーキテクチャの計測(pals#493)

各段階の前後の値を、同じコマンドで測るための置き場所です。定義は `pals-scripts/measure-codebase.py` の先頭と、[設計メモ](../rearchitecture-plan-2026-11-24.md)の付録Aにあります。

```bash
python3 pals-scripts/measure-codebase.py --workspace /tmp/pals-measure --clone --window 2026-11-18..2026-11-24 > docs/rearchitecture/baseline-2026-11-24.json
```

- 読み取りだけを行います(git の clone/fetch と、GitHub の API の参照)。workflow の起動、push、コメントはしません。
- `--no-jobs` を付けると、job ごとの API 呼び出し(実占有と job 時間)を省きます。

| ファイル | 内容 |
|---|---|
| [baseline-2026-11-24.json](baseline-2026-11-24.json) | 段階1の前の値。窓は 11-18〜11-24、churn は 10-01 以降。各 repo の origin/main |

ベースラインと設計メモの数値の対応:
- infra の取消しの実占有は 19.8%(428分)で、設計メモと一致します。
- CI の wall の中央値(infra 20.8分、n=73)は、窓の全成功 run から求めました。設計メモの値(20.4分)は直近25件から求めたので、少し違います。
- PR の open→merge は、窓(11-18〜24)にマージされた PR です。設計メモの値は 11-10 以降の PR です。
