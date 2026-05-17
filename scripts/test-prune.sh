#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/dev/null 2>&1

# Create 3 discarded runs and 1 promoted run, all old
python3 - "$tmpdir" <<'PYEOF'
import json, time, os, sys

tmpdir = sys.argv[1]
ledger = tmpdir + "/.researchloop/scratchpad/runs.jsonl"
os.makedirs(tmpdir + "/.researchloop/scratchpad/runs", exist_ok=True)

runs = [
    {"id": "run-discarded-1", "status": "discarded", "timestamp": "2024-01-01T00:00:00Z", "metric": "val_loss=3.0"},
    {"id": "run-discarded-2", "status": "discarded", "timestamp": "2024-01-02T00:00:00Z", "metric": "val_loss=2.9"},
    {"id": "run-failed-1", "status": "failed", "timestamp": "2024-01-03T00:00:00Z"},
    {"id": "run-promoted-1", "status": "promoted", "timestamp": "2024-01-04T00:00:00Z"},
]

for run in runs:
    run_dir = tmpdir + "/.researchloop/scratchpad/runs/" + run["id"]
    os.makedirs(run_dir, exist_ok=True)
    with open(run_dir + "/log.txt", "w") as f:
        f.write("log for " + run["id"])
    with open(ledger, "a") as f:
        f.write(json.dumps(run) + "\n")
PYEOF

echo "=== Test 1: dry-run with --status discarded ==="
DRY_OUTPUT=$(node ./bin/researchloop.js prune --older-than 30d --status discarded --dry-run --dir "$tmpdir" 2>&1 || true)
echo "$DRY_OUTPUT"

if ! echo "$DRY_OUTPUT" | grep -q "run-discarded"; then
    echo "FAIL: dry-run should list discarded runs"
    exit 1
fi

if [ ! -d "$tmpdir/.researchloop/scratchpad/runs/run-discarded-1" ]; then
    echo "FAIL: dry-run should not delete directories"
    exit 1
fi

echo ""
echo "=== Test 2: actual prune ==="
node ./bin/researchloop.js prune --older-than 30d --status discarded --dir "$tmpdir" 2>&1 || true

if [ -d "$tmpdir/.researchloop/scratchpad/runs/run-discarded-1" ]; then
    echo "FAIL: run-discarded-1 dir should be deleted after prune"
    exit 1
fi
if [ -d "$tmpdir/.researchloop/scratchpad/runs/run-discarded-2" ]; then
    echo "FAIL: run-discarded-2 dir should be deleted after prune"
    exit 1
fi
if [ ! -d "$tmpdir/.researchloop/scratchpad/runs/run-promoted-1" ]; then
    echo "FAIL: promoted run should not be touched"
    exit 1
fi

python3 - "$tmpdir" <<'PYEOF2'
import json, sys
tmpdir = sys.argv[1]
ledger = tmpdir + "/.researchloop/scratchpad/runs.jsonl"
with open(ledger) as f:
    for line in f:
        line = line.strip()
        if not line: continue
        row = json.loads(line)
        print(row["id"], "pruned:", row.get("pruned"), "status:", row["status"])
PYEOF2

echo ""
echo "ALL TESTS PASSED"