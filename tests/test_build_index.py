"""Tests for the deterministic index builder helpers."""
from __future__ import annotations

import importlib.util

from helpers import PROJECT_ROOT


def load_build_index_module():
    module_path = PROJECT_ROOT / "scripts" / "builders" / "build-index.py"
    spec = importlib.util.spec_from_file_location("build_index", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_time_needed_accepts_schema_values():
    build_index = load_build_index_module()

    assert build_index.normalize_time_needed("Quick stop") == "Quick stop"
    assert build_index.normalize_time_needed("Half day") == "Half day"
    assert build_index.normalize_time_needed("Most of the Day") == "Most of the Day"
    assert build_index.normalize_time_needed("All Day") == "All Day"


def test_time_needed_normalizes_legacy_values():
    build_index = load_build_index_module()

    assert build_index.normalize_time_needed("Quick stop (<1 hr)") == "Quick stop"
    assert build_index.normalize_time_needed("Full day") == "All Day"
