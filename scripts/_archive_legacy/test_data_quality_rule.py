"""Test the critical data quality rule: NEVER replace known value with null."""

import sys
import importlib.util
from pathlib import Path

# Test merge_patch from enrich-open-data.py
print("=" * 70)
print("Testing merge_patch (enrich-open-data.py)")
print("=" * 70)

# Load enrich-open-data.py as a module (handles hyphen in filename)
SCRIPTS_DIR = Path(__file__).parent
spec = importlib.util.spec_from_file_location("enrich_open_data", SCRIPTS_DIR / "enrich-open-data.py")
enrich_module = importlib.util.module_from_spec(spec)
sys.modules["enrich_open_data"] = enrich_module
spec.loader.exec_module(enrich_module)

merge_patch = enrich_module.merge_patch

# Test 1: Should NOT replace known value with null
museum1 = {
    "museum_id": "test-1",
    "street_address": "123 Main St",
    "postal_code": "12345",
    "city": "Tulsa"
}
patch1 = {
    "street_address": None,  # LLM returned null
    "postal_code": None,     # LLM returned null
    "city": None,            # LLM returned null
    "website": "http://example.com"  # LLM found website
}

result1 = merge_patch(museum1, patch1)
print("\n✓ Test 1: Known values should be preserved when patch has null")
print(f"  Original street_address: '{museum1['street_address']}'")
print(f"  After merge: '{result1['street_address']}'")
assert result1["street_address"] == "123 Main St", "FAILED: street_address was replaced with null!"
assert result1["postal_code"] == "12345", "FAILED: postal_code was replaced with null!"
assert result1["city"] == "Tulsa", "FAILED: city was replaced with null!"
assert result1["website"] == "http://example.com", "FAILED: website should be added!"
print("  ✓ PASS: All known values preserved, new value added\n")

# Test 2: Should replace null with known value
museum2 = {
    "museum_id": "test-2",
    "street_address": None,
    "postal_code": None,
}
patch2 = {
    "street_address": "456 Elm St",
    "postal_code": "67890"
}

result2 = merge_patch(museum2, patch2)
print("✓ Test 2: Null values should be replaced with known values")
print(f"  Original street_address: {museum2['street_address']}")
print(f"  After merge: '{result2['street_address']}'")
assert result2["street_address"] == "456 Elm St", "FAILED: street_address should be updated!"
assert result2["postal_code"] == "67890", "FAILED: postal_code should be updated!"
print("  ✓ PASS: Null values replaced with known values\n")

# Test 3: Should replace placeholder with null (normalization)
museum3 = {
    "museum_id": "test-3",
    "street_address": "TBD",
    "postal_code": "unknown"
}
patch3 = {
    "street_address": None,
    "postal_code": None
}

result3 = merge_patch(museum3, patch3)
print("✓ Test 3: Placeholder values should be replaceable with null")
print(f"  Original street_address: '{museum3['street_address']}'")
print(f"  After merge: {result3['street_address']}")
assert result3["street_address"] is None, "FAILED: placeholder should be replaced with None!"
assert result3["postal_code"] is None, "FAILED: placeholder should be replaced with None!"
print("  ✓ PASS: Placeholders normalized to null\n")

# Test provenance.py merge_field
print("=" * 70)
print("Testing merge_field (provenance.py)")
print("=" * 70)

from datetime import datetime
from agents.models import EnrichedField, TrustLevel
from agents.provenance import merge_field

# Test 4: Should NOT replace known value with null (no provenance)
current_value4 = "123 Main St"
current_prov4 = None
new_field4 = EnrichedField(
    value=None,
    trust_level=TrustLevel.LLM_EXTRACTED,
    source="validation_agent",
    confidence=3,
    retrieved_at=datetime.now()
)

result_value4, result_prov4, reason4 = merge_field(
    current_value=current_value4,
    current_prov=current_prov4,
    new_field=new_field4,
    manual_lock=False
)

print("\n✓ Test 4: merge_field should reject null when current value exists")
print(f"  Current value: '{current_value4}'")
print(f"  New value: {new_field4.value}")
print(f"  Result: '{result_value4}'")
print(f"  Reason: {reason4}")
assert result_value4 == "123 Main St", "FAILED: Known value replaced with null!"
assert reason4 == "cannot_replace_known_with_null", "FAILED: Wrong rejection reason!"
print("  ✓ PASS: Known value preserved, rejected with correct reason\n")

# Test 5: Should replace null with known value (no provenance)
current_value5 = None
current_prov5 = None
new_field5 = EnrichedField(
    value="456 Elm St",
    trust_level=TrustLevel.LLM_EXTRACTED,
    source="validation_agent",
    confidence=3,
    retrieved_at=datetime.now()
)

result_value5, result_prov5, reason5 = merge_field(
    current_value=current_value5,
    current_prov=current_prov5,
    new_field=new_field5,
    manual_lock=False
)

print("✓ Test 5: merge_field should accept known value when current is null")
print(f"  Current value: {current_value5}")
print(f"  New value: '{new_field5.value}'")
print(f"  Result: '{result_value5}'")
print(f"  Reason: {reason5}")
assert result_value5 == "456 Elm St", "FAILED: Should update null with known value!"
assert reason5 == "no_existing_provenance", "FAILED: Wrong acceptance reason!"
print("  ✓ PASS: Null replaced with known value\n")

# Test 6: Should NOT replace known value with null even with existing provenance
current_value6 = "789 Oak Ave"
current_prov6 = {
    "source": "google_places_api",
    "trust_level": int(TrustLevel.OFFICIAL_EXTRACT),
    "retrieved_at": "2026-01-15T12:00:00",
    "confidence": 4
}
new_field6 = EnrichedField(
    value=None,
    trust_level=TrustLevel.LLM_EXTRACTED,  # Lower trust
    source="validation_agent",
    confidence=3,
    retrieved_at=datetime.now()
)

result_value6, result_prov6, reason6 = merge_field(
    current_value=current_value6,
    current_prov=current_prov6,
    new_field=new_field6,
    manual_lock=False
)

print("✓ Test 6: Should reject null even with provenance tracking")
print(f"  Current value: '{current_value6}' (trust={current_prov6['trust_level']})")
print(f"  New value: {new_field6.value} (trust={int(new_field6.trust_level)})")
print(f"  Result: '{result_value6}'")
print(f"  Reason: {reason6}")
assert result_value6 == "789 Oak Ave", "FAILED: Known value replaced with null!"
assert reason6 == "cannot_replace_known_with_null", "FAILED: Should reject due to null rule!"
print("  ✓ PASS: Known value preserved even with provenance\n")

print("=" * 70)
print("✅ ALL TESTS PASSED!")
print("=" * 70)
print("\nData Quality Rule Verified:")
print("  ✓ merge_patch never replaces known values with null")
print("  ✓ merge_field never replaces known values with null")
print("  ✓ Placeholders can be normalized to null")
print("  ✓ Null values can be filled with known values")
print("\nThis prevents data loss when running enrichment pipelines.")
