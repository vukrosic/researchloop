#!/usr/bin/env python3
"""Patch script for G47 persistent leaderboard"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdLeaderboard function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdLeaderboard() {
  const metric = option("--metric", "value");
  const direction = option("--direction", "higher");
  const top = parseInt(option("--top", "10"), 10);
  const doWrite = hasFlag("--write");
  const cwd = targetDir();
  const ledgerPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  const lbPath = path.join(cwd, ".researchloop", "LEADERBOARD.md");

  let runs = [];
  try {
    const raw = fs.readFileSync(ledgerPath, "utf8");
    for (const line of raw.split("\\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        runs.push(JSON.parse(trimmed));
      } catch { /* skip */ }
    }
  } catch {
    runs = [];
  }

  // Filter to completed runs with the target metric
  const filtered = runs.filter((r) => {
    if (r.status === "completed" || r.status === "promoted") {
      const val = r.metrics?.[metric] ?? r.value;
      return val != null && typeof val === "number" && Number.isFinite(val);
    }
    return false;
  });

  // Sort
  const dirFactor = direction === "lower" ? 1 : -1;
  filtered.sort((a, b) => {
    const aVal = a.metrics?.[metric] ?? a.value;
    const bVal = b.metrics?.[metric] ?? b.value;
    return (aVal - bVal) * dirFactor;
  });

  const topRuns = filtered.slice(0, top);

  // Render markdown
  const lines = [
    "# Leaderboard",
    "",
    `**Metric:** \\`${metric}\\` | **Direction:** ${direction} | **Generated:** ${new Date().toISOString()}`,
    "",
    "| Rank | Run ID | ${metric} | Status | Date |",
    "| ---: | --- | ---: | --- | --- |",
  ];

  topRuns.forEach((run, i) => {
    const val = run.metrics?.[metric] ?? run.value;
    const valStr = val != null ? val.toFixed(4) : "—";
    const runId = run.id ? run.id.substring(0, 8) : "?";
    const status = run.status || "?";
    const date = run.timestamp ? run.timestamp.substring(0, 10) : "?";
    const params = run.params ? JSON.stringify(run.params).substring(0, 40) : "";
    lines.push("| " + (i + 1) + " | " + runId + " | " + valStr + " | " + status + " | " + date + " |");
  });

  const md = lines.join("\\n");

  if (doWrite) {
    fs.writeFileSync(lbPath, md + "\\n");
    console.log("Leaderboard written to .researchloop/LEADERBOARD.md");
  } else {
    console.log(md);
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else {'
new_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "leaderboard") {\n    cmdLeaderboard();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]'
new_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]\n  autoresearch leaderboard [--metric METRIC] [--direction higher|lower] [--top N] [--write] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G47 leaderboard patched successfully, lines:", content.count('\\n'))