#!/usr/bin/env python3
"""Patch script for G27 baseline --lock"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdBaselineLock function before cmdBaselineStatus
old_fn = 'function cmdBaselineStatus() {'
new_fn = '''function cmdBaselineLock() {
  const cwd = targetDir();
  const doUnlock = hasFlag("--unlock");
  const baselineDir = path.join(cwd, ".researchloop");
  const baselineMd = path.join(baselineDir, "baseline.md");
  const lockFile = path.join(baselineDir, "baseline.lock");

  if (doUnlock) {
    try {
      fs.unlinkSync(lockFile);
      console.log("Baseline lock removed.");
    } catch {
      console.error("No baseline lock to remove.");
      process.exitCode = 1;
    }
    return;
  }

  if (!fs.existsSync(baselineMd)) {
    console.error("No baseline.md found. Run `autoresearch baseline-status` first.");
    process.exitCode = 1;
    return;
  }

  const raw = fs.readFileSync(baselineMd, "utf8");
  const whatToRecord = extractSection(raw, "What To Record");
  const metric = extractValue(whatToRecord, "Metric");
  const direction = extractValue(whatToRecord, "Direction");
  const command = extractValue(whatToRecord, "Command or config");

  // Get current git SHA
  let gitSha = "unknown";
  let gitDirty = false;
  try {
    const gitDir = path.join(cwd, ".git");
    if (fs.existsSync(gitDir)) {
      const sha = fs.readFileSync(path.join(gitDir, "HEAD"), "utf8").trim();
      if (sha.startsWith("ref: ")) {
        const ref = sha.slice(5);
        const refPath = path.join(gitDir, ref);
        if (fs.existsSync(refPath)) {
          gitSha = fs.readFileSync(refPath, "utf8").trim().slice(0, 8);
        }
      } else {
        gitSha = sha.slice(0, 8);
      }
      const status = fs.readFileSync(path.join(gitDir, "HEAD"), "utf8").trim();
      // Check for uncommitted changes
      const indexFile = path.join(gitDir, "index");
      if (fs.existsSync(indexFile)) {
        // Simple heuristic: if index exists and is not empty, dirty
        const stat = fs.statSync(indexFile);
        gitDirty = stat.size > 0;
      }
    }
  } catch { /* ignore */ }

  // Get env hash from G14 env capture (if available)
  let envHash = null;
  try {
    const envJsonPath = path.join(baselineDir, "scratchpad", "runs.jsonl");
    if (fs.existsSync(envJsonPath)) {
      const lines = fs.readFileSync(envJsonPath, "utf8").split("\\n").filter(l => l.trim());
      if (lines.length > 0) {
        const lastRow = JSON.parse(lines[lines.length - 1]);
        if (lastRow.env && lastRow.env.env_hash) {
          envHash = lastRow.env.env_hash;
        }
      }
    }
  } catch { /* ignore */ }

  // Get the best completed run's metric value from runs.jsonl
  let baselineValue = null;
  try {
    const runsPath = path.join(baselineDir, "scratchpad", "runs.jsonl");
    if (fs.existsSync(runsPath)) {
      const lines = fs.readFileSync(runsPath, "utf8").split("\\n").filter(l => l.trim());
      for (const line of lines.reverse()) {
        const row = JSON.parse(line);
        if (row.status === "completed" && row.value != null) {
          baselineValue = row.value;
          break;
        }
      }
    }
  } catch { /* ignore */ }

  const lockData = {
    locked_at: new Date().toISOString(),
    metric,
    direction,
    command,
    git_sha: gitSha,
    git_dirty: gitDirty,
    env_hash: envHash,
    baseline_value: baselineValue,
  };

  fs.writeFileSync(lockFile, JSON.stringify(lockData, null, 2) + "\\n");
  console.log("Baseline locked.");
  console.log("  Metric: " + metric + " (" + direction + ")");
  console.log("  Value: " + (baselineValue !== null ? baselineValue : "(not set)"));
  console.log("  Git: " + gitSha + (gitDirty ? " (dirty)" : ""));
}

// Check if baseline is drifted (called by run/compare/promote)
function checkBaselineDrift() {
  const cwd = targetDir();
  const lockFile = path.join(cwd, ".researchloop", "baseline.lock");
  if (!fs.existsSync(lockFile)) return null; // no lock, no drift check

  const lock = JSON.parse(fs.readFileSync(lockFile, "utf8"));

  // Check git SHA drift
  let currentSha = "unknown";
  try {
    const gitDir = path.join(cwd, ".git");
    const head = fs.readFileSync(path.join(gitDir, "HEAD"), "utf8").trim();
    if (head.startsWith("ref: ")) {
      const ref = head.slice(5);
      const refPath = path.join(gitDir, ref);
      if (fs.existsSync(refPath)) {
        currentSha = fs.readFileSync(refPath, "utf8").trim().slice(0, 8);
      }
    } else {
      currentSha = head.slice(0, 8);
    }
  } catch { /* ignore */ }

  const warnings = [];
  if (currentSha !== lock.git_sha) {
    warnings.push("Git SHA drift: locked " + lock.git_sha + ", now " + currentSha);
  }

  // Check baseline metric drift using runs.jsonl
  if (lock.baseline_value !== null) {
    try {
      const runsPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
      if (fs.existsSync(runsPath)) {
        const lines = fs.readFileSync(runsPath, "utf8").split("\\n").filter(l => l.trim());
        let bestValue = null;
        for (const line of lines) {
          const row = JSON.parse(line);
          if (row.status === "completed" && row.value != null) {
            if (bestValue === null) bestValue = row.value;
            else if (lock.direction === "higher") bestValue = Math.max(bestValue, row.value);
            else bestValue = Math.min(bestValue, row.value);
          }
        }
        if (bestValue !== null && bestValue !== lock.baseline_value) {
          const pct = Math.abs((bestValue - lock.baseline_value) / lock.baseline_value * 100).toFixed(1);
          warnings.push("Baseline metric drift: locked " + lock.baseline_value + ", best now " + bestValue + " (" + pct + "%)");
        }
      }
    } catch { /* ignore */ }
  }

  return warnings.length > 0 ? warnings : null;
}

function cmdBaselineStatus() {'''

if old_fn not in content:
    print("ERROR: cmdBaselineStatus marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Replace the first baseline dispatch (await cmdRun(true)) with lock logic
old_dispatch = '''} else if (command === "baseline") {
    await cmdRun(true);
  } else if (command === "scan-papers") {'''
new_dispatch = '''} else if (command === "baseline") {
    const lock = checkBaselineDrift();
    if (lock) {
      console.error("WARNING: baseline is drifted:");
      for (const w of lock) console.error("  " + w);
    }
    if (hasFlag("--lock")) {
      cmdBaselineLock();
    } else if (hasFlag("--unlock")) {
      cmdBaselineLock();
    } else {
      await cmdRun(true);
    }
  } else if (command === "scan-papers") {'''

if old_dispatch not in content:
    print("ERROR: baseline-status dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = 'autoresearch baseline-status [--dir PATH]'
new_help = 'autoresearch baseline-status [--dir PATH]\n  autoresearch baseline --lock [--dir PATH]\n  autoresearch baseline --unlock [--dir PATH]'

if old_help not in content:
    print("ERROR: baseline-status help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G27 baseline --lock patched successfully")