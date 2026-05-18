A new **Tier 1: loop intelligence** feature using the [agent-feature template](https://github.com/vukrosic/autoresearch-ai/blob/main/.github/ISSUE_TEMPLATE/agent-feature.yml). Proposed GOALS.md ID: **G58**.

### Researcher line

A researcher comparing two runs needs to see **code diff + env diff + hyperparam diff + metric delta side-by-side**, because today they grep two JSON blobs by hand and miss things.

### Demo line

```text
$ autoresearch diff lr-3e-4 lr-1e-4
# DIFF: lr-3e-4 vs lr-1e-4

## Metrics
| metric     | lr-3e-4 | lr-1e-4 | delta             |
| val_loss   | 2.39    | 2.43    | +0.04 (worse)     |
| train_loss | 2.10    | 2.18    | +0.08             |
| step/s     | 142     | 138     | -4                |

## Command
- python train.py --lr 3e-4
+ python train.py --lr 1e-4

## Env
- CUDA_VISIBLE_DEVICES=0
+ CUDA_VISIBLE_DEVICES=1
(other vars identical)

## Code (git commit at run time)
both: a3f2b1c — identical
```

The researcher reads one screen and knows exactly why the runs differ. This is the everyday-need that `compare` doesn't currently cover — `compare` shows the table; `diff` shows the *why*.

### Composes with

- `compare` — `diff` is the drill-down from compare's N-way table
- `run` — reads recorded env / command / git-commit metadata
- `report` — diff blocks can be embedded in reports
- `leaderboard` — markdown reports can suggest `diff` between adjacent ranks

### Acceptance criteria

- [ ] `autoresearch diff <a> <b>` prints markdown with sections: Metrics, Command, Env, Code
- [ ] Missing run id exits non-zero with a clear message naming which id is missing
- [ ] `--write FILE` saves to disk; default stdout
- [ ] If both runs share git commit, Code section prints `both: <sha> — identical`
- [ ] Env section shows only differing variables, not a full dump
- [ ] Metrics present in one run but not the other are flagged `(only in a)` / `(only in b)`
- [ ] `scripts/test-diff.sh` covers: two-different-runs, identical-runs, missing-id, missing-metric, env-difference
- [ ] `npm test` is green

### Anti-features (out of scope)

- Does **NOT** do statistical significance (see [#16](https://github.com/vukrosic/autoresearch-ai/issues/16) G33)
- Does **NOT** pull or diff binary artifacts / checkpoints
- Does **NOT** support more than 2 runs at a time (use `compare` for N-way)
- Does **NOT** shell out to `git diff` against the working tree — only compares recorded commits from the ledger

### Files the agent will touch

- `bin/researchloop.js` — add `cmdDiff`
- `scripts/test-diff.sh` — new
- `docs/getting-started.md` — add `diff` to the commands cheatsheet
- `package.json` — add `test:diff` to the `test` script
- `GOALS.md` — add G58 entry under Tier 1

### How to claim

[First-PR-wins.](https://github.com/vukrosic/autoresearch-ai/blob/main/CONTRIBUTING.md#the-claim-flow-first-pr-wins) Open a draft PR titled `[agent] diff — side-by-side run comparison` against `main`, copy the Acceptance lines into the PR checklist, paste a real terminal demo into the Demo block.
