# ResearchLoop — Improvement Goals

Scoping document for the next functionality push. Each goal is sized to be picked up by **one independent AI agent**, with no shared in-flight state required between agents beyond the files in the repo.

Conventions used in this doc:

- **Goal ID** is `G##`. Other goals reference it by ID.
- **Acceptance** lines are written so a reviewer can mechanically check them — every line is either a file/command that must exist or a measurable behavior.
- **Test plan** lines are concrete bash commands or assertions a reviewer (or the agent itself) runs after the goal is "done".
- **Effort**: S = < 1 day, M = 1–3 days, L = > 3 days.
- **Depends on** lists hard prerequisites only. Soft synergies are noted in prose.

Themes:

1. **Ideation & planning** — G01–G03
2. **Evaluation layer** — G04–G06
3. **Execution & sweeps** — G07–G10
4. **Failure handling** — G11–G12
5. **Storage & query** — G13–G14
6. **Dashboard & UI** — G15–G17
7. **Orchestration & multi-agent** — G18–G19
8. **Reporting & claims** — G20–G21
9. **Integrations & ops** — G22–G24
10. **Safety & cost** — G25

The current shipped surface (do not re-do): `init`, `goal`, `inspect`, `scan-papers`, `idea`, `prompt`, `team`, `baseline`, `run`, `record`, `compare`, `report`, `dashboard` (static), `doctor`. The static dashboard exposes `/api/state`, `/api/runs`, `/api/goal`. Skill packs under `skills/researchloop-autoresearch/*` are reference docs, not executed code.

---

## Theme 1 — Ideation & planning

### G01 — `researchloop propose`: concrete experiment plans from goal + repo

**Motivation.** Today `researchloop idea` prints a chat prompt for an agent. There is no command that *itself* writes a structured, ranked list of concrete experiments to disk. Autonomous agents need a machine-readable starting backlog.

**Deliverables.**
- New subcommand `researchloop propose [--n 10] [--write] [--focus hyperparameters|architecture|attention|data]`.
- Output file `.researchloop/scratchpad/proposals.jsonl` — one JSON object per proposal with keys: `id`, `title`, `hypothesis`, `change` (config / code diff sketch), `metric`, `expected_direction`, `estimated_minutes`, `est_cost_usd_or_null`, `risk` ∈ {low, med, high}, `priors` (array of paper/run refs), `created_at`.
- The proposer reads `goal.md`, `repo-profile.json`, `runs.jsonl`, and any `scratchpad/papers/*.md` notes.

**Acceptance.**
- Running `researchloop propose --n 5 --write` in a fixture repo with no prior runs produces 5 valid JSONL rows, each with all required keys, and at least one proposal whose `change` references a real file in the fixture.
- Re-running does **not** duplicate `id`s; ids are content-hashed.
- `proposals.jsonl` is valid newline-delimited JSON (each line parses independently).

**Test plan.**
- `scripts/test-propose.sh` — runs in a temp dir from `examples/fixtures/minimal/`, asserts row count, schema, and id-stability across two runs.
- Add to `npm test` aggregate.

**Depends on.** None.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G02 — Idea/proposal ranking with explainable score

**Motivation.** A backlog without a priority order means agents pick the wrong experiment first. Ranking should be reproducible and explainable, not an opaque LLM judgment.

**Deliverables.**
- `researchloop rank [--input proposals.jsonl] [--write]`.
- Adds two columns to each proposal: `score` (float 0–1) and `score_breakdown` (object with `impact`, `cost`, `risk`, `novelty_vs_runs`, each 0–1 plus a one-line `why`).
- Sort order: descending `score`.
- Writes `.researchloop/scratchpad/ranked-proposals.jsonl` and a `ranked-proposals.md` human view.

**Acceptance.**
- Given a fixed input file, ranking is deterministic across two invocations on the same machine.
- A proposal that duplicates the goal's already-best run in `runs.jsonl` receives `novelty_vs_runs <= 0.2`.
- `score_breakdown.why` is non-empty for every proposal.

**Test plan.**
- `scripts/test-rank.sh` runs against a frozen `proposals.jsonl` fixture committed under `examples/fixtures/proposals/`. Asserts ordering and field presence.

**Depends on.** G01.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

### G03 — Prior-art lookup per proposal

**Motivation.** `scan-papers` runs once at the goal level. We need a per-proposal arXiv + GitHub-style search to attach priors to each idea before an agent commits to running it.

**Deliverables.**
- `researchloop priors --proposal <id> [--limit 5]` — appends a `priors` array to that proposal's row and writes per-paper notes under `scratchpad/papers/` if missing.
- Reuses the existing arXiv fetch path; falls back gracefully when offline (uses cached XML).

**Acceptance.**
- For a proposal mentioning "learning rate warmup", at least one returned prior contains the substring "warmup" in title or abstract.
- Re-running with the same `--proposal` does not duplicate `priors` entries (deduped by arXiv id).
- Offline mode (`RESEARCHLOOP_OFFLINE=1`) succeeds when a recorded XML fixture exists, fails clearly otherwise.

**Test plan.**
- Extend `test-scan-papers.sh` to drive a `priors` lookup against the existing XML fixture; assert dedup on re-run.

**Depends on.** G01.
**Effort.** S. **Agent role.** Worker — CLI feature.

---

## Theme 2 — Evaluation layer

### G04 — Pluggable evaluation runner with multi-metric support

**Motivation.** Today `goal.md` pins a single primary metric (e.g. `val_loss`) parsed via regex from training stdout. Real research tracks several metrics and runs eval scripts separately. We need a structured eval contract.

**Deliverables.**
- File `.researchloop/eval.yaml` (or `.json`) declaring: `metrics` (list of `{name, direction, regex_or_jsonpath, source: stdout|file}`), `eval_command`, optional `gates`.
- `researchloop eval [--run-id ID] [--command CMD]` — runs the eval command, parses *all* declared metrics, appends them to the matching row in `runs.jsonl` under a `metrics` object.
- `researchloop run` automatically calls `eval` post-train if `eval.yaml` exists and `gates.run_eval_after_train: true`.

**Acceptance.**
- A run row in `runs.jsonl` after `researchloop run` + auto-eval contains `metrics.val_loss`, `metrics.val_acc`, and any user-declared metric, each with numeric values.
- If a metric regex does not match, that metric's value is `null` and `runs.jsonl` records a `parse_warnings` array on the row — the command does not crash.
- `researchloop compare --metric val_acc --direction higher` works on rows produced this way.

**Test plan.**
- `scripts/test-eval.sh` uses a deterministic shell script that prints fake `val_loss=0.42` and writes `eval.json` with `val_acc=0.91`. Assert both metrics land on the row.
- Negative case: missing regex match yields `null` and a warning, exit 0.

**Depends on.** None (touches `run` and `record` paths but does not require G01).
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G05 — Promotion gates: keep / discard runs by rule

**Motivation.** Right now every run is equal in the ledger. Agents need to know "this beat the bar, promote it" vs "this is below baseline, archive it" without human review.

**Deliverables.**
- `gates` section in `eval.yaml`: list of rules like `{metric: val_loss, op: "<", value: "{baseline}-0.02"}`.
- After `researchloop eval`, each run row gets `status` ∈ {`promoted`, `kept`, `discarded`} and `gate_reasons` (array).
- `researchloop promote <run-id>` manually flips a row to `promoted` and copies its config + diff snapshot into `.researchloop/winners/<run-id>/`.

**Acceptance.**
- A run that beats baseline by the configured delta auto-flips to `promoted`.
- A run with `val_loss` worse than baseline auto-flips to `discarded` with at least one `gate_reasons` entry.
- `winners/<run-id>/` after promotion contains at minimum `goal.md` snapshot, the row JSON, and a `command.txt`.

**Test plan.**
- `scripts/test-gates.sh` — three deterministic runs: one above bar, one below, one borderline; assert correct `status` for each.

**Depends on.** G04.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

### G06 — Train/val curve capture

**Motivation.** A single end-of-run metric is not enough to debug or compare. We need per-step curves stored in a structured format that the dashboard can plot.

**Deliverables.**
- During `researchloop run`, parse lines matching declared curve regexes (e.g. `^step=(\d+) train_loss=([\d.eE+-]+) val_loss=([\d.eE+-]+)`) and append each point to `.researchloop/scratchpad/curves/<run-id>.jsonl`.
- Curve regex declared in `eval.yaml` under `curves: [{name, regex, fields: [step, train_loss, val_loss]}]`.
- New API endpoint `/api/curves?run=<id>` on the dashboard returns the parsed series.

**Acceptance.**
- Given a deterministic training script that prints 50 step lines, the corresponding `curves/<run-id>.jsonl` has exactly 50 rows with monotonic `step`.
- `/api/curves?run=<id>` returns a JSON array of the same length.
- Curves persist across CLI process restarts (they are flushed per-step, not at end).

**Test plan.**
- `scripts/test-curves.sh` — deterministic script emitting 50 step lines; assert row count, schema, and that the dashboard endpoint returns the array.

**Depends on.** G04 (uses `eval.yaml`).
**Effort.** M. **Agent role.** Worker — CLI feature.

---

## Theme 3 — Execution & sweeps

### G07 — Sweep generator (grid / random / list)

**Motivation.** Agents hand-write `--lr 1e-3`, `--lr 3e-3` runs one at a time. A sweep spec turns one declarative file into a queue of concrete runs.

**Deliverables.**
- File `.researchloop/sweeps/<name>.yaml` with shape:
  ```yaml
  base_command: "python train.py"
  strategy: grid  # grid | random | list
  budget: 12      # max runs (random) or hard cap (grid)
  params:
    lr: {type: log_uniform, min: 1e-5, max: 1e-2}
    batch_size: {type: choice, values: [32, 64, 128]}
  ```
- `researchloop sweep generate <name>` — emits `.researchloop/sweeps/<name>.queue.jsonl`, one row per planned run with the resolved command, id, and param dict.
- `researchloop sweep status <name>` — counts queued / running / done / failed by joining queue against `runs.jsonl`.

**Acceptance.**
- A grid sweep with `lr ∈ {1e-4, 1e-3}` and `batch_size ∈ {32, 64}` produces exactly 4 unique rows with stable ids.
- A random sweep with `budget=10` produces 10 rows; re-running with the same `seed` field produces identical rows.
- Queue file is valid JSONL.

**Test plan.**
- `scripts/test-sweep.sh` covers grid, random+seed, and list strategies against committed spec fixtures.

**Depends on.** None.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G08 — Parallel run scheduler

**Motivation.** A queue with no runner is useless. We need a worker that consumes the queue and executes runs with bounded concurrency.

**Deliverables.**
- `researchloop sweep run <name> [--workers N] [--max-failures K]`.
- Workers are Node child processes. Each claims one queue row by writing a `claimed_by` field, runs the command, parses metrics via the existing pipeline, marks the row `done` or `failed`.
- Claims are made atomically by writing to `.researchloop/sweeps/<name>.lock/<row-id>` files (filesystem-level mutex, no external dep).
- Live progress to stdout: `[3/12] lr=3e-4 batch=64 -> val_loss=0.41 (28s)`.

**Acceptance.**
- A 12-row queue runs to completion under `--workers 4` with no double-claims (each row appears exactly once in `runs.jsonl`).
- Killing the runner mid-sweep (SIGINT) leaves claim files such that a re-run resumes only the unfinished rows.
- `--max-failures 2` stops the sweep after the second failure.

**Test plan.**
- `scripts/test-sweep-run.sh` — queue of 6 deterministic shell commands, 2 of which exit non-zero. Assert ledger has 6 rows, 4 success / 2 failure, and that a follow-up `sweep run` is a no-op.

**Depends on.** G07.
**Effort.** M–L. **Agent role.** Worker — CLI feature.

---

### G09 — Checkpoint capture and `researchloop resume`

**Motivation.** Long runs crash. We currently lose all in-flight state. The CLI should be able to resume a partial run from its last checkpoint.

**Deliverables.**
- Declared in `eval.yaml`: `checkpoint_glob: "checkpoints/*.pt"` and `resume_flag_template: "--resume {path}"`.
- During `run`, the CLI records the newest matching checkpoint path on each successful step into the run row's `last_checkpoint`.
- `researchloop resume <run-id>` re-launches the original command with the resume flag appended.

**Acceptance.**
- After a 50-step run that writes `checkpoints/step_50.pt`, the run row in `runs.jsonl` has `last_checkpoint` ending in `step_50.pt`.
- `researchloop resume <run-id>` prints the exact command it will execute, including the resume flag; with `--dry-run` it does not execute.
- If no checkpoint exists, `resume` exits non-zero with a clear error.

**Test plan.**
- `scripts/test-resume.sh` — script `touch`es checkpoint files mid-run; assert `last_checkpoint` and `--dry-run` output.

**Depends on.** G04.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

### G10 — Replay and reproducibility diff

**Motivation.** A run's value depends on whether the result is reproducible. Agents need a one-shot to verify.

**Deliverables.**
- `researchloop replay <run-id> [--n 1] [--tolerance 0.01]`.
- Re-executes the stored command, captures fresh metrics, writes them as a new row tagged `replay_of: <run-id>`, and prints a diff table.
- Exits non-zero if any primary metric differs by more than `--tolerance` (absolute or relative — declared per metric in `eval.yaml`).

**Acceptance.**
- Replaying a deterministic command yields the same metrics; the command exits 0.
- Replaying a deliberately non-deterministic command (random seed not fixed) reports a non-zero diff and exits non-zero.
- Replay rows carry both `replay_of` and a fresh `id`.

**Test plan.**
- `scripts/test-replay.sh` — deterministic and non-deterministic fixtures; assert exit codes and diff output.

**Depends on.** G04. (Listed in current ROADMAP as `replay <run-id>`; this goal is the formal spec.)
**Effort.** S. **Agent role.** Worker — CLI feature.

---

## Theme 4 — Failure handling

### G11 — NaN / divergence early-stop

**Motivation.** A diverged run wastes hours of compute. The runner should kill it as soon as it can prove it has diverged.

**Deliverables.**
- `eval.yaml` section: `early_stop: [{metric: train_loss, rule: "nan_or_inf", action: kill}, {metric: val_loss, rule: ">10x_baseline_after_step_500", action: kill}]`.
- `researchloop run` evaluates rules after each parsed curve point; on trigger sends SIGTERM, waits, sends SIGKILL, records `status: "killed_by_rule"` and `kill_reason` on the row.

**Acceptance.**
- A training fixture that prints `train_loss=nan` at step 5 is killed within 2s and the row carries `kill_reason: "nan_or_inf train_loss"`.
- A normal run is not affected.

**Test plan.**
- `scripts/test-early-stop.sh` covers the NaN case, the diverged-vs-baseline case, and a normal control.

**Depends on.** G04 + G06.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

### G12 — OOM / hardware retry policy

**Motivation.** OOM and CUDA errors are routine; agents shouldn't manually halve batch size every time.

**Deliverables.**
- `eval.yaml` section: `retry: [{match: "CUDA out of memory|RuntimeError: out of memory", transform: "halve:batch_size", max_retries: 2}]`.
- On match in stderr, the runner mutates the command per the transform and re-runs, recording each attempt as a new row with `retry_of: <original-id>`.

**Acceptance.**
- A fixture command that prints "CUDA out of memory" on first invocation but succeeds on second (driven by an attempt counter file) produces exactly two rows: one failed with `retry_reason`, one succeeded with `retry_of`.
- `max_retries: 0` disables retries.

**Test plan.**
- `scripts/test-retry.sh` with the attempt-counter fixture.

**Depends on.** G04.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

## Theme 5 — Storage & query

### G13 — `researchloop query` over runs.jsonl

**Motivation.** `compare` and `report` are fixed views. Agents need ad-hoc filters: "show all runs where lr > 1e-3 AND val_loss < 0.5 sorted by val_acc desc".

**Deliverables.**
- `researchloop query "<expression>" [--format jsonl|table]`.
- Expression grammar: `where <predicate> [and <predicate>...] sort-by <metric> [asc|desc] limit <n>`.
- Predicates support `=`, `!=`, `<`, `<=`, `>`, `>=`, `contains`, `between a..b` on any field in a row including nested `metrics.*` and `params.*`.

**Acceptance.**
- `researchloop query "where metrics.val_loss < 0.5 sort-by metrics.val_loss asc limit 3"` returns 0–3 rows in valid JSONL.
- Invalid syntax produces a clear one-line error and exits non-zero.
- Empty result set exits 0 with no output (table format prints an empty header row).

**Test plan.**
- `scripts/test-query.sh` against a frozen `runs.jsonl` fixture; cover positive match, no match, syntax error, nested field, limit.

**Depends on.** None (works against the existing ledger; works *better* with G04 metrics).
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G14 — Environment capture per run

**Motivation.** "Reproducible" is a lie without recording git SHA, Python, Torch, GPU, OS, CUDA driver. Today none of this is captured.

**Deliverables.**
- During `run`, capture: git SHA + dirty flag, `python --version`, `pip freeze` hash (sha256 over sorted lines), `torch.__version__`, `cuda` available + version, GPU device names, OS string, hostname.
- Stored under the row's `env` object.
- `doctor` and `replay` consume `env` to warn on mismatches.

**Acceptance.**
- A row in `runs.jsonl` after a real run contains an `env` object with all listed keys; unavailable fields are explicit `null`, not missing.
- `replay` warns (non-fatal) when current `env.git_sha` differs from the stored `env.git_sha`.

**Test plan.**
- `scripts/test-env.sh` runs a no-op command in a temp git repo and asserts the `env` object schema.
- Mutates the repo (dirty working tree) and asserts `git_dirty: true`.

**Depends on.** None. Pairs with G10.
**Effort.** S. **Agent role.** Worker — CLI feature.

---

## Theme 6 — Dashboard & UI

### G15 — Live charts on the dashboard

**Motivation.** The current dashboard is a static HTML page that polls JSON. It does not plot. Agents and humans need at minimum a metric-over-runs scatter and a per-run loss curve.

**Deliverables.**
- Add two charts to `templates/dashboard/index.html`:
  1. **Run scatter** — x-axis = run index (chronological), y-axis = primary metric, color = `status`.
  2. **Curve overlay** — per-run loss curves from `/api/curves`, multi-select up to 5 runs.
- No external CDN dependency at install time — vendor a small chart lib (or hand-rolled SVG) into `templates/dashboard/`.
- Auto-refresh every 5s while charts are visible.

**Acceptance.**
- With 6 rows in `runs.jsonl` (3 done, 2 failed, 1 running), the scatter shows 6 dots in 3 colors.
- Selecting 2 runs in the curve overlay renders 2 lines; selecting "none" shows an empty plot, not an error.
- The dashboard works fully offline (no network requests after page load).

**Test plan.**
- `scripts/test-dashboard.sh` extended: spin up the server, fetch `/`, assert the chart container IDs are present and the vendored asset is shipped in the npm tarball.
- Manual: open `http://127.0.0.1:8787` against a seeded fixture and screenshot.

**Depends on.** G06 (curves endpoint) for the second chart; first chart can ship without G06.
**Effort.** M. **Agent role.** Worker — frontend.

---

### G16 — Run-diff view

**Motivation.** "Why did run B beat run A?" needs a side-by-side of config + metrics + env + curve.

**Deliverables.**
- Dashboard route `/diff?a=<id>&b=<id>` rendering a two-column table: params, metrics, env, with cells highlighted where values differ.
- JSON endpoint `/api/diff?a=<id>&b=<id>` returning `{shared, only_in_a, only_in_b, differences: [{path, a, b}]}`.

**Acceptance.**
- Diffing a run against itself returns `differences: []`.
- Diffing two runs that only differ in `params.lr` returns exactly one differences row with path `params.lr`.
- 404 for unknown run ids.

**Test plan.**
- Extend `test-dashboard.sh` with three HTTP cases.

**Depends on.** G14 for env diff to be meaningful; G15 visual layer.
**Effort.** S–M. **Agent role.** Worker — frontend.

---

### G17 — Experiment lineage view

**Motivation.** Runs branch — a promoted run is the parent of next-iteration runs. Today this lineage is invisible.

**Deliverables.**
- Each run row gains an optional `parent_id` (auto-set by `replay`, `resume`, and by `propose` when a proposal references a prior run; otherwise `null`).
- Dashboard route `/lineage` renders a simple tree (indented list is acceptable; SVG tree is bonus).
- API: `/api/lineage` returns `{roots: [{id, children: [...]}]}`.

**Acceptance.**
- A ledger with one root and two children renders one tree of depth 2.
- Orphans (no parent, no children) appear as their own one-node trees.
- The API output is stable across requests for a fixed ledger.

**Test plan.**
- `scripts/test-lineage.sh` seeds a frozen ledger, hits the API, asserts tree shape.

**Depends on.** G10 and G09 (which populate `parent_id`).
**Effort.** S. **Agent role.** Worker — frontend.

---

## Theme 7 — Orchestration & multi-agent

### G18 — Worker daemon: agents pull from a shared task queue

**Motivation.** Multi-agent today is a static markdown board. We need a real queue that multiple agent processes can claim from without stepping on each other.

**Deliverables.**
- `researchloop tasks add <description> [--lane worker|reviewer|orchestrator] [--depends <task-id>]` writes to `.researchloop/tasks.jsonl`.
- `researchloop tasks claim --agent <name> --lane <lane>` atomically claims the next unblocked task and prints it as JSON. Claim semantics use the same filesystem-mutex pattern as G08.
- `researchloop tasks done <task-id> [--note "..."]` marks a task done.
- `researchloop tasks status` prints the board (queued / claimed / done) grouped by lane.

**Acceptance.**
- Two simultaneous `claim` invocations against a single-task queue: exactly one wins, the other returns `no-task`.
- A task with an unmet dependency is not claimable.
- The board view shows all three lanes and per-lane counts.

**Test plan.**
- `scripts/test-tasks.sh` spawns two background `claim` calls and asserts the win/no-task pattern; covers deps and done.

**Depends on.** None. Replaces the static `team` board over time but does not delete it.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G19 — Auto-reviewer gate before promotion

**Motivation.** The reviewer lane today is a markdown brief. We want an automated review step a winning run must pass before `promote` succeeds.

**Deliverables.**
- `researchloop review <run-id>` runs configured checks declared in `.researchloop/review.yaml`:
  - All declared metrics present and finite.
  - Env captured (G14) and `git_dirty: false`.
  - Curve length ≥ minimum (G06).
  - Replay within tolerance (G10) — opt-in via flag, since it spends compute.
- Outputs a markdown report `winners/<run-id>/review.md` and exits non-zero on failure.
- `promote` is blocked unless `review` has succeeded for the run.

**Acceptance.**
- A run with a dirty git tree fails review with a clear reason.
- A run that passes all checks gets a green `review.md` and is promotable.
- `promote --skip-review` is the only way to bypass and emits a loud warning.

**Test plan.**
- `scripts/test-review.sh` covers pass case, dirty-tree fail case, missing-metric fail case.

**Depends on.** G05, G06, G14. Optional G10.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

## Theme 8 — Reporting & claims

### G20 — Auto-generated experiment report

**Motivation.** A scientist's deliverable is a report, not a JSONL. We should be able to render the current state of the loop into a paper-shaped markdown.

**Deliverables.**
- `researchloop report --format markdown --out report.md [--include-plots]`.
- Sections: Goal, Baseline, Best run, Sweep summary, Loss curves (referencing SVGs written to `report-assets/`), Discarded results, Open questions.
- Plots are simple SVGs written via the same code path as G15's charts (no Python, no extra dep).

**Acceptance.**
- Running on a populated ledger produces a `report.md` ≥ 50 lines with every section header present.
- All claims about runs in the report reference a real run id present in the ledger.
- `--include-plots` writes at least one SVG into `report-assets/`.

**Test plan.**
- `scripts/test-report.sh` against a frozen ledger; assert section headers, run-id references, SVG file count.

**Depends on.** G04 for richer metrics; otherwise none.
**Effort.** M. **Agent role.** Worker — CLI feature.

---

### G21 — Claim audit

**Motivation.** Agent-written reports often hallucinate gains. Every numeric claim should resolve to a ledger row.

**Deliverables.**
- `researchloop audit <file.md>` scans the file for patterns like `\b(\d+\.\d+|\d+%)\b` near keywords (loss, accuracy, perplexity, F1) and tries to match each to a ledger row's metric within tolerance.
- Output: a markdown table of `claim_line, claim_value, matched_run_id_or_null`. Exits non-zero if any claim is unmatched.

**Acceptance.**
- A report that says "val_loss=0.42 on run lr-3e-4" with a matching ledger row passes audit.
- The same report with a fabricated 0.31 fails audit with one unmatched claim.

**Test plan.**
- `scripts/test-audit.sh` covers both cases.

**Depends on.** G20. The existing skill pack `claim-audit/SKILL.md` is the spec source for tolerances.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

## Theme 9 — Integrations & ops

### G22 — Optional Weights & Biases / MLflow export

**Motivation.** Many users already have a tracker. Don't force them off it; offer one-way export.

**Deliverables.**
- `researchloop export --to wandb [--project X]` and `--to mlflow [--uri ...]`.
- Each row in `runs.jsonl` becomes one external run; metrics, params, env, curves all pushed. Idempotent — re-running does not duplicate.
- Both integrations are *optional* runtime imports — the CLI does not list them as deps.

**Acceptance.**
- Without `wandb` installed, the command prints a clear "install with `pip install wandb`" message and exits non-zero.
- With it installed and `WANDB_API_KEY` set, a 3-row ledger pushes 3 W&B runs; a second invocation pushes 0 new runs.

**Test plan.**
- Mocked: a fake `wandb` python module that records calls to a temp file; assert call counts.

**Depends on.** G04, G06, G14.
**Effort.** M. **Agent role.** Worker — integrations.

---

### G23 — Cost and wall-clock accounting

**Motivation.** "What did this experiment cost?" should be answerable. Today we have no time recorded per run.

**Deliverables.**
- During `run`, record `started_at`, `ended_at`, `wall_seconds`.
- Optional `.researchloop/cost.yaml`: `gpu: H100, hourly_usd: 2.50` — multiplied by `wall_seconds / 3600` to populate `est_cost_usd` per row.
- `researchloop report` adds a "Cost" row to the per-run section.

**Acceptance.**
- Every new run row carries `wall_seconds`.
- With `cost.yaml` present, `est_cost_usd` is non-null and equals `wall_seconds / 3600 * hourly_usd` to 4 decimal places.
- Without `cost.yaml`, `est_cost_usd` is `null` and no error is raised.

**Test plan.**
- `scripts/test-cost.sh` with a 2-second deterministic run; assert wall time bounds and cost arithmetic.

**Depends on.** None.
**Effort.** S. **Agent role.** Worker — CLI feature.

---

### G24 — Slack / webhook notifications

**Motivation.** A long sweep finishing while you're at lunch is invisible. A webhook fixes that.

**Deliverables.**
- `.researchloop/notify.yaml`: `webhooks: [{url: ..., events: [run_done, run_failed, sweep_done, promotion]}]`.
- Posts a JSON body per event; payload includes `event`, `run_id`, `metrics`, `goal`, `link` (to local dashboard if reachable).

**Acceptance.**
- A test webhook (local netcat or a fixture HTTP receiver) receives exactly one payload per matching event.
- Webhook failure does not crash the CLI; it logs to stderr and continues.

**Test plan.**
- `scripts/test-notify.sh` spins up a Node HTTP server, runs an event-emitting flow, asserts the bodies received.

**Depends on.** None.
**Effort.** S. **Agent role.** Worker — integrations.

---

## Theme 10 — Safety & cost

### G25 — Agent command sandbox / allowlist

**Motivation.** An autonomous agent will eventually run `rm -rf` or download a 200GB checkpoint. We need a guardrail.

**Deliverables.**
- `.researchloop/safety.yaml`: `allow_prefixes: ["python train.py", "python eval.py", "bash scripts/"]`, `deny_substrings: ["rm -rf", "sudo", "curl |", "wget |"]`, `max_minutes_per_run: 240`, `max_cost_usd_per_run: 5.00`.
- All commands invoked by `run`, `baseline`, `sweep run`, `replay`, `resume` are checked against the policy first.
- Violations exit non-zero with the rule that fired; `--allow-unsafe` is the only way to bypass and emits a loud warning.

**Acceptance.**
- `researchloop run --command "rm -rf /tmp/foo"` is blocked by default with a clear error.
- `researchloop run --command "python train.py"` is allowed.
- `max_minutes_per_run: 1` kills a 3-minute fixture run at ~60s with `status: "killed_by_safety"`.

**Test plan.**
- `scripts/test-safety.sh` covers deny substring, missing prefix, time cap, `--allow-unsafe` bypass.

**Depends on.** None. Should be implemented *early* if any goal in Themes 3 or 7 is shipped — they all execute attacker-controlled strings.
**Effort.** S–M. **Agent role.** Worker — CLI feature.

---

## Cross-cutting suggestions for whichever agent picks up the first goal

- **Do not break existing tests.** Every goal here must keep `npm test` green. New tests under `scripts/test-*.sh` should be added to the aggregate in `package.json` and to the matrix expected by CI.
- **No new runtime dependencies** unless the goal genuinely cannot be done with stdlib Node. The package is currently zero-dep and that is a feature.
- **Keep file formats simple.** Prefer JSONL + YAML/JSON config over invented binary or database formats. SQLite is acceptable only inside `dashboard` if read-only views become unwieldy.
- **Every goal adds at least one test file under `scripts/`** matching the existing bash-integration-test style. Do not introduce a new test framework.
- **Update `docs/getting-started.md` and the relevant skill pack under `skills/researchloop-autoresearch/`** when shipping a new command. The skill pack is the spec; the CLI is the execution.

---

## Sequencing recommendation (not prescriptive)

If we had four agents starting today, a sensible parallel cut:

| Agent | First goal | Reason |
|---|---|---|
| A | G04 (eval layer) | Unblocks G05, G06, G09, G10, G11, G14 |
| B | G07 (sweep gen) | No deps; G08 follows |
| C | G15 (live charts) | Independent surface; users see value immediately |
| D | G25 (safety) | Should land before any sweep/runner ships in the wild |

Once those four are in, Theme 1 (G01–G03) and Theme 8 (G20–G21) can land in parallel.
