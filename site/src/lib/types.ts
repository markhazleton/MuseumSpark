export type Museum = {
  // Identification
  museum_id: string;
  country: string;
  state_province: string;
  city: string;
  museum_name: string;
  alternate_names?: string[] | null;
  website?: string | null;

  // Classification & Status
  status?: "active" | "closed" | "seasonal" | "unknown" | null;
  museum_type?: string | null;
  primary_domain?:
    | "Art"
    | "History"
    | "Science"
    | "Culture"
    | "Specialty"
    | "Mixed"
    | null;
  primary_focus?: string | null;
  topics?: string[] | null;
  audience_focus?:
    | "General"
    | "Family"
    | "Academic"
    | "Children"
    | "Specialist"
    | null;

  // Location & Logistics
  street_address?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  place_id?: string | null;
  address_source?:
    | "official_website"
    | "google_places"
    | "wikipedia"
    | "manual"
    | "unknown"
    | null;
  address_last_verified?: string | null;

  neighborhood?: string | null;
  city_region?: string | null;
  timezone?: string | null;
  city_tier?: 1 | 2 | 3 | null;

  // Visiting Info
  open_hours_url?: string | null;
  tickets_url?: string | null;
  accessibility_url?: string | null;
  reservation_required?: boolean | null;
  best_season?: "Year-round" | "Spring" | "Summer" | "Fall" | "Winter" | null;
  /** v3.1.T: Quick stop ~1-1.25hr | Half day ~2.5-3hr | Most of the Day ~4-5hr | All Day ~6-7hr */
  time_needed?: "Quick stop" | "Half day" | "Most of the Day" | "All Day" | null;
  estimated_visit_minutes?: number | null;

  // Notes
  visit_priority_notes?: string | null;
  parking_notes?: string | null;
  public_transit_notes?: string | null;
  notes?: string | null;

  // ── Scoring & Metrics (MRD v3.1.T - March 2026) ──────────────────────────

  // Reputation & Collection Level (v3.1.T: named strings)
  /** Primary: International / National / Regional / Supra-Local / Local */
  reputation_level?: "International" | "National" | "Regional" | "Supra-Local" | "Local" | null;
  /** Primary: Flagship / Strong / Moderate / Small */
  collection_level?: "Flagship" | "Strong" | "Moderate" | "Small" | null;

  // Legacy integer fields (kept for backwards compatibility with existing data)
  /** @deprecated Use reputation_level. 0=International, 1=National, 2=Regional, 3=Supra-Local, 4=Local */
  reputation?: 0 | 1 | 2 | 3 | 4 | null;
  /** @deprecated Use collection_level. 0=Flagship, 1=Strong, 2=Moderate, 3=Small */
  collection_tier?: 0 | 1 | 2 | 3 | null;

  // Art Collection Strength Scores (0-5)
  /** Impressionist/Post-Impressionist collection strength */
  impressionist_strength?: 0 | 1 | 2 | 3 | 4 | 5 | null;
  /** Modern/Contemporary collection strength */
  modern_contemporary_strength?: 0 | 1 | 2 | 3 | 4 | 5 | null;
  /** Historical Art Traditions strength (v3.1.T). Tradition-based art: non-Western canons, workshop lineage, court art. */
  hat_strength?: 0 | 1 | 2 | 3 | 4 | 5 | null;
  /** Historical Context Score: quality and depth of historical interpretation (5 = Must-See qualifier) */
  historical_context_score?: 0 | 1 | 2 | 3 | 4 | 5 | null;
  /** Exhibitions & Curatorial Authority: programmatic influence beyond permanent holdings */
  eca_score?: 0 | 1 | 2 | 3 | 4 | 5 | null;
  /** Overall depth/authority across all art categories */
  collection_based_strength?: 0 | 1 | 2 | 3 | 4 | 5 | null;

  // Derived Scoring Fields (v3.1.T)
  /** MAX(impressionist_strength, modern_contemporary_strength, hat_strength) */
  collection_based_pas?: number | null;
  /** MAX(collection_based_pas, eca_score) — used in Priority Score formula */
  effective_pas?: number | null;
  /** Primary art focus: strongest of the three collection axes */
  primary_art?: "Impressionist" | "Modern/Contemporary" | "Historical Art Traditions" | null;

  // Computed Scores
  /** Priority Score (lower = higher priority). Floor of 1. Formula: MAX(1, (6-eff_pas)*2 + (6-HC) + rep_penalty + coll_penalty + dual_bonus) */
  priority_score?: number | null;
  /** Behavioral routing tier (deterministic from priority score + qualifiers) */
  outcome_tier?: "Must-See" | "High Priority" | "Regionally Important" | "Detour" | "Consider" | "Background" | null;
  /** Subtype label for Detour/Consider tiers (e.g., Specialized Art Site, Kunsthalle, Locally Historic) */
  additional_labels?: string | null;
  /** Audit provenance: "v3.1.T | 2026-03-01 | NC" (NC=No Change, CH=Changed) */
  audit_tracker?: string | null;
  /** Flagged when historical_context_score = 5 or collection_based_pas = 5 */
  must_see_candidate?: boolean | null;

  nearby_museum_count?: number | null;
  is_scored?: boolean | null;
  is_scoreable?: boolean | null;
  scoring_version?: string | null;
  scored_by?: "assistant" | "manual" | "hybrid" | string | null;
  score_notes?: string | null;
  score_last_verified?: string | null;

  // ── Legacy planner fields from Phase 1.9 ─────────────────────────────────
  /** @deprecated Use priority_score */
  planner_priority_score?: number | null;
  /** @deprecated Use outcome_tier */
  planner_outcome_tier?: string | null;
  /** @deprecated Use additional_labels */
  planner_consider_label?: string | null;
  /** @deprecated Use historical_context_score */
  planner_historical_context?: number | null;
  /** @deprecated Use impressionist_strength */
  planner_impressionist_strength?: number | null;
  /** @deprecated Use modern_contemporary_strength */
  planner_modern_contemporary_strength?: number | null;
  /** @deprecated Use hat_strength */
  planner_traditional_strength?: number | null;
  /** @deprecated Use eca_score */
  planner_exhibition_advantage?: number | null;
  /** @deprecated Use collection_based_pas */
  planner_collection_pas?: number | null;
  /** @deprecated Use effective_pas */
  planner_effective_pas?: number | null;
  /** @deprecated Use reputation_level */
  planner_reputation_level?: string | null;
  /** @deprecated Use collection_level */
  planner_collection_level?: string | null;
  planner_notes?: string | null;
  planner_data_updated_at?: string | null;

  // Enriched Content (LLM-Generated Phase 2.5)
  content_summary?: string | null;
  content_description?: string | null;
  content_highlights?: string[] | null;
  content_generated_at?: string | null;
  content_model?: string | null;
  content_source?: string | null;

  // Legacy (removed field aliases)
  /** @deprecated Use primary_art */
  primary_art_focus?: "Impressionist" | "Modern/Contemporary" | "Historical Art Traditions" | null;
  /** @deprecated Use priority_score */
  overall_quality_score?: number | null;

  // Contact Info
  phone?: string | null;

  // Metadata
  data_sources?: string[] | null;
  confidence?: 1 | 2 | 3 | 4 | 5 | null;
  row_notes_internal?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type AllMuseumsIndex = {
  generated_at?: string;
  total_museums?: number;
  museums: Museum[];
};

export type StateFile = {
  state?: string;
  state_code?: string;
  last_updated?: string;
  museums: Museum[];
};

export type ProgressIndex = {
  generated_from: string;
  generated_at: string;
  total_museums: number;
  full: number;
  placeholder: number;
  full_pct: number;
  by_state: Record<
    string,
    { total: number; full: number; placeholder: number }
  >;
};

/** Outcome tiers in priority order (highest to lowest travel gravity) */
export const OUTCOME_TIERS = [
  "Must-See",
  "High Priority",
  "Regionally Important",
  "Detour",
  "Consider",
  "Background",
] as const;

export type OutcomeTier = typeof OUTCOME_TIERS[number];

/** Reputation levels in priority order */
export const REPUTATION_LEVELS = [
  "International",
  "National",
  "Regional",
  "Supra-Local",
  "Local",
] as const;

export type ReputationLevel = typeof REPUTATION_LEVELS[number];

/** Collection levels in priority order */
export const COLLECTION_LEVELS = [
  "Flagship",
  "Strong",
  "Moderate",
  "Small",
] as const;

export type CollectionLevel = typeof COLLECTION_LEVELS[number];
