#!/usr/bin/env bash
set -euo pipefail

tmp_repo="$(mktemp -d)"
tmp_empty="$(mktemp -d)"
trap 'rm -rf "$tmp_repo" "$tmp_empty"' EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmp_repo" >/tmp/researchloop-resume-init.log
node ./bin/researchloop.js goal --dir "$tmp_repo" "lower val_loss" --metric val_loss --direction lower >/tmp/researchloop-resume-goal.log

cat > "$tmp_repo/.researchloop/baseline.md" <<'EOF'
# Baseline

## What To Record

- Baseline artifact: .researchloop/baseline.md
- Metric: val_loss
- Direction: lower
- Command or config: python train.py
- Model/data/training budget: 5 minutes
- System or accelerator: CPU smoke fixture
- Known limitations: tiny fixture only

## Frozen Surfaces

- Dataset: fixture
- Token budget or eval budget: 1024
- Model size: tiny
- Seed: 13
- Optimizer: adamw
- Architecture: transformer

## Notes

- val_loss: 2.41
EOF

mkdir -p "$tmp_repo/.researchloop/scratchpad/ideas"
cat > "$tmp_repo/.researchloop/scratchpad/ideas/2026-05-17-cosine-scheduler.md" <<'EOF'
# cosine-scheduler

proposed 2026-05-17
EOF
cat > "$tmp_repo/.researchloop/scratchpad/ideas/2026-05-17-token-mixer-swap.md" <<'EOF'
# token-mixer-swap

proposed 2026-05-17
EOF
cat > "$tmp_repo/.researchloop/scratchpad/ideas/2026-05-17-width-slimming.md" <<'EOF'
# width-slimming

proposed 2026-05-17
EOF

node ./bin/researchloop.js record --dir "$tmp_repo" --id lr-1e-4 --status complete --metric val_loss=2.43 --note "lr-1e-4" >/tmp/researchloop-resume-run-1.log
node ./bin/researchloop.js record --dir "$tmp_repo" --id lr-3e-4 --status complete --metric val_loss=2.39 --note "lr-3e-4" >/tmp/researchloop-resume-run-2.log
node ./bin/researchloop.js record --dir "$tmp_repo" --id dropout-0.2 --status crashed --metric val_loss=NaN --note "dropout-0.2" >/tmp/researchloop-resume-run-3.log

node --input-type=module - "$tmp_repo" <<'EOF'
import fs from "node:fs";
import path from "node:path";

const repo = process.argv[2];
const ledger = path.join(repo, ".researchloop", "scratchpad", "runs.jsonl");
const rows = fs
  .readFileSync(ledger, "utf8")
  .split("\n")
  .filter(Boolean)
  .map((line) => JSON.parse(line));

for (const row of rows) {
  if (row.id === "lr-1e-4") row.timestamp = "2026-05-17T20:00:00.000Z";
  if (row.id === "lr-3e-4") row.timestamp = "2026-05-17T23:00:00.000Z";
  if (row.id === "dropout-0.2") row.timestamp = "2026-05-18T00:15:00.000Z";
}

fs.writeFileSync(ledger, `${rows.map((row) => JSON.stringify(row)).join("\n")}\n`);
EOF

node ./bin/researchloop.js resume --dir "$tmp_repo" >/tmp/researchloop-resume-output.log
grep -q "^# RESUME CONTEXT" /tmp/researchloop-resume-output.log
grep -q "## Goal" /tmp/researchloop-resume-output.log
grep -q "lower val_loss" /tmp/researchloop-resume-output.log
grep -q "## Baseline" /tmp/researchloop-resume-output.log
grep -q "val_loss: 2.41" /tmp/researchloop-resume-output.log
grep -q "## Last 3 runs" /tmp/researchloop-resume-output.log
grep -q "lr-1e-4" /tmp/researchloop-resume-output.log
grep -q "lr-3e-4" /tmp/researchloop-resume-output.log
grep -q "dropout-0.2" /tmp/researchloop-resume-output.log
grep -q "done" /tmp/researchloop-resume-output.log
grep -q "crashed" /tmp/researchloop-resume-output.log
grep -q "## Open ideas (3)" /tmp/researchloop-resume-output.log
grep -q "cosine-scheduler" /tmp/researchloop-resume-output.log
grep -q "token-mixer-swap" /tmp/researchloop-resume-output.log
grep -q "width-slimming" /tmp/researchloop-resume-output.log
grep -q "## Next 3 untried, ranked by likely value" /tmp/researchloop-resume-output.log
grep -q "lr-2e-4" /tmp/researchloop-resume-output.log
grep -q "dropout-0.1" /tmp/researchloop-resume-output.log
grep -q "smaller than crashed 0.2" /tmp/researchloop-resume-output.log

node ./bin/researchloop.js resume --dir "$tmp_repo" --since 2026-05-17T22:00:00Z --last 2 >/tmp/researchloop-resume-since.log
grep -q "## Last 2 runs" /tmp/researchloop-resume-since.log
grep -q "lr-3e-4" /tmp/researchloop-resume-since.log
grep -q "dropout-0.2" /tmp/researchloop-resume-since.log
if grep -q "lr-1e-4" /tmp/researchloop-resume-since.log; then
  echo "FAIL: --since should filter out the older run"
  cat /tmp/researchloop-resume-since.log
  exit 1
fi

node ./bin/researchloop.js resume --dir "$tmp_repo" --write >/tmp/researchloop-resume-write.log
grep -q "Resume context written to" /tmp/researchloop-resume-write.log
test -f "$tmp_repo/.researchloop/RESUME.md"
grep -q "^# RESUME CONTEXT" "$tmp_repo/.researchloop/RESUME.md"
grep -q "lr-3e-4" "$tmp_repo/.researchloop/RESUME.md"
if grep -q "^# RESUME CONTEXT" /tmp/researchloop-resume-write.log; then
  echo "FAIL: --write should not print the markdown block to stdout"
  cat /tmp/researchloop-resume-write.log
  exit 1
fi

node ./bin/researchloop.js init --agent codex --dir "$tmp_empty" >/tmp/researchloop-resume-empty-init.log
: > "$tmp_empty/.researchloop/scratchpad/runs.jsonl"
node ./bin/researchloop.js resume --dir "$tmp_empty" >/tmp/researchloop-resume-empty.log
grep -q "no state yet — run autoresearch goal first" /tmp/researchloop-resume-empty.log

echo "autoresearch test:resume passed"
