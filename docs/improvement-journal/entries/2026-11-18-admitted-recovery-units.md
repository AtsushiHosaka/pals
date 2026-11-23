# 現行版だけを復旧するunitを固定入力から生成する（2026-11-18）

[#433](https://github.com/AtsushiHosaka/pals/issues/433)の本番復旧担当から、systemd unitの純生成処理を切り出した。期限切れの旧署名や旧unitを改変せず、別purposeの復旧経路を準備するための部品である。今回の変更は許可・署名・DB排他・復旧処理そのものを実行しない。

infra `76335a4fae7a12df89d28b220f94bb1b73c1965a`を基点に、入力をcanonical UUIDv4、host role、4種類のkind、固定配下のhelper/job pathとSHA256へ限定した。kindごとのjob filenameとpermit別directoryを一致させ、空白・改行・systemd specifier・環境展開・path traversalを拒否する。固定のPythonとCLIだけを生成し、任意のshell・環境・追加directive・callbackは受け取らない。旧unitは読み書きしない。

返すartifactにはimmutableな入力specとunit本文・digestを含める。これは宣言されたpinの結合であり、実ファイルのroot所有・hash・署名・期限・権限を検証した証拠ではない。installerとconsumerが実ファイルと自己source、code bundleを独立して検証する必要がある。systemdのactive表示をhealthや受け入れ成功にしない。

Python3.12.13で新15件と既存workflow契約13件が成功し、独立担当も同じ検査を実行した。rootと独立レビューにP0〜P2指摘はなかった。required CIへ、非ゼロ件数とskipなしを要求する専用stepを追加した。単体・CI件数は製品評価の台帳分母へ足さない。

Macと既存ローカルPGコンテナにはsystemd-analyzeがなかった。追加調査で既存CI用Linuxのsystemd255.4を確認し、生成4unitの検査用コピーへ`systemd-analyze --generators=no --recursive-errors=yes --man=no verify`を実行した。exit1で、API・workerの本番用credential unitがこの環境に無いため、3actorの依存検査が止まった。構文エラーの診断は無かったが全体PASSにはしない。実依存のある対象での再検査、設置・boot・本番復旧は未検証である。ConfigParserを実systemdの代わりにせず、ダミー依存や弱い検査で成功に置き換えない。検査コピーはfinallyで削除しtransportの正常終了を確認した。install・enable・start・restart・generator起動・AWS・DB・有料実行は0件。

担当チャット: codex://threads/01a1e863-d84c-7e82-bedb-156dd25d871e。本番実行担当は引き続きcodex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2で、復旧全体の結合・正規CI・本番承認・配備・保存と再表示の確認を別に進める。

出典: [infra PR #199](https://github.com/AtsushiHosaka/pals-infra/pull/199)、source `4f9a1e29b89236ec2f1c0a0455c8951149629b74`。component CI `44259380454`は4job全ての待機状態を再照合し、本番担当との合意で取り消した。componentはNOT QUALIFIEDのまま保持する。最終統合exact headで、新15件の非ゼロ・skipなしを含むrequired4jobを実行し直す。部品の旧結果は流用しない。
