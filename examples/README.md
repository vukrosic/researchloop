# Examples

Real, copy-paste examples of using AutoResearch-AI against real repos. Each example shows one complete loop:

1. install
2. initialize the harness
3. inspect the target repo
4. generate the agent prompt
5. run or record one experiment
6. report results

## Available examples

| Example | Repo shape | What it demonstrates |
|---|---|---|
| [llm-research-kit.md](llm-research-kit.md) | PyTorch + Hugging Face | End-to-end loop on a tiny LLM training repo: detect adapter, run baseline, log experiment, compare. |

## Fixtures

The [fixtures/](fixtures/) directory contains minimal synthetic repos used by `scripts/test-setup.sh` and other tests. They are not user-facing examples — they exist so the CLI can be tested against blank, partial, and fully-shaped repos without depending on machine-specific state.

## Contributing a new example

Examples are one of the most useful things you can contribute. They become a reviewer's reference, an AI agent's training context, and a user's quickstart all at once.

A good example:

- targets a real, publicly-available repo (link it)
- shows the full loop from install to first logged comparison
- is reproducible — someone with a fresh clone should get the same shape of output
- doesn't depend on a specific GPU or paid API
- includes the actual `cat .researchloop/scratchpad/runs.jsonl` output so readers see what gets logged

Add your example as a new `.md` file in this directory and add a row to the table above. Open a PR following [CONTRIBUTING.md](../CONTRIBUTING.md).
