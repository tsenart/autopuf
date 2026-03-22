# Context

## Objective

Provide the initial CLI surface with the planned command names and stable help output.

## Relevant Design Decisions

- The CLI is the public interface of the system.
- Each planned command should parse cleanly even before implementation logic exists.
- The parser should be testable without invoking actual optimization logic.

## Relevant Files

- [README.md](/Users/tomas/code/pufs/README.md)
- [src/pufopt/cli.py](/Users/tomas/code/pufs/src/pufopt/cli.py)
- [tests/test_cli_smoke.py](/Users/tomas/code/pufs/tests/test_cli_smoke.py)

## Acceptance Criteria

- these commands exist and print structured help:
  - optimize
  - evaluate
  - attack
  - frontier
  - report
- command parsing is covered by tests

## Non-Goals

- no business logic behind the subcommands yet
- no config loading yet

## Open Risks

- later command-specific options may force parser changes
- placeholder handlers could hide missing implementation if not clearly signposted

