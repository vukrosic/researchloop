# Attention Optimization Playbook

Your goal is to test attention-related changes while keeping the rest of the loop stable.

Use this order:

1. Freeze the baseline model and metric.
2. Change one attention-related setting at a time.
3. Keep data, optimizer, and evaluation fixed.
4. Measure the effect quickly.
5. Re-run any promising result before calling it a win.

Useful attention knobs:

- `n_heads`
- `n_kv_heads`
- RoPE sequence length
- attention dropout
- `compile_model` only when backend supports it

Suggested first experiments:

- compare fewer KV heads vs more KV heads
- adjust attention dropout if overfitting appears
- keep RoPE length fixed unless the dataset truly requires a change

If the repo is on a MacBook, stay in the backend that actually works locally and do not force CUDA-only paths.
