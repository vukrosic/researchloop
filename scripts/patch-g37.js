#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";
import { execSync } from "node:child_process";

const __filename = fileURLToPath(import.meta.url);
const scriptDir = path.dirname(__filename);
const repoRoot = path.resolve(scriptDir, "..");
const file = path.join(repoRoot, "bin", "researchloop.js");

let content = fs.readFileSync(file, "utf8");

// Helper to escape ${} in template literals
const e = (str) => str.replace(/\$\{/g, "XXDOLLARXX").replace(/XXDOLLARXX/g, "$\\{");

// 1. Replace readGoalFields to include data_globs
const oldReadGoalFields = "function readGoalFields(cwd) {" +
  "\n  const goalFile = path.join(cwd, \".researchloop\", \"goal.md\");" +
  "\n  const raw = readTextIfExists(goalFile);" +
  "\n  return {" +
  "\n    goal: parseMarkdownSection(raw, \"Goal\") || \"\"," +
  "\n    metric: parseMarkdownSection(raw, \"Target Metric\") || \"\"," +
  "\n    direction: parseMarkdownSection(raw, \"Direction\") || \"\"," +
  "\n    baseline: parseMarkdownSection(raw, \"Baseline Command\") || \"\"," +
  "\n    evaluation: parseMarkdownSection(raw, \"Evaluation Command\") || \"\"," +
  "\n  };" +
  "\n}";

const newReadGoalFields = e(`function readGoalFields(cwd) {
  const goalFile = path.join(cwd, ".researchloop", "goal.md");
  const raw = readTextIfExists(goalFile);
  return {
    goal: parseMarkdownSection(raw, "Goal") || "",
    metric: parseMarkdownSection(raw, "Target Metric") || "",
    direction: parseMarkdownSection(raw, "Direction") || "",
    baseline: parseMarkdownSection(raw, "Baseline Command") || "",
    evaluation: parseMarkdownSection(raw, "Evaluation Command") || "",
    data_globs: parseDataGlobs(raw),
  };
}

function parseDataGlobs(raw) {
  const match = raw.match(/^data_globs:\\s*([\\s\\S]*?)(?=^\\w|\\n#|$)/mi);
  if (!match) return null;
  const items = [];
  for (const line of match[1].split(/\\r?\\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const bulletMatch = trimmed.match(/^-\\s*["']?([^"'\\n]+)["']?\\s*$/);
    if (bulletMatch) items.push(bulletMatch[1].trim());
  }
  return items.length ? items : null;
}

function computeDataFingerprint(cwd, dataGlobs) {
  if (!dataGlobs || !dataGlobs.length) return null;
  const files = [];
  for (const glob of dataGlobs) {
    const pattern = glob.startsWith("/")
      ? path.join(glob)
      : path.join(cwd, glob);
    const dir = path.dirname(pattern);
    const base = path.basename(pattern);
    if (base.includes("*")) {
      try {
        const escaped = base.replace(/[.*+?^\${}()|[\\]\\\\]/g, "\\\\$&");
        const findCmd = "find \"" + dir + "\" -maxdepth 1 -name \"" + escaped + "\" -type f 2>/dev/null || true";
        const findOutput = execSync(findCmd, { cwd, encoding: "utf8", timeout: 5000 });
        for (const f of findOutput.split("\\n").filter(Boolean)) {
          files.push(f);
        }
      } catch {
        // no match
      }
    } else {
      if (fs.existsSync(pattern) && fs.statSync(pattern).isFile()) {
        files.push(pattern);
      }
    }
  }
  if (!files.length) return null;
  files.sort((a, b) => a.localeCompare(b));
  const hash = createHash("sha256");
  for (const file of files) {
    try {
      const stat = fs.statSync(file);
      hash.update(file);
      hash.update(String(stat.size));
      hash.update(String(stat.mtimeMs));
    } catch {
      // skip
    }
  }
  return hash.digest("hex");
}

function cmdDataFingerprint() {
  const cwd = targetDir();
  const goalFields = readGoalFields(cwd);
  const fp = computeDataFingerprint(cwd, goalFields.data_globs);
  if (fp) console.log(fp);
}`);

if (!content.includes(oldReadGoalFields)) {
  console.error("ERROR: Could not find oldReadGoalFields marker");
  console.error("Looking for:", JSON.stringify(oldReadGoalFields.substring(0, 100)));
  process.exit(1);
}
content = content.replace(oldReadGoalFields, newReadGoalFields);
console.log("Step 1: readGoalFields updated");

// 2. Add dataFingerprint compute before effectiveTimeoutMs in cmdRun
const oldEnvLine = "  const env = captureEnv(cwd);\n  const effectiveTimeoutMs";
const newEnvLine = "  const env = captureEnv(cwd);\n  const dataFingerprint = computeDataFingerprint(cwd, goalFields.data_globs);\n  const effectiveTimeoutMs";
if (!content.includes(oldEnvLine)) {
  console.error("ERROR: Could not find env line marker");
  process.exit(1);
}
content = content.replace(oldEnvLine, newEnvLine);
console.log("Step 2: dataFingerprint compute added");

// 3. Add data_fingerprint to row in cmdRun
const oldNotesLine = "    notes: \"\",\n    env,\n  };\n  appendRunRow(cwd, row);";
const newNotesLine = "    notes: \"\",\n    env,\n    data_fingerprint: dataFingerprint,\n  };\n  appendRunRow(cwd, row);";
if (!content.includes(oldNotesLine)) {
  console.error("ERROR: Could not find notes/env row marker");
  process.exit(1);
}
content = content.replace(oldNotesLine, newNotesLine);
console.log("Step 3: data_fingerprint field added to row");

// 4. Add fingerprint warning to cmdCompare
const oldScoredCheck = "  if (!scored.length) {\n    console.log(`No numeric values found for metric: ${resolvedMetric}`);\n    return;\n  }\n\n  scored.sort";
const newScoredCheck = `  if (!scored.length) {
    console.log(\`No numeric values found for metric: \${resolvedMetric}\`);
    return;
  }

  // G37: warn if best and second-best runs have different data fingerprints
  if (scored.length >= 2) {
    const fp0 = scored[0].row.data_fingerprint;
    const fp1 = scored[1].row.data_fingerprint;
    if (fp0 !== fp1) {
      console.error("WARNING: compared runs have different data fingerprints — data may have changed between runs");
    }
  }

  scored.sort`;
if (!content.includes(oldScoredCheck)) {
  console.error("ERROR: Could not find scored check marker");
  process.exit(1);
}
content = content.replace(oldScoredCheck, newScoredCheck);
console.log("Step 4: fingerprint warning added to compare");

// 5. Add command dispatch for data-fingerprint
const oldReportDispatch = "  } else if (command === \"report\") {\n    cmdReport();\n  } else {";
const newReportDispatch = `  } else if (command === "report") {
    cmdReport();
  } else if (command === "data-fingerprint") {
    cmdDataFingerprint();
  } else {`;
if (!content.includes(oldReportDispatch)) {
  console.error("ERROR: Could not find report dispatch marker");
  process.exit(1);
}
content = content.replace(oldReportDispatch, newReportDispatch);
console.log("Step 5: data-fingerprint dispatch added");

fs.writeFileSync(file, content);
console.log("Patch applied successfully");
console.log("New file size:", content.split("\n").length, "lines");