#!/usr/bin/env python3
"""Patch script for G01 propose command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdPropose function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdPropose() {
  const cwd = targetDir();
  const n = parseInt(option("--n", "5"), 10);
  const doWrite = hasFlag("--write");
  const mode = option("--mode", "propose");
  const focus = option("--focus", "all");
  const metric = option("--metric", null);
  const direction = option("--direction", null);

  // Check baseline status
  const baselineFile = path.join(cwd, ".researchloop", "baseline.md");
  let baselineInfo = { status: "missing", metric: null, direction: null };
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
    baselineInfo.status = missing.length === 0 ? "complete" : "incomplete";
    baselineInfo.metric = extractValue(whatToRecord, "Metric") || null;
    baselineInfo.direction = extractValue(whatToRecord, "Direction") || null;
  }

  // Check if baseline is locked
  const lockFile = path.join(cwd, ".researchloop", "baseline.lock");
  if (fs.existsSync(lockFile)) {
    try {
      const lock = JSON.parse(fs.readFileSync(lockFile, "utf8"));
      baselineInfo.locked_at = lock.locked_at;
      baselineInfo.baseline_value = lock.baseline_value;
    } catch { /* ignore */ }
  }

  // Collect prior runs
  let runs = [];
  try {
    const runsPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
    if (fs.existsSync(runsPath)) {
      const lines = fs.readFileSync(runsPath, "utf8").split("\\n").filter(l => l.trim());
      for (const line of lines) {
        runs.push(JSON.parse(line));
      }
    }
  } catch { /* ignore */ }

  // Collect paper notes
  let paperNotes = [];
  try {
    const papersDir = path.join(cwd, ".researchloop", "scratchpad", "papers");
    if (fs.existsSync(papersDir)) {
      for (const f of fs.readdirSync(papersDir)) {
        if (f.endsWith(".md")) {
          const content = fs.readFileSync(path.join(papersDir, f), "utf8");
          paperNotes.push({ id: f.replace(".md", ""), content });
        }
      }
    }
  } catch { /* ignore */ }

  // Collect hypotheses
  let hypotheses = [];
  try {
    const hypDir = path.join(cwd, ".researchloop", "scratchpad", "hypotheses");
    if (fs.existsSync(hypDir)) {
      for (const f of fs.readdirSync(hypDir)) {
        if (f.endsWith(".md")) {
          const content = fs.readFileSync(path.join(hypDir, f), "utf8");
          hypotheses.push({ id: f.replace(".md", ""), content });
        }
      }
    }
  } catch { /* ignore */ }

  // Determine target metric
  const targetMetric = metric || baselineInfo.metric || "val_loss";
  const targetDirection = direction || baselineInfo.direction || "lower";

  // Generate proposals based on prior runs and baseline
  const proposals = [];
  const usedMechanisms = new Set();

  // Extract mechanism from existing runs
  for (const run of runs) {
    if (run.params && run.params._mechanism) {
      usedMechanisms.add(run.params._mechanism);
    }
  }

  // Simple proposal generation based on common ML improvements
  const proposalTemplates = [
    { title: "Learning rate warmup", hypothesis: "Warmup prevents early gradient instability in transformers.", mechanism: "lr_warmup", change: "add warmup schedule", risk: "low" },
    { title: "AdamW instead of Adam", hypothesis: "Decoupled weight decay in AdamW produces better regularization.", mechanism: "optimizer_change", change: "replace Adam with AdamW", risk: "low" },
    { title: "Reduce batch size", hypothesis: "Smaller batches improve generalization for small datasets.", mechanism: "batch_reduction", change: "halve batch_size", risk: "medium" },
    { title: "Add gradient clipping", hypothesis: "Gradient clipping prevents token-level explosion in transformers.", mechanism: "gradient_clipping", change: "set max_grad_norm=1.0", risk: "low" },
    { title: "Increase model width", hypothesis: "Wider layers capture more complex patterns.", mechanism: "width_increase", change: "double hidden_dim", risk: "high" },
    { title: "Dropout regularization", hypothesis: "Dropout prevents overfitting on small datasets.", mechanism: "dropout", change: "add dropout=0.1", risk: "low" },
    { title: "Longer training with early stopping", hypothesis: "More epochs with patience finds better optimum.", mechanism: "longer_training", change: "increase epochs to 200", risk: "medium" },
    { title: "Weight decay tuning", hypothesis: "Optimal weight decay depends on model size and dataset.", mechanism: "weight_decay", change: "sweep weight_decay 0.01-0.1", risk: "medium" },
  ];

  // Filter out already-tried mechanisms
  const available = proposalTemplates.filter(p => !usedMechanisms.has(p.mechanism));

  // Generate id for each proposal (content-hashed)
  function hashId(text) {
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      const char = text.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return "prop_" + Math.abs(hash).toString(16).padStart(8, "0");
  }

  let count = 0;
  for (const tpl of available) {
    if (count >= n) break;

    const id = hashId(tpl.title + Date.now());
    const bestRun = runs.filter(r => r.status === "completed").sort((a, b) => {
      if (targetDirection === "higher") return (b.value || 0) - (a.value || 0);
      return (a.value || 0) - (b.value || 0);
    })[0];

    proposals.push({
      id,
      title: tpl.title,
      hypothesis: tpl.hypothesis,
      change: tpl.change,
      metric: targetMetric,
      expected_direction: targetDirection,
      estimated_minutes: tpl.risk === "low" ? 30 : tpl.risk === "medium" ? 120 : 240,
      est_cost_usd_or_null: null,
      risk: tpl.risk,
      priors: bestRun ? [{ type: "run", id: bestRun.id }] : [],
      kill_criterion: targetMetric + " does not improve by >5% after " + (tpl.risk === "low" ? "1h" : "4h"),
      mechanism: tpl.mechanism,
      mode,
      created_at: new Date().toISOString(),
    });

    count++;
  }

  // Output
  if (doWrite) {
    const proposalsPath = path.join(cwd, ".researchloop", "scratchpad", "proposals.jsonl");
    const scratchpadDir = path.join(cwd, ".researchloop", "scratchpad");
    if (!fs.existsSync(scratchpadDir)) fs.mkdirSync(scratchpadDir, { recursive: true });
    const existingIds = new Set();
    try {
      if (fs.existsSync(proposalsPath)) {
        const existing = fs.readFileSync(proposalsPath, "utf8").split("\\n").filter(l => l.trim());
        for (const line of existing) {
          try { existingIds.add(JSON.parse(line).id); } catch { /* ignore */ }
        }
      }
    } catch { /* ignore */ }

    const filtered = proposals.filter(p => !existingIds.has(p.id));
    if (filtered.length > 0) {
      const lines = filtered.map(p => JSON.stringify(p)).join("\\n") + "\\n";
      fs.appendFileSync(proposalsPath, lines);
    }
    console.log("Wrote " + filtered.length + " new proposal(s) to " + proposalsPath);
  } else {
    // JSON output
    process.stdout.write(JSON.stringify(proposals, null, 2));
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch after idea
old_dispatch = '''} else if (command === "idea") {
    cmdIdea();
  } else if (command === "prompt") {'''
new_dispatch = '''} else if (command === "idea") {
    cmdIdea();
  } else if (command === "propose") {
    cmdPropose();
  } else if (command === "prompt") {'''

if old_dispatch not in content:
    print("ERROR: idea dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = 'autoresearch idea [--dir PATH]'
new_help = 'autoresearch idea [--dir PATH]\n  autoresearch propose [--n N] [--write] [--mode propose|novel|autonomous] [--focus hyperparameters|architecture|attention|data] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G01 propose patched successfully")