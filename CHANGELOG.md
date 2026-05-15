# Changelog

## Unreleased

New:

- `researchloop team` writes a local multi-agent development board with orchestrator, reviewer, and worker briefs.
- `templates/team/` now ships role templates for the development hierarchy.
- `docs/startup/agent-ops.md` explains the human / orchestrator / worker / reviewer flow for building ResearchLoop itself.

Docs:

- README and getting-started now point users to the prompt first and include the team board flow.

## 0.2.0

ResearchLoop becomes a runtime, not just a folder.

New:

- `researchloop run` executes a command, streams output to a per-run log, parses a metric (default regex on `metric=N` or `"metric": N`, plus last-line JSON fallback), and auto-appends a row to `runs.jsonl`. No more manual `record`.
- `researchloop baseline` is `run` for the baseline command and also updates `goal.md` Current Best and `plan.md` Current State.
- `researchloop scan-papers` queries the arXiv API for papers relevant to the goal, writes one markdown note per result to `scratchpad/papers/`, caches responses to `~/.cache/researchloop/arxiv/`, supports `--offline`, `--since YYYY-MM`, `--limit`, `--query`, `--cache-dir`.
- `researchloop idea` now reads `scratchpad/papers/` and adds paper-derived ideas alongside the adapter playbook.

Improvements:

- Tighter adapter detection: pytorch needs a real `train*.py` script or `torch` in deps; huggingface needs `transformers` in deps. No more false positives from filename substrings.
- `candidate_config_files` no longer matches every `.json`/`.yaml`/`.toml` in the repo.
- README install command no longer hardcodes a developer machine path.
- New tests: `test:run`, `test:scan-papers`. arXiv test uses a recorded XML fixture and never hits the network.

Cleanup:

- Removed misleading `projects/researchloop` and `projects/researchloop-cli` symlinks.

## 0.1.0

First public ResearchLoop release.

Includes:

- `researchloop init`
- `researchloop goal`
- `researchloop inspect`
- `researchloop idea`
- `researchloop prompt`
- `researchloop doctor`
- `researchloop record`
- `researchloop compare`
- `researchloop dashboard`
- `researchloop report`

Also includes:

- local-first dashboard
- MacBook / MPS smoke path
- startup docs
- onboarding tests
- competitor research notes
- open source release plan
