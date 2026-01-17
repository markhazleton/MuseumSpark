import unittest
from datetime import datetime, timezone, timedelta

from scripts.agents.models import EnrichedField, TrustLevel
from scripts.agents.provenance import merge_field


class ProvenanceTests(unittest.TestCase):
    def test_higher_trust_overwrites(self):
        current = "old"
        current_prov = {"trust_level": TrustLevel.WIKIPEDIA, "retrieved_at": datetime.now(timezone.utc).isoformat()}
        new = EnrichedField(
            value="new",
            source="wikidata",
            trust_level=TrustLevel.WIKIDATA,
            confidence=4,
        )
        value, prov, reason = merge_field(
            current_value=current, current_prov=current_prov, new_field=new, manual_lock=False
        )
        self.assertEqual(value, "new")
        self.assertEqual(reason, "higher_trust")
        self.assertEqual(int(prov["trust_level"]), int(TrustLevel.WIKIDATA))

    def test_lower_trust_blocked(self):
        current = "old"
        current_prov = {"trust_level": TrustLevel.WIKIDATA, "retrieved_at": datetime.now(timezone.utc).isoformat()}
        new = EnrichedField(
            value="new",
            source="wikipedia",
            trust_level=TrustLevel.WIKIPEDIA,
            confidence=4,
        )
        value, prov, reason = merge_field(
            current_value=current, current_prov=current_prov, new_field=new, manual_lock=False
        )
        self.assertEqual(value, "old")
        self.assertEqual(reason, "lower_trust_or_older")

    def test_equal_trust_newer_overwrites(self):
        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        current_prov = {"trust_level": TrustLevel.WIKIDATA, "retrieved_at": old_time.isoformat()}
        new = EnrichedField(
            value="new",
            source="wikidata",
            trust_level=TrustLevel.WIKIDATA,
            confidence=5,
            retrieved_at=datetime.now(timezone.utc),
        )
        value, prov, reason = merge_field(
            current_value="old", current_prov=current_prov, new_field=new, manual_lock=False
        )
        self.assertEqual(value, "new")
        self.assertEqual(reason, "equal_trust_newer")


if __name__ == "__main__":
    unittest.main()
