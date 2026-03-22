# autopuf

Autonomous adversarial evaluator and optimizer for PUF research.

This repository contains the working implementation and operating docs for an autonomous, falsification-first optimizer for PUF research.

The system does not try to "read papers better." It tries to find the best surviving design under attack, noise, drift, and deployment constraints.

Core idea:

`x* = argmax_x min_a Score(x, a, world)`

Where:

- `x` is a candidate design
- `a` is the strongest attack the system can find
- `world` is the evaluation environment, including noise, drift, readout limits, and protocol constraints
- `Score` is a multi-objective utility over security, robustness, cost, and usability

This is the smallest core that is both useful and achievable:

- useful because it can eliminate weak designs, rank surviving candidates, and suggest the next most informative experiment
- achievable because `v1` can run fully in software against known public results

## Start Here

For José Senart, or anyone touching the repo for the first time, this is the clean path:

1. Bootstrap the repo:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e .
cd formal && lake build && cd ..
```

2. Run one evaluation:

```bash
.venv/bin/python -m pufopt.cli evaluate \
  --candidate candidates/baseline-classical-crp-001.yaml \
  --world configs/worlds/lab-clean-v1.yaml
```

3. Run one full optimization loop:

```bash
.venv/bin/python -m pufopt.cli optimize \
  --suite suites/v1-auth-search.yaml
```

4. Inspect the results:

```bash
.venv/bin/python -m pufopt.cli frontier --run artifacts/runs/<run_id>
.venv/bin/python -m pufopt.cli report --run artifacts/runs/<run_id>
```

What exists today:

- working `evaluate`, `attack`, `optimize`, `frontier`, and `report` commands
- working `pufopt.ops` commands for `next-task`, `pack-context`, `verify-task`, `promote-task`, and `formalize-claim`
- starter candidate and world libraries
- runnable suite templates for smoke, attack-analysis, short optimization, and regression validation
- two baseline candidate families
- two baseline world families
- five attack families
- constrained scoring and frontier maintenance
- a functioning Lean workspace and proof-status plumbing
- formal claim bridge artifacts in run outputs
- bounded Python/Lean differential checks for `classical_crp`
- externalized heuristic coefficients in `configs/heuristics/attacks.yaml`
- externalized regression expectations in `tests/fixtures/regression_expectations.yaml`

What is still explicitly unfinished:

- broader starter coverage beyond the current baseline and regression libraries

## Current Status

Implemented now:

- foundations through package, schema, artifacts, CLI, tests, and Lean workspace
- candidate/world registries and baseline families
- honest evaluation, constraints, scoring, and proof-status tagging
- modeling, replay, nearest-match, CRP exhaustion, and drift-abuse attacks
- adversarial evaluation, frontier maintenance, mutation, scheduling, and optimization
- a working delivery control plane for task selection, context packing, verification, promotion, and run formalization

Remaining work:

- broader formal-family coverage beyond `classical_crp`
- deeper formal claims beyond `specified` bridge status
- richer starter libraries and more varied search spaces

Validation note:

- the attack coefficients and regression thresholds are now externalized and tagged as `heuristic`
- they are validation scaffolding for instrument correctness
- they are not claimed as literature-derived numeric constants

## Mission

`autopuf` has two missions, but only one primary mission.

Primary mission:

- build an autonomous evaluator and optimizer for PUF research

Embedded mission:

- build a formal language and proof environment for PUF security claims using Lean

Decision:

- optimize for `Mission 1` utility first
- embed `Mission 2` as a formal spine from day 0

This means:

- Python is the execution substrate for evaluation, attacks, search, artifacts, and reporting
- Lean is the truth anchor for abstract protocol semantics, security games, proof obligations, and proof status
- promoted strong claims must carry formal status, even when they are not yet fully proved

## Goals

- Build an autonomous search loop for PUF authentication designs.
- Evaluate candidate designs against adversarial attacks and real-world perturbations.
- Recover known failure modes from the literature as regression tests.
- Produce a ranked frontier of surviving candidates and the next most informative experiment.
- Add a formal spine that sharpens claims, tracks assumptions, and raises the quality bar for promoted results.

## Non-Goals

- A Lean-only implementation of the whole repository
- Full formal verification of every protocol and result in `v1`
- Wet-lab control or direct hardware orchestration in `v1`
- General scientific autonomy across unrelated domains
- Replacing researchers with unconstrained idea generation

## `v1` Scope

`v1` focuses on authentication-like PUF systems, not the full space of quantum cryptography.

Included:

- classical PUF-style challenge-response systems
- optical or photonic readout variants
- hybrid designs that mix classical PUF assumptions with quantum-inspired or quantum-network-compatible constraints
- attack search over modeling, replay, nearest-match counterfeiting, CRP exhaustion, and drift/noise
- a Lean formal core for candidate semantics, verifier/adversary roles, security games, and proof-status tracking

Deferred:

- full end-to-end proof of the entire optimizer stack
- full UC-security proof search
- advanced quantum protocol synthesis
- laboratory device control
- materials discovery loops

## Why This Architecture

Any autonomous research system in this space needs all three of these:

1. A generator that proposes candidate designs
2. An adversary that tries to break them
3. An evaluator that scores survival under realistic conditions

Without a falsifier, the system is just automated ideation.
Without an evaluator, the system cannot tell whether a result is correct.
Without a search loop, the system cannot optimize.

For this repo, utility comes first:

- the empirical engine decides what is promising
- the formal engine decides what is precisely claimed
- strong results are only promoted when both layers agree on what the claim means

## System Overview

The system is a closed loop:

1. Generate candidate design
2. Instantiate world conditions
3. Evaluate honest performance
4. Run adversarial search
5. Aggregate score and constraints
6. Formalize strong or promoted claims
7. Update frontier
8. Choose next candidate or next experiment

Outputs:

- best surviving candidates
- Pareto frontier
- failed candidates with reasons
- attack traces
- uncertainty report
- next most informative experiment
- proof status for promoted claims

## Target Repo Layout

```text
.
├── README.md
├── AGENTS.md
├── TASKS.md
├── WORKFLOWS.md
├── TASK_TEMPLATE.md
├── RUNBOOK.md
├── pyproject.toml
├── formal/
│   ├── lean-toolchain
│   ├── lakefile.lean
│   ├── Main.lean
│   └── Autopuf/
│       ├── Model.lean
│       ├── Games.lean
│       ├── Claims.lean
│       └── Bridge.lean
├── ops/
│   ├── tasks/
│   └── templates/
│       ├── task.yaml
│       ├── research-run.yaml
│       ├── formal-claim.yaml
│       └── promotion.yaml
├── src/
│   └── pufopt/
│       ├── cli.py
│       ├── config.py
│       ├── types.py
│       ├── formal/
│       │   ├── bridge.py
│       │   └── proof_status.py
│       ├── loop/
│       │   ├── search.py
│       │   ├── scheduler.py
│       │   └── frontier.py
│       ├── candidates/
│       │   ├── registry.py
│       │   ├── factory.py
│       │   └── mutations.py
│       ├── worlds/
│       │   ├── registry.py
│       │   ├── noise.py
│       │   └── drift.py
│       ├── evaluators/
│       │   ├── honest.py
│       │   ├── adversarial.py
│       │   ├── scoring.py
│       │   └── constraints.py
│       ├── attacks/
│       │   ├── base.py
│       │   ├── modeling.py
│       │   ├── replay.py
│       │   ├── nearest_match.py
│       │   ├── crp_exhaustion.py
│       │   └── drift_abuse.py
│       ├── experiments/
│       │   ├── suites.py
│       │   ├── selection.py
│       │   └── reports.py
│       └── storage/
│           ├── io.py
│           ├── schema.py
│           └── artifacts.py
├── configs/
│   ├── search/
│   ├── worlds/
│   └── scoring/
├── candidates/
├── suites/
├── artifacts/
│   ├── runs/
│   ├── reports/
│   └── frontier/
└── tests/
```

## Toolchain Contract

For deterministic execution, the repo uses these command conventions:

- `python3` is the canonical Python command in docs and task manifests
- `pip3` is the canonical package installer command in docs and task manifests
- project-local installs and CLI runs should use `.venv/bin/python` after bootstrap
- Lean commands run from `formal/`, not the repo root

Minimum environment:

- Python `3.11+`
- Git on `PATH`
- Lean 4 and `lake` on `PATH`

Bootstrap expectation:

- create a local virtual environment with `python3 -m venv .venv`
- use `.venv/bin/python` and `.venv/bin/pip` for repo-local installs and execution

If the environment does not satisfy this contract, `T000` should remain `blocked` until the toolchain is fixed.

## Main Abstractions

### Candidate

A candidate is a complete design hypothesis that can be evaluated.

Examples:

- challenge sampling strategy
- feature extraction pipeline
- thresholding policy
- enrollment budget
- helper data method
- readout mode
- session refresh policy

Candidate contract:

```python
class Candidate(Protocol):
    id: str
    family: str
    params: dict[str, Any]

    def build(self) -> "BuiltCandidate": ...
```

### World

A world defines the environment in which evaluation happens.

Examples:

- sensor noise
- environmental drift
- readout latency budget
- adversary query budget
- allowed CRPs
- verifier trust assumptions

World contract:

```python
class World(Protocol):
    id: str
    params: dict[str, Any]

    def sample(self, seed: int) -> "WorldInstance": ...
```

### Attack

An attack is an optimizer over adversarial actions.

Examples:

- modeling attack
- replay attack
- nearest-match counterfeit attack
- CRP exhaustion
- verifier abuse

Attack contract:

```python
class Attack(Protocol):
    name: str

    def run(
        self,
        candidate: "BuiltCandidate",
        world: "WorldInstance",
        budget: "AttackBudget",
    ) -> "AttackResult": ...
```

### Evaluator

The evaluator computes honest performance, adversarial performance, and aggregate score.

Evaluator contract:

```python
class Evaluator(Protocol):
    def evaluate(
        self,
        candidate: Candidate,
        world: World,
        attacks: list[Attack],
    ) -> "EvaluationResult": ...
```

### Formal Claim

A formal claim captures the abstract meaning of a promoted result.

It is the formalized statement of:

- what candidate family is being discussed
- under which assumptions
- in which security game
- with what proof status

Formal claim contract:

```python
class FormalClaim(Protocol):
    id: str
    candidate_family: str
    security_game: str
    assumptions: list[str]
    proof_status: str
```

## Strong Result Policy

Formalization is triggered by a machine-readable strong-result policy.

Default rule:

- a result is `strong` if it is a valid survivor and at least one of these is true:
  - it enters or updates the frontier
  - it exceeds a configured score threshold
  - it exceeds a configured improvement threshold over baseline
- a result is `surprising` if it contradicts an expected regression boundary or materially exceeds prior baselines by a configured margin

`v1` should keep this policy in the scoring or run configuration rather than in code-only defaults.

## Canonical Metrics

Every evaluation returns these metrics:

- `far`: false accept rate
- `frr`: false reject rate
- `eer`: equal error rate if applicable
- `min_entropy_estimate`
- `modeling_attack_success`
- `replay_attack_success`
- `counterfeit_attack_success`
- `crp_lifetime`
- `latency_ms`
- `readout_cost`
- `enrollment_cost`
- `robustness_under_drift`
- `confidence`

`v1` must also record:

- exact seeds
- exact world parameters
- attack budget used
- artifacts required to reproduce the result
- `formal_claim_id` when available
- `proof_status` for promoted or high-salience results

## Proof Status

Promoted claims must carry one of these proof statuses:

- `empirical_only`
- `specified`
- `partially_proved`
- `proved`
- `counterexample_found`

`v1` does not require every result to be proved.
`v1` does require strong results to be either formalized or explicitly marked as `empirical_only`.

## Constraints

A candidate is invalid if any hard constraint fails.

Default hard constraints:

- `far <= max_far`
- `frr <= max_frr`
- `latency_ms <= max_latency_ms`
- `crp_lifetime >= min_crp_lifetime`
- `readout_cost <= max_readout_cost`
- `confidence >= min_confidence`

Invalid candidates are not scored on the frontier.
They are retained as negative results.

## Scoring

`v1` uses constrained multi-objective scoring with explicit hard filters and a weighted utility for survivors.

```python
score =
    w_security * security_score +
    w_robustness * robustness_score +
    w_efficiency * efficiency_score +
    w_operability * operability_score
```

Recommended decomposition:

```text
security_score
  = 1
  - max(
        modeling_attack_success,
        replay_attack_success,
        counterfeit_attack_success
    )

robustness_score
  = normalized(robustness_under_drift, min_entropy_estimate)

efficiency_score
  = normalized_inverse(latency_ms, readout_cost, enrollment_cost)

operability_score
  = normalized(crp_lifetime, verifier_assumption_penalty)
```

Important rule:

- score is for ranking survivors
- constraints are for rejecting unsafe designs
- attack success must never be hidden inside a soft average

## Search Strategy

`v1` uses a practical hybrid search:

1. seed hand-designed baselines from literature
2. mutate parameters locally
3. run Bayesian or evolutionary search over candidate space
4. periodically resample worlds and attack budgets
5. preserve Pareto frontier

The scheduler chooses between:

- exploitation of promising regions
- exploration of under-sampled regions
- falsification of surprisingly strong candidates
- experiment selection under uncertainty

## Core Loop Pseudocode

```python
def optimize(search_space, world_bank, attack_bank, budget):
    frontier = ParetoFrontier()
    queue = seed_candidates(search_space)

    while budget.remaining():
        candidate = scheduler.pick_candidate(queue, frontier)
        world = scheduler.pick_world(world_bank, frontier)
        attacks = scheduler.pick_attacks(attack_bank, candidate, world)

        result = evaluator.evaluate(candidate, world, attacks)
        score = scorer.compute(result)
        formal = formalizer.sync_if_needed(candidate, score)
        storage.write_result(result)
        storage.write_score(score)
        storage.write_formal_status(formal)
        frontier.update(score)

        if score.is_survivor:
            queue.extend(mutate(candidate, result))
        else:
            queue.extend(learn_from_failure(candidate, result))

    return frontier
```

## Search Space Representation

Candidates are declared as YAML.

Example:

```yaml
id: baseline-optical-auth-001
family: optical_auth
params:
  feature_extractor: spectral_histogram_v1
  threshold_policy: global_margin
  enrollment_samples: 64
  challenge_sampler: random_uniform
  helper_data: none
  crp_refresh_policy: one_time_use
  sensor_mode: standard_camera
```

Worlds are also YAML:

```yaml
id: phone-reader-indoor-v1
params:
  sensor_noise_sigma: 0.03
  temperature_shift_c: 6
  illumination_jitter: 0.12
  angle_variation_deg: 9
  attacker_query_budget: 5000
  verifier_model: honest
```

Suites define the optimization job:

```yaml
id: v1-auth-search
search:
  algorithm: evolutionary
  max_iterations: 200
  seeds:
    - candidates/baseline-optical-auth-001.yaml
    - candidates/baseline-classical-crp-001.yaml
worlds:
  - configs/worlds/phone-reader-indoor-v1.yaml
  - configs/worlds/lab-clean-v1.yaml
attacks:
  - modeling
  - replay
  - nearest_match
  - crp_exhaustion
scoring:
  file: configs/scoring/default.yaml
```

## Required `v1` Attacks

### Modeling Attack

Goal:

- learn the candidate response surface well enough to impersonate or predict responses

Initial implementation:

- simple regression
- tree ensemble
- kernel baseline

Success metric:

- impersonation success or prediction accuracy beyond allowed threshold

### Replay Attack

Goal:

- reuse observed or leaked responses

Success metric:

- authentication success after prior observation

### Nearest-Match Counterfeit Attack

Goal:

- synthesize or select the closest observed fingerprint under the acceptance threshold

Success metric:

- counterfeit acceptance rate

### CRP Exhaustion Attack

Goal:

- deplete safe authentication sessions or exploit challenge reuse pressure

Success metric:

- lifetime collapse under bounded query budget

### Drift Abuse Attack

Goal:

- exploit environmental sensitivity to force false accept or false reject behavior

Success metric:

- attack success under allowed perturbation budget

## Validation Set

`v1` is only acceptable if it recovers known qualitative results.

Regression targets:

1. Weak classical-readout quantum-PUF-like constructions should fail under modeling attack.
2. Designs with one-time or limited CRP assumptions should expose finite session lifetime.
3. Practical remote authentication setups should show sensitivity to verifier trust and database assumptions.

Pass criteria:

- the system reproduces at least two published failure modes
- the system surfaces at least one surviving region or tradeoff frontier
- all results are reproducible from stored artifacts

## Artifact Model

Each run writes a directory:

```text
artifacts/runs/<run_id>/
├── suite.yaml
├── candidate/
│   └── candidate.yaml
├── world/
│   └── world.yaml
├── honest/
│   └── metrics.json
├── attacks/
│   └── *.json
├── formal/
│   ├── claim.yaml
│   ├── proof_status.json
│   └── differential_check.json
├── score/
│   └── score.json
├── frontier/
│   └── update.json
├── planner/
│   └── decision.json
├── logs.txt
└── summary.md
```

This keeps every result replayable and reviewable.

## CLI Plan

The CLI is the public interface of the system.

Required commands:

```bash
.venv/bin/python -m pufopt.cli optimize --suite suites/v1-auth-search.yaml
.venv/bin/python -m pufopt.cli evaluate --candidate candidates/foo.yaml --world configs/worlds/bar.yaml
.venv/bin/python -m pufopt.cli attack --candidate candidates/foo.yaml --world configs/worlds/bar.yaml --attack modeling
.venv/bin/python -m pufopt.cli frontier --run artifacts/runs/<run_id>
.venv/bin/python -m pufopt.cli report --run artifacts/runs/<run_id>
```

## Implementation Order

### Milestone 0

- bootstrap and validate the Python and Lean toolchains
- create package skeleton
- define types and schemas
- implement local artifact storage
- implement CLI stubs
- initialize the Lean workspace and formal claim schema

### Milestone 1

- implement two candidate families
- implement two world models
- implement honest evaluator
- implement modeling and replay attacks
- run deterministic smoke tests
- define the abstract Lean model for candidates, verifiers, adversaries, and security games

### Milestone 2

- implement frontier and scheduler
- add nearest-match and CRP exhaustion attacks
- add constrained scoring
- add run reports
- add proof-status plumbing and bounded differential checks for supported families

### Milestone 3

- reproduce literature-aligned failure modes
- tune search loop
- generate first useful Pareto frontier
- rank next experiments
- attach formal status to strong promoted results

## Testing Strategy

Unit tests:

- schema validation
- deterministic world generation
- metric correctness
- score correctness
- attack contract compliance

Integration tests:

- end-to-end evaluation on a toy candidate
- end-to-end optimize loop on a small suite
- artifact replay from stored run

Regression tests:

- known-bad candidate remains breakable
- known-limited candidate remains CRP-limited
- known-robust toy candidate survives under bounded noise

## Success Criteria

The project is successful when a researcher can do all of the following without editing source code:

1. Add a new candidate in YAML
2. Add a new world in YAML
3. Run the optimizer
4. Inspect attack traces and frontier output
5. Decide what to test next

The project is valuable when the system can:

- eliminate weak designs automatically
- produce non-obvious tradeoffs
- recover known literature boundaries
- recommend the next most informative experiment
- say what is formally specified, partially proved, or still empirical-only

## Immediate Build Plan

First build the evaluator, not the fancy search.

Order of truth:

1. honest evaluation works
2. attacks work
3. constraints reject bad designs
4. scoring ranks survivors
5. strong results carry proof status
6. frontier and search improve over baseline

If the evaluator is weak, the optimizer will confidently optimize the wrong thing.
If the formal layer is absent, promoted claims will drift semantically over time.

The concrete execution backlog lives in [TASKS.md](/Users/tomas/code/pufs/TASKS.md).

The autonomous execution layer lives in:

- [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md)
- [TASK_TEMPLATE.md](/Users/tomas/code/pufs/TASK_TEMPLATE.md)
- [RUNBOOK.md](/Users/tomas/code/pufs/RUNBOOK.md)

## Open Questions For `v2`

- how far to extend formal proofs beyond proof-status tracking and bounded differential checks
- when to add hardware-in-the-loop evaluation
- how to translate materials observations into cryptographic metrics
- how to optimize experiment selection by expected information gain
- how to compare classical PUF, hybrid PUF, qPUF, and non-PUF baselines under one objective
