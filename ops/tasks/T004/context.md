# Context

## Objective

Implement deterministic artifact storage and replay helpers so later evaluation runs can write stable, replayable outputs.

## Relevant Design Decisions

- Run directories must be deterministic from the replay-critical inputs.
- Serialization should stay simple and portable.
- Writes should use same-directory temp files plus atomic replace.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [src/pufopt/storage/io.py](/Users/tomas/code/pufs/src/pufopt/storage/io.py)
- [src/pufopt/storage/artifacts.py](/Users/tomas/code/pufs/src/pufopt/storage/artifacts.py)

## Acceptance Criteria

- a run directory can be created deterministically
- all major objects can be serialized and reloaded
- seeds and config references are always written
- artifact writes are atomic enough to avoid partial-success confusion

## Non-Goals

- no evaluator logic yet
- no frontier persistence policy yet
- no report rendering yet

## Open Risks

- path drift between documented artifacts and actual helpers
- missing replay metadata that later tasks need

