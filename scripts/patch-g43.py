#!/usr/bin/env python3
"""Patch script for G43 tagging/annotation command"""

with open('bin/researchloop.js', 'r') as f:
    content = f.read()

# 1. Add cmdTag function before cmdHelp
old_fn = 'function cmdHelp() {'
new_fn = '''function cmdTag() {
  const cwd = targetDir();
  const runId = String(option("--id", ""));
  const addTag = option("--add", null);
  const removeTag = option("--remove", null);
  const listTags = hasFlag("--list");
  const ledger = path.join(cwd, ".researchloop", "scratchpad", "runs.jsonl");

  if (!runId && !listTags) {
    console.error("Usage: autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]");
    process.exitCode = 1;
    return;
  }
  if (!fs.existsSync(ledger)) {
    console.error("No run ledger found.");
    process.exitCode = 1;
    return;
  }

  const rows = parseRunsLedger(ledger);
  if (listTags) {
    // List all unique tags across all runs
    const tagSet = new Set();
    for (const row of rows) {
      if (row && !row.parse_error && row.tags) {
        for (const t of row.tags) tagSet.add(t);
      }
    }
    const tags = Array.from(tagSet).sort();
    if (tags.length === 0) {
      console.log("No tags recorded yet.");
    } else {
      console.log("Tags: " + tags.join(", "));
    }
    return;
  }

  if (!runId) {
    console.error("--id required for tag operations.");
    process.exitCode = 1;
    return;
  }

  const rowIdx = rows.findIndex((r) => r && !r.parse_error && String(r.id) === String(runId));
  if (rowIdx === -1) {
    console.error("Run not found: " + runId);
    process.exitCode = 1;
    return;
  }

  const row = rows[rowIdx];
  if (!row.tags) row.tags = [];

  if (addTag) {
    const tagStr = String(addTag).trim();
    if (!tagStr) {
      console.error("Tag cannot be empty.");
      process.exitCode = 1;
      return;
    }
    if (!row.tags.includes(tagStr)) {
      row.tags.push(tagStr);
      console.log("Tag added: " + tagStr);
    } else {
      console.log("Tag already exists: " + tagStr);
    }
  }

  if (removeTag) {
    const tagStr = String(removeTag).trim();
    const idx = row.tags.indexOf(tagStr);
    if (idx !== -1) {
      row.tags.splice(idx, 1);
      console.log("Tag removed: " + tagStr);
    } else {
      console.log("Tag not found: " + tagStr);
    }
  }

  if (addTag || removeTag) {
    rows[rowIdx] = row;
    const tmpLedger = ledger + ".tag_tmp";
    fs.writeFileSync(tmpLedger, rows.map((r) => JSON.stringify(r)).join("\\n") + "\\n");
    fs.renameSync(tmpLedger, ledger);
  }

  // Show current tags for this run
  if (row.tags && row.tags.length) {
    console.log("Tags for " + runId + ": " + row.tags.join(", "));
  } else {
    console.log("No tags for " + runId + ".");
  }
}

function cmdHelp() {'''

if old_fn not in content:
    print("ERROR: cmdHelp marker not found")
    exit(1)

content = content.replace(old_fn, new_fn, 1)

# 2. Add dispatch
old_dispatch = 'command === "model-card") {\n    cmdModelCard();\n  } else if (command === "data-fingerprint") {'
new_dispatch = 'command === "model-card") {\n    cmdModelCard();\n  } else if (command === "tag") {\n    cmdTag();\n  } else if (command === "data-fingerprint") {'

if old_dispatch not in content:
    print("ERROR: dispatch not found")
    exit(1)

content = content.replace(old_dispatch, new_dispatch, 1)

# 3. Add help text
old_help = '  autoresearch model-card --id <run-id> [--out FILE.md] [--dir PATH]'
new_help = '  autoresearch model-card --id <run-id> [--out FILE.md] [--dir PATH]\n  autoresearch tag --id <run-id> [--add TAG] [--remove TAG] [--list] [--dir PATH]'

if old_help not in content:
    print("ERROR: help text not found")
    exit(1)

content = content.replace(old_help, new_help, 1)

with open('bin/researchloop.js', 'w') as f:
    f.write(content)

print("G43 tag patched successfully, lines:", content.count('\n'))