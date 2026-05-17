#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cli="node $repo_root/bin/researchloop.js"

echo "=== G50: autoresearch archive ==="

$cli init --agent codex --dir "$tmpdir" >/dev/null
$cli goal --dir "$tmpdir" "lower val_loss" --metric val_loss --direction lower --baseline "echo val_loss=0.5" --evaluation "echo val_loss=0.4" >/dev/null

# Create some runs
echo '{"id":"run-1","status":"completed","metrics":{"val_loss":0.5},"started_at":"2026-01-01T00:00:00Z"}' > "$tmpdir/.researchloop/scratchpad/runs.jsonl"

echo "--- Test 1: archive creates file ---"
echo "runs.jsonl exists: $(cat "$tmpdir/.researchloop/scratchpad/runs.jsonl")"
$cli archive --dir "$tmpdir" 2>&1
archive_file=$(ls -t "$tmpdir"/*.tar.gz 2>/dev/null | head -1)
if [ -z "$archive_file" ]; then
  echo "FAIL: no archive file created"
  exit 1
fi
echo "Archive file: $archive_file"
echo "PASS: archive creates file"

echo ""
echo "--- Test 2: archive contents ---"
$cli archive --name test-archive --dir "$tmpdir" --force 2>&1
if tar -tzf "$tmpdir/test-archive.tar.gz" 2>/dev/null | grep -q "runs.jsonl"; then
  echo "PASS: archive contains runs.jsonl"
else
  echo "FAIL: runs.jsonl not in archive"
  exit 1
fi

echo ""
echo "--- Test 3: restore roundtrip ---"
# Create run file and archive it
mkdir -p "$tmpdir/.researchloop/scratchpad"
echo '{"id":"run-2","status":"completed","metrics":{"val_loss":0.6}}' > "$tmpdir/.researchloop/scratchpad/runs.jsonl"
$cli archive --name restore-test --dir "$tmpdir" --force 2>&1

# Clear and restore (tar extracts into .researchloop from archive)
rm -rf "$tmpdir/.researchloop"
$cli archive restore --file "$tmpdir/restore-test.tar.gz" --dir "$tmpdir" --force 2>&1

if [ -f "$tmpdir/.researchloop/scratchpad/runs.jsonl" ]; then
  if grep -q "run-2" "$tmpdir/.researchloop/scratchpad/runs.jsonl"; then
    echo "PASS: restore preserves runs"
  else
    echo "FAIL: runs not preserved after restore"
    exit 1
  fi
else
  echo "FAIL: .researchloop not restored"
  exit 1
fi

echo ""
echo "--- Test 4: restore into existing dir fails without force ---"
mkdir -p "$tmpdir/.researchloop"
set +e
$cli archive restore --file "$tmpdir/restore-test.tar.gz" --dir "$tmpdir" 2>&1
restore_exit=$?
set -e
if [ "$restore_exit" -eq 0 ]; then
  echo "FAIL: restore should fail into existing dir"
  exit 1
fi
echo "PASS: restore into existing dir fails without force"

echo ""
echo "autoresearch test:archive passed"