# ResearchLoop Skills

This folder ships downloadable agent skills for autonomous AI research.

The package keeps the core product in the CLI, dashboard, prompts, and run ledger.
These skills are the agent-side memory layer that makes the research loop stick.

## What is in here

- `researchloop-autoresearch/` - the main research skill pack
- `researchloop-autoresearch/references/` - focused playbooks for common experiment families
- `researchloop-training-ladder/` - a staged small-to-long training mode for pruning and promotion

## How users use it

Users copy the right file into the skill folder their agent expects.

Typical mapping:

- Codex: copy `researchloop-autoresearch/codex/SKILL.md` into the local Codex skills directory
- Claude Code: copy `researchloop-autoresearch/claude-code/CLAUDE.md` into the Claude Code instructions or skill location they use

## What the skill pack does

- keeps the goal visible
- forces baseline-first behavior
- asks for one small experiment at a time
- records runs and comparisons
- prunes weak ideas instead of spiraling

The CLI prints prompts and creates `.researchloop/` state.
The skills make the agent remember how to behave while doing the work.
