"""CLI for the autopuf delivery control plane."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pufopt.ops.control import (
    find_next_task,
    formalize_claim,
    pack_context,
    promote_task,
    verify_task,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the delivery control-plane parser."""
    parser = argparse.ArgumentParser(
        prog="pufopt.ops",
        description="Autonomous task-control plane for the autopuf delivery workflow.",
    )
    subparsers = parser.add_subparsers(dest="command")

    next_task = subparsers.add_parser("next-task", help="Print the next unblocked task.")
    next_task.add_argument("--tasks-root", default="ops/tasks", help="Task directory root.")
    next_task.set_defaults(handler=_handle_next_task)

    pack = subparsers.add_parser("pack-context", help="Write context.md for a task.")
    pack.add_argument("--task", required=True, help="Task identifier, for example T031.")
    pack.add_argument("--tasks-root", default="ops/tasks", help="Task directory root.")
    pack.add_argument("--repo-root", default=".", help="Repository root for relative paths.")
    pack.set_defaults(handler=_handle_pack_context)

    verify = subparsers.add_parser(
        "verify-task",
        help="Run commands, formal checks, red review, and reproduction for a task.",
    )
    verify.add_argument("--task", required=True, help="Task identifier, for example T031.")
    verify.add_argument("--tasks-root", default="ops/tasks", help="Task directory root.")
    verify.add_argument("--repo-root", default=".", help="Repository root for relative paths.")
    verify.set_defaults(handler=_handle_verify_task)

    promote = subparsers.add_parser("promote-task", help="Evaluate promotion gates for a task.")
    promote.add_argument("--task", required=True, help="Task identifier, for example T031.")
    promote.add_argument("--tasks-root", default="ops/tasks", help="Task directory root.")
    promote.add_argument("--repo-root", default=".", help="Repository root for relative paths.")
    promote.set_defaults(handler=_handle_promote_task)

    formalize = subparsers.add_parser(
        "formalize-claim",
        help="Refresh formal artifacts for an evaluation or optimization run.",
    )
    formalize.add_argument("--run", required=True, help="Run directory path.")
    formalize.set_defaults(handler=_handle_formalize_claim)

    return parser


def _handle_next_task(args: argparse.Namespace) -> int:
    task_id, reason = find_next_task(args.tasks_root)
    if task_id is None:
        print(f"No unblocked task found: {reason}")
        return 0
    print(f"task_id: {task_id}")
    print(f"reason: {reason}")
    print(f"path: {Path(args.tasks_root) / task_id / 'task.yaml'}")
    return 0


def _handle_pack_context(args: argparse.Namespace) -> int:
    context_path = pack_context(args.task, args.tasks_root, args.repo_root)
    print(f"Context packed: {context_path}")
    return 0


def _handle_verify_task(args: argparse.Namespace) -> int:
    artifacts = verify_task(args.task, args.tasks_root, args.repo_root)
    print(f"Verification written to {artifacts['verification']}")
    print(f"Formal check written to {artifacts['formal_check']}")
    print(f"Red review written to {artifacts['red_review']}")
    print(f"Reproduction report written to {artifacts['reproduction']}")
    return 0


def _handle_promote_task(args: argparse.Namespace) -> int:
    promotion_path, success = promote_task(args.task, args.tasks_root, args.repo_root)
    print(f"Promotion artifact: {promotion_path}")
    print(f"status: {'promoted' if success else 'rejected'}")
    return 0 if success else 1


def _handle_formalize_claim(args: argparse.Namespace) -> int:
    formal_dir, updated = formalize_claim(args.run)
    print(f"Formal artifacts written to {formal_dir}")
    print(f"proof_status: {updated.proof_status}")
    if updated.formal_claim_id is not None:
        print(f"formal_claim_id: {updated.formal_claim_id}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the delivery control-plane CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
