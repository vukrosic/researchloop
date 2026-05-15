#!/usr/bin/env node
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import process from "node:process";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const packageRoot = path.resolve(path.dirname(__filename), "..");
const templatesRoot = path.join(packageRoot, "templates");

const args = process.argv.slice(2);
const command = args.find((arg) => !arg.startsWith("-")) || "help";

function option(name, fallback = undefined) {
  const idx = args.indexOf(name);
  if (idx === -1) return fallback;
  const value = args[idx + 1];
  if (!value || value.startsWith("--")) return true;
  return value;
}

function hasFlag(name) {
  return args.includes(name);
}

function optionsAll(name) {
  const values = [];
  for (let idx = 0; idx < args.length; idx += 1) {
    if (args[idx] === name) {
      const value = args[idx + 1];
      if (value && !value.startsWith("--")) {
        values.push(value);
      }
    }
  }
  return values;
}

function positionalText(excludedFlags = []) {
  const idx = args.findIndex((arg) => !arg.startsWith("-"));
  if (idx === -1) {
    return "";
  }
  const skip = new Set(excludedFlags);
  const parts = [];
  for (let i = idx + 1; i < args.length; i += 1) {
    const arg = args[i];
    if (skip.has(arg)) {
      i += 1;
      continue;
    }
    if (arg.startsWith("-")) {
      continue;
    }
    parts.push(arg);
  }
  return parts.join(" ").trim();
}

function targetDir() {
  return path.resolve(String(option("--dir", process.cwd())));
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function writeFileSafe(file, content, force = false) {
  ensureDir(path.dirname(file));
  if (fs.existsSync(file) && !force) {
    return false;
  }
  fs.writeFileSync(file, content);
  return true;
}

function copyDir(src, dest, force = false) {
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath, force);
    } else {
      writeFileSafe(destPath, fs.readFileSync(srcPath), force);
    }
  }
}

function run(commandText, cwd) {
  try {
    return execSync(commandText, {
      cwd,
      stdio: ["ignore", "pipe", "pipe"],
      encoding: "utf8",
      timeout: 5000,
    }).trim();
  } catch {
    return "";
  }
}

function existsAny(cwd, candidates) {
  return candidates.filter((candidate) => fs.existsSync(path.join(cwd, candidate)));
}

function walkFiles(cwd, maxDepth = 3) {
  const out = [];
  function walk(dir, depth) {
    if (depth > maxDepth) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (
        entry.name === ".git" ||
        entry.name === ".researchloop" ||
        entry.name === "node_modules" ||
        entry.name === "__pycache__"
      ) {
        continue;
      }
      const full = path.join(dir, entry.name);
      const rel = path.relative(cwd, full);
      if (entry.isDirectory()) {
        walk(full, depth + 1);
      } else {
        out.push(rel);
      }
    }
  }
  walk(cwd, 0);
  return out;
}

function detectRepo(cwd) {
  const files = walkFiles(cwd, 3);
  const lower = files.map((file) => file.toLowerCase());
  const has = (pattern) => lower.some((file) => file.includes(pattern));

  const adapters = ["generic"];
  if (has("train.py") || has("train_") || has("pytorch") || has("torch")) {
    adapters.push("pytorch");
  }
  if (has("trainer") || has("transformers") || has("huggingface")) {
    adapters.push("huggingface");
  }
  if (files.includes("train_llm.py") && files.includes("configs/llm_config.py")) {
    adapters.push("llm-research-kit");
  }

  return {
    cwd,
    generated_at: new Date().toISOString(),
    git_branch: run("git branch --show-current", cwd) || null,
    git_status_short: run("git status --short", cwd) || null,
    package_files: existsAny(cwd, ["package.json", "pyproject.toml", "requirements.txt", "uv.lock"]),
    candidate_train_files: files.filter((file) => /(^|\/)(train|finetune|pretrain).*\.py$/i.test(file)).slice(0, 30),
    candidate_eval_files: files.filter((file) => /(^|\/)(eval|evaluate|benchmark).*\.py$/i.test(file)).slice(0, 30),
    candidate_config_files: files.filter((file) => /(^|\/|_)(config|cfg)[^/]*\.(py|js|ts|json|yaml|yml|toml)$|\.ya?ml$|\.toml$|\.json$/i.test(file)).slice(0, 40),
    candidate_log_dirs: existsAny(cwd, ["logs", "runs", "wandb", "mlruns", "checkpoints", "plots"]),
    adapters: [...new Set(adapters)],
  };
}

function installAgentFile(cwd, agent, force) {
  const content = [
    "# Research Loop",
    "",
    "Before doing autonomous research, read:",
    "",
    "- `.researchloop/AGENTS.md`",
    "- `.researchloop/goal.md`",
    "- `.researchloop/plan.md`",
    "- `.researchloop/scratchpad/THREAD.md`",
    "",
    "Use `.researchloop/` as durable working memory. Record commands, metrics, decisions, and next experiments.",
    "",
  ].join("\n");

  if (agent === "claude-code") {
    return writeFileSafe(path.join(cwd, "CLAUDE.md"), content, force);
  }
  if (agent === "hermes") {
    return writeFileSafe(path.join(cwd, "HERMES.md"), content, force);
  }
  if (agent === "cursor") {
    return writeFileSafe(path.join(cwd, ".cursor", "rules", "researchloop.mdc"), content, force);
  }
  return writeFileSafe(path.join(cwd, "AGENTS.md"), content, force);
}

function cmdInit() {
  const cwd = targetDir();
  const force = hasFlag("--force");
  const agent = String(option("--agent", "codex"));
  const researchDir = path.join(cwd, ".researchloop");

  copyDir(path.join(templatesRoot, "base"), researchDir, force);
  copyDir(path.join(templatesRoot, "adapters"), path.join(researchDir, "adapters"), force);
  const wroteAgent = installAgentFile(cwd, agent, force);

  const profile = detectRepo(cwd);
  writeFileSafe(
    path.join(researchDir, "repo-profile.json"),
    `${JSON.stringify(profile, null, 2)}\n`,
    true
  );

  console.log(`Research Loop initialized in ${cwd}`);
  console.log(`Harness: ${path.relative(cwd, researchDir)}`);
  console.log(`Agent file: ${wroteAgent ? "written" : "already existed"}`);
  console.log(`Detected adapters: ${profile.adapters.join(", ")}`);
}

function cmdInspect() {
  const cwd = targetDir();
  const researchDir = path.join(cwd, ".researchloop");
  ensureDir(researchDir);
  const profile = detectRepo(cwd);
  fs.writeFileSync(path.join(researchDir, "repo-profile.json"), `${JSON.stringify(profile, null, 2)}\n`);
  console.log(JSON.stringify(profile, null, 2));
}

function cmdPrompt() {
  const cwd = targetDir();
  const agent = String(option("--agent", "codex"));
  const explicitGoal = option("--goal", null);
  const savedGoal = readGoalSummary(path.join(cwd, ".researchloop", "goal.md"));
  const focus = String(option("--focus", option("--playbook", ""))).trim();
  const goal =
    explicitGoal ||
    savedGoal ||
    "Improve the target metric through small, documented experiments.";
  const promptFile = path.join(templatesRoot, "prompts", `${agent}.md`);
  const fallback = path.join(templatesRoot, "prompts", "generic.md");
  const template = fs.readFileSync(fs.existsSync(promptFile) ? promptFile : fallback, "utf8");
  let output = template.replaceAll("{{GOAL}}", goal);

  if (focus) {
    const focusFile = path.join(templatesRoot, "prompts", "focus", `${focus}.md`);
    if (fs.existsSync(focusFile)) {
      output += "\n\n";
      output += fs.readFileSync(focusFile, "utf8").replaceAll("{{GOAL}}", goal);
    }
  }

  process.stdout.write(output);
}

function cmdGoal() {
  const cwd = targetDir();
  const researchDir = path.join(cwd, ".researchloop");
  ensureDir(researchDir);
  const goalText = positionalText(["--dir", "--metric", "--direction", "--baseline", "--evaluation", "--allowed", "--forbidden"]);
  const goalFile = path.join(researchDir, "goal.md");

  if (!goalText) {
    if (fs.existsSync(goalFile)) {
      process.stdout.write(fs.readFileSync(goalFile, "utf8"));
      return;
    }
    console.log("No research goal set yet. Use `researchloop goal \"lower validation loss\"`.");
    return;
  }

  const metric = String(option("--metric", "validation loss"));
  const direction = String(option("--direction", "lower"));
  const baseline = String(option("--baseline", "unknown"));
  const evaluation = String(option("--evaluation", "unknown"));
  const allowed = String(option("--allowed", "optimizer, schedules, initialization, hyperparameters"));
  const forbidden = String(option("--forbidden", "data, architecture, batch size, benchmark definition"));

  const content = [
    "# Research Goal",
    "",
    "## Goal",
    goalText,
    "",
    "## Target Metric",
    metric,
    "",
    "## Direction",
    direction,
    "",
    "## Baseline Command",
    baseline,
    "",
    "## Evaluation Command",
    evaluation,
    "",
    "## Allowed Changes",
    allowed,
    "",
    "## Forbidden Changes",
    forbidden,
    "",
    "## Current Best",
    "Unknown.",
    "",
    "## Notes",
    "Use `researchloop inspect` to generate a repo profile, then ask an agent to fill in the missing benchmark details.",
    "",
  ].join("\n");

  fs.writeFileSync(goalFile, content);
  console.log(`Research goal saved to ${path.relative(cwd, goalFile)}`);
  console.log(`Goal: ${goalText}`);
}

function readGoalSummary(goalFile) {
  if (!fs.existsSync(goalFile)) {
    return "";
  }
  const text = fs.readFileSync(goalFile, "utf8");
  const match = text.match(/## Goal\s+([\s\S]*?)(?:\n## |\n# |$)/i);
  if (match) {
    return match[1].trim();
  }
  return text.trim();
}

function cmdDoctor() {
  const cwd = targetDir();
  const python = String(option("--python", "python3"));
  const nodeVersion = process.version;
  const npmVersion = run("npm --version", cwd) || "not found";
  const gitVersion = run("git --version", cwd) || "not found";
  const pythonVersion = run(`${python} --version`, cwd) || "not found";
  const torchProbe = run(`${python} - <<'PY'\nimport importlib.util\nspec = importlib.util.find_spec('torch')\nif not spec:\n    print('torch missing')\nelse:\n    import torch\n    print(f'torch {torch.__version__}')\n    print(f'cuda {torch.cuda.is_available()}')\n    print(f'mps {hasattr(torch.backends, \"mps\") and torch.backends.mps.is_available()}')\nPY`, cwd) || "torch unknown";

  console.log(`cwd: ${cwd}`);
  console.log(`node: ${nodeVersion}`);
  console.log(`npm: ${npmVersion}`);
  console.log(`git: ${gitVersion}`);
  console.log(`python: ${pythonVersion} (${python})`);
  console.log(torchProbe);
}

function cmdReport() {
  const cwd = targetDir();
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  if (!fs.existsSync(ledger)) {
    console.log("No run ledger found. Run `researchloop init` first.");
    return;
  }
  const rows = fs.readFileSync(ledger, "utf8").split("\n").filter(Boolean);
  const parsed = rows.map((row) => {
    try {
      return JSON.parse(row);
    } catch {
      return { parse_error: true, raw: row };
    }
  });
  const errors = parsed.filter((row) => row.parse_error).length;
  const complete = parsed.filter((row) => row.status === "complete" || row.status === "completed").length;
  console.log(`runs: ${rows.length}`);
  console.log(`complete: ${complete}`);
  console.log(`parse_errors: ${errors}`);
  if (parsed.length) {
    console.log(`last: ${JSON.stringify(parsed[parsed.length - 1], null, 2)}`);
  }
}

function readTextIfExists(file) {
  return fs.existsSync(file) ? fs.readFileSync(file, "utf8") : "";
}

function parseMarkdownSection(text, heading) {
  if (!text) return "";
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = text.match(new RegExp(`^## ${escaped}\\s+([\\s\\S]*?)(?=\\n## |\\n# |$)`, "mi"));
  return match ? match[1].trim() : "";
}

function parseGoalFile(goalFile) {
  const raw = readTextIfExists(goalFile);
  return {
    raw,
    goal: parseMarkdownSection(raw, "Goal") || "",
    metric: parseMarkdownSection(raw, "Target Metric") || "",
    direction: parseMarkdownSection(raw, "Direction") || "",
    baseline: parseMarkdownSection(raw, "Baseline Command") || "",
    evaluation: parseMarkdownSection(raw, "Evaluation Command") || "",
    currentBest: parseMarkdownSection(raw, "Current Best") || "",
    notes: parseMarkdownSection(raw, "Notes") || "",
  };
}

function parsePlanFile(planFile) {
  const raw = readTextIfExists(planFile);
  return {
    raw,
    currentState: parseMarkdownSection(raw, "Current State") || "",
    picklist: parseMarkdownSection(raw, "Picklist") || "",
    ruledOut: parseMarkdownSection(raw, "Ruled Out") || "",
  };
}

function parseRunsLedger(ledgerFile) {
  if (!fs.existsSync(ledgerFile)) {
    return [];
  }
  return readTextIfExists(ledgerFile)
    .split("\n")
    .filter(Boolean)
    .map((row) => {
      try {
        return JSON.parse(row);
      } catch {
        return { parse_error: true, raw: row };
      }
    });
}

function isNumericMetric(value) {
  return Number.isFinite(Number(value));
}

function choosePrimaryMetric(goal, runs) {
  const metricHint = String(goal?.metric || "").trim();
  const metricKeys = new Set();
  for (const run of runs) {
    for (const key of Object.keys(run.metrics || {})) {
      if (isNumericMetric(run.metrics[key])) {
        metricKeys.add(key);
      }
    }
  }

  if (metricHint && metricKeys.has(metricHint)) {
    return metricHint;
  }
  if (metricKeys.has("val_loss")) {
    return "val_loss";
  }
  if (metricKeys.has("loss")) {
    return "loss";
  }
  return metricKeys.values().next().value || "";
}

function summarizeDashboardRuns(runs, primaryMetric, preferHigher = false) {
  const completeRuns = runs.filter((run) => run.status === "complete" || run.status === "completed");
  const parseErrors = runs.filter((run) => run.parse_error).length;
  const latestRun = [...runs].reverse().find((run) => !run.parse_error) || null;

  const metricEntries = runs
    .map((run, index) => ({
      run,
      index,
      value: primaryMetric && isNumericMetric(run.metrics?.[primaryMetric]) ? Number(run.metrics[primaryMetric]) : Number.NaN,
    }))
    .filter((entry) => Number.isFinite(entry.value));

  metricEntries.sort((a, b) => (preferHigher ? b.value - a.value : a.value - b.value));
  const bestRun = metricEntries[0] || null;
  const worstRun = metricEntries[metricEntries.length - 1] || null;
  const series = metricEntries
    .slice()
    .sort((a, b) => a.index - b.index)
    .map((entry) => ({
      id: entry.run.id,
      value: entry.value,
      timestamp: entry.run.timestamp,
    }));

  return {
    totalRuns: runs.length,
    completeRuns: completeRuns.length,
    parseErrors,
    latestRun,
    bestRun,
    worstRun,
    series,
  };
}

function buildDashboardState(cwd) {
  const goalPath = path.join(cwd, ".researchloop", "goal.md");
  const planPath = path.join(cwd, ".researchloop", "plan.md");
  const profilePath = path.join(cwd, ".researchloop", "repo-profile.json");
  const ledgerPath = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");

  const goal = parseGoalFile(goalPath);
  const plan = parsePlanFile(planPath);
  let repoProfile = detectRepo(cwd);
  if (fs.existsSync(profilePath)) {
    try {
      repoProfile = JSON.parse(readTextIfExists(profilePath));
    } catch {
      repoProfile = detectRepo(cwd);
    }
  }
  const runs = parseRunsLedger(ledgerPath);
  const primaryMetric = choosePrimaryMetric(goal, runs);
  const preferHigher = String(goal.direction || "").toLowerCase().includes("high");
  const summary = summarizeDashboardRuns(runs, primaryMetric, preferHigher);

  return {
    cwd,
    generatedAt: new Date().toISOString(),
    goal,
    plan,
    repoProfile,
    runs,
    primaryMetric,
    preferHigher,
    summary,
  };
}

function cmdDashboard() {
  const cwd = targetDir();
  const host = String(option("--host", "127.0.0.1"));
  const port = Number(option("--port", 8787));
  const dashboardFile = path.join(templatesRoot, "dashboard", "index.html");
  const html = readTextIfExists(dashboardFile);

  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", `http://${req.headers.host || `${host}:${port}`}`);
    if (url.pathname === "/" || url.pathname === "/index.html") {
      res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
      res.end(html);
      return;
    }
    if (url.pathname === "/api/state") {
      res.writeHead(200, { "content-type": "application/json; charset=utf-8" });
      res.end(`${JSON.stringify(buildDashboardState(cwd), null, 2)}\n`);
      return;
    }
    if (url.pathname === "/api/runs") {
      res.writeHead(200, { "content-type": "application/json; charset=utf-8" });
      const state = buildDashboardState(cwd);
      res.end(`${JSON.stringify(state.runs, null, 2)}\n`);
      return;
    }
    if (url.pathname === "/api/goal") {
      res.writeHead(200, { "content-type": "application/json; charset=utf-8" });
      const state = buildDashboardState(cwd);
      res.end(`${JSON.stringify(state.goal, null, 2)}\n`);
      return;
    }
    res.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    res.end("Not found");
  });

  server.listen(port, host, () => {
    const address = server.address();
    const actualPort = typeof address === "object" && address ? address.port : port;
    console.log(`ResearchLoop dashboard running at http://${host}:${actualPort}`);
    console.log(`Repo: ${cwd}`);
    console.log("No auth. Localhost only.");
  });

  process.on("SIGINT", () => server.close(() => process.exit(0)));
  process.on("SIGTERM", () => server.close(() => process.exit(0)));
}

function loadRepoProfile(cwd) {
  const profileFile = path.join(cwd, ".researchloop", "repo-profile.json");
  if (fs.existsSync(profileFile)) {
    try {
      return JSON.parse(fs.readFileSync(profileFile, "utf8"));
    } catch {
      return detectRepo(cwd);
    }
  }
  return detectRepo(cwd);
}

function buildIdeaList(profile, goalText) {
  const adapters = Array.isArray(profile?.adapters) ? profile.adapters : ["generic"];
  const adapterSet = new Set(adapters);
  const ideas = [];

  const add = (rank, title, hypothesis, change, killCriterion, whyNow) => {
    ideas.push({ rank, title, hypothesis, change, killCriterion, whyNow });
  };

  if (adapterSet.has("llm-research-kit")) {
    add(
      1,
      "Baseline config lock",
      `We need a clean baseline for ${goalText || "the target metric"} before changing architecture.`,
      "Run the current tiny config once with logging fixed, and verify val_loss parsing end to end.",
      "If the baseline cannot be reproduced twice, do not touch architecture yet.",
      "This tells us whether the metric path is trustworthy."
    );
    add(
      2,
      "Learning rate sweep",
      `Learning rate is usually the cheapest knob for ${goalText || "loss reduction"}.`,
      "Sweep a few learning rates while holding d_model, n_layers, batch size, and dataset fixed.",
      "If no setting beats baseline by a meaningful margin, prune the family.",
      "Cheap, high-signal, and likely to matter before architecture changes."
    );
    add(
      3,
      "Tiny architecture sweep",
      "A small architecture change may help after the optimizer path is stable.",
      "Try one change at a time: d_model, n_layers, or d_ff, but never stack them in the first pass.",
      "If the change helps only once and not on reproduction, discard it.",
      "This is the smallest architecture probe that still feels real."
    );
    add(
      4,
      "Second-seed reproduction",
      "Any win should survive a second run before it is promoted.",
      "Re-run the best candidate with a fresh seed and the same config.",
      "If the win vanishes, demote it and keep searching.",
      "This prevents the project from believing one lucky run."
    );
  } else if (adapterSet.has("huggingface")) {
    add(
      1,
      "Baseline reproduction",
      `Confirm the current Hugging Face training path before changing anything for ${goalText || "the target metric"}.`,
      "Run the existing Trainer or training script once and capture the metric extraction path.",
      "If the baseline is unstable, stop and fix reproducibility first.",
      "Cheap signal before any parameter sweeps."
    );
    add(
      2,
      "Learning rate and schedule sweep",
      "Trainer setups often respond first to LR and warmup changes.",
      "Sweep learning rate, warmup ratio, and scheduler while keeping the dataset and model fixed.",
      "If none of the runs improve, prune the family.",
      "Usually the highest-return low-risk ablation."
    );
    add(
      3,
      "Batch and precision check",
      "Throughput or stability may be limiting the current run.",
      "Try a single batch-size or precision change, not both at once.",
      "If validation gets noisier without speed or quality gain, stop.",
      "A small systems-level change can reveal an easy win."
    );
  } else if (adapterSet.has("pytorch")) {
    add(
      1,
      "Baseline reproduction",
      `Confirm the current PyTorch path before changing anything for ${goalText || "the target metric"}.`,
      "Run the existing train script once and capture the evaluation command plus metric path.",
      "If the baseline cannot be reproduced, fix that first.",
      "You need a stable starting point."
    );
    add(
      2,
      "Optimizer sweep",
      "Optimizer choice is often the cheapest first lever.",
      "Compare AdamW against the repo's current optimizer while holding everything else fixed.",
      "If the alternative does not beat baseline, stop the family.",
      "This is a small, interpretable change."
    );
    add(
      3,
      "Learning rate sweep",
      "Learning rate usually matters more than most architectural changes early on.",
      "Sweep a few learning rates around the current default.",
      "If the curve is flat, prune the family.",
      "Fast and often decisive."
    );
  } else {
    add(
      1,
      "Find the baseline",
      `Before optimizing ${goalText || "the target metric"}, identify the exact command that produces the current metric.`,
      "Use inspect to find the training and evaluation commands, then run the smallest proof-of-life command.",
      "If the baseline is unknown, do not guess at improvements yet.",
      "The workflow starts with observability."
    );
    add(
      2,
      "Metric plumbing check",
      "A lot of early failures are just missing metric extraction.",
      "Make sure the repo prints one clear metric that can be compared run to run.",
      "If no reliable metric exists, stop and add logging before tuning.",
      "Without a metric, experiments are theater."
    );
    add(
      3,
      "Smallest config change",
      "Once the metric is stable, try one config change at a time.",
      "Prefer a hyperparameter or schedule change before touching architecture.",
      "If a change is hard to explain or reproduce, discard it.",
      "This keeps the first pass cheap and legible."
    );
  }

  return ideas;
}

function renderIdeasMarkdown(profile, goalText, ideas) {
  const adapters = (profile?.adapters || ["generic"]).join(", ");
  const lines = [
    "# Research Ideas",
    "",
    `Goal: ${goalText || "Unknown"}`,
    `Adapters: ${adapters}`,
    "",
  ];

  for (const idea of ideas) {
    lines.push(
      `## ${idea.rank}. ${idea.title}`,
      "",
      `Hypothesis: ${idea.hypothesis}`,
      `Change: ${idea.change}`,
      `Kill criterion: ${idea.killCriterion}`,
      `Why now: ${idea.whyNow}`,
      ""
    );
  }

  return lines.join("\n");
}

function cmdIdea() {
  const cwd = targetDir();
  const researchDir = path.join(cwd, ".researchloop");
  ensureDir(researchDir);
  const goalText = option("--goal", "") || readGoalSummary(path.join(researchDir, "goal.md"));
  const profile = loadRepoProfile(cwd);
  const ideas = buildIdeaList(profile, goalText);
  const markdown = renderIdeasMarkdown(profile, goalText, ideas);
  process.stdout.write(`${markdown}\n`);

  if (hasFlag("--write")) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const file = path.join(researchDir, "scratchpad", "ideas", `${stamp}-ideas.md`);
    ensureDir(path.dirname(file));
    fs.writeFileSync(file, `${markdown}\n`);
    console.log(`\nIdea note written to ${path.relative(cwd, file)}`);
  }
}

function cmdCompare() {
  const cwd = targetDir();
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  const metricName = option("--metric", null);
  const direction = String(option("--direction", "lower")).toLowerCase();
  const preferHigher = direction === "higher" || direction === "max" || direction === "maximize";

  if (!fs.existsSync(ledger)) {
    console.log("No run ledger found. Run `researchloop init` first.");
    return;
  }

  const rows = fs
    .readFileSync(ledger, "utf8")
    .split("\n")
    .filter(Boolean)
    .map((row) => {
      try {
        return JSON.parse(row);
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  const candidates = rows.filter((row) => row.metrics && typeof row.metrics === "object");
  let resolvedMetric = metricName;
  if (!resolvedMetric) {
    for (const row of candidates) {
      for (const key of Object.keys(row.metrics)) {
        if (Number.isFinite(rowMetricValue(row, key))) {
          resolvedMetric = key;
          break;
        }
      }
      if (resolvedMetric) {
        break;
      }
    }
  }

  if (!resolvedMetric) {
    console.log("No comparable numeric metric found in the run ledger.");
    return;
  }

  const scored = candidates
    .map((row) => ({
      row,
      value: rowMetricValue(row, resolvedMetric),
    }))
    .filter((entry) => Number.isFinite(entry.value));

  if (!scored.length) {
    console.log(`No numeric values found for metric: ${resolvedMetric}`);
    return;
  }

  scored.sort((a, b) => (preferHigher ? b.value - a.value : a.value - b.value));
  const best = scored[0];
  const worst = scored[scored.length - 1];

  console.log(`metric: ${resolvedMetric}`);
  console.log(`direction: ${preferHigher ? "higher" : "lower"}`);
  console.log(`runs_compared: ${scored.length}`);
  console.log(`best: ${best.row.id} = ${best.value}`);
  console.log(`worst: ${worst.row.id} = ${worst.value}`);
  console.log("top_3:");
  for (const entry of scored.slice(0, 3)) {
    console.log(`- ${entry.row.id}: ${entry.value}`);
  }
}

function rowMetricValue(row, key) {
  if (!row || !row.metrics || !(key in row.metrics)) {
    return Number.NaN;
  }
  return Number(row.metrics[key]);
}

function parseMetric(metricText) {
  const splitAt = metricText.indexOf("=");
  if (splitAt === -1) {
    return [metricText, true];
  }
  const key = metricText.slice(0, splitAt).trim();
  const rawValue = metricText.slice(splitAt + 1).trim();
  const numberValue = Number(rawValue);
  return [key, Number.isNaN(numberValue) ? rawValue : numberValue];
}

function cmdRecord() {
  const cwd = targetDir();
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  ensureDir(path.dirname(ledger));

  const metrics = {};
  for (const metric of optionsAll("--metric")) {
    const [key, value] = parseMetric(metric);
    if (key) {
      metrics[key] = value;
    }
  }

  const row = {
    id: String(option("--id", `run-${new Date().toISOString().replace(/[:.]/g, "-")}`)),
    timestamp: new Date().toISOString(),
    status: String(option("--status", "recorded")),
    agent: String(option("--agent", "manual")),
    command: option("--command", null),
    metrics,
    notes: String(option("--note", "")),
  };

  fs.appendFileSync(ledger, `${JSON.stringify(row)}\n`);
  console.log(`Recorded run: ${row.id}`);
}

function cmdHelp() {
  console.log(`Research Loop

Usage:
  researchloop init [--agent codex|claude-code|hermes|cursor] [--dir PATH] [--force]
  researchloop goal [TEXT] [--dir PATH] [--metric NAME] [--direction lower|higher] [--baseline CMD] [--evaluation CMD] [--allowed TEXT] [--forbidden TEXT]
  researchloop inspect [--dir PATH]
  researchloop idea [--dir PATH] [--goal TEXT] [--write]
  researchloop prompt [--agent codex|claude-code|hermes|generic] [--goal TEXT] [--focus hyperparameters|architecture|attention]
  researchloop doctor [--dir PATH] [--python PATH]
  researchloop record [--dir PATH] [--id ID] [--status STATUS] [--metric key=value] [--note TEXT]
  researchloop compare [--dir PATH] [--metric NAME] [--direction lower|higher]
  researchloop dashboard [--dir PATH] [--host HOST] [--port PORT]
  researchloop report [--dir PATH]

Research Loop installs docs, prompts, scratchpads, and experiment ledgers for autonomous AI research agents.
`);
}

if (hasFlag("--help") || command === "help") {
  cmdHelp();
} else if (command === "init") {
  cmdInit();
} else if (command === "goal") {
  cmdGoal();
} else if (command === "inspect") {
  cmdInspect();
} else if (command === "idea") {
  cmdIdea();
} else if (command === "prompt") {
  cmdPrompt();
} else if (command === "doctor") {
  cmdDoctor();
} else if (command === "record") {
  cmdRecord();
} else if (command === "compare") {
  cmdCompare();
} else if (command === "dashboard") {
  cmdDashboard();
} else if (command === "report") {
  cmdReport();
} else {
  console.error(`Unknown command: ${command}`);
  cmdHelp();
  process.exitCode = 1;
}
