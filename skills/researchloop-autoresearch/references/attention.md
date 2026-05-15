# Attention Playbook

Use this when the bottleneck appears to be the attention block itself.

Try one change at a time:

- number of heads
- head dimension
- context length
- causal masking
- rotary or positional setup
- attention implementation

Rules:

- keep the rest of the model fixed
- keep the metric fixed
- capture throughput and loss together
- record the exact config diff

If the change only helps once, do not promote it.
