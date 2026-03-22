"""Command-line entry point for autopuf."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from pufopt.attacks import run_attack
from pufopt.candidates.factory import build_candidate
from pufopt.evaluators.constraints import apply_constraints, load_constraint_config
from pufopt.evaluators.adversarial import REQUIRED_V1_ATTACKS, evaluate_with_attacks
from pufopt.evaluators.honest import evaluate_honest
from pufopt.evaluators.scoring import load_scoring_config, score_candidate
from pufopt.experiments.reports import (
    load_frontier_snapshot,
    render_frontier_snapshot,
)
from pufopt.formal.bridge import finalize_formal_artifacts, supports_formal_bridge
from pufopt.formal.proof_status import ensure_result_has_proof_status, proof_status_payload
from pufopt.loop.search import optimize_suite
from pufopt.storage.artifacts import create_run_layout, write_artifact, write_run_context
from pufopt.storage.io import write_yaml_atomic
from pufopt.storage.schema import load_candidate_spec, load_world_spec
from pufopt.types import AttackResult, BuiltCandidate, Metrics, ScoreCard, WorldInstance
from pufopt.worlds.registry import sample_world


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="pufopt",
        description="Autonomous adversarial evaluator and optimizer for PUF research.",
    )
    subparsers = parser.add_subparsers(dest="command")

    optimize = subparsers.add_parser("optimize", help="Run an optimization suite.")
    optimize.add_argument("--suite", required=True, help="Path to a suite YAML file.")
    optimize.add_argument(
        "--artifacts-root",
        default=None,
        help="Directory in which to create the suite run folder.",
    )
    optimize.set_defaults(handler=_handle_optimize)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate a candidate in a world.")
    evaluate.add_argument("--candidate", required=True, help="Path to a candidate YAML file.")
    evaluate.add_argument("--world", required=True, help="Path to a world YAML file.")
    evaluate.add_argument(
        "--artifacts-root",
        default="artifacts/runs",
        help="Directory in which to create the run folder.",
    )
    evaluate.add_argument(
        "--scoring-config",
        default="configs/scoring/default.yaml",
        help="Path to the scoring config YAML file.",
    )
    evaluate.add_argument(
        "--seed",
        type=int,
        default=1729,
        help="Deterministic evaluation seed.",
    )
    _add_attack_budget_arguments(evaluate)
    evaluate.set_defaults(handler=_handle_evaluate)

    attack = subparsers.add_parser("attack", help="Run a single attack.")
    attack.add_argument("--candidate", required=True, help="Path to a candidate YAML file.")
    attack.add_argument("--world", required=True, help="Path to a world YAML file.")
    attack.add_argument("--attack", dest="attack_name", required=True, help="Attack family name.")
    attack.add_argument(
        "--artifacts-root",
        default="artifacts/runs",
        help="Directory in which to create the run folder.",
    )
    attack.add_argument(
        "--seed",
        type=int,
        default=1729,
        help="Deterministic evaluation seed.",
    )
    _add_attack_budget_arguments(attack)
    attack.set_defaults(handler=_handle_attack)

    frontier = subparsers.add_parser("frontier", help="Inspect a run frontier.")
    frontier.add_argument("--run", required=True, help="Path to a run directory.")
    frontier.set_defaults(handler=_handle_frontier)

    report = subparsers.add_parser("report", help="Render a run summary report.")
    report.add_argument("--run", required=True, help="Path to a run directory.")
    report.set_defaults(handler=_handle_report)

    return parser


def _handle_placeholder(args: argparse.Namespace) -> int:
    """Provide a stable placeholder until implementation tasks land."""
    command = args.command or "none"
    print(f"{command} is scaffolded but not implemented yet.")
    return 0


def _handle_optimize(args: argparse.Namespace) -> int:
    """Run a deterministic optimization suite."""
    run_root = optimize_suite(args.suite, artifacts_root=args.artifacts_root)
    print(f"Optimization run written to {run_root}")
    print(f"Frontier: {run_root / 'frontier' / 'update.json'}")
    print(f"Summary: {run_root / 'summary.md'}")
    return 0


def _handle_evaluate(args: argparse.Namespace) -> int:
    """Run a single adversarial evaluation and write replayable artifacts."""
    candidate_spec, world_spec, candidate, world = _load_runtime_inputs(
        args.candidate,
        args.world,
        args.seed,
    )
    budget = _attack_budget_from_args(args)

    metrics = evaluate_honest(candidate, world)
    evaluation = evaluate_with_attacks(
        candidate,
        world,
        metrics,
        attack_names=REQUIRED_V1_ATTACKS,
        budget=budget,
        seed=args.seed,
    )
    constrained = apply_constraints(
        candidate_id=candidate.id,
        world_id=world.id,
        metrics=evaluation.honest_metrics,
        config=load_constraint_config(args.scoring_config),
    )
    scorecard = score_candidate(
        constrained,
        load_scoring_config(args.scoring_config),
        frontier_updated=False,
        baseline_utility=None,
    )
    scorecard = ensure_result_has_proof_status(scorecard)

    layout = create_run_layout(
        args.artifacts_root,
        suite_id="evaluate",
        candidate_id=candidate.id,
        world_id=world.id,
        seeds={"evaluation": args.seed},
    )
    _write_common_run_artifacts(
        layout,
        candidate_spec=candidate_spec,
        world_spec=world_spec,
        seeds={"evaluation": args.seed},
        config_refs={
            "candidate": str(Path(args.candidate)),
            "world": str(Path(args.world)),
            "scoring_config": str(Path(args.scoring_config)),
        },
        metadata={
            "command": "evaluate",
            "attack_budget": budget,
            "attack_names": list(REQUIRED_V1_ATTACKS),
        },
    )
    write_artifact(
        layout,
        "honest/metrics.json",
        {
            "candidate_id": candidate.id,
            "world_id": world.id,
            "metrics": metrics,
        },
    )
    _write_attack_artifacts(layout, evaluation.attacks)
    write_artifact(layout, "score/evaluation.json", evaluation)
    if scorecard.is_survivor or supports_formal_bridge(candidate.family):
        scorecard = finalize_formal_artifacts(
            layout.root,
            run_id=layout.run_id,
            candidate=candidate,
            world=world,
            scorecard=scorecard,
        )
    else:
        _write_formal_status_artifact(layout, scorecard)
    write_artifact(layout, "score/score.json", scorecard)
    summary_path = layout.root / "summary.md"
    summary_path.write_text(
        _render_summary(
            scorecard,
            run_root=layout.root,
            metrics=evaluation.honest_metrics,
        ),
        encoding="utf-8",
    )

    print(f"Run written to {layout.root}")
    print(
        f"Disposition: {scorecard.disposition}; utility: "
        f"{scorecard.utility if scorecard.utility is not None else 'n/a'}"
    )
    print(f"Artifacts: {summary_path}")
    return 0


def _handle_attack(args: argparse.Namespace) -> int:
    """Run one attack family and write a replayable attack artifact."""
    candidate_spec, world_spec, candidate, world = _load_runtime_inputs(
        args.candidate,
        args.world,
        args.seed,
    )
    budget = _attack_budget_from_args(args)
    attack = run_attack(
        args.attack_name,
        candidate,
        world,
        budget=budget,
    )

    layout = create_run_layout(
        args.artifacts_root,
        suite_id=f"attack:{attack.name}",
        candidate_id=candidate.id,
        world_id=world.id,
        seeds={"evaluation": args.seed},
    )
    _write_common_run_artifacts(
        layout,
        candidate_spec=candidate_spec,
        world_spec=world_spec,
        seeds={"evaluation": args.seed},
        config_refs={
            "candidate": str(Path(args.candidate)),
            "world": str(Path(args.world)),
            "attack": attack.name,
        },
        metadata={
            "command": "attack",
            "attack_budget": budget,
            "attack_name": attack.name,
        },
    )
    write_artifact(layout, f"attacks/{attack.name}.json", attack)
    summary_path = layout.root / "summary.md"
    summary_path.write_text(_render_attack_summary(attack, layout.root), encoding="utf-8")

    print(f"Attack run written to {layout.root}")
    print(
        f"Attack: {attack.name}; success: "
        f"{attack.success if attack.success is not None else 'n/a'}"
    )
    print(f"Artifacts: {summary_path}")
    return 0


def _handle_frontier(args: argparse.Namespace) -> int:
    """Render the stored frontier snapshot for a run."""
    snapshot = load_frontier_snapshot(args.run)
    print(render_frontier_snapshot(snapshot), end="")
    return 0


def _handle_report(args: argparse.Namespace) -> int:
    """Print the stored run summary if available."""
    summary_path = Path(args.run) / "summary.md"
    if summary_path.is_file():
        print(summary_path.read_text(encoding="utf-8"), end="")
        return 0
    snapshot = load_frontier_snapshot(args.run)
    print(render_frontier_snapshot(snapshot), end="")
    return 0


def _render_summary(scorecard: ScoreCard, run_root: Path, metrics: Metrics) -> str:
    lines = [
        "# Summary",
        "",
        f"- candidate: {scorecard.candidate_id}",
        f"- world: {scorecard.world_id}",
        f"- disposition: {scorecard.disposition}",
        f"- utility: {scorecard.utility if scorecard.utility is not None else 'n/a'}",
        f"- strong_result: {scorecard.strong_result}",
        f"- surprising_result: {scorecard.surprising_result}",
        f"- run_root: {run_root}",
    ]
    if scorecard.proof_status is not None:
        lines.append(f"- proof_status: {scorecard.proof_status}")
    if scorecard.formal_claim_id is not None:
        lines.append(f"- formal_claim_id: {scorecard.formal_claim_id}")
    lines.extend(
        [
            f"- modeling_attack_success: {metrics.get('modeling_attack_success', 'n/a')}",
            f"- replay_attack_success: {metrics.get('replay_attack_success', 'n/a')}",
            f"- counterfeit_attack_success: {metrics.get('counterfeit_attack_success', 'n/a')}",
            f"- crp_exhaustion_attack_success: {metrics.get('crp_exhaustion_attack_success', 'n/a')}",
            f"- drift_abuse_attack_success: {metrics.get('drift_abuse_attack_success', 'n/a')}",
        ]
    )
    if scorecard.reject_reasons:
        lines.append("- reject_reasons:")
        lines.extend(f"  - {reason}" for reason in scorecard.reject_reasons)
    return "\n".join(lines) + "\n"


def _render_attack_summary(attack: AttackResult, run_root: Path) -> str:
    lines = [
        "# Attack Summary",
        "",
        f"- attack: {attack.name}",
        f"- success: {attack.success if attack.success is not None else 'n/a'}",
        f"- run_root: {run_root}",
    ]
    if attack.notes:
        lines.append(f"- notes: {attack.notes}")
    return "\n".join(lines) + "\n"


def _add_attack_budget_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--queries",
        type=int,
        default=1_000,
        help="Attack query budget.",
    )
    parser.add_argument(
        "--observations",
        type=int,
        default=256,
        help="Attack observation budget.",
    )
    parser.add_argument(
        "--search-steps",
        type=int,
        default=128,
        help="Attack search-step budget.",
    )


def _attack_budget_from_args(args: argparse.Namespace) -> dict[str, int]:
    return {
        "queries": args.queries,
        "observations": args.observations,
        "search_steps": args.search_steps,
    }


def _load_runtime_inputs(
    candidate_path: str,
    world_path: str,
    seed: int,
) -> tuple[object, object, BuiltCandidate, WorldInstance]:
    candidate_spec = load_candidate_spec(candidate_path)
    world_spec = load_world_spec(world_path)
    candidate = build_candidate(candidate_path)
    world = sample_world(world_path, seed)
    return candidate_spec, world_spec, candidate, world


def _write_common_run_artifacts(
    layout: object,
    *,
    candidate_spec: object,
    world_spec: object,
    seeds: dict[str, int],
    config_refs: dict[str, str],
    metadata: dict[str, object],
) -> None:
    write_yaml_atomic(layout.candidate_dir / "candidate.yaml", candidate_spec)
    write_yaml_atomic(layout.world_dir / "world.yaml", world_spec)
    write_run_context(
        layout,
        seeds=seeds,
        config_refs=config_refs,
        metadata=metadata,
    )


def _write_attack_artifacts(layout: object, attacks: list[AttackResult]) -> None:
    for attack in attacks:
        write_artifact(layout, f"attacks/{attack.name}.json", attack)


def _write_formal_status_artifact(layout: object, scorecard: ScoreCard) -> None:
    if scorecard.proof_status is None and scorecard.formal_claim_id is None:
        return
    write_artifact(
        layout,
        "formal/proof_status.json",
        proof_status_payload(scorecard),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
