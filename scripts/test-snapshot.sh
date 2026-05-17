#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cli="node $repo_root/bin/researchloop.js"

echo "=== G55: autoresearch snapshot ==="

$cli init --agent codex --dir "$tmpdir" >/dev/null
$cli goal --dir "$tmpdir" "lower val_loss" --metric val_loss --direction lower --baseline "echo val_loss=0.5" --evaluation "echo val_loss=0.4" >/dev/null

# Create runs
printf '{"id":"run-1","status":"completed","metrics":{"val_loss":0.5},"started_at":"2026-01-01T00:00:00Z"}\n' > "$tmpdir/.researchloop/scratchpad/runs.jsonl"

echo "--- Test 1: snapshot save ---"
$cli snapshot save --name my-snapshot --dir "$tmpdir" 2>&1
if [ -d "$tmpdir/.researchloop/snapshots/my-snapshot" ]; then
  echo "PASS: snapshot directory created"
else
  echo "FAIL: snapshot directory not created"
  exit 1
fi

echo ""
echo "--- Test 2: snapshot list ---"
output_list=$($cli snapshot list --dir "$tmpdir" 2>&1)
echo "$output_list"
echo "$output_list" | grep -q "my-snapshot" || { echo "FAIL: snapshot not in list"; exit 1; }
echo "PASS: snapshot list"

echo ""
echo "--- Test 3: snapshot restore roundtrip ---"
# Add new run
printf '{"id":"run-2","status":"completed","metrics":{"val_loss":0.3},"started_at":"2026-01-01T00:01:00Z"}\n{"id":"run-3","status":"completed","metrics":{"val_loss":0.2},"started_at":"2026-01-01T00:02:00Z"}\n' >> "$tmpdir/.researchloop/scratchpad/runs.jsonl"

# Restore snapshot
$cli snapshot restore my-snapshot --force --dir "$tmpdir" 2>&1
if grep -q "run-2" "$tmpdir/.researchloop/scratchpad/runs.jsonl"; then
  echo "FAIL: restore should remove run-2 and run-3"
  exit 1
fi
if ! grep -q "run-1" "$tmpdir/.researchloop/scratchpad/runs.jsonl"; then
  echo "FAIL: restore should preserve run-1"
  exit 1
fi
echo "PASS: snapshot restore"

echo ""
echo "--- Test 4: snapshot diff ---"
printf '{"id":"run-2","status":"completed","metrics":{"val_loss":0.3},"started_at":"2026-01-01T00:01:00Z"}\n' >> "$tmpdir/.researchloop/scratchpad/runs.jsonl"
output_diff=$($cli snapshot diff my-snapshot --dir "$tmpdir" 2>&1)
echo "$output_diff"
echo "$output_diff" | grep -q "run-2" || { echo "FAIL: diff should show new runs"; exit 1; }
echo "PASS: snapshot diff"

echo ""
echo "--- Test 5: snapshot without force fails when new runs exist ---"
printf '{"id":"run-3","status":"completed","metrics":{"val_loss":0.2}}\n' >> "$tmpdir/.researchloop/scratchpad/runs.jsonl"
set +e
$cli snapshot restore my-snapshot --dir "$tmpdir" 2>&1
restore_exit=$?
set -e
if [ "$restore_exit" -eq 0 ]; then
  echo "FAIL: restore should fail when new runs exist"
  exit 1
fi
echo "PASS: restore refuses without force"

echo ""
echo "autoresearch test:snapshot passed"