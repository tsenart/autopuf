# Context

## Objective

Initialize the Lean workspace so `autopuf` has a formal spine from day 0.

## Relevant Design Decisions

- `Mission 1` is still primary: the repo optimizes for evaluator and optimizer utility.
- Lean is the embedded formal track, not the main execution substrate.
- The first Lean goal is structure and claim mapping, not full proofs.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md)
- [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md)

## Acceptance Criteria

- the Lean workspace is initialized
- build instructions are captured in the repo
- the workspace layout supports `Autopuf/Model.lean`, `Autopuf/Games.lean`, `Autopuf/Claims.lean`, and `Autopuf/Bridge.lean`
- the workspace builds from `formal/` with `lake build`

## Non-Goals

- no full protocol proofs yet
- no replacement of the Python execution layer
- no formalization of every candidate family

## Open Risks

- overfitting the formal layout before the bridge contract is settled
- creating a formal hierarchy that is too tightly coupled to one candidate family
