#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G45 suggest ==="

FIXTURE=$(mktemp -d)
trap "rm -rf $FIXTURE" EXIT

mkdir -p "$FIXTURE/.researchloop/scratchpad"

# 10 runs with lr ∈ {1e-4, 1e-3, 1e-2} - best is 1e-3
# lr values: 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010
# best metric is lowest value (direction lower) at lr=0.001
cat > "$FIXTURE/.researchloop/scratchpad/runs.jsonl" << 'EOF'
{"id":"r1","status":"completed","metrics":{"val_loss":0.50},"value":0.50,"timestamp":"2026-05-17T10:00:00Z","params":{"lr":0.001}}
{"id":"r2","status":"completed","metrics":{"val_loss":0.40},"value":0.40,"timestamp":"2026-05-17T10:01:00Z","params":{"lr":0.002}}
{"id":"r3","status":"completed","metrics":{"val_loss":0.30},"value":0.30,"timestamp":"2026-05-17T10:02:00Z","params":{"lr":0.003}}
{"id":"r4","status":"completed","metrics":{"val_loss":0.35},"value":0.35,"timestamp":"2026-05-17T10:03:00Z","params":{"lr":0.004}}
{"id":"r5","status":"completed","metrics":{"val_loss":0.25},"value":0.25,"timestamp":"2026-05-17T10:04:00Z","params":{"lr":0.005}}
{"id":"r6","status":"completed","metrics":{"val_loss":0.20},"value":0.20,"timestamp":"2026-05-17T10:05:00Z","params":{"lr":0.006}}
{"id":"r7","status":"completed","metrics":{"val_loss":0.15},"value":0.15,"timestamp":"2026-05-17T10:06:00Z","params":{"lr":0.007}}
{"id":"r8","status":"completed","metrics":{"val_loss":0.10},"value":0.10,"timestamp":"2026-05-17T10:07:00Z","params":{"lr":0.008}}
{"id":"r9","status":"completed","metrics":{"val_loss":0.05},"value":0.05,"timestamp":"2026-05-17T10:08:00Z","params":{"lr":0.009}}
{"id":"r10","status":"completed","metrics":{"val_loss":0.01},"value":0.01,"timestamp":"2026-05-17T10:09:00Z","params":{"lr":0.010}}
EOF

echo "--- Test 1: suggest --format text ---"
OUT=$(node bin/researchloop.js suggest --dir "$FIXTURE" 2>&1)
echo "$OUT"
echo "$OUT" | grep -q "Auto-Suggest" || { echo "FAIL: missing Auto-Suggest header"; exit 1; }
echo "$OUT" | grep -q "lr" || { echo "FAIL: lr not suggested"; exit 1; }

echo "--- Test 2: suggest --direction lower ---"
OUT2=$(node bin/researchloop.js suggest --direction lower --dir "$FIXTURE" 2>&1)
echo "$OUT2"
echo "$OUT2" | grep -q "lower" || { echo "FAIL: direction lower not in output"; exit 1; }

echo "--- Test 3: suggest --format json ---"
OUT3=$(node bin/researchloop.js suggest --format json --dir "$FIXTURE" 2>&1)
echo "$OUT3" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'suggestions' in d; assert d['metric'] == 'value'; assert len(d['suggestions']) > 0; print('JSON OK')"

echo "--- Test 4: suggest --n 1 ---"
OUT4=$(node bin/researchloop.js suggest --n 1 --dir "$FIXTURE" 2>&1)
echo "$OUT4"
# Should have exactly 1 suggestion line (the table row)
LINES=$(echo "$OUT4" | grep -c "| 1 |")
echo "1-line count: $LINES"
test "$LINES" -eq 1 || { echo "FAIL: expected 1 suggestion"; exit 1; }

echo "--- Test 5: insufficient data (< 3 runs) ---"
FIXTURE2=$(mktemp -d)
mkdir -p "$FIXTURE2/.researchloop/scratchpad"
echo '{"id":"r1","status":"completed","metrics":{"val_loss":0.5},"value":0.5,"params":{"lr":0.001}}' > "$FIXTURE2/.researchloop/scratchpad/runs.jsonl"
echo '{"id":"r2","status":"completed","metrics":{"val_loss":0.4},"value":0.4,"params":{"lr":0.002}}' > "$FIXTURE2/.researchloop/scratchpad/runs.jsonl"
OUT5=$(node bin/researchloop.js suggest --dir "$FIXTURE2" 2>&1)
echo "$OUT5"
echo "$OUT5" | grep -q "Not enough data" || { echo "FAIL: expected insufficient data message"; rm -rf "$FIXTURE2"; exit 1; }
rm -rf "$FIXTURE2"

echo "=== All G45 suggest tests passed ==="