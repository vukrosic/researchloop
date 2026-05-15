#!/usr/bin/env node
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { execSync, spawn } from "node:child_process";
import { createHash } from "node:crypto";
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

function readSafe(file) {
  try {
    return fs.readFileSync(file, "utf8");
  } catch {
    return "";
  }
}

function depsMention(cwd, needle) {
  const candidates = ["requirements.txt", "pyproject.toml", "setup.py", "uv.lock", "Pipfile"];
  const needleLower = needle.toLowerCase();
  for (const name of candidates) {
    const text = readSafe(path.join(cwd, name)).toLowerCase();
    if (text.includes(needleLower)) {
      return true;
    }
  }
  return false;
}

function detectRepo(cwd) {
  const files = walkFiles(cwd, 3);
  const basenames = files.map((file) => path.basename(file));
  const trainScriptPattern = /^(train|finetune|pretrain)[\w-]*\.py$/i;
  const hasTrainScript = basenames.some((name) => trainScriptPattern.test(name));

  const adapters = ["generic"];
  if (hasTrainScript || depsMention(cwd, "torch")) {
    adapters.push("pytorch");
  }
  if (depsMention(cwd, "transformers") || depsMention(cwd, "huggingface_hub")) {
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
    candidate_train_files: files.filter((file) => /(^|\/)(train|finetune|pretrain)[\w-]*\.py$/i.test(file)).slice(0, 30),
    candidate_eval_files: files.filter((file) => /(^|\/)(eval|evaluate|benchmark)[\w-]*\.py$/i.test(file)).slice(0, 30),
    candidate_config_files: files.filter((file) => /(^|\/|_)(config|cfg)[\w-]*\.(py|js|ts|json|yaml|yml|toml)$/i.test(file)).slice(0, 40),
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

function readPaperNotes(cwd) {
  const papersDir = path.join(cwd, ".researchloop", "scratchpad", "papers");
  if (!fs.existsSync(papersDir)) {
    return [];
  }
  const out = [];
  for (const entry of fs.readdirSync(papersDir, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith(".md")) continue;
    const file = path.join(papersDir, entry.name);
    const raw = fs.readFileSync(file, "utf8");
    const titleMatch = raw.match(/^#\s+(.+?)\s*$/m);
    const idMatch = raw.match(/^arXiv:\s*(.+?)\s*$/m);
    out.push({
      title: titleMatch ? titleMatch[1].trim() : entry.name.replace(/\.md$/, ""),
      arxivId: idMatch ? idMatch[1].trim() : entry.name.replace(/\.md$/, ""),
      file: path.relative(cwd, file),
    });
  }
  return out;
}

function buildPaperIdeas(papers, goalText, startRank) {
  const ideas = [];
  let rank = startRank;
  for (const paper of papers.slice(0, 5)) {
    const shortTitle = paper.title.length > 60 ? `${paper.title.slice(0, 57)}...` : paper.title;
    ideas.push({
      rank,
      title: `Read paper: ${shortTitle}`,
      hypothesis: `arXiv ${paper.arxivId} may suggest a mechanism relevant to ${goalText || "the target metric"}.`,
      change: `Read ${paper.file}, extract one concrete mechanism, and decide if it can be ported in one experiment.`,
      killCriterion: "If the mechanism cannot be cleanly ported or has no reproducible result section, log the lesson and skip.",
      whyNow: "Paper was fetched recently and is cheap to read before launching another sweep.",
    });
    rank += 1;
  }
  return ideas;
}

function cmdIdea() {
  const cwd = targetDir();
  const researchDir = path.join(cwd, ".researchloop");
  ensureDir(researchDir);
  const goalText = option("--goal", "") || readGoalSummary(path.join(researchDir, "goal.md"));
  const profile = loadRepoProfile(cwd);
  const ideas = buildIdeaList(profile, goalText);
  const papers = readPaperNotes(cwd);
  if (papers.length) {
    ideas.push(...buildPaperIdeas(papers, goalText, ideas.length + 1));
  }
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

function defaultMetricRegex(metricName) {
  const escaped = metricName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`["']?${escaped}["']?\\s*[:=]\\s*["']?(-?\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)`, "gi");
}

function parseMetricFromOutput(output, metricName, customRegexSource) {
  const regex = customRegexSource
    ? new RegExp(customRegexSource, "gi")
    : defaultMetricRegex(metricName);
  let last = null;
  let match;
  while ((match = regex.exec(output)) !== null) {
    last = match[1] !== undefined ? match[1] : match[0];
  }
  if (last !== null && Number.isFinite(Number(last))) {
    return Number(last);
  }
  const lines = output.split("\n").map((line) => line.trim()).filter(Boolean);
  for (let idx = lines.length - 1; idx >= 0; idx -= 1) {
    try {
      const obj = JSON.parse(lines[idx]);
      if (obj && typeof obj === "object" && metricName in obj && Number.isFinite(Number(obj[metricName]))) {
        return Number(obj[metricName]);
      }
    } catch {
      // not JSON, skip
    }
  }
  return null;
}

function spawnCommand(commandText, cwd, timeoutMs, logFile) {
  return new Promise((resolve) => {
    const child = spawn(commandText, { cwd, shell: true });
    const chunks = [];
    let timedOut = false;
    const logStream = fs.createWriteStream(logFile);
    const timer = setTimeout(() => {
      timedOut = true;
      try {
        child.kill("SIGKILL");
      } catch {
        // already gone
      }
    }, timeoutMs);
    child.stdout.on("data", (data) => {
      chunks.push(data);
      process.stdout.write(data);
      logStream.write(data);
    });
    child.stderr.on("data", (data) => {
      chunks.push(data);
      process.stderr.write(data);
      logStream.write(data);
    });
    child.on("error", (err) => {
      clearTimeout(timer);
      const message = `\nresearchloop: spawn error: ${err.message}\n`;
      logStream.end(message);
      resolve({
        output: Buffer.concat(chunks).toString("utf8") + message,
        exitCode: null,
        timedOut,
        spawnError: err.message,
      });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      logStream.end();
      resolve({
        output: Buffer.concat(chunks).toString("utf8"),
        exitCode: code,
        timedOut,
        spawnError: null,
      });
    });
  });
}

function replaceOrAppendSection(text, heading, body) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`(^## ${escaped}\\s+)([\\s\\S]*?)(?=\\n## |\\n# |$)`, "mi");
  if (pattern.test(text)) {
    return text.replace(pattern, `$1${body}\n`);
  }
  const suffix = text.endsWith("\n") ? "" : "\n";
  return `${text}${suffix}\n## ${heading}\n${body}\n`;
}

function updateGoalCurrentBest(cwd, metricName, value, runId) {
  const goalFile = path.join(cwd, ".researchloop", "goal.md");
  if (!fs.existsSync(goalFile)) {
    return;
  }
  const raw = fs.readFileSync(goalFile, "utf8");
  const body = `${metricName} = ${value} (run ${runId})`;
  fs.writeFileSync(goalFile, replaceOrAppendSection(raw, "Current Best", body));
}

function updatePlanBaseline(cwd, metricName, value, runId) {
  const planFile = path.join(cwd, ".researchloop", "plan.md");
  if (!fs.existsSync(planFile)) {
    return;
  }
  const raw = fs.readFileSync(planFile, "utf8");
  const body = [
    `- Baseline: ${metricName} = ${value} (run ${runId})`,
    "- Best valid result: same as baseline",
    "- Active family: none",
    "- Running jobs: none",
    "- Next action: design first experiment",
  ].join("\n");
  fs.writeFileSync(planFile, replaceOrAppendSection(raw, "Current State", body));
}

function readGoalFields(cwd) {
  const goalFile = path.join(cwd, ".researchloop", "goal.md");
  const raw = readTextIfExists(goalFile);
  return {
    goal: parseMarkdownSection(raw, "Goal") || "",
    metric: parseMarkdownSection(raw, "Target Metric") || "",
    direction: parseMarkdownSection(raw, "Direction") || "",
    baseline: parseMarkdownSection(raw, "Baseline Command") || "",
    evaluation: parseMarkdownSection(raw, "Evaluation Command") || "",
  };
}

async function cmdRun(isBaseline) {
  const cwd = targetDir();
  const goalFields = readGoalFields(cwd);
  const explicitCommand = option("--command", null);
  let cmdText = explicitCommand && typeof explicitCommand === "string" ? explicitCommand : "";
  if (!cmdText) {
    cmdText = isBaseline
      ? goalFields.baseline
      : (goalFields.evaluation || goalFields.baseline);
  }
  if (!cmdText || cmdText.toLowerCase() === "unknown") {
    console.error("No command to run.");
    console.error("Set one via:");
    console.error("  researchloop goal \"<text>\" --baseline \"python train.py\" --evaluation \"python eval.py\"");
    console.error("Or pass --command directly.");
    process.exitCode = 1;
    return;
  }

  const metricName = String(option("--metric", goalFields.metric || "val_loss")).trim() || "val_loss";
  const customRegex = option("--regex", null);
  const regexSource = customRegex && typeof customRegex === "string" ? customRegex : null;
  const timeoutSec = Number(option("--timeout", 600));
  const timeoutMs = Number.isFinite(timeoutSec) && timeoutSec > 0 ? timeoutSec * 1000 : 600000;

  const prefix = isBaseline ? "baseline" : "run";
  const id = String(option("--id", `${prefix}-${new Date().toISOString().replace(/[:.]/g, "-")}`));
  const runDir = path.join(cwd, ".researchloop", "scratchpad", "runs", id);
  ensureDir(runDir);
  const logFile = path.join(runDir, "log.txt");

  console.log(`researchloop ${prefix}`);
  console.log(`command: ${cmdText}`);
  console.log(`metric: ${metricName}`);
  console.log(`timeout: ${timeoutMs / 1000}s`);
  console.log(`log: ${path.relative(cwd, logFile)}`);
  console.log("---");

  const startedAt = new Date().toISOString();
  const result = await spawnCommand(cmdText, cwd, timeoutMs, logFile);
  const finishedAt = new Date().toISOString();

  let status;
  if (result.spawnError) {
    status = "spawn_error";
  } else if (result.timedOut) {
    status = "timeout";
  } else if (result.exitCode !== 0) {
    status = "failed";
  } else {
    status = "complete";
  }

  const metrics = {};
  const metricValue = parseMetricFromOutput(result.output, metricName, regexSource);
  if (metricValue !== null) {
    metrics[metricName] = metricValue;
  }
  if (status === "complete" && metricValue === null) {
    status = "complete_no_metric";
  }

  const row = {
    id,
    timestamp: finishedAt,
    started_at: startedAt,
    status,
    agent: `researchloop ${prefix}`,
    command: cmdText,
    exit_code: result.exitCode,
    log: path.relative(cwd, logFile),
    metrics,
    notes: "",
  };
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");
  ensureDir(path.dirname(ledger));
  fs.appendFileSync(ledger, `${JSON.stringify(row)}\n`);

  const thread = path.join(cwd, ".researchloop", "scratchpad", "THREAD.md");
  ensureDir(path.dirname(thread));
  const metricSuffix = metricValue !== null ? ` ${metricName}=${metricValue}` : "";
  fs.appendFileSync(thread, `- ${finishedAt} ${prefix} ${id} status=${status}${metricSuffix}\n`);

  console.log("---");
  console.log(`status: ${status}`);
  console.log(`exit_code: ${result.exitCode}`);
  if (metricValue !== null) {
    console.log(`${metricName}: ${metricValue}`);
  } else {
    console.log("metric: not parsed");
  }
  console.log(`recorded: ${id}`);

  if (isBaseline && metricValue !== null) {
    updateGoalCurrentBest(cwd, metricName, metricValue, id);
    updatePlanBaseline(cwd, metricName, metricValue, id);
    console.log("goal.md Current Best updated.");
    console.log("plan.md Current State updated.");
  }

  if (status === "failed" || status === "timeout" || status === "spawn_error") {
    process.exitCode = 1;
  }
}

const ARXIV_API_URL = "http://export.arxiv.org/api/query";

function arxivCacheDir() {
  return path.join(os.homedir(), ".cache", "researchloop", "arxiv");
}

function arxivCacheKey(query, limit, since) {
  return createHash("sha1")
    .update(`${query}|${limit}|${since || ""}`)
    .digest("hex")
    .slice(0, 16);
}

async function fetchArxivXml({ query, limit, since, cacheDir, offline }) {
  const fixture = process.env.RESEARCHLOOP_ARXIV_FIXTURE;
  if (fixture) {
    return fs.readFileSync(fixture, "utf8");
  }
  ensureDir(cacheDir);
  const key = arxivCacheKey(query, limit, since);
  const cacheFile = path.join(cacheDir, `${key}.xml`);
  if (fs.existsSync(cacheFile)) {
    return fs.readFileSync(cacheFile, "utf8");
  }
  if (offline) {
    throw new Error(`offline mode: no cache for query "${query}" (key=${key})`);
  }
  const params = new URLSearchParams({
    search_query: query,
    sortBy: "submittedDate",
    sortOrder: "descending",
    max_results: String(limit),
  });
  const url = `${ARXIV_API_URL}?${params.toString()}`;
  const res = await fetch(url, { headers: { "User-Agent": "researchloop/0.2.0" } });
  if (!res.ok) {
    throw new Error(`arxiv fetch failed: HTTP ${res.status}`);
  }
  const xml = await res.text();
  fs.writeFileSync(cacheFile, xml);
  return xml;
}

function decodeXmlEntities(text) {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

function extractXmlTag(block, tag) {
  const re = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i");
  const match = block.match(re);
  return match ? decodeXmlEntities(match[1]).replace(/\s+/g, " ").trim() : "";
}

function parseArxivEntries(xml) {
  const entries = [];
  const entryRe = /<entry>([\s\S]*?)<\/entry>/g;
  let match;
  while ((match = entryRe.exec(xml)) !== null) {
    const block = match[1];
    const idUrl = extractXmlTag(block, "id");
    const arxivId = idUrl.replace(/^https?:\/\/arxiv\.org\/abs\//, "");
    const authorBlocks = block.match(/<author>[\s\S]*?<\/author>/g) || [];
    const authors = authorBlocks
      .map((blk) => extractXmlTag(blk, "name"))
      .filter(Boolean);
    entries.push({
      arxivId,
      idUrl,
      title: extractXmlTag(block, "title"),
      summary: extractXmlTag(block, "summary"),
      published: extractXmlTag(block, "published"),
      updated: extractXmlTag(block, "updated"),
      authors,
    });
  }
  return entries;
}

function filterArxivBySince(entries, since) {
  if (!since) return entries;
  const sinceDate = new Date(since.length === 7 ? `${since}-01` : since);
  if (Number.isNaN(sinceDate.getTime())) return entries;
  return entries.filter((entry) => {
    const date = new Date(entry.published);
    return !Number.isNaN(date.getTime()) && date >= sinceDate;
  });
}

function buildDefaultArxivQuery(goalFields, profile) {
  const parts = [];
  if (goalFields.goal) parts.push(goalFields.goal);
  if (goalFields.metric) parts.push(goalFields.metric);
  const adapters = (profile && profile.adapters) || [];
  if (adapters.includes("huggingface")) parts.push("transformer");
  if (adapters.includes("pytorch")) parts.push("deep learning");
  const joined = parts.filter(Boolean).join(" ").slice(0, 200).trim();
  return joined ? `all:${joined}` : "all:deep learning";
}

function renderPaperMarkdown(entry) {
  const pubDate = entry.published ? entry.published.slice(0, 10) : "";
  return [
    `# ${entry.title || entry.arxivId}`,
    "",
    `arXiv: ${entry.arxivId}`,
    `Published: ${pubDate}`,
    `Authors: ${entry.authors.join(", ")}`,
    `Link: ${entry.idUrl}`,
    "",
    "## Abstract",
    "",
    entry.summary,
    "",
    "## How to port this",
    "",
    "TODO. Fill in when the paper is read.",
    "",
  ].join("\n");
}

async function cmdScanPapers() {
  const cwd = targetDir();
  const goalFields = readGoalFields(cwd);
  const profile = loadRepoProfile(cwd);
  const explicitQuery = option("--query", null);
  const query = explicitQuery && typeof explicitQuery === "string"
    ? explicitQuery
    : buildDefaultArxivQuery(goalFields, profile);
  const limitRaw = Number(option("--limit", 10));
  const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(50, Math.floor(limitRaw)) : 10;
  const sinceOpt = option("--since", null);
  const since = sinceOpt && typeof sinceOpt === "string" ? sinceOpt : null;
  const offline = hasFlag("--offline");
  const cacheDirOpt = option("--cache-dir", null);
  const cacheDir = cacheDirOpt && typeof cacheDirOpt === "string" ? cacheDirOpt : arxivCacheDir();

  console.log("researchloop scan-papers");
  console.log(`query: ${query}`);
  console.log(`limit: ${limit}`);
  if (since) console.log(`since: ${since}`);
  console.log(`cache: ${cacheDir}`);

  let xml;
  try {
    xml = await fetchArxivXml({ query, limit, since, cacheDir, offline });
  } catch (err) {
    console.error(`scan-papers failed: ${err.message}`);
    process.exitCode = 1;
    return;
  }

  let entries = parseArxivEntries(xml);
  entries = filterArxivBySince(entries, since);

  const papersDir = path.join(cwd, ".researchloop", "scratchpad", "papers");
  ensureDir(papersDir);
  for (const entry of entries) {
    const safeId = entry.arxivId.replace(/[/\\]/g, "_");
    const file = path.join(papersDir, `${safeId}.md`);
    fs.writeFileSync(file, renderPaperMarkdown(entry));
  }

  const thread = path.join(cwd, ".researchloop", "scratchpad", "THREAD.md");
  ensureDir(path.dirname(thread));
  fs.appendFileSync(
    thread,
    `- ${new Date().toISOString()} scan-papers query="${query.slice(0, 100)}" found=${entries.length}\n`
  );

  console.log("---");
  console.log(`found: ${entries.length}`);
  for (const entry of entries) {
    const title = entry.title.length > 80 ? `${entry.title.slice(0, 77)}...` : entry.title;
    console.log(`- ${entry.arxivId} ${title}`);
  }
  console.log(`papers written to: ${path.relative(cwd, papersDir)}`);
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
  researchloop run [--dir PATH] [--id ID] [--command CMD] [--metric NAME] [--regex PATTERN] [--timeout SECONDS]
  researchloop baseline [--dir PATH] [--id ID] [--command CMD] [--metric NAME] [--regex PATTERN] [--timeout SECONDS]
  researchloop scan-papers [--dir PATH] [--query TEXT] [--limit N] [--since YYYY-MM] [--cache-dir PATH] [--offline]
  researchloop compare [--dir PATH] [--metric NAME] [--direction lower|higher]
  researchloop dashboard [--dir PATH] [--host HOST] [--port PORT]
  researchloop report [--dir PATH]

Research Loop installs docs, prompts, scratchpads, and experiment ledgers for autonomous AI research agents.
`);
}

async function main() {
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
  } else if (command === "run") {
    await cmdRun(false);
  } else if (command === "baseline") {
    await cmdRun(true);
  } else if (command === "scan-papers") {
    await cmdScanPapers();
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
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
