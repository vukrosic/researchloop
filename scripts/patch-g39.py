#!/usr/bin/env python3
"""Patch script for G39 failures command"""
import re

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdFailures function after cmdTeam (before cmdHelp)
old_fn = 'console.log("Next: create branches or worktrees, then hand each lane to a separate agent.");\n}\n\nfunction cmdHelp()'
new_fn = 'console.log("Next: create branches or worktrees, then hand each lane to a separate agent.");\n}\n\nfunction loadFailurePatterns(cwd) {\n  const patternFile = path.join(cwd, ".researchloop", "failure-patterns.yaml");\n  if (!fs.existsSync(patternFile)) return [];\n  try {\n    const raw = fs.readFileSync(patternFile, "utf8");\n    const patterns = [];\n    for (const line of raw.split("\\n")) {\n      const km = line.match(/^\\s+-\\s+key:\\s*["\']?([^"\'\\n]+)["\']?\\s*$/);\n      const sm = line.match(/^\\s+suggestion:\\s*(.+)\\s*$/);\n      if (km) patterns.push({ key: km[1], suggestion: "" });\n      else if (sm && patterns.length) patterns[patterns.length-1].suggestion = sm[1];\n    }\n    return patterns;\n  } catch { return []; }\n}\n\nfunction cmdFailures() {\n  const cwd = targetDir();\n  const topN = Math.max(1, Math.min(100, Number(option("--top", 10)) || 10));\n  const asJson = hasFlag("--format") && option("--format") === "json";\n  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");\n  const patterns = loadFailurePatterns(cwd);\n\n  if (!fs.existsSync(ledger)) {\n    process.stdout.write(asJson ? "[]\\n" : "No runs recorded.\\n");\n    return;\n  }\n\n  const rows = [];\n  for (const line of fs.readFileSync(ledger, "utf8").split("\\n")) {\n    if (!line.trim()) continue;\n    try { rows.push(JSON.parse(line)); } catch { /* skip */ }\n  }\n\n  const failed = rows.filter((r) => r.status === "failed" || r.status === "killed_by_rule" || r.status === "killed_by_safety");\n  if (!failed.length) {\n    process.stdout.write(asJson ? "[]\\n" : "No failed runs found.\\n");\n    return;\n  }\n\n  const clusters = {};\n  for (const run of failed) {\n    const kr = run.kill_reason || "";\n    const lower = kr.toLowerCase();\n    let clusterKey = kr || "unknown";\n    for (const p of patterns) {\n      if (lower.includes(p.key.toLowerCase())) { clusterKey = p.key; break; }\n    }\n    if (!clusters[clusterKey]) {\n      const pat = patterns.find((p) => p.key.toLowerCase() === clusterKey.toLowerCase());\n      clusters[clusterKey] = { key: clusterKey, count: 0, runIds: [], suggestion: pat ? pat.suggestion : "Inspect stderr for the actual error." };\n    }\n    clusters[clusterKey].count++;\n    clusters[clusterKey].runIds.push(run.id);\n  }\n\n  const sorted = Object.values(clusters).sort((a, b) => b.count - a.count);\n  const top = sorted.slice(0, topN);\n\n  if (asJson) {\n    process.stdout.write(JSON.stringify({ clusters: top, total: failed.length }, null, 2) + "\\n");\n  } else {\n    console.log("=== Failure Clusters ===");\n    console.log("Total failures: " + failed.length);\n    console.log("Clusters: " + sorted.length);\n    console.log("");\n    for (const c of top) {\n      console.log("## " + c.key + " (" + c.count + " runs)");\n      console.log("  Suggestion: " + c.suggestion);\n      console.log("  Examples: " + c.runIds.slice(0, 3).join(", "));\n      console.log("");\n    }\n  }\n}\n\nfunction cmdHelp()'

if old_fn not in content:
    print("ERROR: function marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "report") {\n    cmdReport();\n  } else {\n    console.error(`Unknown command: ${command}`);'
new_dispatch = 'command === "report") {\n    cmdReport();\n  } else if (command === "failures") {\n    cmdFailures();\n  } else {\n    console.error(`Unknown command: ${command}`);'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch report [--dir PATH]'
new_help = '  autoresearch report [--dir PATH]\n  autoresearch failures [--top N] [--format json] [--dir PATH]'

if old_help not in content:
    print("ERROR: help not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G39 failures patched successfully, lines:", content.count('\n'))