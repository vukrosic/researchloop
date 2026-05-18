#!/usr/bin/env python3
"""Patch script for G52 param-importance"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdParamImportance function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdParamImportance() {
  const metric = option("--metric", "value");
  const format = option("--format", "table");
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

  // Filter to runs with the target metric
  const valid = runs.filter((r) => {
    const val = r.metrics?.[metric] ?? r.value;
    return r.status === "completed" || r.status === "promoted";
  });

  if (valid.length < 5) {
    console.log("Insufficient data (" + valid.length + " runs, need at least 5).");
    return;
  }

  // Collect all param keys
  const paramKeys = new Set();
  for (const r of valid) {
    if (r.params && typeof r.params === "object") {
      for (const k of Object.keys(r.params)) {
        paramKeys.add(k);
      }
    }
  }

  // Separate numeric and categorical params
  const numericParams = [];
  const categoricalParams = [];
  for (const key of paramKeys) {
    const vals = valid.map((r) => r.params?.[key]);
    const isNumeric = vals.every((v) => v == null || typeof v === "number");
    if (isNumeric) numericParams.push(key);
    else categoricalParams.push(key);
  }

  // Pearson correlation for numeric params
  function pearsonr(xs, ys) {
    const n = xs.length;
    if (n === 0) return 0;
    const xMean = xs.reduce((s, v) => s + v, 0) / n;
    const yMean = ys.reduce((s, v) => s + v, 0) / n;
    let num = 0, denX = 0, denY = 0;
    for (let i = 0; i < n; i++) {
      const dx = xs[i] - xMean;
      const dy = ys[i] - yMean;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }
    const den = Math.sqrt(denX * denY);
    return den === 0 ? 0 : num / den;
  }

  // ANOVA-style for categorical params
  function anovaSummary(key) {
    const buckets = {};
    for (const r of valid) {
      const cat = String(r.params?.[key] ?? "null");
      if (!buckets[cat]) buckets[cat] = [];
      const val = r.metrics?.[metric] ?? r.value;
      if (val != null) buckets[cat].push(val);
    }
    return Object.entries(buckets).map(([cat, vals]) => {
      const mean = vals.length ? vals.reduce((s, v) => s + v, 0) / vals.length : null;
      const spread = vals.length > 1
        ? Math.sqrt(vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length)
        : 0;
      return { category: cat, count: vals.length, mean, spread };
    });
  }

  const metricVals = valid.map((r) => r.metrics?.[metric] ?? r.value);
  const numericResults = numericParams.map((key) => {
    const xs = valid.map((r) => r.params?.[key] ?? 0);
    const r = pearsonr(xs, metricVals);
    return { param: key, correlation: r, type: "numeric" };
  });

  const categoricalResults = categoricalParams.map((key) => {
    const summary = anovaSummary(key);
    const grandMean = metricVals.filter((v) => v != null).reduce((s, v) => s + v, 0)
      / metricVals.filter((v) => v != null).length;
    const betweenVar = summary.reduce((s, { mean, count }) => {
      if (mean == null) return s;
      return s + count * (mean - grandMean) ** 2;
    }, 0) / valid.length;
    const totalVar = metricVals.filter((v) => v != null).reduce((s, v) => s + (v - grandMean) ** 2, 0)
      / metricVals.filter((v) => v != null).length;
    const etaSq = totalVar === 0 ? 0 : betweenVar / totalVar;
    return { param: key, etaSquared: etaSq, type: "categorical", summary };
  });

  // Sort numeric by |correlation| desc
  numericResults.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));

  if (format === "json") {
    const out = { metric, nRuns: valid.length, numeric: numericResults, categorical: categoricalResults };
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  // Table output
  const lines = ["# Parameter Importance — " + metric, ""];
  lines.push("**Runs analyzed:** " + valid.length + " | **Metric:** " + metric + "");
  lines.push("");

  if (numericParams.length) {
    lines.push("## Numeric Parameters (Pearson r)");
    lines.push("");
    lines.push("| Parameter | r | |r| |");
    lines.push("| --- | ---: | ---: |");
    for (const { param, correlation } of numericResults) {
      lines.push("| " + param + " | " + correlation.toFixed(4) + " | " + Math.abs(correlation).toFixed(4) + " |");
    }
    lines.push("");
  }

  if (categoricalParams.length) {
    lines.push("## Categorical Parameters (eta^2)");
    lines.push("");
    lines.push("| Parameter | eta^2 | Categories |");
    lines.push("| --- | ---: | --- |");
    for (const { param, etaSquared, summary } of categoricalResults) {
      const cats = summary.map((s) => s.category + " (" + s.count + ")").join(", ");
      lines.push("| " + param + " | " + etaSquared.toFixed(4) + " | " + cats + " |");
    }
    lines.push("");
    for (const { param, summary } of categoricalResults) {
      lines.push("### " + param + "");
      lines.push("");
      lines.push("| Category | Count | Mean " + metric + " | Spread |");
      lines.push("| --- | ---: | ---: | ---: |");
      for (const { category, count, mean, spread } of summary) {
        lines.push("| " + category + " | " + count + " | " + (mean != null ? mean.toFixed(4) : "—") + " | " + (spread != null ? spread.toFixed(4) : "—") + " |");
      }
      lines.push("");
    }
  }

  if (numericParams.length === 0 && categoricalParams.length === 0) {
    lines.push("No parameter fields found in completed runs.");
  }

  console.log(lines.join("\\n"));
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "digest") {\n    cmdDigest();\n  } else {'
new_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "digest") {\n    cmdDigest();\n  } else if (command === "param-importance") {\n    cmdParamImportance();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]'
new_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]\n  autoresearch param-importance [--metric METRIC] [--format table|json] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G52 param-importance patched successfully, lines:", content.count('\\n'))