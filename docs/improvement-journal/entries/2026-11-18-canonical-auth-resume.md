# 認証事前確認で止まった本番受け入れ再開（2026-11-18）

成功率と時間を改善するため、通常ログイン後に凍結済みcanonical受け入れ経路を再開した。planとargv・凍結対象のhashを照合した1回のpost-requestは、質問送信前に`authenticated_context_not_observed`、exit 2で止まり、結果JSONLは0行だった。質問送信・有料送信は0件で、数学問題の失敗ではない。

正規診断ではgoto 200、owner_get 0、refresh要求の観測6件、refresh HTTP 400、failed requests 6件、auth false、paid falseだった。refreshの実送信許可はcanonical最大1件で、上限外は中断した。6回の実refreshや6回の利用者試行とは数えない。通常Chromeのhome表示とAWS SSOの成功も、canonical認証contextの成功へ置き換えない。

期限切れseedを確認したが、HTTP 400の詳細原因は未確定である。新しいseedのローカル保存をユーザーへ依頼し、返答待ちとした。台帳は認証事前確認1試行、成功0、`unclassified: 1`のみを追加する。回答時間・モデル費用総額・速度改善率は未測定で、#410・#380全体は未完了。私有ログと認証情報はGitへ含めない。

[再開の条件・hash・失敗・未確認範囲](../../410-resume-auth-diagnostic-2026-11-18.md)。台帳行IDは`2026-11-18-canonical-post-request-auth-context-blocked`。
