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
  priority_score?: number | null;
  impressionist_strength?: 1 | 2 | 3 | 4 | 5 | null;
  modern_contemporary_strength?: 1 | 2 | 3 | 4 | 5 | null;
  primary_art?: "Impressionist" | "Modern/Contemporary" | null;
  historical_context_score?: 1 | 2 | 3 | 4 | 5 | null;
  nearby_museum_count?: number | null;
  is_scored?: boolean | null;
  scoring_version?: string | null;
  scored_by?: "assistant" | "manual" | "hybrid" | null;
  score_notes?: string | null;
  score_last_verified?: string | null;

  // NEW: Tour Planning Scores (LLM-generated, 1-10 scale)
  tour_planning_scores?: TourPlanningScores | null;
  summary_short?: string | null;
  summary_long?: string | null;
  collection_highlights?: CollectionHighlight[] | null;
  signature_artists?: string[] | null;
  visitor_tips?: string[] | null;
  best_for?: string | null;

  // Metadata
  data_sources?: string[] | null;
  confidence?: 1 | 2 | 3 | 4 | 5 | null;
  row_notes_internal?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type TourPlanningScores = {
  // Art Movement Scores (1-10)
  contemporary_score?: number | null;
  modern_score?: number | null;
  impressionist_score?: number | null;
  expressionist_score?: number | null;
  classical_score?: number | null;

  // Geographic/Cultural Focus (1-10)
  american_art_score?: number | null;
  european_art_score?: number | null;
  asian_art_score?: number | null;
  african_art_score?: number | null;

  // Medium Scores (1-10)
  painting_score?: number | null;
  sculpture_score?: number | null;
  decorative_arts_score?: number | null;
  photography_score?: number | null;

  // Collection & Experience (1-10)
  collection_depth?: number | null;
  collection_quality?: number | null;
  exhibition_frequency?: number | null;
  family_friendly_score?: number | null;
  educational_value_score?: number | null;
  architecture_score?: number | null;

  // Rationale
  scoring_rationale?: string | null;
};

export type CollectionHighlight = {
  title: string;
  description?: string | null;
  source?: string | null;
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
