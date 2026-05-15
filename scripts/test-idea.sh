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
node ./bin/researchloop.js record --dir "$tmp_llm" --id llm-baseline --status complete --metric val_loss=1.42 --note "baseline run" >/tmp/researchloop-idea-llm-record-1.log
node ./bin/researchloop.js record --dir "$tmp_llm" --id llm-alt --status complete --metric val_loss=1.31 --note "better run" >/tmp/researchloop-idea-llm-record-2.log
node ./bin/researchloop.js record --dir "$tmp_llm" --id llm-worse --status complete --metric val_loss=1.58 --note "worse run" >/tmp/researchloop-idea-llm-record-3.log
node ./bin/researchloop.js idea --dir "$tmp_llm" >/tmp/researchloop-idea-llm.log

grep -q "Research Ideas" /tmp/researchloop-idea-blank.log
grep -q "Find the baseline" /tmp/researchloop-idea-blank.log
grep -q "Idea note written to" /tmp/researchloop-idea-blank.log
test -f "$tmp_blank/.researchloop/scratchpad/ideas/"*.md

grep -q "Research Ideas" /tmp/researchloop-idea-llm.log
grep -q "Experiment History" /tmp/researchloop-idea-llm.log
grep -q "llm-baseline" /tmp/researchloop-idea-llm.log
grep -q "llm-alt" /tmp/researchloop-idea-llm.log
grep -q "Reconstruct the last meaningful comparison" /tmp/researchloop-idea-llm.log
grep -q "Best: llm-alt = 1.31" /tmp/researchloop-idea-llm.log
grep -q "No run history found" /tmp/researchloop-idea-blank.log

tmp_papers="$(mktemp -d)"
trap 'rm -rf "$tmp_blank" "$tmp_llm" "$tmp_papers"' EXIT
node ./bin/researchloop.js init --agent codex --dir "$tmp_papers" >/tmp/researchloop-idea-papers-init.log
node ./bin/researchloop.js goal --dir "$tmp_papers" "lower validation loss" --metric val_loss --direction lower >/tmp/researchloop-idea-papers-goal.log
RESEARCHLOOP_ARXIV_FIXTURE="$(cd "$(dirname "$0")/.." && pwd)/examples/fixtures/arxiv-sample.xml" \
node ./bin/researchloop.js scan-papers --dir "$tmp_papers" --cache-dir "$(mktemp -d)" --limit 3 >/tmp/researchloop-idea-papers-scan.log
node ./bin/researchloop.js idea --dir "$tmp_papers" >/tmp/researchloop-idea-papers.log
grep -q "Read paper:" /tmp/researchloop-idea-papers.log
grep -q "Efficient Learning Rate Schedules" /tmp/researchloop-idea-papers.log
grep -q "arXiv 2503.12345v1" /tmp/researchloop-idea-papers.log

echo "researchloop test:idea passed"
