#!/usr/bin/env python3
"""Patch script for G13 query command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdQuery function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdQuery() {
  const rawExpr = positionalText();
  const fmt = option("--format", "table");
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

  if (!rawExpr) {
    console.error("Usage: autoresearch query \\"<expression>" [--format jsonl|table] [--dir PATH]");
    process.exitCode = 1;
    return;
  }

  function getNestedValue(obj, path) {
    return path.split(".").reduce((o, k) => (o && o[k] !== undefined ? o[k] : null), obj);
  }

  function evaluatePredicate(lhs, op, rhs) {
    if (lhs === null || lhs === undefined) return false;
    switch (op) {
      case "=": return String(lhs) === String(rhs);
      case "!=": return String(lhs) !== String(rhs);
      case "<": return Number(lhs) < Number(rhs);
      case "<=": return Number(lhs) <= Number(rhs);
      case ">": return Number(lhs) > Number(rhs);
      case ">=": return Number(lhs) >= Number(rhs);
      case "contains": return String(lhs).toLowerCase().includes(String(rhs).toLowerCase());
      case "between": {
        const m = String(rhs).match(/^(.+)\\.\\.(.+)$/);
        if (!m) return false;
        const v = Number(lhs);
        return v >= Number(m[1]) && v <= Number(m[2]);
      }
      default: return false;
    }
  }

  const predicates = [];
  let sortField = null;
  let sortDir = "asc";
  let limitCount = 100;

  const tokens = rawExpr.trim().split(/\\s+/);
  let i = 0;

  if (tokens[i] === "where") {
    i++;
    while (i < tokens.length) {
      if (tokens[i] === "sort-by") {
        i++;
        if (i >= tokens.length) { console.error("query: sort-by requires a field"); process.exitCode = 1; return; }
        sortField = tokens[i];
        i++;
        if (i < tokens.length && (tokens[i] === "asc" || tokens[i] === "desc")) {
          sortDir = tokens[i]; i++;
        }
        break;
      }
      if (tokens[i] === "limit") {
        i++;
        if (i >= tokens.length) { console.error("query: limit requires a number"); process.exitCode = 1; return; }
        limitCount = parseInt(tokens[i], 10);
        i++;
        break;
      }
      if (i + 2 >= tokens.length) { console.error("query: predicate requires field, operator, value"); process.exitCode = 1; return; }
      const field = tokens[i]; i++;
      const op = tokens[i]; i++;
      const value = tokens[i]; i++;
      const validOps = ["=", "!=", "<", "<=", ">", ">=", "contains", "between"];
      if (!validOps.includes(op)) { console.error("query: unknown operator " + op); process.exitCode = 1; return; }
      predicates.push({ field, op, value });
      if (tokens[i] === "and") { i++; }
    }
  } else {
    console.error("query: expression must start with \\"where\\"");
    process.exitCode = 1;
    return;
  }

  let result = runs.filter((row) => {
    return predicates.every(({ field, op, value }) => {
      const v = getNestedValue(row, field);
      return evaluatePredicate(v, op, value);
    });
  });

  if (sortField) {
    result.sort((a, b) => {
      const aV = getNestedValue(a, sortField);
      const bV = getNestedValue(b, sortField);
      const aN = Number(aV), bN = Number(bV);
      const cmp = isNaN(aN) || isNaN(bN) ? String(aV).localeCompare(String(bV)) : aN - bN;
      return sortDir === "desc" ? -cmp : cmp;
    });
  }

  result = result.slice(0, limitCount);

  if (fmt === "jsonl") {
    for (const row of result) {
      process.stdout.write(JSON.stringify(row) + "\\n");
    }
    return;
  }

  if (result.length === 0) {
    console.log("(no rows match)");
    return;
  }

  const allKeys = new Set(["id", "status", "timestamp", "value"]);
  for (const row of result) {
    if (row.metrics) for (const k of Object.keys(row.metrics)) allKeys.add("metrics." + k);
    if (row.params) for (const k of Object.keys(row.params)) allKeys.add("params." + k);
  }
  const cols = Array.from(allKeys);

  const lines = [];
  lines.push("| " + cols.join(" | ") + " |");
  lines.push("| " + cols.map(() => "---").join(" | ") + " |");
  for (const row of result) {
    lines.push("| " + cols.map((c) => {
      const v = c === "id" ? row.id : c === "status" ? row.status : c === "timestamp" ? (row.timestamp || "") : getNestedValue(row, c);
      return v != null ? String(v) : "";
    }).join(" | ") + " |");
  }
  console.log(lines.join("\\n"));
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch after suggest
old_dispatch = 'command === "suggest") {\n    cmdSuggest();\n  } else {'
new_dispatch = 'command === "suggest") {\n    cmdSuggest();\n  } else if (command === "query") {\n    cmdQuery();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = 'autoresearch suggest [--n N] [--metric METRIC] [--direction higher|lower] [--format text|json] [--dir PATH]'
new_help = 'autoresearch suggest [--n N] [--metric METRIC] [--direction higher|lower] [--format text|json] [--dir PATH]\n  autoresearch query "<expression>" [--format jsonl|table] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G13 query patched successfully")