"""Pre-registered scheme-theory measurement: Terra (release defaults: medium), repair cap 6, three arms.

usage: ag_eval.py --ws WS --cards cards.json --arm a|b|c --out OUT [--only id,id] [--spent spent.json]

The harness never changes after pre-registration; per-run records are appended to OUT/rows.jsonl.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
sys.path.append(str(SCRATCH / "idx"))  # tools.stacks_index (PR #72); appended so its older pals_agent never shadows

from pals_agent.artifacts import FileArtifactStore
from pals_agent.explanations import LeanProofSemanticReviewer
from pals_agent.generator import HybridLeanGenerator
from pals_agent.http_transport import HardDeadlineHttpTransport
from pals_agent.lean import LeanVerifier
from pals_agent.lean_profiles import build_profile_verifiers
from pals_agent.lean_target import extract_single_target_declaration
from pals_agent.model_roles import ModelRole, fixed_model_default
from pals_agent.openai import OpenAIResponsesClient
from pals_agent.pipeline import ProofPipeline
from tools.stacks_index.search import (
    StacksIndex,
    lean_query_terms,
    natural_query_terms,
    reciprocal_rank_fusion,
)

# gpt-6.1-terra has no rate in the repo; gpt-5.6-terra's ($2.5 / $12 per 1M tokens) is the proxy.
RATE_IN, RATE_OUT = 2.5 / 1e6, 12.0 / 1e6
RUN_CAP_USD = 1.0
TOTAL_CAP_USD = 10.0
MAX_REPAIRS = 6
NOTE_K = 12
ARMS = {
    "a": ("stacks-4.35", {}),
    "b": ("stacks-frontier-4.35", {"PALS_LEAN_ALLOW_FRONTIER_PROOFS": "true"}),
    "c": ("stacks-frontier-defs-4.35", {"PALS_LEAN_ALLOW_FRONTIER_STATEMENTS": "true"}),
}
KEY = next(
    line.split("=", 1)[1].strip().strip('"')
    for line in Path("/Users/atsushi/Desktop/projects/personal/pals/.env.local").read_text().splitlines()
    if line.startswith("OPENAI_API_KEY=")
)


class Budget(Exception):
    pass


@dataclass
class Meter:
    inp: int = 0
    out: int = 0
    calls: int = 0

    @property
    def usd(self) -> float:
        return self.inp * RATE_IN + self.out * RATE_OUT


@dataclass
class Recording:
    meter: Meter
    spent_file: Path
    inner: HardDeadlineHttpTransport = field(default_factory=HardDeadlineHttpTransport)

    def request(self, **kw):
        total = json.loads(self.spent_file.read_text())["usd"] if self.spent_file.exists() else 0.0
        if self.meter.usd >= RUN_CAP_USD or total + self.meter.usd >= TOTAL_CAP_USD:
            raise Budget("budget cap reached")
        response = self.inner.request(**kw)
        try:
            usage = json.loads(response.body).get("usage") or {}
            self.meter.inp += usage.get("input_tokens", 0)
            self.meter.out += usage.get("output_tokens", 0)
            self.meter.calls += 1
        except Exception:  # noqa: BLE001
            pass
        return response


VERIFY_LOG: ContextVar[list | None] = ContextVar("verify_log", default=None)
_orig_verify = LeanVerifier.verify


def _timed_verify(self, *args, **kwargs):
    start = time.monotonic()
    result = _orig_verify(self, *args, **kwargs)
    log = VERIFY_LOG.get()
    if log is not None:
        log.append(
            {
                "s": round(time.monotonic() - start, 2),
                "ok": bool(result.success),
                "codes": [d.code for d in result.diagnostics if d.severity == "error"][:4],
            }
        )
    return result


LeanVerifier.verify = _timed_verify  # type: ignore[method-assign]


def retrieval_note(index: StacksIndex, built: set[str], card: dict, arm: str) -> str:
    terms = natural_query_terms(card["nl"]) + lean_query_terms(card["formal"])
    scope = "core" if arm == "a" else "all"
    ranked = [
        index.text_search(terms, k=80, scope=scope, include_upstream=False),
        index.symbol_search_lean(card["formal"], k=80, scope=scope),
    ]
    fused = reciprocal_rank_fusion(ranked, k=120)
    picked = []
    for candidate in fused:
        row = index.describe([candidate.name])
        if not row:
            continue
        row = row[0]
        if row["kind"] not in ("theorem", "lemma", "def", "abbrev", "instance", "structure", "class"):
            continue
        if row["trust"] == "frontier" and row["module"] not in built:
            continue
        picked.append(row)
        if len(picked) >= NOTE_K:
            break
    lines = [
        f"  [{r['trust']}] {r['module']} :: {r['kind']} {r['name']} {(r['type'] or '').replace(chr(10), ' ')[:260]}"
        for r in picked
    ]
    head = {
        "a": "Lean 4.35 with Mathlib and the reviewed StacksCore only. Use `import Mathlib`.",
        "b": (
            "Lean 4.35 with Mathlib and StacksCore. A PROOF may also `import` the StacksFrontier modules named "
            "below and use their lemmas; the statement is fixed and uses only Lean, Mathlib or StacksCore names."
        ),
        "c": (
            "Lean 4.35 with Mathlib and StacksCore. The statement is fixed and may use StacksFrontier definitions; "
            "the proof may `import` the StacksFrontier modules named below."
        ),
    }[arm]
    return (
        "\n\n[Library note]\n" + head + " No `sorry`, no new axioms, no `native_decide`.\n"
        "Candidate declarations found by keyword search (unverified; names/signatures may not fit):\n"
        + "\n".join(lines)
        + "\n"
    )


def target_text(card: dict) -> str:
    return card["nl"]


def run() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws", required=True)
    parser.add_argument("--cards", required=True)
    parser.add_argument("--arm", required=True, choices=sorted(ARMS))
    parser.add_argument("--out", required=True)
    parser.add_argument("--only", default="")
    parser.add_argument("--spent", required=True)
    parser.add_argument("--built", default=str(SCRATCH / "imp" / "s2_closure.json"))
    parser.add_argument("--index", default=str(SCRATCH / "idx-out"))
    args = parser.parse_args()
    ws, out, spent_file = Path(args.ws), Path(args.out), Path(args.spent)
    out.mkdir(parents=True, exist_ok=True)
    cards = json.load(open(args.cards, encoding="utf-8"))
    if isinstance(cards, dict):  # the committed cards file keeps the list under "cards"
        cards = cards["cards"]
    only = set(filter(None, args.only.split(",")))
    built = set(json.load(open(args.built)))
    index = StacksIndex(Path(args.index) / "index.sqlite")
    profile, env = ARMS[args.arm]
    opts = dict(
        timeout_seconds=300,
        child_path="/Users/atsushi/.elan/bin:/usr/bin:/bin",
        elan_home="/Users/atsushi/.elan",
        scratch_dir=out / "scratch",
    )
    (out / "scratch").mkdir(exist_ok=True)
    default_v = LeanVerifier(project_dir=ws, **opts)
    router = build_profile_verifiers(
        default_verifier=default_v, workspaces={profile: ws}, environ=env, **opts
    )
    binding = fixed_model_default(ModelRole.DRAFT)
    review_binding = fixed_model_default(ModelRole.PROOF_REVIEW)
    for card in cards:
        if only and card["id"] not in only:
            continue
        total = json.loads(spent_file.read_text())["usd"] if spent_file.exists() else 0.0
        if total >= TOTAL_CAP_USD - 0.4:
            print(f"STOP before {card['id']}: spent {total:.3f} of {TOTAL_CAP_USD}", flush=True)
            break
        meter = Meter()
        review_meter = Meter()
        transport = Recording(meter, spent_file)
        client = OpenAIResponsesClient(api_key=KEY, timeout_seconds=300, transport=transport)
        generator = HybridLeanGenerator(
            model=binding.model, provider=binding.provider, openai=client, use_release_role_bindings=True
        )
        pipe = ProofPipeline(
            generator=generator,
            verifier=default_v,
            artifact_store=FileArtifactStore(out / "art" / f"{card['id']}-{args.arm}"),
            profile_verifiers=router,
            max_repair_attempts=MAX_REPAIRS,
        )
        note = retrieval_note(index, built, card, args.arm)
        log: list = []
        token = VERIFY_LOG.set(log)
        started = time.monotonic()
        error = None
        result = None
        try:
            result = pipe.run_statement(
                statement=target_text(card) + note,
                formal_statement=card["formal"],
                proof_job_id=f"ag-{card['id']}-{args.arm}",
                library_profile=profile,
            )
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {str(exc)[:200]}"
        wall = time.monotonic() - started
        VERIFY_LOG.reset(token)
        row = {
            "id": card["id"],
            "group": card["group"],
            "arm": args.arm,
            "profile": profile,
            "wall_s": round(wall, 1),
            "lean_s": round(sum(v["s"] for v in log), 1),
            "verify_calls": log,
            "model_calls": meter.calls,
            "in_tok": meter.inp,
            "out_tok": meter.out,
            "gen_usd": round(meter.usd, 4),
            "error": error,
            "load_1m": __import__("os").getloadavg()[0],
        }
        if result is not None:
            code = result.generated.lean_code
            row.update(
                state=result.state,
                first_attempt_ok=result.model_attempt_success,
                codes=[d.code for d in result.verification.diagnostics],
                trust=[
                    d.metadata for d in result.verification.diagnostics if d.metadata and "trust_level" in d.metadata
                ],
                imports_frontier=bool(re.search(r"^import StacksFrontier", code, re.M)),
                has_sorry_text=bool(re.search(r"\bsorry\b", code)),
            )
            (out / f"{card['id']}-{args.arm}.lean").write_text(code, encoding="utf-8")
            attempts_dir = out / "art" / f"{card['id']}-{args.arm}" / f"ag-{card['id']}-{args.arm}" / "attempts"
            row["attempts"] = len(list(attempts_dir.glob("*.json"))) if attempts_dir.exists() else None
            row["repairs_used"] = None if row["attempts"] is None else max(0, row["attempts"] - 1)
            if result.state == "verified":
                review_start = time.monotonic()
                review_client = OpenAIResponsesClient(
                    api_key=KEY, timeout_seconds=300, transport=Recording(review_meter, spent_file)
                )
                reviewer = LeanProofSemanticReviewer(
                    client=review_client, model=review_binding.model, provider=review_binding.provider
                )
                try:
                    target = extract_single_target_declaration(code)
                    if target is None:
                        row["review"] = "no_single_target"
                    else:
                        decision = reviewer.review_proof(
                            theorem_statement=card["nl"],
                            formal_statement=card["formal"],
                            target_declaration=target,
                            lean_code=code,
                        )
                        row["review"] = decision.decision
                        row["review_rationale"] = decision.rationale[:600]
                except Exception as exc:  # noqa: BLE001
                    row["review"] = f"error:{type(exc).__name__}"
                row["review_s"] = round(time.monotonic() - review_start, 1)
                row["review_usd"] = round(review_meter.usd, 4)
        row["usd"] = round(meter.usd + review_meter.usd, 4)
        with open(out / "rows.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        total = (json.loads(spent_file.read_text())["usd"] if spent_file.exists() else 0.0) + row["usd"]
        spent_file.write_text(json.dumps({"usd": round(total, 4)}))
        print(
            json.dumps(
                {k: row.get(k) for k in ("id", "arm", "state", "review", "wall_s", "lean_s", "model_calls", "usd", "error")},
                ensure_ascii=False,
            ),
            f"spent={total:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    run()
