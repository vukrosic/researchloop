# Local Dev Tools

Local-only helper scripts for running AutoResearch-AI development experiments. These are not part of the published npm package — they live under `researchloop-dev/` and ship only via the git repo.

## `codex-swarm.sh`

Opens a grid of `Terminal.app` windows on macOS, each running the [Codex CLI](https://github.com/openai/codex). Use it to fan out multiple agent sessions in parallel — for example, six contributors each working a different `G##` goal from [GOALS.md](../../GOALS.md), or one orchestrator + five workers.

### Requirements

- macOS (uses AppleScript + Terminal.app)
- The `codex` CLI on `PATH` (`npm install -g @openai/codex` or equivalent)
- First run prompts once for **Automation permission** to control Terminal — approve under *System Settings → Privacy & Security → Automation* and re-run.

### Usage

```bash
./researchloop-dev/tools/codex-swarm.sh                              # 3x2 grid (6 codex windows)
./researchloop-dev/tools/codex-swarm.sh --cols 2 --rows 2            # 2x2 grid (4 windows)
./researchloop-dev/tools/codex-swarm.sh --cmd "codex --resume"       # different command
./researchloop-dev/tools/codex-swarm.sh --cwd /path/to/repo          # start each window in a working dir
./researchloop-dev/tools/codex-swarm.sh --bottom-pad 120             # leave more room for the dock
```

### Options

| Flag | Default | Purpose |
| --- | --- | --- |
| `--cols N` | `3` | Columns in the grid |
| `--rows M` | `2` | Rows in the grid |
| `--cmd "STR"` | `codex` | Command to run in each window |
| `--cwd /path` | (none) | Working directory for each window |
| `--bottom-pad N` | `80` | Pixels reserved at the bottom for the dock |
| `-h`, `--help` | — | Show inline help |

### Notes

- If Terminal.app wasn't already running, you may get one stray empty window in addition to the grid. Close it manually, or open a Terminal window first before running the script.
- Window bounds use the main display only. Multi-monitor support is not implemented yet.
- Each window is an independent Terminal session — closing them doesn't affect the others.

### Suggested patterns

**Parallel goal work.** Open 6 windows, each in its own checkout or worktree:

```bash
for i in 1 2 3 4 5 6; do
  git worktree add ../autoresearch-ai-wt-$i HEAD
done
./researchloop-dev/tools/codex-swarm.sh --cwd "$(pwd)/../autoresearch-ai-wt-1"  # then tell each agent which goal
```

**Orchestrator + workers.** Run one window as the orchestrator, the rest as worker agents reading shared state from `.researchloop/team/`.

**Timed sprints.** Combine with the [timed research sprint module](../experiments/protocols/timed-research-sprint-module.md) — each window runs its own 5-minute / 5-second probe sprint against a different `change_label`.

### Roadmap

These extensions are not built yet — open an issue if you want one:

- `--prompt-file path` so each window starts with a different role prompt (researcher / coder / planner)
- `--worktree-from /path` to auto-create N disposable git worktrees of a target repo
- Linux support (xterm / gnome-terminal / kitty)
- A tmux-backed variant so a parent agent can `send-keys` into specific windows after launch
