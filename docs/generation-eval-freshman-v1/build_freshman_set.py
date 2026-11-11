#!/usr/bin/env python3
"""大学1年レベルの評価題 40 題（freshman-v1）の生成と検査。

generation-eval-v1（pals-agent の testdata）と同じ項目・同じ検査の考え方で、
分割だけ 50/50（dev_unseen / held_out）にしたもの。標準ライブラリだけを使い、
pals-agent のサブモジュールに依存しない（版の違うサブモジュールでも動くように
定数と分割の関数を複製している。複製元: pals_agent/evals/manifest.py）。

使い方:
    python3 build_freshman_set.py build     # manifest.json と SPLIT.sha256 を書く
    python3 build_freshman_set.py validate  # 検査だけ（既定）
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
SPLIT_FILE = HERE / "SPLIT.sha256"

VERSION = "generation-eval-freshman-v1"
SPLIT_SALT = "pals-generation-eval-freshman-v1"
HELD_OUT_FRACTION = 0.5
SPLITS = ("dev_unseen", "held_out")
TIERS = ("easy", "medium", "hard")
# 一手で終わる自明な題。測定で区別できるよう印を付ける（`trivial: true`）。
TRIVIAL = frozenset({
    "two-to-ten-mod-eleven", "mean-and-squared-deviation", "union-monotone",
    "fair-die-even-probability", "abs-continuous-at-zero", "set-difference-of-union",
})
FAITHFULNESS_RULE = (
    "期待される結論の主張が定理文として述べられていれば忠実とみなす。題文にある証明方法の"
    "指定（「定義から」「直接の計算で」「ε-N 論法で」等）は定理文に反映できないため、"
    "忠実さの判定には使わない。定式化の自由度がある題は、その結論に認める形を書いた。"
)
OUTLOOKS = ("direct", "lemma-needed", "awkward", "unlikely")
TAGS = (
    "needs-induction",
    "epsilon-delta",
    "inequality",
    "linear-algebra",
    "counterexample",
    "computation",
    "existence-uniqueness",
    "equivalence",
)
# (x+y)^2 の展開は検査の題材にしない（AGENTS.md）。generation-eval-v1 と同じ正規表現。
BANNED_PATTERNS = (
    re.compile(r"\(\s*[A-Za-z0-9]+\s*[+\-]\s*[A-Za-z0-9]+\s*\)\s*(?:\^|\*\*)\s*2"),
    re.compile(r"\(\s*[A-Za-z0-9]+\s*[+\-]\s*[A-Za-z0-9]+\s*\)\s*²"),
)
_CJK = re.compile(r"[぀-ヿ一-鿿]")
_TAG_RULES = {
    "needs-induction": r"induction|帰納|for every natural|任意の自然数|first n ",
    "epsilon-delta": r"limit|converg|continuous|連続|極限|収束|derivative|微分|differentiab",
    "inequality": r"inequal|不等式|[<>≤≥]|at most|at least|bound",
    "linear-algebra": r"matrix|matrices|linear map|vector space|eigen"
    r"|determinant|行列|線形|固有|dimension",
    "counterexample": r"counterexample|反例|not injective|単射か"
    r"|ではない|does not exist|存在しない|false",
    "computation": r"compute|evaluate|calculate|求め|解け|solve",
    "existence-uniqueness": r"exists|unique|存在|一意",
    "equivalence": r"if and only if|iff|同値|であることと",
}
REQUIRED = (
    "id", "source", "field", "tier", "tier_basis", "split", "language", "statement",
    "statement_sha256", "expected_conclusion", "mathlib_outlook", "tags", "history",
    "fixed_lean_statement", "expected_answer", "trivial",
)
POLICY = (
    "held_out は最終確認専用。誰も調整・探索・試走に使わない。開くときは理由を"
    "改善ジャーナルに書き、開いた後の題は調整に使わない。dev_unseen は作成時点で"
    "どの調整・評価・試走にも未使用。"
)

# (slug, field, tier, statement, 期待される結論, Mathlib の見込み, 期待する答え)
# 文は自分の言葉で書いた標準的な演習。既存の題・カタログのカードの言い換えではない。
# 難度は assigned（構造からの手動割り当て）。easy=1 手〜数手、medium=補題や場合分けが要る。
P: list[tuple[str, str, str, str, str, str, str | None]] = [
    # --- calculus-analysis (9) ---
    ("cube-plus-id-increasing", "calculus-analysis", "easy",
     "Show that f(x) = x^3 + x is strictly increasing on the real line.",
     "任意の実数 x<y について x^3+x < y^3+y が成り立つ。", "direct", None),
    ("quadratic-derivative-by-definition", "calculus-analysis", "easy",
     "f(x)=3x²−5x+2 の導関数を、差分商の極限の定義から求め、任意の実数 x で f'(x)=6x−5 であることを示せ。",
     "f は任意の実数 x で微分可能で、導関数は 6x−5 である。", "lemma-needed", "6x-5"),
    ("sine-lipschitz", "calculus-analysis", "medium",
     "Prove that |sin x − sin y| ≤ |x − y| for all real numbers x and y.",
     "任意の実数 x,y について |sin x − sin y| ≤ |x − y| が成り立つ。", "lemma-needed", None),
    ("exp-two-x-derivative", "calculus-analysis", "easy",
     "関数 g(x)=e^{2x} の導関数が、任意の実数 x で 2e^{2x} であることを示せ。",
     "g は任意の実数 x で微分可能で g'(x)=2e^{2x}。", "direct", "2e^{2x}"),
    ("abs-continuous-at-zero", "calculus-analysis", "easy",
     "Show that the absolute value function f(x) = |x| is continuous at 0.",
     "f(x)=|x| は x=0 で連続である。", "direct", None),
    ("cubic-root-in-unit-interval", "calculus-analysis", "medium",
     "方程式 x³+x−1=0 は開区間 (0,1) に少なくとも1つの実数解を持つことを示せ。",
     "x³+x−1=0 を満たす実数 x が 0<x<1 の範囲に存在する。", "lemma-needed", None),
    ("arctan-lipschitz", "calculus-analysis", "medium",
     "Prove that |arctan x − arctan y| ≤ |x − y| for all real x, y.",
     "任意の実数 x,y について |arctan x − arctan y| ≤ |x − y| が成り立つ。", "lemma-needed", None),
    ("integral-of-sine-over-half-period", "calculus-analysis", "easy",
     "微積分の基本定理を用いて、定積分 ∫_0^π sin x dx の値が 2 であることを示せ。",
     "∫_0^π sin x dx = 2。", "direct", "2"),
    ("inverse-one-plus-square-derivative", "calculus-analysis", "easy",
     "関数 f(x)=1/(1+x²) の導関数が、任意の実数 x で −2x/(1+x²)² であることを示せ。",
     "f は任意の実数 x で微分可能で f'(x) = −2x/(1+x²)²。", "direct", "-2x/(1+x^2)^2"),
    # --- linear-algebra (7) ---
    ("eigenvectors-of-symmetric-2x2", "linear-algebra", "easy",
     "行列 A=[[2,1],[1,2]] について、ベクトル (1,1) は固有値 3 の固有ベクトル、"
     "(1,−1) は固有値 1 の固有ベクトルであることを示せ。",
     "A(1,1)=3(1,1) かつ A(1,−1)=1·(1,−1)。どちらも零ベクトルでない。", "direct", None),
    ("inverse-by-exhibiting", "linear-algebra", "easy",
     "Show that the real matrix A = [[1,2],[3,4]] is invertible by exhibiting "
     "an inverse matrix.",
     "B=[[−2,1],[3/2,−1/2]] は AB=BA=I（単位行列）を満たす。したがって A は可逆。",
     "direct", None),
    ("dependent-consecutive-triples", "linear-algebra", "easy",
     "R³ のベクトル (1,2,3), (4,5,6), (7,8,9) は線形独立でないことを示せ。",
     "自明でない一次関係が存在する。例: 1·(1,2,3) − 2·(4,5,6) + 1·(7,8,9) = 0。",
     "direct", None),
    ("idempotent-eigenvalues", "linear-algebra", "medium",
     "Prove that if a real square matrix A satisfies A·A = A, then every real "
     "eigenvalue of A is 0 or 1.",
     "A が正方行列で A·A=A、λ が A の固有値なら λ=0 または λ=1。", "lemma-needed", None),
    ("transpose-of-product", "linear-algebra", "easy",
     "実数成分の行列 A (m×n)、B (n×p) について、積の転置 (AB)^T が B^T A^T に等しいことを示せ。",
     "任意の m×n 行列 A、n×p 行列 B について (AB)^T = B^T A^T。", "direct", None),
    ("zero-sum-plane-subspace", "linear-algebra", "easy",
     "Show that W = {(x, y, z) ∈ ℝ³ : x + y + z = 0} is a linear subspace of ℝ³.",
     "W は零ベクトルを含み、加法とスカラー倍で閉じている。", "lemma-needed", None),
    ("swap-sum-difference-bijective", "linear-algebra", "medium",
     "線形写像 T:ℝ²→ℝ², T(x,y)=(x+y, x−y) は全単射であることを示せ。",
     "T は単射かつ全射である（逆写像 (u,v)↦((u+v)/2,(u−v)/2) をもつ）。", "lemma-needed", None),
    # --- discrete-logic (5) ---
    ("set-difference-of-union", "discrete-logic", "easy",
     "Show that for any sets A, B, C we have A \\ (B ∪ C) = (A \\ B) ∩ (A \\ C).",
     "任意の集合 A,B,C について A\\(B∪C) = (A\\B)∩(A\\C)。", "direct", None),
    ("image-of-intersection", "discrete-logic", "medium",
     "写像 f:A→B と部分集合 X,Y⊆A について f(X∩Y) ⊆ f(X)∩f(Y) を示せ。"
     "また、逆の包含が一般には成り立たない例を挙げよ。",
     "f(X∩Y)⊆f(X)∩f(Y) は常に成り立つ。逆の包含（等号）が成り立たない f,X,Y が存在する"
     "（具体例: f:ℝ→ℝ を定数関数 0、X={0}、Y={1} とすると f(X∩Y)=∅、f(X)∩f(Y)={0}）。",
     "lemma-needed", "反例あり"),
    ("powerset-cardinality", "discrete-logic", "medium",
     "Prove that a finite set with n elements has exactly 2^n subsets.",
     "要素数 n の有限集合の部分集合の個数は 2^n。", "direct", None),
    ("union-monotone", "discrete-logic", "easy",
     "集合 A,B,C について、A⊆B ならば A∪C ⊆ B∪C であることを示せ。",
     "A⊆B ならば A∪C ⊆ B∪C。", "direct", None),
    ("no-surjection-onto-powerset", "discrete-logic", "medium",
     "Prove (Cantor) that there is no surjective function from a set S onto its power set.",
     "任意の集合 S について、S から S の冪集合への全射は存在しない。", "direct", None),
    # --- number-theory (5) ---
    ("odd-square-mod-eight", "number-theory", "easy",
     "n が奇数ならば、n² を 8 で割った余りは 1 であることを示せ。",
     "n が奇数なら n² ≡ 1 (mod 8)。", "lemma-needed", None),
    ("consecutive-product-even", "number-theory", "easy",
     "Show that n(n+1) is even for every integer n.",
     "任意の整数 n について n(n+1) は偶数。", "direct", None),
    ("coprime-sum-and-product", "number-theory", "medium",
     "整数 a,b が互いに素ならば、a+b と ab も互いに素であることを示せ。",
     "gcd(a,b)=1 ならば gcd(a+b, ab)=1。", "lemma-needed", None),
    ("cube-minus-self-divisible-by-six", "number-theory", "medium",
     "整数 n について、n³−n は 6 の倍数であることを示せ。",
     "任意の整数 n について 6 ∣ n³−n。", "lemma-needed", None),
    ("two-to-ten-mod-eleven", "number-theory", "easy",
     "2^10 を 11 で割った余りが 1 であることを、直接の計算で示せ。",
     "2^10=1024 であり 1024=11×93+1。したがって 2^10 ≡ 1 (mod 11)。", "direct", "1"),
    # --- inequalities (4) ---
    ("am-gm-two-variables", "inequalities", "easy",
     "Prove that (a + b)/2 ≥ √(ab) for all nonnegative real numbers a and b.",
     "任意の非負実数 a,b について (a+b)/2 ≥ √(ab)。", "lemma-needed", None),
    ("bounded-rational-function", "inequalities", "medium",
     "Show that x / (1 + x^2) ≤ 1/2 for every real number x.",
     "任意の実数 x について x/(1+x^2) ≤ 1/2。", "lemma-needed", None),
    ("bernoulli-inequality", "inequalities", "medium",
     "Prove Bernoulli's inequality: for every real x ≥ −1 and every natural number n, "
     "(1 + x)^n ≥ 1 + n·x.",
     "任意の実数 x≥−1 と自然数 n について (1+x)^n ≥ 1+n·x。", "direct", None),
    ("reverse-triangle-inequality", "inequalities", "easy",
     "実数 a,b について、||a|−|b|| ≤ |a−b| が成り立つことを示せ。",
     "任意の実数 a,b について ||a|−|b|| ≤ |a−b|。", "direct", None),
    # --- sequences-limits (5) ---
    ("alternating-over-n-tends-to-zero", "sequences-limits", "easy",
     "Show that the sequence a_n = (−1)^n / n (n ≥ 1) converges to 0.",
     "n→∞ のとき (−1)^n / n → 0（|a_n| = 1/n で挟み撃ち）。", "lemma-needed", "0"),
    ("sqrt-difference-tends-to-zero", "sequences-limits", "medium",
     "数列 a_n=√(n+1)−√n が 0 に収束することを示せ。",
     "n→∞ のとき √(n+1)−√n → 0（有理化して a_n=1/(√(n+1)+√n) とみなせる）。",
     "lemma-needed", "0"),
    ("n-over-n-plus-one-monotone", "sequences-limits", "easy",
     "Show that the sequence a_n = n/(n+1) is strictly increasing and a_n < 1 for every n.",
     "任意の自然数 n について a_n < a_{n+1} かつ a_n < 1。", "direct", None),
    ("geometric-sequence-tends-to-zero", "sequences-limits", "easy",
     "実数 r が |r|<1 を満たすとき、数列 r^n (n=0,1,2,…) は 0 に収束することを示せ。",
     "|r|<1 ならば n→∞ のとき r^n → 0。", "direct", "0"),
    ("limit-of-sum", "sequences-limits", "medium",
     "Suppose a_n → a and b_n → b as n → ∞. Prove from the ε-N definition that "
     "a_n + b_n → a + b.",
     "a_n→a かつ b_n→b ならば a_n+b_n → a+b。認める定理文: ε-N 形、または "
     "Filter.Tendsto による形のどちらでもよい（証明方法の指定は定理文に反映しない）。",
     "direct", None),
    # --- probability-statistics (5) ---
    ("fair-die-even-probability", "probability-statistics", "easy",
     "公正なサイコロを1回振るとき、偶数の目が出る確率は 1/2 であることを示せ。",
     "標本空間 {1,…,6} の一様分布で、事象 {2,4,6} の確率は 3/6=1/2。"
     "認める定式化: 一様な有限集合上の数え上げの比、または同等の確率測度での記述。",
     "lemma-needed", "1/2"),
    ("two-dice-sum-seven", "probability-statistics", "medium",
     "Two fair six-sided dice are rolled. Show that the probability that the sum "
     "is 7 equals 1/6.",
     "36 通りの等確率の組のうち和が 7 になるのは 6 通りなので確率は 6/36=1/6。"
     "認める定式化: 36 要素の一様な有限集合上の数え上げの比、または同等の確率測度での記述。",
     "lemma-needed", "1/6"),
    ("independent-union-probability", "probability-statistics", "medium",
     "事象 A,B が独立で P(A)=1/2, P(B)=1/3 のとき、P(A∪B)=2/3 であることを示せ。",
     "独立なので P(A∩B)=1/6。P(A∪B)=1/2+1/3−1/6=2/3。"
     "認める定式化: 確率測度 P と独立 P(A∩B)=P(A)P(B) の仮定のもとでの主張。"
     "（標本空間を具体に取る場合は、条件を満たす一様な有限空間でもよい）。",
     "lemma-needed", "2/3"),
    ("mean-and-squared-deviation", "probability-statistics", "easy",
     "Show that the mean of the numbers 1, 2, 3, 4, 5 is 3, and that the sum of "
     "the squared deviations from this mean is 10.",
     "(1+2+3+4+5)/5=3 であり、Σ(k−3)^2 = 4+1+0+1+4 = 10。", "direct", "mean 3, sum 10"),
    ("three-tosses-two-heads", "probability-statistics", "medium",
     "A fair coin is tossed three times. Show that the probability of getting exactly "
     "two heads is 3/8.",
     "8 通りの等確率の結果のうち、表がちょうど2回になるのは 3 通りなので確率は 3/8。"
     "認める定式化: 有限一様空間での数え上げの比、または同等の確率測度での記述。",
     "lemma-needed", "3/8"),
]


def detect_language(text: str) -> str:
    return "ja" if _CJK.search(text) else "en"


def derive_tags(statement: str) -> list[str]:
    low = statement.lower()
    return sorted(t for t, rule in _TAG_RULES.items() if re.search(rule, low))


def _rank(pid: str) -> str:
    return hashlib.sha256(f"{SPLIT_SALT}:{pid}".encode()).hexdigest()


def assign_splits(items: list[dict[str, Any]]) -> None:
    """(field, tier) の層ごとに held_out を 50% の切り捨てとし、合計を round(0.5N) に補正する。
    層内の並びは sha256(salt:id)。乱数を使わない。"""

    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for p in items:
        strata[(p["field"], p["tier"])].append(p)
    quota = {k: int(len(v) * HELD_OUT_FRACTION) for k, v in strata.items()}
    target = round(len(items) * HELD_OUT_FRACTION)
    by_remainder = sorted(
        strata, key=lambda k: (-(len(strata[k]) * HELD_OUT_FRACTION - quota[k]), k)
    )
    for k in by_remainder:
        if sum(quota.values()) >= target:
            break
        quota[k] += 1
    for k, members in strata.items():
        for i, p in enumerate(sorted(members, key=lambda p: _rank(p["id"]))):
            p["split"] = "held_out" if i < quota[k] else "dev_unseen"


def split_checksum(items: list[dict[str, Any]]) -> str:
    lines = sorted(f"{p['id']}\t{p['split']}\t{p['statement_sha256']}" for p in items)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def build() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for slug, field, tier, statement, conclusion, outlook, answer in P:
        items.append({
            "id": f"fy1-{slug}",
            "source": "authored:freshman-textbook-exercise",
            "field": field,
            "tier": tier,
            "tier_basis": "assigned",
            "split": "dev_unseen",
            "language": detect_language(statement),
            "statement": statement,
            "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
            "expected_conclusion": conclusion,
            "mathlib_outlook": outlook,
            "expected_answer": answer,
            "fixed_lean_statement": None,
            "trivial": slug in TRIVIAL,
            "tags": derive_tags(statement),
            "history": [],
        })
    assign_splits(items)
    items.sort(key=lambda p: p["id"])
    return {
        "schema_version": "pals.generation-eval-manifest.v1",
        "version": VERSION,
        "split_salt": SPLIT_SALT,
        "held_out_policy": POLICY,
        "faithfulness_rule": FAITHFULNESS_RULE,
        "problems": items,
        "split_checksum": split_checksum(items),
    }


def validate(manifest: dict[str, Any], frozen: str | None = None) -> list[str]:
    errors: list[str] = []
    items = manifest.get("problems", [])
    errors += [f"duplicate id {i}" for i, n in Counter(p.get("id") for p in items).items() if n > 1]
    errors += [
        "duplicate statement text"
        for _, n in Counter(p.get("statement") for p in items).items()
        if n > 1
    ]
    for p in items:
        pid = p.get("id", "?")
        errors += [f"{pid}: missing {k}" for k in REQUIRED if k not in p]
        if p.get("tier") not in TIERS:
            errors.append(f"{pid}: bad tier")
        if p.get("split") not in SPLITS:
            errors.append(f"{pid}: bad split")
        if p.get("language") not in ("ja", "en"):
            errors.append(f"{pid}: bad language")
        if p.get("mathlib_outlook") not in OUTLOOKS:
            errors.append(f"{pid}: bad mathlib_outlook")
        if any(t not in TAGS for t in p.get("tags", [])):
            errors.append(f"{pid}: unknown tag")
        if p.get("fixed_lean_statement") is not None:
            errors.append(f"{pid}: fixed_lean_statement must be null")
        if not str(p.get("expected_conclusion", "")).strip():
            errors.append(f"{pid}: empty expected_conclusion")
        text = " ".join(
            str(p.get(k) or "") for k in ("statement", "expected_conclusion", "expected_answer")
        )
        if any(b.search(text) for b in BANNED_PATTERNS) or re.search(
            r"binomial_square|square_binomial", pid
        ):
            errors.append(f"{pid}: banned squared-binomial material")
        if hashlib.sha256(p.get("statement", "").encode()).hexdigest() != p.get("statement_sha256"):
            errors.append(f"{pid}: statement_sha256 does not match the text")
        if p.get("history"):
            errors.append(f"{pid}: history must be empty (unused at creation)")
    held = sum(p.get("split") == "held_out" for p in items)
    if items and held != round(len(items) * HELD_OUT_FRACTION):
        errors.append(f"held_out size {held} is not half of {len(items)}")
    if split_checksum(items) != manifest.get("split_checksum"):
        errors.append("split_checksum does not match the problems")
    if frozen is not None and split_checksum(items) != frozen.strip():
        errors.append("split differs from the frozen SPLIT.sha256")
    recomputed = [dict(p) for p in items]
    assign_splits(recomputed)
    if {p["id"]: p["split"] for p in recomputed} != {p["id"]: p["split"] for p in items}:
        errors.append("splits are not the deterministic stratified assignment")
    if "held_out" not in str(manifest.get("held_out_policy", "")):
        errors.append("held_out_policy must be stated in the manifest")
    if not manifest.get("faithfulness_rule"):
        errors.append("faithfulness_rule must be stated in the manifest")
    return errors


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "validate"
    if cmd == "build":
        m = build()
        MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        SPLIT_FILE.write_text(m["split_checksum"] + "\n")
        print(f"wrote {len(m['problems'])} problems, checksum {m['split_checksum']}")
        return 0
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errs = validate(m, SPLIT_FILE.read_text())
    for e in errs:
        print("ERROR:", e)
    items = m["problems"]
    print(
        f"{len(items)} problems; split={dict(Counter(p['split'] for p in items))}; "
        f"tier={dict(Counter(p['tier'] for p in items))}; "
        f"language={dict(Counter(p['language'] for p in items))}; "
        f"field={dict(Counter(p['field'] for p in items))}"
    )
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
