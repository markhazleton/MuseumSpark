"""Pydantic models for the LLM enrichment pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TrustLevel(IntEnum):
    """Hierarchy of source reliability for field-level provenance."""

    UNKNOWN = 0
    LLM_GUESS = 1
    LLM_EXTRACTED = 2
    WIKIPEDIA = 3
    WIKIDATA = 4
    OFFICIAL_EXTRACT = 5
    OFFICIAL_JSON_LD = 6
    MANUAL_OVERRIDE = 10


class EnrichedField(BaseModel, Generic[T]):
    """Provenance envelope for any enriched field."""

    value: T
    source: str = Field(..., description="Specific origin (e.g., 'wikidata', 'official_site')")
    trust_level: TrustLevel = Field(..., description="Numeric trust score")
    confidence: int = Field(..., ge=1, le=5, description="Model confidence in value")
    retrieved_at: datetime = Field(default_factory=_utcnow)


class Recommendation(BaseModel):
    """Proposed change that requires review."""

    field_name: str
    current_value: Any
    proposed_value: Any
    reason: str
    confidence: int = Field(..., ge=1, le=5)
    evidence: str
    source: str
    trust_level: TrustLevel
    retrieved_at: datetime = Field(default_factory=_utcnow)


class PrimaryDomain(str, Enum):
    ART = "Art"
    HISTORY = "History"
    SCIENCE = "Science"
    CULTURE = "Culture"
    SPECIALTY = "Specialty"
    MIXED = "Mixed"


class MuseumRecordUpdate(BaseModel):
    """Strongly-typed model for state file updates (wrapped in EnrichedField)."""

    museum_id: str

    museum_name: Optional[EnrichedField[str]] = None
    city: Optional[EnrichedField[str]] = None
    street_address: Optional[EnrichedField[str]] = None
    postal_code: Optional[EnrichedField[str]] = None
    website: Optional[EnrichedField[str]] = None
    latitude: Optional[EnrichedField[float]] = None
    longitude: Optional[EnrichedField[float]] = None

    primary_domain: Optional[EnrichedField[PrimaryDomain]] = None
    museum_type: Optional[EnrichedField[str]] = None
    audience_focus: Optional[
        EnrichedField[str]
    ] = None

    city_tier: Optional[EnrichedField[int]] = None
    reputation: Optional[EnrichedField[int]] = None
    collection_tier: Optional[EnrichedField[int]] = None
    time_needed: Optional[EnrichedField[str]] = None

    impressionist_strength: Optional[EnrichedField[int]] = None
    modern_contemporary_strength: Optional[EnrichedField[int]] = None
    historical_context_score: Optional[EnrichedField[int]] = None

    notes: Optional[EnrichedField[str]] = None

    confidence: Optional[int] = Field(None, ge=1, le=5)
    data_sources: Optional[list[str]] = None


class ValidationAgentOutput(BaseModel):
    """Complete output from the validation/cleaning agent."""

    state_file_updates: MuseumRecordUpdate
    recommendations: list[Recommendation] = Field(default_factory=list)
    needs_deep_dive: bool = False
    confidence: int = Field(..., ge=1, le=5)
    model_used: str
    agent_version: str = "validation_v1"
    processed_at: datetime = Field(default_factory=_utcnow)
    data_sources: list[str] = Field(default_factory=list)


class CollectionHighlight(BaseModel):
    title: str
    description: Optional[str] = None
    source: Optional[str] = None


class TourPlanningScores(BaseModel):
    """Scoring dimensions for tour planning and filtering (1-10 scale)."""
    
    # Art Movement Specializations (1-10, art museums only)
    contemporary_score: Optional[int] = Field(None, ge=1, le=10, description="Contemporary art (1950-present)")
    modern_score: Optional[int] = Field(None, ge=1, le=10, description="Modern art (1860s-1950)")
    impressionist_score: Optional[int] = Field(None, ge=1, le=10, description="Impressionist & Post-Impressionist")
    expressionist_score: Optional[int] = Field(None, ge=1, le=10, description="Expressionist movements")
    classical_score: Optional[int] = Field(None, ge=1, le=10, description="Classical & Renaissance art")
    
    # Geographic/Cultural Focus (1-10)
    american_art_score: Optional[int] = Field(None, ge=1, le=10, description="American art focus")
    european_art_score: Optional[int] = Field(None, ge=1, le=10, description="European art focus")
    asian_art_score: Optional[int] = Field(None, ge=1, le=10, description="Asian art focus")
    african_art_score: Optional[int] = Field(None, ge=1, le=10, description="African & Indigenous art")
    
    # Medium Specializations (1-10)
    painting_score: Optional[int] = Field(None, ge=1, le=10, description="Painting collection strength")
    sculpture_score: Optional[int] = Field(None, ge=1, le=10, description="Sculpture collection strength")
    decorative_arts_score: Optional[int] = Field(None, ge=1, le=10, description="Decorative arts, ceramics, textiles")
    photography_score: Optional[int] = Field(None, ge=1, le=10, description="Photography collection")
    
    # Collection Characteristics (1-10, all museums)
    collection_depth: int = Field(..., ge=1, le=10, description="1=narrow specialist, 10=encyclopedic")
    collection_quality: int = Field(..., ge=1, le=10, description="1=local, 5=regional, 8=national, 10=world-class")
    exhibition_frequency: Optional[int] = Field(None, ge=1, le=10, description="New shows/exhibitions per year")
    
    # Visitor Experience (1-10, all museums)
    family_friendly_score: int = Field(..., ge=1, le=10, description="Suitability for families with children")
    educational_value_score: int = Field(..., ge=1, le=10, description="Educational programs & resources")
    architecture_score: Optional[int] = Field(None, ge=1, le=10, description="Building itself worth seeing")
    
    # Justification (required)
    scoring_rationale: str = Field(..., description="Brief explanation of key scores (2-3 sentences)")


class DeepDiveAgentOutput(BaseModel):
    """Complete output from the deep dive agent."""

    state_file_updates: MuseumRecordUpdate
    recommendations: list[Recommendation] = Field(default_factory=list)
    summary_short: str
    summary_long: str
    collection_highlights: list[CollectionHighlight] = Field(default_factory=list)
    signature_artists: list[str] = Field(default_factory=list)
    visitor_tips: list[str] = Field(default_factory=list)
    best_for: Optional[str] = None
    historical_significance: Optional[str] = None
    architectural_notes: Optional[str] = None
    curatorial_approach: Optional[str] = None
    tour_planning_scores: Optional[TourPlanningScores] = None
    sources_consulted: list[str] = Field(default_factory=list)
    thinking_budget_used: Optional[int] = None
    confidence: int = Field(..., ge=1, le=5)
    model_used: str
    agent_version: str = "deep_dive_v1"
    processed_at: datetime = Field(default_factory=_utcnow)

