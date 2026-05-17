#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/dev/null 2>&1
node ./bin/researchloop.js record --id run-a --status complete --metric val_loss=0.5 --dir "$tmpdir" 2>&1

echo "=== Test: add tag ==="
node ./bin/researchloop.js tag --id run-a --add "baseline" --dir "$tmpdir" 2>&1

echo ""
echo "=== Test: list tags ==="
node ./bin/researchloop.js tag --list --dir "$tmpdir" 2>&1

echo ""
echo "=== Test: add another tag ==="
node ./bin/researchloop.js tag --id run-a --add "low-loss" --dir "$tmpdir" 2>&1

echo ""
echo "=== Test: show run tags ==="
node ./bin/researchloop.js tag --id run-a --dir "$tmpdir" 2>&1

echo ""
echo "=== Test: remove tag ==="
node ./bin/researchloop.js tag --id run-a --remove "baseline" --dir "$tmpdir" 2>&1

echo ""
echo "ALL TESTS PASSED"