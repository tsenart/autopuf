# TASKS

This file turns the design in [README.md](/Users/tomas/code/pufs/README.md) and [AGENTS.md](/Users/tomas/code/pufs/AGENTS.md) into an executable backlog.

Each task should be instantiated using [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md) and executed using [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md).

The goal is not to list everything that could be done. The goal is to define the shortest path to a real `v1` autonomous evaluator that:

- accepts candidate and world specs
- runs honest evaluation plus required attacks
- applies hard constraints and scoring
- maintains a frontier
- produces replayable artifacts
- reproduces at least two literature-aligned failure modes

## Execution Rules

- Tasks are ordered by dependency, not by importance.
- A task is only done when its acceptance criteria are satisfied.
- Tasks on the critical path should be completed before parallel nice-to-haves.
- No search or optimization work begins until the evaluator and artifact pipeline are trustworthy.

## Critical Path

These are the non-skippable steps:

1. Repository and package skeleton
2. Shared schemas and type system
3. Artifact storage and replay
4. Candidate and world loading
5. Honest evaluator
6. Modeling and replay attacks
7. Constraints and scoring
8. End-to-end `evaluate`
9. Frontier and optimize loop
10. Validation against literature-aligned failure modes

## Parallel Work Packs

Once the foundations are in place, these can be done in parallel:

- attack implementations
- example candidate families
- world models
- report generation
- regression fixtures

## Phase 0: Foundations

### `T001` Create Python package skeleton

Why:

- establish the import structure and repo layout from the README

Depends on:

- nothing

Outputs:

- `pyproject.toml`
- `src/pufopt/__init__.py`
- package directories from the target repo layout

Acceptance criteria:

- `python -m pufopt.cli --help` resolves
- the package installs in editable mode
- empty modules import without side effects

### `T002` Define shared types and protocols

Why:

- all components depend on common object shapes

Depends on:

- `T001`

Outputs:

- `src/pufopt/types.py`

Acceptance criteria:

- types exist for `CandidateSpec`, `WorldSpec`, `AttackSpec`, `EvaluationResult`, `AttackResult`, `ScoreCard`, `FrontierEntry`, and `PlanDecision`
- attack, evaluator, candidate, and world protocols are defined
- mypy-friendly type hints exist for public interfaces

### `T003` Define schema validation layer

Why:

- external YAML and JSON must fail closed

Depends on:

- `T002`

Outputs:

- `src/pufopt/storage/schema.py`
- schema definitions or validation models

Acceptance criteria:

- invalid candidate specs are rejected with actionable errors
- invalid world specs are rejected with actionable errors
- invalid suite specs are rejected with actionable errors
- schema validation is covered by unit tests

### `T004` Implement artifact storage contract

Why:

- no result is useful if it cannot be replayed

Depends on:

- `T002`
- `T003`

Outputs:

- `src/pufopt/storage/io.py`
- `src/pufopt/storage/artifacts.py`

Acceptance criteria:

- a run directory can be created deterministically
- all major objects can be serialized and reloaded
- seeds and config references are always written
- artifact writes are atomic enough to avoid partial-success confusion

### `T005` Create CLI skeleton

Why:

- the system must be usable without editing Python

Depends on:

- `T001`

Outputs:

- `src/pufopt/cli.py`

Acceptance criteria:

- these commands exist and print structured help:
  - `optimize`
  - `evaluate`
  - `attack`
  - `frontier`
  - `report`
- command parsing is covered by tests

### `T006` Add test harness and CI-local conventions

Why:

- we need fast feedback before the system gets complex

Depends on:

- `T001`

Outputs:

- `tests/`
- baseline test config in `pyproject.toml`

Acceptance criteria:

- unit tests run with one command
- a minimal smoke test passes
- deterministic seeding utilities are available to tests

## Phase 1: Inputs And Buildable Objects

### `T010` Implement candidate registry and loader

Why:

- candidates must be declared in YAML and loaded into buildable objects

Depends on:

- `T002`
- `T003`
- `T004`

Outputs:

- `src/pufopt/candidates/registry.py`
- `src/pufopt/candidates/factory.py`

Acceptance criteria:

- a valid candidate YAML loads into a `CandidateSpec`
- `build()` returns a `BuiltCandidate`
- unknown family names fail clearly

### `T011` Implement world registry and loader

Why:

- evaluations need reproducible environment definitions

Depends on:

- `T002`
- `T003`
- `T004`

Outputs:

- `src/pufopt/worlds/registry.py`

Acceptance criteria:

- a valid world YAML loads into a `WorldSpec`
- sampling with the same seed gives the same world instance
- unknown world families fail clearly

### `T012` Implement baseline candidate family `classical_crp`

Why:

- `v1` needs one simple baseline family for honest eval and early attack work

Depends on:

- `T010`

Outputs:

- candidate family implementation
- at least one example YAML in `candidates/`

Acceptance criteria:

- candidate builds successfully
- candidate exposes enough behavior for honest evaluation and replay-style attacks

### `T013` Implement baseline candidate family `optical_auth`

Why:

- `v1` needs a second family closer to the intended PUF authentication use case

Depends on:

- `T010`

Outputs:

- candidate family implementation
- at least one example YAML in `candidates/`

Acceptance criteria:

- candidate builds successfully
- candidate supports configurable feature extraction, thresholding, and session policy

### `T014` Implement baseline world `lab_clean`

Why:

- we need a low-noise reference environment

Depends on:

- `T011`

Outputs:

- world implementation
- example YAML in `configs/worlds/`

Acceptance criteria:

- low-noise deterministic world instance can be sampled
- all core parameters are persisted into artifacts

### `T015` Implement baseline world `phone_reader_indoor`

Why:

- we need a realistic higher-variance world for robustness evaluation

Depends on:

- `T011`

Outputs:

- world implementation
- example YAML in `configs/worlds/`

Acceptance criteria:

- world includes noise, lighting jitter, angle variation, and temperature shift
- repeated sampling with fixed seed is deterministic

## Phase 2: Evaluator Core

### `T020` Implement honest evaluator

Why:

- no optimizer should exist before nominal evaluation is trustworthy

Depends on:

- `T012`
- `T013`
- `T014`
- `T015`

Outputs:

- `src/pufopt/evaluators/honest.py`

Acceptance criteria:

- computes `far`, `frr`, `eer` when applicable
- computes latency and cost metrics
- computes `crp_lifetime`
- emits machine-readable metrics artifact
- fails clearly when metrics are unavailable

### `T021` Implement constraints engine

Why:

- unsafe candidates must be rejected before ranking

Depends on:

- `T020`

Outputs:

- `src/pufopt/evaluators/constraints.py`
- default scoring config in `configs/scoring/default.yaml`

Acceptance criteria:

- candidates that violate hard thresholds are marked `rejected`
- reasons for rejection are explicit and persisted
- constrained-out candidates never reach the frontier

### `T022` Implement scoring engine

Why:

- surviving candidates need comparable utility

Depends on:

- `T021`

Outputs:

- `src/pufopt/evaluators/scoring.py`

Acceptance criteria:

- only valid survivors receive a score
- security terms are not averaged away behind soft utility
- weighted utility is reproducible from stored inputs

### `T023` Implement top-level `evaluate` command

Why:

- researchers need a single-command evaluation path before search exists

Depends on:

- `T004`
- `T020`
- `T021`
- `T022`
- `T005`

Outputs:

- working `evaluate` CLI

Acceptance criteria:

- `evaluate` loads candidate and world YAML
- writes a full run artifact directory
- emits a short summary pointing to artifacts

## Phase 3: Adversarial Core

### `T030` Implement attack base classes and budget handling

Why:

- all attacks need a common interface and comparable budget semantics

Depends on:

- `T002`

Outputs:

- `src/pufopt/attacks/base.py`

Acceptance criteria:

- attack interface is concrete enough for implementations
- attack budgets are serializable and enforced

### `T031` Implement modeling attack

Why:

- this is the first serious falsifier and one of the required literature-aligned attacks

Depends on:

- `T030`
- `T020`

Outputs:

- `src/pufopt/attacks/modeling.py`

Acceptance criteria:

- supports at least three simple model families
- outputs best attack found under budget
- writes attack trace artifact

### `T032` Implement replay attack

Why:

- replay is low-complexity, important, and easy to validate

Depends on:

- `T030`
- `T020`

Outputs:

- `src/pufopt/attacks/replay.py`

Acceptance criteria:

- attack can exploit observed responses when allowed by world/candidate assumptions
- success metric is persisted

### `T033` Implement nearest-match counterfeit attack

Why:

- this is a core attack for noisy physical fingerprints

Depends on:

- `T030`
- `T020`

Outputs:

- `src/pufopt/attacks/nearest_match.py`

Acceptance criteria:

- attack searches for closest observed or synthesized sample under threshold
- counterfeit acceptance rate is reported

### `T034` Implement CRP exhaustion attack

Why:

- limited-use challenge spaces are central to practical deployment

Depends on:

- `T030`
- `T020`

Outputs:

- `src/pufopt/attacks/crp_exhaustion.py`

Acceptance criteria:

- attack models challenge depletion or safe-session collapse
- lifetime reduction is reported explicitly

### `T035` Implement drift abuse attack

Why:

- robustness under realistic perturbation must be attackable, not just measured passively

Depends on:

- `T030`
- `T020`

Outputs:

- `src/pufopt/attacks/drift_abuse.py`

Acceptance criteria:

- attack perturbs within allowed environmental budget
- success is measured as induced false accept or false reject behavior

### `T036` Implement top-level `attack` command

Why:

- attacks must be runnable independently for debugging and research workflows

Depends on:

- `T031`
- `T032`
- `T005`

Outputs:

- working `attack` CLI

Acceptance criteria:

- single attack can run against a candidate/world pair
- writes a complete attack artifact

## Phase 4: Aggregation And Search

### `T040` Implement adversarial evaluator orchestration

Why:

- we need one component that runs all required attacks and aggregates the result

Depends on:

- `T031`
- `T032`
- `T033`
- `T034`
- `T035`
- `T021`
- `T022`

Outputs:

- `src/pufopt/evaluators/adversarial.py`

Acceptance criteria:

- runs all required attacks for a suite
- returns one `EvaluationResult`
- marks run `untrusted` if required attacks are missing

### `T041` Implement frontier maintenance

Why:

- optimization without survivor tracking is just random search

Depends on:

- `T040`

Outputs:

- `src/pufopt/loop/frontier.py`

Acceptance criteria:

- frontier excludes rejected candidates
- dominated candidates are tracked separately
- repeated updates are deterministic

### `T042` Implement candidate mutations

Why:

- the search loop needs local moves through candidate space

Depends on:

- `T010`
- `T040`

Outputs:

- `src/pufopt/candidates/mutations.py`

Acceptance criteria:

- mutations preserve schema validity
- mutations stay inside declared parameter domains

### `T043` Implement scheduler

Why:

- we need principled selection of next candidate, world, and attack mix

Depends on:

- `T041`
- `T042`

Outputs:

- `src/pufopt/loop/scheduler.py`

Acceptance criteria:

- scheduler supports exploration and exploitation modes
- scheduler can prioritize falsification of strong survivors

### `T044` Implement optimize loop

Why:

- this is the first real autonomous search path

Depends on:

- `T040`
- `T041`
- `T042`
- `T043`

Outputs:

- `src/pufopt/loop/search.py`
- working `optimize` CLI

Acceptance criteria:

- suite file can launch a full optimization run
- run writes frontier snapshots and run artifacts
- at least one mutation cycle occurs automatically

### `T045` Implement frontier and report commands

Why:

- researchers need usable output, not just raw JSON

Depends on:

- `T041`
- `T044`
- `T005`

Outputs:

- `frontier` CLI
- `report` CLI

Acceptance criteria:

- frontier can be rendered from a run directory
- report summarizes survivors, failures, and next candidate suggestions

## Phase 5: Validation And Research Utility

### `T050` Create literature-aligned regression fixtures

Why:

- `v1` must prove itself against known public boundaries

Depends on:

- `T023`
- `T036`

Outputs:

- fixture candidate and world specs in `candidates/` and `configs/worlds/`
- regression notes in `tests/fixtures/` or `suites/`

Acceptance criteria:

- includes at least one modeling-vulnerable construction
- includes at least one CRP-limited construction
- includes at least one trust-limited remote-auth-like construction

### `T051` Implement regression suites

Why:

- known failures should remain detectable over time

Depends on:

- `T050`
- `T040`

Outputs:

- regression suites in `suites/`
- automated regression tests

Acceptance criteria:

- suite reproduces at least two literature-aligned failure modes
- failure conditions are asserted in tests

### `T052` Implement example run reports

Why:

- researchers need confidence that the system says something useful

Depends on:

- `T045`
- `T051`

Outputs:

- example reports under `artifacts/reports/` or generated docs

Acceptance criteria:

- report shows at least one survivor
- report shows at least one rejected candidate with explicit reason
- report shows at least one recommended next experiment

## Phase 6: Researcher Usability

### `T060` Add starter candidate and world library

Why:

- the system is more useful when new users can start from templates

Depends on:

- `T012`
- `T013`
- `T014`
- `T015`

Outputs:

- baseline YAML library

Acceptance criteria:

- at least four candidate examples and three world examples exist
- each example is schema-valid and runnable

### `T061` Add suite templates

Why:

- most researchers should start from a suite, not a hand-built CLI call

Depends on:

- `T044`

Outputs:

- suite templates for:
  - smoke evaluation
  - attack-only analysis
  - short optimization run
  - regression run

Acceptance criteria:

- each suite template runs without manual editing

### `T062` Add runbook section for first-time operators

Why:

- a repo can be technically complete and still be hard to use

Depends on:

- `T060`
- `T061`

Outputs:

- README or separate operator section

Acceptance criteria:

- a new user can run one evaluation and one optimization loop from copy-paste commands

## First Build Sequence

Do these in this exact order:

1. `T001`
2. `T002`
3. `T003`
4. `T004`
5. `T005`
6. `T006`
7. `T010`
8. `T011`
9. `T012`
10. `T014`
11. `T020`
12. `T021`
13. `T022`
14. `T023`
15. `T030`
16. `T031`
17. `T032`
18. `T040`
19. `T041`
20. `T044`
21. `T050`
22. `T051`

This is the minimum path to a credible `v1`.

## Recommended Parallelization After Foundations

After `T006`, split work like this:

- Track A: `T010`, `T012`, `T013`
- Track B: `T011`, `T014`, `T015`
- Track C: `T020`, `T021`, `T022`
- Track D: `T030`, `T031`, `T032`, then `T033`, `T034`, `T035`

Merge point:

- `T040`

## Definition Of Done

The backlog is complete when all of the following are true:

- `evaluate` works end-to-end from YAML
- `attack` works end-to-end from YAML
- `optimize` runs at least one meaningful search loop
- every run writes replayable artifacts
- the frontier logic excludes rejected candidates
- at least two literature-aligned failures are reproduced
- a report names the next most informative experiment

At that point, the repo has a real autonomous evaluator, not just design docs.
