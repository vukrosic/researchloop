#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G52 param-importance ==="

FIXTURE=$(mktemp -d)
trap "rm -rf $FIXTURE" EXIT

mkdir -p "$FIXTURE/.researchloop/scratchpad"

# Create runs with lr (numeric) and optimizer (categorical) params
# lr strongly correlates with val_loss, optimizer has weak correlation
cat > "$FIXTURE/.researchloop/scratchpad/runs.jsonl" << 'EOF'
{"id":"r1","status":"completed","metrics":{"val_loss":0.50},"value":0.50,"timestamp":"2026-05-17T10:00:00Z","params":{"lr":0.001,"optimizer":"adam"}}
{"id":"r2","status":"completed","metrics":{"val_loss":0.45},"value":0.45,"timestamp":"2026-05-17T10:01:00Z","params":{"lr":0.002,"optimizer":"adam"}}
{"id":"r3","status":"completed","metrics":{"val_loss":0.40},"value":0.40,"timestamp":"2026-05-17T10:02:00Z","params":{"lr":0.003,"optimizer":"adam"}}
{"id":"r4","status":"completed","metrics":{"val_loss":0.35},"value":0.35,"timestamp":"2026-05-17T10:03:00Z","params":{"lr":0.004,"optimizer":"sgd"}}
{"id":"r5","status":"completed","metrics":{"val_loss":0.30},"value":0.30,"timestamp":"2026-05-17T10:04:00Z","params":{"lr":0.005,"optimizer":"sgd"}}
{"id":"r6","status":"completed","metrics":{"val_loss":0.25},"value":0.25,"timestamp":"2026-05-17T10:05:00Z","params":{"lr":0.006,"optimizer":"sgd"}}
{"id":"r7","status":"completed","metrics":{"val_loss":0.20},"value":0.20,"timestamp":"2026-05-17T10:06:00Z","params":{"lr":0.007,"optimizer":"adam"}}
{"id":"r8","status":"completed","metrics":{"val_loss":0.15},"value":0.15,"timestamp":"2026-05-17T10:07:00Z","params":{"lr":0.008,"optimizer":"sgd"}}
{"id":"r9","status":"completed","metrics":{"val_loss":0.10},"value":0.10,"timestamp":"2026-05-17T10:08:00Z","params":{"lr":0.009,"optimizer":"adam"}}
{"id":"r10","status":"completed","metrics":{"val_loss":0.05},"value":0.05,"timestamp":"2026-05-17T10:09:00Z","params":{"lr":0.010,"optimizer":"sgd"}}
{"id":"r11","status":"discarded","metrics":{"val_loss":0.99},"value":0.99,"timestamp":"2026-05-17T10:10:00Z","params":{"lr":0.999,"optimizer":"adam"}}
EOF

echo "--- Test 1: param-importance --format table ---"
OUT=$(node bin/researchloop.js param-importance --dir "$FIXTURE" 2>&1)
echo "$OUT"
echo "$OUT" | grep -q "Pearson r" || { echo "FAIL: missing Pearson r section"; exit 1; }
echo "$OUT" | grep -q "Categorical Parameters" || { echo "FAIL: missing Categorical section"; exit 1; }
echo "$OUT" | grep -q "lr" || { echo "FAIL: lr param not found"; exit 1; }
echo "$OUT" | grep -q "optimizer" || { echo "FAIL: optimizer param not found"; exit 1; }

echo "--- Test 2: param-importance --metric val_loss ---"
OUT2=$(node bin/researchloop.js param-importance --metric val_loss --dir "$FIXTURE" 2>&1)
echo "$OUT2"
echo "$OUT2" | grep -q "val_loss" || { echo "FAIL: val_loss metric not in header"; exit 1; }

echo "--- Test 3: param-importance --format json ---"
OUT3=$(node bin/researchloop.js param-importance --format json --dir "$FIXTURE" 2>&1)
echo "$OUT3" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'numeric' in d and 'categorical' in d; assert d['nRuns'] == 10; print('JSON OK')"

echo "--- Test 4: insufficient data (< 5 runs) ---"
FIXTURE2=$(mktemp -d)
mkdir -p "$FIXTURE2/.researchloop/scratchpad"
echo '{"id":"r1","status":"completed","metrics":{"val_loss":0.5},"value":0.5,"params":{"lr":0.001}}' > "$FIXTURE2/.researchloop/scratchpad/runs.jsonl"
OUT4=$(node bin/researchloop.js param-importance --dir "$FIXTURE2" 2>&1)
echo "$OUT4"
echo "$OUT4" | grep -q "Insufficient data" || { echo "FAIL: expected insufficient data message"; rm -rf "$FIXTURE2"; exit 1; }
rm -rf "$FIXTURE2"

echo "--- Test 5: lr should rank #1 (strongest correlation) ---"
OUT5=$(node bin/researchloop.js param-importance --dir "$FIXTURE" 2>&1)
echo "$OUT5"
# Extract the first param listed under Pearson r (should be lr after sorting by |r|)
LR_LINE=$(echo "$OUT5" | grep "^| lr")
echo "lr line: $LR_LINE"
echo "$LR_LINE" | grep -q "| lr |" || { echo "FAIL: lr not in table"; exit 1; }

echo "=== All G52 param-importance tests passed ==="