# PALS product core: language unification tasks

WORKING checklist for CORE-007/008/015/016/017. Issue: [#229](https://github.com/AtsushiHosaka/pals/issues/229).

## 調査結果（2026-11-04、コード読解のみ。本番DBと本番ログは未確認）

- 画面の言語は、端末の `pals.ui-language`（`pals-webfront/lib/uiMessages.ts:7`）に保存する。保存がなければ `navigator.languages` から決める（`components/UiLocaleProvider.tsx:15`）。サーバーには保存しない。
- 回答の既定の言語は、サーバー側の別設定 `account_output_language_preferences` にある。行がないアカウントは、常に `en` として扱う（`pals-api/app/domain/models/account_preferences.py:5`、`app/infrastructure/repositories/proof_requests.py:201`）。APIは `Accept-Language` を一切読まない。
- 設定画面は、画面の言語と出力言語を別々の部品で表示する（`components/AccountOutputLanguageSettings.tsx:164`、`165`）。出力言語が未保存のとき、設定画面は `en` を表示する。
- 要求ごとの回答言語は、`response_language()`（`pals-api/app/domain/response_language.py:85`）で決まる。依頼文の中の明示指定だけを検出し、依頼文の言語は見ない。検出がなければアカウントの出力言語を使う。この挙動は 2026-10-26 の pals-api #24 で入った。CORE-015 の旧記述（依頼文の言語を優先）と食い違ったまま、仕様は更新されていなかった。
- agent は `request.output_language` に従う。確認質問のプロンプトは `chat_runtime.py:164`、`proof_reuse.py:404` で出力言語を指定する。`output_language` が `en` なら、英語の確認質問になる。agent はこの値を上書きしない。
- 英語固定の確認文が2箇所ある。`pals-agent/pals_agent/proof_reuse.py:478`（流儀の確認 `Which reading of … applies?`）と `geometry_input.py:251`（幾何入力の確認の見出し）。Issue の質問文はこれらの定型文ではなく、モデルが生成した文である。
- 以上から、Issue の英語の確認質問は、その要求の `output_language` が `en` だったために生成されたと推定する。`en` になる経路は2つある。アカウントに保存行がなく既定の `en` が使われた経路と、以前に設定画面で `en` を保存した経路である。どちらかは、保存された要求の `output_language` を確認しないと決まらない。

## 未決定事項

- **OQ-1（オーナーの判断が必要）**: 依頼文の言語を、アカウントの設定より優先するか。
  - A: 設定が常に優先する（2026-10-26 以降の実装。オーナーの「出力設定を尊重する」要求）。
  - B: 依頼文の言語が常に優先する（CORE-015 の旧記述、2026-10-05 の承認）。
  - C: 明示的に選んだ回答言語は依頼文の言語に優先し、依頼文の言語は既定の言語（画面の言語に従う）に優先する。CORE-015 の現行案。
  - Issue #229 の完了条件「設定が自動でも手動でも、日本語で入力すれば日本語で返る」は B に近い。C は、手動で別の言語を選んだ学習者に、依頼文の言語を適用しない。
- **OQ-2**: 既存の保存済み出力言語を、明示的な回答言語の選択として扱うか。扱う場合、既存の挙動は変わらない。扱わない場合、これらの行を画面の言語に従わせる。
- **OQ-3**: 画面の言語をサーバーに保存し、端末間で共有してよいか。CORE-007 の「同じアカウントを使う端末間で共有する」は、これを前提にしている。

## Tasks

- [ ] OQ-1〜OQ-3 をオーナーが決める（`type:decision` の Issue に記録する）。
- [ ] CORE-017: agent の英語固定の確認文2箇所を4言語にする（pals-agent）。
- [ ] CORE-016: API が `Accept-Language` から初期の言語を決める。保存行がない場合の既定を `en` 固定から置き換える。
- [ ] CORE-016: IPの国による推定は、ブラウザが言語を示さない場合の補助とし、国とIPを保存しない（プライバシー確認を含む）。
- [ ] CORE-007: 言語設定を1つにする。設定画面は、画面の言語と回答の言語が一致しているか、明示的に別の言語を選んでいるかを示す。
- [ ] CORE-007: 画面の言語を変更したとき、明示的な回答言語がなければ、既定の回答言語も同じ値になる。
- [ ] CORE-015: OQ-1 の結論に合わせて `response_language()` と回帰テストを変更する。
- [ ] テスト: 新規アカウントの初期言語（`ja-JP`、`fr-FR,ja`、`fr-FR`、`zh-TW`、`zh-CN`、言語なし）。
- [ ] テスト: 日本語の依頼に対して、確認質問を含む学習者向けの文言が、設定が自動でも手動でも日本語になる。
- [ ] テスト: 明示的に別の回答言語を選んだとき、その選択が優先される。
