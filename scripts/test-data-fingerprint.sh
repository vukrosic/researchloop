#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/dev/null 2>&1

mkdir -p "$tmpdir/data"
echo "train data" > "$tmpdir/data/train.txt"
echo "val data" > "$tmpdir/data/val.txt"

cat > "$tmpdir/.researchloop/goal.md" << 'EOF'
# Goal

Goal: test data fingerprinting
Target Metric: val_loss
Direction: lower

data_globs:
  - data/*.txt
EOF

echo "=== Test 1: data-fingerprint command ==="
OUTPUT=$(node ./bin/researchloop.js data-fingerprint --dir "$tmpdir" 2>&1 || true)
echo "Output: $OUTPUT"
if [ -n "$OUTPUT" ] && [ "$OUTPUT" != "No data_globs configured or no files matched." ]; then
    echo "PASS: fingerprint computed"
else
    echo "FAIL: expected fingerprint string"
    exit 1
fi

echo ""
echo "=== Test 2: Two runs with identical data have same fingerprint ==="
python3 - "$tmpdir" <<'PYEOF'
import json, sys, os, hashlib

tmpdir = sys.argv[1]
ledger = tmpdir + "/.researchloop/scratchpad/runs.jsonl"
os.makedirs(tmpdir + "/.researchloop/scratchpad/runs", exist_ok=True)

train_path = tmpdir + "/data/train.txt"
val_path = tmpdir + "/data/val.txt"
files = sorted([train_path, val_path])
h = hashlib.sha256()
for f in files:
    s = os.stat(f)
    h.update(f.encode())
    h.update(str(s.st_size).encode())
    h.update(str(s.st_mtime).encode())
fp = h.hexdigest()

runs = [
    {"id": "run-a", "status": "complete", "timestamp": "2024-01-01T00:00:00Z", "data_fingerprint": fp},
    {"id": "run-b", "status": "complete", "timestamp": "2024-01-02T00:00:00Z", "data_fingerprint": fp},
]
for run in runs:
    with open(ledger, "a") as f:
        f.write(json.dumps(run) + "\n")
PYEOF

OUTPUT=$(node ./bin/researchloop.js compare --metric val_loss --direction lower --dir "$tmpdir" 2>&1 || true)
echo "Compare output:"
echo "$OUTPUT"
if echo "$OUTPUT" | grep -q "different data fingerprints"; then
    echo "FAIL: should not warn when fingerprints are identical"
    exit 1
else
    echo "PASS: no fingerprint warning for identical data"
fi

echo ""
echo "ALL TESTS PASSED"