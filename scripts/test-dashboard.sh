#!/usr/bin/env bash
set -euo pipefail

tmpdir="$(mktemp -d)"
logfile="$(mktemp)"
pid=""

cleanup() {
  if [[ -n "$pid" ]]; then
    kill "$pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$tmpdir"
  rm -f "$logfile"
}
trap cleanup EXIT

node ./bin/researchloop.js init --agent codex --dir "$tmpdir" >/tmp/researchloop-dashboard-init.log
node ./bin/researchloop.js goal --dir "$tmpdir" "lower validation loss" --metric val_loss --direction lower >/tmp/researchloop-dashboard-goal.log
node ./bin/researchloop.js record --dir "$tmpdir" --id run-a --status complete --metric val_loss=3.20 --metric tokens_seen=64 --note "first dashboard run" >/tmp/researchloop-dashboard-run-a.log
node ./bin/researchloop.js record --dir "$tmpdir" --id run-b --status complete --metric val_loss=2.90 --metric tokens_seen=128 --note "second dashboard run" >/tmp/researchloop-dashboard-run-b.log

node ./bin/researchloop.js dashboard --dir "$tmpdir" --port 0 >"$logfile" 2>&1 &
pid=$!

url=""
for _ in $(seq 1 80); do
  if [[ -s "$logfile" ]]; then
    url="$(grep -o 'http://127.0.0.1:[0-9]\+' "$logfile" | tail -n 1 || true)"
    if [[ -n "$url" ]]; then
      break
    fi
  fi
  sleep 0.1
done

if [[ -z "$url" ]]; then
  echo "dashboard did not start" >&2
  cat "$logfile" >&2 || true
  exit 1
fi

state="$(curl -s "$url/api/state")"
page="$(curl -s "$url/")"

printf '%s' "$page" | grep -q 'ResearchLoop Dashboard'
printf '%s' "$page" | grep -q 'Local experiment tracking'
printf '%s' "$state" | grep -q '"primaryMetric": "val_loss"'
printf '%s' "$state" | grep -q '"bestRun"'
printf '%s' "$state" | grep -q '"run-b"'
printf '%s' "$state" | grep -q '"val_loss": 2.9'

echo "researchloop test:dashboard passed"
