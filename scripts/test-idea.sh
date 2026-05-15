#!/usr/bin/env bash
set -euo pipefail

tmp_blank="$(mktemp -d)"
tmp_llm="$(mktemp -d)"
trap 'rm -rf "$tmp_blank" "$tmp_llm"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmp_blank" >/tmp/researchloop-idea-blank-init.log
node ./bin/researchloop.js goal --dir "$tmp_blank" "lower validation loss" --metric val_loss --direction lower >/tmp/researchloop-idea-blank-goal.log
node ./bin/researchloop.js idea --dir "$tmp_blank" --write >/tmp/researchloop-idea-blank.log

mkdir -p "$tmp_llm/configs" "$tmp_llm/training" "$tmp_llm/optimizers"
touch "$tmp_llm/train_llm.py"
touch "$tmp_llm/configs/llm_config.py"
touch "$tmp_llm/configs/dataset_config.py"
touch "$tmp_llm/training/trainer.py"
touch "$tmp_llm/training/evaluation.py"
touch "$tmp_llm/optimizers/muon.py"
node ./bin/researchloop.js init --agent codex --dir "$tmp_llm" >/tmp/researchloop-idea-llm-init.log
node ./bin/researchloop.js goal --dir "$tmp_llm" "lower validation loss" --metric val_loss --direction lower >/tmp/researchloop-idea-llm-goal.log
node ./bin/researchloop.js idea --dir "$tmp_llm" >/tmp/researchloop-idea-llm.log

grep -q "Research Ideas" /tmp/researchloop-idea-blank.log
grep -q "Find the baseline" /tmp/researchloop-idea-blank.log
grep -q "Idea note written to" /tmp/researchloop-idea-blank.log
test -f "$tmp_blank/.researchloop/scratchpad/ideas/"*.md

grep -q "Research Ideas" /tmp/researchloop-idea-llm.log
grep -q "learning rate" /tmp/researchloop-idea-llm.log
grep -q "d_model" /tmp/researchloop-idea-llm.log
grep -q "n_layers" /tmp/researchloop-idea-llm.log

echo "researchloop test:idea passed"
