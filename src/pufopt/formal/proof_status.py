"""Proof-status helpers shared across CLI and search flows."""

from __future__ import annotations

from dataclasses import replace

from pufopt.types import ProofStatus, ScoreCard


def ensure_result_has_proof_status(scorecard: ScoreCard) -> ScoreCard:
    """Attach the lowest-assurance proof status when a salient result lacks one."""
    if (
        scorecard.proof_status is None
        and (scorecard.strong_result or scorecard.surprising_result)
    ):
        return replace(scorecard, proof_status="empirical_only")
    return scorecard


def upgrade_to_specified(
    scorecard: ScoreCard,
    *,
    formal_claim_id: str,
) -> ScoreCard:
    """Upgrade a scorecard to `specified` once a formal claim is emitted."""
    proof_status: ProofStatus = "specified"
    return replace(
        scorecard,
        proof_status=proof_status,
        formal_claim_id=formal_claim_id,
    )


def proof_status_payload(scorecard: ScoreCard) -> dict[str, object]:
    """Serialize the proof-status view for artifact writing."""
    return {
        "candidate_id": scorecard.candidate_id,
        "world_id": scorecard.world_id,
        "formal_claim_id": scorecard.formal_claim_id,
        "proof_status": scorecard.proof_status,
        "strong_result": scorecard.strong_result,
        "surprising_result": scorecard.surprising_result,
    }
