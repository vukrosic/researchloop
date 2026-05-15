#!/usr/bin/env bash
set -euo pipefail

goal="reduce validation loss"

hyper="$(node ./bin/researchloop.js prompt --agent codex --goal "$goal" --focus hyperparameters)"
arch="$(node ./bin/researchloop.js prompt --agent codex --goal "$goal" --focus architecture)"
attn="$(node ./bin/researchloop.js prompt --agent codex --goal "$goal" --focus attention)"

printf '%s' "$hyper" | grep -q "Hyperparameter Optimization Playbook"
printf '%s' "$hyper" | grep -q "muon_lr"
printf '%s' "$hyper" | grep -q "learning rate"

printf '%s' "$arch" | grep -q "Architecture Optimization Playbook"
printf '%s' "$arch" | grep -q "d_model"
printf '%s' "$arch" | grep -q "n_kv_heads"

printf '%s' "$attn" | grep -q "Attention Optimization Playbook"
printf '%s' "$attn" | grep -q "RoPE"
printf '%s' "$attn" | grep -q "n_kv_heads"

if printf '%s' "$hyper" | grep -q '{{GOAL}}'; then
  echo "hyperparameter playbook still has GOAL placeholder" >&2
  exit 1
fi

echo "researchloop test:focus-prompts passed"
