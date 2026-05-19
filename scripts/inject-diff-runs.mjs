#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const researchloopPath = path.join(path.dirname(__filename), "..", "bin", "researchloop.js");

const content = fs.readFileSync(researchloopPath, "utf8");
const marker = "\nfunction cmdTeam() {";
const idx = content.indexOf(marker);

if (idx === -1) {
  console.error("Marker not found");
  process.exit(1);
}

const codeDiff = '\
function cmdDiffRuns() {\
  const cwd = targetDir();\
  const diffRunsIdx = args.findIndex((a, i) => a === "diff-runs" && i < args.length - 2);\
  const runIdA = String(option("--id-a", diffRunsIdx !== -1 && args[diffRunsIdx + 1] ? args[diffRunsIdx + 1] : ""));\
  const runIdB = String(option("--id-b", diffRunsIdx !== -1 && args[diffRunsIdx + 2] ? args[diffRunsIdx + 2] : ""));\
  const format = String(option("--format", "text")).toLowerCase();\
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");\
\
  if (!runIdA || !runIdB) {\
    console.error("Usage: autoresearch diff-runs <id-a> <id-b> [--format text|json|markdown] [--dir PATH]");\
    process.exitCode = 1;\
    return;\
  }\
  if (!fs.existsSync(ledger)) {\
    console.error("No run ledger found.");\
    process.exitCode = 1;\
    return;\
  }\
\
  const rows = parseRunsLedger(ledger);\
  const rowA = rows.find((r) => r && !r.parse_error && String(r.id) === String(runIdA)) || null;\
  const rowB = rows.find((r) => r && !r.parse_error && String(r.id) === String(runIdB)) || null;\
\
  if (!rowA) { console.error("Run not found: " + runIdA); process.exitCode = 1; return; }\
  if (!rowB) { console.error("Run not found: " + runIdB); process.exitCode = 1; return; }\
\
  const identical = JSON.stringify(rowA) === JSON.stringify(rowB);\
\
  const allParamKeys = new Set([...Object.keys(rowA.params || {}), ...Object.keys(rowB.params || {})]);\
  const paramDiffs = [];\
  for (const key of allParamKeys) {\
    const valA = rowA.params?.[key];\
    const valB = rowB.params?.[key];\
    if (JSON.stringify(valA) !== JSON.stringify(valB)) {\
      paramDiffs.push({ key, a: valA, b: valB });\
    }\
  }\
\
  const allMetricKeys = new Set([...Object.keys(rowA.metrics || {}), ...Object.keys(rowB.metrics || {})]);\
  const metricDiffs = [];\
  for (const key of allMetricKeys) {\
    const valA = Number(rowA.metrics?.[key]);\
    const valB = Number(rowB.metrics?.[key]);\
    if (Number.isFinite(valA) && Number.isFinite(valB)) {\
      const delta = valB - valA;\
      const arrow = delta > 0 ? "\\u2191" : delta < 0 ? "\\u2193" : " ";\
      metricDiffs.push({ key, a: valA, b: valB, delta, arrow });\
    } else {\
      metricDiffs.push({ key, a: valA, b: valB, delta: null, arrow: "?" });\
    }\
  }\
\
  const envFields = ["git_sha", "python_version", "pip_freeze_sha256", "torch_version", "cuda_available", "os", "hostname"];\
  const envDiffs = [];\
  for (const field of envFields) {\
    const valA = rowA.env?.[field];\
    const valB = rowB.env?.[field];\
    if (JSON.stringify(valA) !== JSON.stringify(valB)) {\
      envDiffs.push({ field, a: valA, b: valB });\
    }\
  }\
\
  let codeDiffA = null;\
  let codeDiffB = null;\
  const runDirA = path.join(cwd, ".researchloop", "scratchpad", "runs", String(rowA.id));\
  const runDirB = path.join(cwd, ".researchloop", "scratchpad", "runs", String(rowB.id));\
  if (fs.existsSync(path.join(runDirA, "code.diff"))) {\
    codeDiffA = fs.readFileSync(path.join(runDirA, "code.diff"), "utf8");\
  }\
  if (fs.existsSync(path.join(runDirB, "code.diff"))) {\
    codeDiffB = fs.readFileSync(path.join(runDirB, "code.diff"), "utf8");\
  }\
  const codeChanged = codeDiffA !== codeDiffB;\
\
  const dataFpA = rowA.data_fingerprint || null;\
  const dataFpB = rowB.data_fingerprint || null;\
  const dataFingerprintChanged = dataFpA !== null && dataFpB !== null && dataFpA !== dataFpB;\
\
  if (format === "json") {\
    const out = {\
      id_a: runIdA,\
      id_b: runIdB,\
      identical,\
      params: { diffs: paramDiffs, changed: paramDiffs.length > 0 },\
      metrics: { diffs: metricDiffs, changed: metricDiffs.some((m) => m.delta !== 0) },\
      env: { diffs: envDiffs, changed: envDiffs.length > 0 },\
      code_diff: { changed: codeChanged, a: codeDiffA, b: codeDiffB },\
      data_fingerprint: { changed: dataFingerprintChanged, a: dataFpA, b: dataFpB },\
    };\
    console.log(JSON.stringify(out, null, 2));\
    return;\
  }\
\
  if (format === "markdown") {\
    const lines = [\
      "## Run Diff: " + runIdA + " vs " + runIdB,\
      "",\
      "| Section | Status |",\
      "| --- | --- |",\
      "| Params | " + (identical ? "identical" : paramDiffs.length === 0 ? "identical" : paramDiffs.length + " change(s)") + " |",\
      "| Metrics | " + (identical ? "identical" : metricDiffs.filter((m) => m.delta !== 0).length === 0 ? "identical" : metricDiffs.filter((m) => m.delta !== 0).length + " change(s)") + " |",\
      "| Env | " + (identical ? "identical" : envDiffs.length === 0 ? "identical" : envDiffs.length + " difference(s)") + " |",\
      "| Code | " + (identical ? "identical" : codeChanged ? "changed" : "unchanged") + " |",\
      "| Data fingerprint | " + (dataFpA === dataFpB ? "identical" : dataFingerprintChanged ? "changed" : "N/A") + " |",\
      "",\
    ];\
    if (!identical && paramDiffs.length > 0) {\
      lines.push("### Params Diff", "");\
      lines.push("| Param | Run A | Run B |", "| --- | --- | --- |");\
      for (const d of paramDiffs) {\
        lines.push("| " + d.key + " | " + JSON.stringify(d.a) + " | " + JSON.stringify(d.b) + " |");\
      }\
      lines.push("");\
    }\
    if (!identical && metricDiffs.length > 0) {\
      lines.push("### Metrics Diff", "");\
      lines.push("| Metric | Run A | Run B | Delta | Direction |", "| --- | --- | --- | --- | --- |");\
      for (const m of metricDiffs) {\
        const deltaStr = m.delta !== null && Number.isFinite(m.delta) ? m.delta.toFixed(4) : "N/A";\
        lines.push("| " + m.key + " | " + m.a + " | " + m.b + " | " + deltaStr + " | " + m.arrow + " |");\
      }\
      lines.push("");\
    }\
    if (!identical && envDiffs.length > 0) {\
      lines.push("### Env Diff", "");\
      lines.push("| Field | Run A | Run B |", "| --- | --- | --- |");\
      for (const d of envDiffs) {\
        lines.push("| " + d.field + " | " + JSON.stringify(d.a) + " | " + JSON.stringify(d.b) + " |");\
      }\
      lines.push("");\
    }\
    if (!identical && codeChanged && codeDiffA !== null && codeDiffB !== null) {\
      lines.push("### Code Diff", "");\
      lines.push("```diff");\
      lines.push("--- run " + runIdA);\
      lines.push("+++ run " + runIdB);\
      lines.push("```");\
      lines.push("");\
    }\
    if (!identical && dataFingerprintChanged) {\
      lines.push("### Data Fingerprint Diff", "");\
      lines.push("- Run A: " + dataFpA);\
      lines.push("- Run B: " + dataFpB);\
      lines.push("");\
    }\
    if (identical) {\
      lines.push("*All sections are identical.*");\
    }\
    process.stdout.write(lines.join("\\n") + "\\n");\
    return;\
  }\
\
  console.log("=== Run Diff: " + runIdA + " vs " + runIdB + " ===");\
  if (identical) {\
    console.log("Status: IDENTICAL (all sections match)");\
    return;\
  }\
  if (paramDiffs.length > 0) {\
    console.log("\\n--- Params Diff ---");\
    for (const d of paramDiffs) {\
      console.log("  " + d.key + ": " + JSON.stringify(d.a) + " -> " + JSON.stringify(d.b));\
    }\
  }\
  if (metricDiffs.length > 0) {\
    console.log("\\n--- Metrics Diff ---");\
    for (const m of metricDiffs) {\
      const deltaStr = m.delta !== null && Number.isFinite(m.delta)\
        ? (m.delta > 0 ? "+" : "") + m.delta.toFixed(4)\
        : "N/A";\
      console.log("  " + m.key + ": " + m.a + " -> " + m.b + " (" + deltaStr + ") " + m.arrow);\
    }\
  }\
  if (envDiffs.length > 0) {\
    console.log("\\n--- Env Diff ---");\
    for (const d of envDiffs) {\
      console.log("  " + d.field + ": " + JSON.stringify(d.a) + " -> " + JSON.stringify(d.b));\
    }\
  }\
  if (codeChanged) {\
    console.log("\\n--- Code Diff ---");\
    if (codeDiffA !== null && codeDiffB !== null) {\
      console.log("  code.diff: run " + runIdA + " and run " + runIdB + " differ");\
    } else if (codeDiffA !== null) {\
      console.log("  code.diff: present in run " + runIdA + ", absent in run " + runIdB);\
    } else if (codeDiffB !== null) {\
      console.log("  code.diff: absent in run " + runIdA + ", present in run " + runIdB);\
    }\
  }\
  if (dataFingerprintChanged) {\
    console.log("\\n--- Data Fingerprint Diff ---");\
    console.log("  data_fingerprint: " + dataFpA + " -> " + dataFpB);\
  }\
}';

const newContent = content.slice(0, idx) + "\n" + codeDiff + content.slice(idx);
fs.writeFileSync(researchloopPath, newContent);
console.log("cmdDiffRuns injected successfully");