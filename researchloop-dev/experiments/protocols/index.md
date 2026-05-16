# Protocol Index

Use this index to map user requests to the right experiment module and protocol.

## Modules

| User Request | Module | Notes |
| --- | --- | --- |
| "run five-second experiments for three minutes" | [timed-research-sprint-module.md](./timed-research-sprint-module.md) | Resolve budgets from the request. |
| "run five-minute, five-second experiments" | [timed-research-sprint-module.md](./timed-research-sprint-module.md) | Same module with `sprint_budget=5m`, `probe_budget=5s`. |
| "keep trying probes and save validation loss" | [timed-research-sprint-module.md](./timed-research-sprint-module.md) | Require timestamped JSONL rows. |
| "test agent reset behavior" | [timed-research-sprint-module.md](./timed-research-sprint-module.md) | Use `worktree` reset strategy by default. |

## Specializations

| Target / Task | Protocol | Module |
| --- | --- | --- |
| `llm-research-kit` optimizer probes | [../llm-research-kit-optimizer-sprint.md](../llm-research-kit-optimizer-sprint.md) | `timed-research-sprint` |

## Default Interpretation

If Vuk says:

```text
Do five-second for three minutes on llm-research-kit.
```

Infer:

- module: `timed-research-sprint`
- protocol: `llm-research-kit-optimizer-sprint.md`
- target: `/Users/vukrosic/my-life/research-repos/llm-research-kit`
- sprint budget: `180s`
- probe budget: `5s`
- metric: `val_loss`
- direction: `lower`
- reset strategy: `worktree`
- result directory: `researchloop-dev/experiments/runs/`
