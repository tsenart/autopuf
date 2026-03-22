"""Rendering helpers for frontier and optimization reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from pufopt.storage.io import read_json_file


def load_frontier_snapshot(run_root: str | Path) -> dict[str, Any]:
    """Load the current frontier snapshot from a run directory."""
    return read_json_file(Path(run_root) / "frontier" / "update.json")


def render_frontier_snapshot(snapshot: Mapping[str, Any]) -> str:
    """Render a human-readable frontier summary."""
    lines = [
        "# Frontier",
        "",
        f"- frontier_count: {snapshot.get('counts', {}).get('frontier', 0)}",
        f"- dominated_count: {snapshot.get('counts', {}).get('dominated', 0)}",
        f"- rejected_count: {snapshot.get('counts', {}).get('rejected', 0)}",
    ]

    last_update = snapshot.get("last_update")
    if isinstance(last_update, Mapping):
        lines.extend(
            [
                f"- last_candidate: {last_update.get('candidate_id', 'n/a')}",
                f"- last_status: {last_update.get('status', 'n/a')}",
            ]
        )

    frontier = snapshot.get("frontier", [])
    if isinstance(frontier, list) and frontier:
        lines.append("")
        lines.append("## Survivors")
        lines.append("")
        for entry in frontier:
            if not isinstance(entry, Mapping):
                continue
            lines.append(
                "- "
                + f"{entry.get('candidate_id', 'n/a')} "
                + f"({entry.get('family', 'n/a')}) "
                + f"utility={entry.get('utility', 'n/a')}"
            )
    return "\n".join(lines) + "\n"


def render_optimization_summary(snapshot: Mapping[str, Any]) -> str:
    """Render the top-level markdown summary for an optimize run."""
    lines = [
        "# Optimization Summary",
        "",
        f"- run_id: {snapshot.get('run_id', 'n/a')}",
        f"- iterations_completed: {snapshot.get('iterations_completed', 0)}",
        f"- frontier_count: {snapshot.get('counts', {}).get('frontier', 0)}",
        f"- dominated_count: {snapshot.get('counts', {}).get('dominated', 0)}",
        f"- rejected_count: {snapshot.get('counts', {}).get('rejected', 0)}",
    ]
    best = snapshot.get("best")
    if isinstance(best, Mapping):
        lines.extend(
            [
                f"- best_candidate: {best.get('candidate_id', 'n/a')}",
                f"- best_family: {best.get('family', 'n/a')}",
                f"- best_utility: {best.get('utility', 'n/a')}",
            ]
        )
    next_action = snapshot.get("next_action")
    if isinstance(next_action, Mapping):
        lines.extend(
            [
                f"- next_action: {next_action.get('action', 'n/a')}",
                f"- next_reason: {next_action.get('reason', 'n/a')}",
            ]
        )
    lines.append("")
    lines.append("## Frontier")
    lines.append("")
    lines.extend(_frontier_lines(snapshot))
    return "\n".join(lines) + "\n"


def _frontier_lines(snapshot: Mapping[str, Any]) -> list[str]:
    """Render the frontier block without a nested top-level heading."""
    lines = [
        f"- frontier_count: {snapshot.get('counts', {}).get('frontier', 0)}",
        f"- dominated_count: {snapshot.get('counts', {}).get('dominated', 0)}",
        f"- rejected_count: {snapshot.get('counts', {}).get('rejected', 0)}",
    ]
    last_update = snapshot.get("last_update")
    if isinstance(last_update, Mapping):
        lines.extend(
            [
                f"- last_candidate: {last_update.get('candidate_id', 'n/a')}",
                f"- last_status: {last_update.get('status', 'n/a')}",
            ]
        )
    frontier = snapshot.get("frontier", [])
    if isinstance(frontier, list) and frontier:
        lines.append("")
        lines.append("### Survivors")
        lines.append("")
        for entry in frontier:
            if not isinstance(entry, Mapping):
                continue
            lines.append(
                "- "
                + f"{entry.get('candidate_id', 'n/a')} "
                + f"({entry.get('family', 'n/a')}) "
                + f"utility={entry.get('utility', 'n/a')}"
            )
    return lines
