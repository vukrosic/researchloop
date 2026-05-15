# Hyperparameters Playbook

Use this when the likely next win is a cheap tuning change.

Try one family at a time:

- learning rate
- warmup
- optimizer
- weight decay
- batch size
- gradient clipping

Rules:

- keep architecture fixed
- keep the dataset fixed
- keep the metric fixed
- sweep only a few values
- record every run

Kill the family quickly if the curve is flat.
