# Vision

## The problem

Autonomous AI research is bottlenecked less by model access than by **research discipline**. PhD students, small labs, independent researchers, and applied teams all hit the same wall: a coding agent can write training code, but it can't keep a coherent multi-day research loop — goals drift, baselines disappear, runs aren't comparable, ideas don't accumulate, and every new session starts from zero.

AutoResearch-AI gives an agent the operating system for that loop. It is not a model, not a benchmark, not a hosted service. It is the durable scaffolding that lets a research conversation between human and agent survive across sessions, machines, and weeks.

## What it should do

- Keep goals, baseline, runs, ideas, papers, and comparison as **plain files** in the repo, inspectable with `cat`.
- Make first experiments cheap, small, and obvious — never trigger an expensive run on the first turn.
- Prefer **history-first** ideas (grounded in this repo's prior runs and recent papers) over generic sweeps.
- Stay easy to install, inspect, and fork. Zero runtime dependencies in the published CLI.
- Make agents accountable: every run logs its environment, command, output, and result.
- Keep the published npm package focused on the researcher's day-to-day workflow.

## What it is not

To stay focused, AutoResearch-AI is explicitly **not**:

- **An AutoML tool.** It does not pick architectures or hyperparameters for you — it gives an agent the scaffolding to do that, and gives you the receipts.
- **A hosted agent service.** The CLI runs locally. Future hosted layers (dashboard, team history, managed runners) are optional, paid, and built around the open core — never required to use the tool.
- **A model wrapper.** It is agent-agnostic. Codex, Claude Code, Cursor, Hermes, and others all work via the same templates.
- **A benchmark suite.** It does not ship benchmark tasks. It runs the experiments *you* define against *your* repo.
- **An experiment-tracking-only tool.** There are good ones already (W&B, MLflow, Aim). AutoResearch-AI's contribution is the **loop**: goal → baseline → idea → run → compare → promote → continue, with the agent in the seat.

## Principles

1. **Plain files beat hidden state.** If a researcher can't `cat` it, it doesn't exist for the loop.
2. **Baseline first.** No experiment is meaningful without something to improve against. The CLI refuses to start the loop without one.
3. **Smallest useful proof.** Every change ships with the smallest test or run that demonstrates it.
4. **Agent-agnostic by default, agent-specific by opt-in.** The same template should work across coding agents; agent-specific skill packs are additive, not replacements.
5. **Reproducibility is a feature, not a side effect.** Every run captures its environment. Every result is replayable.
6. **Built in the open, by humans and agents.** Both can contribute via the `G##` slot system in [GOALS.md](GOALS.md). PRs are reviewed the same way regardless of who wrote them.
7. **Honest about results.** Don't claim a result you didn't run. Cite sources.

## The long-term picture

A researcher should be able to: install the CLI on any machine, point it at any ML repo, hand the prompt to any coding agent, and get back a multi-day research loop with logged runs, comparable metrics, accumulated ideas, and a result they could publish — all without losing context between sessions.

The open core stays free forever. Optional paid layers (hosted dashboard, team run history, managed GPU runners, lab templates, compliance support) fund the core.

---

This is the north star. Specific commands, file formats, and roadmap items are in [ROADMAP.md](ROADMAP.md) and [GOALS.md](GOALS.md), and they evolve faster than this document.
