"""Tests for Phase 3 priority scoring (MRD v3.1.T).

These exercise the deterministic compute_priority_score() and
assign_outcome_tier() functions without touching the filesystem.
"""
from __future__ import annotations

import pytest
from helpers import minimal_museum
from scripts.phases.phase3_priority import (
    COLLECTION_PENALTY,
    REPUTATION_PENALTY,
    ScoreBreakdown,
    assign_outcome_tier,
    compute_priority_score,
)


# ---------------------------------------------------------------------------
# Priority score formula
# ---------------------------------------------------------------------------

class TestComputePriorityScore:
    def test_basic_regional_moderate(self):
        """Regional/Moderate museum with mid-range art scores."""
        m = minimal_museum(
            impressionist_strength=3,
            modern_contemporary_strength=2,
            hat_strength=1,
            historical_context_score=3,
            eca_score=2,
            reputation_level="Regional",
            collection_level="Moderate",
        )
        bd = compute_priority_score(m)
        assert bd.can_score is True
        assert bd.collection_based_pas == 3   # max(3,2,1)
        assert bd.effective_pas == 3           # max(3,2)
        assert bd.dual_strength_bonus == 0     # imp<3 doesn't trigger (imp=3 but mod=2)
        assert bd.reputation_penalty == 2
        assert bd.collection_penalty == 2
        # (6-3)*2 + (6-3) + 2 + 2 + 0 = 6+3+2+2 = 13
        assert bd.priority_score == 13

    def test_dual_strength_bonus_triggers(self):
        """Dual-strength bonus activates when both imp >= 3 AND mod >= 3."""
        m = minimal_museum(
            impressionist_strength=4,
            modern_contemporary_strength=3,
            hat_strength=0,
            historical_context_score=4,
            eca_score=0,
            reputation_level="National",
            collection_level="Strong",
        )
        bd = compute_priority_score(m)
        assert bd.dual_strength_bonus == -2
        # (6-4)*2 + (6-4) + 0 + 0 + (-2) = 4+2-2 = 4
        assert bd.priority_score == 4

    def test_dual_strength_bonus_not_triggered_when_mod_below_threshold(self):
        """Bonus does NOT fire when mod_contemporary < 3 even if imp >= 3."""
        m = minimal_museum(
            impressionist_strength=4,
            modern_contemporary_strength=2,
            hat_strength=0,
        )
        bd = compute_priority_score(m)
        assert bd.dual_strength_bonus == 0

    def test_flagship_national_top_scores_clamps_to_one(self):
        """A world-class museum with perfect scores should not go below 1."""
        m = minimal_museum(
            impressionist_strength=5,
            modern_contemporary_strength=5,
            hat_strength=5,
            historical_context_score=5,
            eca_score=5,
            reputation_level="International",
            collection_level="Flagship",
        )
        bd = compute_priority_score(m)
        assert bd.priority_score >= 1
        assert bd.collection_based_pas == 5
        assert bd.effective_pas == 5

    def test_local_small_low_scores(self):
        """A local museum with minimal collections gets a high priority number."""
        m = minimal_museum(
            impressionist_strength=1,
            modern_contemporary_strength=0,
            hat_strength=0,
            historical_context_score=1,
            eca_score=0,
            reputation_level="Local",
            collection_level="Small",
        )
        bd = compute_priority_score(m)
        assert bd.priority_score > 15

    def test_eca_boosts_effective_pas_above_collection_based(self):
        """ECA >= collection art scores should elevate effective_pas."""
        m = minimal_museum(
            impressionist_strength=2,
            modern_contemporary_strength=1,
            hat_strength=0,
            eca_score=4,
            reputation_level="National",
            collection_level="Moderate",
        )
        bd = compute_priority_score(m)
        assert bd.collection_based_pas == 2
        assert bd.effective_pas == 4           # eca dominates

    def test_missing_all_art_strength_cannot_score(self):
        """Museum with no art strength fields cannot be scored."""
        m = minimal_museum(
            impressionist_strength=None,
            modern_contemporary_strength=None,
            hat_strength=None,
        )
        bd = compute_priority_score(m)
        assert bd.can_score is False
        assert any("art_strength" in f for f in bd.missing_fields)

    def test_missing_reputation_cannot_score(self):
        m = minimal_museum(reputation_level=None)
        # Remove legacy fields too
        m.pop("reputation", None)
        bd = compute_priority_score(m)
        assert bd.can_score is False

    def test_missing_collection_cannot_score(self):
        m = minimal_museum(collection_level=None)
        m.pop("collection_tier", None)
        bd = compute_priority_score(m)
        assert bd.can_score is False

    def test_hat_only_museum_scores_correctly(self):
        """A museum strong only in HAT (Historical Art Traditions) can score."""
        m = minimal_museum(
            impressionist_strength=0,
            modern_contemporary_strength=0,
            hat_strength=4,
            historical_context_score=4,
            eca_score=0,
            reputation_level="Regional",
            collection_level="Strong",
        )
        bd = compute_priority_score(m)
        assert bd.can_score is True
        assert bd.collection_based_pas == 4
        assert bd.dual_strength_bonus == 0   # HAT doesn't trigger dual bonus


# ---------------------------------------------------------------------------
# Reputation and collection penalty tables
# ---------------------------------------------------------------------------

class TestPenaltyTables:
    @pytest.mark.parametrize("level,expected", [
        ("International", 0),
        ("National", 0),
        ("Regional", 2),
        ("Supra-Local", 3),
        ("Local", 4),
    ])
    def test_reputation_penalties(self, level, expected):
        assert REPUTATION_PENALTY[level] == expected

    @pytest.mark.parametrize("level,expected", [
        ("Flagship", 0),
        ("Strong", 0),
        ("Moderate", 2),
        ("Small", 4),
    ])
    def test_collection_penalties(self, level, expected):
        assert COLLECTION_PENALTY[level] == expected


# ---------------------------------------------------------------------------
# Outcome tier assignment
# ---------------------------------------------------------------------------

class TestAssignOutcomeTier:
    def _scored(self, **overrides) -> tuple[dict, ScoreBreakdown]:
        m = minimal_museum(**overrides)
        bd = compute_priority_score(m)
        assert bd.can_score, f"Museum could not be scored: {bd.missing_fields}"
        return m, bd

    def test_must_see_when_collection_pas_five(self):
        m, bd = self._scored(
            impressionist_strength=5,
            modern_contemporary_strength=5,
            hat_strength=5,
            reputation_level="International",
            collection_level="Flagship",
        )
        assert assign_outcome_tier(m, bd) == "Must-See"

    def test_must_see_when_historical_context_five(self):
        m, bd = self._scored(
            impressionist_strength=3,
            modern_contemporary_strength=2,
            hat_strength=0,
            historical_context_score=5,
            reputation_level="Regional",
            collection_level="Moderate",
        )
        assert assign_outcome_tier(m, bd) == "Must-See"

    def test_high_priority_low_score(self):
        """Priority score <= 9 should yield High Priority."""
        m, bd = self._scored(
            impressionist_strength=4,
            modern_contemporary_strength=3,
            historical_context_score=4,
            eca_score=0,
            reputation_level="National",
            collection_level="Strong",
        )
        assert bd.priority_score <= 9
        assert assign_outcome_tier(m, bd) == "High Priority"

    def test_background_default_low_art(self):
        """Museum with minimal art scores and local rep should be Background."""
        m, bd = self._scored(
            impressionist_strength=0,
            modern_contemporary_strength=0,
            hat_strength=1,
            historical_context_score=0,
            eca_score=0,
            reputation_level="Local",
            collection_level="Small",
        )
        tier = assign_outcome_tier(m, bd)
        assert tier in ("Background", "Consider")

    def test_regionally_important_regional_museum(self):
        """Score 10-15 + Regional rep + moderate art should be Regionally Important."""
        m, bd = self._scored(
            impressionist_strength=3,
            modern_contemporary_strength=1,
            hat_strength=0,
            historical_context_score=3,
            eca_score=0,
            reputation_level="Regional",
            collection_level="Moderate",
        )
        # score = (6-3)*2 + (6-3) + 2 + 2 + 0 = 6+3+2+2 = 13
        assert 10 <= bd.priority_score <= 15
        assert assign_outcome_tier(m, bd) == "Regionally Important"

    def test_all_tiers_are_known_strings(self):
        """Every score path must return one of the six canonical tier strings."""
        valid_tiers = {
            "Must-See", "High Priority", "Regionally Important",
            "Detour", "Consider", "Background",
        }
        configs = [
            dict(impressionist_strength=5, modern_contemporary_strength=4, hat_strength=3,
                 reputation_level="International", collection_level="Flagship"),
            dict(impressionist_strength=4, modern_contemporary_strength=3,
                 reputation_level="National", collection_level="Strong"),
            dict(impressionist_strength=2, modern_contemporary_strength=1,
                 reputation_level="Regional", collection_level="Moderate"),
            dict(impressionist_strength=1, modern_contemporary_strength=0,
                 reputation_level="Local", collection_level="Small"),
        ]
        for cfg in configs:
            m, bd = self._scored(**cfg)
            tier = assign_outcome_tier(m, bd)
            assert tier in valid_tiers, f"Unknown tier '{tier}' for {cfg}"
