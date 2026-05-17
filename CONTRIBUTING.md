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

## The claim flow (how to pick work)

AutoResearch-AI uses a numbered-goal slot system to coordinate humans and AI agents working in parallel without stepping on each other.

1. **Browse [GOALS.md](GOALS.md).** Pick a `G##` goal where:
   - no open issue or PR already references it
   - every goal in its `Depends on` line is already merged
   - the `Files owned` line doesn't conflict with work already in flight
   - the effort tag (S / M / L) matches what you can commit to

2. **Claim it.** Open a [Contribute-a-Goal issue](.github/ISSUE_TEMPLATE/contribute-goal.yml) with:
   - the `G##` ID in the title
   - a one-paragraph approach
   - which agent (if any) is writing the code (Codex / Claude / Cursor / Hermes / human)
   - confirmation you've read [AGENTS.md](AGENTS.md) and this file

3. **Wait for the claim to be acknowledged** (typically same-week). The maintainer will label it `claimed` and assign it to you. This prevents two contributors racing the same goal.

4. **Branch from `main`.** Branch naming convention: `g##-short-description` (e.g., `g14-env-capture`).

5. **Implement.** Keep the change focused — one `G##` per PR. Architecture changes need an issue first.

6. **Run tests locally.** `npm test` must be green. If you added or changed CLI behavior, add a `scripts/test-*.sh` for it and wire it into the `test` script in `package.json`.

7. **Open a PR** using the [PR template](.github/PULL_REQUEST_TEMPLATE.md). **Copy every Acceptance line from the `G##` goal into the PR checklist and tick each one.** PRs that skip this get bounced back.

8. **Respond to review.** First-review SLA is ~7 days. Be patient and kind.

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
