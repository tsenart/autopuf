"""Python-to-Lean formal bridge and bounded differential checks."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pufopt.formal.proof_status import upgrade_to_specified
from pufopt.storage.io import to_serializable, write_json_atomic, write_yaml_atomic
from pufopt.types import BuiltCandidate, FormalClaimSpec, ScoreCard, WorldInstance

SUPPORTED_FAMILIES = {"classical_crp"}


@dataclass(frozen=True, slots=True)
class DifferentialCheckResult:
    """Result of a bounded Python-versus-Lean differential check."""

    supported: bool
    family: str
    passed: bool
    check_id: str
    lean_command: list[str]
    reference: dict[str, object]
    observed: dict[str, object]
    mismatches: list[str]
    notes: str | None = None


def supports_formal_bridge(candidate_family: str) -> bool:
    """Return whether the family has a bounded Lean reference semantics."""
    return candidate_family in SUPPORTED_FAMILIES


def finalize_formal_artifacts(
    run_root: str | Path,
    *,
    run_id: str,
    candidate: BuiltCandidate,
    world: WorldInstance,
    scorecard: ScoreCard,
) -> ScoreCard:
    """Emit formal claim, proof-status, and differential-check artifacts."""
    formal_dir = Path(run_root) / "formal"
    formal_dir.mkdir(parents=True, exist_ok=True)
    claim_path = formal_dir / "claim.yaml"
    proof_status_path = formal_dir / "proof_status.json"

    differential = run_bounded_differential_check(candidate, scorecard, run_id=run_id)
    write_json_atomic(formal_dir / "differential_check.json", asdict(differential))

    updated = scorecard
    if differential.supported and differential.passed:
        claim = build_formal_claim(
            candidate,
            world,
            updated,
            run_id=run_id,
            differential=differential,
        )
        write_yaml_atomic(claim_path, claim)
        updated = upgrade_to_specified(updated, formal_claim_id=claim.id)
    elif claim_path.exists():
        claim_path.unlink()

    if updated.proof_status is not None or updated.formal_claim_id is not None:
        write_json_atomic(proof_status_path, to_serializable({
            "candidate_id": updated.candidate_id,
            "world_id": updated.world_id,
            "formal_claim_id": updated.formal_claim_id,
            "proof_status": updated.proof_status,
            "strong_result": updated.strong_result,
            "surprising_result": updated.surprising_result,
        }))
    elif proof_status_path.exists():
        proof_status_path.unlink()

    return updated


def build_formal_claim(
    candidate: BuiltCandidate,
    world: WorldInstance,
    scorecard: ScoreCard,
    *,
    run_id: str,
    differential: DifferentialCheckResult,
) -> FormalClaimSpec:
    """Build one deterministic formal claim from a supported run."""
    claim_id = _formal_claim_id(candidate.id, world.id, run_id)
    assumptions = _assumptions_for(candidate)
    return FormalClaimSpec(
        id=claim_id,
        candidate_family=candidate.family,
        security_game=_security_game_for(candidate),
        assumptions=assumptions,
        claim=_claim_text_for(candidate, world, scorecard),
        proof_status="specified",
        lean_modules=[
            "formal/Autopuf/Model.lean",
            "formal/Autopuf/Games.lean",
            "formal/Autopuf/Claims.lean",
            "formal/Autopuf/Bridge.lean",
        ],
        bridge_checks={
            "supported": True,
            "differential_check_id": differential.check_id,
            "passed": differential.passed,
            "reference_family": differential.family,
        },
        related_runs=[run_id],
        notes="Generated from a supported bounded differential check.",
    )


def run_bounded_differential_check(
    candidate: BuiltCandidate,
    scorecard: ScoreCard,
    *,
    run_id: str,
) -> DifferentialCheckResult:
    """Run one bounded differential check against the Lean reference semantics."""
    if candidate.family != "classical_crp":
        return DifferentialCheckResult(
            supported=False,
            family=candidate.family,
            passed=False,
            check_id=_differential_check_id(run_id, candidate.id, candidate.family),
            lean_command=[],
            reference={},
            observed={},
            mismatches=[],
            notes="No supported Lean reference semantics for this family yet.",
        )

    challenge_space_size = _positive_int(candidate.params.get("challenge_space_size"), "challenge_space_size")
    response_bit_width = _positive_int(candidate.params.get("response_bit_width"), "response_bit_width")
    replay_window = _positive_int(candidate.params.get("replay_window"), "replay_window")
    lean_command = [
        "lake",
        "exe",
        "autopuf-formal",
        "differential",
        "classical_crp",
        str(challenge_space_size),
        str(response_bit_width),
        str(replay_window),
    ]
    output = subprocess.run(
        lean_command,
        cwd=_repo_root() / "formal",
        capture_output=True,
        text=True,
        check=False,
    )
    check_id = _differential_check_id(run_id, candidate.id, candidate.family)
    if output.returncode != 0:
        return DifferentialCheckResult(
            supported=True,
            family=candidate.family,
            passed=False,
            check_id=check_id,
            lean_command=lean_command,
            reference={},
            observed={},
            mismatches=[output.stderr.strip() or "Lean differential command failed"],
            notes="Lean command failed during bounded differential check.",
        )

    reference = _parse_key_value_lines(output.stdout)
    observed = {
        "challenge_count": len(_string_list(candidate.params.get("challenge_labels"))),
        "response_width": response_bit_width,
        "replay_window": replay_window,
        "expected_lifetime": _metric_int(scorecard.metrics.get("crp_lifetime")),
        "security_game": _security_game_for(candidate),
    }

    comparisons = {
        "challenge_count": observed["challenge_count"],
        "response_width": observed["response_width"],
        "replay_window": observed["replay_window"],
        "expected_lifetime": observed["expected_lifetime"],
        "security_game": observed["security_game"],
    }
    mismatches = [
        f"{key}: observed={comparisons[key]!r} reference={reference.get(key)!r}"
        for key in comparisons
        if str(comparisons[key]) != str(reference.get(key))
    ]
    supported = str(reference.get("supported", "false")).lower() == "true"
    return DifferentialCheckResult(
        supported=supported,
        family=candidate.family,
        passed=supported and not mismatches,
        check_id=check_id,
        lean_command=lean_command,
        reference=reference,
        observed=observed,
        mismatches=mismatches,
        notes="Bounded differential check compares classical_crp structural semantics.",
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _formal_claim_id(candidate_id: str, world_id: str, run_id: str) -> str:
    digest = hashlib.sha1(f"{candidate_id}|{world_id}|{run_id}".encode("utf-8")).hexdigest()
    return f"claim-{digest[:12]}"


def _differential_check_id(run_id: str, candidate_id: str, family: str) -> str:
    digest = hashlib.sha1(f"{run_id}|{candidate_id}|{family}".encode("utf-8")).hexdigest()
    return f"diff-{digest[:12]}"


def _assumptions_for(candidate: BuiltCandidate) -> list[str]:
    if candidate.family == "classical_crp":
        return [
            "challenge_space_size > 0",
            "response_bit_width > 0",
            "replay_window > 0",
            "bounded_crp_authentication game semantics",
        ]
    return ["unsupported family assumptions are not formalized yet"]


def _security_game_for(candidate: BuiltCandidate) -> str:
    if candidate.family == "classical_crp":
        return "bounded_crp_authentication"
    return "unsupported_game"


def _claim_text_for(
    candidate: BuiltCandidate,
    world: WorldInstance,
    scorecard: ScoreCard,
) -> str:
    return (
        f"Candidate {candidate.id} in world {world.id} is represented in the "
        f"{_security_game_for(candidate)} security game with proof_status="
        f"{scorecard.proof_status or 'specified'}."
    )


def _parse_key_value_lines(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _positive_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer for differential checks")
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero for differential checks")
    return value


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _metric_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)
