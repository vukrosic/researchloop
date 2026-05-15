# Hyperparameter Optimization Playbook

Your goal is to test one history-backed hyperparameter change at a time, not to default to a sweep.

Use this order:

1. Read the repo's run history first and confirm the current baseline exactly as it exists.
2. If the history suggests tuning is the bottleneck, change one knob at a time.
3. Keep data, sequence length, batch size, and evaluation constant.
4. Prefer the knob the history points to instead of starting with learning rate by default.
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
