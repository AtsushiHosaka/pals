# Overlay検証用containerの回収確認

2026年11月5日15時台JST、親担当が既存のローカルLinux/arm64 imageを使い、検証用の未起動containerを2個、順番に作成して回収した。両方ともcreate成功後の応答喪失を明示的に模擬し、正規cleanupによる回収・名前での残存0・元のTimeoutExpiredの伝播を確認した。containerを起動せず、imageのpull/build/公開、モデル、AWS、DB、本番の操作は行っていない。

担当Codex。[担当チャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)、進行は[#257](https://github.com/AtsushiHosaka/pals/issues/257)、[infra#99の親担当検証記録](https://github.com/AtsushiHosaka/pals-infra/pull/99#issuecomment-6651790130)。

## 固定したsourceと対象

| profile | source commit | script SHA-256 | 結果 |
|---|---|---|---|
| reviewed-project-v1 | 0d23f2a69305b2a0bf52f41ab4721384f1242922 | 78100a1cc163635daa25277f6d79f89406159d7a83fb461ff1b7bb378db93595 | 回収・残存0・例外伝播を確認 |
| source-only-v1 | 9b7ce83b4f91cbca932e52fb9a48785c74859d1f | dcdb24dadb155dece2c2364fe919154e367a9d9f7551ab1ad15c1b760b67ada3 | 回収・残存0・例外伝播を確認 |

両方ともGitの固定commitからscriptだけを別の保護ファイルへ取り出し、hashを確認して使った。既存imageはIDで固定し、一意name・owner/expiry label・network noneを付けた。daemonがcreateに成功した後、wrapperが応答を呼出側へ渡す直前にTimeoutExpiredを送る。実際のdaemon障害を発生させた試験ではない。wrapperが実際のIDを受け取っていても、検査対象の関数には渡していない。

最初の試験は新profileのcreate直後の失敗を通し、次は修正済みの従来project=None経路を通した。sourceのcopyへ進む前に失敗させるため、画像内の全sourceやproject metadataの正しさを証明する試験ではない。normal build/publicationと本番activationは未検証のままである。

## 保存と台帳

Git外の結果JSONはSHA-256 599f799eac6c08181a9b36f8a5eda95ff363ffd79c111cfcdf46b72d25ab39ca。raw container IDやregistry名、認証情報を公開していない。失敗時の補助回収もexactなname・image・label・created/非runningを照合する条件を付けた。2件とも正規処理で回収され、補助削除は不要だった。

品質台帳にはfeature_auditの1行としてn=2、successes=2を記録する。数学・モデルの精度、継続稼働率や未知の故障率には読み替えない。費用・所要時間・p50/p95は測っていないため空欄にする。実装担当と独立担当のfixture単体件数は、この2件へ足さない。既存333行をbyte単位で保持し、6グラフを同じcommitで再生成する。
