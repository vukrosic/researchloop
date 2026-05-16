# Repeatable Research Sprint Plan

This plan turns bounded research sprints into a repeatable workflow for testing AutoResearch-AI prompts and agent behavior.

The goal is that Vuk can say:

```text
Run timed experiments on this target: 3 minutes total, 5 seconds per probe.
```

And the agent knows how to:

- choose the right protocol
- choose a reset strategy
- run repeated short probes
- record every timestamp and metric
- save durable results
- reset all local changes
- continue indefinitely across many sessions

## What This Is

This is a local-only control-room workflow.

It is not a normal CI test. It is a repeatable autonomous research run pattern:

```text
target repo + protocol + budget + probe loop + ledger + report + reset proof
```

Use it to test whether agents can do real research work with discipline:

- keep time
- make small code changes
- run actual experiments
- record losses and failures
- preserve useful data
- avoid polluting the research repo
- resume from prior ledgers

## Folder Model

Use `researchloop-dev/experiments/` as the home for this system.

```text
researchloop-dev/experiments/
  README.md
  repeatable-research-sprint-plan.md
  llm-research-kit-optimizer-sprint.md
  protocols/
    index.md
    timed-research-sprint-module.md
  runs/
```

Planned responsibilities:

- `repeatable-research-sprint-plan.md`: this implementation plan.
- `*.md` protocol files: human-readable rules for each experiment type.
- `protocols/`: reusable modules and protocol indexes.
- `runs/`: durable ledgers and reports from actual executions.

## Run Identity

Every sprint gets one stable run id:

```text
<target>-<protocol>-<timestamp>
```

Example:

```text
llm-kit-optimizer-sprint-20260517-052600
```

The run id must be used in:

- disposable worktree path
- status snapshots
- JSONL ledger
- markdown report
- optional transcript

## Core Rules

1. Resolve `sprint_budget` and `probe_budget` from the user request.
2. Always capture live target status before experiments when reset is expected.
3. Default to a disposable worktree for git repos, but allow another reset strategy when the user explicitly chooses it.
4. Always save ledgers outside disposable state.
5. Every probe gets start time, end time, actual duration, status, and notes.
6. Every completed probe gets a metric, or an explicit parse-failure note.
7. Never claim a loss or timing value without command evidence.
8. Stop by wall-clock budget, not by vibes.
9. Delete or remove the sandbox after the sprint.
10. Compare live target status before and after cleanup.
11. Treat non-empty before/after diff as a failed reset proof.
12. Keep failed probes in the ledger; failure is research data.

## Standard Prompt Shape

When Vuk says:

```text
Run five-second optimizer experiments on llm-research-kit for three minutes.
```

The agent should infer:

- target: `/Users/vukrosic/my-life/research-repos/llm-research-kit`
- module: `protocols/timed-research-sprint-module.md`
- protocol: `llm-research-kit-optimizer-sprint.md`
- sprint budget: about 3 minutes wall-clock
- probe budget: about 5 seconds training time
- edit scope: optimizer-related code unless the prompt names another area
- output: JSONL ledger plus markdown report
- reset strategy: default to disposable worktree unless Vuk overrides it

If the user names a different target or budget, the same workflow applies with those values.

## Execution Loop

For each sprint:

1. Read the selected protocol.
2. Capture live target status.
3. Create the reset environment required by the chosen reset strategy.
4. Create the ledger at `researchloop-dev/experiments/runs/<RUN_ID>.jsonl`.
5. Record sprint start timestamp and epoch seconds.
6. Run probes until the wall-clock budget is nearly exhausted.
7. After each probe, append one JSON object to the ledger.
8. After the final probe, write a markdown report.
9. Reset and remove the sandbox.
10. Capture live target status again.
11. Diff before and after status snapshots.
12. Add reset proof to the report.

## Probe Loop

Each probe should be small and intentional.

For a probe:

- make one small change
- run the selected training command
- stop training around `probe_budget`
- evaluate validation loss
- record actual duration
- record changed files and diff summary
- decide whether the next probe should exploit, revert, or branch from the best result

The agent may run slightly over the probe budget because evaluation and cleanup take time. Record the real duration.

## Ledger Schema

Each JSONL line should contain:

```json
{
  "run_id": "llm-kit-optimizer-sprint-20260517-052600",
  "probe_id": "001",
  "protocol": "llm-research-kit-optimizer-sprint",
  "target_repo": "/Users/vukrosic/my-life/research-repos/llm-research-kit",
  "base_commit": "8b9aeb960824ce46950193c5eebd47a3c2eedccf",
  "change_label": "muon_ns_steps_3",
  "sprint_budget_seconds": 180,
  "probe_budget_seconds": 5,
  "start_timestamp": "2026-05-17T05:26:43+08:00",
  "end_timestamp": "2026-05-17T05:26:48+08:00",
  "duration_seconds": 5.119,
  "elapsed_sprint_seconds": 5.119,
  "status": "complete",
  "val_loss": 6.0263,
  "train_loss": 3.4024,
  "notes": "Tiny synthetic MPS probe."
}
```

Required fields:

- `run_id`
- `probe_id`
- `protocol`
- `target_repo`
- `base_commit`
- `sprint_budget_seconds`
- `probe_budget_seconds`
- `change_label`
- `start_timestamp`
- `end_timestamp`
- `duration_seconds`
- `elapsed_sprint_seconds`
- `status`
- `notes`

Required when available:

- `val_loss`
- `train_loss`
- `val_perplexity`
- `changed_files`
- `diff_stat`
- `command`
- `error`

## Report Schema

Each markdown report should include:

- run id
- protocol
- target repo
- base commit
- sprint budget
- probe budget
- actual start and end time
- number of probes attempted
- number of probes completed
- best validation loss
- best probe id
- result table
- notable failures
- reset proof result
- paths to status snapshots
- next recommended protocol or probe family

## Prompt Testing

This workflow doubles as a prompt test.

Each run should answer:

- Did the agent pick the right protocol without extra hand-holding?
- Did it avoid editing the live checkout?
- Did it keep checking wall-clock time?
- Did it record every probe?
- Did it preserve results outside the sandbox?
- Did it clean up the sandbox?
- Did it prove reset with before/after status?
- Did it summarize results accurately?

If the answer is no, update the protocol, prompt, or future CLI behavior.

## CLI Product Direction

The current workflow can be manual, but the product should grow toward first-class commands.

Possible future command:

```bash
autoresearch sprint \
  --protocol llm-kit-optimizer \
  --target /Users/vukrosic/my-life/research-repos/llm-research-kit \
  --budget 3m \
  --probe-budget 5s \
  --agent codex
```

Expected product responsibilities:

- create sandbox
- preserve ledger
- enforce budget checks
- expose current best probe
- run cleanup
- emit reset proof
- produce report

## Milestones

### Milestone 1: Human Protocol

- Keep the existing markdown protocol.
- Add this repeatable workflow plan.
- Store actual run ledgers and reports in `experiments/runs/`.
- Run a few manual sprints to expose missing rules.

### Milestone 2: Protocol Index

- Add a protocol index with stable protocol ids.
- Define target defaults, edit scopes, budgets, and ledger fields.
- Make it easy for an agent to choose the right protocol from a user request.

### Milestone 3: Runner Script

- Add a local-only helper script for sandbox creation and cleanup.
- Keep it out of the npm package until the workflow is proven.
- Use the helper to remove repetitive shell glue from agent runs.

### Milestone 4: Prompt Evaluation

- Save transcripts for selected runs.
- Score each run against prompt-test criteria.
- Update prompts when agents skip timing, ledgers, or reset proofs.

### Milestone 5: Product Command

- Promote the proven behavior into `autoresearch sprint`.
- Add fast smoke tests for sandbox creation, ledger persistence, and reset proof.
- Keep actual expensive or repo-specific experiment runs in the control room.

## Immediate Next Step

The next implementation step is to run the module on the concrete three-minute request:

```text
Run timed sprint on llm-research-kit: 3 minutes total, 5 seconds per probe, optimize validation loss.
```
