# Hugging Face Trainer Adapter

Useful files:
- `training_args`
- `Trainer`
- `accelerate`
- `config.json`
- dataset loading scripts
- metric callbacks

Default first experiments:
1. Confirm a tiny run works.
2. Identify evaluation metric and save path.
3. Sweep learning rate and schedule before model architecture.
4. Preserve dataset and split unless the goal allows data changes.
