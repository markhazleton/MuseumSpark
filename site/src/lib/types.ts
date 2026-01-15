export type Museum = {
  museum_id: string
  country: string
  state_province: string
  city: string
  museum_name: string
  alternate_names?: string[] | null
  website?: string | null

  status?: string | null
  museum_type?: string | null
  primary_domain?: string | null
  reputation?: string | null
  collection_tier?: string | null
  time_needed?: string | null
  estimated_visit_minutes?: number | null
  priority_score?: number | null

  street_address?: string | null
  address_line2?: string | null
  postal_code?: string | null
  latitude?: number | null
  longitude?: number | null

  open_hours_url?: string | null
  tickets_url?: string | null
  accessibility_url?: string | null
  reservation_required?: boolean | null

  notes?: string | null
  data_sources?: string[] | null
  confidence?: number | null
}

export type AllMuseumsIndex = {
  generated_at?: string
  total_museums?: number
  museums: Museum[]
}

export type StateFile = {
  state?: string
  state_code?: string
  last_updated?: string
  museums: Museum[]
}

export type ProgressIndex = {
  generated_from: string
  generated_at: string
  total_museums: number
  full: number
  placeholder: number
  full_pct: number
  by_state: Record<string, { total: number; full: number; placeholder: number }>
}
