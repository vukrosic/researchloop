# AutoResearch-AI Repo Rules

You are working in the AutoResearch-AI repository. This file is the entry point for any AI coding agent (Codex, Claude Code, Cursor, Hermes, others) sent to make changes here.

## Mission

Keep the npm package, docs, skill packs, and local dev control room aligned.
Prefer small, documented changes that keep the package easy to install and easy to trust.

## Start

Before changing code, read the relevant repo files:

- [`README.md`](README.md)
- [`VISION.md`](VISION.md)
- [`ROADMAP.md`](ROADMAP.md)
- [`GOALS.md`](GOALS.md) — the canonical contributor slot system
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — local setup and the claim flow
- [`docs/getting-started.md`](docs/getting-started.md)
- [`docs/startup/README.md`](docs/startup/README.md)
- [`researchloop-dev/rules/control-room.md`](researchloop-dev/rules/control-room.md) when touching local-only onboarding or transcript assets

Before subtree work, read the nearest scoped `AGENTS.md` if one exists (most subdirectories have one).

On first contact in this repo, the agent should:

- briefly introduce AutoResearch-AI and what it does
- inspect the local machine for useful system context, especially available GPUs
- inspect the workspace for one or more likely AI research repositories
- if multiple candidate repos are present, ask which one to use
- if no clear repo is present, ask the user which repository to target before proceeding

## Hard Rules

1. Do not claim a result unless you ran the command or can point to existing evidence.
2. Keep the published npm package lean. The CLI is intentionally zero runtime-dependency — adding one requires explicit justification in the PR.
3. Keep prompts, templates, docs, and tests in sync when behavior changes.
4. Keep `researchloop-dev/` local-only and out of published package contents (`package.json` `files` whitelist controls this).
5. Preserve the current CLI contract unless the user explicitly asks to change it.
6. Prefer the smallest useful test or proof before widening the scope.
7. When editing skills, update the agent mapping docs at the same time.
8. **Acceptance criteria are not optional.** If you implement a `G##` goal, copy each Acceptance line from `GOALS.md` into the PR template's checklist and demonstrate each one. Reviewers reject PRs that skip this.
9. **Name yourself in PRs.** If you are an AI agent, identify which one (Codex / Claude / Cursor / Hermes / other) in the PR's "Agent attribution" section so reviewers know what kind of review the change needs.

## Working Style

- Use the existing file-based loop: goal, plan, prompt, record, compare, report.
- If a change affects agent behavior, update the generated prompt/template and the user-facing docs together.
- If a change affects release or onboarding, add a test or a concrete smoke check.
- For non-trivial changes: open a `G##`-linked issue first (use the [Contribute-a-Goal template](.github/ISSUE_TEMPLATE/contribute-goal.yml)) before coding. This prevents two agents racing the same goal.

## What you can change without a PR (maintainer only)

Direct-to-`main` is acceptable only for repo-meta files: `README.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `GOVERNANCE.md`, `SUPPORT.md`, `CITATION.cff`, `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`. Everything under `bin/`, `templates/`, `skills/`, `scripts/`, and `examples/` goes through PR review.
