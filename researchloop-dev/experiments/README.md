# Experiment Protocols

This folder holds local-only ResearchLoop experiment protocols.

These are not normal install tests. They describe real autonomous research runs we want agents to perform safely: bounded wall-clock sprints, adjustable probe budgets, run ledgers, reset proofs, and follow-up reports.

Use `runs/` for the actual ledger and markdown report from each execution.
Each run should also write a self-contained HTML report with the loss graphs.

Use this folder when the question is:

- can the agent run a real research loop?
- can it keep timestamps, metrics, and decisions straight?
- can it explore code changes without polluting the target repo?
- can it reset the workspace completely after the run?

Protocols:

- [LLM Research Kit optimizer sprint](./llm-research-kit-optimizer-sprint.md)

Modules:

- [Timed research sprint module](./protocols/timed-research-sprint-module.md)
- [Protocol index](./protocols/index.md)

Plans:

- [Repeatable research sprint plan](./repeatable-research-sprint-plan.md)
