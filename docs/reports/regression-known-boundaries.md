# Regression Validation Report

Date:

- March 22, 2026

Suite:

- [regression-known-boundaries.yaml](/Users/tomas/code/pufs/suites/regression-known-boundaries.yaml)

Purpose:

- verify that `autopuf` still detects three expected boundary types
- do so with explicit heuristic provenance rather than implied literature calibration

Calibration status:

- attack coefficients: `heuristic`
- regression thresholds: `heuristic`
- citation status: `qualitative_literature_alignment_only`

## Observed Results

- `regression-modeling-vulnerable-crp-001`
  - `modeling_attack_success = 0.8173218`
  - `replay_attack_success = 0.8377044`
  - interpretation: the intentionally weak CRP construction remains clearly learnable and replayable

- `regression-crp-limited-crp-001`
  - `crp_exhaustion_attack_success = 0.85`
  - `reduced_crp_lifetime = 1`
  - rejection reason: `crp_lifetime below min_crp_lifetime (4 < 32)`
  - interpretation: the limited-use construction still collapses under query pressure and is correctly rejected

- `regression-trust-limited-remote-auth-001`
  - `replay_attack_success = 0.754471`
  - `counterfeit_attack_success = 0.88032675`
  - interpretation: the remote-auth-like optical setup remains fragile under a leaky verifier/database assumption

## Combined Suite Outcome

- iterations completed: `3`
- frontier count: `1`
- dominated count: `1`
- rejected count: `1`
- best survivor: `regression-modeling-vulnerable-crp-001`
- next suggested action: `increase_modeling_pressure`

## Meaning

- the validation harness is catching the intended failure shapes
- the result is about instrument behavior, not about claiming these exact numbers from papers
- the next scientific step is calibration against cited literature or datasets, not adding more hardcoded thresholds
