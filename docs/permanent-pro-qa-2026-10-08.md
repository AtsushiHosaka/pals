# 無期限QA Proの実装と公開Miniの確認

指定したテストアカウントに、課金なし・期限なしのProを付与する仕組みを実装し、本番DBの署名付き更新と公開サービスの復旧を確認した。実際の付与はMini側のAWS管理者認証を待っている。ブラウザでのPro受け入れ確認は未実施。既存の期限付き100回枠では、無期限の現行Proを再現できなかった。

## Pro資格は無期限、利用枠は毎月更新する

月300万利用トークン、1依頼30万利用トークンの現行Proを使う。利用枠はUTCの暦月ごとに更新する。付与を取り消して同じ月に再付与しても、使用量は戻らない。取消前に受理した処理は元の月の枠で精算する。

付与には有効なCognitoアカウント、専用operator、変更理由、再実行時にも使う固定grant IDを必要とする。アプリやworkerからの自己付与は拒否する。Stripe契約がある場合は契約を優先し、今回の操作ではStripe契約や請求を作らない。メールアドレス、パスワード、実subjectはこの記録に含めない。

## 実機はguestを含む26段階のリリースだった

[Miniの読み取り検査](https://github.com/AtsushiHosaka/pals/actions/runs/37727633388)で、release sequence 13、26段階のregistryを確認した。APIの実プロセスはprodで、トークン機能と現行DBのreadinessは有効だった。この全体設定を変更せず、指定したアカウントに資格を付与する。

Dockerのコンテナ設定と新しいexecプロセスには、起動時に読み込む設定が現れなかった。欠落を無効と判定しないよう、実プロセスの環境をメモリ内で参照する検査を追加した。出力は限定した状態値と真偽値だけに絞った。

mainには、実機に未適用の数学設定、proof-request-lean、recipe-search、draft-addition-candidates、reply-languageが含まれていた。これらを保持し、QA Proを最後に加える26→32段階の署名付き移行を検証した。移行元・順序・SQL・manifestを固定し、一般的な追加ステップの許可は設けていない。

## DB更新後のデータ保全検査で公開復旧が止まった

[公開更新](https://github.com/AtsushiHosaka/pals/actions/runs/37732494046)は、DBの適用後に停止した。公開APIは502を返し、[既存の署名付き復旧処理](https://github.com/AtsushiHosaka/pals/actions/runs/37733657722)も失敗した。

[保護された状態の診断](https://github.com/AtsushiHosaka/pals/actions/runs/37733979733)で、適用結果が`applied`、release sequenceが14、admissionが有効であることを確認した。独立した署名付き観測も`candidate`を返した。停止理由は、host側の既存テーブルのデータ保全検査だった。診断では非公開ログの本文を出力していない。

旧検査は全列を含む`row_to_json`のハッシュを比較する。今回のSQLは`proof_requests.formal_job_id`と`proof_clarifications.output_language`を追加するため、元の値が同じでも、行があるテーブルのハッシュは変わる。実PostgreSQLでこの挙動を再現した。修正した実際のメソッドは、元の列の順序・値・行数を保持した場合に成功し、元の値の変更、行の追加・削除、新しい列への値の追加など10件の異常を拒否した。

[修正後の復旧](https://github.com/AtsushiHosaka/pals/actions/runs/37735183465)は、実機の元データとの一致を確認して成功した。保護されたauthorityとそのpinだけを更新し、manifest・signature・snapshot・DB admissionを維持した。pendingの解除、公開health 200、サインイン画面200、未認証のauth 401を確認した。続く[通常の署名付きリリース](https://github.com/AtsushiHosaka/pals/actions/runs/37735647795)も成功した。どちらも初回は自動監視のロックと競合して変更前に停止し、同じ処理の再実行で完了した。

[復旧後の最終検査](https://github.com/AtsushiHosaka/pals/actions/runs/37735973356)では、release sequence 15、32段階のregistry、prodとtoken有効、QA ProのDBテーブルとreadinessを確認した。Mini側で必要なAWS管理者認証は確認できなかった。認証後に付与とブラウザ確認を続ける。

## コードの検証は成功、本番付与は別に確認する

| 対象 | 検証結果 |
|---|---|
| API | unit 1,965件成功、既存skip 1件。実PostgreSQLの課金・Project・既存経路98件成功。 |
| 署名付きDB更新 | 実PostgreSQL 16とpgvectorで8件成功。不正入力の拒否、rollback、既存データ・権限、replayと次の通常更新を確認。 |
| Web | 最新mainを保持し、1,514件成功。型・lint、日本語表示も確認。 |
| worker | token・claim・回答処理の関連202件成功。backend permit、独立QA、使用量不明時の停止を保持。 |
| host | controller 20件、authority 71件、operator 48件成功。一時DB権限による実CLIの2件、実PostgreSQLの行保全検証も成功。 |

スイート間には重複があるため件数は合算しない。APIの全体静的検査にはmainでも再現する問題が残る。workerの全体検査にはlocalhost権限、固定Python版、Leanと親リポジトリのfixtureが必要で、関連テストの成功を全体検証完了とは扱わない。

本番操作は、既存Mini runnerのmain限定workflowから行う。保護されたhost codeの更新、署名付きDBリリース、専用の短命operatorによる付与を順に確認する。付与後は既存ブラウザでPro・無期限・月間利用枠と有料機能への導線を確認する。未実装のモデル切替やtoken経路まで検証済みとは扱わない。
