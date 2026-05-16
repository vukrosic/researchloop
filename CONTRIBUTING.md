# Contributing

Welcome. Keep changes small and real.

## Quick Links

- **Vision:** [`VISION.md`](VISION.md)
- **Docs:** [`docs/getting-started.md`](docs/getting-started.md)
- **Tests (local):** `npm test`
- **Tests (release gate):** `npm run test:release` (adds the packed-tarball install test; slower)

## Good Contributions

- new repo adapters
- better prompt templates
- dashboard and run-logging improvements
- onboarding and first-run fixes
- examples from real research workflows
- regression tests for behavior that has bitten us before

## Before You PR

- run `npm test` and make sure it is green
- keep the change focused (one lane at a time)
- do not claim results you did not run
- open an issue first for large features or architecture changes
- if you change CLI behavior, update or add a `scripts/test-*.sh` for it

## CI

`.github/workflows/ci.yml` runs `npm test` on Node 18 / 20 / 22 against ubuntu-latest and macos-latest for every push and pull request, plus a packed-tarball install job. PRs do not merge until those jobs are green.

## Style

- prefer plain files over hidden state
- keep the product inspectable
- make the smallest useful loop work first
- avoid runtime dependencies in the npm package; the CLI is intentionally zero-dep
