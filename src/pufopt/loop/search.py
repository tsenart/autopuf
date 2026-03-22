"""Optimization search loop."""

from __future__ import annotations

from pathlib import Path

from pufopt.candidates.factory import build_candidate_definition
from pufopt.candidates.mutations import mutate_candidate_spec
from pufopt.evaluators.adversarial import evaluate_with_attacks
from pufopt.evaluators.constraints import apply_constraints, load_constraint_config
from pufopt.evaluators.honest import evaluate_honest
from pufopt.evaluators.scoring import load_scoring_config, score_candidate
from pufopt.experiments.reports import render_optimization_summary
from pufopt.experiments.selection import suggest_next_action
from pufopt.experiments.suites import LoadedSuite, load_optimization_suite
from pufopt.formal.bridge import finalize_formal_artifacts, supports_formal_bridge
from pufopt.formal.proof_status import ensure_result_has_proof_status, proof_status_payload
from pufopt.loop.frontier import FrontierState
from pufopt.loop.scheduler import (
    SchedulerConfig,
    enqueue_mutations,
    initialize_scheduler_state,
    pick_candidate,
    pick_world,
)
from pufopt.storage.artifacts import create_run_layout, write_artifact, write_run_context
from pufopt.storage.io import write_yaml_atomic
from pufopt.storage.schema import load_world_spec
from pufopt.types import ScoreCard
from pufopt.worlds.registry import default_world_registry


def optimize_suite(
    suite_path: str | Path,
    *,
    artifacts_root: str | Path | None = None,
) -> Path:
    """Run a small deterministic optimization suite."""
    suite = load_optimization_suite(suite_path)
    scoring_config_path = suite.scoring_config_path
    constraint_config = load_constraint_config(scoring_config_path)
    scoring_config = load_scoring_config(scoring_config_path)
    scheduler = initialize_scheduler_state(suite.seed_candidates)
    scheduler_config = SchedulerConfig(mode=suite.spec.search.params.get("mode", "balanced"))
    candidate_index = {candidate.id: candidate for candidate in suite.seed_candidates}
    frontier = FrontierState()

    run_layout = create_run_layout(
        artifacts_root or suite.artifacts_root,
        suite_id=suite.spec.id,
        seeds={"suite": 1729},
    )
    write_yaml_atomic(run_layout.root / "suite.yaml", suite.raw_data)
    write_run_context(
        run_layout,
        seeds={"suite": 1729},
        config_refs={
            "suite": str(suite.path),
            "scoring_config": scoring_config_path,
        },
        metadata={
            "command": "optimize",
            "algorithm": suite.spec.search.algorithm,
            "worlds": list(suite.world_paths),
            "attacks": [attack.name for attack in suite.spec.attacks],
        },
    )

    iteration_count = suite.spec.search.max_iterations or len(suite.seed_candidates)
    last_score: ScoreCard | None = None
    for iteration in range(iteration_count):
        if not scheduler.queue and not frontier.frontier:
            break

        candidate_spec, candidate_decision = pick_candidate(
            scheduler,
            frontier,
            candidate_index,
            iteration=iteration,
            config=scheduler_config,
        )
        world_path, world_decision = pick_world(
            scheduler,
            suite.world_paths,
            candidate=candidate_spec,
        )
        world_spec = load_world_spec(world_path)
        world_definition = default_world_registry.create(world_spec)
        world = world_definition.sample(iteration + 1)
        candidate = build_candidate_definition(candidate_spec).build()

        honest_metrics = evaluate_honest(candidate, world)
        evaluation = evaluate_with_attacks(
            candidate,
            world,
            honest_metrics,
            attack_names=[attack.name for attack in suite.spec.attacks],
            budget=suite.spec.budgets,
            seed=iteration + 1,
        )
        constrained = apply_constraints(
            candidate_id=candidate.id,
            world_id=world.id,
            metrics=evaluation.honest_metrics,
            config=constraint_config,
        )
        baseline_utility = frontier.best().utility if frontier.best() else None
        preliminary_score = score_candidate(
            constrained,
            scoring_config,
            frontier_updated=False,
            baseline_utility=baseline_utility,
        )
        frontier_update = frontier.update(preliminary_score, family=candidate.family)
        score = score_candidate(
            constrained,
            scoring_config,
            frontier_updated=frontier_update.frontier_updated,
            baseline_utility=baseline_utility,
        )
        score = ensure_result_has_proof_status(score)
        if score.is_survivor or supports_formal_bridge(candidate.family):
            score = finalize_formal_artifacts(
                run_layout.root,
                run_id=run_layout.run_id,
                candidate=candidate,
                world=world,
                scorecard=score,
            )
        final_frontier_update = frontier_update
        if score.utility is not None:
            final_frontier_update = frontier.update(score, family=candidate.family)
        last_score = score

        mutations = mutate_candidate_spec(
            candidate_spec,
            metrics=score.metrics,
            max_variants=3,
        )
        for mutation in mutations:
            candidate_index[mutation.id] = mutation
        enqueue_mutations(scheduler, mutations)

        decision_payload = {
            "iteration": iteration,
            "candidate": candidate_decision,
            "world": world_decision,
            "mutations_enqueued": [mutation.id for mutation in mutations],
        }
        frontier_snapshot = frontier.snapshot(
            run_id=run_layout.run_id,
            update=final_frontier_update,
        )
        next_action = suggest_next_action(frontier_snapshot)
        final_snapshot = {
            **frontier_snapshot,
            "iterations_completed": iteration + 1,
            "best": frontier.best(),
            "next_action": next_action,
        }

        iteration_dir = Path("iterations") / f"{iteration:03d}"
        write_artifact(run_layout, iteration_dir / "candidate.json", candidate_spec)
        write_artifact(run_layout, iteration_dir / "world.json", world_spec)
        write_artifact(run_layout, iteration_dir / "evaluation.json", evaluation)
        write_artifact(run_layout, iteration_dir / "score.json", score)
        write_artifact(run_layout, iteration_dir / "planner.json", decision_payload)
        write_artifact(run_layout, "planner/decision.json", decision_payload)
        write_artifact(run_layout, "frontier/update.json", final_snapshot)
        if frontier.best() is not None:
            write_artifact(run_layout, "score/score.json", frontier.best())
        if score.proof_status is not None or score.formal_claim_id is not None:
            write_artifact(
                run_layout,
                "formal/proof_status.json",
                proof_status_payload(score),
            )
        (run_layout.root / "summary.md").write_text(
            render_optimization_summary(final_snapshot),
            encoding="utf-8",
        )

    if last_score is None:
        raise ValueError("optimization suite did not execute any iterations")
    return run_layout.root
