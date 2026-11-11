# Recipe の具体化: 現行の `exact` はどこまで通るか、何を足せば届くか（2026-11-10、実 Lean、モデル 0 回）

- 指標: 再利用経路の被覆（成功率）と、1 回の compile 時間。費用はゼロ（モデル呼び出しなし）。
- 仮説: 一般形 Recipe は、Lean の単一化に任せると定義的に一致する具体例しか通らない。closer を足せば被覆は伸びるが、Recipe を使わない近道で通る危険が出る。
- 変更: なし（本番コード・フラグ・pin は不変）。実験スクリプトは pals-agent の `claude/recipe-instantiation-experiment`。結果の文書は [recipe-instantiation-experiment-2026-11-10](../../recipe-instantiation-experiment-2026-11-10.md)。
- 測定の条件: Lean 4.32.0-rc1、Mathlib 8b62164、Recipe 12 件（既存 10＋ε-δ の和・定数倍 2）、手書きの 48 文（正例 38、負例 10）、5〜6 種の closer。import 形式 262 compile、append 形式 46 compile、再実行 36 compile。Lean は 1 回に 1 プロセス。他セッションの Lean が並走（load average 9〜35）。
- 結果:
  - 現行の `exact G _` は正例 38 件中 10 件（定義的に一致するものだけ）。
  - 束縛つき `exact`／`simpa`／`convert`、`apply_rules`、束縛つき `convert … using 1; funext x; ring` を足すと、失敗 28 件中 26 件を、Recipe を使い近道なしで救えた。残る 2 件は候補にない Recipe が要る正しい失敗。
  - 裸の simp 系（`simpa`、`aesop`）は、微分可能性の 3 文で Recipe を使わず近道で閉じた。使用定数検査が要る。
  - 候補 5 件の `first | exact …` は救済 0 件。
  - 負例 10 件のうち 9 件は全 closer で失敗。1 件（`x^2*x`、`pow 3` で定義的に正しい）は通ったが、ラベルの誤りで、Recipe を使った正しい証明。
  - 1 compile の中央値は import 4.0〜4.3 秒、append 4.8〜5.2 秒。Mathlib の読み込みが支配的で、PIR-014 の「約 10 秒」は再現しなかった。
- 判断: PIR-006 は、束縛つき `exact`、`convert/funext/ring`、Recipe 限定の `apply_rules` を足し、使用定数検査（G を使う、近道補題なし）と一緒にするなら緩めてよい。検査なしの緩和と、裸の simp 系は不可。
- 限界: cold キャッシュ未測定、append は 12 文のみ、負荷が一定でない、本番の検証器では未実施、検査は定数の有無（必要条件に近いが十分ではない）。
