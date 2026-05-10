# AI / LLM Enrichment Plan

## Engineering Change Proposal (ECP) — MuseumSpark LLM Enrichment Pipeline Stabilization
>
> **Status:** Active / In-Progress  
> **Date:** January 15, 2026

**Document Purpose**
This ECP formalizes a set of engineering changes to improve correctness, repeatability, and maintainability of the enrichment pipeline described in this document, while staying aligned to the Master Requirements (MRD) policies: full backbone for all museums; scoring only for qualifying art museums; strict enumerations for “Time Needed”; and computed fields such as nearby museum count.

---

### 1) Background / Current State

The current architecture uses:

* A **MuseumContext** object that combines the state record, cached free-source data (Wikidata/OSM/Wikipedia), cached website scrape/JSON-LD, and prior LLM results.
* A **two-agent approach**:

  * Validation/Cleaning agent (fast/cheap) for all museums
  * Deep Dive agent (higher-quality model) for top museums only
* Guardrails and controls already described: JSON-mode, schema-first prompts, caching, budgets, source precedence, placeholder defense, and QA gold sets.  

---

### 2) Problem Statement (Why change)

As written, the plan correctly states a **source precedence hierarchy** and mentions provenance output, but it does not fully specify **how precedence is enforced at the field level**, nor how to prevent **churn** and **regressions** when re-running agents over time.  

---

### 3) Goals and Non-Goals

**Goals**

1. Enforce **field-level source precedence** so lower-trust sources cannot overwrite higher-trust values.
2. Reduce dataset churn via deterministic normalization, bounded write rules, and consistent derived-field computation.  
3. Make QA gates enforceable (hard stops) using validation failure rate, drift thresholds, and gold-set comparisons.
4. Ensure MRD policies remain hard guardrails (art-only scoring, time-needed whitelist).  

**Non-Goals**

* Changing the MRD scoring formula or tier definitions.
* Building the full web app UI/SQLite backend (this ECP is pipeline-focused).

---

### 4) Proposed Changes (Design Summary)

#### Change A — Field-Level Provenance and Trust Enforcement (Priority 1)

**What**
Introduce a standardized “field provenance” envelope for every enriched field written to state records and museum subfolder outputs.

**Data model (conceptual)**

* For each mutable field:

  * `value`
  * `source` (e.g., `website_json_ld`, `official_site_text`, `wikidata`, `wikipedia`, `llm`)
  * `retrieved_at`
  * `trust_level` (ordered to match stated hierarchy)

**Write rules**

* Overwrite only if:

  1. `new_trust_level > old_trust_level`, OR
  2. `new_trust_level == old_trust_level` AND `newer(retrieved_at)` AND `non_placeholder`, OR
  3. `manual_lock == false` (for protected fields)
* Enforce placeholder defense across all fields.

**Where stored**

* Persist a `provenance.json` per museum folder (already present conceptually) and ensure state-file updates reference the same trust metadata.

**Rationale**
Operationalizes the plan’s “never overwrite higher-trust with lower” promise into deterministic behavior.

---

#### Change B — “Recommend vs Write” Mode for High-Churn Ranking Fields (Priority 1)

**What**
For fields that influence trip prioritization and are vulnerable to LLM variance (e.g., Reputation Tier, Collection Tier, Time Needed, scoring fields), switch the LLM from “authoritative writer” to “proposal generator” unless evidence is high-trust.

**Rules**

* Baseline computed/heuristic result is produced deterministically where feasible (e.g., Time Needed mapping rules).
* LLM outputs include:

  * recommendation + evidence pointers + confidence
* Auto-apply only when:

  * confidence ≥ threshold AND source evidence is ≥ Wikidata/Wikipedia, or official website-derived
* Otherwise, enqueue for manual review (aligning with “human review focus” for GOLD/conf≤3).

**Hard guardrails**

* Art-only scoring enforced: scoring fields cannot be written unless `primary_domain = Art`.  

---

#### Change C — Context Shaping and Token Budget Governance (Priority 2)

**What**
Before any model call, construct a compact “evidence packet” from cached sources rather than sending raw HTML or large claim sets.

**Controls**

* Enforce per-museum max context size and per-batch budget pre-checks (already stated; formalize as required pipeline behavior).
* Maintain deterministic truncation rules (e.g., top N JSON-LD fields, summary character caps).

**Rationale**
Reduces cost drift and improves output stability across runs.

---

#### Change D — Enforceable Quality Gates and Release Blocking (Priority 2)

**What**
Convert monitoring suggestions into hard gating conditions.

**Blocking conditions**

* Validation failure rate exceeds threshold → stop run.
* Gold-set drift exceeds threshold → stop run.
* Any MRD scoring-field changes for GOLD-tier museums require manual approval before merge/release.

---

#### Change E — Hash Folder Strategy: Add Human-Readable Alias (Priority 3)

**What**
Keep the deterministic `folder_hash` (if desired) but add a human-readable alias file (or optional alternate folder structure) for maintainability.

**Current**

* `folder_hash` is part of MuseumContext and used for folder paths.  

**Proposed**

* Add `slug_alias` = `{city_slug}-{museum_slug}--{museum_id_suffix}` stored in `core.json` and/or an index mapping.
* Keep existing hash-based lookup for determinism; add alias for review/debug.

---

### 5) Implementation Plan (Work Packages)

**WP1 — Provenance + Trust Framework (2–3 days)**

* Define trust enum matching the documented hierarchy.
* Implement field envelope + write rules
* Update state-file update function to require provenance on any mutation
* Add regression tests for “cannot overwrite higher trust with lower trust”

**WP2 — Recommend vs Write + Review Queue (2–3 days)**

* Introduce `recommendations.json` / `review_queue.json` per run
* Modify both agents’ output models to include evidence + confidence
* Apply auto-write only when guardrails satisfied
* Enforce MRD art-only scoring and time-needed whitelist at write-time.

**WP3 — Evidence Packet Builder + Token Guards (1–2 days)**

* Implement deterministic evidence packet construction from cached sources in MuseumContext
* Enforce per-item max size; truncate predictably
* Add unit tests around truncation determinism

**WP4 — Quality Gates as Pipeline Stops (1–2 days)**

* Implement run-level metrics and thresholds:

  * validation failure rate gate
  * gold-set drift gate
* Add CLI “--fail-on-drift” default true

**WP5 — Human-Readable Alias (0.5–1 day)**

* Implement slug generation + mapping file
* Ensure no breaking changes to existing folder layout

---

### 6) Acceptance Criteria (Definition of Done)

1. **Precedence correctness**: Lower-trust sources cannot overwrite higher-trust values (automated tests).
2. **Churn reduction**: Re-running validation on unchanged inputs produces zero diffs (excluding timestamps).
3. **MRD compliance**:

   * Non-art museums never receive scoring fields.  
   * Time Needed always in the MRD whitelist.  
4. **Quality gates**:

   * Pipeline halts when validation failure rate threshold is exceeded.
   * Pipeline halts when gold-set drift exceeds threshold.
5. **Cost governance**: Budget pre-checks prevent batch runs from exceeding configured spend.

---

### 7) Risks and Mitigations

* **Risk: Added metadata increases file size and complexity.**
  Mitigation: Keep provenance per-field minimal; store verbose diffs only in run artifacts.

* **Risk: Recommend-vs-write slows enrichment throughput.**
  Mitigation: Apply only to high-impact ranking fields; keep straightforward normalization auto-write.

* **Risk: Source evidence extraction becomes brittle across websites.**
  Mitigation: Prefer JSON-LD and targeted scraping; treat scrape failures as “no-evidence,” not “LLM guess.”

---

### 8) Rollout Strategy

1. Enable provenance + precedence rules first (WP1) and run on a small state slice.
2. Enable recommend-vs-write for ranking fields next (WP2).
3. Add quality gates and gold-set drift blocking (WP4).
4. Expand by MRD phase order, using checkpoints as defined.  

---

### 9) Operational Metrics (Monitoring)

Minimum run metrics:

* cache hit %, validation error rate, drift score vs gold set, tokens and estimated spend, mean latency.
* count of “manual review required” items (confidence ≤ 3).

---

### 10) Deliverables

* Updated Pydantic models (agent outputs include provenance, evidence, confidence)
* Precedence-aware write module
* Evidence packet builder module
* QA gate module + gold-set comparator
* Run artifact outputs: `changes.json`, `review_queue.json`, summary metrics

---

## Original Plan & Technical Specifications

## Goals

* Add per-museum canonical detail (LLM-assisted) without breaking current state/index pipelines.
* Keep state files canonical for museums without a per-museum file; when a per-museum file exists, it becomes the source of truth for that museum.
* Produce LLM summaries with tiered quality (GOLD/SILVER) based on museum priority.
* **Focus on top 100 art museums first** to deliver usable data quickly within a ~$5-8 budget using OpenAI models.
* Maximize free data sources (Wikidata, OSM, Wikipedia) before any LLM calls.
* Prefer **OpenAI GPT-4o-mini (validation) + GPT-4o (deep dive)**; allow a toggle to Claude models only if OpenAI is unavailable.
* **Use Pydantic agents with strong model validation** to ensure data quality and structured outputs.

## MRD Alignment (Travel Prioritization)

* Center on the MRD priority-score use case: city-tiering, reputation, collection tier, time-needed, and nearby-museum count all remain populated and current.
* Limit art scoring to museums with `primary_domain = Art` or aligned art subtypes; non-art museums remain unscored to preserve planning coverage without inflating priority.
* Preserve the MRD inclusion policy: keep all museums in the backbone; score only relevant art museums.
* Keep MRD notes fields rich for travel context (signature artists, historical significance, visitor guidance) to support itinerary decisions.

## Museum Folder Naming (Deterministic Hash)

Use a deterministic one-way hash to create short, filesystem-safe folder names from `museum_id`:

```python
import hashlib

def museum_id_to_folder(museum_id: str) -> str:
    """
    Generate a short, deterministic folder name from museum_id.

    Example:
        museum_id: "usa-ny-new-york-metropolitan-museum-of-art"
        folder:    "m_a1b2c3d4"  (8-char hash prefix)

    The hash is:
    - Deterministic: same museum_id always produces same folder
    - One-way: cannot reverse to get museum_id
    - Short: 8 characters + prefix for filesystem safety
    - Collision-resistant: SHA256 truncated to 8 hex chars (4 billion possibilities)
    """
    hash_bytes = hashlib.sha256(museum_id.encode('utf-8')).hexdigest()
    return f"m_{hash_bytes[:8]}"

# Lookup file maps hash back to museum_id
# data/states/{STATE}/_museum_lookup.json
{
    "m_a1b2c3d4": "usa-ny-new-york-metropolitan-museum-of-art",
    "m_e5f6g7h8": "usa-il-chicago-art-institute-of-chicago"
}
```

**Folder structure with hash:**

```
data/states/NY/
├── NY.json                           # State file (canonical)
├── _museum_lookup.json               # Hash → museum_id mapping
├── m_a1b2c3d4/                       # Metropolitan Museum
│   ├── core.json
│   ├── summaries.json
│   └── provenance.json
└── m_b2c3d4e5/                       # Another museum
    ├── core.json
    └── summaries.json
```

## Agent Input: Complete Museum Context

**Both agents receive ALL available data for a museum:**

```python
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class MuseumContext(BaseModel):
    """Complete context passed to both agents."""

    # Core identity from state file
    museum_id: str
    museum_name: str
    state_province: str
    city: str
    country: str

    # All fields from STATE JSON file
    state_record: dict = Field(..., description="Complete record from {STATE}.json")

    # All cached data for this museum
    cached_data: CachedMuseumData

    # Computed metadata
    folder_hash: str = Field(..., description="Deterministic hash folder name")
    has_existing_enrichment: bool = False

class CachedMuseumData(BaseModel):
    """All cached data sources for a museum."""

    # Free API cache
    wikidata_entity: Optional[dict] = None
    wikidata_claims: Optional[dict] = None
    nominatim_result: Optional[dict] = None
    wikipedia_summary: Optional[str] = None

    # Website scraping cache
    website_html: Optional[str] = None
    website_json_ld: Optional[dict] = None
    subpages_scraped: list[dict] = Field(default_factory=list)

    # Previous LLM results (if re-running)
    previous_validation: Optional[dict] = None
    previous_classification: Optional[dict] = None
    previous_scoring: Optional[dict] = None
    previous_deep_dive: Optional[dict] = None

    # Cache metadata
    cache_timestamp: Optional[datetime] = None
    cache_version: str = "v1"

def load_museum_context(museum_id: str, state_code: str) -> MuseumContext:
    """Load complete context for a museum from all sources."""

    # 1. Load state file record
    state_path = PROJECT_ROOT / "data" / "states" / f"{state_code}.json"
    state_data = load_json(state_path)
    state_record = next(
        (m for m in state_data["museums"] if m["museum_id"] == museum_id),
        None
    )

    # 2. Generate folder hash
    folder_hash = museum_id_to_folder(museum_id)

    # 3. Load all cached data
    cached_data = load_cached_data(museum_id, state_code, folder_hash)

    # 4. Check for existing enrichment
    museum_folder = PROJECT_ROOT / "data" / "states" / state_code / folder_hash
    has_existing = museum_folder.exists()

    return MuseumContext(
        museum_id=museum_id,
        museum_name=state_record["museum_name"],
        state_province=state_record["state_province"],
        city=state_record.get("city", "Unknown"),
        country=state_record.get("country", "USA"),
        state_record=state_record,
        cached_data=cached_data,
        folder_hash=folder_hash,
        has_existing_enrichment=has_existing
    )
```

## Pydantic Agent Architecture

Two specialized Pydantic agents handle different enrichment tasks. **Both receive the complete `MuseumContext`**.

### Agent 1: Data Validation & Cleaning Agent (Fast/Cheap)

**Purpose:** Validate, clean, and classify museum records at scale using a fast, cost-effective model.

**Primary Model:** OpenAI `gpt-4o-mini` ($0.15/$0.60 per MTok)

**Fallback:** Claude Haiku only if OpenAI is unavailable.

**Input:** Complete `MuseumContext` (state record + all cached data)

**Output:**

1. Updates to STATE file record (via strongly-typed model)
2. Creates/updates museum subfolder with validated data

**Responsibilities:**

* Validate existing data against schema
* Clean and normalize fields (addresses, URLs, names)
* Classify `primary_domain` and `museum_type`; only set art scoring fields when `primary_domain = Art`
* Fill MRD travel-prioritization fields where safe: `city_tier`, `reputation`, `collection_tier`, `time_needed`
* Identify missing/placeholder fields
* Score art museums (impressionist_strength, modern_contemporary_strength, historical_context_score) only for art museums
* Flag records needing deep dive

**Pydantic Models:**

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, Generic, TypeVar, Any
from enum import IntEnum, Enum
from datetime import datetime

T = TypeVar("T")

class TrustLevel(IntEnum):
    """Hierarchy of source reliability for field-level provenance."""
    UNKNOWN = 0
    LLM_GUESS = 1          # Generated by LLM with low confidence
    LLM_EXTRACTED = 2      # Extracted by LLM from unstructured text
    WIKIPEDIA = 3          # Sourced from Wikipedia summary/infobox
    WIKIDATA = 4           # Sourced from structured Wikidata
    OFFICIAL_EXTRACT = 5   # Extracted from official website text
    OFFICIAL_JSON_LD = 6   # Structured data from official site
    MANUAL_OVERRIDE = 10   # Human-verified truth

class EnrichedField(BaseModel, Generic[T]):
    """Provenance envelope for any enriched field."""
    value: T
    source: str = Field(..., description="Specific origin (e.g., 'wikidata', 'url')")
    trust_level: TrustLevel = Field(..., description="Numeric trust score")
    confidence: int = Field(..., ge=1, le=5, description="Model confidence in value")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

class Recommendation(BaseModel):
    """Proposed change for a field that requires review."""
    field_name: str
    current_value: Any
    proposed_value: Any
    reason: str
    confidence: int
    evidence: str

class PrimaryDomain(str, Enum):
    ART = "Art"
    HISTORY = "History"
    SCIENCE = "Science"
    CULTURE = "Culture"
    SPECIALTY = "Specialty"
    MIXED = "Mixed"

class MuseumRecordUpdate(BaseModel):
    """Strongly-typed model for STATE file updates.

    Only non-None fields will be written back to the state file.
    This ensures we never accidentally overwrite good data with nulls.
    """
    # Identity (read-only, for validation)
    museum_id: str

    # Fields that can be updated (wrapped in EnrichedField)
    museum_name: Optional[EnrichedField[str]] = None
    city: Optional[EnrichedField[str]] = None
    street_address: Optional[EnrichedField[str]] = None
    postal_code: Optional[EnrichedField[str]] = None
    website: Optional[EnrichedField[str]] = None
    latitude: Optional[EnrichedField[float]] = None
    longitude: Optional[EnrichedField[float]] = None

    # Classification fields
    primary_domain: Optional[EnrichedField[PrimaryDomain]] = None
    museum_type: Optional[EnrichedField[str]] = Field(None)
    audience_focus: Optional[EnrichedField[Literal["General", "Family", "Academic", "Children", "Specialist"]]] = None

    # MRD fields
    city_tier: Optional[EnrichedField[int]] = None
    reputation: Optional[EnrichedField[int]] = None
    collection_tier: Optional[EnrichedField[int]] = None
    time_needed: Optional[EnrichedField[str]] = None

    # Scoring fields (art museums only)
    impressionist_strength: Optional[EnrichedField[int]] = None
    modern_contemporary_strength: Optional[EnrichedField[int]] = None
    historical_context_score: Optional[EnrichedField[int]] = None

    # User-facing content
    notes: Optional[EnrichedField[str]] = Field(None)

    # Metadata
    confidence: Optional[int] = Field(None, ge=1, le=5)
    data_sources: Optional[list[str]] = None

    @field_validator('museum_type')
    @classmethod
    def validate_museum_type(cls, v):
        if v and v.value and len(v.value.split()) > 6:
            raise ValueError('museum_type should be 2-4 words')
        return v

    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        if v and v.value and not v.value.startswith(('http://', 'https://')):
            v.value = f"https://{v.value}"
        return v

class ValidationAgentOutput(BaseModel):
    """Complete output from validation agent."""

    # Updated: Split authoritative updates from recommendations
    state_file_updates: MuseumRecordUpdate
    recommendations: list[Recommendation] = Field(default_factory=list)

    # Validation results
    is_valid: bool
    missing_required: list[str] = Field(default_factory=list)
    placeholder_fields: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)

    # Recommendations
    needs_deep_dive: bool = Field(default=False, description="Flag for complex cases")
    deep_dive_reason: Optional[str] = None

    # Provenance
    agent_version: str = "v1.0"
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gpt-4o-mini-2025-12-01"
    confidence: int = Field(..., ge=1, le=5)
```

**Usage:**

```python
def run_validation_agent(context: MuseumContext) -> ValidationAgentOutput:
    """Run validation agent with complete museum context.

    Note: Uses build_evidence_packet() to enforce strict token budgets
    and prevent context window overflow.
    """
    
    # 1. Shape context into compact evidence packet
    evidence_packet = build_evidence_packet(
        context, 
        max_tokens=1500, 
        include_json_ld=True
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini-2025-12-01",
        max_tokens=2000,
        temperature=0,
        messages=[{
            "role": "system",
            "content": "You are a precise data-cleaning agent. Respond with strictly valid JSON that conforms to the provided Pydantic schema."
        }, {
            "role": "user",
            "content": f"""Validate and clean this museum record using the evidence provided.

## Evidence Packet:
{json.dumps(evidence_packet, indent=2)}

Analyze available data and return a ValidationAgentOutput JSON.
- Use 'state_file_updates' ONLY for high-confidence fixes backed by high-trust evidence.
- Use 'recommendations' for low-confidence guesses or major changes to ranking fields (Reputation, Collection Tier).
- Set TrustLevel accurately for every updated field.

Return JSON only, matching the ValidationAgentOutput schema."""
        }]
    )

    return ValidationAgentOutput.model_validate_json(response.choices[0].message.content)
```

### Agent 2: Deep Dive Research Agent (Thorough/Premium)

**Purpose:** Generate rich, detailed analysis for high-priority museums using extended thinking.

**Primary Model:** OpenAI `gpt-4o` ($2.50/$10.00 per MTok)

**Fallback:** Claude Sonnet with extended thinking only if OpenAI is unavailable.

**Input:** Complete `MuseumContext` (state record + all cached data)

**Output:**

1. Updates to STATE file record (via strongly-typed model)
2. Creates detailed museum subfolder files (summaries.json, analysis.json)

**Responsibilities:**

* Generate detailed user-facing descriptions
* Research collection highlights and signature works
* Analyze historical significance and curatorial approach
* Identify visitor tips and practical information
* Strengthen MRD travel signals: emphasize signature artists, flagship collections, and time-needed guidance
* Cross-reference multiple sources for accuracy

**Pydantic Models:**

```python
class CollectionHighlight(BaseModel):
    """Notable work or collection area."""
    name: str = Field(..., max_length=100)
    artist_or_period: Optional[str] = Field(None, max_length=100)
    significance: str = Field(..., max_length=200)

class DeepDiveAgentOutput(BaseModel):
    """Complete output from deep dive agent."""

    # What to update in STATE file
    state_file_updates: MuseumRecordUpdate
    recommendations: list[Recommendation] = Field(default_factory=list)

    # Rich content for museum subfolder
    summary_short: str = Field(..., max_length=500, description="User-facing notes")
    summary_long: str = Field(..., max_length=2000, description="Detailed narrative")

    # Structured analysis
    collection_highlights: list[CollectionHighlight] = Field(default_factory=list, max_length=5)
    signature_artists: list[str] = Field(default_factory=list, max_length=10)
    visitor_tips: list[str] = Field(default_factory=list, max_length=5)
    best_for: list[str] = Field(default_factory=list, description="Audience types")

    # Optional deep analysis
    historical_significance: Optional[str] = Field(None, max_length=500)
    architectural_notes: Optional[str] = Field(None, max_length=300)
    curatorial_approach: Optional[str] = Field(None, max_length=300)

    # Art museum specific (if applicable)
    art_scoring: Optional[ArtMuseumScoring] = None

    # Provenance
    sources_consulted: list[str] = Field(default_factory=list)
    agent_version: str = "v1.0"
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = "gpt-4o-2025-12-01"
    thinking_budget_used: Optional[int] = None
    confidence: int = Field(..., ge=1, le=5)

    @field_validator('summary_short')
    @classmethod
    def validate_summary_short(cls, v):
        if len(v) < 100:
            raise ValueError('summary_short should be at least 100 characters')
        return v

class ArtMuseumScoring(BaseModel):
    """Scoring specific to art museums."""
    impressionist_strength: int = Field(..., ge=1, le=5, description="1=none, 5=flagship")
    modern_contemporary_strength: int = Field(..., ge=1, le=5)
    historical_context_score: int = Field(..., ge=1, le=5, description="Curatorial quality")
    primary_art: Literal["Impressionist", "Modern/Contemporary"]
    score_notes: str = Field(..., max_length=200)
```

**Usage with Extended Thinking:**

```python
def run_deep_dive_agent(context: MuseumContext) -> DeepDiveAgentOutput:
    """Run deep dive agent with complete museum context and extended thinking."""

    # Construct strict context
    evidence_packet = build_evidence_packet(context, max_tokens=6000)

    response = client.chat.completions.create(
        model="gpt-4o-2025-12-01",
        max_tokens=16000,
        temperature=0.1,
        messages=[{
            "role": "system",
            "content": "You are a precise research analyst. Respond with strictly valid JSON that conforms to the provided Pydantic schema."
        }, {
            "role": "user",
            "content": f"""Research this museum thoroughly using the evidence provided.

## Evidence Packet:
{json.dumps(evidence_packet, indent=2)}

Provide a comprehensive DeepDiveAgentOutput with:
1. state_file_updates: Verified facts (use TrustLevel)
2. recommendations: Suggested changes that need review
3. summary_short: Compelling 2-3 sentence description (100-500 chars)
4. summary_long: Detailed narrative about the museum (up to 2000 chars)
5. collection_highlights: Up to 5 notable works or collections
6. signature_artists: Key artists represented
7. visitor_tips: Practical advice for visitors
8. art_scoring: If this is an art museum, provide scoring

Return JSON only, matching the DeepDiveAgentOutput schema."""
        }]
    )

    response_content = response.choices[0].message.content
    result = DeepDiveAgentOutput.model_validate_json(response_content)
    result.thinking_budget_used = None
    return result
```

## Output: State File Updates + Museum Subfolder

**Both agents produce two outputs:**

### 1. Update STATE File Record

```python
def apply_state_file_updates(
    state_code: str,
    museum_id: str,
    updates: MuseumRecordUpdate,
    context: MuseumContext
) -> None:
    """Apply agent updates to the state file, implementing trust precedence."""

    state_path = PROJECT_ROOT / "data" / "states" / f"{state_code}.json"
    state_data = load_json(state_path)

    # Find and update the museum record
    for i, museum in enumerate(state_data["museums"]):
        if museum["museum_id"] == museum_id:
            # Only update non-None fields
            update_dict = updates.model_dump(exclude_none=True, exclude={"museum_id"})

            for key, field_wrapper in update_dict.items():
                if not isinstance(field_wrapper, dict) or 'trust_level' not in field_wrapper:
                    continue # specific handling for scalar vs wrapped needed in real impl
                
                # Unwrap the value
                new_val = field_wrapper['value']
                new_trust = field_wrapper['trust_level']

                # Trust Precedence Logic (simplified)
                # In real implementation: Compare against stored provenance 
                museum[key] = new_val

            # Update metadata
            museum["updated_at"] = datetime.utcnow().isoformat()
            museum["last_updated"] = datetime.utcnow().date().isoformat()

            state_data["museums"][i] = museum
            break

    # Save state file
    save_json(state_path, state_data)
```

### 2. Create Museum Subfolder

```python
def write_museum_subfolder(
    state_code: str,
    museum_id: str,
    folder_hash: str,
    output: ValidationAgentOutput | DeepDiveAgentOutput
) -> None:
    """Create/update museum-specific subfolder with enrichment data."""

    # Create folder
    museum_folder = PROJECT_ROOT / "data" / "states" / state_code / folder_hash
    museum_folder.mkdir(parents=True, exist_ok=True)

    # Update lookup file
    lookup_path = PROJECT_ROOT / "data" / "states" / state_code / "_museum_lookup.json"
    lookup = load_json(lookup_path) if lookup_path.exists() else {}
    lookup[folder_hash] = museum_id
    save_json(lookup_path, lookup)

    # Write core.json (canonical record snapshot)
    core_data = {
        "museum_id": museum_id,
        "folder_hash": folder_hash,
        "state_file_updates": output.state_file_updates.model_dump(exclude_none=True),
        "updated_at": datetime.utcnow().isoformat()
    }
    save_json(museum_folder / "core.json", core_data)

    # Write provenance.json (Field-Level History)
    provenance_record = {
        "run_metadata": {
            "agent_version": output.agent_version,
            "model_used": output.model_used,
            "processed_at": output.processed_at.isoformat(),
            "confidence": output.confidence,
        },
        "field_provenance": {}
    }
    
    # Extract field provenance from updates
    updates_dump = output.state_file_updates.model_dump(exclude_none=True)
    for k, v in updates_dump.items():
        if isinstance(v, dict) and 'trust_level' in v:
            provenance_record["field_provenance"][k] = {
                "source": v['source'],
                "trust_level": v['trust_level'],
                "retrieved_at": v['retrieved_at']
            }
            
    if isinstance(output, DeepDiveAgentOutput):
        provenance_record["run_metadata"]["thinking_budget_used"] = output.thinking_budget_used
        provenance_record["run_metadata"]["sources_consulted"] = output.sources_consulted

        # Write summaries.json for deep dive
        summaries_data = {
            "museum_id": museum_id,
            "summary_short": output.summary_short,
            "summary_long": output.summary_long,
            "collection_highlights": [h.model_dump() for h in output.collection_highlights],
            "signature_artists": output.signature_artists,
            "visitor_tips": output.visitor_tips,
            "best_for": output.best_for,
            "historical_significance": output.historical_significance,
            "architectural_notes": output.architectural_notes,
            "generated_at": output.processed_at.isoformat(),
            "model": output.model_used
        }
        save_json(museum_folder / "summaries.json", summaries_data)

        # Write analysis.json if art museum
        if output.art_scoring:
            analysis_data = {
                "museum_id": museum_id,
                "art_scoring": output.art_scoring.model_dump(),
                "curatorial_approach": output.curatorial_approach,
                "generated_at": output.processed_at.isoformat()
            }
            save_json(museum_folder / "analysis.json", analysis_data)

    save_json(museum_folder / "provenance.json", provenance_data)
```

## Agent Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ENRICHMENT PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 0: Free Enrichment (All 1,269 museums)                           │
│  ├── Wikidata, OSM, Wikipedia → Cache                                  │
│  └── Website scraping → Cache                                          │
│                                                                         │
│  Step 1: Load Complete Context                                          │
│  ├── Read STATE file record                                            │
│  ├── Load ALL cached data (Wikidata, Wikipedia, website, previous LLM) │
│  ├── Generate folder_hash from museum_id                               │
│  └── Build MuseumContext object                                        │
│                                                                         │
│  Step 2: Validation Agent (All museums)                                 │
│  ├── Input: Complete MuseumContext                                     │
│  ├── Model: GPT-4o-mini (fallback Haiku)                               │
│  ├── Output: ValidationAgentOutput (Pydantic)                          │
│  ├── → Update STATE file with state_file_updates                       │
│  ├── → Create museum subfolder: {hash}/core.json, provenance.json      │
│  └── → Flag needs_deep_dive for top museums                            │
│                                                                         │
│  Step 3: Deep Dive Agent (Top 100 only)                                 │
│  ├── Input: Complete MuseumContext (including validation results)      │
│  ├── Model: GPT-4o (fallback Sonnet)                                   │
│  ├── Output: DeepDiveAgentOutput (Pydantic)                            │
│  ├── → Update STATE file with state_file_updates                       │
│  └── → Create/update subfolder: summaries.json, analysis.json          │
│                                                                         │
│  Step 4: Rebuild Index                                                  │
│  ├── Merge STATE files + museum subfolders                             │
│  ├── Pydantic validation on all records                                │
│  └── Compute derived fields (priority_score, nearby_museum_count) per MRD │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Tiers & Canonical Sources

* **Index (derived):** data/index/all-museums.json rebuilt from merged state bundles; used for browse/search.
* **State (canonical unless overridden):** data/states/{STATE}.json remains canonical for museums without per-museum detail.
* **Per-museum (canonical when present):** data/states/{STATE}/{folder_hash}/ holds multi-file detail; overrides the corresponding entry in the state bundle when rebuilding.

## MRD Field Completion Rules (LLM + Heuristics)

* **City Tier:** Prefer authoritative city tier if present; otherwise infer by population or metro rank if cached; never downgrade manually set tiers.
* **Reputation Tier:** Use MRD scale (0=International, 1=National, 2=Regional, 3=Local); only upgrade when corroborated by at least two high-trust sources (e.g., AAMD membership + encyclopedic collection footprint).
* **Collection Tier:** Map to MRD scale (0=Flagship, 1=Strong, 2=Moderate, 3=Small); do not infer from reputation alone—require collection size, breadth, or known holdings evidence.
* **Time Needed:** Choose from {"Quick stop (<1 hr)", "Half day", "Full day"}; for campuses with multiple buildings, prefer "Half day" unless clearly small; never emit free text.
* **Nearby Museum Count:** Recompute in index build from the merged dataset; do not let LLM write this field.
* **Primary Domain:** Only set art scoring fields when `primary_domain = Art`; leave non-art museums unscored per MRD policy.
* **Notes:** Keep travel-useful specifics—signature artists, flagship collections, historical significance, visitor logistics; avoid generic praise.

## Naming & Paths

* **museum_id:** `{country}-{state}-{city_slug}-{museum_slug}`, lowercase, ASCII, hyphen-separated
* **folder_hash:** `m_{sha256(museum_id)[:8]}` - deterministic 8-char hash
* **Lookup file:** `data/states/{STATE}/_museum_lookup.json` maps hash → museum_id

**Folder layout:**

```
data/states/{STATE}/
├── {STATE}.json                      # State file (canonical source)
├── _museum_lookup.json               # Hash → museum_id mapping
├── m_{hash1}/                        # Museum subfolder
│   ├── core.json                     # Canonical record + updates
│   ├── summaries.json                # LLM-generated descriptions
│   ├── analysis.json                 # Art scoring + deep analysis
│   └── provenance.json               # Agent metadata + sources
└── m_{hash2}/
    └── ...
```

## Three-Tier Model Strategy (Cost Optimization)

| Tier | Model | Agent | Use Case | Cost/MTok (in/out) |
|------|-------|-------|----------|-------------------|
| Tier 0 | Free APIs | N/A | Wikidata, OSM, Wikipedia | $0 |
| Tier 1 | GPT-4o-mini | Validation | Classification, scoring, cleaning | $0.15/$0.60 |
| Tier 2 | GPT-4o | Deep Dive | Top 100 detailed descriptions | $2.50/$10.00 |

**Fallback option:** Claude Haiku (Tier 1) and Claude Sonnet (Tier 2) only if OpenAI endpoints are unavailable.

## LLM Response Caching

Cache all LLM responses in the museum subfolder:

```
data/states/{STATE}/{folder_hash}/
├── cache/
│   ├── validation_v1.json     # ValidationAgentOutput
│   └── deep_dive_v1.json      # DeepDiveAgentOutput
```

## Scoring (MRD v1.0)

* Applies to art museums only.
* Inputs: impressionist_strength, modern_contemporary_strength, historical_context_score, reputation_tier, collection_tier
* Derive: primary_art = max(impressionist_strength, modern_contemporary_strength)
* Dual-strength bonus: subtract 2 if both art strengths ≥ 4
* Formula (lower is better):
  $$\text{priority\_score} = (6 - \text{primary\_art}) \times 3 + (6 - \text{historical\_context\_score}) \times 2 + \text{reputation\_penalty} + \text{collection\_penalty} - \text{dual\_strength\_bonus}$$

## Quality Tiers

| Tier | Museums | Agent | Model | Fields | Human Review |
|------|---------|-------|-------|--------|--------------|
| GOLD | Top 50 art | Deep Dive | GPT-4o (fallback Sonnet) | All + detailed analysis | Required |
| SILVER | 51-100 art | Deep Dive | GPT-4o (fallback Sonnet) | Scoring + brief notes | 10% spot-check |
| BRONZE | All others | Validation | GPT-4o-mini (fallback Haiku) | Cleaned + free-source fields | Automated |

## Budget & Cost Estimate (OpenAI-first)

Assumes total prompt+completion tokens shown per task.

| Task | Museums | Agent | Model | Est. Tokens | Est. Cost |
|------|---------|-------|-------|-------------|-----------|
| Free enrichment | 1,269 | N/A | N/A | 0 | $0 |
| Validation | 1,269 | Validation | GPT-4o-mini | 500K | ~$0.38 |
| Deep Dive (GOLD) | 50 | Deep Dive | GPT-4o | 150K | ~$1.88 |
| Deep Dive (SILVER) | 50 | Deep Dive | GPT-4o | 100K | ~$1.25 |
| Buffer (retries) | - | - | - | - | $1.00 |
| **Total** | **1,269** | Mixed | Mixed | **~750K** | **~$4.50** |

**Anthropic fallback pricing (if toggled):** Haiku $0.25/$1.25 MTok; Sonnet $3/$15 MTok.

**Budget guardrails:** enforce a hard ceiling via per-run budget flags and abort if estimated remaining budget < 15% of ceiling.

## Execution Steps

### Step 1: Run Free Enrichment on All Museums

```bash
python scripts/enrich-open-data.py --state ALL --compute-mrd-fields --scrape-website
```

### Step 2: Run Validation Agent on All Museums

```bash
python scripts/agents/validation_agent.py --all-states --budget 1.00 --provider openai --model gpt-4o-mini
```

### Step 3: Run Deep Dive Agent on Top 100

```bash
python scripts/agents/deep_dive_agent.py --top-n 100 --budget 3.50 --provider openai --model gpt-4o --checkpoint-interval 10
```

### Step 4: Validate and Rebuild Index

```bash
python scripts/validate-json.py
python scripts/build-index.py --calculate-scores --update-nearby-counts
python scripts/build-progress.py
```

## File Structure for Agents

```
scripts/
├── agents/
│   ├── __init__.py
│   ├── models.py              # All Pydantic models (MuseumContext, outputs)
│   ├── context.py             # load_museum_context(), museum_id_to_folder()
│   ├── validation_agent.py    # Data validation & cleaning
│   ├── deep_dive_agent.py     # Rich descriptions with thinking
│   ├── output.py              # apply_state_file_updates(), write_museum_subfolder()
│   └── utils.py               # Caching, budget management, checkpoints
├── enrich-open-data.py        # Existing free enrichment
├── enrich-llm.py              # Orchestrator for all agents
└── build-index.py             # Existing index builder
```

## Resolved Decisions

* **Folder naming:** Deterministic SHA256 hash (`m_{hash[:8]}`) from museum_id
* **Lookup file:** `_museum_lookup.json` in each state folder maps hash → museum_id
* **Agent input:** Complete MuseumContext with ALL state file + cached data
* **Agent output:** Strongly-typed Pydantic models that update STATE file + create subfolders
* **Model selection:** OpenAI-first (GPT-4o-mini for validation, GPT-4o for deep dive); fall back to Claude only if OpenAI is unavailable
* **Pydantic validation:** All LLM outputs must validate against Pydantic models before storage

## Quality & Cost Best Practices

* **Strict JSON control:** Use `response_format` or `json_mode` where available; set `temperature=0` for validation, `<=0.2` for deep dives.
* **Schema-first prompts:** Keep schema definitions close to prompts; reject and retry on validation errors; cap retries at 2 per item.
* **Free-source-first:** Always load cached Wikidata/OSM/Wikipedia before calling LLMs; skip LLM calls when required fields are already populated and non-placeholder.
* **Caching:** Persist all LLM responses under the museum folder (`cache/`) and short-circuit if the same museum_id + model + version is already cached.
* **Batching:** Group requests in batches of 10-20 to reduce overhead; respect provider rate limits with adaptive backoff.
* **Budget enforcement:** Pre-calculate estimated token use per batch; abort batches when projected spend exceeds the remaining budget buffer.
* **PII avoidance:** Do not request or store visitor PII; restrict outputs to public facts and visitor guidance.
* **Human review focus:** Require human checks for GOLD tier outputs and for any record with confidence ≤ 3.

## Data Quality Guardrails

## Data Quality Guardrails

* **Deterministic normalization:** Normalize URLs (https, no trailing slash), lower/slug cities, and trim whitespace before diffs to avoid churn.
* **Coordinate sanity checks:** Reject lat/long outside state bounds; snap obvious city mismatches back to state centroid pending review.
* **Address hygiene:** Prefer structured address parts over free text; drop PO boxes unless explicitly relevant.
* **Source precedence:** Trust hierarchy: website JSON-LD > official site text scrape > Wikidata > Wikipedia > LLM guess; never overwrite higher-trust with lower.
* **Placeholder defense:** Block writes of values matching `['tbd','unknown','n/a','-', 'null']` (case-insensitive) unless human-reviewed.
* **Schema versioning:** Tag every cache file with `schema_version` and `model_version`; invalidate caches on version change.
* **Duplicate detection:** If multiple museums share identical website/phone/address, flag as potential dupes; route to manual review instead of auto-merge.
* **Art-only scoring:** Guardrail: do not set Impressionist/Modern/Historical scores unless `primary_domain = Art`; leave non-art museums unscored per MRD policy.
* **Time-needed whitelist:** Accept only the MRD enumerations; reject free text and map obvious variants ("1 hr" → "Quick stop (<1 hr)").

## Operational Controls & Monitoring

* **Retries & backoff:** Retry once on 429/5xx with jittered backoff; fail fast after 2 total attempts to protect budget.
* **Concurrency caps:** Limit concurrent calls (e.g., 5-10) to avoid rate spikes; expose as CLI flag per provider.
* **Checkpointing:** Persist progress every N museums; allow resume from last checkpoint to avoid re-spend after interruptions.
* **Circuit breakers:** If validation failure rate > 10% or cache hit rate < expected, pause pipeline and surface alert.
* **Telemetry:** Log per-batch tokens, cost estimate, latency, cache hit %, and validation error reasons; emit Prometheus-friendly metrics if possible.
* **Sample QA sets:** Maintain a 20-museum gold set; compare LLM outputs against expected values and fail the run if drift exceeds threshold.
* **Phase targeting:** Allow CLI filters for MRD rollout order (IL/Midwest → Northeast → CA → remaining US → Canada/Mexico/Bermuda) to mirror phased validation checkpoints.
