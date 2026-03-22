# Formal Workspace

This directory contains the Lean workspace for the `autopuf` formal spine.

## Build

```bash
cd formal
lake build
```

## Layout

- `Main.lean`: minimal executable entry point
- `Autopuf.lean`: library import surface
- `Autopuf/Model.lean`: abstract protocol objects
- `Autopuf/Games.lean`: security-game and game-instance structures
- `Autopuf/Claims.lean`: proof-status vocabulary and formal claims
- `Autopuf/Bridge.lean`: bindings between empirical runs and formal claims
