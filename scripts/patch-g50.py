#!/usr/bin/env python3
"""Patch script for G50 archive/restore command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdArchive and cmdRestore before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdArchive() {
  const cwd = targetDir();
  const name = String(option("--name", "archive-" + new Date().toISOString().slice(0, 10)));
  const includeArtifacts = hasFlag("--include-artifacts");
  const outFile = String(option("--out", name + ".tar.gz"));
  const force = hasFlag("--force");

  const rlDir = path.join(cwd, ".researchloop");
  if (!fs.existsSync(rlDir)) {
    console.error("No .researchloop directory found.");
    process.exitCode = 1;
    return;
  }

  const absOut = path.resolve(cwd, outFile);
  if (fs.existsSync(absOut) && !force) {
    console.error("Archive already exists: " + absOut + ". Use --force to overwrite.");
    process.exitCode = 1;
    return;
  }

  const files = [
    "scratchpad/runs.jsonl",
    "goal.md",
    "plan.md",
    "baseline.md",
    "eval.yaml",
    "safety.yaml",
    "winners/",
  ];

  const includes = [];
  for (const f of files) {
    const fp = path.join(rlDir, f);
    if (fs.existsSync(fp)) includes.push(f);
  }

  const winnersDir = path.join(rlDir, "winners");
  if (fs.existsSync(winnersDir)) {
    includes.push("winners/");
  }

  if (includeArtifacts) {
    const runsDir = path.join(rlDir, "scratchpad", "runs");
    if (fs.existsSync(runsDir)) includes.push("scratchpad/runs/");
  }

  if (includes.length === 0) {
    console.error("Nothing to archive.");
    process.exitCode = 1;
    return;
  }

  const filesArg = includes.join(" ");
  const tarCmd = "tar -czf \\"" + absOut + "\\" -C \\"" + rlDir + "\\" " + filesArg;

  try {
    execSync(tarCmd, { cwd: rlDir, encoding: "utf8", timeout: 30000 });
    const stat = fs.statSync(absOut);
    const sizeStr = stat.size >= 1048576
      ? (stat.size / 1048576).toFixed(1) + " MB"
      : (stat.size / 1024).toFixed(0) + " KB";
    console.log("Archive created: " + absOut + " (" + sizeStr + ")");
    console.log("Contents: " + filesArg);
  } catch (err) {
    console.error("Archive failed: " + (err.stderr || err.message));
    process.exitCode = 1;
  }
}

function cmdRestore() {
  const cwd = targetDir();
  const archiveIdx = args.findIndex((a) => a === "restore");
  const archiveFile = String(option("--file", archiveIdx !== -1 && args[archiveIdx + 1] ? args[archiveIdx + 1] : ""));
  const force = hasFlag("--force");

  if (!archiveFile) {
    console.error("Usage: autoresearch archive restore --file <archive.tar.gz> [--force] [--dir PATH]");
    process.exitCode = 1;
    return;
  }

  if (!fs.existsSync(archiveFile)) {
    console.error("Archive not found: " + archiveFile);
    process.exitCode = 1;
    return;
  }

  const rlDir = path.join(cwd, ".researchloop");
  if (fs.existsSync(rlDir) && !force) {
    console.error(".researchloop/ already exists. Use --force to overwrite.");
    process.exitCode = 1;
    return;
  }

  const absArchive = path.isAbsolute(archiveFile) ? archiveFile : path.resolve(cwd, archiveFile);
  const cmd = "tar -xzf \\"" + absArchive + "\\" -C \\"" + cwd + "\\"";
  try {
    execSync(cmd, { encoding: "utf8", timeout: 30000 });
    console.log("Archive restored to " + cwd);
  } catch (err) {
    console.error("Restore failed: " + (err.stderr || err.message));
    process.exitCode = 1;
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch - use a unique marker
old_dispatch = '  } else if (command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else {'
new_dispatch = '  } else if (command === "data-fingerprint") {\n    cmdDataFingerprint();\n  } else if (command === "archive") {\n    if (args.includes("restore")) {\n      cmdRestore();\n    } else {\n      cmdArchive();\n    }\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text - find the last help line
old_help = '  autoresearch data-fingerprint [--dir PATH]'
new_help = '  autoresearch data-fingerprint [--dir PATH]\n  autoresearch archive [--name NAME] [--include-artifacts] [--out FILE.tar.gz] [--force] [--dir PATH]\n  autoresearch archive restore --file <archive.tar.gz> [--force] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G50 archive patched successfully, lines:", content.count('\n'))