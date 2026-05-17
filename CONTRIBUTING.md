# Contributing

AutoResearch-AI is built in the open by humans and AI coding agents working in parallel. Welcome.

## What kind of contributions we want

Most-wanted:

- New repo adapters (under `templates/adapters/`) for ML frameworks the CLI doesn't detect well yet.
- Better prompt templates (under `templates/prompts/`) — especially focus playbooks for specific research lanes (architecture, optimizer, attention, eval).
- Dashboard and run-logging improvements (under `templates/dashboard/`, `bin/researchloop.js`).
- Onboarding and first-run fixes — anything that shortens "install" → "first logged experiment."
- Real examples from real research workflows under `examples/`.
- Regression tests for behavior that has bitten us before (under `scripts/test-*.sh`).
- Implementations of open `G##` goals in [GOALS.md](GOALS.md).

Out of scope (please open a Discussion before working on these):

- Adding runtime dependencies to the npm package. The CLI is intentionally zero-runtime-dep. Justify in the PR if you really need one.
- Architecture rewrites or new top-level commands without a `G##` slot.
- Hosted infrastructure / SaaS code. The core stays inspectable and forkable.

## Local setup

Prerequisites: Node 18, 20, or 22 (CI tests all three), git, bash, macOS or Linux.

```bash
git clone https://github.com/vukrosic/autoresearch-ai.git
cd autoresearch-ai
npm link                 # installs the CLI globally from your checkout
autoresearch --help      # smoke test
npm test                 # full local test suite (~1-2 min)
```

To unlink when you're done:

```bash
npm unlink -g autoresearch-ai
```

## The claim flow (first-PR-wins)

AutoResearch-AI uses a **first-PR-wins** slot system. No maintainer permission needed to start. Whoever ships first wins.

1. **Browse [GOALS.md](GOALS.md) or the [open issues](https://github.com/vukrosic/autoresearch-ai/issues).** Pick a `G##` goal where:
   - every goal in its `Depends on` line is already merged into `main` (check `git log`, not just the issue tracker)
   - the effort tag (S / M / L) matches what you can commit to in one sitting

2. **Branch from `main`.** Branch naming: `g##-short-description` (e.g., `g14-env-capture`). One `G##` per branch.

3. **Open a draft PR immediately** — within the first hour of starting work — titled `[goal] G## — your-short-description` against `main`. Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) and fill in:
   - the linked issue (if one exists) or the `G##` from GOALS.md
   - **every Acceptance line from the `G##` goal, copy-pasted into the checklist** — this is the mechanical check reviewers use
   - "Agent attribution" — which agent (if any) wrote the code (Codex / Claude / Cursor / Hermes / human)

   The draft PR is your claim. Other contributors will see it and pick something else. If you abandon (no commits for 7 days), anyone may take over.

4. **Implement.** Keep the change focused — one `G##` per PR. Architecture changes need an issue + discussion first.

5. **Run tests locally.** `npm test` must be green. If you added or changed CLI behavior, add a `scripts/test-*.sh` for it and wire it into the `test` script in `package.json`.

6. **Mark the PR ready for review** when every Acceptance line is checked and CI is green.

7. **Respond to review.** First-review SLA is ~7 days. Be patient and kind. PRs that skip the Acceptance checklist get bounced back.

**Race conditions.** If two non-draft PRs land on the same goal at the same time, the first to be merged wins. The other can be rebased onto the merged work or closed. This rarely happens in practice — the draft-PR-as-claim signal is enough.

**What if the goal has no formal Acceptance lines?** Some early `G##` goals are less rigid. In that case, write your own Acceptance lines in the PR description, derived from the Deliverables section, and ask for sign-off on them as part of the review. The maintainer will fold them back into GOALS.md.

## Test patterns

Tests are bash scripts under `scripts/test-*.sh`. Each one:

- creates a temp directory (use `mktemp -d`)
- runs the CLI against it
- asserts on output / files created
- cleans up

Wire your new test into the `test` script in `package.json` so it runs as part of `npm test`. Example test scripts to copy from: [scripts/test-goal.sh](scripts/test-goal.sh), [scripts/test-doctor.sh](scripts/test-doctor.sh) (if present), or [scripts/test-setup.sh](scripts/test-setup.sh).

Available test subsets (run any one in isolation):

```bash
npm run smoke              # CLI --help works
npm run smoke:e2e          # end-to-end install + init + first run
npm run test:setup         # blank-repo and fixture setup checks
npm run test:adapters      # repo-shape adapter detection
npm run test:run           # `run` and `baseline` against shell commands
# ... (see package.json for the full list)
```

The release gate adds a packed-tarball install check:

```bash
npm run test:release       # = npm test + test:packed
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs `npm test` on Node 18 / 20 / 22 against ubuntu-latest and macos-latest for every push and pull request, plus a packed-tarball install job. PRs do not merge until those jobs are green.

## PR-flow vs. direct-to-main

| Area | How changes land |
|---|---|
| `bin/`, `templates/`, `skills/`, `scripts/`, `examples/` | Pull request, reviewed by maintainer |
| `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `GOVERNANCE.md`, `CITATION.cff` | Maintainer may merge directly to `main` |
| `README.md`, `CHANGELOG.md`, `ROADMAP.md`, `GOALS.md` | Maintainer may merge directly to `main`; contributors via PR |

When in doubt: open a PR.

## Style

- Prefer plain files over hidden state.
- Keep the product inspectable — a researcher should be able to `cat` any file in `.researchloop/` and understand what it is.
- Make the smallest useful loop work first.
- Don't claim results you didn't run. Cite sources.
- Avoid runtime dependencies in the npm package.
- Comments only when the WHY is non-obvious. Don't narrate what the code does.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). Report unacceptable behavior to **shifter040@gmail.com**.

## Citing

If you publish work that used AutoResearch-AI, please cite it via [CITATION.cff](CITATION.cff).
