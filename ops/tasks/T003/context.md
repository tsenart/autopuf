# Context

## Objective

Implement the external schema layer so candidates, worlds, suites, and formal claims can be loaded safely from YAML or JSON.

## Relevant Design Decisions

- External specs must fail closed with actionable validation messages.
- The schema layer should normalize both README-style optimization suites and runbook-style research runs.
- Formal claims must validate against the proof-status vocabulary.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [TASKS.md](/Users/tomas/code/pufs/TASKS.md)
- [src/pufopt/types.py](/Users/tomas/code/pufs/src/pufopt/types.py)
- [src/pufopt/storage/schema.py](/Users/tomas/code/pufs/src/pufopt/storage/schema.py)

## Acceptance Criteria

- invalid candidate specs are rejected with actionable errors
- invalid world specs are rejected with actionable errors
- invalid suite specs are rejected with actionable errors
- invalid formal claim manifests are rejected with actionable errors
- schema validation is covered by unit tests

## Non-Goals

- no candidate registry yet
- no world registry yet
- no run artifact writing yet

## Open Risks

- suite schema drift between optimization jobs and research-run manifests
- under-validating nested params and getting confusing downstream failures

