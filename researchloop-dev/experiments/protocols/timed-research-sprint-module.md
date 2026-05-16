# Timed Research Sprint Module

This is the reusable module for bounded autonomous research experiments.

Use it when the user asks for repeated short probes inside a larger wall-clock budget, for example:

```text
Run 5-second experiments for 3 minutes.
Run optimizer probes for 5 minutes, 10 seconds each.
Run timed validation-loss experiments and save every result.
```

## Parameters

Every run must resolve these parameters before starting:

| Parameter | Meaning | Example |
| --- | --- | --- |
| `target_repo` | Repo or folder to optimize | `/Users/vukrosic/my-life/research-repos/llm-research-kit` |
| `sprint_budget` | Approximate total wall-clock budget | `3m`, `5m`, `30m` |
| `probe_budget` | Approximate per-probe training budget | `5s`, `10s`, `60s` |
| `objective` | What to improve or test | `validation loss` |
| `metric` | Metric to record and compare | `val_loss` |
| `direction` | Whether lower or higher is better | `lower` |
| `edit_scope` | Code or config area to change | `optimizers/` |
| `reset_strategy` | How to clean changes after the run | `worktree`, `clone`, `in_place_snapshot` |
| `ledger_dir` | Where durable results live | `researchloop-dev/experiments/runs/` |
| `agent_model` | Model used to run the sprint | `GPT-5.4 Mini` |

If the user says only "five-second for three minutes," infer:

- `sprint_budget=3m`
- `probe_budget=5s`
- `metric=val_loss`
- `direction=lower`
- target and edit scope from the surrounding request

## Default Reset Strategy

Default to `worktree` when the target is a git repo.

The reason is practical: prompt testing needs proof that the agent can explore code and still return the live checkout to the same status. A disposable worktree gives a clean place to make changes and a simple reset proof.

This is a default, not a law. Other strategies are allowed:

| Strategy | Use When | Reset Proof |
| --- | --- | --- |
| `worktree` | The target is a git repo and may contain valuable local work | before/after live status diff is empty |
| `clone` | Worktree is unavailable or the target repo state should be fully copied | clone directory is deleted and live status is unchanged |
| `in_place_snapshot` | The target is intentionally disposable or user explicitly approves live edits | patch/status snapshot is restored and verified |
| `no_reset` | The user explicitly wants changes to remain | report says reset was skipped by request |

Never run destructive cleanup in a live checkout unless the user explicitly approves that target as disposable.

## Change Strategy

Changes do not have to be tiny.

Default to one clear change per probe because it makes the ledger interpretable, but the agent may make larger changes when the user asks for broader optimization.

Each probe still needs a `change_label` and a short note describing what changed.

Good labels:

- `baseline`
- `muon_ns_steps_3`
- `adamw_beta2_0_95`
- `optimizer_lr_scale_0_7`
- `rewrite_optimizer_step`

## Timing Rules

The sprint is controlled by wall-clock time.

Required timestamps:

- sprint start timestamp
- probe start timestamp
- probe train cutoff timestamp, if training is separately timed
- probe end timestamp
- sprint end timestamp

Required durations:

- probe training duration, if measurable
- probe total duration including evaluation
- elapsed sprint seconds after each probe
- total sprint duration

Stop rule:

- Before starting each probe, compare elapsed sprint time to `sprint_budget`.
- Start another probe only if there is enough time for a useful run.
- A probe may end slightly after the budget; record the real time.
- Once elapsed time is at or above the budget, stop and write the report.

For `sprint_budget=3m` and `probe_budget=5s`, a good practical threshold is:

- continue while elapsed time is below about `170s`
- stop once elapsed time is near or above `180s`
- do not hide overshoot; record it

## Probe Requirements

Every attempted probe must append a ledger row.

A completed probe must record:

- validation loss value
- timestamp of the validation result
- actual duration
- command or script used
- changed files or diff summary

A failed probe must record:

- failure status
- timestamp
- actual duration
- error summary
- whether the failure changed the next probe

Failure rows stay in the ledger. They are useful prompt-test data.

## Ledger Schema

Each line in the JSONL ledger is one probe.

Required fields:

- `run_id`
- `probe_id`
- `module`
- `protocol`
- `target_repo`
- `base_ref`
- `sprint_budget_seconds`
- `probe_budget_seconds`
- `objective`
- `metric`
- `direction`
- `change_label`
- `start_timestamp`
- `end_timestamp`
- `duration_seconds`
- `elapsed_sprint_seconds`
- `status`
- `notes`

Required when available:

- `agent_model`
- `train_cutoff_timestamp`
- `validation_timestamp`
- `val_loss`
- `train_loss`
- `val_perplexity`
- `command`
- `changed_files`
- `diff_stat`
- `error`

Example:

```json
{"run_id":"llm-kit-optimizer-sprint-20260517-060000","probe_id":"001","module":"timed-research-sprint","protocol":"llm-research-kit-optimizer","target_repo":"/Users/vukrosic/my-life/research-repos/llm-research-kit","base_ref":"8b9aeb960824ce46950193c5eebd47a3c2eedccf","sprint_budget_seconds":180,"probe_budget_seconds":5,"objective":"lower validation loss","metric":"val_loss","direction":"lower","change_label":"muon_ns_steps_3","start_timestamp":"2026-05-17T06:00:00+08:00","validation_timestamp":"2026-05-17T06:00:06+08:00","end_timestamp":"2026-05-17T06:00:06+08:00","duration_seconds":6.1,"elapsed_sprint_seconds":6.1,"status":"complete","val_loss":6.02,"train_loss":3.40,"notes":"5-second MPS synthetic probe."}
```

## Report Requirements

Every sprint writes a markdown report next to the ledger.

The report must include:

- resolved parameters
- actual sprint start and end timestamps
- actual total duration
- number of probes attempted
- number of probes completed
- agent model used
- best metric value
- best probe id
- result table with validation timestamp and validation loss
- failed probes
- reset strategy
- reset proof
- paths to ledger and status snapshots
- recommended next run

Two HTML-report rules:

1. Always write a self-contained HTML report next to the markdown report.
2. The HTML report must visually explain what happened and include both the validation-loss-over-time graph and the running-minimum-loss-over-time graph.

The HTML report should stay readable without extra tooling or a notebook. A static browser-openable file is enough.

## Prompt-Test Checklist

After every sprint, score the agent behavior:

- Did it infer or ask for missing parameters?
- Did it preserve timestamps for every probe?
- Did every validation loss have evidence?
- Did it stop around the sprint budget?
- Did it save ledger and report outside disposable state?
- Did it reset or intentionally skip reset according to strategy?
- Did it explain results without overstating them?

## Minimal User Command

For the next concrete run, this should be enough:

```text
Run timed sprint on llm-research-kit: 3 minutes total, 5 seconds per probe, optimize validation loss.
```

The agent should resolve that into:

- module: `timed-research-sprint`
- protocol: `llm-research-kit-optimizer-sprint.md`, treated as an optimizer specialization
- sprint budget: `180s`
- probe budget: `5s`
- metric: `val_loss`
- reset strategy: `worktree` unless Vuk overrides it
