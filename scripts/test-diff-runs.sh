#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/tmp/researchloop-diff-runs-init.log

# Create two runs that differ only in lr param
node ./bin/researchloop.js record --dir "$tmpdir" \
  --id run-a --status complete \
  --metric val_loss=2.50 --metric accuracy=0.71 \
  --note "baseline" >/tmp/researchloop-diff-runs-a.log 2>&1

node ./bin/researchloop.js record --dir "$tmpdir" \
  --id run-b --status complete \
  --metric val_loss=1.90 --metric accuracy=0.75 \
  --note "lower lr" >/tmp/researchloop-diff-runs-b.log 2>&1

# Manually add params field to run rows using python
python3 - "$tmpdir" <<'PYEOF'
import json
import sys
tmpdir = sys.argv[1]
ledger = tmpdir + "/.researchloop/scratchpad/runs.jsonl"
tmp_ledger = ledger + ".tmp"

rows = []
with open(ledger, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row["id"] == "run-a":
            row["params"] = {"lr": 0.001, "batch_size": 32, "epochs": 10}
        elif row["id"] == "run-b":
            row["params"] = {"lr": 0.0001, "batch_size": 32, "epochs": 10}
        rows.append(row)

with open(tmp_ledger, "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")

import os
os.replace(tmp_ledger, ledger)
PYEOF

# Test 1: text format - diff on lr param only
node ./bin/researchloop.js diff-runs run-a run-b --dir "$tmpdir" >/tmp/researchloop-diff-runs-text.log 2>&1

# Should show lr param change
if ! grep -q 'lr:' /tmp/researchloop-diff-runs-text.log; then
  echo "FAIL: diff-runs text format did not show lr param change"
  cat /tmp/researchloop-diff-runs-text.log
  exit 1
fi

# Test 2: diff identical runs shows "IDENTICAL"
node ./bin/researchloop.js diff-runs run-a run-a --dir "$tmpdir" >/tmp/researchloop-diff-runs-identical.log 2>&1
if ! grep -q "IDENTICAL" /tmp/researchloop-diff-runs-identical.log; then
  echo "FAIL: diff-runs same run should show IDENTICAL"
  cat /tmp/researchloop-diff-runs-identical.log
  exit 1
fi

# Test 3: json format
node ./bin/researchloop.js diff-runs run-a run-b --format json --dir "$tmpdir" >/tmp/researchloop-diff-runs-json.log 2>&1
if ! grep -q '"id_a": "run-a"' /tmp/researchloop-diff-runs-json.log; then
  echo "FAIL: diff-runs json format did not produce valid JSON"
  cat /tmp/researchloop-diff-runs-json.log
  exit 1
fi

# Test 4: markdown format
node ./bin/researchloop.js diff-runs run-a run-b --format markdown --dir "$tmpdir" >/tmp/researchloop-diff-runs-md.log 2>&1
if ! grep -q "Run Diff" /tmp/researchloop-diff-runs-md.log; then
  echo "FAIL: diff-runs markdown format did not produce expected output"
  cat /tmp/researchloop-diff-runs-md.log
  exit 1
fi

echo "autoresearch test:diff-runs passed"