#!/usr/bin/env python3
"""Patch script for G51 experiment digest"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdDigest function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdDigest() {
  const sinceStr = option("--since", "24h");
  const format = option("--format", "markdown");
  const cwd = targetDir();
  const ledgerPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");

  // Parse --since duration
  const sinceMatch = sinceStr.match(/^(\\d+)([hdm])?$/);
  let sinceHours = 24;
  if (sinceMatch) {
    const val = parseInt(sinceMatch[1], 10);
    const unit = sinceMatch[2] || "h";
    if (unit === "h") sinceHours = val;
    else if (unit === "d") sinceHours = val * 24;
    else if (unit === "m") sinceHours = val * 60 * 24 * 30;
  }
  const sinceMs = sinceHours * 60 * 60 * 1000;
  const cutoff = Date.now() - sinceMs;

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

  // Filter by timestamp
  const recent = runs.filter((r) => {
    if (!r.timestamp) return false;
    const ts = new Date(r.timestamp).getTime();
    return ts >= cutoff;
  });

  if (recent.length === 0) {
    console.log("No runs in the last " + sinceStr + ".");
    return;
  }

  const completed = recent.filter((r) => r.status === "completed" || r.status === "promoted");
  const failed = recent.filter((r) => r.status === "failed" || r.status === "killed");

  const metrics = recent
    .map((r) => r.metrics?.value ?? r.value)
    .filter((v) => v != null && Number.isFinite(v));

  const best = metrics.length ? Math.max(...metrics) : null;
  const worst = metrics.length ? Math.min(...metrics) : null;

  const wallSecs = recent.reduce((s, r) => s + (r.wall_seconds || 0), 0);
  const cost = recent.reduce((s, r) => s + (r.est_cost_usd || 0), 0);

  if (format === "json") {
    const out = {
      period: sinceStr,
      totalRuns: recent.length,
      completed: completed.length,
      failed: failed.length,
      bestMetric: best,
      worstMetric: worst,
      totalWallSeconds: wallSecs,
      totalEstimatedCost: cost > 0 ? cost : null,
    };
    console.log(JSON.stringify(out, null, 2));
  } else {
    // Markdown
    const lines = [
      "# Experiment Digest — last " + sinceStr,
      "",
      "| Metric | Value |",
      "| --- | --- |",
      "| Runs total | " + recent.length + " |",
      "| Completed | " + completed.length + " |",
      "| Failed | " + failed.length + " |",
      "| Best metric | " + (best != null ? best.toFixed(4) : "—") + " |",
      "| Worst metric | " + (worst != null ? worst.toFixed(4) : "—") + " |",
      "| Total wall time | " + wallSecs.toFixed(0) + "s |",
      "| Total est. cost | " + (cost > 0 ? "$" + cost.toFixed(2) : "—") + " |",
    ];
    console.log(lines.join("\\n"));
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else {'
new_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "digest") {\n    cmdDigest();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]'
new_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]\\n  autoresearch digest [--since DURATION] [--format text|json|markdown] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G51 digest patched successfully, lines:", content.count('\\n'))