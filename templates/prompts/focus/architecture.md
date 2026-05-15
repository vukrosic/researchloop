# Architecture Optimization Playbook

Your goal is to explore small architecture changes without losing the baseline.

Use this order:

1. Read the repo's run history and lock the current baseline and metric.
2. Make one architecture change at a time.
3. Prefer the smallest change that can plausibly matter.
4. Keep data, evaluation, and training loop fixed.
5. Log the exact config diff and the result.

Useful architecture knobs:

- `d_model`
- `n_heads`
- `n_layers`
- `d_ff`
- `n_kv_heads`
- `activation_variant`
- `activation_slope`

Suggested first experiments:

- widen `d_model` slightly
- reduce or increase `n_layers` by one step
- change `n_kv_heads` while keeping `d_model` and `n_heads` consistent
- compare `squared_relu` against `relu` or `leaky_squared_relu`

Do not change architecture and optimizer in the same first-pass experiment unless the goal explicitly requires it.
