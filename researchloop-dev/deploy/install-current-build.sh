#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
tarball="$("$root/researchloop-dev/deploy/pack-current-build.sh")"

npm install -g "$tarball"
