# Context

## Objective

Create the minimal Python package skeleton required to start implementation of the auto-optimizer.

## Relevant Design Decisions

- The package name is `pufopt`.
- The top-level entry point is `python -m pufopt.cli`.
- The repo layout should follow the target structure in [README.md](/Users/tomas/code/pufs/README.md).
- This task must not implement system logic beyond the skeleton.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md)
- [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md)

## Acceptance Criteria

- `python -m pufopt.cli --help` resolves
- the package installs in editable mode
- empty modules import without side effects

## Non-Goals

- no evaluator logic
- no attacks
- no scoring
- no optimizer loop

## Open Risks

- introducing structure that later blocks the shared type system
- adding too much code before schema and artifact contracts exist
