A new **Tier 1: loop intelligence** feature using the [agent-feature template](https://github.com/vukrosic/autoresearch-ai/blob/main/.github/ISSUE_TEMPLATE/agent-feature.yml). Proposed GOALS.md ID: **G57**.

> This is one of the first issues to use the new agent-feature template. Implementing it cleanly is itself a test of whether the format works.

### Researcher line

An ML researcher coming back the next morning needs `autoresearch` to reconstruct yesterday's state — current goal, baseline, last N runs, open ideas, suggested next experiments — in **one command**, so their coding agent can pick up the loop without re-reading 200 lines of ledger.

### Demo line

```text
$ autoresearch resume
# RESUME CONTEXT — 2026-05-18 (since 2026-05-17 22:14)

## Goal
lower val_loss (direction: lower)

## Baseline
val_loss: 2.41 — .researchloop/baseline.md

## Last 3 runs
| id          | val_loss | delta  | status  |
| lr-3e-4     | 2.39     | -0.02  | done    |
| lr-1e-4     | 2.43     | +0.02  | done    |
| dropout-0.2 | NaN      | —      | crashed |

## Open ideas (3)
- cosine-scheduler — proposed 2026-05-17
- token-mixer-swap — proposed 2026-05-17

## Next 3 untried, ranked by likely value
1. lr-2e-4 (between 1e-4 and 3e-4, neither beat baseline)
2. dropout-0.1 (smaller than crashed 0.2)
3. cosine-scheduler (from open ideas)
```

The researcher pastes this block into their coding agent prompt and the agent picks up immediately. This is the durable-context promise from [VISION.md](https://github.com/vukrosic/autoresearch-ai/blob/main/VISION.md) made real.

### Composes with

- `goal` — reads current goal definition
- `compare` — reads ledger for last N runs
- `idea` — reads open ideas
- `prompt` — `resume` output can be injected into the agent prompt template

### Acceptance criteria

- [ ] `autoresearch resume` prints markdown to stdout: goal, baseline, last 3 runs, open ideas, 3 ranked next experiments
- [ ] `--since DATE` filters runs to after that timestamp (ISO date)
- [ ] `--write` saves to `.researchloop/RESUME.md` instead of stdout
- [ ] `--last N` configures how many recent runs to show (default 3)
- [ ] Empty ledger prints `no state yet — run autoresearch goal first` and exits 0
- [ ] `scripts/test-resume.sh` covers: happy path, empty ledger, ledger with crashed runs, `--since` filter, `--write`
- [ ] `npm test` is green

### Anti-features (out of scope)

- Does **NOT** call an LLM — pure ledger summarization, zero deps
- Does **NOT** modify ledger / baseline / goal files (read-only)
- Does **NOT** replace `report` — `resume` is mid-loop pickup; `report` is end-state writeup
- "Next 3 untried" is a simple heuristic (gaps in tried hyperparams + listing open ideas), not an ML suggestion engine

### Files the agent will touch

- `bin/researchloop.js` — add `cmdResume`
- `scripts/test-resume.sh` — new
- `docs/getting-started.md` — add resume to a "morning workflow" section
- `templates/prompts/first-contact.md` — reference `autoresearch resume` as the first command an agent should run on a returning session
- `package.json` — add `test:resume` to the `test` script
- `GOALS.md` — add a G57 entry under Tier 1

### How to claim

[First-PR-wins.](https://github.com/vukrosic/autoresearch-ai/blob/main/CONTRIBUTING.md#the-claim-flow-first-pr-wins) Open a draft PR titled `[agent] resume — reconstruct mid-loop session context` against `main`, copy the Acceptance lines into the PR checklist, paste a real terminal demo into the Demo block.
