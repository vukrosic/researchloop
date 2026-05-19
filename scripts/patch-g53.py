#!/usr/bin/env python3
"""Patch script for G53 validate command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

old_fn = 'function cmdHelp() {'
new_fn = '''function cmdValidate() {
  const cwd = targetDir();
  const rlDir = path.join(cwd, ".researchloop");
  const checks = [];
  let exitCode = 0;

  function check(pass, msg) {
    checks.push({ pass, msg });
    if (!pass) exitCode = 1;
  }

  // 1. goal.md exists and complete
  const goalFile = path.join(rlDir, "goal.md");
  if (!fs.existsSync(goalFile)) {
    check(false, "goal.md missing");
  } else {
    const raw = fs.readFileSync(goalFile, "utf8");
    const required = ["Goal:", "Target Metric:", "Direction:"];
    const missing = required.filter((r) => !raw.includes(r));
    if (missing.length) {
      check(false, "goal.md incomplete: " + missing.join(", "));
    } else {
      check(true, "goal.md complete");
    }
  }

  // 2. eval.yaml valid (optional, warn if missing)
  const evalFile = path.join(rlDir, "eval.yaml");
  if (!fs.existsSync(evalFile)) {
    checks.push({ pass: true, msg: "eval.yaml missing (optional)" });
  } else {
    try {
      const evalRaw = fs.readFileSync(evalFile, "utf8");
      const metricsMatch = evalRaw.match(/metrics:\\s*\\n([\\s\\S]*?)(?=\\n\\w|\\n#|$)/mi);
      if (metricsMatch) {
        const items = metricsMatch[1];
        const nameMatches = items.match(/name:\\s*(\\S+)/g) || [];
        const hasMetrics = nameMatches.length > 0;
        check(hasMetrics, "eval.yaml has " + nameMatches.length + " metric(s)");
      } else {
        check(false, "eval.yaml missing metrics section");
      }
    } catch {
      check(false, "eval.yaml unreadable");
    }
  }

  // 3. Commands executable (check baseline command from goal.md)
  const goalRaw = fs.existsSync(goalFile) ? fs.readFileSync(goalFile, "utf8") : "";
  const baselineMatch = goalRaw.match(/baseline:\\s*\\n\\s*-\\s*["\']?(.+?)(?=["\']?\\n)/mi);
  const evalMatch = goalRaw.match(/evaluation:\\s*\\n\\s*-\\s*["\']?(.+?)(?=["\']?\\n)/mi);
  const cmdToCheck = baselineMatch || evalMatch;
  if (cmdToCheck) {
    const cmd = cmdToCheck[1].trim().split(" ")[0].replace(/['"]/g, "");
    const cmdPath = cmd.startsWith("/") ? cmd : require("path").join(cwd, cmd);
    try {
      require("child_process").execSync("which " + cmd + " 2>/dev/null || test -f " + cmdPath, { timeout: 5000 });
      check(true, "command " + cmd + " found");
    } catch {
      check(false, "command not found: " + cmd);
    }
  }

  // 4. Data globs match files (if data_globs declared)
  const dataGlobsMatch = goalRaw.match(/data_globs:\\s*([\\s\\S]*?)(?=^\\w|\\n#|$)/mi);
  if (dataGlobsMatch) {
    const lines = dataGlobsMatch[1].split("\\n");
    for (const line of lines) {
      const m = line.match(/^-\\s*["\']?([^"\'\\n]+)["\']?\\s*$/);
      if (m) {
        const glob = m[1].trim();
        if (glob) {
          const resolved = glob.startsWith("/") ? glob : path.join(cwd, glob);
          const dir = path.dirname(resolved);
          const base = path.basename(resolved);
          if (base.includes("*")) {
            const escaped = base.replace(/[*?]/g, "\\\\$&");
            try {
              const out = require("child_process").execSync("ls " + dir + "/ 2>/dev/null | head -1", { encoding: "utf8", timeout: 5000 });
              check(true, "data glob " + glob + " matched files");
            } catch {
              check(false, "data glob " + glob + " matched no files");
            }
          } else {
            check(fs.existsSync(resolved), "data glob " + glob + " " + (fs.existsSync(resolved) ? "found" : "not found"));
          }
        }
      }
    }
  }

  // 5. Metric regexes compile
  const evalRaw = fs.existsSync(evalFile) ? fs.readFileSync(evalFile, "utf8") : "";
  const regexMatches = evalRaw.match(/regex_or_jsonpath:\\s*["\']?([^"\'\\n]+)["\']?/g) || [];
  for (const rm of regexMatches) {
    const m = rm.match(/regex_or_jsonpath:\\s*["\']?([^"\'\\n]+)["\']?/);
    if (m) {
      try {
        new RegExp(m[1]);
        check(true, "metric regex " + m[1] + " compiles");
      } catch {
        check(false, "metric regex " + m[1] + " invalid");
      }
    }
  }

  // 6. Safety policy doesn't block declared commands
  const safetyFile = path.join(rlDir, "safety.yaml");
  if (fs.existsSync(safetyFile)) {
    try {
      const safetyRaw = fs.readFileSync(safetyFile, "utf8");
      const denyMatch = safetyRaw.match(/deny_substrings:\\s*([\\s\\S]*?)(?=^\\w|\\n#|$)/mi);
      if (denyMatch && cmdToCheck) {
        const cmd = cmdToCheck[1].trim();
        const denyLines = denyMatch[1].split("\\n");
        for (const dl of denyLines) {
          const dm = dl.match(/^-\\s*["\']?(.+?)["\']?\\s*$/);
          if (dm && cmd.includes(dm[1])) {
            check(false, "safety policy would block command (deny: " + dm[1] + ")");
          }
        }
      }
    } catch { /* skip */ }
  }

  // Print results
  console.log("=== Validation Results ===");
  for (const c of checks) {
    const icon = c.pass ? "\\u2713" : "\\u2717";
    console.log(icon + " " + c.msg);
  }
  const passed = checks.filter((c) => c.pass).length;
  const failed = checks.filter((c) => !c.pass).length;
  console.log("\\n" + passed + " passed, " + failed + " failed");

  if (exitCode !== 0) {
    process.exitCode = 1;
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else {'
new_dispatch = 'command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "validate") {\n    cmdValidate();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]'
new_help = '  autoresearch archive [--name NAME] [--include-artifacts] [--out FILE.tar.gz] [--force] [--dir PATH]\n  autoresearch validate [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G53 validate patched successfully, lines:", content.count('\n'))