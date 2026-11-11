"""freshman-v1 の検査。`python3 -m pytest docs/generation-eval-freshman-v1` で実行する。"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_freshman_set as b  # noqa: E402

MANIFEST = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
ITEMS = MANIFEST["problems"]
V1 = HERE.parents[1] / "pals-agent" / "testdata" / "generation-eval-v1" / "manifest.json"


def test_manifest_validates_against_frozen_split():
    assert b.validate(MANIFEST, (HERE / "SPLIT.sha256").read_text()) == []


def test_manifest_is_what_the_builder_produces():
    assert b.build() == MANIFEST


def test_counts_and_half_split():
    assert len(ITEMS) == 40
    assert Counter(p["split"] for p in ITEMS) == {"dev_unseen": 20, "held_out": 20}
    assert len({p["field"] for p in ITEMS}) >= 6
    assert {p["language"] for p in ITEMS} == {"ja", "en"}


def test_held_out_policy_is_written():
    assert "held_out" in MANIFEST["held_out_policy"] and "調整" in MANIFEST["held_out_policy"]


def test_no_lean_statement_and_conclusion_is_present():
    assert all(p["fixed_lean_statement"] is None for p in ITEMS)
    assert all(len(p["expected_conclusion"]) >= 8 for p in ITEMS)


def test_squared_binomial_is_banned():
    bad = {**ITEMS[0], "statement": "Expand (x+y)^2.", "statement_sha256": "x"}
    probe = {**MANIFEST, "problems": [bad]}
    assert any("banned" in e for e in b.validate(probe))
    assert not any(
        pat.search(" ".join(str(v) for v in p.values())) for p in ITEMS for pat in b.BANNED_PATTERNS
    )


def test_tampering_with_a_statement_or_split_is_detected():
    t = json.loads(json.dumps(MANIFEST))
    t["problems"][0]["statement"] += " "
    assert b.validate(t)
    t = json.loads(json.dumps(MANIFEST))
    t["problems"][0]["split"] = "dev_unseen" if t["problems"][0]["split"] == "held_out" else "held_out"
    assert b.validate(t)


@pytest.mark.skipif(not V1.exists(), reason="pals-agent submodule not checked out")
def test_disjoint_from_generation_eval_v1():
    v1 = json.loads(V1.read_text(encoding="utf-8"))["problems"]
    assert {p["id"] for p in ITEMS}.isdisjoint(p["id"] for p in v1)
    assert {p["statement_sha256"] for p in ITEMS}.isdisjoint(p["statement_sha256"] for p in v1)
    norm = lambda s: re.sub(r"\s+", "", s.lower())  # noqa: E731
    assert {norm(p["statement"]) for p in ITEMS}.isdisjoint(norm(p["statement"]) for p in v1)
