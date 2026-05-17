#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
cd "$REPO_DIR"

# Create a temp directory for the test
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# Create minimal researchloop structure
mkdir -p "$TMP_DIR/.researchloop/scratchpad/runs"

# Copy failure patterns so clustering works
cp "$REPO_DIR/templates/base/failure-patterns.yaml" "$TMP_DIR/.researchloop/failure-patterns.yaml"

# Seed runs.jsonl with:
# - 5 OOM failures (kill_reason contains "oom", status=failed or killed_by_safety)
# - 2 timeout failures (kill_reason contains "timeout", status=killed_by_safety)
# Only status=failed|killed_by_rule|killed_by_safety is included
cat > "$TMP_DIR/.researchloop/scratchpad/runs.jsonl" << 'EOF'
{"id": "oom-1", "status": "failed", "kill_reason": "CUDA out of memory", "timestamp": "2025-01-01T00:00:00Z"}
{"id": "oom-2", "status": "failed", "kill_reason": "out of memory", "timestamp": "2025-01-01T00:01:00Z"}
{"id": "oom-3", "status": "failed", "kill_reason": "OOM during allocation", "timestamp": "2025-01-01T00:02:00Z"}
{"id": "oom-4", "status": "killed_by_safety", "kill_reason": "out of memory in safety check", "timestamp": "2025-01-01T00:03:00Z"}
{"id": "oom-5", "status": "killed_by_safety", "kill_reason": "OOM detected", "timestamp": "2025-01-01T00:04:00Z"}
{"id": "timeout-1", "status": "killed_by_safety", "kill_reason": "timeout reached", "timestamp": "2025-01-01T00:05:00Z"}
{"id": "timeout-2", "status": "killed_by_safety", "kill_reason": "timeout exceeded", "timestamp": "2025-01-01T00:06:00Z"}
{"id": "success-run", "status": "complete", "timestamp": "2025-01-01T00:07:00Z"}
EOF

echo "=== Test: autoresearch failures --top 10 ==="
OUTPUT=$(node ./bin/researchloop.js failures --top 10 --dir "$TMP_DIR" 2>&1)
echo "$OUTPUT"

echo ""
echo "=== Verifications ==="

# Check that we got exactly 3 clusters (oom, out of memory, timeout)
if echo "$OUTPUT" | grep -q "Clusters: 3"; then
    echo "PASS: Found exactly 3 clusters"
else
    echo "FAIL: Expected 3 clusters"
    echo "$OUTPUT"
    exit 1
fi

# Check that OOM-related clusters suggest halving batch size
if echo "$OUTPUT" | grep -q "Halve batch_size"; then
    echo "PASS: OOM-related clusters suggest halving batch_size"
else
    echo "FAIL: OOM clusters should suggest halving batch_size"
    echo "$OUTPUT"
    exit 1
fi

# Check total failures is 7
if echo "$OUTPUT" | grep -q "Total failures: 7"; then
    echo "PASS: Found 7 failures"
else
    echo "FAIL: Expected 7 failures"
    echo "$OUTPUT"
    exit 1
fi

echo ""
echo "=== Test: JSON output ==="
JSON_OUTPUT=$(node ./bin/researchloop.js failures --top 10 --format json --dir "$TMP_DIR" 2>&1)
echo "$JSON_OUTPUT"

# Check JSON has clusters array with 3 entries
if echo "$JSON_OUTPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert len(d['clusters'])==3, 'Expected 3 clusters in JSON'; print('PASS: JSON has 3 clusters')" 2>&1; then
    echo "JSON cluster count OK"
else
    echo "FAIL: JSON should have 3 clusters"
    exit 1
fi

# Check that JSON includes suggestion for each cluster
if echo "$JSON_OUTPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert all('suggestion' in c for c in d['clusters']), 'Missing suggestion field'; print('PASS: All clusters have suggestions')" 2>&1; then
    echo "JSON suggestions OK"
else
    echo "FAIL: JSON should have suggestions"
    exit 1
fi

echo ""
echo "ALL TESTS PASSED"