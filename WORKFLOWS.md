# WORKFLOWS

This file defines the operating workflows for autonomous execution with minimal human supervision.

There are two workflows:

- the `Delivery Workflow` for building the system
- the `Research Workflow` for using the system to find results

The design goal is simple:

- humans define objectives, constraints, and promotion policy
- agents execute everything routine
- no result is trusted until it survives fixed gates

## Source Of Truth

The `autopuf` repo is governed by these documents:

- [README.md](/Users/tomas/code/pufs/README.md): system architecture
- [AGENTS.md](/Users/tomas/code/pufs/AGENTS.md): role contracts
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md): backlog and dependency order
- [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md): task contract
- [RUNBOOK.md](/Users/tomas/code/pufs/RUNBOOK.md): operator procedures

If these conflict, precedence is:

1. hard constraints in `README.md`
2. role and gate rules in `AGENTS.md`
3. task order and acceptance criteria in `TASKS.md`
4. execution mechanics in this file
5. operator defaults in `RUNBOOK.md`

## Core Principles

- Every state transition must be backed by artifacts.
- Every artifact must be reproducible from stored inputs and seeds.
- Every promising result must be attacked before promotion.
- Every surprising result must be reproduced before promotion.
- Every failure must be preserved as a first-class outcome.
- Every autonomous action must stay inside the declared file ownership and objective boundaries.
- Every promoted strong claim must carry formal status.

## Proof Status Vocabulary

Use this exact vocabulary for formal claim status:

- `empirical_only`
- `specified`
- `partially_proved`
- `proved`
- `counterexample_found`

## Global Status Vocabulary

Use this exact vocabulary for task and run states:

- `ready`
- `context_packed`
- `in_progress`
- `implemented`
- `self_tested`
- `red_reviewed`
- `reproduced`
- `promoted`
- `blocked`
- `rejected`
- `untrusted`

Do not invent alternate status words in machine-readable artifacts.

## Delivery Workflow

The `Delivery Workflow` is the state machine for building the repository itself.

### Delivery States

#### `ready`

Meaning:

- the task is unblocked and can be started

Entry criteria:

- dependencies in [TASKS.md](/Users/tomas/code/pufs/TASKS.md) are marked complete
- task manifest exists

Required artifacts:

- `ops/tasks/<task_id>/task.yaml`

Allowed transitions:

- `context_packed`
- `blocked`

#### `context_packed`

Meaning:

- the executor has prepared the minimum context needed to perform the task

Entry criteria:

- design references selected
- allowed file set declared
- acceptance criteria copied into task manifest

Required artifacts:

- `ops/tasks/<task_id>/context.md`
- `ops/tasks/<task_id>/task.yaml`

Allowed transitions:

- `in_progress`
- `blocked`

#### `in_progress`

Meaning:

- implementation work is actively happening

Entry criteria:

- file ownership claimed
- builder assigned

Required artifacts:

- `ops/tasks/<task_id>/plan.md`
- `ops/tasks/<task_id>/activity.log`

Allowed transitions:

- `implemented`
- `blocked`
- `rejected`

#### `implemented`

Meaning:

- code or docs for the task are written

Entry criteria:

- required outputs exist
- no known missing implementation steps remain

Required artifacts:

- updated source files
- `ops/tasks/<task_id>/implementation_report.md`

Allowed transitions:

- `self_tested`
- `blocked`
- `rejected`

#### `self_tested`

Meaning:

- the builder has run the task's own acceptance checks

Entry criteria:

- required tests and commands completed
- outputs match task acceptance criteria

Required artifacts:

- `ops/tasks/<task_id>/verification.json`
- logs for test commands

Allowed transitions:

- `red_reviewed`
- `blocked`
- `rejected`

#### `red_reviewed`

Meaning:

- an adversarial reviewer has tried to break the implementation

Entry criteria:

- red review completed
- edge cases and contract failures checked

Required artifacts:

- `ops/tasks/<task_id>/red_review.md`

Allowed transitions:

- `reproduced`
- `implemented`
- `blocked`
- `rejected`

Rule:

- if red review finds a real issue, the task returns to `implemented`

#### `reproduced`

Meaning:

- the implementation was rerun from clean inputs and produced the same result

Entry criteria:

- relevant commands rerun with fixed seeds or deterministic setup
- artifacts regenerated successfully

Required artifacts:

- `ops/tasks/<task_id>/reproduction_report.md`

Allowed transitions:

- `promoted`
- `implemented`
- `blocked`

#### `promoted`

Meaning:

- the task is accepted as complete

Entry criteria:

- all acceptance criteria satisfied
- no unresolved red-review findings
- reproduction succeeded

Required artifacts:

- `ops/tasks/<task_id>/promotion.yaml`

Allowed transitions:

- none

#### `blocked`

Meaning:

- the task cannot progress without external resolution

Entry criteria:

- missing dependency
- unresolved ambiguity with real consequences
- failing gate outside current task ownership

Required artifacts:

- `ops/tasks/<task_id>/blocker.md`

Allowed transitions:

- `ready`
- `rejected`

#### `rejected`

Meaning:

- the current implementation attempt is invalid and must not be promoted

Entry criteria:

- acceptance criteria cannot be met with the current approach
- fatal design conflict or failed gate

Required artifacts:

- `ops/tasks/<task_id>/rejection.md`

Allowed transitions:

- `ready`

### Delivery Roles Per State

- `Planner`: move tasks to `ready`
- `Context Builder`: move tasks to `context_packed`
- `Builder`: move tasks to `implemented`
- `Verifier`: move tasks to `self_tested`
- `Red Reviewer`: move tasks to `red_reviewed`
- `Reproducer`: move tasks to `reproduced`
- `Integrator`: move tasks to `promoted`

## Delivery Promotion Gates

Each task must pass all of these before `promoted`:

1. `Schema Gate`
   - all machine-readable files validate
2. `Output Gate`
   - declared outputs exist
3. `Acceptance Gate`
   - all task-level acceptance criteria pass
4. `Red Review Gate`
   - no unresolved critical findings remain
5. `Reproduction Gate`
   - result can be regenerated from clean inputs
6. `Formal Contract Gate`
   - tasks touching the formal spine must validate their claim schemas and bridge outputs

## Delivery Artifact Contract

Each active task should use this directory:

```text
ops/tasks/<task_id>/
├── task.yaml
├── context.md
├── plan.md
├── activity.log
├── implementation_report.md
├── verification.json
├── red_review.md
├── reproduction_report.md
├── blocker.md
├── rejection.md
└── promotion.yaml
```

Not every file must exist for every task state, but `task.yaml` must always exist once a task is active.

## Delivery State Transition Rules

- Only one builder may hold write ownership of a file set at a time.
- Red review must be performed by a different agent or by a clean pass with different prompts and no hidden state.
- If a task changes public interfaces, all dependent task manifests must be revalidated.
- A task may skip reproduction only for pure documentation changes. Code changes may not skip reproduction.

## Delivery Workflow Pseudocode

```python
def run_delivery_task(task):
    assert task.status == "ready"

    context = context_builder.pack(task)
    task.status = "context_packed"

    implementation = builder.execute(task, context)
    task.status = "implemented"

    verification = verifier.check(task, implementation)
    if not verification.passed:
        task.status = "rejected"
        return
    task.status = "self_tested"

    review = red_reviewer.challenge(task, implementation)
    if review.has_critical_findings:
        task.status = "implemented"
        return
    task.status = "red_reviewed"

    reproduction = reproducer.rerun(task)
    if not reproduction.passed:
        task.status = "implemented"
        return
    task.status = "reproduced"

    integrator.promote(task)
    task.status = "promoted"
```

## Research Workflow

The `Research Workflow` is the state machine for evaluating candidate designs and discovering robust results.

### Research States

#### `ready`

Meaning:

- candidate, world, and suite specs exist and are schema-valid

Required artifacts:

- candidate YAML
- world YAML
- suite YAML if applicable

Allowed transitions:

- `context_packed`
- `blocked`

#### `context_packed`

Meaning:

- run configuration, budgets, and attack set are frozen

Required artifacts:

- `artifacts/runs/<run_id>/suite.yaml`
- `artifacts/runs/<run_id>/candidate.yaml`
- `artifacts/runs/<run_id>/world.yaml`

Allowed transitions:

- `in_progress`
- `blocked`

#### `in_progress`

Meaning:

- evaluation is running

Allowed transitions:

- `implemented`
- `blocked`
- `rejected`

#### `implemented`

Meaning:

- honest evaluation and attacks have finished

Required artifacts:

- all required attack outputs
- raw metrics

Allowed transitions:

- `self_tested`
- `untrusted`

#### `self_tested`

Meaning:

- scoring and constraints have been applied and internal consistency checks passed

Required artifacts:

- `metrics.json`
- `score.json`

Allowed transitions:

- `red_reviewed`
- `untrusted`

#### `red_reviewed`

Meaning:

- stronger or alternate attacks were attempted on any strong or surprising result

Required artifacts:

- updated attack traces
- challenge note if the result changed materially

Allowed transitions:

- `reproduced`
- `implemented`
- `untrusted`

#### `reproduced`

Meaning:

- the run or a targeted subset was rerun from saved artifacts and matched within tolerance

Required artifacts:

- replay log
- comparison report

Allowed transitions:

- `promoted`
- `untrusted`

#### `promoted`

Meaning:

- the result is accepted for frontier update or experiment planning

Required artifacts:

- `frontier/update.json` or `planner/decision.json`

Allowed transitions:

- none

#### `untrusted`

Meaning:

- the run completed but failed one or more trust gates

Required artifacts:

- trust failure reason

Allowed transitions:

- `ready`
- `rejected`

### Research Promotion Gates

Each research run must pass these gates:

1. `Spec Gate`
   - candidate, world, suite, and scoring configs validate
2. `Coverage Gate`
   - all required attack families ran
3. `Constraint Gate`
   - hard constraints applied before ranking
4. `Reproduction Gate`
   - strong or surprising results rerun successfully
5. `Trace Gate`
   - attack traces and metrics are stored
6. `Formal Claim Gate`
   - strong or promoted results carry `proof_status` and a formal claim reference, or are explicitly marked `empirical_only`
7. `Differential Gate`
   - if a supported family has a Lean reference semantics, bounded differential checks must pass before promotion

## Research Workflow Pseudocode

```python
def run_research_job(job):
    freeze_inputs(job)
    job.status = "context_packed"

    result = evaluator.evaluate(job.candidate, job.world, job.attacks)
    job.status = "implemented"

    if not scorer.inputs_are_complete(result):
        job.status = "untrusted"
        return
    score = scorer.compute(result)
    job.status = "self_tested"

    if is_strong_or_surprising(score):
        review = red_team.intensify(job, result)
        if review.breaks_result:
            job.status = "implemented"
            return
        formal = formalizer.sync(job, result)
        if formal.supported and not formal.differential_checks_passed:
            job.status = "untrusted"
            return
    job.status = "red_reviewed"

    reproduction = reproducer.rerun(job)
    if not reproduction.passed:
        job.status = "untrusted"
        return
    job.status = "reproduced"

    frontier.update(score)
    planner.schedule_next(job, score)
    job.status = "promoted"
```

## Human Escalation Policy

Autonomy should stop and ask for human input only when one of these is true:

- the objective function changes
- hard constraints or scoring weights need to change
- a result appears publication-worthy or strongly contradicts priors
- a task requires edits outside its allowed ownership
- a blocker cannot be resolved from local context
- compute or lab costs exceed the allowed budget

Everything else should be handled automatically.

## Retry Policy

Default retries:

- schema errors: `0`
- transient command or environment failures: `2`
- failed tests after implementation: `1` rebuild cycle
- failed red review: return to `implemented`
- failed reproduction: return to `implemented` if fixable, otherwise `untrusted`

Never retry silently without writing the reason into artifacts.

## Parallelism Policy

Use parallel execution only when:

- tasks have disjoint write ownership
- research runs do not overwrite the same artifact path
- one worker is not blocked on the other's output

Do not parallelize:

- schema migrations with downstream dependencies
- multiple builders editing the same files
- frontier updates into the same run directory

## World-Class Workflow Metrics

Track the workflow itself with these metrics:

- task cycle time
- task promotion rate
- red-review catch rate
- reproduction pass rate
- human intervention rate
- percentage of runs ending `untrusted`
- percent of optimizer budget spent on invalid candidates
- expected information gain per accepted run

World-class performance means:

- low human intervention
- high reproduction pass rate
- high red-review catch rate before promotion
- high ratio of informative failures to wasted runs

## Minimum Viable Automation Layer

An autonomous executor is ready to build when it can do all of the following:

1. load the next unblocked task from `ops/tasks/`
2. pack context from repo docs and local files
3. execute builder, verifier, red review, and reproduction passes
4. update task state machine artifacts
5. launch research runs from suite files
6. launch formalization and bounded differential-check jobs for strong results
7. promote only results that pass gates

At that point, the repo is not just documented. It is operable.
