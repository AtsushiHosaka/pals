# Apple Silicon Local LLM Design for PALS

Updated: 2026-06-19

## Decision

PALS local LLM work assumes Apple Silicon only. There is no NVIDIA GPU, CUDA, or bitsandbytes path in the local design.

Current local hardware assumption:

- Apple Silicon: M5 Max.
- Unified memory: 128 GB.

The local stack is:

- Inference for `.local`: Ollama, using local Qwen-compatible models.
- Fine tuning for `.local`: MLX / MLX-LM on Apple Silicon.
- Production/shared baseline: Bedrock or another managed provider in `.dev` and `.prod`.
- Lean correctness: always decided by the Lean verifier, not by model confidence.

Sources:

- [MLX-LM](https://github.com/ml-explore/mlx-lm): Apple Silicon generation and fine-tuning package.
- [Hugging Face PEFT](https://huggingface.co/docs/peft/index): parameter-efficient fine tuning concepts such as LoRA.
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md): local inference and model creation API.
- [Qwen](https://github.com/QwenLM/Qwen3): Qwen family local running and post-training references.

## Non-Goals

- Do not design around NVIDIA GPUs, CUDA kernels, bitsandbytes, Axolotl-on-CUDA, or Unsloth-on-CUDA for local work.
- Do not plan full fine tuning as the first local training step.
- Do not try to train directly inside the currently installed Ollama GGUF model.
- Do not make AWS custom model hosting the local-model deployment path for MVP.

Those paths can exist later as cloud research options, but they are not the local default.

## Local Runtime Roles

Use separate logical roles even when the same base model is used underneath:

- `draft`: natural-language decomposition into proof subgoals.
- `sketch`: Lean skeleton, `have` statements, helper lemmas, and holes.
- `prove`: next tactic or proof-fragment candidates for a specific Lean goal.
- `repair`: local fixes from Lean diagnostics.

The first practical split should be two adapters:

- `draft_sketch`: theorem/problem to structured subgoals and Lean skeleton.
- `prove_repair`: Lean goal/diagnostics/retrieved lemmas to tactic or patch candidates.

Split into four adapters only after enough data exists to justify it.

## Model Policy

Start small and measured:

1. Baseline inference: current Ollama `qwen2.5:3b`.
2. First Apple Silicon tuning target: Qwen 3B/4B adapter training to validate the pipeline.
3. Main local quality target: 7B/8B-class Qwen or Lean-specialized models, because 128 GB unified memory makes this practical enough to benchmark seriously.
4. Stretch target: 14B-class models for inference and possibly small adapter runs if wall-clock time is acceptable.
5. Keep `qwen2.5:0.5b` as a speed/debug model, not a proof-quality target.

RAM-dependent guidance:

- 16 GB unified memory: 0.5B-3B inference, tiny LoRA experiments, short context.
- 24-32 GB: 3B/4B LoRA is the main target; 7B quantized inference may be OK.
- 64 GB+: 7B/8B LoRA becomes plausible.
- Current 128 GB M5 Max: 7B/8B LoRA should be treated as realistic, 14B as an experimental tier, and 30B+ as inference-only or cloud/managed unless benchmarks prove otherwise.

Always benchmark on the actual Mac before committing to a model size. Training that technically runs but takes too long is not useful for PALS iteration.

## Training Backend

Use MLX-LM for local fine tuning because it is built for Apple Silicon and supports low-rank and full-model fine tuning, quantized models, Hugging Face Hub integration, and local conversion/quantization.

Local training artifacts should live under ignored output directories, for example:

```text
outputs/local-training/
  datasets/
  runs/
  adapters/
  evals/
```

Do not commit trained adapters or converted model weights unless the user explicitly asks and the license/storage implications are checked.

## Data Format

Use JSONL records. Keep role-specific datasets separate so each adapter has a clean target.

Draft/sketch example:

```json
{
  "role": "draft_sketch",
  "input": {
    "problem_text": "Prove ...",
    "lean_statement": "theorem ... := by",
    "imports": ["Mathlib"]
  },
  "output": {
    "subgoals": ["Show ...", "Use ..."],
    "lean_sketch": "have h1 : ... := by\n  sorry\n..."
  },
  "meta": {
    "source": "pals",
    "lean_version": "4.x",
    "mathlib_rev": "..."
  }
}
```

Prove/repair example:

```json
{
  "role": "prove_repair",
  "input": {
    "goal_state": "...",
    "local_context": "...",
    "retrieved_lemmas": ["Nat.succ_eq_add_one", "..."],
    "diagnostics": "unknown identifier ..."
  },
  "output": {
    "candidate": "rw [Nat.succ_eq_add_one]\n..."
  },
  "meta": {
    "verified": true,
    "elapsed_ms": 481,
    "attempt_index": 3
  }
}
```

Rules:

- Store visible proof plans, sketches, model outputs, verifier diagnostics, and verified final code.
- Do not store hidden reasoning.
- Keep failed attempts; they are valuable repair data.
- Reject final proofs containing `sorry` or `admit`.
- Pin Lean, Lake, and mathlib versions for every trace.

## Local Training Loop

1. Run DSP+ with `.local` Ollama and one managed baseline.
2. Verify all generated Lean code.
3. Save successful proofs plus failed attempts and diagnostics.
4. Build small role-specific JSONL datasets.
5. Train `draft_sketch` LoRA with MLX-LM.
6. Train `prove_repair` LoRA with MLX-LM.
7. Evaluate pass@1/pass@k, compile rate, repair success, latency, and tokens.
8. Only then merge/export adapters for Ollama use if it improves local evaluation.

The key loop is not "train once and trust it." It is "train, verify, compare, keep or discard."

## Adapter Strategy

Preferred local strategy:

```text
Qwen base model
├── draft_sketch LoRA adapter
└── prove_repair LoRA adapter
```

Operationally:

- During training/evaluation, keep adapters as MLX artifacts.
- For `.local` application runtime, either:
  - call MLX-LM directly for adapter-aware inference, or
  - merge/export a role-specific model and load it with Ollama.
- If Ollama adapter loading is used, validate it with a tiny adapter first before making it the standard path.

Do not assume the existing Ollama `qwen2.5:3b` GGUF is the trainable source. Use Hugging Face or MLX-compatible source weights for training.

## DSP+ Agent Design Under Apple Silicon

The local DSP+ graph should be:

```text
retrieve
  -> draft_model(.local Ollama or MLX draft_sketch adapter)
  -> sketch_model(.local Ollama or MLX draft_sketch adapter)
  -> syntax_check(Lean)
  -> prove_subgoal(.local Ollama or MLX prove_repair adapter)
  -> compile(Lean)
  -> repair(.local Ollama or MLX prove_repair adapter)
  -> persist_trace
```

Budget controls are mandatory:

- cap proof attempts per subgoal;
- cap repair rounds;
- cap generated tokens;
- cache retrieved lemma context;
- cache prompts when MLX-LM is used directly;
- record latency and success by role/model/adapter.

## Cost Implications

Local Apple Silicon inference and LoRA training have no cloud token or GPU rental cost, but they still have opportunity cost:

- slower experiments than managed frontier models;
- memory pressure on the Mac;
- long-running training jobs can make the laptop unpleasant to use;
- quality may lag behind managed models until enough verified traces exist.

Use managed models strategically:

- for bootstrapping high-quality traces;
- for hard proof jobs;
- for periodic baseline comparisons.

Use local models:

- for cheap iteration;
- for repeated prove/repair candidate generation;
- for offline development;
- for role-specific adapters after verified data accumulates.

## Initial Milestones

1. Keep `.local` inference on Ollama `qwen2.5:3b`.
2. Add trace persistence for draft/sketch/prove/repair attempts.
3. Build a 50-problem local benchmark.
4. Train a tiny `draft_sketch` MLX-LM LoRA on 100-500 verified or curated examples.
5. Train a tiny `prove_repair` MLX-LM LoRA on verified goal/diagnostic pairs.
6. Repeat the same adapter run on a 7B/8B candidate if the 3B/4B run improves over baseline.
7. Compare against untuned `qwen2.5:3b`, the 7B/8B candidate, and a Bedrock baseline.
8. Only promote an adapter if it improves verified compile success or reduces attempts without increasing false confidence.

## Bottom Line

With only an Apple Silicon Mac, local fine tuning is still possible, but the design must be MLX-first and LoRA-first. The goal is not to create a giant local prover. The goal is to create small role-specific adapters that make DSP+ cheaper and more reliable while Lean remains the judge.
