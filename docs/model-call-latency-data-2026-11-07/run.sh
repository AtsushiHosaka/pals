#!/bin/zsh
# usage: run.sh <label> <problems: luna12|terra12> <only (comma ids, or empty for all)> <model> <effort> <max-usd>
# The key comes from the caller's environment or, if unset, from the OPENAI_API_KEY line of the
# project's git-ignored .env.local. It is never printed or written anywhere else.
S=/private/tmp/claude-501/-Users-atsushi-Desktop-projects-personal-pals--claude-worktrees-stacks-project-formalization-d2e49f/9390b54e-2180-4b94-830a-27ee4874a1c1/scratchpad
if [ -z "${OPENAI_API_KEY:-}" ]; then
  OPENAI_API_KEY=$(python3 -I "$S/scripts/read_key.py")
  export OPENAI_API_KEY
fi
if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is empty" >&2
  exit 2
fi
export LEAN_PATH=$(sed -n 's/^export LEAN_PATH=//p' /private/tmp/claude-501/-Users-atsushi-Desktop-projects-personal-pals--claude-worktrees-admiring-dijkstra-b962de/7bbf366c-8bb6-441c-9e7e-5efc84436e55/scratchpad/leanenv.sh)
LEAN_BIN=/Users/atsushi/.elan/toolchains/leanprover--lean4---v4.32.0-rc1/bin/lean
cd "$S/agent"
PYTHONPATH="$S/agent" exec /Users/atsushi/Desktop/projects/personal/pals/pals-agent/.venv/bin/python tools/mathlib_index/hint_ab.py \
  --problems "$S/problems-$2.json" --only "$3" --arms baseline \
  --index-dir "$S/agent" --out "$S/out" --run-label "$1" --model "$4" --effort "$5" \
  --max-repairs 6 --max-usd "$6" \
  --lean ~/.elan/bin/lean --lake ~/.elan/bin/lake --hint-lean "$LEAN_BIN" \
  --lean-project /Users/atsushi/Desktop/projects/personal/pals/pals-agent/lean-workspace \
  --elan-home ~/.elan --scratch "$S/scratch"
