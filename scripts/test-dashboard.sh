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
node ./bin/researchloop.js run --dir "$tmpdir" --id run-a --metric val_loss --command "printf 'val_loss=3.20\nval_loss=3.00\nval_loss=2.85\n'" >/tmp/researchloop-dashboard-run-a.log
node ./bin/researchloop.js run --dir "$tmpdir" --id run-b --metric val_loss --command "printf 'val_loss=3.10\nval_loss=2.95\nval_loss=2.70\n'" >/tmp/researchloop-dashboard-run-b.log
node ./bin/researchloop.js run --dir "$tmpdir" --id run-c --metric val_loss --command "printf 'val_loss=2.95\nval_loss=2.80\nval_loss=2.60\n'" >/tmp/researchloop-dashboard-run-c.log

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
printf '%s' "$page" | grep -q 'Loss comparison'
printf '%s' "$page" | grep -q 'Experiments'
printf '%s' "$state" | grep -q '"primaryMetric": "val_loss"'
printf '%s' "$state" | grep -q '"traces"'
printf '%s' "$state" | grep -q '"comparison"'
printf '%s' "$state" | grep -q '"run-c"'
printf '%s' "$state" | grep -q '"metric_history"'
printf '%s' "$state" | grep -q '"val_loss": \['
printf '%s' "$state" | grep -q '3.1'
printf '%s' "$state" | grep -q '2.95'
printf '%s' "$state" | grep -q '2.7'

echo "researchloop test:dashboard passed"
