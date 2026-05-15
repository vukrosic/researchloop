# Contributing

ResearchLoop is meant to be useful to researchers first.

Good contributions:

- new repo adapters
- better agent prompt templates
- run ledger improvements
- examples from real research workflows
- bug reports from PhD students, labs, and independent researchers

Before adding a large feature, open an issue or write a short proposal in `docs/research/ideas/`.

## Local Development

```bash
npm link
npm run smoke
npm run smoke:e2e
```

## Design Rules

- Keep the core open source and easy to inspect.
- Prefer plain files over hidden state.
- Never claim an experiment result that was not actually run.
- Make the smallest useful loop work before expanding scope.
