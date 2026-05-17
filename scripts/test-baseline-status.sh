#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "=== Test 1: Missing baseline ==="
OUTPUT=$(node ./bin/researchloop.js baseline-status --dir "$TMP_DIR" 2>&1 || true)
echo "$OUTPUT"
if echo "$OUTPUT" | grep -q "Baseline not found"; then
    echo "PASS: missing baseline detected"
else
    echo "FAIL: expected 'Baseline not found' message"
    exit 1
fi

echo ""
echo "=== Test 2: Incomplete baseline ==="
mkdir -p "$TMP_DIR/.researchloop"
cat > "$TMP_DIR/.researchloop/baseline.md" << 'EOF'
# Baseline

## What To Record

- Baseline artifact: model_v1.pt
- Metric: val_loss

## Frozen Surfaces

- Dataset: ImageNet-1k
- Model size: ResNet-50

## Notes

EOF
OUTPUT=$(node ./bin/researchloop.js baseline-status --dir "$TMP_DIR" 2>&1 || true)
echo "$OUTPUT"
if echo "$OUTPUT" | grep -q "Baseline is incomplete"; then
    echo "PASS: incomplete baseline detected"
else
    echo "FAIL: expected 'Baseline is incomplete' message"
    exit 1
fi

echo ""
echo "=== Test 3: Complete baseline ==="
cat > "$TMP_DIR/.researchloop/baseline.md" << 'EOF'
# Baseline

## What To Record

- Baseline artifact: model_v1.pt
- Metric: val_loss
- Direction: lower
- Command or config: python train.py --epochs 100
- Model/data/training budget: 24h GPU
- System or accelerator: NVIDIA A100
- Known limitations: pretrained on ImageNet only

## Frozen Surfaces

- Dataset: ImageNet-1k
- Token budget or eval budget: 50k eval samples
- Model size: ResNet-50
- Seed: 42
- Optimizer: SGD
- Architecture: ResNet-50

## Notes

Link to run id: run-001

EOF
OUTPUT=$(node ./bin/researchloop.js baseline-status --dir "$TMP_DIR" 2>&1 || true)
echo "$OUTPUT"
if echo "$OUTPUT" | grep -q "Baseline is complete"; then
    echo "PASS: complete baseline detected"
else
    echo "FAIL: expected 'Baseline is complete' message"
    exit 1
fi
if echo "$OUTPUT" | grep -q "val_loss"; then
    echo "PASS: metric shown"
else
    echo "FAIL: metric should be shown"
    exit 1
fi

echo ""
echo "=== Test 4: JSON output ==="
JSON_OUTPUT=$(node ./bin/researchloop.js baseline-status --dir "$TMP_DIR" --format json 2>&1 || true)
echo "$JSON_OUTPUT"
if echo "$JSON_OUTPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['status']=='complete', 'status should be complete'; assert d['metric']=='val_loss', 'metric mismatch'; assert d['frozen_variables']['seed']=='42', 'seed mismatch'; print('PASS: JSON output valid')" 2>&1; then
    echo "JSON validation passed"
else
    echo "FAIL: JSON validation failed"
    exit 1
fi

echo ""
echo "ALL TESTS PASSED"