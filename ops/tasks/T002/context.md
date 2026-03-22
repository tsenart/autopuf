# Context

## Objective

Define the shared type and protocol layer that the loader, evaluator, attack, scoring, and formal plumbing tasks will depend on.

## Relevant Design Decisions

- The system uses Python for execution and Lean as the formal spine.
- The shared type layer must cover both empirical artifacts and formal-claim metadata.
- The contracts should stay lightweight and explicit at this stage.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [AGENTS.md](/Users/tomas/code/pufs/AGENTS.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [src/pufopt/types.py](/Users/tomas/code/pufs/src/pufopt/types.py)

## Acceptance Criteria

- types exist for CandidateSpec, WorldSpec, AttackSpec, EvaluationResult, AttackResult, ScoreCard, FrontierEntry, PlanDecision, FormalClaimSpec, and ProofStatus
- attack, evaluator, candidate, and world protocols are defined
- mypy-friendly type hints exist for public interfaces

## Non-Goals

- no YAML parsing yet
- no candidate or world loading logic yet
- no scoring implementation yet

## Open Risks

- adding fields that later force unnecessary churn across the evaluator pipeline
- failing to represent proof-status and formal-claim linkage clearly enough

