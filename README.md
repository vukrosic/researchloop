<p align="center">
  <img src="./assets/researchloop-banner.webp" alt="ResearchLoop banner" width="100%" />
</p>

ResearchLoop is an open source npm package for autonomous AI research workflows.

If you want the full step-by-step usage and publish guide, read [docs/getting-started.md](./docs/getting-started.md).

It installs a durable research harness into a machine learning repo so agents like Codex, Claude Code, Hermes, Cursor, and similar tools can inspect the code, propose experiments, run small checks, log results, and continue the loop without losing context.

## Give This Prompt To Your Agent

Copy this into Codex, Claude Code, Hermes, Cursor, or another coding agent:

```text
Run npm install -g researchloop, then read the docs and propose an autonomous research plan.
```

---

Manual Installation:

```bash
npm install -g researchloop
```

Local development from this checkout:

```bash
git clone https://github.com/vukrosic/researchloop.git
cd researchloop
npm link
researchloop --help
```

## Quick Start

```bash
researchloop init --agent codex
researchloop goal "lower validation loss" --metric val_loss --direction lower \
  --baseline "python train.py" --evaluation "python eval.py"
researchloop inspect
researchloop scan-papers --limit 10
researchloop idea --write
researchloop prompt --agent codex
researchloop team --workers 8
researchloop baseline
researchloop run --id lr-3e-4 --command "python train.py --lr 3e-4"
researchloop compare --metric val_loss --direction lower
researchloop report
researchloop dashboard
researchloop doctor
```

Then paste the generated prompt into the coding agent.

## What It Creates

```text
.researchloop/
  AGENTS.md
  goal.md
  plan.md
  repo-profile.json
  team/
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
skills/               Downloadable agent research skill packs
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
- `researchloop scan-papers` fetches relevant arXiv abstracts into `.researchloop/scratchpad/papers/`.
- `researchloop idea` opens a chat-first research prompt that reads the repo history, asks for the time budget if needed, and can write the prompt into an idea note.
- `researchloop prompt` prints an agent-ready autonomous research prompt, with optional focus playbooks.
- `researchloop team` generates a local multi-agent development board for the ResearchLoop repo or another project.
- `researchloop baseline` runs the baseline command, parses the metric, and locks it into `goal.md` and `plan.md`.
- `researchloop run` executes a training or eval command, streams the log, parses the metric, and records the run.
- `researchloop record` appends a structured run result to `runs.jsonl` (use for manual rows).
- `researchloop compare` ranks runs by a chosen metric.
- `researchloop report` summarizes the run ledger.
- `researchloop dashboard` starts a local localhost dashboard for experiment tracking.
- `researchloop doctor` checks basic local tooling.
- `npm test` runs every fast check below in sequence. CI runs this on Node 18 / 20 / 22 against ubuntu and macos for every push and PR.
- `npm run test:release` adds the packed-tarball install check on top of `npm test`. Run this before publishing.
- `npm run test:setup` runs the blank-repo and minimal-fixture setup checks.
- `npm run test:compare` checks comparison output for a few recorded runs.
- `npm run test:run` checks `run` and `baseline` against deterministic shell commands, including a noisy-log case.
- `npm run test:scan-papers` checks the arXiv scan path against a recorded XML fixture (no network).
- `npm run test:goal` checks goal saving and prompt handoff.
- `npm run test:idea` checks the chat-first idea prompt for a blank repo, an llm-research-kit-shaped repo, and a paper-augmented repo.
- `npm run test:team` checks the multi-agent development board and worker files.
- `npm run test:dashboard` checks the local dashboard server and API.
- `npm run test:prompts` checks prompt templates for placeholder drift.
- `npm run test:focus-prompts` checks the hyperparameter, architecture, and attention playbooks.
- `npm run test:site` checks the public landing page copy (reads the file directly; no server needed).
- `npm run test:adapters` checks repo-shape adapter detection against negative cases.
- `npm run test:packed` packs the tarball, installs into an isolated npm prefix, and runs the harness end-to-end.

## Open Source

ResearchLoop should stay open source at the core. The npm package, prompts, adapters, and run ledger format should be inspectable and forkable.

The package also ships optional skill packs under `skills/` so teams can copy the same research rules into Codex, Claude Code, or other agent-specific folders.

Possible paid layers later:

- hosted dashboard
- team run history
- managed GPU runners
- private lab templates
- compliance/export support
- priority support for labs and companies
