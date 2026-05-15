# Architecture Playbook

Use this when tuning model shape or layer structure.

Try one change at a time:

- width
- depth
- feedforward size
- number of heads
- embedding size
- normalization placement

Rules:

- do not stack multiple architecture changes in the first pass
- keep the optimizer and schedule fixed
- compare against a reproduced baseline
- re-run the best candidate with a second seed

If the win does not reproduce, drop it.
