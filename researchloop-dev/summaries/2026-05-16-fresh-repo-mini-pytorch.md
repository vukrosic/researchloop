# Fresh Repo Onboarding Summary

- Scenario: fresh minimal PyTorch repo copied into a clean lab folder and exercised with the current local ResearchLoop build.
- What the agent did: `init`, `inspect`, `prompt`, `goal`, a second `prompt`, and `idea`.
- What failed: nothing obvious in the CLI flow itself. I did not run a separate spawned mini-agent in this pass, so this is a CLI-level onboarding proof rather than a full interactive LLM transcript.
- What should change next: if we want a true end-to-end LLM onboarding gate, add a small scripted harness that feeds the generated prompt into a fresh mini-agent and saves its raw replies alongside this CLI proof.
- Evidence: the prompt asked for one time-budget question, told the agent to use history first, and told it not to default to generic sweeps.
