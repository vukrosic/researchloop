# Releasing

Reference for cutting a new release of `autoresearch-ai` to npm. Maintainer-only.

## Versioning

We follow [Semantic Versioning](https://semver.org/), with pre-1.0 conventions:

- `0.X.0` (minor bump) — new features, behavior changes, or breaking changes to the CLI surface. **Pre-1.0, breaking changes ship as minor bumps; this is documented in [README.md](README.md) and [SECURITY.md](SECURITY.md).**
- `0.X.Y` (patch bump) — bug fixes, doc-only changes, dependency updates that don't change behavior.
- `1.0.0` — first stable release. CLI surface frozen except via deprecation cycle. Not scheduled yet.

When in doubt: bump minor.

## Pre-release checklist

Before running `npm publish`, verify:

- [ ] `main` is green in CI for the commit you're about to release.
- [ ] [CHANGELOG.md](CHANGELOG.md) has a new section for this version with: added / changed / fixed / removed lines and the release date.
- [ ] [ROADMAP.md](ROADMAP.md) `Done (X.Y.Z)` section reflects what shipped.
- [ ] [package.json](package.json) `version` field is bumped.
- [ ] `npm run test:release` is green locally. This runs the full suite plus the packed-tarball install test, which catches `files` whitelist regressions and missing assets.
- [ ] You ran `npm pack --dry-run` and skimmed the file list — nothing under `researchloop-dev/`, `docs/research/`, `docs/startup/`, `competitors/`, or `examples/fixtures/` should appear.
- [ ] `README.md` is consistent with the actual CLI surface as of this version.
- [ ] If any prompts or templates changed, the matching `scripts/test-*.sh` was updated.

## Cut the release

```bash
# 1. Final local check
git checkout main
git pull
npm run test:release

# 2. Bump version (commits + tags automatically)
npm version minor    # or: patch / major
# This creates: commit "0.X.Y" + tag "v0.X.Y"

# 3. Push the commit and the tag
git push --follow-tags

# 4. Publish to npm
npm publish

# 5. Sanity-check the published artifact in an isolated prefix
mkdir -p /tmp/autoresearch-verify && cd /tmp/autoresearch-verify
npm init -y >/dev/null
npm install autoresearch-ai@latest
./node_modules/.bin/autoresearch --version    # should match the version you just published
./node_modules/.bin/autoresearch --help
```

## After publishing

- [ ] Draft a GitHub Release pointing at the new tag. Body = the new CHANGELOG section.
- [ ] If the release fixes a security issue covered by [SECURITY.md](SECURITY.md), credit the reporter (if they consented) in the release notes.
- [ ] Close any GitHub Issues / Discussions resolved by this release.
- [ ] Bump the `Done (X.Y.Z)` section in [ROADMAP.md](ROADMAP.md) if you hadn't yet, and move the new `Now` items into the next planning window.

## If something goes wrong

- **Published broken version.** Do not unpublish if it's been more than ~5 minutes — npm forbids re-publishing the same version. Instead, immediately publish a patch (`0.X.Y+1`) with the fix, and add a deprecation notice to the broken version:
  ```bash
  npm deprecate autoresearch-ai@0.X.Y "broken release, please upgrade to 0.X.Y+1"
  ```
- **Forgot to bump version.** `npm publish` will fail with `403 Forbidden — cannot publish over previously published version`. Bump and retry.
- **Tarball includes files it shouldn't.** Fix `files` in `package.json`, bump patch, republish, deprecate the broken version.

## npm publish access

Today only the maintainer (npm user `vukrosic`) has publish rights. When the project gains co-maintainers (see [GOVERNANCE.md](GOVERNANCE.md)), publish rights stay with the project owner until governance is formalized.
