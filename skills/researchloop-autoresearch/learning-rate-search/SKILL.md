---
name: researchloop-learning-rate-search
description: Use when the main question is which learning rate works best for the current baseline or architecture.
---

# Learning Rate Search

Read `../references/search-playbook.md`.

Use this skill when you only need a learning-rate sweep.

- test a small LR grid around the current baseline
- keep every other variable fixed
- compare on the real target metric
- promote only the LR that is stable and reproducible

