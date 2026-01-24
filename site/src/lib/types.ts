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
  time_needed?: "Quick stop" | "Half day" | "Full day" | null;
  estimated_visit_minutes?: number | null;

  // Notes
  visit_priority_notes?: string | null;
  parking_notes?: string | null;
  public_transit_notes?: string | null;
  notes?: string | null;

  // Scoring & Metrics (Art Museums)
  reputation?: 0 | 1 | 2 | 3 | null; // 0=International, 1=National, 2=Regional, 3=Local
  collection_tier?: 0 | 1 | 2 | 3 | null; // 0=Flagship, 1=Strong, 2=Moderate, 3=Small
  priority_score?: number | null; // Hidden gem score (lower=better)
  overall_quality_score?: number | null; // Best museum score (higher=better)
  impressionist_strength?: 1 | 2 | 3 | 4 | 5 | null;
  modern_contemporary_strength?: 1 | 2 | 3 | 4 | 5 | null;
  primary_art?: "Impressionist" | "Modern/Contemporary" | null;
  historical_context_score?: 1 | 2 | 3 | 4 | 5 | null;
  nearby_museum_count?: number | null;
  is_scored?: boolean | null;
  is_scoreable?: boolean | null;
  scoring_version?: string | null;
  scored_by?: "assistant" | "manual" | "hybrid" | "gpt-5.2" | null;
  score_notes?: string | null;
  score_last_verified?: string | null;

  // Product Owner/Planner Metadata (Phase 1.9)
  planner_priority_score?: number | null;
  planner_outcome_tier?: string | null;
  planner_consider_label?: string | null;
  planner_historical_context?: number | null;
  planner_impressionist_strength?: number | null;
  planner_modern_contemporary_strength?: number | null;
  planner_traditional_strength?: number | null;
  planner_exhibition_advantage?: number | null;
  planner_collection_pas?: number | null;
  planner_effective_pas?: number | null;
  planner_reputation_level?: string | null;
  planner_collection_level?: string | null;
  planner_notes?: string | null;
  planner_data_updated_at?: string | null;

  // Enriched Content (LLM-Generated Phase 2.5)
  content_summary?: string | null; // 50-100 words
  content_description?: string | null; // 200-300 words with markdown
  content_highlights?: string[] | null; // 5-8 bullet points
  content_generated_at?: string | null;
  content_model?: string | null;
  content_source?: string | null;

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
