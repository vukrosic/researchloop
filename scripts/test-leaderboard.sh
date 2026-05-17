#!/usr/bin/env bash
set -e
cd /Users/vukrosic/my-life/autoresearch-ai

echo "=== Test G47 leaderboard ==="

# Create a temp fixture repo
FIXTURE=$(mktemp -d)
trap "rm -rf $FIXTURE" EXIT

mkdir -p "$FIXTURE/.researchloop/scratchpad"

# Create goal.md
cat > "$FIXTURE/.researchloop/goal.md" << 'EOF'
Goal: Test goal
Target Metric: val_loss
Direction: lower

## Baseline Command
echo hello
EOF

# Create a runs.jsonl with 5 runs (completed + promoted statuses)
cat > "$FIXTURE/.researchloop/scratchpad/runs.jsonl" << 'EOF'
{"id":"run-aaaaa1","status":"completed","metrics":{"val_loss":0.42},"value":0.42,"timestamp":"2026-05-01T10:00:00Z"}
{"id":"run-aaaaa2","status":"completed","metrics":{"val_loss":0.31},"value":0.31,"timestamp":"2026-05-01T11:00:00Z"}
{"id":"run-aaaaa3","status":"promoted","metrics":{"val_loss":0.25},"value":0.25,"timestamp":"2026-05-01T12:00:00Z"}
{"id":"run-aaaaa4","status":"completed","metrics":{"val_loss":0.55},"value":0.55,"timestamp":"2026-05-01T13:00:00Z"}
{"id":"run-aaaaa5","status":"discarded","metrics":{"val_loss":0.10},"value":0.10,"timestamp":"2026-05-01T14:00:00Z"}
{"id":"run-aaaaa6","status":"running","metrics":{"val_loss":0.99},"value":0.99,"timestamp":"2026-05-01T15:00:00Z"}
EOF

echo "--- Test 1: leaderboard without --write (stdout) ---"
OUT=$(node bin/researchloop.js leaderboard --dir "$FIXTURE" 2>&1)
echo "$OUT"
# Should show top 10 sorted by val_loss (lower is better by default)
echo "$OUT" | grep -q "Leaderboard" || { echo "FAIL: missing Leaderboard header"; exit 1; }
echo "$OUT" | grep -q "0.2500" || { echo "FAIL: best run (0.25) not at top"; exit 1; }
echo "$OUT" | grep -q "0.3100" || { echo "FAIL: second best run not present"; exit 1; }

echo "--- Test 2: leaderboard --metric val_loss --direction higher (higher is better) ---"
OUT2=$(node bin/researchloop.js leaderboard --metric val_loss --direction higher --dir "$FIXTURE" 2>&1)
echo "$OUT2"
echo "$OUT2" | grep -q "0.5500" || { echo "FAIL: highest val_loss not at top for direction=higher"; exit 1; }

echo "--- Test 3: leaderboard --top 3 ---"
OUT3=$(node bin/researchloop.js leaderboard --top 3 --dir "$FIXTURE" 2>&1)
echo "$OUT3"
# Should only show top 3
echo "$OUT3" | grep -c "run-" | grep -q 3 || { echo "FAIL: expected 3 run entries"; exit 1; }

echo "--- Test 4: leaderboard --write ---"
node bin/researchloop.js leaderboard --write --dir "$FIXTURE" 2>&1
test -f "$FIXTURE/.researchloop/LEADERBOARD.md" || { echo "FAIL: LEADERBOARD.md not written"; exit 1; }
cat "$FIXTURE/.researchloop/LEADERBOARD.md"
grep -q "Leaderboard" "$FIXTURE/.researchloop/LEADERBOARD.md" || { echo "FAIL: LEADERBOARD.md missing header"; exit 1; }
echo "PASS: --write created LEADERBOARD.md"

echo "--- Test 5: leaderboard --metric unknown_metric ---"
OUT5=$(node bin/researchloop.js leaderboard --metric unknown_metric --dir "$FIXTURE" 2>&1)
echo "$OUT5"
# Should handle gracefully (no crashes, empty table OK)

echo "=== All G47 leaderboard tests passed ==="