---
name: researchloop-autoresearch
description: Use when doing autonomous AI research in a machine learning repo with ResearchLoop, especially when choosing experiments, preserving baselines, or logging run results.
---

# ResearchLoop Autoresearch

You are the research agent inside a repo that uses ResearchLoop.

Before changing code, read:

- `.researchloop/goal.md`
- `.researchloop/plan.md`
- `.researchloop/AGENTS.md`
- `.researchloop/scratchpad/THREAD.md`
- `.researchloop/repo-profile.json`

If `Time Budget` is missing in `.researchloop/plan.md`, ask exactly one question first: "How long do you usually want a typical experiment to run?" Save the answer in the plan and use it to shape experiment length.

Then work in this order:

1. Confirm the baseline.
2. Propose the smallest informative next experiment.
3. Change one thing at a time.
4. Run the smallest valid check.
5. Record the result.
6. Compare against the baseline.
7. Prune weak branches quickly.
8. Continue until the goal is met or the family is exhausted.

Use the ResearchLoop commands as the control plane:

- `researchloop goal`
- `researchloop inspect`
- `researchloop prompt`
- `researchloop idea`
- `researchloop record`
- `researchloop compare`
- `researchloop report`

Do not claim improvement without a recorded run.
Do not stack architecture changes before the baseline is stable.
Do not let the loop drift away from the saved goal.

## When to use playbooks

If the task is clearly one of these families, load the matching reference:

- hyperparameters -> `references/hyperparameters.md`
- architecture -> `references/architecture.md`
- attention -> `references/attention.md`
