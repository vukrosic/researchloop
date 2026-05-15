# ResearchLoop Getting Started

ResearchLoop is an open source npm package that helps an AI agent run a disciplined research loop inside a machine learning repo.

The shortest way to think about it:

- you install the CLI
- you point it at a repo
- it creates a durable `.researchloop/` workspace
- your AI agent uses that workspace to plan, run, compare, and record experiments

## 1. Install

From your own machine:

```bash
npm install -g researchloop
```

For local development from this repo:

```bash
cd /Users/vukrosic/my-life/researchloop
npm link
researchloop --help
```

If you want to hand this to an AI agent, the simplest instruction is:

```text
Install ResearchLoop, initialize the repo, inspect the project, then use the generated prompt to start the research loop.
```

## 2. Initialize a repo

Run this inside a blank folder or inside an existing ML repo:

```bash
researchloop init --agent codex
```

That creates:

```text
.researchloop/
  AGENTS.md
  goal.md
  plan.md
  repo-profile.json
  scratchpad/
    THREAD.md
    runs.jsonl
    ideas/
    papers/
    variants/
    sweeps/
```

If you want the agent-specific file for another tool, use:

```bash
researchloop init --agent claude-code
researchloop init --agent hermes
researchloop init --agent cursor
```

## 3. Set the research goal

Tell ResearchLoop what the agent should optimize:

```bash
researchloop goal "lower validation loss"
```

You can also add structure:

```bash
researchloop goal "lower validation loss" --metric val_loss --direction lower
```

That saves the objective into `.researchloop/goal.md`, which the agent and the prompt command can read later.

## 4. Generate experiment ideas

```bash
researchloop idea --write
```

This prints a ranked list of small experiments for the current repo shape. For `llm-research-kit`, that usually means baseline checks, learning-rate sweeps, and tiny architecture changes. For a generic repo, it starts with finding the baseline and metric plumbing.

## 5. Inspect the repo

```bash
researchloop inspect
```

This writes a repo profile into `.researchloop/repo-profile.json` and helps the agent understand:

- possible training files
- possible eval files
- config files
- log folders
- likely adapters

## 6. Generate the agent prompt

```bash
researchloop prompt --agent codex
```

Paste the output into your AI agent.

You can also attach a focused playbook:

```bash
researchloop prompt --agent codex --focus hyperparameters
researchloop prompt --agent codex --focus architecture
researchloop prompt --agent codex --focus attention
```

That prompt tells the agent to:

- read the `.researchloop/` files
- establish a baseline
- propose small experiments
- record runs
- compare results
- keep the loop moving

You can still pass `--goal` for a one-off override, but the normal flow is to save the goal once and let the prompt command read it back.

If you want the prompt to narrow in on a family of experiments, use one of the built-in focus playbooks:

- `hyperparameters`
- `architecture`
- `attention`

## 7. Record and compare runs

After a run finishes:

```bash
researchloop record --id first-run --status complete --metric val_loss=2.31 --note "first logged experiment"
```

To compare runs:

```bash
researchloop compare --metric val_loss --direction lower
```

For metrics where higher is better:

```bash
researchloop compare --metric accuracy --direction higher
```

Then summarize the current state:

```bash
researchloop report
```

## 8. Open the dashboard

Serve a local dashboard for the current repo:

```bash
researchloop dashboard
```

Then open the localhost URL it prints. The dashboard reads the repo's `.researchloop/` files and shows:

- the saved goal
- the run ledger
- the best run so far
- the latest run
- a small trend chart for the main metric

It does not need accounts or auth because it stays on your machine.

## 9. Test the setup before you trust it

Run the local checks from this repo:

```bash
npm run smoke
npm run test:compare
npm run test:setup
npm run test:prompts
npm run test:site
npm run smoke:e2e
```

These checks verify that:

- the CLI starts
- the setup flow works in a blank folder
- `compare` ranks runs
- prompt templates are clean
- the website copy matches the product
- the end-to-end flow works

## 10. Use it in a real ML repo

Once the basics work, move into a real project:

```bash
cd /path/to/your/ml-repo
researchloop init --agent codex
researchloop inspect
researchloop prompt --agent codex --goal "improve validation loss"
```

Then give the prompt to your AI agent and let it run the loop.

ResearchLoop is not trying to magically solve the model for you. It gives the agent the operating system for research: goals, baseline, logs, comparison, and continuation.

## 11. Publish to npm

The package is published to the public npm registry at [npmjs.com](https://www.npmjs.com/).

Before publishing:

```bash
npm login
npm whoami
npm pack --dry-run
```

Make sure the package name is available and the contents look right.

For this repo, the package name is currently `researchloop` in `package.json`. If that name is available in your npm account, publish with:

```bash
npm publish
```

If you later switch to a scoped package like `@yourname/researchloop`, publish with:

```bash
npm publish --access public
```

Common release flow:

```bash
npm version patch
git push --follow-tags
npm publish
```

Typical release checklist:

1. run the local tests
2. check `npm pack --dry-run`
3. bump the version
4. publish to npm
5. update the website and README if the usage changed

## 12. Where users install it from

Users install it from the npm registry with:

```bash
npm install -g researchloop
```

If they prefer local use inside one repo:

```bash
npm install researchloop
```

Then they run the CLI from that environment.

## 13. The one-line handoff to an AI agent

If you want the shortest possible instruction for Codex, Claude Code, Hermes, or a similar agent, give it this:

```text
Use ResearchLoop: run init, inspect the repo, read .researchloop/AGENTS.md and goal.md, establish the baseline, then run small experiments, record results, compare runs, and keep the research loop moving.
```
