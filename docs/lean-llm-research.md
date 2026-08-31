# Lean LLM Research for PALS

Updated: 2026-06-19

## Executive Summary

Lean code generation for PALS is feasible, but the highest-probability path is not "fine-tune qwen2.5:3b until it becomes a full prover." The better route is:

1. Build a verifier-centered Draft, Sketch, and Prove pipeline first.
2. Use a frontier or strong managed model for the early draft/sketch baseline.
3. Collect verified PALS traces.
4. Fine-tune a local model only for narrow roles: Lean sketching, next-tactic proposal, compiler-error repair, and possibly premise selection.
5. Move to RL/RFT only after the evaluator and dataset are stable.

Current local state: Ollama has `qwen2.5:3b` and `qwen2.5:0.5b`. These are useful for cheap experiments, but the current Lean-specific literature points more strongly to 4B-8B Lean-specialized provers or Qwen-based distilled provers for practical local work.

PALS should add `.local` alongside `.dev` and `.prod`. In `.local`, default the LLM provider to Ollama so draft/sketch/prove/repair experiments can run without Bedrock token spend. Keep `.dev` for shared AWS resources and `.prod` for production.

Local hardware assumption: only Apple Silicon Mac is available, currently M5 Max with 128 GB unified memory. Local fine tuning should therefore use MLX/MLX-LM and LoRA-style adapters. Do not design the local path around NVIDIA GPUs, CUDA, bitsandbytes, or CUDA-first training tools. The detailed local design is in [Apple Silicon Local LLM Design for PALS](apple-silicon-local-llm.md).

## PALS Context

Relevant repository decisions as of this note:

- `pals` is the private parent/meta repository.
- `pals-agent` is the public OSS LangGraph agent and owns Lean verifier tooling.
- Lean verifier should run as an agent tool/runtime. It may be a sidecar or separate process in production, but source ownership stays in `pals-agent`.
- AWS MVP target is monthly JPY 80,000, scale-to-zero preferred, with Lambda/API Gateway, SQS, Fargate RunTask, Aurora Serverless v2, S3, and Bedrock as the likely baseline.

## Draft, Sketch, and Prove

The method is usually named Draft, Sketch, and Prove (DSP), not "Draft Sketch Proof." The original paper maps informal proofs into formal proof sketches and then uses those sketches to guide an automated prover into easier subproblems. It reports a jump from 20.9% to 39.3% on a competition-problem collection when sketches guide the prover.

Source: [Draft, Sketch, and Prove: Guiding Formal Theorem Provers with Informal Proofs](https://arxiv.org/abs/2210.12283)

For PALS, translate DSP into Lean as:

1. Draft: produce concise natural-language subgoals from the user theorem/problem.
2. Sketch: formalize the subgoals as Lean `have` statements, lemmas, or proof skeletons.
3. Prove: fill each sketch hole using theorem retrieval, tactic search, model samples, and Lean compiler feedback.
4. Repair: feed diagnostics back into the agent until the proof compiles or budget is exhausted.

DSP+ is especially relevant because it revives DSP for modern reasoning models and reports strong results without extra model training. Its changes are directly useful:

- Draft concise subgoals instead of long free-form proof text.
- Autoformalize subgoals with hypotheses during sketching.
- Mask syntactically broken sketch lines before proof search.
- Combine symbolic search such as Aesop with step provers.

Source: [Reviving DSP for Advanced Theorem Proving in the Era of Reasoning Models](https://arxiv.org/abs/2506.11487)

PALS implication: implement DSP+ before investing heavily in fine-tuning. It gives a strong baseline and produces exactly the trace data needed for later SFT/RL.

## Lean-Specific Model Landscape

The research trend is clear: successful Lean provers combine model generation with verifier feedback, retrieval, synthetic data, and repeated search. Pure single-shot code generation is usually not enough.

### LeanDojo / ReProver

LeanDojo provides open tooling, data extraction from Lean, interaction with the proof environment, and ReProver, a retrieval-augmented prover. It is important because PALS will need premise selection from mathlib, not only raw code generation. The paper emphasizes reproducibility and reports that ReProver needed about one GPU-week of training.

Source: [LeanDojo: Theorem Proving with Retrieval-Augmented Language Models](https://arxiv.org/abs/2306.15626)

PALS use: build a local retrieval layer over accessible lemmas, imports, prior PALS proofs, and mathlib docs. This should be part of `agent/tools` rather than baked only into prompts.

### Lean-STaR

Lean-STaR trains models to generate informal thoughts before proof steps, then uses expert iteration on Lean-verified samples. This aligns well with DSP because the draft can become structured proof intent and the proof step can become Lean tactic/code.

Source: [Lean-STaR: Learning to Interleave Thinking and Proving](https://arxiv.org/abs/2407.10040)

PALS use: store visible "proof plan" or "subgoal rationale" fields separately from hidden reasoning. These can become supervised training targets later.

### DeepSeek-Prover

DeepSeek-Prover-V1.5 specializes in Lean 4 with SFT, reinforcement learning from proof assistant feedback, and MCTS-style search. DeepSeek-Prover-V2 uses subgoal decomposition powered by DeepSeek-V3, combines informal and formal reasoning, and reports very high MiniF2F results at the 671B scale.

Sources:

- [DeepSeek-Prover-V1.5](https://arxiv.org/abs/2408.08152)
- [DeepSeek-Prover-V2](https://arxiv.org/abs/2504.21801)

PALS use: copy the pattern, not the scale. Use subgoal decomposition plus verifier-guided repair. Avoid trying to reproduce 671B-scale RL.

### Kimina-Prover and Kimina Lean Server

Kimina-Prover is trained from Qwen2.5-72B with a large RL pipeline and releases distilled 1.5B/7B variants. This is relevant because PALS already has Qwen locally. Kimina Lean Server is also highly relevant: it exposes Lean 4 through a REST API, uses LeanREPL, runs multiple REPL processes, caches imports, and returns tactic states/feedback.

Sources:

- [Kimina-Prover Preview](https://arxiv.org/abs/2504.11354)
- [Kimina Lean Server](https://arxiv.org/abs/2504.21230)

PALS use: evaluate Kimina Lean Server or mirror its API shape for `POST /compile`, `POST /check-syntax`, and `POST /run-tactic`.

### Goedel-Prover-V2

Goedel-Prover-V2 uses scaffolded data synthesis, verifier-guided self-correction, and checkpoint averaging. The 8B model reports very strong pass@32 on MiniF2F and is much more realistic for local or small-cloud experiments than 70B+ models.

Source: [Goedel-Prover-V2](https://arxiv.org/abs/2508.03613)

PALS use: if model weights are available and license-compatible, test an 8B Goedel-style model before training qwen2.5:3b from scratch.

### Leanabell-Prover-V2

Leanabell-Prover-V2 focuses on verifier-integrated RL for 7B models. It directly optimizes multi-turn interactions with Lean feedback and reports gains when post-training existing prover models.

Source: [Leanabell-Prover-V2](https://arxiv.org/abs/2507.08649)

PALS use: this is the most relevant later-stage RL recipe. It requires a stable verifier, trace format, and reward definition first.

### Pythagoras-Prover

Pythagoras-Prover is the most interesting new result for the local route. It reports a 4B and 32B open-source Lean prover family, curriculum SFT, dynamic proof-reasoning filtering, Augmented Lean Formalisation (ALF), and a diffusion-based prover. The 4B result is especially important because it suggests practical local-scale Lean provers are possible if the data pipeline is good.

Source: [Pythagoras-Prover](https://arxiv.org/abs/2606.12594)

PALS use: track release status. If the 4B weights/data are usable, benchmark it before investing in qwen2.5:3b tuning.

## Tuning Local LLMs

### What is realistic

Local tuning can work, but it should target narrow submodules:

- NL theorem/proof -> concise DSP draft subgoals.
- Draft subgoals -> Lean proof sketch with holes or `have` statements.
- Lean diagnostics -> repaired local patch.
- Goal state + retrieved premises -> next tactic candidates.
- Theorem statement -> import/premise shortlist.

Trying to make qwen2.5:3b solve arbitrary Lean/mathlib proofs end-to-end is unlikely to be reliable. It may still become a useful sketcher or repair assistant after LoRA/QLoRA.

### Recommended model candidates

Start with this order:

1. Pythagoras-Prover-4B, if weights are available and usable.
2. Kimina-Prover distilled 7B or 1.5B, if available and usable.
3. Goedel-Prover-V2-8B or DeepSeek-Prover-V2-7B, if available and usable.
4. Qwen2.5-Coder 7B/14B or Qwen3 Coder small/medium variants for code-shaped Lean generation.
5. Existing local `qwen2.5:3b` for the smallest baseline and possibly a LoRA sketcher.

Note: Hugging Face lists `Qwen/Qwen2.5-3B-Instruct` with a `qwen-research` license, while newer Qwen generations may have different licenses. Check license compatibility before using any fine-tuned model outside research/personal use.

Sources:

- [Qwen2.5-3B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [Ollama qwen2.5 library](https://ollama.com/library/qwen2.5)

### Data recipe to copy

Use verifier-gated data creation:

1. Pin Lean, Lake, and mathlib versions.
2. Build a small PALS benchmark from known target theorem types.
3. Add public benchmark/dev data: MiniF2F, ProofNet, LeanDojo/mathlib extracted traces where license-compatible.
4. Generate candidate drafts/sketches/proofs using a strong model.
5. Verify every final proof with Lean.
6. Store failures too: diagnostics, attempted patches, timeout, imports, and retrieved premises.
7. Train on verified positives plus repair pairs, not unfiltered model output.
8. Keep a contamination-safe eval set that is never used for prompt examples or SFT.

Useful public benchmark sources:

- [MiniF2F](https://arxiv.org/abs/2109.00110)
- [ProofNet](https://arxiv.org/abs/2302.12433)
- [LeanDojo benchmark](https://arxiv.org/abs/2306.15626)

### Apple Silicon local training constraint

PALS local tuning is Apple Silicon only:

- Use MLX/MLX-LM for local LoRA experiments.
- Use Ollama for normal `.local` inference.
- Treat QLoRA/bitsandbytes/CUDA recipes as cloud-only or non-local references.
- Prefer `draft_sketch` and `prove_repair` adapters over one monolithic adapter.
- Start from Hugging Face or MLX-compatible weights, not the Ollama GGUF currently installed.
- With 128 GB unified memory, treat 7B/8B adapter training as realistic enough to benchmark seriously; treat 14B as an experimental tier.

### Training stages

Stage A: No training baseline

- Evaluate local `qwen2.5:3b` with Ollama.
- Evaluate one managed frontier/Bedrock model.
- Measure pass@1, pass@8, pass@32, compile success, repair success, average verifier seconds, and token cost.

Stage B: DSP+ implementation

- Build the agent graph around draft -> sketch -> prove -> repair.
- Use Lean verifier feedback as a first-class tool result.
- Use retrieval for imports and theorem names.

Stage C: Apple Silicon LoRA SFT

- Start from HF-format weights, not the Ollama GGUF file.
- Train MLX/MLX-LM adapters for `draft_sketch` and `prove_repair` first.
- Export merged/quantized model to Ollama only after evaluation.
- Compare against the untuned model and against a stronger managed baseline.

Stage D: Expert iteration

- Sample many candidate proofs.
- Keep only Lean-verified successes.
- Add hard negatives and diagnostic repair pairs.
- Repeat SFT.

Stage E: RL/RFT

- Only after the above is stable.
- Reward should be simple at first: compiles, no `sorry`, no `admit`, no timeout, smaller patch, fewer imports, lower verifier cost.
- Leanabell and DeepSeek-Prover patterns become relevant here.

## AWS Cost and Deployment Implications

All costs here are directional and should be recalculated in the AWS Pricing Calculator before implementation. The important architectural point is that always-on GPU hosting conflicts with the JPY 80,000/month MVP guardrail.

### Non-LLM baseline

Lambda/API Gateway/SQS/S3 should be inexpensive for MVP usage. AWS Lambda pricing is request + duration based, includes a free tier, and charges requests at a per-million rate. Fargate bills per second with a 1-minute minimum and charges requested CPU/memory/storage. Aurora Serverless v2 bills ACUs per second, supports starting capacity 0 ACU, and 1 ACU is about 2 GiB memory.

Sources:

- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [Amazon Aurora pricing](https://aws.amazon.com/rds/aurora/pricing/)

Rough verifier example using the AWS Fargate US East example rates shown on the pricing page:

- 1 vCPU, 2 GB memory, 10 minutes/job is about USD 0.008/job before logs, image pull overhead, public IPv4, and storage.
- 1,000 proof jobs/month: about USD 8 for verifier compute.
- 10,000 proof jobs/month: about USD 80 for verifier compute.

This is compatible with the budget if jobs are short and scale-to-zero is preserved.

### Managed model inference

Bedrock on-demand is the cleanest MVP path because it scales with tokens, not idle GPU hours.

Useful current Bedrock examples:

- Qwen3 Coder Next in Asia Pacific Tokyo: USD 0.60 / 1M input tokens, USD 1.44 / 1M output tokens.
- Qwen3 Next 80B A3B in Asia Pacific Tokyo: USD 0.18 / 1M input tokens, USD 1.45 / 1M output tokens.
- DeepSeek v3.2 in Asia Pacific Tokyo: USD 0.74 / 1M input tokens, USD 2.22 / 1M output tokens.
- Claude 3.5 Sonnet public extended access is much more expensive at USD 6 / 1M input and USD 30 / 1M output in listed regions.

Source: [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)

Illustrative DSP job cost for Qwen3 Coder Next Tokyo:

- Assumption: 4 model calls/job, total 32k input tokens and 8k output tokens.
- Cost/job: about USD 0.031.
- 1,000 jobs/month: about USD 31.
- 10,000 jobs/month: about USD 307.

DeepSeek v3.2 Tokyo under the same token shape is about USD 0.042/job. A Claude/Sonnet-class model under the same shape is about USD 0.43/job, which is useful for high-quality baselines but not for high-volume MVP usage.

### Fine-tuning on AWS

Bedrock Reinforcement Fine Tuning is attractive operationally but expensive for experimentation. Bedrock lists Qwen3 32B RFT at USD 80/hour, with fine-tuned inference priced separately. Ten hours is USD 800 before inference; thirty hours is USD 2,400. That is a research expense, not an always-on MVP component.

Source: [Amazon Bedrock pricing, Qwen model customization](https://aws.amazon.com/bedrock/pricing/)

For local/open LoRA training, use spot/on-demand GPU only as batch work and keep it outside the always-on production stack. A small 3B/7B LoRA run can be a one-off experiment; a provisioned endpoint is where costs become dangerous.

### Custom model hosting

Bedrock Custom Model Import charges per Custom Model Unit minute. The page lists USD 0.05718/min in US East/US West and notes that Llama 3.1 8B 128K requires 2 Custom Model Units. That reference point implies about USD 6.86/hour and roughly USD 5,000/month if kept on 24/7. Exact CMUs depend on model architecture and context length.

Source: [Amazon Bedrock Custom Model Import pricing](https://aws.amazon.com/bedrock/pricing/)

PALS implication: do not host a custom local prover 24/7 in AWS during MVP. If self-hosting is needed, use batch windows, scale-to-zero endpoints, or run local inference outside AWS.

## Recommended PALS Plan

1. Build the Lean verifier API first.
   - Endpoints: `POST /compile`, `POST /check-syntax`, `POST /run-tactic`.
   - Capture exit code, diagnostics, normalized goals, elapsed time, timeout, memory, imports, and artifact references.
   - Evaluate Kimina Lean Server before building everything from scratch.

2. Implement DSP+ as the default agent shape.
   - Nodes: retrieve, draft, sketch, compile, prove_subgoal, repair, persist.
   - Use `sorry` only as an internal sketch marker; final accepted proofs must reject `sorry`/`admit`.
   - Mask or drop syntactically broken sketch lines before proof search.

3. Establish a benchmark before training.
   - 50-100 PALS-style theorems.
   - MiniF2F/ProofNet subset if compatible.
   - Metrics: pass@k, no-sorry compile rate, mean verifier seconds, tokens/job, cost/job, repair iterations.

4. Run a model bake-off.
   - `.local`: Ollama `qwen2.5:3b`, split by role with `OLLAMA_DRAFT_MODEL` and `OLLAMA_PROVE_MODEL`.
   - Apple Silicon tuning: MLX/MLX-LM LoRA adapters for `draft_sketch` and `prove_repair`.
   - Managed cheap: Bedrock Qwen3 Coder Next or DeepSeek v3.2.
   - Managed high quality: a frontier model for baseline only.
   - Lean-specialized local/open: Pythagoras/Kimina/Goedel/DeepSeek prover if weights are available.

5. Fine-tune only after traces exist.
   - First target: sketch and repair LoRA.
   - Second target: next-tactic proposal.
   - Later target: verifier-integrated RL or Bedrock RFT.

## Bottom Line

Yes, local LLM tuning is plausible for PALS, but it should be a data flywheel around Lean verification rather than a one-shot model training project. The MVP should use DSP+ with managed models to create reliable traces, then use those traces to tune a small local prover/sketcher. If Pythagoras-Prover-4B or a Kimina/Goedel/DeepSeek 7B-8B model is usable, it is probably a better starting point than teaching `qwen2.5:3b` Lean from scratch.
