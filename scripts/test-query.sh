#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G13 query ==="

FIXTURE=$(mktemp -d)
trap "rm -rf $FIXTURE" EXIT

mkdir -p "$FIXTURE/.researchloop/scratchpad"

cat > "$FIXTURE/.researchloop/scratchpad/runs.jsonl" << 'EOF'
{"id":"r1","status":"completed","metrics":{"val_loss":0.50},"value":0.50,"timestamp":"2026-05-17T10:00:00Z","params":{"lr":0.001}}
{"id":"r2","status":"completed","metrics":{"val_loss":0.31},"value":0.31,"timestamp":"2026-05-17T10:01:00Z","params":{"lr":0.003}}
{"id":"r3","status":"failed","metrics":{"val_loss":null},"value":null,"timestamp":"2026-05-17T10:02:00Z","params":{"lr":0.005}}
{"id":"r4","status":"completed","metrics":{"val_loss":0.20},"value":0.20,"timestamp":"2026-05-17T10:03:00Z","params":{"lr":0.010}}
{"id":"r5","status":"completed","metrics":{"val_loss":0.10},"value":0.10,"timestamp":"2026-05-17T10:04:00Z","params":{"lr":0.020}}
EOF

echo "--- Test 1: query with where val_loss < 0.4 ---"
OUT=$(node bin/researchloop.js query "where metrics.val_loss < 0.4" --dir "$FIXTURE" 2>&1)
echo "$OUT"
# val_loss: r1=0.50(no), r2=0.31(yes), r3=null(no failed), r4=0.20(yes), r5=0.10(yes)
echo "$OUT" | grep -q "r4" || { echo "FAIL: r4 (val_loss 0.20) should be in results"; exit 1; }
echo "$OUT" | grep -q "r5" || { echo "FAIL: r5 (val_loss 0.10) should be in results"; exit 1; }
echo "$OUT" | grep -q "r2" || { echo "FAIL: r2 (val_loss 0.31) should be in results"; exit 1; }
echo "$OUT" | grep -q "r1" && { echo "FAIL: r1 (val_loss 0.50) should NOT be in results"; exit 1; }
echo "$OUT" | grep -q "r3" && { echo "FAIL: r3 (failed, null val_loss) should NOT be in results"; exit 1; }

echo "--- Test 2: query with sort-by val_loss asc ---"
OUT2=$(node bin/researchloop.js query "where status = completed sort-by metrics.val_loss asc" --dir "$FIXTURE" 2>&1)
echo "$OUT2"
# Should be sorted lowest to highest
POS=$(echo "$OUT2" | grep -n "r5" | head -1 | cut -d: -f1)
echo "r5 position: $POS (should be first data row after header)"
test "$POS" -eq 3 || { echo "FAIL: r5 should be first data row"; exit 1; }

echo "--- Test 3: query with limit 2 ---"
OUT3=$(node bin/researchloop.js query "where metrics.val_loss < 1 sort-by metrics.val_loss asc limit 2" --dir "$FIXTURE" 2>&1)
echo "$OUT3"
echo "$OUT3" | grep -c "r[0-9]" | grep -q 2 || { echo "FAIL: expected exactly 2 result rows"; exit 1; }

echo "--- Test 4: query --format jsonl ---"
OUT4=$(node bin/researchloop.js query "where status = completed sort-by metrics.val_loss asc limit 2" --format jsonl --dir "$FIXTURE" 2>&1)
echo "$OUT4"
echo "$OUT4" | python3 -c "import sys; lines=sys.stdin.read().strip().split('\\n'); assert len(lines)==2; print('JSONL OK')"

echo "--- Test 5: query with between operator ---"
OUT5=$(node bin/researchloop.js query "where metrics.val_loss between 0.20..0.50" --dir "$FIXTURE" 2>&1)
echo "$OUT5"
echo "$OUT5" | grep -q "r4" || { echo "FAIL: r4 (0.20) should be in 0.20..0.50 range"; exit 1; }
echo "$OUT5" | grep -q "r1" || { echo "FAIL: r1 (0.50) should be in 0.20..0.50 range"; exit 1; }

echo "--- Test 6: query empty result ---"
OUT6=$(node bin/researchloop.js query "where metrics.val_loss > 100" --dir "$FIXTURE" 2>&1)
echo "$OUT6"
echo "$OUT6" | grep -q "(no rows match)" || { echo "FAIL: expected empty result message"; exit 1; }

echo "--- Test 7: query invalid syntax ---"
OUT7=$(node bin/researchloop.js query "whatever" --dir "$FIXTURE" 2>&1; echo "exit: $?")
echo "$OUT7"
echo "$OUT7" | grep -q 'must start with' || { echo "FAIL: expected error about where"; exit 1; }

echo "=== All G13 query tests passed ==="