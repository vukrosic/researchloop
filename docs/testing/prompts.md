# Prompt Template Test Plan

Purpose:

Make sure the generated prompts stay clean for each supported agent.

## Commands

```bash
npm run test:prompts
```

## Checks

- `codex` prompt includes the goal and the durable working-memory instructions.
- `claude-code` prompt includes the autonomy rule and the append-only log guidance.
- `hermes` prompt includes the orchestration language.
- `generic` prompt still works as the fallback.
- No prompt contains the raw `{{GOAL}}` placeholder.

## Why It Matters

Prompt drift is the kind of bug that quietly breaks the product without breaking the CLI. This test keeps the packaging honest.
