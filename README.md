# ResearchLoop

ResearchLoop is an open source npm package for autonomous AI research workflows.

If you want the full step-by-step usage and publish guide, read [docs/getting-started.md](./docs/getting-started.md).

It installs a durable research harness into a machine learning repo so agents like Codex, Claude Code, Hermes, Cursor, and similar tools can inspect the code, propose experiments, run small checks, log results, and continue the loop without losing context.

This repo is both the product and the startup home base.

## Install

```bash
npm install -g researchloop
```

Local development from this checkout:

```bash
cd /Users/vukrosic/my-life/researchloop
npm link
researchloop --help
```

## Quick Start

```bash
researchloop init --agent codex
researchloop goal "lower validation loss"
researchloop inspect
researchloop idea --write
researchloop prompt --agent codex
researchloop prompt --agent codex --focus hyperparameters
researchloop dashboard
researchloop doctor
researchloop record --id first-run --status complete --metric val_loss=2.31 --note "First logged experiment"
researchloop compare --metric val_loss --direction lower
researchloop report
```

Then paste the generated prompt into the coding agent.

## What It Creates

```text
.researchloop/
  AGENTS.md
  goal.md
  plan.md
  repo-profile.json
  adapters/
  scratchpad/
    THREAD.md
    runs.jsonl
    ideas/
    papers/
    variants/
    sweeps/
```

The package does not claim to magically train every model. It gives an agent the operating system for serious research: constraints, baseline-first behavior, experiment logs, idea files, and reproducible reports.

## Repo Layout

```text
bin/                  CLI entrypoint
templates/            Harness, adapters, and agent prompts
docs/site/            Landing page
docs/research/        Local testing notes and research logs
docs/competitors/     Competitor and adjacent-project research
docs/testing/         Setup and onboarding test plans
docs/startup/         Users, customers, open source, and go-to-market
examples/             Copyable end-to-end usage examples
examples/fixtures/    Minimal repo fixtures used by setup tests
scripts/              Smoke tests for the npm package
```

## Current Evidence

Tested on this MacBook:

- `researchloop init`, `inspect`, `prompt`, `doctor`, and `report` pass in a clean temp repo.
- `researchloop inspect` correctly detects `llm-research-kit` as `generic`, `pytorch`, `huggingface`, and `llm-research-kit`.
- `researchloop doctor` confirms local torch 2.8.0, CUDA false, MPS true.
- A tiny synthetic LLM training run completed locally through `llm-research-kit` on MPS.

See `docs/research/experiments/macbook-e2e-2026-05-15.md`.

## Product Thesis

Autonomous AI research is bottlenecked less by model access than by research discipline. Most repos lack a stable loop for:

- clear goals
- baselines
- small experiments
- run logs
- comparison
- pruning
- continuation

ResearchLoop packages that loop as an open source npm tool.

## Users

Primary users:

- PhD students running ablations
- small AI labs
- independent AI researchers
- companies with model, prompt, or eval optimization work

The startup plan is in `docs/startup/`.

## Commands

- `researchloop init` creates `.researchloop/` and agent instruction files.
- `researchloop goal` saves a durable research objective in `.researchloop/goal.md`.
- `researchloop inspect` writes `.researchloop/repo-profile.json`.
- `researchloop idea` generates ranked experiment ideas and can write an idea note.
- `researchloop prompt` prints an agent-ready autonomous research prompt, with optional focus playbooks.
- `researchloop dashboard` starts a local localhost dashboard for experiment tracking.
- `researchloop doctor` checks basic local tooling.
- `researchloop record` appends a structured run result to `runs.jsonl`.
- `researchloop compare` ranks runs by a chosen metric.
- `researchloop report` summarizes the run ledger.
- `npm run test:setup` runs the blank-repo and minimal-fixture setup checks.
- `npm run test:compare` checks comparison output for a few recorded runs.
- `npm run test:goal` checks goal saving and prompt handoff.
- `npm run test:idea` checks idea generation for a blank repo and an llm-research-kit-shaped repo.
- `npm run test:dashboard` checks the local dashboard server and API.
- `npm run test:prompts` checks prompt templates for placeholder drift.
- `npm run test:focus-prompts` checks the hyperparameter, architecture, and attention playbooks.
- `npm run test:site` checks the public landing page copy.

## Open Source

ResearchLoop should stay open source at the core. The npm package, prompts, adapters, and run ledger format should be inspectable and forkable.

Possible paid layers later:

- hosted dashboard
- team run history
- managed GPU runners
- private lab templates
- compliance/export support
- priority support for labs and companies
