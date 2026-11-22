#!/usr/bin/env python3
"""pals#381: 修復2回以上の題の、最初の失敗の Lean 診断を種類で数える。

2段階。生データ（Lean 本文を含むので git に入れない）は `extract` だけが読む。
  extract  records.jsonl と、第1候補の再コンパイル結果（classify_*.json）から、
           診断の見出し（テンプレートの語句だけ。goal・Lean 本文は捨てる）と修復回数の CSV を作る。
  table    その CSV から件数の表（Markdown）を出す。git 上の CSV だけで再現できる。

  python3 first_failure_diagnosis.py extract --raw <t2-lane> --out first_failure_diagnosis.csv
  python3 first_failure_diagnosis.py table --csv first_failure_diagnosis.csv

held_out は読まない。実行は有料の呼び出しをしない（保存済みの記録を読むだけ）。
"""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

# (run のディレクトリ, 再コンパイルの run 名)。cheap-first と cheap-patch の dev_unseen 20題 各2回 = 80題・回。
# 初回の候補は同じ構成なので、journal の「80題・回」と同じ集合。tuning は別集計。
RUNS = [
    ("fix1/cheap_dev20", "cheap_dev20", "dev_unseen"),
    ("fix1/cheap_dev20_b", "cheap_dev20_b", "dev_unseen"),
    ("fix2/cp1_dev20_a", "cp1_dev20_a", "dev_unseen"),
    ("fix2/cp1_dev20_b", "cp1_dev20_b", "dev_unseen"),
    ("fix1/cheap_tuning14", "cheap_tuning14", "tuning"),
    ("fix2/cp1_tuning14", "cp1_tuning14", "tuning"),
]
# 診断の見出し（goal や識別子を含まない先頭の語句だけを残す）
HEADS = [
    (r"^Unknown (identifier|constant)", "unknown_name"),
    (r"^unknown (namespace|identifier)", "unknown_name"),
    (r"^Type mismatch", "type_mismatch"),
    (r"^Application type mismatch", "type_mismatch"),
    (r"^(failed to synthesize|typeclass instance)", "type_mismatch"),
    (r"^unsolved goals", "unsolved_goals"),
    (r"^`exact\?` could not close", "exact_open"),
    (r"^`?simp`? made no progress", "simp_no_progress"),
    (r"^(linarith|nlinarith|positivity) failed", "linarith_failed"),
    (r"^omega could not", "omega_failed"),
    (r"^Tactic `rfl` failed", "rfl_failed"),
    (r"^(unexpected token|expected )", "syntax"),
]
# 種類（issue #381 の語彙）への対応。形式化の誤り・import の不足は診断だけでは判定できない。
KIND = {
    "unknown_name": "存在しない補題名・定数",
    "type_mismatch": "型の不一致・引数・instance",
    "unsolved_goals": "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "exact_open": "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "simp_no_progress": "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "linarith_failed": "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "omega_failed": "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "rfl_failed": "その他（rfl が定義上の等式にならない）",
    "syntax": "その他（構文）",
    "other": "その他",
}
KIND_ORDER = [
    "存在しない補題名・定数",
    "型の不一致・引数・instance",
    "tactic が閉じない（simp・linarith・omega・exact?・未解決の goal）",
    "命題の形式化の誤り",
    "import の不足",
    "その他（構文）",
    "その他（rfl が定義上の等式にならない）",
    "その他",
]
FIELDS = ["set", "run", "problem_id", "repairs", "verified", "first_ok", "first_head", "n_errors"]


def head_of(msg):
    for pat, name in HEADS:
        if re.search(pat, msg.strip()):
            return name
    return "other"


def extract(raw, out):
    raw = Path(raw)
    rows = []
    for d, name, s in RUNS:
        cls = {i["problem_id"]: i for i in json.load(open(raw / "classify_cheap_first_failures.json")) if i["run"] == name}
        for line in open(raw / d / "records.jsonl"):
            r = json.loads(line)
            c = cls.get(r["problem_id"])
            head = ""
            if not r["first_attempt_ok"]:
                if not c or not c["errors"]:
                    head = "missing"
                else:
                    head = head_of(c["errors"][0]["message"])
            rows.append(dict(set=s, run=name, problem_id=r["problem_id"], repairs=r.get("repairs") or 0,
                             verified=int(bool(r["verified"])), first_ok=int(bool(r["first_attempt_ok"])),
                             first_head=head, n_errors=(c or {}).get("n_errors", "")))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")


def table(path):
    rows = list(csv.DictReader(open(path)))
    out = []
    for s in ("dev_unseen", "tuning"):
        rs = [r for r in rows if r["set"] == s]
        out.append(f"\n### {s}（{len(rs)} 題・回、{len({r['run'] for r in rs})} 回）\n")
        ff = [r for r in rs if r["first_ok"] == "0"]
        r2 = [r for r in ff if int(r["repairs"]) >= 2]
        r1 = [r for r in ff if int(r["repairs"]) == 1]
        r0 = [r for r in ff if int(r["repairs"]) == 0]
        out.append(f"初回失敗 {len(ff)} 件（修復2回以上 {len(r2)}、1回 {len(r1)}、0回 {len(r0)}）\n")
        cnt = {k: Counter() for k in ("r2", "r1", "all")}
        for r in ff:
            k = KIND[r["first_head"]] if r["first_head"] in KIND else "診断なし"
            cnt["all"][k] += 1
            if int(r["repairs"]) >= 2: cnt["r2"][k] += 1
            elif int(r["repairs"]) == 1: cnt["r1"][k] += 1
        out.append("| 最初の失敗の種類 | 修復2回以上 | 修復1回 | 初回失敗の全体 |\n|---|---|---|---|")
        for k in KIND_ORDER + ["診断なし"]:
            if any(cnt[x][k] for x in cnt) or k in KIND_ORDER[:5]:
                tag = "（診断から判定不能）" if k in ("命題の形式化の誤り",) else ""
                out.append(f"| {k}{tag} | {cnt['r2'][k]} | {cnt['r1'][k]} | {cnt['all'][k]} |")
        out.append(f"| 計 | {len(r2)} | {len(r1)} | {len(ff)} |")
        by = defaultdict(list)
        for r in r2: by[r["problem_id"]].append(r)
        if by:
            out.append("\n修復2回以上の題ごと（件数・最初の失敗の種類・修復回数）:\n\n| 題 | 件数 | 最初の失敗の診断 | 修復回数 |\n|---|---|---|---|")
            for p, v in sorted(by.items(), key=lambda x: -len(x[1])):
                out.append(f"| {p} | {len(v)} | {', '.join(sorted({x['first_head'] for x in v}))} | {', '.join(x['repairs'] for x in v)} |")
    print("\n".join(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("--raw", required=True); e.add_argument("--out", required=True)
    t = sub.add_parser("table"); t.add_argument("--csv", required=True)
    a = ap.parse_args()
    extract(a.raw, a.out) if a.cmd == "extract" else table(a.csv)
