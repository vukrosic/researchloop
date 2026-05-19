#!/usr/bin/env python3
"""Patch script for G48 model-card command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

old_fn = 'function cmdPrune() {'
new_fn = '''function cmdModelCard() {
  const cwd = targetDir();
  const runId = String(option("--id", ""));
  const outFile = option("--out", null);
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");

  if (!runId) {
    console.error("Usage: autoresearch model-card --id <run-id> [--out FILE.md] [--dir PATH]");
    process.exitCode = 1;
    return;
  }
  if (!fs.existsSync(ledger)) {
    console.error("No run ledger found.");
    process.exitCode = 1;
    return;
  }

  const rows = parseRunsLedger(ledger);
  const row = rows.find((r) => r && !r.parse_error && String(r.id) === String(runId)) || null;
  if (!row) {
    console.error("Run not found: " + runId);
    process.exitCode = 1;
    return;
  }

  const metrics = row.metrics || {};
  const env = row.env || {};
  const params = row.params || {};

  const lines = [
    "# Model Card",
    "",
    "## Model Details",
    "",
    "**Run ID:** " + row.id,
    "**Status:** " + (row.status || "unknown"),
    "**Timestamp:** " + (row.timestamp || "unknown"),
    "",
    params && Object.keys(params).length
      ? "**Parameters:**\\n" + Object.entries(params).map(([k, v]) => "- " + k + ": " + JSON.stringify(v)).join("\\n")
      : "**Parameters:** [TODO: fill in]",
    "",
    "## Intended Use",
    "",
    "[TODO: fill in]",
    "",
    "## Training Data",
    "",
    "**Data Fingerprint:** " + (row.data_fingerprint || "[TODO: compute with data-fingerprint command]"),
    "",
    "[TODO: document training data sources, size, and preprocessing]",
    "",
    "## Evaluation Results",
    "",
  ];

  const metricLines = Object.entries(metrics)
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => "- **" + k + ":** " + v);
  if (metricLines.length) {
    lines.push("| Metric | Value |", "| --- | --- |");
    for (const [k, v] of Object.entries(metrics)) {
      if (v !== null && v !== undefined) {
        lines.push("| " + k + " | " + v + " |");
      }
    }
  } else {
    lines.push("[TODO: fill in evaluation metrics]");
  }

  lines.push("");
  lines.push("## Limitations");
  lines.push("");
  lines.push("[TODO: fill in known limitations]");
  lines.push("");
  lines.push("## Ethical Considerations");
  lines.push("");
  lines.push("[TODO: fill in ethical considerations]");
  lines.push("");
  lines.push("## Hardware & Software Stack");
  lines.push("");
  lines.push("| Component | Value |", "| --- | --- |");
  if (env.os) lines.push("| OS | " + env.os + " |");
  if (env.python_version) lines.push("| Python | " + env.python_version + " |");
  if (env.torch_version) lines.push("| PyTorch | " + env.torch_version + " |");
  if (env.cuda_available) lines.push("| CUDA | " + (env.cuda_version || "available") + " |");
  if (env.hostname) lines.push("| Hostname | " + env.hostname + " |");
  if (env.git_sha) lines.push("| Git SHA | " + env.git_sha + " |");
  if (env.git_dirty !== undefined) lines.push("| Working Tree | " + (env.git_dirty ? "dirty" : "clean") + " |");
  if (!env.os && !env.python_version) {
    lines.push("| Hardware | [TODO: fill in] |");
    lines.push("| Software | [TODO: fill in] |");
  }

  const output = lines.join("\\n") + "\\n";

  if (outFile) {
    fs.writeFileSync(outFile, output);
    console.log("Model card written to " + outFile);
  } else {
    process.stdout.write(output);
  }
}

function cmdPrune() {'''

if old_fn not in content:
    print("ERROR: cmdPrune marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "prune") {\n    cmdPrune();\n  } else if (command === "data-fingerprint") {'
new_dispatch = 'command === "prune") {\n    cmdPrune();\n  } else if (command === "model-card") {\n    cmdModelCard();\n  } else {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch data-fingerprint [--dir PATH]'
new_help = '  autoresearch data-fingerprint [--dir PATH]\n  autoresearch model-card --id <run-id> [--out FILE.md] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G48 model-card patched successfully, lines:", content.count('\n'))