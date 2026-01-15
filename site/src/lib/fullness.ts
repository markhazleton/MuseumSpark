import type { Museum } from './types'

const PLACEHOLDER_STRINGS = new Set(['', 'tbd', 'unknown', 'n/a'])
function isMissing(value: unknown): boolean {
  if (value === null || value === undefined) return true
  if (Array.isArray(value)) return value.length === 0
  if (typeof value === 'string') return PLACEHOLDER_STRINGS.has(value.trim().toLowerCase())
  return false
}

function hasTimeEstimate(m: Museum): boolean {
  return !isMissing(m.time_needed) || !isMissing(m.estimated_visit_minutes)
}

function hasDataSources(m: Museum): boolean {
  return Array.isArray(m.data_sources) && m.data_sources.length > 0
}

function hasConfidence(m: Museum): boolean {
  const c = m.confidence
  if (typeof c !== 'number') return false
  if (!Number.isInteger(c)) return false
  return c >= 1 && c <= 5
}

const PHASE1_SCHEMA_REQUIRED_FIELDS: Array<keyof Museum> = [
  'museum_id',
  'country',
  'state_province',
  'city',
  'museum_name',
  'website',
  'museum_type',
  'street_address',
  'postal_code',
]

const PHASE1_ENRICHMENT_CORE_FIELDS: Array<keyof Museum> = [
  'primary_domain',
  'status',
  'reputation',
  'collection_tier',
  'notes',
  'data_sources',
  'confidence',
]

export function isFullRecord(m: Museum): boolean {
  for (const f of PHASE1_SCHEMA_REQUIRED_FIELDS) {
    if (isMissing(m[f])) return false
  }

  for (const f of PHASE1_ENRICHMENT_CORE_FIELDS) {
    if (f === 'data_sources') {
      if (!hasDataSources(m)) return false
      continue
    }
    if (f === 'confidence') {
      if (!hasConfidence(m)) return false
      continue
    }
    if (isMissing(m[f])) return false
  }

  if (!hasTimeEstimate(m)) return false

  return true
}
