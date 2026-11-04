# 本番seq17と次の更新の確認（2026年11月4日）

11月4日23時38分JST、既存SSM経路を使い、本番2ホストを読み取り確認した。両ホストの設定は同じseq17 manifestを参照し、manifestと署名のSHA、固定した公開鍵SPKI、実署名を照合した。7コンテナは稼働していた。再起動、署名、DB適用、IAM変更は行っていない。

| 項目 | 実機で確認した値 |
|---|---|
| manifest SHA-256 | `fc702c2375024ba81e2f8d34f34ab6bcf0efd1867e8aa16bd99d972589fb9095` |
| 発行 | 2026-11-03 16:11:19 UTC |
| 期限 | 2026-11-04 16:11:19 UTC、11月5日01:11:19 JST |
| API / reconciler | `9f45a39ea023ac9f7f28f9efdb816b90c18cffff` |
| worker | `6e5c58dec2459962b2df498385d47cd8d6abe3a2` |
| Web | `581fd231ebb260ab9a6c0a66962a65b684a044af` |
| infra | `6ddafd53259d3385af0243521d729e11a93106f1` |
| 維持されているverifier imageのsource | `189b44378e6e63e5ab7c92d9c5b7d6507acd80f0` |

期限切れだけで稼働中のサービスが止まる実装ではないが、その後の起動・復旧には影響する。コンテナ稼働の確認は、利用者が回答を得られたことや復旧試験の成功とは分ける。

## 修正の候補

| 候補 | 確認した範囲 | 未了 |
|---|---|---|
| [pals-api #44](https://github.com/AtsushiHosaka/pals-api/pull/44) | 正しい本番系統がbase。head `bcfba22fe14198be15da5d12301b95db937561d4`。タイトル・チャット・共有関連28テストとRuff通過 | マージ、新イメージ、署名、配備、実画面 |
| [pals-agent #48](https://github.com/AtsushiHosaka/pals-agent/pull/48) | seq17からの移植。head `7f17c526aec5d4d341fbbb7cc034ac33ec28f000`。対象71テストとRuff通過。#42/#43の理由ログを保持 | 広い回帰試験は260通過・既存1失敗。モデル評価、信頼pin、新イメージ、署名、配備 |
| Webのタイトル・Leanポップオーバー | #35/#36は本番系統へマージ済みというGitHub情報を確認 | 次の正確なsource/imageと実画面の確認 |
| WebのOGカード | #31は別のmainへマージ済み | 本番系統への移植と確認 |

agent #48の既存失敗は、変更前の正確なseq17でも再現した。story testは330秒を期待するが、変更していないworkerの再照合上限は2,000秒だった。この修正では無関係な上限やテストを変えていない。単体テストの通過から、説明の精度向上を主張しない。

## 更新前に必要なもの

稼働中infraの計算ホストの信頼リストにはseq17 workerがあり、新workerはまだ含まれない。プロンプト差分だけでも、このsource pinを正規に更新しなければ配備できない。古いローカルinfraのスクリプトを、実機より新しいものとして使わない。

次の更新には、正確な変更範囲、4つの不変イメージdigestとsource、直前manifestへの結び付け、DB identity、schemaと役割、toolchain、候補manifestのdigestが必要である。Terraformが必要なら保存したplanと操作一覧、停止時間と復旧手順、一時IAMの範囲と削除手順も提示する。CloudWatch導入に伴うホスト交換や費用構成の変更を、署名期限への対応へ無断で混ぜない。

現行のAurora runtime-update CLIは、署名を検証してDBへ適用する経路であり、オフラインの準備やdry-runには使えない。24時間の方針を保ち、現行source/imageを維持する更新候補をオフラインで作るツールを別に準備している。未署名候補の整形・値の検査と、KMS署名・正規admissionの成功は別である。

配備の承認範囲が未確定の部分は、具体的な候補と操作を示してからオーナーへ確認する。過去の「Codexに任せる」だけでIAM付与や署名制限の変更まで承認されたとは扱わない。

進行と判断は[#234](https://github.com/AtsushiHosaka/pals/issues/234)、署名更新は[#142](https://github.com/AtsushiHosaka/pals/issues/142)、担当は[このCodexチャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)。rawのSSM応答、内部ホスト、資源ID、設定の秘密は公開しない。
