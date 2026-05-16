# ResearchLoop Repo Rules

You are working in the ResearchLoop repository.

## Mission

Keep the npm package, docs, skill packs, and local dev control room aligned.
Prefer small, documented changes that keep the package easy to install and easy to trust.

## Start

Before changing code, read the relevant repo files:

- `README.md`
- `ROADMAP.md`
- `docs/getting-started.md`
- `docs/startup/README.md`
- `researchloop-dev/rules/control-room.md` when touching local-only onboarding or transcript assets

Before subtree work, read the nearest scoped `AGENTS.md` if one exists.

On first contact in this repo, the agent should:

- briefly introduce ResearchLoop and what it does
- inspect the local machine for useful system context, especially available GPUs
- inspect the workspace for one or more likely AI research repositories
- if multiple candidate repos are present, ask which one to use
- if no clear repo is present, ask the user which repository to target before proceeding

## Hard Rules

1. Do not claim a result unless you ran the command or can point to existing evidence.
2. Keep the published npm package lean.
3. Keep prompts, templates, docs, and tests in sync when behavior changes.
4. Keep `researchloop-dev/` local-only and out of published package contents.
5. Preserve the current CLI contract unless the user explicitly asks to change it.
6. Prefer the smallest useful test or proof before widening the scope.
7. When editing skills, update the agent mapping docs at the same time.

## Working Style

- Use the existing file-based loop: goal, plan, prompt, record, compare, report.
- If a change affects agent behavior, update the generated prompt/template and the user-facing docs together.
- If a change affects release or onboarding, add a test or a concrete smoke check.
