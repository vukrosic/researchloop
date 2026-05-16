#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
out_dir="$root/researchloop-dev/fixtures/packages"

mkdir -p "$out_dir"

tarball="$(
  cd "$root"
  npm pack --pack-destination "$out_dir" --json | node -e 'const fs=require("node:fs"); const text=fs.readFileSync(0,"utf8"); const data=JSON.parse(text); process.stdout.write(data[0].filename);'
)"

printf '%s/%s\n' "$out_dir" "$tarball"
