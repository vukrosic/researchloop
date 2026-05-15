#!/usr/bin/env bash
set -euo pipefail

goal="reduce validation loss"

out="$(node ./bin/researchloop.js prompt --goal "$goal")"
printf '%s' "$out" | grep -q "$goal"
printf '%s' "$out" | grep -q ".researchloop/AGENTS.md"
printf '%s' "$out" | grep -q ".researchloop/plan.md"
printf '%s' "$out" | grep -q ".researchloop/scratchpad/runs.jsonl"
printf '%s' "$out" | grep -q "Use that history first"
printf '%s' "$out" | grep -q "target explicit"
printf '%s' "$out" | grep -q "Use this folder, point me at a GitHub repo, or spin up a demo research repo?"
printf '%s' "$out" | grep -q "learning-rate or hyperparameter sweeps"
if printf '%s' "$out" | grep -q '{{GOAL}}'; then
  echo "prompt template still has GOAL placeholder" >&2
  exit 1
fi

echo "researchloop test:prompts passed"
