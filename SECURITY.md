# Security Policy

## Supported versions

Only the latest `0.x` release on [npm](https://www.npmjs.com/package/autoresearch-ai) receives security fixes. Older versions are not patched. AutoResearch-AI is pre-1.0 and the surface evolves; pin to a specific version in production use and upgrade on a regular cadence.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **shifter040@gmail.com** with:

- a description of the issue
- minimal reproduction steps
- the version of `autoresearch-ai`, Node, and OS you observed it on
- impact (what an attacker can read, write, run, exfiltrate, or DOS)

You should expect:

- an acknowledgement within 7 days
- a triage decision (accepted / needs more info / out of scope) within 14 days
- a fix or mitigation plan for accepted issues, with credit to you in the release notes if you want it

## Scope

In scope:

- The published `autoresearch-ai` npm package and the CLI it installs.
- Files and scripts the CLI writes into a target repo's `.researchloop/` directory.
- Prompts and templates that instruct downstream agents to execute commands.
- The local dashboard server (`autoresearch dashboard`).

Out of scope:

- Behavior of third-party coding agents (Codex, Claude Code, Cursor, Hermes, etc.) themselves.
- Vulnerabilities in user-written training scripts, model weights, or data.
- Issues that require already-compromised local credentials or a malicious operator on the same machine.
- Anything under `competitors/` — those are research notes, not shipped product.

## What we care about most

- **Command injection / arbitrary code execution** via CLI arguments, `runs.jsonl`, prompts, or template files.
- **Path traversal** when the CLI reads / writes inside a target repo.
- **Unauthenticated network exposure** of the local dashboard (it should default to loopback).
- **Prompt-injection vectors** that cause an agent to run destructive commands the user did not approve.
- **Supply-chain** issues: tarball contents, install scripts, declared dependencies.

Thanks for helping keep AutoResearch-AI safe to install.
