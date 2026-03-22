"""Task-control helpers for the autopuf delivery workflow."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pufopt.candidates.factory import build_candidate_definition
from pufopt.formal.bridge import finalize_formal_artifacts
from pufopt.formal.proof_status import ensure_result_has_proof_status
from pufopt.storage.io import read_json_file, read_yaml_file, write_json_atomic, write_yaml_atomic
from pufopt.storage.schema import load_candidate_spec, load_world_spec
from pufopt.types import ScoreCard
from pufopt.worlds.registry import WorldInstanceRecord

TASK_FINAL_STATUSES = {"promoted", "rejected"}
TASK_BLOCKED_STATUSES = {"blocked"}
VERIFY_PASSING_STATUS = "reproduced"
CONTEXT_PASSING_STATUS = "context_packed"
GATE_PASS = "pass"
GATE_FAIL = "fail"
GATE_NA = "n_a"


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Normalized subprocess result for task verification."""

    cmd: str
    exit_code: int
    stdout: str
    stderr: str


def find_next_task(tasks_root: str | Path) -> tuple[str | None, str]:
    """Return the next unblocked task id and a short explanation."""
    task_map = _load_all_manifests(tasks_root)
    if not task_map:
        return None, f"no task manifests found under {Path(tasks_root)}"

    for task_id, manifest in task_map.items():
        status = str(manifest.get("status", "ready"))
        if status in TASK_FINAL_STATUSES or status in TASK_BLOCKED_STATUSES:
            continue
        if _dependencies_satisfied(manifest, task_map):
            return task_id, "dependencies satisfied"
    return None, "no unblocked task has all dependencies promoted"


def pack_context(task_id: str, tasks_root: str | Path, repo_root: str | Path) -> Path:
    """Write the minimal context pack for one task and advance its status."""
    manifest_path = _task_manifest_path(task_id, tasks_root)
    manifest = _load_manifest(manifest_path)
    task_dir = manifest_path.parent
    context_path = task_dir / "context.md"

    design_docs = _string_list(manifest.get("inputs", {}).get("design_docs", []))
    code_paths = _string_list(manifest.get("inputs", {}).get("code_paths", []))
    formal_paths = _string_list(manifest.get("inputs", {}).get("formal_paths", []))
    acceptance = _string_list(manifest.get("acceptance_criteria", []))
    risks = _string_list(manifest.get("risks", []))

    lines = [
        "# Context",
        "",
        "## Objective",
        "",
        str(manifest.get("objective", "")).strip(),
        "",
        "## Relevant Design Decisions",
        "",
    ]
    if design_docs:
        lines.extend(f"- {doc}" for doc in design_docs)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Relevant Files",
            "",
        ]
    )
    if code_paths or formal_paths:
        lines.extend(f"- {path}" for path in [*code_paths, *formal_paths])
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Acceptance Criteria",
            "",
        ]
    )
    if acceptance:
        lines.extend(f"- {criterion}" for criterion in acceptance)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Open Risks",
            "",
        ]
    )
    if risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- none")
    context_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if manifest.get("status") not in TASK_FINAL_STATUSES:
        manifest["status"] = CONTEXT_PASSING_STATUS
        write_yaml_atomic(manifest_path, manifest)
    return context_path


def verify_task(task_id: str, tasks_root: str | Path, repo_root: str | Path) -> dict[str, Path]:
    """Run task verification, red review, reproduction, and formal checks."""
    repo = Path(repo_root)
    manifest_path = _task_manifest_path(task_id, tasks_root)
    manifest = _load_manifest(manifest_path)
    task_dir = manifest_path.parent

    command_results = [_run_command(command, repo) for command in _string_list(manifest.get("required_commands", []))]
    output_checks = _required_output_checks(repo, _string_list(manifest.get("required_outputs", [])))
    commands_pass = all(result.exit_code == 0 for result in command_results)
    outputs_pass = all(check["passed"] for check in output_checks)
    acceptance_pass = commands_pass and outputs_pass

    verification_checks = output_checks + [
        {
            "name": _slugify(criterion),
            "passed": acceptance_pass,
            "reason": None if acceptance_pass else "required commands or outputs failed",
        }
        for criterion in _string_list(manifest.get("acceptance_criteria", []))
    ]
    verification_payload = {
        "task_id": task_id,
        "status": "self_tested" if acceptance_pass else "implemented",
        "commands": [
            {
                "cmd": result.cmd,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            for result in command_results
        ],
        "checks": verification_checks,
        "notes": "Verification is green." if acceptance_pass else "One or more required commands or outputs failed.",
    }
    verification_path = write_json_atomic(task_dir / "verification.json", verification_payload)

    formal_check_payload = _build_formal_check(task_id, manifest, repo)
    formal_check_path = write_json_atomic(task_dir / "formal_check.json", formal_check_payload)

    red_review_path = task_dir / "red_review.md"
    red_review_path.write_text(
        _render_red_review(
            manifest,
            command_results=command_results,
            output_checks=output_checks,
            formal_check=formal_check_payload,
        ),
        encoding="utf-8",
    )

    reproduction_results = [
        _run_command(command, repo) for command in _string_list(manifest.get("required_commands", []))
    ]
    reproduction_pass = all(result.exit_code == 0 for result in reproduction_results)
    reproduction_path = task_dir / "reproduction_report.md"
    reproduction_path.write_text(
        _render_reproduction_report(reproduction_results, reproduction_pass),
        encoding="utf-8",
    )

    if acceptance_pass and formal_check_payload["passed"] and reproduction_pass:
        manifest["status"] = VERIFY_PASSING_STATUS
    else:
        manifest["status"] = "implemented"
    write_yaml_atomic(manifest_path, manifest)

    return {
        "verification": verification_path,
        "formal_check": formal_check_path,
        "red_review": red_review_path,
        "reproduction": reproduction_path,
    }


def promote_task(task_id: str, tasks_root: str | Path, repo_root: str | Path) -> tuple[Path, bool]:
    """Evaluate promotion gates, write promotion.yaml, and update task status."""
    repo = Path(repo_root)
    manifest_path = _task_manifest_path(task_id, tasks_root)
    manifest = _load_manifest(manifest_path)
    task_dir = manifest_path.parent

    verification_path = task_dir / "verification.json"
    formal_check_path = task_dir / "formal_check.json"
    red_review_path = task_dir / "red_review.md"
    reproduction_path = task_dir / "reproduction_report.md"

    schema_gate = _schema_gate(
        manifest_path,
        verification_path,
        formal_check_path,
    )
    output_gate = _gate_from_bool(
        all(check["passed"] for check in _required_output_checks(repo, _string_list(manifest.get("required_outputs", []))))
    )
    verification_payload = read_json_file(verification_path) if verification_path.is_file() else {}
    acceptance_gate = _gate_from_bool(
        bool(verification_payload)
        and all(command.get("exit_code") == 0 for command in verification_payload.get("commands", []))
        and all(check.get("passed") for check in verification_payload.get("checks", []))
    )
    red_review_gate = _gate_from_bool(_red_review_passed(red_review_path))
    reproduction_gate = _gate_from_bool(_reproduction_passed(reproduction_path))
    formal_gate = _formal_gate(formal_check_path, required=bool(manifest.get("formal_contract_required", False)))

    success = all(
        gate == GATE_PASS
        for gate in (
            schema_gate,
            output_gate,
            acceptance_gate,
            red_review_gate,
            reproduction_gate,
        )
    ) and formal_gate in {GATE_PASS, GATE_NA}

    promotion_payload = {
        "task_id": task_id,
        "status": "promoted" if success else "rejected",
        "promoted_by": "Integrator",
        "gates": {
            "schema_gate": schema_gate,
            "output_gate": output_gate,
            "acceptance_gate": acceptance_gate,
            "red_review_gate": red_review_gate,
            "reproduction_gate": reproduction_gate,
            "formal_contract_gate": formal_gate,
        },
        "evidence": {
            "verification": str(verification_path) if verification_path.is_file() else None,
            "formal_check": str(formal_check_path) if formal_check_path.is_file() else None,
            "red_review": str(red_review_path) if red_review_path.is_file() else None,
            "reproduction": str(reproduction_path) if reproduction_path.is_file() else None,
        },
        "notes": "Promotion accepted." if success else "Promotion blocked by one or more failed gates.",
    }
    promotion_path = write_yaml_atomic(task_dir / "promotion.yaml", promotion_payload)
    manifest["status"] = "promoted" if success else "rejected"
    write_yaml_atomic(manifest_path, manifest)
    return promotion_path, success


def formalize_claim(run_root: str | Path) -> tuple[Path, ScoreCard]:
    """Regenerate formal artifacts for a run and refresh its score artifact."""
    root = Path(run_root)
    score_path = root / "score" / "score.json"
    if not score_path.is_file():
        raise FileNotFoundError(score_path)

    run_id = _load_run_id(root)
    candidate, world = _load_run_subject(root)
    score = _load_scorecard(score_path)
    score = ensure_result_has_proof_status(score)
    updated = finalize_formal_artifacts(
        root,
        run_id=run_id,
        candidate=candidate,
        world=world,
        scorecard=score,
    )
    write_json_atomic(score_path, updated)
    return root / "formal", updated


def _task_manifest_path(task_id: str, tasks_root: str | Path) -> Path:
    manifest_path = Path(tasks_root) / task_id / "task.yaml"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    return manifest_path


def _load_manifest(path: str | Path) -> dict[str, Any]:
    payload = read_yaml_file(path)
    if not isinstance(payload, dict):
        raise ValueError(f"task manifest at {path} must be a mapping")
    return payload


def _load_all_manifests(tasks_root: str | Path) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for manifest_path in sorted(Path(tasks_root).glob("T*/task.yaml"), key=lambda item: _task_sort_key(item.parent.name)):
        manifests[manifest_path.parent.name] = _load_manifest(manifest_path)
    return manifests


def _task_sort_key(task_id: str) -> tuple[int, str]:
    digits = "".join(character for character in task_id if character.isdigit())
    return (int(digits or 0), task_id)


def _dependencies_satisfied(
    manifest: dict[str, Any],
    task_map: dict[str, dict[str, Any]],
) -> bool:
    for dependency in _string_list(manifest.get("depends_on", [])):
        if task_map.get(dependency, {}).get("status") != "promoted":
            return False
    return True


def _run_command(command: str, repo_root: Path) -> CommandResult:
    process = subprocess.run(
        ["/bin/zsh", "-lc", command],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        cmd=command,
        exit_code=process.returncode,
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
    )


def _required_output_checks(repo_root: Path, required_outputs: list[str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for output in required_outputs:
        exists = (repo_root / output).exists()
        checks.append(
            {
                "name": f"output:{output}",
                "passed": exists,
                "reason": None if exists else f"missing required output: {output}",
            }
        )
    return checks


def _build_formal_check(task_id: str, manifest: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    required = bool(manifest.get("formal_contract_required", False))
    checks: list[dict[str, Any]] = []
    formal_paths = _string_list(manifest.get("inputs", {}).get("formal_paths", []))
    for path in formal_paths:
        exists = (repo_root / path).exists()
        checks.append(
            {
                "name": f"formal_path:{path}",
                "passed": exists,
                "reason": None if exists else f"missing formal path: {path}",
            }
        )
    formal_outputs = [
        path for path in _string_list(manifest.get("required_outputs", [])) if "formal" in Path(path).parts
    ]
    for path in formal_outputs:
        exists = (repo_root / path).exists()
        checks.append(
            {
                "name": f"formal_output:{path}",
                "passed": exists,
                "reason": None if exists else f"missing formal output: {path}",
            }
        )

    if not required:
        return {
            "task_id": task_id,
            "required": False,
            "passed": True,
            "checks": checks,
            "notes": "Task does not require a formal contract gate.",
        }

    passed = bool(checks) and all(check["passed"] for check in checks)
    return {
        "task_id": task_id,
        "required": True,
        "passed": passed,
        "checks": checks,
        "notes": (
            "Formal contract checks passed."
            if passed
            else "Formal contract checks failed."
        ),
    }


def _render_red_review(
    manifest: dict[str, Any],
    *,
    command_results: list[CommandResult],
    output_checks: list[dict[str, Any]],
    formal_check: dict[str, Any],
) -> str:
    failing_commands = [result for result in command_results if result.exit_code != 0]
    failing_outputs = [check for check in output_checks if not check["passed"]]
    critical_findings = []
    if failing_commands:
        critical_findings.extend(f"command failed: {result.cmd}" for result in failing_commands)
    if failing_outputs:
        critical_findings.extend(check["reason"] for check in failing_outputs if check.get("reason"))
    if formal_check.get("required") and not formal_check.get("passed"):
        critical_findings.append("formal contract gate failed")

    recommendation = (
        "Promote."
        if not critical_findings
        else "Do not promote until the listed critical findings are resolved."
    )
    lines = [
        "# Red Review",
        "",
        "## Assumptions Challenged",
        "",
        "- required commands succeed from a clean repo root",
        "- required outputs exist at the declared paths",
        "- formal contract checks stay consistent with the manifest",
        "",
        "## Edge Cases Tested",
        "",
    ]
    if _string_list(manifest.get("required_commands", [])):
        lines.extend(f"- reran command contract: {command}" for command in _string_list(manifest.get("required_commands", [])))
    else:
        lines.append("- task has no required commands")
    lines.extend(
        [
            "",
            "## Findings",
            "",
        ]
    )
    if critical_findings:
        lines.extend(f"- {finding}" for finding in critical_findings)
    else:
        lines.append("- no breaking issues found in the declared verification surface")
    lines.extend(
        [
            "",
            "## Critical Findings Remaining",
            "",
        ]
    )
    if critical_findings:
        lines.extend(f"- {finding}" for finding in critical_findings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            recommendation,
            "",
        ]
    )
    return "\n".join(lines)


def _render_reproduction_report(results: list[CommandResult], passed: bool) -> str:
    lines = [
        "# Reproduction Report",
        "",
        "## Commands Rerun",
        "",
    ]
    if results:
        lines.extend(f"- {result.cmd}" for result in results)
    else:
        lines.append("- no required commands declared")
    lines.extend(
        [
            "",
            "## Result Comparison",
            "",
            "- deterministic command replay under the same working directory",
            "",
            "## Tolerance",
            "",
            "- exact exit-code match",
            "",
            "## Outcome",
            "",
            f"- passed: {'true' if passed else 'false'}",
            "",
        ]
    )
    return "\n".join(lines)


def _schema_gate(*paths: Path) -> str:
    for path in paths:
        if not path.is_file():
            return GATE_FAIL
        try:
            if path.suffix == ".json":
                read_json_file(path)
            else:
                read_yaml_file(path)
        except Exception:
            return GATE_FAIL
    return GATE_PASS


def _red_review_passed(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return "## Critical Findings Remaining" in text and "\n- none\n" in text


def _reproduction_passed(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return "- passed: true" in text


def _formal_gate(path: Path, *, required: bool) -> str:
    if not required:
        return GATE_NA
    if not path.is_file():
        return GATE_FAIL
    payload = read_json_file(path)
    return GATE_PASS if payload.get("passed") else GATE_FAIL


def _gate_from_bool(passed: bool) -> str:
    return GATE_PASS if passed else GATE_FAIL


def _load_run_id(run_root: Path) -> str:
    context_path = run_root / "context.json"
    if context_path.is_file():
        payload = read_json_file(context_path)
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id:
            return run_id
    return run_root.name


def _load_run_subject(run_root: Path) -> tuple[Any, WorldInstanceRecord]:
    direct_candidate = run_root / "candidate" / "candidate.yaml"
    direct_world = run_root / "world" / "world.yaml"
    if direct_candidate.is_file() and direct_world.is_file():
        candidate_spec = load_candidate_spec(direct_candidate)
        world_spec = load_world_spec(direct_world)
        candidate = build_candidate_definition(candidate_spec).build()
        world = WorldInstanceRecord(id=world_spec.id, params=dict(world_spec.params))
        return candidate, world

    score_payload = read_json_file(run_root / "score" / "score.json")
    candidate_id = score_payload.get("candidate_id")
    world_id = score_payload.get("world_id")
    for iteration_path in sorted((run_root / "iterations").glob("*/score.json")):
        iteration_score = read_json_file(iteration_path)
        if (
            iteration_score.get("candidate_id") == candidate_id
            and iteration_score.get("world_id") == world_id
        ):
            iteration_dir = iteration_path.parent
            candidate_spec = load_candidate_spec(iteration_dir / "candidate.json")
            world_spec = load_world_spec(iteration_dir / "world.json")
            candidate = build_candidate_definition(candidate_spec).build()
            world = WorldInstanceRecord(id=world_spec.id, params=dict(world_spec.params))
            return candidate, world
    raise FileNotFoundError(
        f"could not resolve candidate/world artifacts for run {run_root}"
    )


def _load_scorecard(path: Path) -> ScoreCard:
    payload = read_json_file(path)
    return ScoreCard(**payload)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "check"


def _string_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return [str(raw)]
