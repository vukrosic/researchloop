#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G27 baseline --lock ==="

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
- Model/data/training budget: GPT-2 small, 1M tokens
- System or accelerator: NVIDIA A100
- Known limitations: Small dataset, may overfit

## Frozen Surfaces

- Dataset: ./data/train.txt
- Token budget or eval budget: 1M training tokens
- Model size: 124M params
- Seed: 42
- Optimizer: AdamW
- Architecture: transformer decoder

## Notes

Baseline established 2026-05-17.
EOF

# Create a git repo with a commit
git init "$FIXTURE" > /dev/null 2>&1
cd "$FIXTURE"
git config user.email "test@test.com"
git config user.name "Test"
echo "test" > file.txt
git add file.txt
git commit -m "initial" > /dev/null 2>&1
cd /Users/vukrosic/my-life/autoresearch-ai

echo "--- Test 1: baseline --lock creates lock file ---"
OUT=$(node bin/researchloop.js baseline --lock --dir "$FIXTURE" 2>&1)
echo "$OUT"
echo "$OUT" | grep -q "Baseline locked" || { echo "FAIL: expected 'Baseline locked'"; exit 1; }
test -f "$FIXTURE/.researchloop/baseline.lock" || { echo "FAIL: baseline.lock not created"; exit 1; }

echo "--- Test 2: lock file contains required keys ---"
LOCK_CONTENT=$(cat "$FIXTURE/.researchloop/baseline.lock")
echo "$LOCK_CONTENT"
echo "$LOCK_CONTENT" | grep -q '"locked_at"' || { echo "FAIL: locked_at missing"; exit 1; }
echo "$LOCK_CONTENT" | grep -q '"metric"' || { echo "FAIL: metric missing"; exit 1; }
echo "$LOCK_CONTENT" | grep -q '"git_sha"' || { echo "FAIL: git_sha missing"; exit 1; }
echo "$LOCK_CONTENT" | grep -q '"baseline_value"' || { echo "FAIL: baseline_value missing"; exit 1; }

echo "--- Test 3: baseline --unlock removes lock ---"
node bin/researchloop.js baseline --unlock --dir "$FIXTURE" 2>&1
test ! -f "$FIXTURE/.researchloop/baseline.lock" || { echo "FAIL: baseline.lock not removed"; exit 1; }

echo "--- Test 4: baseline-status shows complete ---"
OUT4=$(node bin/researchloop.js baseline-status --dir "$FIXTURE" 2>&1)
echo "$OUT4"
echo "$OUT4" | grep -q "Baseline is complete" || { echo "FAIL: expected baseline status"; exit 1; }

echo "--- Test 5: baseline-status --format json ---"
OUT5=$(node bin/researchloop.js baseline-status --format json --dir "$FIXTURE" 2>&1)
echo "$OUT5"
echo "$OUT5" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='complete'" || { echo "FAIL: JSON status not complete"; exit 1; }

echo "--- Test 6: baseline shows drift warning when drifted ---"
# Create lock with old git SHA
echo '{"locked_at":"2026-05-01T00:00:00Z","metric":"val_loss","direction":"lower","command":"python train.py","git_sha":"00000000","git_dirty":false,"env_hash":null,"baseline_value":null}' > "$FIXTURE/.researchloop/baseline.lock"
node bin/researchloop.js baseline --dir "$FIXTURE" 2>&1 | grep -q "Git SHA drift" || { echo "FAIL: expected drift warning"; exit 1; }

echo "--- Test 7: missing baseline shows error ---"
FIXTURE2=$(mktemp -d)
mkdir -p "$FIXTURE2/.researchloop"
OUT7=$(node bin/researchloop.js baseline --lock --dir "$FIXTURE2" 2>&1; echo "exit: $?")
echo "$OUT7"
echo "$OUT7" | grep -q "No baseline.md found" || { echo "FAIL: expected error about missing baseline"; exit 1; }
rm -rf "$FIXTURE2"

echo "=== All G27 baseline --lock tests passed ==="