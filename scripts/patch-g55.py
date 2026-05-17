#!/usr/bin/env python3
"""Patch script for G55 snapshot command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdSnapshot before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdSnapshot() {
  const cwd = targetDir();
  const rlDir = path.join(cwd, ".researchloop");
  const snapshotIdx = args.findIndex((a) => a === "snapshot");
  const subcommand = args[snapshotIdx + 1] || "";
  const snapshotName = String(option("--name", ""));
  const note = String(option("--note", ""));
  const force = hasFlag("--force");

  if (subcommand === "save") {
    const name = snapshotName || "snapshot-" + new Date().toISOString().slice(0, 10);
    const snapshotDir = path.join(rlDir, "snapshots", name);

    if (fs.existsSync(snapshotDir) && !force) {
      console.error("Snapshot '" + name + "' already exists. Use --force to overwrite.");
      process.exitCode = 1;
      return;
    }

    // Ensure snapshots dir
    const snapshotsBase = path.join(rlDir, "snapshots");
    fs.mkdirSync(snapshotDir, { recursive: true });

    // Files to snapshot
    const files = ["runs.jsonl", "goal.md", "plan.md", "baseline.md", "eval.yaml", "safety.yaml"];
    for (const f of files) {
      const src = path.join(rlDir, f);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, path.join(snapshotDir, f));
      }
    }

    // Copy winners dir if exists
    const winnersSrc = path.join(rlDir, "winners");
    if (fs.existsSync(winnersSrc)) {
      copyDir(winnersSrc, path.join(snapshotDir, "winners"));
    }

    // Write metadata
    const runsFile = path.join(rlDir, "runs.jsonl");
    let runCount = 0;
    let bestMetric = null;
    if (fs.existsSync(runsFile)) {
      const rows = parseRunsLedger(runsFile);
      runCount = rows.filter((r) => r && !r.parse_error).length;
      const lastRow = rows.filter((r) => r && !r.parse_error).pop();
      if (lastRow && lastRow.metrics) {
        bestMetric = JSON.stringify(lastRow.metrics);
      }
    }

    const metadata = {
      name,
      created_at: new Date().toISOString(),
      note,
      run_count: runCount,
      best_metric: bestMetric,
    };
    fs.writeFileSync(path.join(snapshotDir, "metadata.json"), JSON.stringify(metadata, null, 2));

    console.log("Snapshot saved: " + name);
    console.log("  runs: " + runCount + ", best: " + (bestMetric || "none"));
  } else if (subcommand === "list") {
    const snapshotsBase = path.join(rlDir, "snapshots");
    if (!fs.existsSync(snapshotsBase)) {
      console.log("No snapshots found.");
      return;
    }

    const entries = fs.readdirSync(snapshotsBase).filter((f) => {
      return fs.statSync(path.join(snapshotsBase, f)).isDirectory();
    });

    if (entries.length === 0) {
      console.log("No snapshots found.");
      return;
    }

    console.log("Snapshots:");
    for (const entry of entries.sort()) {
      const metaFile = path.join(snapshotsBase, entry, "metadata.json");
      if (fs.existsSync(metaFile)) {
        const meta = JSON.parse(fs.readFileSync(metaFile, "utf8"));
        console.log("  " + entry + " — " + meta.run_count + " runs, best: " + (meta.best_metric || "none") + ", " + meta.created_at);
      } else {
        console.log("  " + entry);
      }
    }
  } else if (subcommand === "restore") {
    if (!snapshotName) {
      console.error("Usage: autoresearch snapshot restore <name> [--force] [--dir PATH]");
      process.exitCode = 1;
      return;
    }

    const snapshotDir = path.join(rlDir, "snapshots", snapshotName);
    if (!fs.existsSync(snapshotDir)) {
      console.error("Snapshot not found: " + snapshotName);
      process.exitCode = 1;
      return;
    }

    // Check for new runs if not force
    if (!force && fs.existsSync(path.join(rlDir, "runs.jsonl"))) {
      const currentRuns = parseRunsLedger(path.join(rlDir, "runs.jsonl"));
      const snapshotRuns = fs.existsSync(path.join(snapshotDir, "runs.jsonl"))
        ? parseRunsLedger(path.join(snapshotDir, "runs.jsonl"))
        : [];
      if (currentRuns.length > snapshotRuns.length) {
        console.error("New runs exist since snapshot. Use --force to overwrite.");
        process.exitCode = 1;
        return;
      }
    }

    // Restore files
    const files = ["runs.jsonl", "goal.md", "plan.md", "baseline.md", "eval.yaml", "safety.yaml"];
    for (const f of files) {
      const src = path.join(snapshotDir, f);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, path.join(rlDir, f));
      } else if (fs.existsSync(path.join(rlDir, f))) {
        fs.unlinkSync(path.join(rlDir, f));
      }
    }

    // Restore winners
    const winnersSrc = path.join(snapshotDir, "winners");
    if (fs.existsSync(winnersSrc)) {
      if (fs.existsSync(path.join(rlDir, "winners"))) {
        fs.rmSync(path.join(rlDir, "winners"), { recursive: true });
      }
      copyDir(winnersSrc, path.join(rlDir, "winners"));
    }

    console.log("Snapshot restored: " + snapshotName);
  } else if (subcommand === "diff") {
    if (!snapshotName) {
      console.error("Usage: autoresearch snapshot diff <name> [--dir PATH]");
      process.exitCode = 1;
      return;
    }

    const snapshotDir = path.join(rlDir, "snapshots", snapshotName);
    if (!fs.existsSync(snapshotDir)) {
      console.error("Snapshot not found: " + snapshotName);
      process.exitCode = 1;
      return;
    }

    const snapshotRunsFile = path.join(snapshotDir, "runs.jsonl");
    const currentRunsFile = path.join(rlDir, "runs.jsonl");
    const snapshotRuns = fs.existsSync(snapshotRunsFile) ? parseRunsLedger(snapshotRunsFile) : [];
    const currentRuns = fs.existsSync(currentRunsFile) ? parseRunsLedger(currentRunsFile) : [];

    const snapshotIds = new Set(snapshotRuns.filter((r) => r && r.id).map((r) => r.id));
    const newRuns = currentRuns.filter((r) => r && r.id && !snapshotIds.has(r.id));

    console.log("Runs added since snapshot: " + newRuns.length);
    for (const run of newRuns) {
      console.log("  " + run.id + " — " + JSON.stringify(run.metrics || {}));
    }
  } else {
    console.log("Usage: autoresearch snapshot <save|list|restore|diff> [options]");
    console.log("  save <name> [--note TEXT] [--force]    Save a snapshot");
    console.log("  list                                     List all snapshots");
    console.log("  restore <name> [--force]                 Restore a snapshot");
    console.log("  diff <name>                              Show changes since snapshot");
  }
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src)) {
    const srcPath = path.join(src, entry);
    const destPath = path.join(dest, entry);
    if (fs.statSync(srcPath).isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = '  } else if (command === "archive") {'
new_dispatch = '  } else if (command === "archive") {\n    if (args.includes("restore")) {\n      cmdRestore();\n    } else {\n      cmdArchive();\n    }\n  } else if (command === "snapshot") {\n    cmdSnapshot();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch archive [--name NAME] [--include-artifacts] [--out FILE.tar.gz] [--force] [--dir PATH]\n  autoresearch archive restore --file <archive.tar.gz> [--force] [--dir PATH]'
new_help = '  autoresearch archive [--name NAME] [--include-artifacts] [--out FILE.tar.gz] [--force] [--dir PATH]\n  autoresearch archive restore --file <archive.tar.gz> [--force] [--dir PATH]\n  autoresearch snapshot save <name> [--note TEXT] [--force] [--dir PATH]\n  autoresearch snapshot list [--dir PATH]\n  autoresearch snapshot restore <name> [--force] [--dir PATH]\n  autoresearch snapshot diff <name> [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G55 snapshot patched successfully, lines:", content.count('\n'))