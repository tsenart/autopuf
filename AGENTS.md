# AGENTS

This file defines the agent operating system for `autopuf`.

Agents are not generic assistants. Each agent owns a sharply bounded responsibility, produces machine-readable artifacts, and is evaluated on falsification quality, reproducibility, and decision value.

Task sequencing and dependency order live in [TASKS.md](/Users/tomas/code/pufs/TASKS.md).
Execution state machines and gates live in [WORKFLOWS.md](/Users/tomas/code/pufs/WORKFLOWS.md).

## Operating Principle

The system is adversarial by design.

The primary mission is utility:

- eliminate weak designs
- rank survivors
- choose the next best experiment

The formal layer exists to strengthen promoted claims, not to replace empirical evaluation.

Every strong result must survive all three empirical checks:

1. honest evaluation
2. adversarial attack
3. replayable reproduction

Every promoted strong claim must also carry formal status:

4. formal specification of the claim being promoted

No agent is allowed to promote a result directly to "good." Agents can only:

- propose
- break
- measure
- verify
- schedule

## Core Loop

The system runs this loop:

1. `Generator` proposes candidate
2. `World Builder` instantiates environment
3. `Honest Evaluator` measures baseline performance
4. `Red Team` attacks candidate
5. `Scorer` applies constraints and utility
6. `Frontier Keeper` updates best-known survivors
7. `Planner` selects next candidate or experiment

## Global Rules

- All agents must write artifacts to disk.
- All outputs must include exact inputs, seeds, and config references.
- All agents must fail closed on invalid schemas.
- All claims must be linked to metrics or attack traces.
- Any non-reproducible result is automatically downgraded to `untrusted`.
- Attack success always overrides optimistic narrative summaries.
- Strong results must carry `proof_status` and `formal_claim_id`, or be explicitly marked `empirical_only`.

## Shared Schemas

Every agent reads and writes the same canonical objects.

Required object types:

- `CandidateSpec`
- `WorldSpec`
- `AttackSpec`
- `EvaluationResult`
- `AttackResult`
- `ScoreCard`
- `FrontierEntry`
- `PlanDecision`
- `FormalClaimSpec`
- `ProofStatus`

The implementation should keep these types in `src/pufopt/types.py` and validate external files at load time.

## Agent Roster

### 1. Generator

Purpose:

- create or mutate candidate designs

Inputs:

- search configuration
- prior results
- frontier

Outputs:

- `CandidateSpec`

Allowed actions:

- seed baseline candidates
- mutate parameters
- crossover promising candidates if enabled
- propose ablation candidates

Forbidden actions:

- directly setting score
- ignoring hard constraints from prior failures

Success metric:

- percentage of proposals that produce novel information, not just duplicate failures

### 2. World Builder

Purpose:

- instantiate the environment for evaluation

Inputs:

- `WorldSpec`
- scheduler decision

Outputs:

- concrete world instance with resolved randomness

Responsibilities:

- sample noise
- sample drift
- enforce resource budgets
- expose verifier model assumptions

Success metric:

- deterministic replay from stored seed

### 3. Honest Evaluator

Purpose:

- measure nominal candidate performance without adversarial optimization

Inputs:

- built candidate
- world instance

Outputs:

- honest metrics

Responsibilities:

- FAR, FRR, EER if relevant
- entropy estimate
- latency
- cost
- CRP lifetime estimate

Failure condition:

- any missing metric required by scoring

### 4. Red Team

Purpose:

- break the candidate

Inputs:

- built candidate
- world instance
- attack budget

Outputs:

- one `AttackResult` per attack family

Required `v1` attack families:

- `modeling`
- `replay`
- `nearest_match`
- `crp_exhaustion`
- `drift_abuse`

Behavior:

- maximize attack success under declared budget
- preserve intermediate traces
- record best-found attack parameters

Success metric:

- attack quality, not runtime vanity

### 5. Scorer

Purpose:

- turn metrics and attack outputs into constraint decisions and ranked utility

Inputs:

- honest metrics
- attack results
- scoring config

Outputs:

- `ScoreCard`

Behavior:

- apply hard constraints first
- score only surviving candidates
- record exact reasons for rejection

Hard rule:

- a candidate rejected by constraints cannot appear on the frontier

### 6. Frontier Keeper

Purpose:

- maintain the current set of non-dominated survivors

Inputs:

- `ScoreCard`
- prior frontier

Outputs:

- updated frontier
- dominated candidate list

Responsibilities:

- de-duplicate equivalent candidates
- track best-known version per family
- preserve historical frontier snapshots

Success metric:

- stable and reproducible frontier updates

### 7. Planner

Purpose:

- choose the next highest-value action

Inputs:

- frontier
- failures
- uncertainty map
- budget remaining

Outputs:

- `PlanDecision`

Allowed decisions:

- explore candidate region
- exploit promising region
- intensify attack on strong survivor
- resample under harder worlds
- schedule discriminating experiment

Planner objective:

- maximize expected information gain per unit budget

### 8. Formalizer

Purpose:

- translate promoted or high-salience results into formal claims and track proof status

Inputs:

- candidate family semantics
- threat model
- promoted result summary
- claim templates

Outputs:

- `FormalClaimSpec`
- proof-status artifact
- Lean modules or references

Responsibilities:

- define abstract protocol semantics
- define the security game being claimed
- record assumptions explicitly
- assign or update `proof_status`
- support bounded differential checks between Python and Lean semantics

Success metric:

- precision of assumptions and stable mapping from empirical result to formal claim

## Artifact Contracts

Each agent writes its output to a standard location inside the current run directory.

Example:

```text
artifacts/runs/<run_id>/
├── candidate/
│   └── candidate.yaml
├── world/
│   └── world.yaml
├── honest/
│   └── metrics.json
├── attacks/
│   ├── modeling.json
│   ├── replay.json
│   ├── nearest_match.json
│   ├── crp_exhaustion.json
│   └── drift_abuse.json
├── formal/
│   ├── claim.yaml
│   └── proof_status.json
├── score/
│   └── score.json
├── frontier/
│   └── update.json
└── planner/
    └── decision.json
```

These files are the handoff layer between agents.

## Status Vocabulary

Use this exact status vocabulary:

- `valid`
- `invalid`
- `survivor`
- `dominated`
- `rejected`
- `untrusted`
- `reproduced`

Do not invent synonyms in artifacts.

## Review Gates

### Gate 1: Schema Gate

The run stops if candidate, world, or scoring config is invalid.

### Gate 2: Metric Gate

The run stops if honest evaluation does not produce required metrics.

### Gate 3: Attack Gate

The run is marked `untrusted` if any required attack family did not run.

### Gate 4: Reproducibility Gate

The run is marked `untrusted` if seeds or configs are missing.

### Gate 5: Formal Claim Gate

Strong or promoted results must either:

- link to a formal claim and proof status
- or be explicitly labeled `empirical_only`

## Decision Heuristics

The planner should use these defaults:

- prefer breaking strong candidates over generating more weak ones
- prefer experiments that distinguish between two nearby explanations
- prefer low-cost worlds early and hard worlds later
- prefer ablations when a candidate looks surprisingly strong
- prefer local mutations around frontier candidates

## Negative Results Policy

Negative results are first-class outputs.

Store:

- rejected candidates
- failed attacks
- broken assumptions
- frontier demotions

Every negative result must include:

- why it failed
- under what world it failed
- whether the failure is likely structural or parameter-specific

## Minimal Execution Script

The system should support this control flow:

```python
candidate = generator.next()
world = world_builder.instantiate()
honest = honest_evaluator.run(candidate, world)
attacks = red_team.run_all(candidate, world)
score = scorer.compute(candidate, world, honest, attacks)
formal = formalizer.sync(candidate, score)
frontier = frontier_keeper.update(score)
decision = planner.decide(frontier, score)
```

## `v1` Responsibilities By File

Map initial implementation ownership like this:

- `src/pufopt/types.py`: shared types and schemas
- `src/pufopt/storage/`: artifact contracts and replay
- `src/pufopt/evaluators/honest.py`: nominal evaluation
- `src/pufopt/attacks/modeling.py`: first serious adversary
- `src/pufopt/attacks/replay.py`: low-complexity adversary
- `src/pufopt/evaluators/scoring.py`: constraint and utility logic
- `src/pufopt/loop/frontier.py`: Pareto maintenance
- `src/pufopt/loop/search.py`: loop orchestrator
- `src/pufopt/cli.py`: public interface
- `src/pufopt/formal/bridge.py`: Python and Lean claim mapping
- `formal/Autopuf/`: Lean models, games, and claims

## Agent Quality Bar

An agent is only useful if it improves researcher decision quality.

Minimum acceptable behavior:

- no silent failure
- no hidden defaults in scoring
- no irreproducible success claims
- no ranking without attached attack evidence

Desired behavior:

- concise artifacts
- clear failure reasons
- stable re-runs under fixed seeds
- useful next-step decisions

## Human-in-the-Loop Policy

Humans still control:

- search-space definition
- scoring weights
- hard constraints
- acceptance of surprising results
- promotion of `v1` findings into papers or experiments

Agents control:

- search within declared space
- attack optimization
- repeatable evaluation
- prioritization of next actions
- formalization of promoted claims within declared abstractions

## Definition Of Done For `v1`

`v1` is done when all of the following are true:

1. A researcher can add a new candidate without editing Python.
2. The system can run all required attacks automatically.
3. Results are stored as replayable artifacts.
4. The frontier excludes constrained-out candidates.
5. The planner emits a concrete next action.
6. At least two known literature-aligned failure modes are reproduced.
7. Strong promoted results carry proof status and link to a formal claim or are explicitly marked `empirical_only`.

When these conditions hold, the project has crossed from "interesting framework" into "real autonomous evaluator."
