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
- carries proof status for promoted strong claims
- exposes a thin executable control plane for task selection, verification, promotion, and run formalization

## Execution Rules

- Tasks are ordered by dependency, not by importance.
- A task is only done when its acceptance criteria are satisfied.
- Tasks on the critical path should be completed before parallel nice-to-haves.
- No search or optimization work begins until the evaluator and artifact pipeline are trustworthy.

## Status Snapshot

Done:

- `T000` through `T008`
- `T010` through `T015`
- `T020` through `T026`
- `T030` through `T045`
- `T050` through `T052`
- `T060` through `T062`

Pending:

- none in the current `v1` backlog

Important note:

- the current `v1` backlog is now implemented end to end, including the thin delivery control plane; follow-up work should extend breadth, rigor, or domain coverage rather than re-open completed baseline tasks.

## Critical Path

These are the non-skippable steps:

1. Toolchain bootstrap and validation
2. Repository and package skeleton
3. Shared schemas and type system
4. Artifact storage and replay
5. Candidate and world loading
6. Honest evaluator
7. Modeling and replay attacks
8. Constraints and scoring
9. End-to-end `evaluate`
10. Formal claim and proof-status plumbing
11. Frontier and optimize loop
12. Validation against literature-aligned failure modes

## Parallel Work Packs

Once the foundations are in place, these can be done in parallel:

- attack implementations
- example candidate families
- world models
- report generation
- regression fixtures
- formal core and Python-Lean bridge work

## Phase 0: Foundations

### `T000` Bootstrap and validate local toolchains [done]

Why:

- autonomous execution needs validated Python and Lean toolchains before any task can run reliably

Depends on:

- nothing

Outputs:

- documented prerequisites and validation commands in `RUNBOOK.md`

Acceptance criteria:

- required tools are explicitly listed
- validation commands are explicitly listed
- the build sequence starts from this bootstrap step

### `T001` Create Python package skeleton [done]

Why:

- establish the import structure and repo layout from the README

Depends on:

- `T000`

Outputs:

- `pyproject.toml`
- `src/pufopt/__init__.py`
- package directories from the target repo layout

Acceptance criteria:

- `.venv/bin/python -m pufopt.cli --help` resolves
- the package installs in editable mode
- empty modules import without side effects

### `T002` Define shared types and protocols [done]

Why:

- all components depend on common object shapes

Depends on:

- `T000`
- `T001`

Outputs:

- `src/pufopt/types.py`

Acceptance criteria:

- types exist for `CandidateSpec`, `WorldSpec`, `AttackSpec`, `EvaluationResult`, `AttackResult`, `ScoreCard`, `FrontierEntry`, `PlanDecision`, `FormalClaimSpec`, and `ProofStatus`
- attack, evaluator, candidate, and world protocols are defined
- mypy-friendly type hints exist for public interfaces

### `T003` Define schema validation layer [done]

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
- invalid formal claim manifests are rejected with actionable errors
- schema validation is covered by unit tests

### `T004` Implement artifact storage contract [done]

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

### `T005` Create CLI skeleton [done]

Why:

- the system must be usable without editing Python

Depends on:

- `T000`
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

### `T006` Add test harness and CI-local conventions [done]

Why:

- we need fast feedback before the system gets complex

Depends on:

- `T000`
- `T001`

Outputs:

- `tests/`
- baseline test config in `pyproject.toml`

Acceptance criteria:

- unit tests run with one command
- a minimal smoke test passes
- deterministic seeding utilities are available to tests

### `T007` Initialize Lean workspace [done]

Why:

- the formal spine must exist from day 0 if we want promoted claims to map cleanly into Lean

Depends on:

- `T000`
- `T001`

Outputs:

- `formal/lean-toolchain`
- `formal/lakefile.lean`
- `formal/Main.lean`
- `formal/Autopuf/Model.lean`
- `formal/Autopuf/Games.lean`
- `formal/Autopuf/Claims.lean`
- `formal/Autopuf/Bridge.lean`

Acceptance criteria:

- the Lean workspace is initialized
- build instructions are captured in the repo
- the workspace layout supports `Autopuf/Model.lean`, `Autopuf/Games.lean`, `Autopuf/Claims.lean`, and `Autopuf/Bridge.lean`
- the workspace builds from `formal/` with `lake build`

### `T008` Define formal claim schema and proof-status types [done]

Why:

- promoted strong results need machine-readable formal status even before they are fully proved

Depends on:

- `T002`
- `T003`
- `T007`

Outputs:

- proof-status type definitions
- formal claim schema definitions
- `ops/templates/formal-claim.yaml`

Acceptance criteria:

- proof status values are defined and validated
- formal claim manifests validate
- evaluation artifacts can reference `formal_claim_id` and `proof_status`
- promotion artifacts can record formal-gate outcomes

## Phase 1: Inputs And Buildable Objects

### `T010` Implement candidate registry and loader [done]

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

### `T011` Implement world registry and loader [done]

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

### `T012` Implement baseline candidate family `classical_crp` [done]

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

### `T013` Implement baseline candidate family `optical_auth` [done]

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

### `T014` Implement baseline world `lab_clean` [done]

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

### `T015` Implement baseline world `phone_reader_indoor` [done]

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

### `T020` Implement honest evaluator [done]

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

### `T021` Implement constraints engine [done]

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
- the default scoring config includes strong-result and proof-policy settings

### `T022` Implement scoring engine [done]

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
- strong-result classification is computed from configuration rather than hidden code defaults

### `T023` Implement top-level `evaluate` command [done]

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

## Phase 2.5: Formal Spine

### `T024` Define Lean abstract core model [done]

Why:

- the empirical engine needs a stable formal target for promoted claims

Depends on:

- `T007`
- `T008`
- `T002`

Outputs:

- `formal/Autopuf/Model.lean`
- `formal/Autopuf/Games.lean`
- `formal/Autopuf/Claims.lean`

Acceptance criteria:

- the model defines abstract candidate, challenge, response, verifier, adversary, and security-game concepts
- assumptions and claim statements can be represented explicitly
- the Lean modules are organized for incremental extension

### `T025` Implement formal claim bridge and artifact plumbing [done]

Why:

- promoted results need a stable bridge between empirical runs and formal claims

Depends on:

- `T004`
- `T008`
- `T023`
- `T024`

Outputs:

- `src/pufopt/formal/bridge.py`
- `formal/Autopuf/Bridge.lean`
- formal claim artifacts in run outputs

Acceptance criteria:

- a run can emit `formal_claim_id`
- a run can emit `proof_status`
- a supported run can emit a bounded differential-check artifact
- formal claim artifacts are written deterministically

### `T026` Add bounded differential checks between Python and Lean reference semantics [done]

Why:

- supported families need a concrete consistency check between implementation behavior and formal meaning

Depends on:

- `T024`
- `T025`
- `T012`

Outputs:

- differential test harness
- at least one bounded reference check for a supported family

Acceptance criteria:

- at least one supported candidate family has a bounded differential check
- mismatch is surfaced as a promotion-blocking finding for supported claims

## Phase 3: Adversarial Core

### `T030` Implement attack base classes and budget handling [done]

Why:

- all attacks need a common interface and comparable budget semantics

Depends on:

- `T002`

Outputs:

- `src/pufopt/attacks/base.py`

Acceptance criteria:

- attack interface is concrete enough for implementations
- attack budgets are serializable and enforced

### `T031` Implement modeling attack [done]

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

### `T032` Implement replay attack [done]

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

### `T033` Implement nearest-match counterfeit attack [done]

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

### `T034` Implement CRP exhaustion attack [done]

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

### `T035` Implement drift abuse attack [done]

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

### `T036` Implement top-level `attack` command [done]

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

### `T040` Implement adversarial evaluator orchestration [done]

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

### `T041` Implement frontier maintenance [done]

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

### `T042` Implement candidate mutations [done]

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

### `T043` Implement scheduler [done]

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

### `T044` Implement optimize loop [done]

Why:

- this is the first real autonomous search path

Depends on:

- `T040`
- `T041`
- `T042`
- `T043`
- `T025`
- `T026`

Outputs:

- `src/pufopt/loop/search.py`
- working `optimize` CLI

Acceptance criteria:

- suite file can launch a full optimization run
- run writes frontier snapshots and run artifacts
- at least one mutation cycle occurs automatically

### `T045` Implement frontier and report commands [done]

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

### `T050` Create literature-aligned regression fixtures [done]

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

### `T051` Implement regression suites [done]

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

### `T052` Implement example run reports [done]

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

### `T060` Add starter candidate and world library [done]

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

### `T061` Add suite templates [done]

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

### `T062` Add runbook section for first-time operators [done]

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

1. `T000`
2. `T001`
3. `T002`
4. `T003`
5. `T004`
6. `T005`
7. `T006`
8. `T007`
9. `T008`
10. `T010`
11. `T011`
12. `T012`
13. `T013`
14. `T014`
15. `T015`
16. `T020`
17. `T021`
18. `T022`
19. `T023`
20. `T024`
21. `T025`
22. `T030`
23. `T031`
24. `T032`
25. `T033`
26. `T034`
27. `T035`
28. `T036`
29. `T040`
30. `T041`
31. `T026`
32. `T042`
33. `T043`
34. `T044`
35. `T050`
36. `T051`

This is the minimum path to a credible `v1`.

## Recommended Parallelization After Foundations

After `T008`, split work like this while preserving dependencies:

- Track A: `T010`, then `T012` and `T013`
- Track B: `T011`, then `T014` and `T015`
- Track C: after `T020`, run `T021`, then `T022`
- Track D: after `T023` and `T024`, run `T025`, then `T026`
- Track E: after `T020` and `T030`, run `T031`, `T032`, `T033`, `T034`, and `T035`, then `T036`
- Track F: after `T040`, run `T041` and `T042`, then `T043`

Primary merge points:

- `T020` for evaluator work
- `T040` for adversarial aggregation
- `T044` for the first autonomous optimize loop

## Definition Of Done

The backlog is complete when all of the following are true:

- `evaluate` works end-to-end from YAML
- `attack` works end-to-end from YAML
- `optimize` runs at least one meaningful search loop
- every run writes replayable artifacts
- the frontier logic excludes rejected candidates
- at least two literature-aligned failures are reproduced
- a report names the next most informative experiment
- strong promoted results carry proof status and formal-claim linkage or are explicitly marked `empirical_only`

At that point, the repo has a real autonomous evaluator, not just design docs.
