#!/usr/bin/env bash
# codex-swarm.sh — open a grid of Terminal.app windows on macOS, each running `codex`.
#
# macOS only. Requires Terminal.app and the codex CLI on PATH.
# First run will prompt for Automation permission to control Terminal.

set -euo pipefail

cols=3
rows=2
cmd="codex"
cwd=""
bottom_pad=80

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cols) cols="$2"; shift 2 ;;
    --rows) rows="$2"; shift 2 ;;
    --cmd) cmd="$2"; shift 2 ;;
    --cwd) cwd="$2"; shift 2 ;;
    --bottom-pad) bottom_pad="$2"; shift 2 ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [options]

Opens a grid of Terminal.app windows, each running \`codex\` (or another command).

Options:
  --cols N           Columns in the grid (default: $cols)
  --rows M           Rows in the grid (default: $rows)
  --cmd "STR"        Command to run in each window (default: "$cmd")
  --cwd /path        Working directory for each window
  --bottom-pad N     Pixels reserved at the bottom for the dock (default: $bottom_pad)
  -h, --help         Show this help

Examples:
  $(basename "$0")                              # 3x2 grid of codex windows
  $(basename "$0") --cols 2 --rows 2            # 2x2 grid
  $(basename "$0") --cmd "codex --resume"       # custom command per window
EOF
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

count=$(( cols * rows ))

osascript - "$cmd" "$cwd" "$cols" "$rows" "$count" "$bottom_pad" <<'APPLESCRIPT'
on run argv
  set theCmd to item 1 of argv
  set theCwd to item 2 of argv
  set numCols to (item 3 of argv) as integer
  set numRows to (item 4 of argv) as integer
  set numCount to (item 5 of argv) as integer
  set bottomPad to (item 6 of argv) as integer

  tell application "Finder"
    set screenBounds to bounds of window of desktop
  end tell
  set screenLeft to item 1 of screenBounds
  set screenTop to item 2 of screenBounds
  set screenRight to item 3 of screenBounds
  set screenBottom to item 4 of screenBounds

  set usableWidth to screenRight - screenLeft
  set usableHeight to (screenBottom - screenTop) - bottomPad

  set winWidth to usableWidth div numCols
  set winHeight to usableHeight div numRows

  tell application "Terminal"
    activate
    repeat with i from 0 to (numCount - 1)
      set col to i mod numCols
      set rowIdx to i div numCols
      set x1 to screenLeft + (col * winWidth)
      set y1 to screenTop + (rowIdx * winHeight)
      set x2 to x1 + winWidth
      set y2 to y1 + winHeight

      if theCwd is "" then
        set fullCmd to theCmd
      else
        set fullCmd to "cd " & quoted form of theCwd & " && " & theCmd
      end if

      do script fullCmd
      delay 0.15
      set bounds of front window to {x1, y1, x2, y2}
    end repeat
  end tell
end run
APPLESCRIPT

echo "Launched $count Terminal windows in ${cols}x${rows} grid running: $cmd"
