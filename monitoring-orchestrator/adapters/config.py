"""Configuration resolution for shared platform settings and project overrides."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Return a recursive merge without mutating either input."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def resolve_project_signal_config(config: dict[str, Any], project_name: str, signal: str) -> dict[str, Any]:
    """Merge a root-level platform block with one project's signal overrides."""
    projects = config.get("projects", {})
    if project_name not in projects:
        raise KeyError(f"Unknown monitoring project: {project_name}")

    global_config = config.get(signal, {})
    project_config = projects[project_name].get(signal, {})
    if not isinstance(global_config, dict) or not isinstance(project_config, dict):
        raise ValueError(f"{signal} configuration must be a mapping")
    return deep_merge(global_config, project_config)

