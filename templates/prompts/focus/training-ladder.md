# Training Ladder Playbook

Use this when the user wants a staged training mode that starts with many short runs, eliminates the worst, and then lengthens the surviving runs over 3-4 rounds total.

Read the repo history first:

- `.researchloop/scratchpad/runs.jsonl`
- `.researchloop/scratchpad/THREAD.md`
- `.researchloop/plan.md`
- recent idea notes in `.researchloop/scratchpad/ideas/`

If `Time Budget` is missing in `.researchloop/plan.md`, ask exactly one question first: "How long do you usually want a typical experiment to run?" Save the answer there and use it to pick the stage lengths.

Work in stages:

1. Stage 1: propose a batch of the smallest cheap runs, around 10-20 min each.
2. Stage 2: keep only the best survivors and lengthen the runs a bit, around 20-60 min.
3. Stage 3: prune again and lengthen the remaining runs again, around 1-3 hr.
4. Stage 4: do a final reproducibility pass on the best 1-2 survivors, around 3-8 hr or overnight if the machine is modest.

Rules:

- offer a realistic time band for each stage
- keep early stages short on modest hardware
- only lengthen after pruning losers
- stop if the gains vanish on reproduction
- do not turn the ladder into a generic sweep
