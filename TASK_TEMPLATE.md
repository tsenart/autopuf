# TASK TEMPLATE

This file defines the concrete task contract for autonomous execution.

Every task in [TASKS.md](/Users/tomas/code/pufs/TASKS.md) should be instantiated as a machine-readable manifest plus a small context pack.

## Required Files Per Task

Each task should live under:

```text
ops/tasks/<task_id>/
├── task.yaml
├── context.md
├── plan.md
├── activity.log
├── verification.json
├── red_review.md
├── reproduction_report.md
└── promotion.yaml
```

At minimum, `task.yaml` must exist before execution starts.

## `task.yaml` Contract

Use this shape:

```yaml
id: T031
title: Implement modeling attack
status: ready
phase: Phase 3
objective: >
  Implement a modeling attack that learns candidate response behavior well enough
  to estimate impersonation success under a declared attack budget.
depends_on:
  - T030
  - T020
inputs:
  design_docs:
    - README.md
    - AGENTS.md
    - TASKS.md
    - WORKFLOWS.md
    - RUNBOOK.md
  code_paths:
    - src/pufopt/attacks/base.py
    - src/pufopt/evaluators/honest.py
  formal_paths:
    - formal/Autopuf/Model.lean
allowed_write_paths:
  - src/pufopt/attacks/modeling.py
  - tests/
required_outputs:
  - src/pufopt/attacks/modeling.py
  - tests/test_modeling_attack.py
acceptance_criteria:
  - supports at least three simple model families
  - outputs best attack found under budget
  - writes attack trace artifact
required_commands:
  - pytest tests/test_modeling_attack.py
  - python -m pufopt.cli attack --candidate candidates/foo.yaml --world configs/worlds/bar.yaml --attack modeling
artifacts:
  - verification.json
  - red_review.md
  - reproduction_report.md
risks:
  - overfitting toy fixtures without generalizing to interface contract
  - hidden non-determinism in model training
escalation_triggers:
  - attack interface in base.py is too weak for implementation
  - honest evaluator does not expose sufficient features
formal_claim_id: null
proof_status_required: false
owner_role: Builder
reviewer_role: Red Reviewer
promoter_role: Integrator
```

## Field Meanings

- `id`: must match a task in [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- `title`: short human-readable name
- `status`: one of the status values in [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md)
- `objective`: precise success statement
- `depends_on`: upstream tasks that must be promoted first
- `inputs.design_docs`: the minimal docs needed for context packing
- `inputs.code_paths`: relevant local files for context
- `inputs.formal_paths`: relevant Lean files for formal or bridge tasks
- `allowed_write_paths`: strict ownership boundary
- `required_outputs`: concrete file outputs
- `acceptance_criteria`: copied exactly from the backlog plus task-specific clarifications
- `required_commands`: the minimal command set for verification
- `artifacts`: what must be written before promotion
- `risks`: likely failure modes
- `escalation_triggers`: conditions that require human review or task blocking
- `formal_claim_id`: optional link to a formal claim for tasks that implement or modify the formal spine
- `proof_status_required`: whether the task must emit or update proof-status artifacts before promotion

## `context.md` Contract

`context.md` should contain exactly these sections:

```md
# Context

## Objective

## Relevant Design Decisions

## Relevant Files

## Acceptance Criteria

## Non-Goals

## Open Risks
```

Rules:

- keep it short
- include only the task-relevant context
- avoid dumping whole docs

## `plan.md` Contract

Use this shape:

```md
# Plan

1. Read the relevant interfaces.
2. Implement the smallest valid version.
3. Add targeted tests.
4. Run required commands.
5. Write artifacts for verification, red review, and reproduction.
```

The actual numbered steps should be task-specific.

## `verification.json` Contract

Use this shape:

```json
{
  "task_id": "T031",
  "status": "self_tested",
  "commands": [
    {
      "cmd": "pytest tests/test_modeling_attack.py",
      "exit_code": 0
    }
  ],
  "checks": [
    {
      "name": "supports_three_model_families",
      "passed": true
    },
    {
      "name": "writes_attack_trace",
      "passed": true
    }
  ],
  "notes": "Deterministic under fixed seed."
}
```

Rules:

- each acceptance criterion should map to at least one check
- failed checks must include a short reason

## `red_review.md` Contract

This file must answer:

- what assumptions were attacked
- what edge cases were checked
- what broke
- what did not break
- whether critical findings remain

Use this structure:

```md
# Red Review

## Assumptions Challenged

## Edge Cases Tested

## Findings

## Critical Findings Remaining

## Recommendation
```

## `reproduction_report.md` Contract

This file must answer:

- what was rerun
- whether the same result was obtained
- what tolerances were used

Use this structure:

```md
# Reproduction Report

## Commands Rerun

## Result Comparison

## Tolerance

## Outcome
```

## `promotion.yaml` Contract

Use this shape:

```yaml
task_id: T031
status: promoted
promoted_by: Integrator
gates:
  schema_gate: pass
  output_gate: pass
  acceptance_gate: pass
  red_review_gate: pass
  reproduction_gate: pass
evidence:
  verification: ops/tasks/T031/verification.json
  red_review: ops/tasks/T031/red_review.md
  reproduction: ops/tasks/T031/reproduction_report.md
notes: Modeling attack implementation accepted.
```

## Execution Rules

- The builder may only edit files in `allowed_write_paths`.
- The verifier may not change source files.
- The red reviewer may propose changes but may not silently apply them.
- If acceptance criteria are ambiguous, block the task instead of guessing.
- If reproduction fails, the task cannot be promoted.

## Minimal Human Supervision Policy

Humans should only need to:

- approve changes to task scope
- resolve real blockers
- approve objective or scoring changes
- inspect high-stakes surprising outcomes

Everything else should be executable from the task manifest.

## Example Task Pack Lifecycle

1. Create `task.yaml` for the next unblocked task.
2. Pack `context.md` from the design docs and relevant files.
3. Implement according to `plan.md`.
4. Run required commands and write `verification.json`.
5. Run red review and write `red_review.md`.
6. Reproduce from clean inputs and write `reproduction_report.md`.
7. Promote with `promotion.yaml`.

This is the minimum contract for autonomous implementation.
