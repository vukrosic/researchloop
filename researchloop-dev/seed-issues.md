# Seed issues for contributors

Source-of-truth for the GitHub issue bodies. When seeding a new wave of contributor work, draft the body here, review it, then `gh issue create`. Keep this file in sync with the live issues so a future agent can regenerate them if needed.

**Current live issues** (as of 2026-05-17):

| # | G## | Title | Effort | Tier | Labels |
|---|---|---|---|---|---|
| [1](https://github.com/vukrosic/autoresearch-ai/issues/1) | G14 | Environment capture per run | S | 0 | good first issue, tier-0 |
| [2](https://github.com/vukrosic/autoresearch-ai/issues/2) | G25 | Agent command sandbox / allowlist | S–M | 0 | good first issue, tier-0, security |
| [3](https://github.com/vukrosic/autoresearch-ai/issues/3) | G26 | autoresearch baseline-status | S | 1 | good first issue, tier-1, shipped |
| [4](https://github.com/vukrosic/autoresearch-ai/issues/4) | G31 | autoresearch doctor --repair-plan | S | 3 | good first issue, tier-3, shipped |
| [8](https://github.com/vukrosic/autoresearch-ai/issues/8) | G04 | Pluggable evaluation runner (eval.yaml schema) | M | 2 | keystone, tier-2 |
| [9](https://github.com/vukrosic/autoresearch-ai/issues/9) | G07 | Sweep generator | M | 4 | tier-4 |
| [10](https://github.com/vukrosic/autoresearch-ai/issues/10) | G18 | Worker daemon / task queue | M | 4 | tier-4 |
| [11](https://github.com/vukrosic/autoresearch-ai/issues/11) | G13 | autoresearch query over runs.jsonl | M | 4 | tier-4, shipped |
| [12](https://github.com/vukrosic/autoresearch-ai/issues/12) | G23 | Cost and wall-clock accounting | S | 5 | good first issue, tier-5, shipped |
| [13](https://github.com/vukrosic/autoresearch-ai/issues/13) | G24 | Slack / webhook notifications | S | 6 | good first issue, tier-6 |

All use the **first-PR-wins** claim flow — see [CONTRIBUTING.md](../CONTRIBUTING.md#the-claim-flow-first-pr-wins).

---

## Seeding the next wave

When the current wave is partially absorbed (say, 5+ goals merged), pick the next set of READY-NOW goals from GOALS.md using these rules:

1. **Effort: S or M.** L-effort goals need a human-architect conversation first.
2. **No open dependencies.** Every `Depends on:` G## must be merged into `main`.
3. **No file-ownership collision.** Two simultaneously-open issues should not own the same file (see GOALS.md's file ownership map). `bin/researchloop.js` is the exception — it's the shared CLI surface; the integration owner for any conflict is the reviewer lane.
4. **Spread across tiers.** Don't seed only Tier 4 stuff if Tier 0/1/2 has open beachhead work. Tier 0 safety always seeds first if open.

Next wave candidates (after current 10 absorb): goals downstream of whatever ships first. If **G04** lands, unlock G05, G06, G09, G10, G11, G12, G19, G20, G22. If **G26** lands, unlock G27, G28, G01. If **G29** is ready to seed standalone, do that.

## Issue body template

Use this skeleton for every new seed:

```markdown
A Tier N (theme) goal from [GOALS.md#gNN](https://github.com/vukrosic/autoresearch-ai/blob/main/GOALS.md#gNN--<slug>). Effort: **S|M|L**. Depends on: **none | G##, G##**.

> One-line motivation pulled verbatim from GOALS.md.

#### Deliverables

(bulleted, from GOALS.md)

#### Acceptance

(bulleted, verbatim from GOALS.md — these are what the reviewer mechanically checks)

#### Files you'll touch

(from GOALS.md)

#### How to claim

[First-PR-wins.](https://github.com/vukrosic/autoresearch-ai/blob/main/CONTRIBUTING.md#the-claim-flow-first-pr-wins) Open a draft PR titled `[goal] G## — short-description` against `main`, copy the Acceptance lines into the PR checklist.
```

## gh issue create boilerplate

```bash
gh issue create \
  --title "[goal] G## — title from GOALS.md" \
  --label "goal-claim,agent-friendly,tier-N,<good first issue if S>,<keystone if unlocks 3+>" \
  --body "$(cat <<'EOF'
... body from template above ...
EOF
)"
```

Add `security` label if the goal touches sandbox / command execution. Add `keystone` label only when the goal unlocks 3 or more downstream goals.
