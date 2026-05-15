# Example - llm-research-kit

Local repo:

`/Users/vukrosic/my-life/research-repos/llm-research-kit`

## Inspect

```bash
researchloop inspect --dir /Users/vukrosic/my-life/research-repos/llm-research-kit
```

Detected adapters:

- generic
- pytorch
- huggingface
- llm-research-kit

## Check Environment

```bash
researchloop doctor \
  --dir /Users/vukrosic/my-life/research-repos/llm-research-kit \
  --python /Users/vukrosic/miniconda3/bin/python3
```

Result:

- torch 2.8.0
- CUDA false
- MPS true

## Record A Run

```bash
researchloop record \
  --dir /Users/vukrosic/my-life/research-repos/llm-research-kit \
  --id mac-e2e-002 \
  --status complete \
  --metric val_loss=4.415755748748779 \
  --metric tokens_seen=128 \
  --note "Tiny synthetic MacBook MPS smoke run"
```

## Report

```bash
researchloop report --dir /Users/vukrosic/my-life/research-repos/llm-research-kit
```

Expected summary:

- runs: 2
- complete: 2
- parse errors: 0
