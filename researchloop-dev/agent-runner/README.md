# agent-runner — orchestrator for autoresearch-ai contributors

Picks one `claim-next`-labeled issue, spawns an implementer agent (Codex or Claude Code) in a fresh git worktree, opens a draft PR, then spawns a reviewer agent (the other one) to post a verdict comment. Human merges what survives review.

> Standalone extraction in progress: the separate `gitswarm` project now lives in `/Users/vukrosic/my-life/gitswarm` and is the path for the GitHub-issues dashboard split. This local copy stays here during the migration.

## Files

- [`orchestrate.sh`](orchestrate.sh) — the one entry point. Bash; ~200 lines.
- [`prompts/implement.md`](prompts/implement.md) — system prompt for the implementer.
- [`prompts/review.md`](prompts/review.md) — system prompt for the reviewer (independent, must not have implementer context).
- `state/` — per-run logs, rendered prompts, reviewer verdicts. Gitignored.

## How it picks work

```bash
gh issue list --label claim-next                  # the ready queue
  --jq '.[] | select(in-progress not in labels)'   # not already being worked
  | sort by issue number | head -1                 # lowest-numbered first
```

Maintainer controls the queue by adding/removing the `claim-next` label. `needs-validation` is a hard skip — speculative proposals never enter.

## Run modes

```bash
# Pick lowest claim-next, full loop (implement → push → draft PR → review):
./orchestrate.sh

# Specific issue:
./orchestrate.sh 65

# Re-run reviewer on an existing PR:
./orchestrate.sh --review 68

# Dry run (prints what it would do; spawns no agent):
DRY_RUN=1 ./orchestrate.sh 65
```

## Agent choice

Default: **Codex implements, Claude reviews.** Different models, different blind spots.

Swap with env vars:

```bash
IMPLEMENTER=claude REVIEWER=codex ./orchestrate.sh 65
```

The CLI binaries must be installed and authenticated. Verify with:

```bash
codex --version    # adjust CODEX_BIN if installed elsewhere
claude --version   # adjust CLAUDE_BIN
```

> **Note on flags:** `codex exec "<prompt>"` and `claude -p "<prompt>"` are the non-interactive entry points used here. Verify exact syntax against your installed versions before the first live run — these flags can change between CLI releases.

## Failure modes the orchestrator catches

1. **Implementer escalation:** agent drops `BLOCKED.md` or `OBJECTION.md` → orchestrator posts an issue comment with the worktree path and stops. Human takes over.
2. **Uncommitted changes:** orchestrator commits with a "safety net" message rather than discard.
3. **No commits:** if the agent finished without producing commits, no PR is opened.
4. **Worktree collision:** orchestrator refuses to overwrite an existing worktree.

## Failure modes the reviewer catches

1. **Acceptance theater** — checkboxes ticked but the diff doesn't satisfy them.
2. **Demo theater** — the PR demo is a synthetic 1-line ledger, not a real workflow.
3. **Scope creep** — files touched outside the issue's "Files" list.
4. **Anti-feature violations** — agent silently expanded beyond what the issue allowed.
5. **>500 LOC** — auto-flag for human review regardless of correctness.

The reviewer's verdict goes back as a PR comment with a structured format. Human reads ~1 of 3 PRs (the approves) instead of all of them.

## State / observability

Each run leaves files under `state/`:

- `prompt-<issue>.md` — rendered implementer prompt (for replay / debugging)
- `implementer-<issue>.log` — full implementer stdout/stderr
- `review-prompt-<pr>.md` — rendered reviewer prompt
- `review-<pr>.md` — reviewer's final comment (also posted to GitHub)

`state/` is gitignored — local-only.

## Cost & safety

- Each loop runs **one** implementer + **one** reviewer. Estimate ~$1-5 per issue depending on agent / model / iteration count.
- Hard timeout: `AGENT_TIMEOUT=1800` (30 min) per spawn. Set lower for paranoid first runs.
- Worktrees live under `.agent-worktrees/` at the repo root — gitignored, easy to wipe.
- The orchestrator does NOT auto-merge PRs. Every change requires human merge.

## What this is NOT

- Not a multi-issue parallel runner (yet — get single-issue right first).
- Not a cron daemon (yet — keep human-triggered until prompts are tuned).
- Not a model gateway. Talks directly to the local Codex / Claude CLIs.
- Not a substitute for human review on the keystone goals (G04 etc).

## Roadmap

When the single-issue loop is trusted on 3+ real PRs:

1. Add parallel mode (work on N claim-next issues at once).
2. Add an "improve" loop — if reviewer says request-changes, re-spawn implementer with the review comment as additional context.
3. Add a budget cap (max-spawns-per-day, max-cost-per-day) before automating with cron.
4. Move agent execution off the laptop to a small VPS or GitHub Actions.
