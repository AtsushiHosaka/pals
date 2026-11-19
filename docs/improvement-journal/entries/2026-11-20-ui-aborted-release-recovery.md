# 中止した配備の復旧経路

本番UIは未切替で、#433は未完了である。取得済みownerは正規入口で解放した。後続の実機更新・本番実API受入・撮影はまだ実施していない。11月20日02:03 JSTのホーム公開GETはHTTP 200だったが、これは機能受入の証拠ではない。

再更新で過去の更新を1段しか扱えない問題を[infra PR #223](https://github.com/AtsushiHosaka/pals-infra/pull/223)で修正した。完了した過去2段を元のclosure、source、実台帳、provider結果から検証し、未知・未完了・衝突する履歴は拒否する。

claim後に中止した配備の32操作も実AWS応答を取得して照合した。30件は成功、2件は読み取り失敗だった。変更命令を読み取り扱いに変えず、失敗も保持した。[infra PR #224](https://github.com/AtsushiHosaka/pals-infra/pull/224)には、この履歴のconsumerと、自分のsuccessor fenceを片付ける正規入口を追加した。元ownerを復活させず、別のcleanup専用owner、freshな署名、元の実行構成、full18field DB共有lease、両実機のmTLS、nonceと期限を組み合わせる。

独立レビューで、computeの除去中もDB共有leaseを保持すること、既に除去した記録から再開できること、効果の直前にlease残時間を確かめること、listenerの起動遅延を待つことを修正した。これらは配備前に一連の失敗復帰を通せていなかった準備不足である。初期のprimitive単体テスト成功を、全経路の完了とは扱わない。

source `05328608a44bb4645f7c9c5f90df6ebc69607f3f`で、native safety143、repair35、repair native92、履歴16、native cleanup24、producer13、archive facts3、release step168、transition17の計511件が成功した。TLS・ECDSA署名・filesystem・遅延TCP起動を実動作で検査した。DBとAWSのunit境界は分けており、実機cleanupや本番成功を証明しない。transitionの初回実行はworld-writableな親directoryで15件が失敗し、宣言済みの保護されたscratchを使った再実行で17件が成功した。元の失敗ログは保持した。

同じ限定IAMは02:00 JSTまでを実適用・readback済みで、期限を迎えた。04:00への期限以外差分ゼロの案は、自動承認審査が具体的な明示承認を要求して拒否したため未適用である。SG追加はない。追加のモデル生成も行っていない。実機の後処理・復旧設定更新・配備・本番受入が終わるまで完了とはしない。
