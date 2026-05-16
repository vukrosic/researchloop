# LLM Kit Optimizer Once

## Summary

One disposable ResearchLoop probe ran against `llm-research-kit` on a detached worktree, then the worktree was removed and the live checkout was verified unchanged.

## Run

- Run id: `llm-kit-optimizer-once-20260517-050920`
- Target repo: `/Users/vukrosic/my-life/research-repos/llm-research-kit`
- Base commit: `8b9aeb960824ce46950193c5eebd47a3c2eedccf`
- Worktree: `/Users/vukrosic/my-life/research-repos/.researchloop-runs/llm-kit-optimizer-once-20260517-050920`
- Change label: `muon_ns_steps_3_mps_safe_compile`

## Timing

- Start: `2026-05-17T05:26:43.131309+08:00`
- Train cutoff: `2026-05-17T05:26:48.134504+08:00`
- End: `2026-05-17T05:26:48.250011+08:00`
- Duration: `5.119s`
- Steps: `384`

## Results

- Train loss: `3.402402877807617`
- Validation loss: `6.026325464248657`
- Validation accuracy: `0.012096774193548387`
- Validation perplexity: `414.19027274616855`
- Device: `mps`

## Reset Proof

- Before status file: `/Users/vukrosic/my-life/research-repos/.researchloop-runs/llm-kit-optimizer-once-20260517-050920.before-status.txt`
- After status file: `/Users/vukrosic/my-life/research-repos/.researchloop-runs/llm-kit-optimizer-once-20260517-050920.after-status.txt`
- Result: empty diff

## Notes

The disposable worktree used a Muon variant with `ns_steps=3` and a CUDA-only compile guard so the probe would run safely on MPS. After the probe, the worktree was reset and removed, and the live checkout stayed unchanged.
