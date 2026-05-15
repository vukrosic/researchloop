# LLM Research Kit Adapter

Useful files:
- `train_llm.py`
- `configs/llm_config.py`
- `configs/dataset_config.py`
- `training/trainer.py`
- `training/evaluation.py`
- `optimizers/`
- `plots/metrics_*.json`

MacBook mode:
- Use MPS or CPU for smoke tests.
- Keep `torch.compile` disabled outside CUDA.
- Prefer tiny configs for local proof-of-life.

CUDA mode:
- Enable compile and mixed precision when supported.
- Use repeated seeds before claiming wins.
- Run pruning before promoting stacked changes.
