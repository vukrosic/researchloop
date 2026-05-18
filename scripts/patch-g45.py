#!/usr/bin/env python3
"""Patch script for G45 auto-suggest"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdSuggest function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdSuggest() {
  const metric = option("--metric", "value");
  const direction = option("--direction", "higher");
  const n = parseInt(option("--n", "3"), 10);
  const fmt = option("--format", "text");
  const cwd = targetDir();
  const ledgerPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");

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

  const valid = runs.filter((r) => {
    const val = r.metrics?.[metric] ?? r.value;
    return (r.status === "completed" || r.status === "promoted") && val != null && Number.isFinite(val);
  });

  if (valid.length < 3) {
    console.log("Not enough data to suggest experiments (need at least 3 runs).");
    return;
  }

  const paramKeys = new Set();
  for (const r of valid) {
    if (r.params && typeof r.params === "object") {
      for (const k of Object.keys(r.params)) paramKeys.add(k);
    }
  }

  const isLower = direction === "lower";
  const dirFactor = isLower ? 1 : -1;
  valid.sort((a, b) => {
    const aV = a.metrics?.[metric] ?? a.value;
    const bV = b.metrics?.[metric] ?? b.value;
    return (aV - bV) * dirFactor;
  });
  const bestRun = valid[0];
  const bestVal = bestRun.metrics?.[metric] ?? bestRun.value;

  const numericKeys = [];
  const catKeys = [];
  for (const k of paramKeys) {
    const vals = valid.map((r) => r.params?.[k]);
    if (vals.every((v) => v == null || typeof v === "number")) numericKeys.push(k);
    else catKeys.push(k);
  }

  const suggestions = [];

  for (const key of numericKeys) {
    const xs = valid.map((r) => r.params?.[key] ?? 0);
    const ys = valid.map((r) => r.metrics?.[metric] ?? r.value);

    const sortedYs = [...ys].sort((a, b) => (a - b) * dirFactor);
    const cutoff = sortedYs[Math.min(Math.ceil(xs.length * 0.3), sortedYs.length - 1)];
    let num = 0, den = 0;
    for (let i = 0; i < xs.length; i++) {
      const w = ys[i] <= cutoff ? 1 : 0.1;
      num += xs[i] * w;
      den += w;
    }
    const weightedCenter = den > 0 ? num / den : xs.reduce((s, v) => s + v, 0) / xs.length;

    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const xRange = xMax - xMin;

    const step = xRange > 0 ? (weightedCenter - (xMin + xMax) / 2) * 0.5 : weightedCenter * 0.2;
    const suggested = Math.max(xMin, Math.min(xMax, weightedCenter + step));
    const confidence = xRange > 0 ? Math.min(0.95, 1 - Math.abs(step) / (xRange + 1e-10)) : 0.3;

    suggestions.push({
      param: key,
      suggested,
      testedRange: [xMin, xMax],
      confidence: Math.max(0.1, confidence),
      reason: "weighted center of top 30% runs is " + weightedCenter.toFixed(4) + ", suggest exploring toward " + suggested.toFixed(4),
    });
  }

  for (const key of catKeys) {
    const seen = new Set(valid.map((r) => String(r.params?.[key] ?? "null")));
    const goalFile = path.join(cwd, ".researchloop", "goal.md");
    let candidates = [];
    try {
      const goalRaw = fs.readFileSync(goalFile, "utf8");
      const sweepMatch = goalRaw.match(/params:[\\s\\S]*?(?=^\\w|\\n#|$)/mi);
      if (sweepMatch) {
        const lines = sweepMatch[0].split("\\n");
        for (const line of lines) {
          const m = line.match(/^-\\s*(\\w+):\\s*\\[/);
          if (m) candidates.push(m[1]);
        }
      }
    } catch { /* no goal.yaml */ }

    if (candidates.length === 0) candidates = Array.from(seen);
    for (const cand of candidates) {
      if (!seen.has(cand)) {
        suggestions.push({
          param: key,
          suggested: cand,
          testedRange: null,
          confidence: 0.4,
          reason: "categorical '" + key + "' has no run with value '" + cand + "' yet",
        });
      }
    }
  }

  suggestions.sort((a, b) => b.confidence - a.confidence);
  const top = suggestions.slice(0, n);

  if (fmt === "json") {
    console.log(JSON.stringify({ metric, direction, bestRun: bestRun.id, bestValue: bestVal, suggestions: top }, null, 2));
    return;
  }

  const lines = [
    "# Auto-Suggest — " + metric + " (" + direction + ")",
    "",
    "**Best run:** " + bestRun.id + " | **" + metric + ":** " + (bestVal != null ? bestVal.toFixed(4) : "—"),
    "",
    "| # | Parameter | Suggested | Confidence | Reason |",
    "| ---: | --- | ---: | ---: | --- |",
  ];

  top.forEach((s, i) => {
    const suggested = s.testedRange != null ? Number(s.suggested).toFixed(6) : s.suggested;
    lines.push("| " + (i + 1) + " | " + s.param + " | " + suggested + " | " + (s.confidence * 100).toFixed(0) + "% | " + s.reason + " |");
  });

  if (top.length === 0) {
    lines.push("| | | | | |");
    lines.push("No specific suggestions yet. Try running more experiments first.");
  }

  console.log(lines.join("\\n"));
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "param-importance") {\n    cmdParamImportance();\n  } else {'
new_dispatch = 'command === "param-importance") {\n    cmdParamImportance();\n  } else if (command === "suggest") {\n    cmdSuggest();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found, searching...")
    # Try to find the actual dispatch
    idx = content.find('command === "param-importance")');
    if idx >= 0:
        print("Found param-importance at index", idx)
        print(repr(content[idx:idx+100]))
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text - use the exact content from the file
old_help = 'autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]\\n  autoresearch digest [--since DURATION] [--format text|json|markdown] [--dir PATH]'
new_help = 'autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]\\n  autoresearch digest [--since DURATION] [--format text|json|markdown] [--dir PATH]\\n  autoresearch param-importance [--metric METRIC] [--format table|json] [--dir PATH]\\n  autoresearch suggest [--n N] [--metric METRIC] [--direction higher|lower] [--format text|json] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found, searching...")
    idx = content.find('autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]');
    if idx >= 0:
        print("Found tag line at index", idx)
        print(repr(content[idx:idx+400]))
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G45 suggest patched successfully, lines:", content.count('\\n'))