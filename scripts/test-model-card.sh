#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/dev/null 2>&1
node ./bin/researchloop.js record --id run-001 --status complete \
  --metric val_loss=0.42 --metric accuracy=0.91 \
  --dir "$tmpdir" 2>&1

echo "=== Test: model-card with run-id ==="
OUTPUT=$(node ./bin/researchloop.js model-card --id run-001 --dir "$tmpdir" 2>&1 || true)
echo "$OUTPUT"

# Check all section headers present
for section in "Model Details" "Intended Use" "Training Data" "Evaluation Results" "Limitations" "Ethical Considerations" "Hardware"; do
  if ! echo "$OUTPUT" | grep -q "$section"; then
    echo "FAIL: missing section '$section'"
    exit 1
  fi
done

# Check real metrics appear
if ! echo "$OUTPUT" | grep -q "val_loss"; then
  echo "FAIL: val_loss metric missing"
  exit 1
fi
if ! echo "$OUTPUT" | grep -q "0.42"; then
  echo "FAIL: metric value 0.42 missing"
  exit 1
fi

# Check TODO markers (at least 2)
TODO_COUNT=$(echo "$OUTPUT" | grep -c "\[TODO" || true)
if [ "$TODO_COUNT" -lt 2 ]; then
  echo "FAIL: expected at least 2 [TODO] markers, got $TODO_COUNT"
  exit 1
fi

echo ""
echo "=== Test: model-card --out file ==="
node ./bin/researchloop.js model-card --id run-001 --out "$tmpdir/MODEL_CARD.md" --dir "$tmpdir" 2>&1
if [ ! -f "$tmpdir/MODEL_CARD.md" ]; then
  echo "FAIL: --out file not created"
  exit 1
fi
echo "PASS: --out file created"

echo ""
echo "ALL TESTS PASSED"