#!/usr/bin/env python3
"""Patch script for G41 prune command"""
import re

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdPrune function after cmdDiffRuns (before readTextIfExists)
old_fn = 'function readTextIfExists(file) {'
new_fn = '''function cmdPrune() {
  const cwd = targetDir();
  const olderThan = option("--older-than", "30d");
  const statusFilter = option("--status", "discarded");
  const dryRun = hasFlag("--dry-run");
  const keepPromoted = !hasFlag("--no-keep-promoted");
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  const runsDir = path.join(cwd, ".researchloop", "scratchpad", "runs");

  if (!fs.existsSync(ledger)) {
    console.log("No runs recorded.");
    return;
  }

  const match = olderThan.match(/^(\\d+)(d|h)$/);
  if (!match) {
    console.error("Invalid --older-than format. Use Nd or Nh (e.g. 30d, 24h).");
    process.exitCode = 1;
    return;
  }
  const value = parseInt(match[1]);
  const unit = match[2];
  const nowMs = Date.now();
  const cutoffMs = nowMs - (unit === "d" ? value * 86400000 : value * 3600000);

  const rows = parseRunsLedger(ledger);
  const toPrune = [];

  for (const row of rows) {
    if (!row || row.parse_error) continue;
    if (row.pruned) continue;
    if (statusFilter && row.status !== statusFilter) continue;
    if (keepPromoted && (row.status === "promoted" || row.status === "kept")) continue;
    const ts = row.timestamp ? new Date(row.timestamp).getTime() : 0;
    if (ts < cutoffMs) {
      toPrune.push(row);
    }
  }

  if (toPrune.length === 0) {
    console.log("No runs match the criteria.");
    return;
  }

  let totalSize = 0;
  const dirsToDelete = [];

  for (const row of toPrune) {
    const runPath = path.join(runsDir, String(row.id));
    if (fs.existsSync(runPath)) {
      let size = 0;
      try {
        const stat = fs.statSync(runPath);
        if (stat.isDirectory()) {
          size = getDirSize(runPath);
        }
      } catch { /* skip */ }
      totalSize += size;
      dirsToDelete.push({ row, runPath, size });
    }
  }

  const sizeStr = totalSize >= 1073741824
    ? (totalSize / 1073741824).toFixed(2) + " GB"
    : (totalSize / 1048576).toFixed(1) + " MB";

  if (dryRun) {
    console.log("Dry run — would prune " + toPrune.length + " run(s), reclaim " + sizeStr + ":");
    for (const { row, runPath, size } of dirsToDelete) {
      const s = size >= 1048576 ? (size / 1048576).toFixed(1) + " MB" : (size / 1024).toFixed(0) + " KB";
      console.log("  " + row.id + " (" + s + ") — " + row.status);
    }
    return;
  }

  let deleted = 0;
  for (const { row, runPath } of dirsToDelete) {
    try {
      fs.rmSync(runPath, { recursive: true, force: true });
      deleted++;
    } catch { /* skip */ }
  }

  const updatedRows = rows.map((row) => {
    if (!row || row.parse_error) return row;
    if (toPrune.some((p) => p.id === row.id)) {
      return { ...row, pruned: true, pruned_at: new Date().toISOString() };
    }
    return row;
  });

  const tmpLedger = ledger + ".prune_tmp";
  fs.writeFileSync(tmpLedger, updatedRows.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
  fs.renameSync(tmpLedger, ledger);

  console.log("Pruned " + deleted + " run(s), reclaimed " + sizeStr + ".");
}

function getDirSize(dir) {
  let size = 0;
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        size += getDirSize(full);
      } else if (entry.isFile()) {
        try { size += fs.statSync(full).size; } catch { /* skip */ }
      }
    }
  } catch { /* skip */ }
  return size;
}

function readTextIfExists(file) {'''

if old_fn not in content:
    print("ERROR: readTextIfExists marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "diff-runs") {\n    cmdDiffRuns();\n  } else {'
new_dispatch = 'command === "diff-runs") {\n    cmdDiffRuns();\n  } else if (command === "prune") {\n    cmdPrune();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch diff-runs --id-a <id> --id-b <id> [--format text|json|markdown] [--dir PATH]'
new_help = '  autoresearch diff-runs --id-a <id> --id-b <id> [--format text|json|markdown] [--dir PATH]\n  autoresearch prune [--older-than Nd] [--status STATUS] [--dry-run] [--no-keep-promoted] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G41 prune patched successfully, lines:", content.count('\n'))