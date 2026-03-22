# Context

## Objective

Document and validate the minimum local toolchains required for autonomous execution.

## Relevant Design Decisions

- The repo has a Python execution layer and a Lean formal spine.
- Build execution should not start until both toolchains are acknowledged.
- This task is about bootstrap clarity, not implementation of project logic.

## Relevant Files

- [RUNBOOK.md](/Users/tomas/code/pufs/RUNBOOK.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md)

## Acceptance Criteria

- required tools are explicitly listed
- validation commands are explicitly listed
- the build sequence starts from this bootstrap step

## Non-Goals

- no package implementation
- no Lean model implementation
- no schema or evaluator work

## Open Risks

- under-specifying environment expectations for future autonomous runs
- documenting commands that are not actually aligned with later tasks
