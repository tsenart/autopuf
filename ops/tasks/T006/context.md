# Context

## Objective

Establish the default local test command, smoke coverage, and deterministic utilities used by the rest of the repo.

## Relevant Design Decisions

- The repo should have one default test command for local verification.
- A smoke test should prove the package and CLI load path works.
- Test utilities should make deterministic seeding easy to reuse.

## Relevant Files

- [pyproject.toml](/Users/tomas/code/pufs/pyproject.toml)
- [tests/test_cli_smoke.py](/Users/tomas/code/pufs/tests/test_cli_smoke.py)
- [tests/utils.py](/Users/tomas/code/pufs/tests/utils.py)

## Acceptance Criteria

- unit tests run with one command
- a minimal smoke test passes
- deterministic seeding utilities are available to tests

## Non-Goals

- no CI provider integration yet
- no benchmark or slow-test taxonomy yet

## Open Risks

- later adoption of another test runner
- helpers existing without enough conventions around usage

