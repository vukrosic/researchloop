# Heat Lens

Heat Lens is a tiny local macOS app for answering a simple question: what is heating my Mac right now?

It shows:

- the current macOS thermal state
- the top CPU-consuming processes
- a small hint for each row so you can spot the likely culprit quickly

Important limitation:

- macOS does not expose a reliable public API for raw package temperature.
- this app uses the public thermal state plus CPU and memory usage as the best practical proxy.

## Build

```bash
cd /Users/vukrosic/my-life/autoresearch-ai/researchloop-dev/mac-heat-lens
./build.sh
```

## Run

```bash
open .build/HeatLens.app
```

## What to look for

- `Nominal` means the machine is comfortable.
- `Warm` means load is starting to build.
- `Hot` means something is likely sitting on the CPU for a while.
- `Critical` means macOS is strongly trying to cool down.

If you see a browser helper, chat helper, or Codex/Claude worker near the top while the thermal state rises, that process is usually the main reason the Mac feels hot.
