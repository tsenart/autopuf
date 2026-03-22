"""Artifact serialization and atomic I/O helpers."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if it does not already exist."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def to_serializable(value: Any) -> Any:
    """Convert common runtime objects into JSON-serializable data."""
    if is_dataclass(value):
        return to_serializable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): to_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_serializable(item) for item in value]
    return value


def write_json_atomic(path: str | Path, payload: Any) -> Path:
    """Write JSON atomically using a temporary file in the same directory."""
    output_path = Path(path)
    ensure_directory(output_path.parent)
    serialized = json.dumps(
        to_serializable(payload),
        indent=2,
        sort_keys=True,
    )
    _write_text_atomic(output_path, serialized + "\n")
    return output_path


def read_json_file(path: str | Path) -> Any:
    """Read JSON data from disk."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_yaml_atomic(path: str | Path, payload: Any) -> Path:
    """Write YAML atomically using a temporary file in the same directory."""
    output_path = Path(path)
    ensure_directory(output_path.parent)
    serialized = yaml.safe_dump(
        to_serializable(payload),
        sort_keys=False,
        default_flow_style=False,
    )
    _write_text_atomic(output_path, serialized)
    return output_path


def read_yaml_file(path: str | Path) -> Any:
    """Read YAML data from disk."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _write_text_atomic(path: Path, contents: str) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(contents)
        temp_name = handle.name

    os.replace(temp_name, path)

