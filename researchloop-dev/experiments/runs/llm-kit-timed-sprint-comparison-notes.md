# LLM Kit Timed Sprint Comparison Notes

This note documents the two saved `llm-research-kit` timed sprint runs and the comparison view that overlays them.

## Saved runs

- `llm-kit-timed-sprint-20260517-061853`
- `llm-kit-timed-sprint-html-20260517-062734`

Both runs are stored permanently in this folder with their markdown reports and JSONL ledgers.

## Why the comparison graph was confusing

The comparison page is a visual aid, but the canonical data are the JSONL rows and markdown summaries.

The running-minimum curve should be read as a monotonic best-so-far metric:

- it can stay flat
- it can step downward when a better validation loss appears
- it should not increase numerically within a run

If the visual feels backwards, trust the ledger rows and the run summary table first. The underlying validation-loss values for both runs improved to their best-so-far points as expected.

## Key values

- First run best validation loss: `10.19455087184906`
- Second run best validation loss: `6.162621438503265`
- Both runs used `GPT-5.4 Mini`

## Permanent artifacts

- [`llm-kit-timed-sprint-20260517-061853.md`](./llm-kit-timed-sprint-20260517-061853.md)
- [`llm-kit-timed-sprint-20260517-061853.jsonl`](./llm-kit-timed-sprint-20260517-061853.jsonl)
- [`llm-kit-timed-sprint-html-20260517-062734.md`](./llm-kit-timed-sprint-html-20260517-062734.md)
- [`llm-kit-timed-sprint-html-20260517-062734.html`](./llm-kit-timed-sprint-html-20260517-062734.html)
- [`llm-kit-timed-sprint-html-20260517-062734.jsonl`](./llm-kit-timed-sprint-html-20260517-062734.jsonl)
- [`llm-kit-timed-sprint-comparison.html`](./llm-kit-timed-sprint-comparison.html)
