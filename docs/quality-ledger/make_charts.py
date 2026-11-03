#!/usr/bin/env python3
"""Regenerate the quality-ledger charts from ledger.csv.

Usage (from the repository root):
    python docs/quality-ledger/make_charts.py

Needs only the standard library, pandas and matplotlib. Writes light and dark PNGs to
docs/quality-ledger/charts/. No network access, no model calls.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.csv"
OUT = HERE / "charts"

# Palette: the validated categorical slots 1-5 (adjacent-pair CVD and normal-vision checks pass in
# both modes). Dark mode uses its own steps of the same hues, not an automatic flip.
THEMES = {
    "light": {
        "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e3e2de",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"], "neutral": "#8a8982",
    },
    "dark": {
        "surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "grid": "#383835",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"], "neutral": "#8a8982",
    },
}
TAG_ORDER = ["infra", "verifier", "model", "review", "policy-refusal"]  # fixed slot order
TAG_NA = "n/a"


def tag_of(code: str) -> str:
    head = code.split(".")[0]
    return {"infra": "infra", "verifier": "verifier", "model": "model", "review": "review",
            "policy": "policy-refusal", "retrieval": "model"}.get(head, TAG_NA)


def load() -> pd.DataFrame:
    df = pd.read_csv(LEDGER, dtype={"overlap_with": str})
    df["date"] = pd.to_datetime(df["date"])
    df["overlap_with"] = df["overlap_with"].fillna("")
    df["failures"] = df["failures_json"].apply(lambda s: json.loads(s) if isinstance(s, str) and s else {})
    return df


FAMILIES = {"answer_latency", "recipe_retrieval", "exact_precheck", "statement_index", "lean_runtime",
            "proof_generation", "guest_quality", "catalog_audit", "load_test", "feature_audit",
            "availability", "other"}


def validate(df: pd.DataFrame) -> list[str]:
    """Return a list of problems found in ledger.csv (empty when the ledger is consistent)."""
    taxonomy = (HERE / "taxonomy.md").read_text(encoding="utf-8")
    codes = set(re.findall(r"^\| `([a-z]+\.[a-z_0-9]+|unclassified)`", taxonomy, flags=re.M))
    codes.add("unclassified")
    errors = []
    for _, r in df.iterrows():
        rid = r["id"]
        if r["family"] not in FAMILIES:
            errors.append(f"{rid}: unknown family {r['family']!r}")
        if pd.isna(r["source"]) or not str(r["source"]).strip():
            errors.append(f"{rid}: source is empty")
        if pd.notna(r["success_rate"]) and not 0 <= r["success_rate"] <= 1:
            errors.append(f"{rid}: success_rate outside 0..1")
        if pd.notna(r["n"]) and pd.notna(r["successes"]) and r["successes"] > r["n"]:
            errors.append(f"{rid}: successes > n")
        for code in r["failures"]:
            if code not in codes:
                errors.append(f"{rid}: failure code {code!r} is not in taxonomy.md")
    for rid in df.loc[df["id"].duplicated(), "id"]:
        errors.append(f"{rid}: duplicate id")
    known = set(df["id"])
    for _, r in df.iterrows():
        for other in filter(None, r["overlap_with"].split(";")):
            if other not in known:
                errors.append(f"{r['id']}: overlap_with refers to unknown id {other!r}")
    return errors


def style(theme: dict) -> None:
    plt.rcParams.update({
        "figure.facecolor": theme["surface"], "axes.facecolor": theme["surface"],
        "savefig.facecolor": theme["surface"], "text.color": theme["ink"],
        "axes.labelcolor": theme["ink2"], "xtick.color": theme["ink2"], "ytick.color": theme["ink2"],
        "axes.edgecolor": theme["grid"], "axes.grid": True, "axes.axisbelow": True, "grid.color": theme["grid"],
        "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "legend.frameon": False,
    })


def fmt_dates(ax, dates=None) -> None:
    if dates is not None and len(dates):
        pad = pd.Timedelta(days=2)
        ax.set_xlim(dates.min() - pad, dates.max() + pad)
    loc = mdates.AutoDateLocator(minticks=3, maxticks=5)
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))


def chart_success(df: pd.DataFrame, theme: dict, path: Path) -> None:
    d = df[df["success_rate"].notna() & df["n"].notna() & (df["overlap_with"] == "")]
    fams = [f for f, g in d.groupby("family") if len(g) >= 3]
    fams.sort(key=lambda f: -len(d[d["family"] == f]))
    cols = 3
    rows = -(-len(fams) // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(11, 2.9 * rows), sharey=True, squeeze=False)
    for ax in axes.flat[len(fams):]:
        ax.axis("off")
    for ax, fam in zip(axes.flat, fams):
        g = d[d["family"] == fam].sort_values("date")
        ax.scatter(g["date"], g["success_rate"], s=10 + 4 * g["n"].clip(upper=100) ** 0.5 * 3,
                   color=theme["series"][0], edgecolor=theme["surface"], linewidth=1.2, zorder=3)
        ax.set_title(f"{fam}  (k={len(g)})", loc="left")
        ax.set_ylim(-0.04, 1.04)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        fmt_dates(ax, g["date"])
    fig.suptitle("Success rate over time, by experiment family", x=0.01, ha="left", fontsize=12,
                 fontweight="bold", color=theme["ink"])
    fig.text(0.01, 0.945, "Each dot is one ledger row (marker size grows with n; dots are not connected). Rows in a panel are different "
             "datasets and metrics: read trends only within one experiment series, never across the whole panel.",
             ha="left", va="top", color=theme["ink2"], fontsize=8.5, wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def chart_failures(df: pd.DataFrame, theme: dict, path: Path) -> None:
    d = df[df["overlap_with"] == ""]
    events, rows_with = Counter(), Counter()
    for fails in d["failures"]:
        for code, k in fails.items():
            rows_with[code] += 1
            events[code] += int(k or 0)
    codes = sorted(rows_with, key=lambda c: (-events[c], c))[::-1]  # biggest at the top
    colors = {t: theme["series"][i] for i, t in enumerate(TAG_ORDER)}
    colors[TAG_NA] = theme["neutral"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 0.34 * len(codes) + 2.0), sharey=True)
    for ax, data, title in ((a1, rows_with, "Ledger rows in which the code occurs"),
                            (a2, events, "Failure events (sum of counts; repeated runs inflate this)")):
        vals = [data[c] for c in codes]
        ax.barh(codes, vals, color=[colors[tag_of(c)] for c in codes], height=0.62)
        for y, v in enumerate(vals):
            ax.text(v, y, f" {v}", va="center", color=theme["ink2"], fontsize=8)
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, max(vals) * 1.15)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[t]) for t in TAG_ORDER + [TAG_NA]]
    fig.legend(handles, TAG_ORDER + [TAG_NA], loc="lower center", ncol=6, fontsize=8.5)
    fig.suptitle("Failures by taxonomy code (colour = tag)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def chart_cost_latency(df: pd.DataFrame, theme: dict, path: Path) -> None:
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True)
    c = df[df["cost_usd"].notna() & (df["cost_usd"] > 0)]
    own, agg = c[c["overlap_with"] == ""], c[c["overlap_with"] != ""]
    a1.scatter(own["date"], own["cost_usd"], s=36, color=theme["series"][0], edgecolor=theme["surface"],
               linewidth=1.2, label="one run or campaign", zorder=3)
    a1.scatter(agg["date"], agg["cost_usd"], s=36, facecolor="none", edgecolor=theme["series"][0],
               linewidth=1.4, label="aggregate that overlaps other rows", zorder=3)
    a1.set_yscale("log")
    a1.set_ylabel("USD (list-price estimate)")
    a1.set_title("Cost per ledger row (log scale)", loc="left")
    a1.legend(loc="upper left", fontsize=8.5)
    lat = df[df["latency_p50_s"].notna() & (df["latency_p50_s"] > 0) & (df["overlap_with"] == "")]
    fams = [f for f, _ in Counter(lat["family"]).most_common(5)]
    for i, fam in enumerate(fams):
        g = lat[lat["family"] == fam]
        a2.scatter(g["date"], g["latency_p50_s"], s=34, color=theme["series"][i], edgecolor=theme["surface"],
                   linewidth=1.2, label=f"{fam} (k={len(g)})", zorder=3)
    a2.set_yscale("log")
    a2.set_ylabel("seconds (p50 or stated median)")
    a2.set_title("Latency p50 per ledger row (log scale; units of work differ by family)", loc="left")
    a2.legend(loc="upper left", fontsize=8.5, ncol=2)
    fmt_dates(a2, pd.concat([c["date"], lat["date"]]))
    a1.set_xlim(a2.get_xlim())
    fig.suptitle("Cost and latency over time", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    df = load()
    problems = validate(df)
    if problems:
        print("ledger.csv has problems:", *problems, sep="\n  - ")
        sys.exit(1)
    OUT.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        style(theme)
        chart_success(df, theme, OUT / f"success_rate_by_family_{name}.png")
        chart_failures(df, theme, OUT / f"failure_breakdown_{name}.png")
        chart_cost_latency(df, theme, OUT / f"cost_latency_over_time_{name}.png")
    print(f"wrote {len(list(OUT.glob('*.png')))} PNGs to {OUT} from {len(df)} ledger rows")


if __name__ == "__main__":
    main()
