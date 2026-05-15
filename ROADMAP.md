# Roadmap

## Now

- Keep `/Users/vukrosic/my-life/researchloop` as the single repo home.
- Make the npm package useful before adding hosted infrastructure.
- Validate the loop on `llm-research-kit` and one outside repo.
- Talk to PhD students and lab users before expanding adapters.

## MVP

- Install harness with `researchloop init`.
- Inspect repo structure with `researchloop inspect`.
- Generate agent prompts with `researchloop prompt`.
- Check local environment with `researchloop doctor`.
- Summarize run ledger with `researchloop report`.
- Provide templates for Codex, Claude Code, Hermes, Cursor, PyTorch, Hugging Face, and generic repos.

## Done (0.2.0)

- `researchloop run` and `researchloop baseline` execute commands and parse metrics into the ledger.
- `researchloop scan-papers` pulls arXiv abstracts for the goal and writes per-paper notes.
- `researchloop idea` now surfaces paper-derived ideas alongside the adapter playbook.
- Adapter detection no longer false-positives on filename substrings.

## Next Product Work

- `researchloop replay <run-id>` re-executes a stored run and flags reproducibility deltas.
- `researchloop scan-github` for repos with similar training scripts.
- `researchloop promote <run-id>` copies a winning config/diff into `winners/`.
- Public demo repo that shows one full autonomous research loop end to end.

## Startup Work

- Recruit 5 PhD students or independent AI researchers for repo walkthroughs.
- Recruit 2 small-company users with prompt/model/eval optimization pain.
- Ship small releases every few days, with one visible user-facing improvement per release.
- Ship one public demo video showing install to first logged experiment.
- Publish the open source repo when the CLI has one polished loop.
