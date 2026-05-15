# PyTorch Adapter

Useful files:
- `train.py`
- `eval.py`
- `configs/`
- `requirements.txt`
- `pyproject.toml`
- `checkpoints/`
- `logs/`

Default first experiments:
1. Run a one-batch smoke test.
2. Establish baseline metric parsing.
3. Try one optimizer or schedule ablation.
4. Reproduce any apparent win.

Common knobs:
- optimizer
- learning rate
- weight decay
- schedule
- warmup
- precision
- initialization
- gradient clipping
