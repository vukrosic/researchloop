#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cli="node $repo_root/bin/researchloop.js"

$cli init --agent codex --dir "$tmpdir" >/tmp/researchloop-run-init.log
$cli goal --dir "$tmpdir" "lower validation loss" \
  --metric val_loss --direction lower \
  --baseline "printf 'epoch 1\nval_loss=1.42\n'" \
  --evaluation "printf 'val_loss=1.30\n'" >/tmp/researchloop-run-goal.log

$cli baseline --dir "$tmpdir" --id baseline-001 >/tmp/researchloop-run-baseline.log
grep -q "status: complete" /tmp/researchloop-run-baseline.log
grep -q "val_loss: 1.42" /tmp/researchloop-run-baseline.log
grep -q "recorded: baseline-001" /tmp/researchloop-run-baseline.log
grep -q "goal.md Current Best updated" /tmp/researchloop-run-baseline.log
grep -q "val_loss = 1.42" "$tmpdir/.researchloop/goal.md"
grep -q "Baseline: val_loss = 1.42" "$tmpdir/.researchloop/plan.md"
test -f "$tmpdir/.researchloop/scratchpad/runs/baseline-001/log.txt"
grep -q "val_loss=1.42" "$tmpdir/.researchloop/scratchpad/runs/baseline-001/log.txt"
grep -q '"id":"baseline-001"' "$tmpdir/.researchloop/scratchpad/runs.jsonl"
grep -q '"val_loss":1.42' "$tmpdir/.researchloop/scratchpad/runs.jsonl"

$cli run --dir "$tmpdir" --id run-better --command "printf 'val_loss=1.18\n'" >/tmp/researchloop-run-better.log
grep -q "status: complete" /tmp/researchloop-run-better.log
grep -q "val_loss: 1.18" /tmp/researchloop-run-better.log

$cli run --dir "$tmpdir" --id run-json --command "printf '%s\n' '{\"val_loss\": 1.05}'" >/tmp/researchloop-run-json.log
grep -q "val_loss: 1.05" /tmp/researchloop-run-json.log

set +e
$cli run --dir "$tmpdir" --id run-fail --command "false" >/tmp/researchloop-run-fail.log
fail_exit=$?
set -e
if [ "$fail_exit" -eq 0 ]; then
  echo "expected failed run to exit nonzero"
  exit 1
fi
grep -q "status: failed" /tmp/researchloop-run-fail.log

$cli run --dir "$tmpdir" --id run-nometric --command "echo nothing here" >/tmp/researchloop-run-nometric.log
grep -q "status: complete_no_metric" /tmp/researchloop-run-nometric.log

set +e
$cli run --dir "$tmpdir" --id run-timeout --command "sleep 5" --timeout 1 >/tmp/researchloop-run-timeout.log
to_exit=$?
set -e
if [ "$to_exit" -eq 0 ]; then
  echo "expected timeout run to exit nonzero"
  exit 1
fi
grep -q "status: timeout" /tmp/researchloop-run-timeout.log

$cli compare --dir "$tmpdir" --metric val_loss --direction lower >/tmp/researchloop-run-compare.log
grep -q "best: run-json = 1.05" /tmp/researchloop-run-compare.log

echo "researchloop test:run passed"
