# Hyperparameter Optimization Playbook

Your goal is to test the cheapest high-signal hyperparameter changes first.

Use this order:

1. Establish the current baseline exactly as it exists.
2. Sweep learning rate before changing architecture.
3. Hold data, sequence length, batch size, and evaluation constant.
4. Change one knob at a time.
5. Record every run in `.researchloop/scratchpad/runs.jsonl`.

Useful hyperparameters to try:

- `muon_lr`
- `adamw_lr`
- `warmup_ratio`
- `weight_decay`
- `dropout`
- `grad_clip`
- `activation_variant`
- `activation_slope`

For each candidate:

- state the hypothesis
- define the kill criterion
- run the smallest proof that can fail or improve
- compare against baseline
- only keep wins that are reproducible

Do not stack multiple changes in the first pass.
