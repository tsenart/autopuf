# RUNBOOK

This file defines the operator workflow for running `autopuf` with minimal human supervision.

The operator can be:

- a human
- a supervisory agent
- a simple orchestrator process

The runbook assumes the workflow rules in [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md) and the task contracts in [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md).

## Operating Modes

### `build`

Purpose:

- implement tasks from [TASKS.md](/Users/tomas/code/pufs/TASKS.md)

Primary artifact root:

- `ops/tasks/`

### `research`

Purpose:

- run candidate evaluation and optimization jobs

Primary artifact root:

- `artifacts/runs/`

### `strict`

Purpose:

- high-confidence mode for promotion-worthy tasks or surprising results

Behavior:

- no skipped gates
- mandatory reproduction
- mandatory red review on all nontrivial outputs

### `formal`

Purpose:

- build or update Lean formal claims, proof status, and Python-Lean bridge checks

Primary artifact root:

- `formal/`

## Startup Checklist

Before any autonomous work begins:

1. Validate that the core docs exist.
2. Validate task manifests or suite specs.
3. Validate write ownership boundaries.
4. Validate required directories.
5. Freeze the current objective, constraints, scoring config, and proof policy for the run.

If any of these fail, stop and mark the run `blocked`.

## Build Mode Procedure

### Step 1: Select next task

Pick the first unblocked task from [TASKS.md](/Users/tomas/code/pufs/TASKS.md) whose dependencies are promoted.

Create:

- `ops/tasks/<task_id>/task.yaml`

Use the contract in [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md).

### Step 2: Pack context

Create:

- `ops/tasks/<task_id>/context.md`

Context should include:

- task objective
- relevant design decisions
- allowed write paths
- acceptance criteria
- open risks

Do not include unrelated files.

### Step 3: Execute implementation

Create:

- `ops/tasks/<task_id>/plan.md`
- `ops/tasks/<task_id>/activity.log`

Implementation rules:

- stay inside `allowed_write_paths`
- prefer the smallest valid implementation
- add tests as close to the changed behavior as possible

### Step 4: Verify

Run all commands listed in `task.yaml`.

Create:

- `ops/tasks/<task_id>/verification.json`

If verification fails:

- either return to implementation once
- or mark `rejected` with reason

### Step 5: Red review

Run an adversarial review on:

- edge cases
- interfaces
- determinism
- failure handling
- artifact completeness

Create:

- `ops/tasks/<task_id>/red_review.md`

If critical findings exist:

- return the task to `implemented`

### Step 6: Reproduce

Rerun the implementation from clean task inputs.

Create:

- `ops/tasks/<task_id>/reproduction_report.md`

If reproduction fails:

- return to `implemented` if fixable
- otherwise mark `untrusted` or `blocked`

### Step 7: Promote

Create:

- `ops/tasks/<task_id>/promotion.yaml`

Only then may the task be marked complete.

## Research Mode Procedure

### Step 1: Select job

Pick one of:

- a suite from `suites/`
- a candidate/world pair for targeted evaluation

Freeze:

- candidate
- world
- attack set
- budgets
- scoring config

### Step 2: Run honest evaluation

Required output:

- honest metrics artifact

If required metrics are missing:

- mark the run `untrusted`

### Step 3: Run required attacks

Required `v1` attacks:

- modeling
- replay
- nearest_match
- crp_exhaustion
- drift_abuse

If any required attack is missing:

- mark the run `untrusted`

### Step 4: Score and constrain

Apply:

1. hard constraints
2. utility scoring for survivors

Do not rank rejected candidates.

### Step 5: Intensify on strong or surprising results

If a result is:

- near the top of the frontier
- much stronger than prior baselines
- contradictory to known expectations

Then:

- rerun with stronger attacks
- rerun under harder worlds
- ablate key parameters

### Step 6: Formalize the promoted claim

For any strong or promoted result:

- assign or update `formal_claim_id`
- assign `proof_status`
- if the family is supported by Lean reference semantics, run bounded differential checks

If formalization fails:

- mark the result `empirical_only` only if that policy is explicitly allowed
- otherwise mark `untrusted`

### Step 7: Reproduce

Rerun the result from stored artifacts and seeds.

If it does not reproduce:

- mark `untrusted`

### Step 8: Promote result

Only promoted results may:

- update the frontier
- influence planner decisions
- appear in summary reports as real findings
- claim stronger-than-empirical assurance

## Escalation Matrix

Escalate to a human only for these cases:

- unclear or conflicting objective
- scoring or constraint changes
- write ownership conflict
- major architecture conflict between tasks
- suspiciously strong or publication-grade result
- mismatch between Python behavior and Lean reference semantics
- compute or lab budget breach
- blocker that cannot be resolved from repo context

Do not escalate for normal implementation details, test failures, or expected red-review findings.

## Stop Conditions

Stop the current autonomous run when:

- a required gate cannot be passed
- artifacts are incomplete or corrupted
- a task attempts to write outside allowed ownership
- scoring inputs are incomplete
- the run exceeds the explicit budget

Stopping is a valid outcome. Silent continuation is not.

## Daily Autonomous Cadence

In steady-state, the orchestrator should do this:

1. promote any tasks that cleared all gates
2. reopen tasks sent back by red review or failed reproduction
3. select the next unblocked task on the critical path
4. execute one build cycle
5. execute one research cycle if the evaluator path is healthy
6. emit a daily summary

The system should favor depth on the critical path over wide shallow parallelism.

## Daily Summary Contract

Each autonomous session should emit:

- tasks promoted
- tasks blocked
- tasks returned by red review
- research runs promoted
- research runs marked `untrusted`
- frontier changes
- next recommended actions

This can be machine-readable or markdown, but it must be concise and auditable.

## Suggested Control Plane

The repository should eventually expose these commands:

```bash
python -m pufopt.cli evaluate --candidate ... --world ...
python -m pufopt.cli attack --candidate ... --world ... --attack modeling
python -m pufopt.cli optimize --suite ...
python -m pufopt.cli frontier --run ...
python -m pufopt.cli report --run ...
python -m pufopt.ops next-task
python -m pufopt.ops pack-context --task T031
python -m pufopt.ops verify-task --task T031
python -m pufopt.ops promote-task --task T031
python -m pufopt.ops formalize-claim --run artifacts/runs/<run_id>
```

The `pufopt.ops` commands are not implemented yet, but this is the intended autonomous control plane.

## World-Class Standards

The workflow is world-class only if it can do all of the following with low human supervision:

- pick the next correct task
- implement within declared ownership
- verify itself with task-level acceptance checks
- attack its own outputs before promotion
- reproduce strong results before trusting them
- attach proof status to promoted strong claims
- preserve negative results
- keep an auditable trail for every important decision

If any of these are missing, the system is not autonomous enough.
