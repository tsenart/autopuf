# Regression Fixtures

These fixtures are intentionally weak or assumption-limited.

They are not claims about any one published implementation.
They are compact, executable stand-ins for public boundary types that `autopuf` should keep detecting over time.
Their thresholds are validation scaffolding, not literature-calibrated constants.

Current boundaries encoded here:

- `regression-modeling-vulnerable-crp-001`
  - small CRP-style construction
  - expected signal: `modeling_attack_success >= 0.80`
  - provenance: `heuristic`

- `regression-crp-limited-crp-001`
  - limited challenge space with aggressive replay window
  - expected signal:
    - `crp_exhaustion_attack_success >= 0.80`
    - `reduced_crp_lifetime <= 1`
  - provenance: `heuristic`

- `regression-trust-limited-remote-auth-001`
  - remote-auth-like optical configuration under a leaky verifier/database model
  - expected signal:
    - `replay_attack_success >= 0.70`
    - `counterfeit_attack_success >= 0.80`
  - provenance: `heuristic`
