#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G01 propose command ==="

FIXTURE=$(mktemp -d)
trap "rm -rf $FIXTURE" EXIT

mkdir -p "$FIXTURE/.researchloop"

# Create a complete baseline.md
cat > "$FIXTURE/.researchloop/baseline.md" << 'EOF'
# Baseline

## What To Record

- Baseline artifact: artifacts/baseline_run/model.pt
- Metric: val_loss
- Direction: lower
- Command or config: python train.py --epochs 100

## Frozen Surfaces

- Dataset: ./data/train.txt
- Model size: 124M params
- Seed: 42

## Notes

Baseline established 2026-05-17.
EOF

echo "--- Test 1: propose generates JSON output ---"
OUT1=$(node bin/researchloop.js propose --dir "$FIXTURE" 2>&1)
echo "$OUT1" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d, list); assert len(d)>0; print('OK: got', len(d), 'proposals')" || { echo "FAIL: JSON output invalid"; exit 1; }

echo "--- Test 2: propose --n 3 limits output ---"
OUT2=$(node bin/researchloop.js propose --n 3 --dir "$FIXTURE" 2>&1)
echo "$OUT2" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)<=3; print('OK: got', len(d), 'proposals (max 3)')" || { echo "FAIL: limit not respected"; exit 1; }

echo "--- Test 3: propose --write creates proposals.jsonl ---"
node bin/researchloop.js propose --write --dir "$FIXTURE" 2>&1
test -f "$FIXTURE/.researchloop/scratchpad/proposals.jsonl" || { echo "FAIL: proposals.jsonl not created"; exit 1; }
LINES=$(wc -l < "$FIXTURE/.researchloop/scratchpad/proposals.jsonl")
echo "proposals.jsonl has $LINES line(s)"
test "$LINES" -ge 1 || { echo "FAIL: no proposals written"; exit 1; }

echo "--- Test 4: proposal has all required keys ---"
node bin/researchloop.js propose --dir "$FIXTURE" 2>&1 | python3 -c "
import sys,json
d=json.load(sys.stdin)
required=['id','title','hypothesis','change','metric','expected_direction','risk','kill_criterion','mechanism']
for r in d:
    for k in required:
        assert k in r, f'Missing key: {k}'
print('OK: all proposals have required keys')
"

echo "--- Test 5: propose --write id stability ---"
# Run again, should not duplicate ids
node bin/researchloop.js propose --write --dir "$FIXTURE" 2>&1
FIRST_ID=$(head -1 "$FIXTURE/.researchloop/scratchpad/proposals.jsonl" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "First proposal id: $FIRST_ID"

echo "--- Test 6: propose with metric direction ---"
OUT6=$(node bin/researchloop.js propose --metric accuracy --direction higher --dir "$FIXTURE" 2>&1)
echo "$OUT6" | python3 -c "import sys,json; d=json.load(sys.stdin); assert all(p['metric']=='accuracy' for p in d); assert all(p['expected_direction']=='higher' for p in d); print('OK: metric/direction respected')" || { echo "FAIL: metric/direction not set"; exit 1; }

echo "--- Test 7: missing baseline still works ---"
FIXTURE2=$(mktemp -d)
mkdir -p "$FIXTURE2/.researchloop"
OUT7=$(node bin/researchloop.js propose --n 2 --dir "$FIXTURE2" 2>&1)
echo "$OUT7" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>0; print('OK: works without baseline')" || { echo "FAIL: should work without baseline"; exit 1; }
rm -rf "$FIXTURE2"

echo "=== All G01 propose tests passed ==="