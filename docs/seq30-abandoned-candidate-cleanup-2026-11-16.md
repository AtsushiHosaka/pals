# seq30の放棄候補の配置回収（2026-11-16）

有効化していない候補b976について、正規`release-observe.py`で所有権がないことと前版の稼働状態を確認した後、正規`release-host-clean.py`で候補の配置を回収しました。受領書に記録されたcontrolの4ディレクトリ、computeの3ディレクトリが削除対象と一致し、別の読戻しで両roleの`gone_verified=true`を確認しました。これは配置回収の技術確認1件の成功であり、本番リリースや製品受け入れの成功ではありません。

親は`24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infraは`ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`、候補SHA256は`b976afec64f31a3d9f3b74a11dbff6b9a9b46d27d32be2d2865e82cf1fc3f59a`です。期限切れを理由にした例外ではなく、未有効化で放棄した候補を扱う正規cleanupを使用しました。

## 観測と保護条件

直前の正規観測は2026-11-16 07:58:56 UTCで、ownerなし、application・databaseの変更なしでした。既知の12 attempt stateを確認し、前版4 actorのimage pinとの一致、controlの前版runtime config照合を確認しています。両roleのflagged processは0でした。正規validatorでhost binding、900秒以内の鮮度、candidateが稼働していないことを照合してからcleanupへ進みました。

削除対象は実prepare受領書から正規に再導出しました。前版が参照するpathとの重複・包含を拒否する検査を通し、回収後の受領書でもその対象と一致しています。ホスト側でも所有権lockと、稼働container・unit・他releaseの参照を保護する正規処理を使用しました。所有権を持つreleaseを強制終了したり、receiptやPASSを手作業で作ったりしていません。

private journalでは08:01:05 UTCから08:01:14 UTCまでに、各roleのcleanとreadback-goneについて、それぞれ1組のintent・send・resultを確認しました。このtimestamp幅を処理全体の精密なwall時間とは扱いません。受領書の`application_mutated`と`database_mutated`はfalseです。これらは製品やDBへの変更がないという値で、配置ファイルを削除していないという意味ではありません。

## 根拠と限界

| 記録 | SHA256 |
|---|---|
| 直前観測のファイル | `432a24fc8c6e9932ec9e6d0e90d7e682fd216f8b4f257fbb4c6abbd108c2a5dc` |
| cleanup受領書内の観測canonical JSON | `d1ac63cf4fa4c6d6e61090baa990af359d673e6910121184ab85a87ecc078b77` |
| 元prepare受領書 | `c8f640575375f6eb3bce753bac697f410df6b4c619ac4c16001637a19ff13054` |
| cleanup受領書 | `0919b33b0a75c47bed42de1bb78b4f51f88e79a0147a658659dc6c54f5ac9919` |
| cleanupログ | `8a54ac599949b3672bf3fba8768438e231b545fec31790b4c49499b5bb0adc83` |

観測のファイルhashとcanonical JSON hashは表現が異なります。実ファイルを正規の`enc`で再符号化したhashがcleanup受領書に一致することを確認しました。raw記録、内部path、識別子は公開しません。

cleanup後の所有権や前版の製品動作を新しい観測で再確認した記録ではありません。質問・モデル呼び出しは追加しておらず、費用総額も測定していません。[通知抑制作成の失敗](seq30-alert-minute-precision-failure-2026-11-16.md)やその未完了結果を、この配置回収の成功で書き換えません。
