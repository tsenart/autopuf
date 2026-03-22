# Context

## Objective

Make proof status and formal claims first-class, validated artifacts across the Python and Lean sides of the repo.

## Relevant Design Decisions

- Proof status is a fixed vocabulary shared across workflows.
- Formal claim manifests must validate before promotion uses them.
- Promotion artifacts must record formal-gate outcomes.

## Relevant Files

- [src/pufopt/types.py](/Users/tomas/code/pufs/src/pufopt/types.py)
- [src/pufopt/storage/schema.py](/Users/tomas/code/pufs/src/pufopt/storage/schema.py)
- [ops/templates/formal-claim.yaml](/Users/tomas/code/pufs/ops/templates/formal-claim.yaml)
- [ops/templates/promotion.yaml](/Users/tomas/code/pufs/ops/templates/promotion.yaml)
- [formal/Autopuf/Claims.lean](/Users/tomas/code/pufs/formal/Autopuf/Claims.lean)

## Acceptance Criteria

- proof status values are defined and validated
- formal claim manifests validate
- evaluation artifacts can reference `formal_claim_id` and `proof_status`
- promotion artifacts can record formal-gate outcomes

## Non-Goals

- no proof search yet
- no Python-Lean bridge execution yet

## Open Risks

- vocabulary drift between the Python and Lean representations
- formal-claim templates becoming richer before the bridge exists

