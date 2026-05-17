# Governance

AutoResearch-AI is open source software built in the open. This document explains who decides what, how decisions get made, and how that can change over time.

## Current state (pre-1.0)

The project has **one maintainer**: [Vuk Rosic](https://github.com/vukrosic) (shifter040@gmail.com). The maintainer:

- merges pull requests
- triages issues and labels them
- cuts releases and publishes to npm
- decides the roadmap and what lands in [GOALS.md](GOALS.md)
- enforces the [Code of Conduct](CODE_OF_CONDUCT.md)
- handles security disclosures per [SECURITY.md](SECURITY.md)

This is BDFL-style governance, appropriate for a young project finding its shape. It is **not** the long-term plan.

## How decisions are made

| Decision type | Who decides | How it's communicated |
|---|---|---|
| Bug fix, small feature, doc edit | PR author + maintainer | Inline review on the PR |
| New `G##` goal, scope change | Maintainer | Edit to [GOALS.md](GOALS.md) (visible in git history) |
| Roadmap shift, deprecation, breaking CLI change | Maintainer, with discussion | [ROADMAP.md](ROADMAP.md) update + [CHANGELOG.md](CHANGELOG.md) entry; major changes get a GitHub Discussion first |
| Code of Conduct enforcement | Maintainer | Private to the reporter; sanctions are public when they involve removal from project spaces |
| Security fix | Maintainer | Coordinated disclosure per [SECURITY.md](SECURITY.md) |

For anything contentious, the rule of thumb is: open a [GitHub Discussion](https://github.com/vukrosic/autoresearch-ai/discussions) first, code second. The point is to avoid wasted PR work.

## How to become a co-maintainer

The project will need co-maintainers as it grows. The path:

1. **Contribute consistently.** Multiple merged PRs across more than one area of the codebase (CLI, templates, tests, docs).
2. **Show good judgment in review.** Leave thoughtful, kind reviews on others' PRs.
3. **Be reachable.** Respond to issues / PRs you're involved in within a reasonable window.

When the maintainer thinks the project would be better with you as a co-maintainer, they will reach out and propose it publicly via a Discussion. New co-maintainers get:

- merge rights on PRs
- triage rights on issues
- listed in `MAINTAINERS.md` (created when the second maintainer joins)
- their GitHub handle added to [.github/CODEOWNERS](.github/CODEOWNERS)

Co-maintainers **do not** automatically get npm publish rights or commit-to-main rights — those stay with the project owner until governance is formalized (target: 1.0).

## How this document changes

Changes to this document follow the same rule as scope changes: open a Discussion first, then a PR. Both must be visible for at least 7 days before merging.

## Stepping down

Maintainers may step down at any time by opening a PR to `MAINTAINERS.md` (or to this file, if they're the sole maintainer). If the sole maintainer needs to hand the project off, they will announce it via a pinned Discussion and the project README at least 30 days before transferring ownership.
