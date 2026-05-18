#!/usr/bin/env python3
"""Patch script for G28 topic command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdTopic function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdTopic() {
  const cwd = targetDir();
  const mode = option("--mode", "propose");
  const doWrite = hasFlag("--write");
  const positional = positionalText();

  const topicText = positional || option("--topic", "");
  if (!topicText && !hasFlag("--topic")) {
    console.error("Usage: autoresearch topic "<text>" [--mode propose|novel|autonomous] [--dir PATH] [--write]");
    process.exitCode = 1;
    return;
  }

  // Check baseline status (reuses baseline logic)
  const baselineFile = path.join(cwd, ".researchloop", "baseline.md");
  let baselineState = "unknown";
  let baselineMetric = null;
  let baselineValue = null;

  if (fs.existsSync(baselineFile)) {
    const raw = fs.readFileSync(baselineFile, "utf8");
    const whatToRecord = extractSection(raw, "What To Record");
    const frozenSurfaces = extractSection(raw, "Frozen Surfaces");
    const requiredWhatToRecord = ["Baseline artifact", "Metric", "Direction", "Command or config"];
    const requiredFrozen = ["Dataset", "Model size", "Seed"];
    let missing = [];
    for (const key of requiredWhatToRecord) {
      if (!sectionHasValue(whatToRecord, key)) missing.push(key);
    }
    for (const key of requiredFrozen) {
      if (!sectionHasValue(frozenSurfaces, key)) missing.push(key);
    }
    baselineState = missing.length === 0 ? "complete" : "incomplete";
    baselineMetric = extractValue(whatToRecord, "Metric") || null;
    baselineValue = extractValue(whatToRecord, "Metric") || null;
  } else {
    baselineState = "missing";
  }

  // Check for prior runs
  let priorRunCount = 0;
  let bestRun = null;
  try {
    const runsPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
    if (fs.existsSync(runsPath)) {
      const lines = fs.readFileSync(runsPath, "utf8").split("\\n").filter(l => l.trim());
      priorRunCount = lines.length;
      for (const line of lines.reverse()) {
        const row = JSON.parse(line);
        if (row.status === "completed" && row.value != null) {
          bestRun = row;
          break;
        }
      }
    }
  } catch { /* ignore */ }

  // Check for existing paper notes
  let paperNotes = [];
  try {
    const papersDir = path.join(cwd, ".researchloop", "scratchpad", "papers");
    if (fs.existsSync(papersDir)) {
      for (const f of fs.readdirSync(papersDir)) {
        if (f.endsWith(".md")) paperNotes.push(f.replace(".md", ""));
      }
    }
  } catch { /* ignore */ }

  // Autonomy mode requires locked baseline
  if (mode === "autonomous") {
    const lockFile = path.join(cwd, ".researchloop", "baseline.lock");
    if (!fs.existsSync(lockFile)) {
      console.error("topic: --mode autonomous requires a locked baseline. Run `autoresearch baseline --lock` first.");
      process.exitCode = 1;
      return;
    }
  }

  // Build output
  const slug = topicText.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50);
  const timestamp = new Date().toISOString().split("T")[0];

  let output = "# Topic: " + topicText + "\\n\\n";
  output += "_Generated: " + timestamp + " | Mode: " + mode + "_\\n\\n";

  output += "## Baseline State\\n";
  output += "- Status: **" + baselineState + "**\\n";
  if (baselineMetric) output += "- Metric: " + baselineMetric + "\\n";
  if (baselineValue) output += "- Baseline value: " + baselineValue + "\\n";
  if (priorRunCount > 0) output += "- Prior runs: " + priorRunCount + "\\n";
  if (bestRun) output += "- Best run: " + bestRun.id + " (" + bestRun.value + ")\\n";
  output += "\\n";

  if (baselineState !== "complete") {
    output += "**Action required:** Baseline is " + baselineState + ". ";
    output += "Create or complete `.researchloop/baseline.md` before proceeding with experiments.\\n\\n";
  }

  output += "## Available Modes\\n\\n";
  output += "### propose (default)\\n";
  output += "Read repo history and optionally search papers to propose 2-4 grounded next experiments.\\n\\n";
  output += "### novel\\n";
  output += "Generate 3-5 genuinely different hypotheses with mechanism, why it might work, why it might fail, smallest test, and kill criterion.\\n\\n";
  output += "### autonomous\\n";
  output += "Run the full loop (read history, search papers, write notes, choose cheapest meaningful test, run it, record it, compare it) within an agreed time budget. **Requires baseline lock.**\\n\\n";

  output += "## Next Steps\\n\\n";
  output += "Choose a mode and run:\\n\\n";
  output += "```bash\\n";
  output += "autoresearch propose --topic \\"" + topicText + "\\"\\n";
  output += "# OR\\n";
  output += "autoresearch hypothesis --from-runs --topic \\"" + topicText + "\\"\\n";
  output += "```\\n\\n";

  if (paperNotes.length > 0) {
    output += "## Relevant Paper Notes\\n";
    for (const note of paperNotes) {
      output += "- " + note + "\\n";
    }
    output += "\\n";
  }

  output += "_Topic intake generated by AutoResearch-AI G28_\\n";

  if (doWrite) {
    const topicsDir = path.join(cwd, ".researchloop", "scratchpad", "topics");
    if (!fs.existsSync(topicsDir)) fs.mkdirSync(topicsDir, { recursive: true });
    const outPath = path.join(topicsDir, slug + ".md");
    fs.writeFileSync(outPath, output);
    console.log("Topic note written to: " + outPath);
    if (mode === "autonomous" && baselineState !== "complete") {
      console.log("WARNING: baseline is " + baselineState + " — autonomous mode may not behave correctly.");
    }
  } else {
    process.stdout.write(output);
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch after suggest
old_dispatch = '''} else if (command === "suggest") {
    cmdSuggest();
  } else if (command === "query") {'''
new_dispatch = '''} else if (command === "suggest") {
    cmdSuggest();
  } else if (command === "topic") {
    cmdTopic();
  } else if (command === "query") {'''

if old_dispatch not in content:
    print("ERROR: suggest dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = 'autoresearch suggest [--n N] [--metric METRIC] [--direction higher|lower] [--format text|json] [--dir PATH]'
new_help = 'autoresearch suggest [--n N] [--metric METRIC] [--direction higher|lower] [--format text|json] [--dir PATH]\n  autoresearch topic "<text>" [--mode propose|novel|autonomous] [--dir PATH] [--write]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G28 topic patched successfully")