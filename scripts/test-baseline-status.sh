#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cli="node $repo_root/bin/researchloop.js"

blank="$tmpdir/blank"
mkdir -p "$blank"

set +e
missing_output="$($cli baseline-status --dir "$blank" 2>&1)"
missing_exit=$?
set -e
if [ "$missing_exit" -eq 0 ]; then
  echo "expected missing baseline to exit nonzero"
  exit 1
fi
if [ "$missing_output" != "missing baseline: .researchloop/baseline.md not found" ]; then
  echo "unexpected missing baseline output: $missing_output"
  exit 1
fi

partial="$tmpdir/partial"
mkdir -p "$partial/.researchloop"
cat >"$partial/.researchloop/baseline.md" <<'EOF'
# Baseline

## What To Record

- Baseline artifact:
- Metric: val_loss
- Direction: lower
- Command or config:
- Known limitations:

## Frozen Surfaces

- Dataset:
- Seed:
EOF

set +e
partial_output="$($cli baseline-status --dir "$partial" 2>&1)"
partial_exit=$?
set -e
if [ "$partial_exit" -eq 0 ]; then
  echo "expected partial baseline to exit nonzero"
  exit 1
fi
if [ "$partial_output" != "partial baseline: missing command/config/artifact, frozen variables, caveats" ]; then
  echo "unexpected partial baseline output: $partial_output"
  exit 1
fi

complete="$tmpdir/complete"
mkdir -p "$complete/.researchloop"
cat >"$complete/.researchloop/baseline.md" <<'EOF'
# Baseline

Status: current

## What To Record

- Baseline artifact: reports/baseline.json
- Metric: val_loss
- Direction: lower
- Command or config: python train.py --epochs 1
- Model/data/training budget: 1 epoch on tiny fixture
- System or accelerator: CPU
- Known limitations: CPU-only smoke baseline

## Frozen Surfaces

- Dataset: tiny-shakespeare
- Token budget or eval budget: 512 tokens
- Model size: 12M
- Seed: 13
- Optimizer: AdamW
- Architecture: baseline transformer
EOF

complete_output="$($cli baseline-status --dir "$complete")"
printf '%s\n' "$complete_output" | grep -q "baseline complete:"
printf '%s\n' "$complete_output" | grep -q "metric val_loss (lower)"
printf '%s\n' "$complete_output" | grep -q "command/config python train.py --epochs 1"
printf '%s\n' "$complete_output" | grep -q "artifact reports/baseline.json"
printf '%s\n' "$complete_output" | grep -q "Dataset=tiny-shakespeare"
printf '%s\n' "$complete_output" | grep -q "caveats CPU-only smoke baseline"
if printf '%s\n' "$complete_output" | grep -q "not documented"; then
  echo "complete summary invented placeholder text"
  exit 1
fi

json_output="$($cli baseline-status --dir "$complete" --format json)"
node -e '
const row = JSON.parse(process.argv[1]);
if (!row.present || !row.complete) process.exit(1);
if (row.missing.length !== 0) process.exit(1);
if (row.fields.metric !== "val_loss") process.exit(1);
if (row.fields.commandOrConfig !== "python train.py --epochs 1") process.exit(1);
if (!row.summary.includes("CPU-only smoke baseline")) process.exit(1);
' "$json_output"

echo "autoresearch test:baseline-status passed"
