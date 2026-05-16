# Search Playbook

Use this for hyperparameter, learning-rate, optimizer, schedule, batch-size, weight-decay, and warmup search.

1. Change one knob family at a time.
2. Pick a narrow grid or small candidate set.
3. Prefer the cheapest valid run that can reject the bad options.
4. Log the grid, seed, and metric for each run.
5. Stop when the curve clearly flattens, regresses, or reproduces a win.

