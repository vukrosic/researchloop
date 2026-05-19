#!/usr/bin/env python3
"""Patch script for G37 data-fingerprint command"""
import re

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add parseDataGlobs and computeDataFingerprint helper functions before readTextIfExists
old_fn = 'function readTextIfExists(file) {'
new_fn = '''function parseDataGlobs(raw) {
  const match = raw.match(/^data_globs:\\s*([\\s\\S]*?)(?=^\\w|\\n#|$)/mi);
  if (!match) return null;
  const items = [];
  for (const line of match[1].split(/\\r?\\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const bulletMatch = trimmed.match(/^-\\s*["']?([^"'\\n]+)["']?\\s*$/);
    if (bulletMatch) items.push(bulletMatch[1].trim());
  }
  return items.length ? items : null;
}

function computeDataFingerprint(cwd, dataGlobs) {
  if (!dataGlobs || !dataGlobs.length) return null;
  const files = [];
  for (const glob of dataGlobs) {
    const pattern = glob.startsWith("/") ? glob : path.join(cwd, glob);
    const dir = path.dirname(pattern);
    const base = path.basename(pattern);
    if (base.includes("*")) {
      try {
        const escaped = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const findOutput = execSync("find \\"" + dir + "\\" -maxdepth 1 -name \\"" + escaped + "\\" -type f 2>/dev/null || true", { cwd, encoding: "utf8", timeout: 5000 });
        for (const f of findOutput.split("\\n").filter(Boolean)) {
          files.push(f);
        }
      } catch { /* no match */ }
    } else {
      if (fs.existsSync(pattern) && fs.statSync(pattern).isFile()) {
        files.push(pattern);
      }
    }
  }
  if (!files.length) return null;
  files.sort((a, b) => a.localeCompare(b));
  const hash = createHash("sha256");
  for (const file of files) {
    try {
      const stat = fs.statSync(file);
      hash.update(file);
      hash.update(String(stat.size));
      hash.update(String(stat.mtimeMs));
    } catch { /* skip */ }
  }
  return hash.digest("hex");
}

function cmdDataFingerprint() {
  const cwd = targetDir();
  const goalFile = path.join(cwd, ".researchloop", "goal.md");
  if (!fs.existsSync(goalFile)) {
    console.error("No goal.md found. Run `autoresearch goal` first.");
    process.exitCode = 1;
    return;
  }
  const raw = fs.readFileSync(goalFile, "utf8");
  const globs = parseDataGlobs(raw);
  const fp = computeDataFingerprint(cwd, globs);
  if (fp) console.log(fp);
  else console.log("No data_globs configured or no files matched.");
}

function readTextIfExists(file) {'''

if old_fn not in content:
    print("ERROR: readTextIfExists marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add data_fingerprint compute in cmdRun (after captureEnv)
old_env_line = '  const env = captureEnv(cwd);\n  const effectiveTimeoutMs'
new_env_line = '  const env = captureEnv(cwd);\n  const dataFingerprint = computeDataFingerprint(cwd, goalFields.data_globs);\n  const effectiveTimeoutMs'

if old_env_line not in content:
    print("ERROR: captureEnv marker not found")
    exit(1)

content = content.replace(old_env_line, new_env_line, 1)

# 3. Add data_fingerprint to row
old_row = '    notes: "",\n    env,\n  };\n  appendRunRow(cwd, row);'
new_row = '    notes: "",\n    env,\n    data_fingerprint: dataFingerprint,\n  };\n  appendRunRow(cwd, row);'

if old_row not in content:
    print("ERROR: row marker not found")
    exit(1)

content = content.replace(old_row, new_row, 1)

# 4. Add fingerprint warning to cmdCompare
old_compare = '  if (!scored.length) {\n    console.log(`No numeric values found for metric: ${resolvedMetric}`);\n    return;\n  }\n\n  scored.sort'
new_compare = '  if (!scored.length) {\n    console.log(`No numeric values found for metric: ${resolvedMetric}`);\n    return;\n  }\n\n  if (scored.length >= 2) {\n    const fp0 = scored[0].row.data_fingerprint;\n    const fp1 = scored[1].row.data_fingerprint;\n    if (fp0 && fp1 && fp0 !== fp1) {\n      console.error("WARNING: compared runs have different data fingerprints — data may have changed between runs");\n    }\n  }\n\n  scored.sort'

if old_compare not in content:
    print("ERROR: compare marker not found")
    exit(1)

content = content.replace(old_compare, new_compare, 1)

# 5. Add dispatch for data-fingerprint
old_dispatch = 'command === "prune") {\n    cmdPrune();\n  } else {'
new_dispatch = 'command === "prune") {\n    cmdPrune();\n  } else if (command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 6. Add help text
old_help = '  autoresearch prune [--older-than Nd] [--status STATUS] [--dry-run] [--no-keep-promoted] [--dir PATH]'
new_help = '  autoresearch prune [--older-than Nd] [--status STATUS] [--dry-run] [--no-keep-promoted] [--dir PATH]\n  autoresearch data-fingerprint [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G37 data-fingerprint patched successfully, lines:", content.count('\n'))