# #410の既存回答を別sidecarで再観測した機能確認（2026-11-18）

先に送信した1件の回答を、新しい観測sourceと別sidecar contractで読み直した結果、canonical acceptanceと正規statusの再検証がacceptedとなった。phaseは`post_deployment`、候補は`1be72c60b705328c30b61c198fa037f6b6ef14dfd0f9ed92aa118914bf543f15`である。これは独立した機能確認の証拠であり、元の失敗済みreleaseをacceptedへ昇格したものではない。

担当セッションは`codex://threads/01a1e863-d84c-7e82-bedb-156dd25d871e`。[前段の認証停止と元gate失敗](410-resume-auth-diagnostic-2026-11-18.md)は親PR #414のmerge `c208730f5c408a4f53a5f69059395faacb65209c`に保持されている。観測sourceの修正は[PR #415](https://github.com/AtsushiHosaka/pals/pull/415)、merge `922aca6924587e7a232b6306c2eae6984954c2e8`で統合した。

## 実行sourceとsidecarの固定

実行sourceは`52ccfc334e97cce5215918eb44d89c62415b241a`。[exact CI](https://github.com/AtsushiHosaka/pals/actions/runs/44121623208)の`repository-safety`と`release-acceptance-contracts`は両方成功した。実行した4ファイルをimmutable archiveへ保存し、そのfingerprintは`83fa73fdb8a60fb9dc59ffda1423a714ae11cf6adfa37c1861ab9541d252c91f`である。

新しいsidecarのSHA256は`74eb71ee1f5cf4f58de9c638216a4028563b13d638e6b15168d5ae42f0b5cebc`。元planの`acceptance.post_contract`が指す旧contractと比較し、変更fieldが`runner_sha256`だけであることを確認した。runtime・model・scenario・source・image・固有の結論条件を含む他fieldは不変である。plan全体をsidecarと比較したという意味ではない。旧plan・seed・failed journalは変更していない。

記録作成時にも、provenanceの旧contract hashと参照先、新sidecar hash、4ファイルのpinと実archive、実行source revisionを読み取り専用で独立照合した。元planのSHA256 `8807d098d93df78b85ae2fdb04e24c7d7271c69093ab3e44c75d40837578e388`も保持する。token・claim値・内部保存先・host・IP・質問本文・request/chat IDは公開しない。

## 実際のrecapture結果

新しい別attempt台帳のSHA256は`df7222b02c3f07471c08ed28d551bd556559e359febf8d80a01b677ed97a1f55`。source順序からの推測だけでなく、実runtimeの前後と配信asset 26件を照合した観測である。正規statusの再検証でもacceptedを確認した。

| 確認対象 | 結果 |
|---|---|
| phase／terminal | post_deployment／answered |
| evidence | lean_verified |
| runtime metadata | 6 roles照合 |
| renderとreload | hash一致 |
| attempted_mutations | 0 |
| suppressed_cloudflare_rum_posts | 3 |
| served_assets | 26 |
| authentication_posts | 1 |
| product telemetry | 0 |

RUMの3件は通信をabortしたまま専用counterへ分離した。認証POST 1件やasset 26件、抑止3件を別の利用者試行や数学の成功数へ数えない。本recaptureの新規有料送信は0件で、再開全体の新規質問は先の1件から増やしていない。

観測の開始は`2026-11-17T16:06:51.570872Z`、終了は`2026-11-17T16:08:16.330041Z`で、JSTでは11月18日である。この区間は既存回答の再観測に要した時間であり、生成時間や#380の10秒目標の性能値ではない。金額は未取得なのでUSD欄は空にする。

## 認証診断と未完了の後処理

認証の追加診断では、新しい18日分のseedはrefresh HTTP 200、旧16日分はHTTP 400・`NotAuthorizedException`だった。認証sourceを変更せずに確認し、追加の有料送信は行っていない。

元releaseのfailed、停止時間超過、accepted=falseはそのまま保持する。owner解放とcleanupは未完了である。引継ぎ時点で、01:40 JST失効の固定policy案について追加承認を待っており、applyは0件。今回の機能確認を権限更新や後処理適用の許可として扱わない。後続の承認・適用・cleanup結果は担当が確認後に追記する。

品質台帳は別sidecarでの機能gate再観測1件をn=1・成功1とし、元gate失敗行への`overlap_with`を付ける。旧失敗を消さず、生成した数学問題の独立試行や10秒目標の成功率へ合算しない。台帳行IDは`2026-11-18-canonical-acceptance-sidecar-recapture`。

## #380のsource readinessと残る配備準備

[API #118](https://github.com/AtsushiHosaka/pals-api/pull/118)・[API #120](https://github.com/AtsushiHosaka/pals-api/pull/120)は正規production source branch `claude/seq28-api-response-language`へ統合済みで、headは`eebb1abf7c010c3a13c1179a810db82e2b142e5e`。[push CI](https://github.com/AtsushiHosaka/pals-api/actions/runs/44057839447)の`api-regression`はこのexact headで成功した。[Web #83](https://github.com/AtsushiHosaka/pals-webfront/pull/83)・[Web #84](https://github.com/AtsushiHosaka/pals-webfront/pull/84)も正規branch `codex/sidebar-inline-math-20261031`へ統合済みで、head `6dea87ed9af806ddecc124206c416a8dae4c450f`の[CI](https://github.com/AtsushiHosaka/pals-webfront/actions/runs/44057863274)で`web-regression`が成功した。両checkはGitHub Actions app 15368で、strict・PR必須・admin enforcementの保護を維持していることを読み取り専用で照合した。

一方、配備候補と親gitlinkはAPI `4868a504fc6f20211742377b80e40ac27a88464c`、Web `86c946b34ebb14fa9b0f8742d6de2d17ab55aa70`という旧sourceのままで、上記統合headの祖先である。既に正規branchへ統合されているため、追加cherry-pick PRは不要。各mainはstale/divergedな差分があり、既存機能を失うリスクのある配備sourceの代替にはせず、scope外の別案件も変更していない。

新sourceを含む候補pins・images・provenance・local qualification・acceptanceは未実施である。今回のrecapture acceptedは旧配備候補に対する別証拠であり、新しいAPI/Web sourceの配備や「80%を10秒以内」の達成を証明しない。この段階で行ったのはsourceの準備状況と公開記録の確認だけで、本番設定・権限の変更は0件である。
