A new **Tier 5: reporting & dashboard** feature using the [agent-feature template](https://github.com/vukrosic/autoresearch-ai/blob/main/.github/ISSUE_TEMPLATE/agent-feature.yml). Builds on **G23 cost-accounting** ([#12](https://github.com/vukrosic/autoresearch-ai/issues/12)). Proposed GOALS.md ID: **G59** (enforcement layer atop G23).

### Researcher line

A researcher running an unattended overnight sweep needs `autoresearch` to **halt the loop** when run-count / cost / wall-clock crosses a threshold, because otherwise the GPU budget burns by morning with no human in the loop and they can't trust the tool for autonomous use.

### Demo line

```text
$ autoresearch budget --max-runs 5 --max-cost 4.00 --max-hours 6
Budget written: halt on 5 runs OR $4.00 OR 6h (whichever first)

$ autoresearch team --workers 4
[worker-1] run lr-2e-4 → val_loss 2.40
[worker-2] run dropout-0.1 → val_loss 2.41
[worker-1] run cosine-sched → val_loss 2.38
[worker-2] run lr-5e-5 → val_loss 2.45
[worker-1] run momentum-0.95 → val_loss 2.39
BUDGET HALT: max-runs reached (5/5)
Wrote .researchloop/BUDGET_HALT.md

$ cat .researchloop/BUDGET_HALT.md
# Budget halt — 2026-05-18 02:14
- Reason: max-runs reached
- Runs executed: 5 / 5
- Cost spent: $2.40 / $4.00
- Wall-clock: 3h 22m / 6h
```

The researcher wakes up to a halted loop and a readable summary instead of a surprise bill.

### Composes with

- `team` — checks budget pre-spawn; halts between runs when any limit hits
- `run` — records cost & duration into ledger for budget to read
- `report` — final report includes `budget consumed: X / Y`
- `dashboard` — surfaces budget remaining as a visible stat

### Acceptance criteria

- [ ] `autoresearch budget --max-runs N --max-cost X --max-hours H` writes `.researchloop/budget.json` (at least one limit required; others optional)
- [ ] `autoresearch budget --status` prints current consumption vs. each set limit
- [ ] `autoresearch budget --clear` removes the budget file
- [ ] `autoresearch team` checks the budget before each spawn; if any limit is exceeded it writes `BUDGET_HALT.md`, exits non-zero, halts further spawns
- [ ] `BUDGET_HALT.md` contains the trigger reason + each-limit-spent vs. limit-set
- [ ] `--max-cost` is a no-op (with a friendly warning) if the ledger has no `cost_usd` field (i.e. G23 not yet merged) — `--max-runs` and `--max-hours` ship independently
- [ ] `scripts/test-budget.sh` covers: each limit type triggers halt, status command, clear command, missing-cost-field warning
- [ ] `npm test` is green

### Anti-features (out of scope)

- Does **NOT** fetch real billing from cloud providers — cost is read from per-run logged `cost_usd` only
- Does **NOT** halt mid-run — halts BETWEEN runs only (mid-run halt requires signal handling, separate issue)
- Does **NOT** support per-experiment budget overrides
- Does **NOT** auto-resume after a halt — the researcher must explicitly clear or raise the budget

### Files the agent will touch

- `bin/researchloop.js` — add `cmdBudget`; modify `cmdTeam` to check budget pre-spawn
- `scripts/test-budget.sh` — new
- `docs/getting-started.md` — new section "Unattended runs"
- `package.json` — add `test:budget` to the `test` script
- `GOALS.md` — extend G23 entry or add G59 for the enforcement layer

### How to claim

[First-PR-wins.](https://github.com/vukrosic/autoresearch-ai/blob/main/CONTRIBUTING.md#the-claim-flow-first-pr-wins) Open a draft PR titled `[agent] budget — halt the loop on run/cost/time limits` against `main`, copy the Acceptance lines into the PR checklist, paste a real terminal demo into the Demo block.

**Note on dependency:** if G23 ([#12](https://github.com/vukrosic/autoresearch-ai/issues/12)) is not yet merged when this is claimed, ship `--max-runs` and `--max-hours` first and stub `--max-cost` with the friendly warning. Don't block on G23.
