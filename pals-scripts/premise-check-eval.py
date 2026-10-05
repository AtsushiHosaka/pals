#!/usr/bin/env python3
"""Evaluate the proof-request premise check (PFR-014) against the real provider.

Runs only the assessment step (no catalog, API, database or Lean). It needs the pals-agent
package on PYTHONPATH and OPENAI_API_KEY in the environment; it never prints the key.
Each case states whether the learner should be asked first ("ask") or not ("ready").
Results: docs/premise-check-evaluation-2026-10-05.md.
"""

import concurrent.futures
import json
import sys
from dataclasses import dataclass, replace

from pals_agent.openai import OpenAIResponsesClient
from pals_agent.proof_reuse import ProofReuseRuntime
from pals_agent.settings import AgentSettings

AS_WRITTEN_Q = ("As stated, this seems to fail for n = 0, where n^2 + n = 0 is even. "
                "Which claim do you mean?")
FIELD_Q = "Over which field is the vector space defined?"
CASES = [
    ("F1", "ask", "en", "Prove that for every natural number n, n^2 + n is odd.", []),
    ("F2", "ask", "en", "Show that x/x = 1 for every real number x.", []),
    ("F3", "ask", "ja", "すべての実数 x について、√(x²) = x であることを示せ。", []),
    ("F4", "ask", "en", "Prove that every continuous function f: ℝ → ℝ is differentiable.", []),
    ("A1", "ask", "en", "Prove that every linear operator on a finite-dimensional nonzero vector space has an eigenvalue.", []),
    ("A2", "ask", "ja", "有限次元ベクトル空間上の線形写像は固有値をもつことを示せ。", []),
    ("A3", "ask", "en", "Prove that x^2 + 1 has no roots.", []),
    ("R0", "ready", "en", "Show that a^2 ≥ 0.", []),
    ("R1", "ready", "en", "Prove that the kernel of a linear map is a subspace.", []),
    ("R2", "ready", "ja", "x²が実数全体で連続であることを示してください。", []),
    ("R3", "ready", "en", "Prove that for every natural number n, n^2 + n is even.", []),
    ("R4", "ready", "en", "Prove that the sum of two odd integers is even.", []),
    ("R5", "ready", "en", "Prove that there are infinitely many primes.", []),
    ("R6", "ready", "en", "Show that 0.999... = 1.", []),
    ("F5", "ask", "en", "Prove that every prime number is odd.", []),
    ("F6", "ask", "en", "Prove that 2^n > n^2 for every natural number n.", []),
    ("F7", "ask", "ja", "無理数どうしの積は無理数であることを示せ。", []),
    ("R7", "ready", "en", "Prove that every bounded monotone sequence of real numbers converges.", []),
    ("R8", "ready", "en", "Prove that the square root of 2 is irrational.", []),
    ("R9", "ready", "en", "Prove that the identity element of a group is unique.", []),
    ("R10", "ready", "en", "Prove the triangle inequality |a + b| <= |a| + |b|.", []),
    ("R11", "ready", "en", "Prove that if n^2 is even then n is even.", []),
    ("R12", "ready", "ja", "微分可能な関数は連続であることを示せ。", []),
    ("R13", "ready", "en", "Prove that every finite integral domain is a field.", []),
    ("C1", "ready", "en", "Prove that for every natural number n, n^2 + n is odd.",
     [{"question_id": "q1", "question": AS_WRITTEN_Q, "answer": "Prove the statement as written"}]),
    ("C2", "ready", "en", "Prove that every linear operator on a finite-dimensional nonzero vector space has an eigenvalue.",
     [{"question_id": "q1", "question": FIELD_Q, "answer": "Over the complex numbers"}]),
]


class Stop(Exception):
    pass


class Catalog:
    profiles = ("generic-v1",)

    def retrieve(self, statement, profile_id, *, deadline):
        raise Stop(statement)


@dataclass(frozen=True)
class Recording(OpenAIResponsesClient):
    sink: list | None = None

    def generate(self, **kwargs):
        raw = super().generate(**kwargs)
        self.sink.append(raw)
        return raw


def run(case):
    ident, expected, language, statement, turns = case
    settings = AgentSettings.from_env()
    sink: list = []
    client = Recording(api_key=settings.openai_api_key, base_url=settings.openai_base_url,
                       max_output_tokens=6000, sink=sink)
    engine = ProofReuseRuntime(client=client, catalog=Catalog())
    try:
        result = engine.answer({"statement": statement, "output_language": language,
                                "context_turns": turns})
        outcome = result.outcome
        error = result.error_code
    except Stop:
        outcome, error = "ready", None
    preflight = json.loads(sink[0]) if sink else None
    actual = "ask" if outcome == "needs_input" else outcome
    return {"id": ident, "expected": expected, "actual": actual, "error": error,
            "ok": actual == expected, "preflight": preflight}


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run, CASES))
    for r in results:
        p = r["preflight"] or {}
        q = (p.get("question") or {})
        print(json.dumps({"id": r["id"], "ok": r["ok"], "expected": r["expected"], "actual": r["actual"],
                          "error": r["error"], "question": q.get("text"), "options": q.get("options"),
                          "statement": p.get("statement"),
                          "premise_check": p.get("premise_check")}, ensure_ascii=False))
    print(json.dumps({"passed": sum(r["ok"] for r in results), "total": len(results)}))
