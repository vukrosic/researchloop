#!/usr/bin/env bash
set -euo pipefail

base="/Users/vukrosic/AI Science Projects/testing-research-loop"
stamp="$(date +%Y-%m-%dT%H-%M-%S)"
lab="$base/researchloop-onboarding-lab-$stamp"

mkdir -p "$lab"
printf '%s\n' "$lab"
