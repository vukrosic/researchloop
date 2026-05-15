# ResearchLoop Development Team

Use this pack when you want to split ResearchLoop work across many agents without losing the merge story.

## Roles

- human: release direction and final merge gate
- orchestrator: decomposition and assignment
- reviewer: merge safety and test gate
- workers: one lane each

## Flow

1. The human sets the release goal.
2. The orchestrator reads the board and assigns non-overlapping lanes.
3. Each worker gets one branch or worktree.
4. The reviewer checks diffs, tests, and overlap before merge.
5. The human merges the accepted branches.

## Commands

```bash
researchloop team --workers 8
researchloop goal "ship the next ResearchLoop release"
researchloop inspect
researchloop prompt --agent codex
```

## Board

Open `board.md` first. It is the quick map for who owns what.

If you want to create the branches and worktrees in one shot, run `setup.sh`.
