#!/usr/bin/env python3
"""Patch script for G26 baseline-status command"""
import re

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdBaselineStatus function after cmdReport (before cmdHelp)
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdBaselineStatus() {
  const cwd = targetDir();
  const asJson = hasFlag("--format") && option("--format") === "json";
  const baselineFile = path.join(cwd, ".researchloop", "baseline.md");

  if (!fs.existsSync(baselineFile)) {
    const msg = "Baseline not found. Run `autoresearch baseline` or create .researchloop/baseline.md";
    if (asJson) {
      process.stdout.write(JSON.stringify({ status: "missing", message: msg }, null, 2) + "\\n");
    } else {
      console.log("Error: " + msg);
    }
    process.exitCode = 1;
    return;
  }

  const raw = fs.readFileSync(baselineFile, "utf8");

  // Parse the two sections
  const whatToRecord = extractSection(raw, "What To Record");
  const frozenSurfaces = extractSection(raw, "Frozen Surfaces");
  const notes = extractSection(raw, "Notes");

  const requiredWhatToRecord = ["Baseline artifact", "Metric", "Direction", "Command or config"];
  const optionalWhatToRecord = ["Model/data/training budget", "System or accelerator", "Known limitations"];
  const requiredFrozen = ["Dataset", "Model size", "Seed"];
  const optionalFrozen = ["Token budget or eval budget", "Optimizer", "Architecture"];

  const allRequired = [...requiredWhatToRecord, ...requiredFrozen];
  const missing = [];

  for (const key of requiredWhatToRecord) {
    if (!sectionHasValue(whatToRecord, key)) missing.push(key);
  }
  for (const key of requiredFrozen) {
    if (!sectionHasValue(frozenSurfaces, key)) missing.push(key);
  }

  if (missing.length) {
    if (asJson) {
      process.stdout.write(JSON.stringify({ status: "incomplete", missing_fields: missing, message: "Baseline is missing required fields" }, null, 2) + "\\n");
    } else {
      console.log("Baseline is incomplete. Missing fields:");
      for (const m of missing) console.log("  - " + m);
    }
    process.exitCode = 1;
    return;
  }

  if (asJson) {
    process.stdout.write(JSON.stringify({
      status: "complete",
      metric: extractValue(whatToRecord, "Metric"),
      direction: extractValue(whatToRecord, "Direction"),
      command: extractValue(whatToRecord, "Command or config"),
      baseline_artifact: extractValue(whatToRecord, "Baseline artifact"),
      frozen_variables: {
        dataset: extractValue(frozenSurfaces, "Dataset"),
        model_size: extractValue(frozenSurfaces, "Model size"),
        seed: extractValue(frozenSurfaces, "Seed"),
        optimizer: extractValue(frozenSurfaces, "Optimizer") || null,
        architecture: extractValue(frozenSurfaces, "Architecture") || null,
      },
      caveats: extractValue(whatToRecord, "Known limitations") || null,
    }, null, 2) + "\\n");
  } else {
    console.log("Baseline is complete.");
    console.log("");
    console.log("Metric: " + extractValue(whatToRecord, "Metric") + " (" + extractValue(whatToRecord, "Direction") + ")");
    console.log("Command: " + extractValue(whatToRecord, "Command or config"));
    console.log("Artifact: " + extractValue(whatToRecord, "Baseline artifact"));
    console.log("");
    console.log("Frozen surfaces:");
    console.log("  Dataset: " + extractValue(frozenSurfaces, "Dataset"));
    console.log("  Model size: " + extractValue(frozenSurfaces, "Model size"));
    console.log("  Seed: " + extractValue(frozenSurfaces, "Seed"));
    const opt = extractValue(frozenSurfaces, "Optimizer");
    const arch = extractValue(frozenSurfaces, "Architecture");
    if (opt) console.log("  Optimizer: " + opt);
    if (arch) console.log("  Architecture: " + arch);
    const caveats = extractValue(whatToRecord, "Known limitations");
    if (caveats) {
      console.log("");
      console.log("Caveats: " + caveats);
    }
  }
}

function extractSection(text, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[]\\\\]/g, "\\\\$&");
  const match = text.match(new RegExp(`^## ${escaped}[\\\\s\\\\S]*?\\\\n(.*?)(?=\\\\n## |\\\\n# |$)`, "mi"));
  return match ? match[1] : "";
}

function sectionHasValue(section, key) {
  const pattern = `^\\\\s*[-*]?\\\\s*${key.replace(/[.*+?^${}()|[]\\\\]/g, "\\\\$&")}\\\\s*[:\\\\-]\\\\s*(.+)\\\\n`;
  const re = new RegExp(pattern, "mi");
  return re.test(section);
}

function extractValue(section, key) {
  const pattern = `^\\\\s*[-*]?\\\\s*${key.replace(/[.*+?^${}()|[]\\\\]/g, "\\\\$&")}\\\\s*[:\\\\-]\\\\s*(.+)\\\\n`;
  const re = new RegExp(pattern, "mi");
  const m = section.match(re);
  return m ? m[1].trim() : "";
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp function marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "report") {\n    cmdReport();\n  } else if (command === "failures") {'
new_dispatch = 'command === "report") {\n    cmdReport();\n  } else if (command === "baseline-status") {\n    cmdBaselineStatus();\n  } else if (command === "failures") {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch report [--dir PATH]'
new_help = '  autoresearch report [--dir PATH]\n  autoresearch baseline-status [--dir PATH] [--format json]'

if old_help not in content:
    print("ERROR: help not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G26 baseline-status patched successfully, lines:", content.count('\n'))