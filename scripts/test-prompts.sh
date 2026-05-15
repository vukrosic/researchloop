#!/usr/bin/env bash
set -euo pipefail

goal="reduce validation loss"

for agent in codex claude-code hermes generic; do
  out="$(node ./bin/researchloop.js prompt --agent "$agent" --goal "$goal")"
  printf '%s' "$out" | grep -q "$goal"
  printf '%s' "$out" | grep -q ".researchloop/AGENTS.md"
  printf '%s' "$out" | grep -q ".researchloop/plan.md"
  case "$agent" in
    codex)
      printf '%s' "$out" | grep -q "Never claim a result"
      ;;
    claude-code)
      printf '%s' "$out" | grep -q "Do not stop just because one experiment is exhausted"
      ;;
    hermes)
      printf '%s' "$out" | grep -q "Coordinate the research loop"
      ;;
    generic)
      printf '%s' "$out" | grep -q "Do not claim results without evidence"
      ;;
  esac
  if printf '%s' "$out" | grep -q '{{GOAL}}'; then
    echo "prompt template still has GOAL placeholder for $agent" >&2
    exit 1
  fi
done

echo "researchloop test:prompts passed"
