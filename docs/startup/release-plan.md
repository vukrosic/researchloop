# Release Plan

ResearchLoop should ship like a living developer tool, not a one-time launch.

The release rhythm should be small and frequent: every few days when there is a real improvement, and never only for ceremony.

## What We Release

Each release should ship one or more of these:

- better onboarding
- a clearer prompt
- a stronger adapter
- a more useful dashboard
- a better experiment command
- a more trustworthy test or log
- a real benchmark or proof on `llm-research-kit`

Do not release vague "startup progress." Release a concrete user-visible change.

## Release Cadence

Use a lightweight cadence:

- `0.1.x` for the first public loop
- prereleases like `0.1.1-beta.1` when the package is moving fast
- full patch releases when the loop and tests are stable

The goal is to make shipping normal. Small releases create trust because users can see momentum.

## GitHub Setup

The GitHub repo should be simple and public:

- default branch protected
- CI required on pull requests
- issue templates for bugs, adapter requests, and user feedback
- labels for `release`, `adapter`, `onboarding`, `docs`, `bug`, `good first issue`
- release drafts enabled
- a changelog or release note file in the repo

The repo should make the product legible to outside users:

- one README
- one getting-started guide
- one roadmap
- one place for startup notes
- one place for competitor notes
- one place for release notes

## Release Process

1. Pick one user-visible improvement.
2. Verify it locally on a clean temp repo.
3. Verify `npm run smoke` and the affected tests.
4. Bump the version.
5. Write a short release note with:
   - what changed
   - why it matters
   - what was tested
   - any limitations
6. Tag the release on GitHub.
7. Publish the npm package.
8. Post the release on X.
9. Ask one or two users to try the new loop.

## Release Note Style

Keep release notes short and concrete.

Good release notes mention:

- the feature name
- the user problem it solves
- the exact command or workflow it improves
- the test or proof that backs it up

Bad release notes talk about "vision" without showing a user-facing change.

## Launch Sequence

The first launch should be:

1. Public GitHub repo for `researchloop`
2. First npm publish
3. Short demo video or screen recording
4. X post announcing the loop
5. 3 to 5 direct messages to PhD students or lab users
6. One public request for feedback

The launch is not finished when the package is published. It is finished when someone else tries the loop and gives usable feedback.

## What To Improve Next

The next improvements should be boring and practical:

- better first-run onboarding
- a more obvious `researchloop goal`
- one more adapter if a user actually needs it
- better `researchloop compare` output
- a richer dashboard view
- a clearer `researchloop idea` output for architecture and hyperparameter sweeps

The first release after launch should focus on removing friction from the first 10 minutes.

