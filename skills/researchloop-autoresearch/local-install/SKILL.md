---
name: researchloop-local-install
description: Use when you need the shortest local package artifact handoff string or smoke-test command for ResearchLoop in a separate agent with no source-repo context.
---

# Local Package

Use this when another agent is on the same machine and should see ResearchLoop only as a local npm package artifact, not as this source repository.

Copy this to the other agent:

```text
/Users/vukrosic/AI Science Projects/testing-research-loop/researchloop-0.3.0.tgz Act as an automated AI researcher. This package contains the tools and prompts. Follow `templates/prompts/first-contact.md`: only talk to me first, explain my system/GPU/repo in simple language, check whether a baseline exists and where it is documented, and wait for approval before init, training, baselines, sweeps, or experiments.
```

If the agent needs to smoke-test the package as a fresh npm install, give it only this:

```bash
TARBALL="/Users/vukrosic/AI Science Projects/testing-research-loop/researchloop-0.3.0.tgz"
npm install -g "$TARBALL"
researchloop --help
```

Do not tell the separate agent to inspect the ResearchLoop source checkout unless the task is specifically to develop ResearchLoop itself.
