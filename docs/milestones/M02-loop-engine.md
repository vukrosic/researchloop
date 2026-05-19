# M02 — Loop Engine

> **Status:** planned. This doc is the source of truth for the milestone. Each GitHub issue under this milestone links to a section here. Update the doc, not the issues, when scope shifts.

## The bet

Today AutoResearch-AI is a **disciplined logger**: it records experiments, baselines, env, and run rows. It does not yet **decide what to run next**. This milestone closes that gap with a small, pluggable search loop. Every plugin (history, ablation, paper-port, evolution) is just a function that turns the archive into a ranked batch of next candidates. The loop itself is a 4-stage state machine; everything else is shared infrastructure.

```text
                     ┌────────────────────┐
                     │   archive          │  runs.jsonl + mechanism + outcome
                     │   + failure ledger │  failures.jsonl (mechanism deaths)
                     └─────────┬──────────┘
                               │ read
   ┌───────────┐               ▼
   │ proposer  │  ────►  candidates.jsonl  (mechanism, files, ΔE, $)
   │ (plugin)  │
   └───────────┘               │
                               ▼
                     ┌────────────────────┐
                     │   evaluator        │  cheap-mode → full-mode
                     │   (run + budget)   │  kill on safety / divergence
                     └─────────┬──────────┘
                               ▼
                     ┌────────────────────┐
                     │   selector         │  rank, promote, kill,
                     │                    │  write outcome back to archive
                     └────────────────────┘
                               │ feed back
                               ▼
                          (next cycle)
```

---

## Dependency graph

```text
F1 (archive schema) ─┬─► L1 (propose orch)     ─┬─► L2 (loop driver) ──► U3 (loop --watch)
                     │                          │
F2 (failure ledger) ─┼─► L3 (rank w/ failures)  ┘
                     │                                          
F3 (proposer iface) ─┴─► P1 history ─► D1 dogfood             U1 archive view
                         P2 ablation ─► D2 dogfood             U2 dashboard panel
                         P3 paper-port ─► D3 dogfood
                         P4 evolution ─► D4 dogfood

E1 (cheap_mode schema) ─► E2 (run --cheap) ─► E3 (escalation, used by L2)
```

**Critical path:** F1 → L1 → L2 → first dogfood. Everything else can run in parallel after F1+F2+F3 land.

## Parallelism — who can work at the same time

| Wave | Issues that can run concurrently | Why parallel |
|---|---|---|
| **0** | F1, F2, F3, E1 | Each writes to its own new file under `bin/lib/` or `templates/`; the only collision point is `bin/researchloop.js` and they each add a small registration line in a separate location. |
| **1** | L1, L3, E2, U1 | F# foundation landed. Each touches a different command. |
| **2** | L2, E3, P1, P2, P3, P4, U2 | The loop driver is sequential by itself; proposer plugins live in `bin/proposers/<name>/` (no collisions). |
| **3** | D1, D2, D3, D4, U3 | Dogfoods only need their own plugin landed. |

`bin/researchloop.js` is the one shared file. Each issue lands its real code in a `bin/lib/<module>.js` or `bin/proposers/<name>/` file and only adds a 1–3 line command registration in `researchloop.js`. The integration owner (reviewer) merges PRs in wave order.

---

## Shared conventions for every issue in this milestone

- **Plain files first.** Every new state file is JSONL or YAML/Markdown under `.researchloop/`. No DBs.
- **Stdin/stdout for plugins.** No subprocess globals, no environment passing. Plugin runners hand the plugin a JSON blob on stdin and read JSON on stdout. Plugin failures = non-zero exit + JSON error on stderr.
- **JSON schemas live in `templates/schemas/`.** Every new file format ships its schema there. Tests assert against the schema with a tiny `node bin/researchloop.js schema validate <file> <schema>` helper (added in F1).
- **Test script per issue.** `scripts/test-<slug>.sh`, hooked into `npm test`. The script creates a temp dir, exercises happy path + at least one failure path, exits non-zero on failure.
- **Safety policy passes.** All commands that shell out must go through `evaluateCommandSafety` (G25). Cheap-mode runs respect `max_minutes_per_run`.
- **No mutation of existing shipped commands without a flag.** Extensions to `run`, `rank`, `eval.yaml` must be opt-in (`--cheap`, new optional keys) so existing dogfoods stay green.

---

## Wave 0 — Shared foundation

### M02-F1 — Archive schema v2: mechanism, outcome, lineage

**Researcher line.** A researcher running a multi-day loop needs every row in `runs.jsonl` to carry *what the change actually was* and *whether it lived or died*, because otherwise the proposer keeps re-suggesting dead mechanisms and the rank command can't deduplicate.

**Demo line.**
```text
$ autoresearch run --command "python train.py --dropout=0.1" \
    --mechanism "dropout=0.1" --parent-run-id r-014
[run r-018] dropout=0.1 → val_loss 2.38

$ autoresearch archive view --mechanism "dropout=*"
r-014  dropout=0.05  kept       val_loss 2.41
r-018  dropout=0.1   pending    val_loss 2.38
r-022  dropout=0.2   killed_baseline  val_loss 2.55
```

**New fields appended to every row in `runs.jsonl`:**

| Field | Type | Required | Default for migration | Notes |
|---|---|---|---|---|
| `mechanism` | string | yes (new rows) | `"unknown"` | Short human slug, ≤ 60 chars. Canonicalize: lowercase, replace ` ` with `-`. |
| `mechanism_hash` | string | yes (new rows) | sha256 of `"unknown"` | sha256(canonical(mechanism)), first 16 hex chars. |
| `outcome` | enum | yes (new rows) | `"pending"` | `pending \| kept \| killed_baseline \| killed_budget \| killed_diverged \| killed_oom \| killed_safety \| discarded` |
| `parent_run_id` | string\|null | yes (new rows) | `null` | The run this was perturbed from, or `null` for fresh starts. |
| `proposer` | string\|null | yes (new rows) | `null` | Plugin name. `null` for manual runs. |
| `cycle_id` | string\|null | yes (new rows) | `null` | Loop cycle id from L2. `null` for manual runs. |
| `cheap` | bool | yes (new rows) | `false` | Set by E2 (`--cheap`). |

**New module: `bin/lib/archive.js`.** Exports:

```js
export function readArchive(dir = '.')           // → Array<row>
export function appendRow(row, dir = '.')        // validates against schema, appends
export function migrateRow(oldRow)               // → newRow with defaults
export function mechanismHash(mechanismStr)      // → 16-hex-char string
export function searchByMechanism(predicate, dir) // → Array<row>; predicate(row) → bool
export function findRunById(runId, dir)          // → row | null
```

**New command: `autoresearch archive migrate [--dir PATH] [--dry-run]`.** Reads `.researchloop/runs.jsonl`, applies `migrateRow` to each row missing v2 fields, writes back. With `--dry-run`, prints the diff and exits 0.

**New schema file: `templates/schemas/run-row.schema.json`.** JSON Schema for a v2 row. Used by tests and by L1's validator.

**New helper command: `autoresearch schema validate <file> <schema>`.** Generic validator — used by tests in all later issues.

**Acceptance.**
- [ ] `autoresearch run --command "echo hi" --mechanism "noop"` writes a row with all v2 fields populated and a non-empty `mechanism_hash`.
- [ ] `autoresearch archive migrate --dry-run` on a v1 ledger prints a diff that adds (only) the v2 fields with defaults.
- [ ] `autoresearch archive migrate` on a v1 ledger transforms it to v2; running again is a no-op.
- [ ] `autoresearch archive view --mechanism "<glob>"` filters rows by mechanism glob.
- [ ] `autoresearch schema validate .researchloop/runs.jsonl templates/schemas/run-row.schema.json` exits 0 on a valid ledger, non-zero on a corrupt one with a line + field message.
- [ ] `scripts/test-archive-schema.sh` covers: write+read, migration idempotency, schema rejection of bad rows, mechanism hash stability across runs.
- [ ] `npm test` is green.

**Anti-features.**
- Does NOT change the existing `metrics` / `env` / `command` row shape. Strict-additive.
- Does NOT introduce a database. JSONL stays the on-disk format.
- Does NOT auto-infer `mechanism` from a diff — that's the proposer's job.

**Files owned.**
- `bin/lib/archive.js` (new)
- `bin/researchloop.js` (additions: `archive migrate`, `archive view`, `schema validate`)
- `templates/schemas/run-row.schema.json` (new)
- `scripts/test-archive-schema.sh` (new)
- `package.json` — add `test:archive-schema` to the `test` script

**Depends on.** None.

---

### M02-F2 — Failure ledger

**Researcher line.** A researcher running the loop overnight needs the proposer to *stop suggesting things we already proved don't work*, because otherwise every cycle re-litigates the same dead mechanism and wastes a GPU-hour.

**Demo line.**
```text
$ autoresearch loop --plugin history --max-candidates 3
[cycle c-007] proposed 3 candidates
[c-007] candidate "dropout=0.2" → mechanism_hash matches dead entry from c-004 → skipped
[c-007] candidate "lr=1e-3"     → ran, val_loss 2.55 → kill: killed_baseline
[c-007] candidate "rope-base=20k" → ran, val_loss 2.36 → kept
$ cat .researchloop/failures.jsonl | wc -l
4
```

**New file: `.researchloop/failures.jsonl`.** Append-only. Each line:

```json
{
  "mechanism": "dropout=0.2",
  "mechanism_hash": "a3f9c1d2...",
  "reason": "below_baseline",
  "evidence_run_ids": ["r-022"],
  "first_attempt": "2026-05-18T02:14:00Z",
  "last_attempt": "2026-05-19T11:30:00Z",
  "attempts": 2,
  "baseline_metric": 2.40,
  "observed_metric": 2.55
}
```

`reason` ∈ `{below_baseline, diverged, oom, timeout, manual_kill, eval_error, killed_safety}`.

**New module: `bin/lib/failures.js`.** Exports:

```js
export function appendFailure(rec, dir = '.')      // upserts by mechanism_hash; bumps `attempts` and `last_attempt`
export function lookupFailure(mechanismHash, dir)  // → record | null
export function isMechanismDead(mechanismHash, dir, { minAttempts = 1 } = {}) // → bool
export function readFailures(dir)                  // → Array<record>
export function nearestDeadMechanism(mechanism, dir, threshold = 0.85)
//   → { record, similarity } | null
//   similarity = Jaro-Winkler over canonicalized mechanism strings
```

**Append-on-kill integration.** A small hook in `bin/researchloop.js`'s run wrapper: when a run completes with outcome ≠ `kept`, also call `appendFailure` with the right reason. This is the only modification to existing run logic in F2; it is gated behind the v2 schema being present.

**New schema: `templates/schemas/failure.schema.json`.**

**Acceptance.**
- [ ] After a run that ends `killed_baseline`, `.researchloop/failures.jsonl` has a row with that run's mechanism_hash and `attempts: 1`.
- [ ] A second run with the same `mechanism_hash` ending in any kill state bumps `attempts: 2` and updates `last_attempt` (does NOT create a second row).
- [ ] `isMechanismDead(hash)` returns true after one kill by default.
- [ ] `nearestDeadMechanism("dropout=0.19", ...)` returns the `dropout=0.2` record with similarity > 0.85.
- [ ] `scripts/test-failures.sh` covers: append, upsert, similarity match, schema validation.

**Anti-features.**
- Does NOT auto-clean entries. Dead is dead until a human or a future "reconsider" command clears them.
- Does NOT prevent a run from happening — only L3 (rank) and L2 (loop) read this ledger to filter / deprioritize.

**Files owned.**
- `bin/lib/failures.js` (new)
- `bin/researchloop.js` (hook in run wrapper; ~5 lines)
- `templates/schemas/failure.schema.json` (new)
- `scripts/test-failures.sh` (new)

**Depends on.** F1.

---

### M02-F3 — Proposer plugin interface

**Researcher line.** A researcher (and the four plugin authors after this issue) needs a stable, language-agnostic contract for "given the archive, return a ranked batch of candidates", because plugins should be swappable and forkable without touching the core.

**Demo line.**
```text
$ ls bin/proposers/
null/  history/  ablation/  paper-port/  evolution/

$ autoresearch propose --plugin null --k 3
[propose] plugin=null returned 0 candidates (expected for null)

$ autoresearch propose --plugin history --k 3
[propose] plugin=history returned 3 candidates → .researchloop/candidates.jsonl
```

**Plugin contract.** Each plugin lives at `bin/proposers/<name>/index.{mjs,sh,py}` and is invoked as `<runtime> bin/proposers/<name>/index.<ext>`. The plugin reads one JSON blob from stdin and writes one JSON blob to stdout.

**Stdin schema (input to plugin):**

```json
{
  "archive_path": ".researchloop/runs.jsonl",
  "failures_path": ".researchloop/failures.jsonl",
  "baseline": { "command": "...", "metric_name": "val_loss", "metric_value": 2.40, "git_sha": "..." },
  "budget": { "max_runs": 3, "max_minutes_per_run": 30 },
  "k": 3,
  "cycle_id": "c-007",
  "dir": "/abs/path/to/repo",
  "plugin_config": { /* optional, from .researchloop/proposers/<name>.yaml */ }
}
```

**Stdout schema (output from plugin):**

```json
{
  "proposer": "history",
  "cycle_id": "c-007",
  "candidates": [
    {
      "mechanism": "dropout=0.1",
      "rationale": "perturbing best-of-archive dropout=0.05 by +0.05 (top-3 sensitive)",
      "files_to_touch": ["configs/base.yaml"],
      "config_delta": { "dropout": 0.1 },
      "command_override": null,
      "parent_run_id": "r-014",
      "expected_delta": -0.02,
      "cost_estimate_usd": 0.40,
      "evidence": [ { "type": "run", "id": "r-014" } ]
    }
  ]
}
```

`expected_delta` is signed: negative means "lower val_loss is the goal, so we expect a decrease". The selector inverts based on `metric_direction` in eval.yaml.

**New module: `bin/lib/proposers.js`.** Exports:

```js
export function discoverProposers()                 // → [{ name, runtime, path }]
export function runProposer(name, input, opts)      // → { stdout, stderr, exitCode }
export function validateProposerOutput(output)      // → { ok, errors[] }
```

**Stub plugin: `bin/proposers/null/`.**
- `index.mjs`: reads stdin, returns `{ proposer: "null", cycle_id, candidates: [] }`.
- `README.md`: "Returns no candidates. Used to test the interface."

**New schema: `templates/schemas/proposer-input.schema.json`, `templates/schemas/proposer-output.schema.json`.**

**Acceptance.**
- [ ] `discoverProposers()` finds the `null` plugin without any registry file (auto-discovery from `bin/proposers/*/index.*`).
- [ ] `autoresearch propose --plugin null` returns successfully with 0 candidates.
- [ ] Output that fails the schema (e.g. missing `mechanism` field) is rejected with a clear error line.
- [ ] A plugin that exits non-zero produces an error message including the plugin's stderr — does not crash the CLI.
- [ ] `scripts/test-proposers-interface.sh` covers: null plugin happy path, bad-output rejection, plugin-crash handling, schema validation.

**Anti-features.**
- Does NOT define a Python or Node-only API. Stdin/stdout JSON only.
- Does NOT execute candidate commands. Only L1/L2 do that.
- Does NOT cache plugin output across cycles (cache is a future issue).

**Files owned.**
- `bin/lib/proposers.js` (new)
- `bin/proposers/null/index.mjs` (new)
- `bin/proposers/null/README.md` (new)
- `templates/schemas/proposer-input.schema.json` (new)
- `templates/schemas/proposer-output.schema.json` (new)
- `scripts/test-proposers-interface.sh` (new)

**Depends on.** F1 (schemas + validator helper).

---

### M02-E1 — `eval.yaml` cheap_mode block

**Researcher line.** A researcher with a 3-hour training script needs the loop to sanity-check candidates at 1–5% scale first, because committing a full GPU-hour per random idea is the dominant cost of automated search.

**Demo line.**
```text
# .researchloop/eval.yaml
metric:
  name: val_loss
  direction: minimize
cheap_mode:
  data_fraction: 0.01
  max_steps: 500
  max_minutes: 5
  override_args: ["--max-steps=500", "--data-frac=0.01"]
  acceptance_band: 0.05   # cheap result within this of baseline → escalate to full
```

**Schema extension.** Add the `cheap_mode` block to `.researchloop/eval.yaml`. Required keys when present: `max_minutes`; either `override_args` (list passed to command) or `data_fraction` + `max_steps` (advisory, not enforced by E1 — E2 handles the wiring).

**Acceptance.**
- [ ] `templates/eval.yaml` documents the `cheap_mode` block in a header comment.
- [ ] `templates/schemas/eval.schema.json` is updated and `autoresearch schema validate .researchloop/eval.yaml ...` passes on the new template.
- [ ] `docs/eval-schema.md` describes the block with one worked example.
- [ ] `scripts/test-eval-schema.sh` validates both legacy (no cheap_mode) and new templates.

**Anti-features.**
- Does NOT execute anything — pure schema/doc change.

**Files owned.**
- `templates/eval.yaml`
- `templates/schemas/eval.schema.json` (new or extended)
- `docs/eval-schema.md` (new)
- `scripts/test-eval-schema.sh` (new)

**Depends on.** None (G04 already shipped).

---

## Wave 1 — Loop driver + runner extensions

### M02-L1 — `autoresearch propose --plugin <name>`

**Researcher line.** A researcher chaining `propose → run → compare` manually needs a single command that drives a plugin and stages its candidates as a real, replayable batch, because today there is no on-disk artifact between "the agent had an idea" and "we ran it".

**Demo line.**
```text
$ autoresearch propose --plugin history --k 3 --cycle-id c-008
[propose] plugin=history → 3 candidates written to .researchloop/cycles/c-008/candidates.jsonl
$ autoresearch propose --explain c-008
candidate-0  dropout=0.1     parent=r-014  expected -0.02  $0.40
candidate-1  lr=2e-4         parent=r-014  expected -0.01  $0.40
candidate-2  rope-base=20000 parent=r-014  expected -0.03  $0.40
```

**Behaviour.**
- Reads baseline from `.researchloop/baseline.lock` (G27) or `.researchloop/baseline.md` (G26).
- Builds the plugin input blob, runs the plugin via `bin/lib/proposers.js`, validates output.
- Writes candidates to `.researchloop/cycles/<cycle_id>/candidates.jsonl` (cycle_id auto-generated if omitted; format: `c-NNN` zero-padded next index).
- `--explain <cycle_id>` pretty-prints the candidate batch.
- `--dry-run` runs the plugin but does not write any state.

**Acceptance.**
- [ ] `propose --plugin null --k 1` exits 0 and writes a valid (empty) candidates file.
- [ ] `propose --plugin history --k 3` writes 3 schema-valid candidate rows.
- [ ] Missing baseline → exits non-zero with a message that points at `baseline-status` (G26).
- [ ] Plugin output that fails schema → exits non-zero with the line + field of the violation.
- [ ] `propose --explain c-XXX` prints a table; missing cycle → clear error.
- [ ] `scripts/test-propose-plugin.sh` covers happy path + missing baseline + bad plugin output + `--dry-run`.

**Anti-features.**
- Does NOT execute candidates. Only stages them.
- Does NOT rank — that's L3.

**Files owned.**
- `bin/researchloop.js` (extend `cmdPropose`)
- `scripts/test-propose-plugin.sh` (new)

**Depends on.** F1, F3.

---

### M02-L3 — rank with failure awareness

**Researcher line.** A researcher reviewing tomorrow's candidate batch needs the ranked list to bury anything that we already proved doesn't work, because otherwise the top-K is contaminated with re-suggestions.

**Demo line.**
```text
$ autoresearch rank c-008
rank  cand-id          mechanism        score   notes
  1   c-008-cand-2     rope-base=20000  0.78    novel mechanism
  2   c-008-cand-1     lr=2e-4          0.62    novel mechanism
  3   c-008-cand-0     dropout=0.1      0.05    PENALIZED: similar to dead mechanism "dropout=0.2" (sim 0.91)
```

**Behaviour.**
- Extends existing `rank` (G02). Reads `failures.jsonl` and applies a multiplicative penalty `(1 - similarity)` to any candidate whose `mechanism_hash` is in the ledger or whose `nearestDeadMechanism` similarity > 0.85.
- Penalty surface visible in the explanation column.

**Acceptance.**
- [ ] A candidate with an exact-match dead `mechanism_hash` ranks last with score ≤ 0.1 and a `PENALIZED` note.
- [ ] A candidate with similarity 0.91 to a dead entry gets penalized in proportion.
- [ ] A novel mechanism ranks above any penalized one.
- [ ] `scripts/test-rank-failures.sh` covers exact match + near match + no failures present.

**Anti-features.**
- Does NOT remove penalized candidates from the file. Just reorders / annotates.

**Files owned.**
- `bin/researchloop.js` (extend `cmdRank`)
- `scripts/test-rank-failures.sh` (new)

**Depends on.** F2.

---

### M02-E2 — `autoresearch run --cheap`

**Researcher line.** A researcher running the loop overnight needs `run --cheap` to actually execute the candidate at 1–5% scale and tag the row as cheap, because otherwise nothing in the archive distinguishes a screened-out idea from a fully-trained loser.

**Demo line.**
```text
$ autoresearch run --cheap --command "python train.py" --mechanism "dropout=0.1"
[run r-019] CHEAP mode (max-steps=500, data-frac=0.01) → val_loss 2.45 in 4m12s
$ autoresearch archive view --cheap-only
r-019  dropout=0.1   cheap  pending  val_loss 2.45
```

**Behaviour.**
- Reads `cheap_mode` block from `.researchloop/eval.yaml`. If missing, exits non-zero with a pointer to E1.
- Appends `override_args` to the command before invoking it.
- Enforces `max_minutes` via the existing safety policy (G25).
- Sets `cheap: true` on the row.
- Row's `outcome` stays `pending`; the selector (in L2) decides escalation/kill.

**Acceptance.**
- [ ] `run --cheap` with no `cheap_mode` block exits non-zero with a clear message.
- [ ] A cheap run respects `max_minutes` (kills at the cap with `outcome: killed_safety` and `cheap: true`).
- [ ] The resulting row has `cheap: true` and the override_args appear in `row.command`.
- [ ] `scripts/test-cheap-mode.sh` covers happy path, missing config, time-cap kill.

**Anti-features.**
- Does NOT auto-escalate. E3 does that.
- Does NOT change behaviour of `run` without `--cheap`.

**Files owned.**
- `bin/researchloop.js` (extend `cmdRun`)
- `scripts/test-cheap-mode.sh` (new)

**Depends on.** E1, F1.

---

### M02-U1 — `autoresearch archive view` / `archive search`

**Researcher line.** A researcher (and every plugin author) needs a fast CLI query over the archive by mechanism, outcome, proposer, and cycle, because grepping JSONL by hand is the friction that makes humans stop using their own tool.

**Demo line.**
```text
$ autoresearch archive view --proposer history --outcome kept --limit 5
$ autoresearch archive search --mechanism "dropout=*" --since 2026-05-15
$ autoresearch archive view --cycle c-007 --format json
```

**Acceptance.**
- [ ] All four filters work and compose (AND semantics).
- [ ] Globs supported on `--mechanism`.
- [ ] `--format json` emits a JSON array; `--format text` is the default table.
- [ ] `scripts/test-archive-view.sh` covers each filter, format, no-match, and corrupt-row tolerance.

**Anti-features.**
- Does NOT mutate the archive.

**Files owned.**
- `bin/researchloop.js` (extend `cmdArchive`)
- `scripts/test-archive-view.sh` (new)

**Depends on.** F1.

---

## Wave 2 — Loop driver + proposer plugins

### M02-L2 — `autoresearch loop`

**Researcher line.** A researcher who wants to walk away for an hour needs *one* command that runs propose → rank → cheap-eval → select → write-back, because chaining them by hand defeats the point.

**Demo line.**
```text
$ autoresearch loop --plugin history --max-candidates 3 --budget-runs 3
[c-008] propose      → 3 candidates
[c-008] rank         → top 3: rope-base=20000, lr=2e-4, dropout=0.1 (penalized)
[c-008] cheap-eval   r-019 dropout=0.1   → val_loss 2.45 (over baseline 2.40) → killed_baseline
[c-008] cheap-eval   r-020 lr=2e-4       → val_loss 2.38 (under baseline) → ESCALATE (E3)
[c-008] cheap-eval   r-021 rope-base=20k → val_loss 2.36 (under baseline) → ESCALATE (E3)
[c-008] cycle summary → .researchloop/cycles/c-008/SUMMARY.md
```

**Behaviour.**
- Wraps the four stages. Each stage writes its artifact under `.researchloop/cycles/<cycle_id>/`:
  - `candidates.jsonl` (L1)
  - `ranked.jsonl` (L3)
  - `runs.jsonl` (rows for cheap-mode evals; also appended to the global archive)
  - `SUMMARY.md` (human-readable cycle report, generated last)
- Safety: refuses to start if `baseline-status` reports incomplete. Refuses to start if `safety.yaml` is missing.
- Budget: respects existing G67 budget command if a budget file is present.
- Escalation: if E3 has shipped, escalates passing cheap runs to full mode. If E3 not present, marks the row `outcome: pending` and emits a TODO list in `SUMMARY.md`.

**New module: `bin/lib/loop.js`.** Encapsulates the cycle state machine. `bin/researchloop.js` only registers `cmdLoop` and delegates.

**Acceptance.**
- [ ] `loop --plugin null` runs end-to-end with zero candidates and writes a `SUMMARY.md` saying "no candidates proposed".
- [ ] `loop --plugin history` on a repo with a real baseline produces a SUMMARY.md with each candidate's mechanism, cheap result, and decision.
- [ ] Missing baseline → exits non-zero with a baseline-status pointer.
- [ ] `--max-candidates 0` exits 0 as a no-op.
- [ ] A candidate that exceeds `max_minutes_per_run` ends with `killed_safety` and feeds the failure ledger.
- [ ] `scripts/test-loop.sh` covers null happy path, history happy path with two passing + one penalized candidate, missing baseline, safety kill.

**Anti-features.**
- Does NOT run a daemon. One cycle per invocation. U3 does --watch.
- Does NOT pick the plugin automatically. Caller must specify.

**Files owned.**
- `bin/lib/loop.js` (new)
- `bin/researchloop.js` (register `cmdLoop`)
- `scripts/test-loop.sh` (new)

**Depends on.** F1, F2, F3, L1, L3, E2.

---

### M02-E3 — cheap-to-full escalation

**Researcher line.** A researcher needs cheap-mode wins to automatically queue a full-mode confirmation, because the whole point of cheap-mode is to filter; a filter that doesn't promote winners is just a strainer with a hole.

**Demo line.**
```text
[c-008] cheap-eval r-020 lr=2e-4 → val_loss 2.38 (Δ -0.02, within 0.05 band of baseline)
[c-008] ESCALATE r-020 → full-mode run r-020-full enqueued
```

**Behaviour.**
- Triggered inside L2 after each cheap eval.
- Condition: `cheap_result.metric` is better than baseline OR within `acceptance_band` of baseline.
- Effect: enqueues a full-mode run (no `--cheap`) with the same `mechanism`, `parent_run_id`, and `cycle_id`. Outcome on the full-mode row is what counts for `kept`/`killed_baseline`.

**Acceptance.**
- [ ] Cheap row with improvement triggers a full-mode row that shares mechanism + cycle_id but has `cheap: false`.
- [ ] Cheap row that misses the band leaves no full-mode follow-up and writes a failure ledger entry on the cheap row's mechanism.
- [ ] `scripts/test-escalation.sh` covers both branches.

**Anti-features.**
- Does NOT escalate without a `cheap_mode.acceptance_band` set.
- Does NOT escalate already-escalated mechanisms in the same cycle.

**Files owned.**
- `bin/lib/loop.js` (escalation function)
- `scripts/test-escalation.sh` (new)

**Depends on.** L2, E2.

---

### M02-P1 — `history` proposer (the chassis check)

**Researcher line.** A researcher with a populated archive needs a first plugin that just perturbs the current best run along its most-sensitive dimensions, because that's the cheapest demonstration that the loop interface works end-to-end.

**Demo line.**
```text
$ autoresearch propose --plugin history --k 3
candidate-0 dropout=0.10   parent r-014  expected -0.02
candidate-1 lr=2.0e-4      parent r-014  expected -0.01
candidate-2 rope-base=20000 parent r-014  expected -0.03
```

**Algorithm.**
1. Read archive. Filter to `outcome: kept` rows. Pick top-K by metric.
2. Across those rows' `config_delta` or `command` strings, compute variance per scalar key. Top-3 by variance = "sensitive dimensions".
3. For each sensitive dimension, propose one perturbation of the best run's value (±25% or ±1σ of observed range, whichever is smaller).
4. Skip any candidate whose `mechanism_hash` is in the failure ledger.

**Acceptance.**
- [ ] On a fixture archive with 5 `kept` rows varying `dropout`, `lr`, `rope-base`, the plugin emits 3 candidates touching those three keys.
- [ ] On an empty archive (no `kept` rows) the plugin returns 0 candidates with rationale "no kept runs to perturb from".
- [ ] Dead mechanisms are skipped.
- [ ] `scripts/test-proposer-history.sh` covers all three.

**Anti-features.**
- Does NOT touch list/dict-valued keys (only scalars).
- Does NOT call any LLM. Pure analytical plugin.

**Files owned.**
- `bin/proposers/history/index.mjs` (new)
- `bin/proposers/history/README.md` (new)
- `examples/fixtures/history-proposer/` (new — sample archive)
- `scripts/test-proposer-history.sh` (new)

**Depends on.** F1, F2, F3.

---

### M02-P2 — `ablation` proposer

**Researcher line.** A researcher with a working system needs a plugin that automatically removes each component once to find what carries the metric, because ablation is the cheapest path to a publishable interpretability result and humans skip it.

**Algorithm.**
1. Read the current best `kept` run's command + referenced config files.
2. Inspect repo: for each top-level key in the active config file(s), and each `import` in the entrypoint script (typically `train.py` or `main.py`), record it as a *component*.
3. For each component, emit one candidate that "removes" it. Removal heuristics:
   - Config scalar: set to the schema default (or `null` if no schema).
   - Config list: replace with `[]`.
   - Module import: replace the call site with an identity passthrough (the plugin doesn't have to do this — it emits a `files_to_touch` plan and the calling agent implements it).
4. `expected_delta` defaults to 0 — ablation isn't predicting improvement; it's measuring contribution.

**Acceptance.**
- [ ] On a fixture repo with a config that has `dropout`, `weight_decay`, `lr_scheduler`, the plugin emits 3 candidates each zeroing/disabling one.
- [ ] `mechanism` strings are of the form `ablate:<component>`.
- [ ] `files_to_touch` is populated; `config_delta` is populated for config-level ablations.
- [ ] `scripts/test-proposer-ablation.sh` covers fixture + missing best-run case.

**Anti-features.**
- Does NOT actually edit files. Only emits the plan.
- Does NOT try to ablate everything in one cycle — emits one component per candidate, capped at `k`.

**Files owned.**
- `bin/proposers/ablation/index.mjs` (new)
- `bin/proposers/ablation/README.md` (new)
- `examples/fixtures/ablation-proposer/` (new)
- `scripts/test-proposer-ablation.sh` (new)

**Depends on.** F1, F3.

---

### M02-P3 — `paper-port` proposer

**Researcher line.** A researcher who ran `paper-read` on three recent arxiv papers needs a plugin that converts those notes into concrete porting candidates against the local baseline, because notes that don't become experiments are just bookmarks.

**Algorithm.**
1. Glob `.researchloop/scratchpad/papers/*.md`. Parse the five required G29 sections per file.
2. For each note whose `how to port this` section is non-empty:
   - Extract files-to-touch hints (`backticked paths` or paths under `files:` if present).
   - Build a candidate with `mechanism: "port:<paper-id>:<short-claim>"`, `files_to_touch` from the hints, `evidence: [{type: "paper", id: paper_id}]`.
3. Skip if the paper-id's mechanism_hash is already in the archive (already attempted) or in failures (already killed).

**Acceptance.**
- [ ] On a fixture with two `paper-read` notes, plugin emits two candidates with `mechanism` starting `port:`.
- [ ] A note with an empty "how to port this" section is skipped with a `notes_incomplete` rationale logged to stderr.
- [ ] Already-attempted papers are skipped.
- [ ] `scripts/test-proposer-paper-port.sh` covers fixture + skip cases.

**Anti-features.**
- Does NOT fetch arxiv. Reads only existing notes.
- Does NOT actually port code.

**Files owned.**
- `bin/proposers/paper-port/index.mjs` (new)
- `bin/proposers/paper-port/README.md` (new)
- `examples/fixtures/paper-port-proposer/` (new)
- `scripts/test-proposer-paper-port.sh` (new)

**Depends on.** F1, F3, G29.

---

### M02-P4 — `evolution` proposer (scoped)

**Researcher line.** A researcher on a sub-problem with a fast deterministic eval (sampler tuning, loss tweaks, small-model arch) needs an evolutionary search plugin that keeps a population and mutates the best, because for these sub-problems random + history is provably worse than guided evolution.

**Behaviour.**
- Reads/writes `.researchloop/evolution/<generation>.jsonl` — a population of program/config snippets with fitness scores from the archive.
- Selects top-N parents (default N=4, configurable).
- For each parent, builds an LLM mutation prompt (template: `templates/prompts/evolution-mutate.md`) and emits it as a candidate whose `files_to_touch` is the parent's surface and whose `mechanism` is `evolve:gen-<g>:cand-<i>`.
- **Important constraint.** Plugin refuses to run unless `eval.yaml` has `cheap_mode.max_minutes <= 10`. Evolution requires fast eval; on a slow eval this plugin should not be used.
- The plugin itself does NOT call an LLM. It writes the mutation prompt into the candidate's `rationale` field and into a sidecar `mutation-prompt.md` under the cycle dir; the orchestrating agent (Claude/Codex/Cursor) is expected to read and apply it. This keeps the plugin offline-safe.

**Acceptance.**
- [ ] Refuses to run if `cheap_mode.max_minutes > 10` (or missing) with a clear message.
- [ ] On generation 0 with no population, emits candidates from history-best as parents.
- [ ] Writes generation files atomically (temp + rename).
- [ ] `mechanism` strings encode generation + parent + slot.
- [ ] `scripts/test-proposer-evolution.sh` covers refuse-path + happy generation-0 + generation-1 reading prior population.

**Anti-features.**
- Does NOT call an LLM directly.
- Does NOT escape the sub-problem constraint check.
- Does NOT cross-pollinate across cycles outside `.researchloop/evolution/`.

**Files owned.**
- `bin/proposers/evolution/index.mjs` (new)
- `bin/proposers/evolution/README.md` (new)
- `templates/prompts/evolution-mutate.md` (new)
- `examples/fixtures/evolution-proposer/` (new)
- `scripts/test-proposer-evolution.sh` (new)

**Depends on.** F1, F3, E1.

---

### M02-U2 — Dashboard "loop" panel

**Researcher line.** A researcher with `dashboard` already running needs a loop view that lists recent cycles, the candidate batch per cycle, and per-candidate outcome, because flipping between `archive view` and the dashboard is the seam where teams lose the thread.

**Behaviour.**
- New page in the existing static dashboard at `/loop`.
- Reads `.researchloop/cycles/*/SUMMARY.md` and renders a table of cycles with sparkline of pass/fail counts.
- Click-through on a cycle opens its `SUMMARY.md` rendered inline.

**Acceptance.**
- [ ] `autoresearch dashboard` shows a "Loop" link in the nav after at least one cycle exists.
- [ ] The loop page renders a table with cycle_id, plugin, candidates, kept count, killed count, started_at.
- [ ] Empty state (no cycles) shows a "run `autoresearch loop` to start" hint.

**Anti-features.**
- Does NOT add live updates. Static read-on-load matches the existing dashboard contract.

**Files owned.**
- `templates/dashboard/loop.html` (new)
- `bin/researchloop.js` (server route)
- `scripts/test-dashboard-loop.sh` (new)

**Depends on.** L2.

---

## Wave 3 — Dogfood gates + watch mode

### M02-D1..D4 — Dogfood per plugin

For each of P1..P4, run a full cycle on `llm-research-kit` (or an equivalent small fixture) and commit:

- `examples/dogfood/<plugin>-proposer/` containing:
  - The cycle's `candidates.jsonl`, `ranked.jsonl`, `SUMMARY.md` (copied).
  - A `RESULT.md` documenting: what worked, what required manual rescue, which G## or M02 issue would have prevented each rescue.
  - A short asciinema or text transcript.

Each dogfood is a separate issue. Each dogfood must:
- [ ] Run from a clean clone without modifying the loop code.
- [ ] Produce at least one candidate with `outcome: kept` OR document why none could be kept (negative-result acceptance).
- [ ] Have its `RESULT.md` peer-reviewed before close.

**Depends on.** The matching P# plus L2.

---

### M02-U3 — `autoresearch loop --watch`

**Researcher line.** A researcher walking away for the night needs the loop to keep cycling until a budget halts it, because manually re-running `autoresearch loop` is what `cron` is for, but cron doesn't know about budgets.

**Behaviour.**
- `autoresearch loop --watch --plugin <name> --interval 0` runs one cycle, then the next, with no delay between (`--interval N` adds N seconds).
- Halts on:
  - G67 budget reached (writes BUDGET_HALT.md and exits 0).
  - Three consecutive cycles with zero `kept` candidates (writes STAGNATION.md and exits 0).
  - SIGINT — clean shutdown, finishes current cycle.

**Acceptance.**
- [ ] Without a budget file, `--watch` runs and can be SIGINT'd cleanly mid-cycle.
- [ ] With a tiny budget, exits 0 after halt with the right halt file.
- [ ] Stagnation detection works on a fixture where the plugin always returns 0 candidates.
- [ ] `scripts/test-loop-watch.sh` covers all three exits.

**Anti-features.**
- Does NOT daemonize / fork to background. Foreground process only.

**Files owned.**
- `bin/lib/loop.js` (watch loop)
- `bin/researchloop.js` (flag wiring)
- `scripts/test-loop-watch.sh` (new)

**Depends on.** L2, G67 (budget command, already shipped in issues queue).

---

## Out of scope for M02 (flag as follow-ups, do not expand)

- **Cross-repo archive sharing / team mode.** Belongs to a hosted layer per VISION.md.
- **LLM API calls from inside any plugin.** All plugins are offline-safe in M02. LLM-mediated mutation in P4 is via a prompt-file handoff to the calling agent.
- **Self-modifying loop / meta-search.** A proposer that mutates other proposers is a separate milestone.
- **Real billing integration.** Cost stays as logged `cost_usd` per row (G23 surface).
- **A web UI for editing candidates.** Files first. Dashboard is read-only.

---

## Release gate for M02

M02 ships when:

1. F1, F2, F3, L1, L2, L3, E1, E2 are merged and `npm test` is green.
2. At least **two** proposer plugins (P1 + one other) have green dogfoods (D1 + one of D2/D3/D4).
3. The dashboard loop panel renders.
4. A short demo recording of `loop --watch` on `llm-research-kit` is committed under `assets/demo/M02-loop.cast`.

Everything else (remaining proposers, U3 watch mode, extra dogfoods) is post-gate polish but should land before declaring 0.5.0.
