import RoadmapNav from '../components/RoadmapNav'

export default function DataModelPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-20">
      <RoadmapNav />
      {/* Header */}
      <div className="rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold">Data Model Documentation</h1>
        <p className="mt-3 text-xl text-indigo-100">
          Comprehensive field reference with data sources and pipeline stages
        </p>
      </div>

      {/* Overview */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Museum Data Model</h2>
        <p className="text-slate-700 leading-relaxed mb-4">
          Each museum record in MuseumSpark contains 50+ fields spanning identification, location, logistics, 
          scoring metrics, and enriched content. This document details every field, its data source, and the 
          pipeline phase that populates it.
        </p>
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
          <h3 className="font-bold text-blue-900 mb-2">Pipeline Phases</h3>
          <ul className="text-sm text-slate-700 space-y-1">
            <li><strong>Phase 0:</strong> Identity verification (Wikidata, website validation)</li>
            <li><strong>Phase 0.5:</strong> Wikidata structured data extraction</li>
            <li><strong>Phase 0.7:</strong> Official website metadata harvesting</li>
            <li><strong>Phase 1:</strong> Backbone data (address, type, classification)</li>
            <li><strong>Phase 1.5:</strong> Wikipedia article extraction</li>
            <li><strong>Phase 2:</strong> LLM scoring (art museums only)</li>
            <li><strong>Phase 2.5:</strong> Content generation (summaries, highlights)</li>
            <li><strong>Phase 3:</strong> Priority score calculation</li>
          </ul>
        </div>
      </div>

      {/* Identification Fields */}
      <FieldSection 
        title="Identification" 
        icon="🏛️"
        description="Core identifiers and naming"
      >
        <Field
          name="museum_id"
          type="string"
          required
          source="Initial Ingestion"
          phase="Seed"
          description="Unique stable identifier in slug format (e.g., 'usa-co-denver-denver-art-museum')"
          example="usa-co-denver-denver-art-museum"
        />
        <Field
          name="museum_name"
          type="string"
          required
          source="Walker Reciprocal List → Wikidata → Official Website"
          phase="Phase 0"
          description="Official museum name"
          example="Denver Art Museum"
        />
        <Field
          name="alternate_names"
          type="string[]"
          source="Wikidata, Wikipedia"
          phase="Phase 0.5"
          description="Common abbreviations or prior names"
          example='["DAM", "Denver Museum of Art"]'
        />
      </FieldSection>

      {/* Location Fields */}
      <FieldSection 
        title="Location & Geography" 
        icon="📍"
        description="Address, coordinates, and regional classification"
      >
        <Field
          name="country"
          type="string"
          required
          source="Walker Reciprocal List"
          phase="Seed"
          description="Country (USA or Canada)"
          example="USA"
        />
        <Field
          name="state_province"
          type="string"
          required
          source="Walker Reciprocal List"
          phase="Seed"
          description="Full state or province name"
          example="Colorado"
        />
        <Field
          name="city"
          type="string"
          required
          source="Walker Reciprocal List → Wikidata"
          phase="Phase 0"
          description="City name"
          example="Denver"
        />
        <Field
          name="city_tier"
          type="number (1-3)"
          source="Census data, heuristic classification"
          phase="Phase 1"
          description="City size classification: 1=Major hub (1M+), 2=Medium city (100K-1M), 3=Small town (<100K)"
          example="1"
        />
        <Field
          name="street_address"
          type="string"
          required
          source="Official Website → Google Places → Wikipedia"
          phase="Phase 0.7, Phase 1"
          description="Primary street address"
          example="100 W 14th Ave Pkwy"
        />
        <Field
          name="address_line2"
          type="string | null"
          source="Official Website, Google Places"
          phase="Phase 1"
          description="Secondary address line (suite, building, etc.)"
          example="null"
        />
        <Field
          name="postal_code"
          type="string"
          required
          source="Official Website → Google Places"
          phase="Phase 0.7, Phase 1"
          description="ZIP or postal code"
          example="80204"
        />
        <Field
          name="latitude"
          type="number"
          source="Google Places API, Wikidata"
          phase="Phase 0.5, Phase 1"
          description="Latitude coordinate for mapping"
          example="39.7372"
        />
        <Field
          name="longitude"
          type="number"
          source="Google Places API, Wikidata"
          phase="Phase 0.5, Phase 1"
          description="Longitude coordinate for mapping"
          example="-104.9893"
        />
        <Field
          name="place_id"
          type="string | null"
          source="Google Places API"
          phase="Phase 1"
          description="Google Places ID for reverse lookup"
          example="ChIJXXXXXXXXXXX"
        />
        <Field
          name="neighborhood"
          type="string | null"
          source="Wikidata, local knowledge"
          phase="Phase 1"
          description="Neighborhood or district within city"
          example="Civic Center"
        />
        <Field
          name="city_region"
          type="string | null"
          source="Heuristic classification"
          phase="Phase 1"
          description="Multi-city region for grouping"
          example="Denver Metro"
        />
        <Field
          name="timezone"
          type="string"
          source="Timezone lookup by coordinates"
          phase="Phase 1"
          description="IANA timezone identifier"
          example="America/Denver"
        />
        <Field
          name="address_source"
          type="enum"
          source="Pipeline metadata"
          phase="Phase 0.7, Phase 1"
          description="Source of address information: official_website, google_places, wikipedia, manual, unknown"
          example="official_website"
        />
        <Field
          name="address_last_verified"
          type="date"
          source="Pipeline metadata"
          phase="Phase 1"
          description="ISO date of last address verification"
          example="2026-01-15"
        />
      </FieldSection>

      {/* Classification Fields */}
      <FieldSection 
        title="Classification & Type" 
        icon="🎨"
        description="Museum categorization and focus areas"
      >
        <Field
          name="museum_type"
          type="string"
          required
          source="Wikidata, IMLS, website analysis"
          phase="Phase 0.5, Phase 1"
          description="Primary museum classification"
          example="Art Museum"
        />
        <Field
          name="primary_domain"
          type="enum"
          source="Heuristic from museum_type and topics"
          phase="Phase 1"
          description="High-level domain: Art, History, Science, Culture, Specialty, Mixed"
          example="Art"
        />
        <Field
          name="topics"
          type="string[]"
          source="Wikidata, Wikipedia parsing"
          phase="Phase 1.5"
          description="Specific topics or subject areas"
          example='["American Art", "Modern Art", "Native American Art"]'
        />
        <Field
          name="audience_focus"
          type="enum"
          source="Website analysis, Wikidata"
          phase="Phase 0.7"
          description="Primary audience: General, Family, Academic, Children, Specialist"
          example="General"
        />
        <Field
          name="status"
          type="enum"
          source="Website check, Wikidata"
          phase="Phase 0, Phase 0.7"
          description="Operating status: active, closed, seasonal, unknown"
          example="active"
        />
      </FieldSection>

      {/* Contact & Web Fields */}
      <FieldSection 
        title="Contact & Web Presence" 
        icon="🌐"
        description="Website URLs and contact information"
      >
        <Field
          name="website"
          type="string (URL)"
          required
          source="Walker Reciprocal List → Wikidata → Manual verification"
          phase="Seed, Phase 0"
          description="Official museum website URL"
          example="https://denverartmuseum.org"
        />
        <Field
          name="phone"
          type="string | null"
          source="Official Website, Google Places"
          phase="Phase 0.7, Phase 1"
          description="Public phone number"
          example="(720) 865-5000"
        />
        <Field
          name="open_hours_url"
          type="string (URL) | null"
          source="Website scraping"
          phase="Phase 0.7"
          description="Direct link to hours/admission page"
          example="https://denverartmuseum.org/visit"
        />
        <Field
          name="tickets_url"
          type="string (URL) | null"
          source="Website scraping"
          phase="Phase 0.7"
          description="Direct link to tickets/booking page"
          example="https://tickets.denverartmuseum.org"
        />
        <Field
          name="accessibility_url"
          type="string (URL) | null"
          source="Website scraping"
          phase="Phase 0.7"
          description="Link to accessibility information"
          example="https://denverartmuseum.org/accessibility"
        />
      </FieldSection>

      {/* Visiting Information */}
      <FieldSection 
        title="Visiting Logistics" 
        icon="🎫"
        description="Planning information for visitors"
      >
        <Field
          name="time_needed"
          type="enum"
          source="LLM inference from collection size"
          phase="Phase 2"
          description="Recommended visit duration: Quick stop (< 2hr), Half day (2-4hr), Full day (4+ hr)"
          example="Full day"
        />
        <Field
          name="estimated_visit_minutes"
          type="number | null"
          source="Heuristic from collection_tier and exhibits"
          phase="Phase 1"
          description="More precise visit duration estimate"
          example="240"
        />
        <Field
          name="reservation_required"
          type="boolean | null"
          source="Website scraping"
          phase="Phase 0.7"
          description="Whether timed entry or reservations required"
          example="false"
        />
        <Field
          name="best_season"
          type="enum"
          source="Manual input, regional knowledge"
          phase="Manual"
          description="Optimal season to visit: Year-round, Spring, Summer, Fall, Winter"
          example="Year-round"
        />
        <Field
          name="parking_notes"
          type="string | null"
          source="Website scraping, manual input"
          phase="Phase 0.7, Manual"
          description="Parking availability and costs"
          example="On-site parking $15/day, street parking limited"
        />
        <Field
          name="public_transit_notes"
          type="string | null"
          source="Website scraping, manual input"
          phase="Phase 0.7, Manual"
          description="Public transit access details"
          example="RTD Light Rail: Theatre District/Convention Center Station (5 min walk)"
        />
        <Field
          name="visit_priority_notes"
          type="string | null"
          source="Manual curation"
          phase="Manual"
          description="Travel-specific notes and tips"
          example="Visit Wednesday evenings for free admission after 5pm"
        />
      </FieldSection>

      {/* Scoring Fields - Art Museums Only */}
      <FieldSection 
        title="Scoring Metrics (Art Museums)" 
        icon="⭐"
        description="LLM-assigned and computed scores"
      >
        <Field
          name="is_scoreable"
          type="boolean | null"
          source="Phase 0 eligibility check"
          phase="Phase 0.5"
          description="Whether museum qualifies for scoring (art museums with sufficient evidence)"
          example="true"
        />
        <Field
          name="impressionist_strength"
          type="number (1-5) | null"
          source="LLM judgment (Claude 3.5 Sonnet)"
          phase="Phase 2"
          description="Impressionist collection strength: 1=None, 2=Minor, 3=Moderate, 4=Strong, 5=Flagship"
          example="4"
        />
        <Field
          name="modern_contemporary_strength"
          type="number (1-5) | null"
          source="LLM judgment (Claude 3.5 Sonnet)"
          phase="Phase 2"
          description="Modern/Contemporary collection strength: 1=None, 2=Minor, 3=Moderate, 4=Strong, 5=Flagship"
          example="5"
        />
        <Field
          name="historical_context_score"
          type="number (1-5) | null"
          source="LLM judgment (Claude 3.5 Sonnet)"
          phase="Phase 2"
          description="Curatorial and educational quality: 1=Poor, 2=Minimal, 3=Moderate, 4=Strong, 5=Outstanding"
          example="5"
        />
        <Field
          name="reputation"
          type="number (0-3) | null"
          source="LLM judgment (Claude 3.5 Sonnet)"
          phase="Phase 2"
          description="Cultural significance: 0=International, 1=National, 2=Regional, 3=Local"
          example="0"
        />
        <Field
          name="collection_tier"
          type="number (0-3) | null"
          source="LLM judgment (Claude 3.5 Sonnet)"
          phase="Phase 2"
          description="Collection size/depth: 0=Flagship, 1=Strong, 2=Moderate, 3=Small"
          example="0"
        />
        <Field
          name="primary_art"
          type="enum"
          source="Derived from max(impressionist_strength, modern_contemporary_strength)"
          phase="Phase 2"
          description="Primary collection focus: Impressionist or Modern/Contemporary"
          example="Modern/Contemporary"
        />
        <Field
          name="nearby_museum_count"
          type="number | null"
          source="Computed from city clustering"
          phase="Phase 1"
          description="Number of other museums in the same city"
          example="8"
        />
        <Field
          name="priority_score"
          type="number | null"
          source="Deterministic formula (MRD Section 5)"
          phase="Phase 3"
          description="Hidden gem score: lower = higher priority. Range typically 0-25"
          example="7.5"
        />
        <Field
          name="overall_quality_score"
          type="number | null"
          source="Deterministic formula (inverted priority components)"
          phase="Phase 3"
          description="Absolute quality score: higher = better. Range typically 5-25"
          example="22"
        />
        <Field
          name="confidence"
          type="number (1-5) | null"
          source="LLM self-assessment"
          phase="Phase 2"
          description="LLM confidence in scoring: 1=Low, 5=Very High"
          example="5"
        />
        <Field
          name="score_notes"
          type="string | null"
          source="LLM explanation"
          phase="Phase 2"
          description="2-3 sentence explanation of key scoring decisions"
          example="World-class modern/contemporary collection with works by Pollock, Rothko, Warhol. Strong Impressionist holdings including Monet and Renoir. Exceptional curatorial quality and educational programming."
        />
        <Field
          name="scoring_version"
          type="string | null"
          source="Pipeline metadata"
          phase="Phase 2"
          description="Version of scoring algorithm used"
          example="MRD-v2.0"
        />
        <Field
          name="scored_by"
          type="enum"
          source="Pipeline metadata"
          phase="Phase 2"
          description="Scoring method: assistant (LLM), manual, hybrid, gpt-5.2"
          example="assistant"
        />
        <Field
          name="score_last_verified"
          type="date"
          source="Pipeline metadata"
          phase="Phase 2"
          description="ISO date of last score verification"
          example="2026-01-15"
        />
      </FieldSection>

      {/* Enriched Content */}
      <FieldSection 
        title="Enriched Content (LLM-Generated)" 
        icon="📝"
        description="AI-generated summaries and highlights"
      >
        <Field
          name="content_summary"
          type="string | null"
          source="LLM generation (Claude 3.5 Sonnet)"
          phase="Phase 2.5"
          description="50-100 word concise overview for listings"
          example="The Denver Art Museum features world-class collections spanning ancient to contemporary art..."
        />
        <Field
          name="content_description"
          type="string | null"
          source="LLM generation (Claude 3.5 Sonnet)"
          phase="Phase 2.5"
          description="200-300 word detailed description with markdown formatting"
          example="## Overview\nThe Denver Art Museum (DAM) is one of the largest art museums between..."
        />
        <Field
          name="content_highlights"
          type="string[]"
          source="LLM generation (Claude 3.5 Sonnet)"
          phase="Phase 2.5"
          description="5-8 bullet points of key features and must-see items"
          example='["American Indian Art collection", "European paintings", "Hamilton Building by Daniel Libeskind"]'
        />
        <Field
          name="content_generated_at"
          type="datetime"
          source="Pipeline metadata"
          phase="Phase 2.5"
          description="ISO 8601 timestamp of content generation"
          example="2026-01-15T14:30:00Z"
        />
        <Field
          name="content_model"
          type="string | null"
          source="Pipeline metadata"
          phase="Phase 2.5"
          description="Model used for content generation"
          example="claude-3.5-sonnet"
        />
        <Field
          name="content_source"
          type="string | null"
          source="Pipeline metadata"
          phase="Phase 2.5"
          description="Source material used for content generation"
          example="wikipedia,official_website"
        />
      </FieldSection>

      {/* Metadata Fields */}
      <FieldSection 
        title="Metadata & Provenance" 
        icon="🔍"
        description="Data quality and tracking fields"
      >
        <Field
          name="data_sources"
          type="string[]"
          source="Pipeline tracking"
          phase="All phases"
          description="List of data sources used for this record"
          example='["walker_reciprocal", "wikidata", "wikipedia", "official_website"]'
        />
        <Field
          name="notes"
          type="string | null"
          source="Manual input, pipeline notes"
          phase="Any"
          description="General notes, highlights, or additional context"
          example="Recently renovated wing featuring Indigenous art"
        />
        <Field
          name="row_notes_internal"
          type="string | null"
          source="Pipeline/curator notes"
          phase="Any"
          description="Internal maintenance notes (not displayed to users)"
          example="Need to verify collection tier post-expansion"
        />
        <Field
          name="created_at"
          type="date"
          source="Initial ingestion timestamp"
          phase="Seed"
          description="ISO date when record was first created"
          example="2025-12-01"
        />
        <Field
          name="updated_at"
          type="date"
          source="Last modification timestamp"
          phase="Any update"
          description="ISO date of last record modification"
          example="2026-01-15"
        />
      </FieldSection>

      {/* Data Sources Summary */}
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-indigo-900">Primary Data Sources</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <DataSource
            name="Walker Reciprocal Program"
            description="Seed list of 1,269+ museums with basic info (name, city, website)"
            fields="museum_name, city, state, website"
          />
          <DataSource
            name="Wikidata"
            description="Structured knowledge base for coordinates, museum types, alternate names"
            fields="latitude, longitude, museum_type, alternate_names"
          />
          <DataSource
            name="Wikipedia"
            description="Article text for background, history, and collection descriptions"
            fields="topics, historical context evidence"
          />
          <DataSource
            name="Official Museum Websites"
            description="Primary source for addresses, hours, contact info, accessibility"
            fields="street_address, phone, open_hours_url, tickets_url"
          />
          <DataSource
            name="Google Places API"
            description="Geocoding, address validation, place IDs"
            fields="latitude, longitude, place_id, postal_code"
          />
          <DataSource
            name="LLM Analysis (Claude)"
            description="Scoring judgment and content generation for art museums"
            fields="All scoring fields, content_summary, content_highlights"
          />
        </div>
      </div>

      {/* Field Status Legend */}
      <div className="rounded-lg bg-slate-100 p-6">
        <h2 className="mb-4 text-xl font-bold text-slate-900">Field Status Legend</h2>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="inline-block rounded bg-red-100 px-2 py-1 text-xs font-bold text-red-800">REQUIRED</span>
            <p className="mt-1 text-slate-600">Must be present, validated during ingestion</p>
          </div>
          <div>
            <span className="inline-block rounded bg-blue-100 px-2 py-1 text-xs font-bold text-blue-800">OPTIONAL</span>
            <p className="mt-1 text-slate-600">May be null, populated when available</p>
          </div>
          <div>
            <span className="inline-block rounded bg-purple-100 px-2 py-1 text-xs font-bold text-purple-800">COMPUTED</span>
            <p className="mt-1 text-slate-600">Derived from other fields, not stored separately</p>
          </div>
        </div>
      </div>
    </div>
  )
}

interface FieldSectionProps {
  title: string
  icon: string
  description: string
  children: React.ReactNode
}

function FieldSection({ title, icon, description, children }: FieldSectionProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center gap-3">
        <span className="text-3xl">{icon}</span>
        <div>
          <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
          <p className="text-sm text-slate-600">{description}</p>
        </div>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  )
}

interface FieldProps {
  name: string
  type: string
  required?: boolean
  source: string
  phase: string
  description: string
  example: string
}

function Field({ name, type, required, source, phase, description, example }: FieldProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="mb-2 flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <code className="rounded bg-slate-800 px-2 py-1 text-sm font-mono text-white">{name}</code>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">{type}</span>
            {required && <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-bold text-red-800">REQUIRED</span>}
          </div>
        </div>
      </div>
      <p className="mb-3 text-sm text-slate-700">{description}</p>
      <div className="grid md:grid-cols-2 gap-3 text-xs">
        <div>
          <span className="font-semibold text-slate-600">Source:</span>
          <div className="text-slate-700 mt-1">{source}</div>
        </div>
        <div>
          <span className="font-semibold text-slate-600">Phase:</span>
          <div className="text-slate-700 mt-1">{phase}</div>
        </div>
      </div>
      <div className="mt-3 rounded bg-slate-100 p-2 text-xs">
        <span className="font-semibold text-slate-600">Example:</span>
        <code className="ml-2 text-slate-800">{example}</code>
      </div>
    </div>
  )
}

interface DataSourceProps {
  name: string
  description: string
  fields: string
}

function DataSource({ name, description, fields }: DataSourceProps) {
  return (
    <div className="rounded-lg bg-white border border-indigo-200 p-4">
      <h3 className="font-bold text-indigo-900 mb-2">{name}</h3>
      <p className="text-sm text-slate-700 mb-3">{description}</p>
      <div className="text-xs text-slate-600">
        <span className="font-semibold">Key Fields:</span>
        <div className="mt-1 text-slate-700">{fields}</div>
      </div>
    </div>
  )
}
