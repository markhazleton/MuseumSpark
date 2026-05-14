"""Tests for JSON Schema validation of state museum files.

Exercises the schema directly via jsonschema so the same invariants
the CLI validate-json.py enforces are continuously verified in CI.
"""
from __future__ import annotations

import json
import copy

import pytest
from jsonschema import validate, ValidationError

from helpers import SCHEMA_PATH, STATES_DIR, minimal_museum


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def minimal_state_doc(**museum_overrides) -> dict:
    """Return a minimal valid state document wrapping one museum."""
    return {
        "state": "Colorado",
        "state_code": "CO",
        "museums": [minimal_museum(**museum_overrides)],
    }


# ---------------------------------------------------------------------------
# Schema structure
# ---------------------------------------------------------------------------

class TestSchemaLoads:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, schema):
        assert isinstance(schema, dict)
        assert "$schema" in schema or "$defs" in schema or "properties" in schema


# ---------------------------------------------------------------------------
# Valid documents pass
# ---------------------------------------------------------------------------

class TestValidDocuments:
    def test_minimal_valid_state_doc(self, schema):
        validate(instance=minimal_state_doc(), schema=schema)

    def test_empty_museums_array_is_valid(self, schema):
        doc = {"state": "Colorado", "state_code": "CO", "museums": []}
        validate(instance=doc, schema=schema)

    def test_state_file_on_disk_passes(self, schema):
        """At least one real state file from the dataset must pass validation."""
        state_files = sorted(STATES_DIR.glob("*.json"))
        assert state_files, "No state files found — dataset missing?"
        # Validate the first file found (alphabetical); it must pass.
        first = state_files[0]
        data = json.loads(first.read_text(encoding="utf-8"))
        validate(instance=data, schema=schema)


# ---------------------------------------------------------------------------
# Invalid documents fail with ValidationError
# ---------------------------------------------------------------------------

class TestInvalidDocuments:
    def test_missing_state_field_raises(self, schema):
        doc = minimal_state_doc()
        del doc["state"]
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_missing_state_code_raises(self, schema):
        doc = minimal_state_doc()
        del doc["state_code"]
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_missing_museum_id_raises(self, schema):
        doc = minimal_state_doc()
        del doc["museums"][0]["museum_id"]
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_missing_museum_name_raises(self, schema):
        doc = minimal_state_doc()
        del doc["museums"][0]["museum_name"]
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_missing_country_raises(self, schema):
        doc = minimal_state_doc()
        del doc["museums"][0]["country"]
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_invalid_state_code_pattern_raises(self, schema):
        """state_code must be exactly two uppercase letters."""
        doc = minimal_state_doc()
        doc["state_code"] = "COLO"
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)

    def test_museums_not_array_raises(self, schema):
        doc = minimal_state_doc()
        doc["museums"] = "not-an-array"
        with pytest.raises(ValidationError):
            validate(instance=doc, schema=schema)
