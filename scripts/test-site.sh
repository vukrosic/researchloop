#!/usr/bin/env bash
set -euo pipefail

site="$(curl -s http://localhost:8000/researchloop/docs/site/index.html)"

printf '%s' "$site" | grep -q 'Research Loop - Autonomous AI Research, in one prompt'
printf '%s' "$site" | grep -q 'npm install -g researchloop'
printf '%s' "$site" | grep -q 'Automated AI research.'
printf '%s' "$site" | grep -q 'Humans scope. Agents run.'
printf '%s' "$site" | grep -q 'a pile of agents handle'
printf '%s' "$site" | grep -q 'researchloop dashboard'
printf '%s' "$site" | grep -q 'Local only. No auth. No cloud.'
printf '%s' "$site" | grep -q 'Placeholder'

echo "researchloop test:site passed"
