#!/usr/bin/env python3
"""Patch script for G23 cost and wall-clock accounting"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add wall_seconds and est_cost_usd to the row in cmdRun
old_row = '''  const row = {
    id,
    timestamp: finishedAt,
    started_at: startedAt,
    status,
    agent: `autoresearch ${prefix}`,
    command: cmdText,
    exit_code: result.exitCode,
    log: path.relative(cwd, logFile),
    metrics,
    metric_history: metricSeries.length ? { [metricName]: metricSeries } : {},
    notes: "",
    env,
    data_fingerprint: dataFingerprint,
  };'''

new_row = '''  const wallSeconds = Math.round((new Date(finishedAt) - new Date(startedAt)) / 1000);
  let estCostUsd = null;
  const costConfigPath = path.join(cwd, ".researchloop", "cost.yaml");
  if (fs.existsSync(costConfigPath)) {
    try {
      const costRaw = fs.readFileSync(costConfigPath, "utf8");
      const hourlyMatch = costRaw.match(/hourly_usd:\\s*([0-9.]+)/i);
      if (hourlyMatch && hourlyMatch[1]) {
        estCostUsd = parseFloat((wallSeconds / 3600 * parseFloat(hourlyMatch[1])).toFixed(4));
      }
    } catch { /* skip */ }
  }

  const row = {
    id,
    timestamp: finishedAt,
    started_at: startedAt,
    ended_at: finishedAt,
    wall_seconds: wallSeconds,
    status,
    agent: `autoresearch ${prefix}`,
    command: cmdText,
    exit_code: result.exitCode,
    log: path.relative(cwd, logFile),
    metrics,
    metric_history: metricSeries.length ? { [metricName]: metricSeries } : {},
    notes: "",
    env,
    data_fingerprint: dataFingerprint,
    est_cost_usd: estCostUsd,
  };'''

if old_row not in content:
    print("ERROR: row marker not found")
    exit(1)

content = content.replace(old_row, new_row, 1)

# 2. Update cmdReport to show cost info
old_report = '  console.log(`runs: ${rows.length}`);\n  console.log(`complete: ${complete}`);\n  console.log(`parse_errors: ${errors}`);\n  if (parsed.length) {\n    console.log(`last: ${JSON.stringify(parsed[parsed.length - 1], null, 2)}`);'
new_report = '  console.log(`runs: ${rows.length}`);\n  console.log(`complete: ${complete}`);\n  console.log(`parse_errors: ${errors}`);\n  const totalWallSeconds = parsed.filter((r) => r && !r.parse_error && r.wall_seconds).reduce((s, r) => s + (r.wall_seconds || 0), 0);\n  if (totalWallSeconds > 0) {\n    console.log(`wall_time: ${Math.round(totalWallSeconds)}s total`);\n  }\n  if (parsed.length) {\n    const last = parsed[parsed.length - 1];\n    console.log(`last: ${JSON.stringify(last, null, 2)}`);\n  }'

if old_report not in content:
    print("ERROR: report output marker not found")
    exit(1)

content = content.replace(old_report, new_report, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G23 cost patched successfully, lines:", content.count('\n'))