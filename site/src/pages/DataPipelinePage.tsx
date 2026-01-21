import RoadmapNav from '../components/RoadmapNav'

export default function DataPipelinePage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-20">
      <RoadmapNav />
      {/* Header */}
      <div className="rounded-xl bg-gradient-to-br from-teal-600 to-blue-700 p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold">Data Pipeline Documentation</h1>
        <p className="mt-3 text-xl text-teal-100">
          From raw roster to enriched museum intelligence: Our 10-phase quality assurance process
        </p>
      </div>

      {/* Executive Summary */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Pipeline Overview</h2>
        <p className="text-slate-700 leading-relaxed mb-4">
          MuseumSpark transforms a simple membership roster into a rich, validated dataset through a rigorous 
          10-phase enrichment pipeline. Each phase adds layers of verified information from authoritative sources 
          before any AI/LLM processing begins. This approach ensures data quality, transparency, and auditability.
        </p>
        <div className="grid md:grid-cols-3 gap-4 mt-6">
          <StatCard label="Pipeline Phases" value="10" icon="🔄" />
          <StatCard label="Data Sources" value="6+" icon="📊" />
          <StatCard label="Quality Gates" value="Multiple" icon="✓" />
        </div>
      </div>

      {/* Design Philosophy */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-blue-900">Design Philosophy</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <Principle 
            icon="🎯"
            title="Evidence First"
            description="Gather and validate facts from authoritative sources before applying any AI analysis"
          />
          <Principle 
            icon="🔗"
            title="Source Attribution"
            description="Every field tracks its data source and verification date for full transparency"
          />
          <Principle 
            icon="🔄"
            title="Idempotent Operations"
            description="Re-running phases produces consistent results; safe to execute multiple times"
          />
          <Principle 
            icon="🚦"
            title="Quality Gates"
            description="Each phase validates inputs and outputs; failed validations prevent downstream processing"
          />
        </div>
      </div>

      {/* Pipeline Stages */}
      <div className="space-y-6">
        <h2 className="text-3xl font-bold text-slate-900">Pipeline Stages</h2>

        {/* Ingestion */}
        <PipelineStage
          phase="Ingestion"
          subtitle="Walker Art Center Reciprocal Program Roster"
          status="seed"
          description="The foundation of our dataset: 1,269+ museums from the Walker Art Reciprocal Program membership list."
        >
          <SubSection title="Input Source">
            <p className="text-sm text-slate-700 mb-3">
              <strong>File:</strong> <code className="bg-slate-100 px-2 py-1 rounded text-xs">data/index/walker-reciprocal.csv</code>
            </p>
            <div className="text-sm text-slate-700">
              <strong>Fields Provided:</strong>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li><strong>STATE:</strong> Full state/province name (e.g., "Colorado")</li>
                <li><strong>NAME:</strong> Museum name as listed by Walker</li>
                <li><strong>CITY:</strong> City location</li>
                <li><strong>URL:</strong> Official museum website</li>
              </ul>
            </div>
          </SubSection>

          <SubSection title="Processing Steps">
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-700">
              <li><strong>Validation:</strong> Verify CSV integrity, check required headers, validate URLs</li>
              <li><strong>Normalization:</strong> Convert state names to two-letter codes (Colorado → CO)</li>
              <li><strong>ID Generation:</strong> Create stable museum_id slugs (e.g., <code className="bg-slate-100 px-1">usa-co-denver-denver-art-museum</code>)</li>
              <li><strong>Duplicate Detection:</strong> Match by website URL and (state, name, city) tuple to avoid duplicates</li>
              <li><strong>Stub Creation:</strong> Initialize placeholder records with required schema fields</li>
            </ol>
          </SubSection>

          <SubSection title="Output">
            <div className="text-sm text-slate-700">
              <p className="mb-2"><strong>State Files:</strong> <code className="bg-slate-100 px-2 py-1 rounded text-xs">data/states/&#123;STATE_CODE&#125;.json</code></p>
              <p className="mb-3">Each museum record starts with:</p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>museum_id, museum_name, city, state_province, country</li>
                <li>website (validated URL)</li>
                <li>Placeholder values: street_address="TBD", postal_code="TBD", museum_type="Unknown"</li>
                <li>Timestamps: created_at, updated_at</li>
              </ul>
            </div>
          </SubSection>

          <QualityGate checks={[
            "All required headers present in CSV",
            "No duplicate museum entries (by URL or state+name+city)",
            "Valid URL format for all websites",
            "State names successfully mapped to codes"
          ]} />
        </PipelineStage>

        {/* Phase 0 */}
        <PipelineStage
          phase="Phase 0"
          subtitle="Identity Verification (Google Places API)"
          status="enrichment"
          description="Validates addresses and establishes geographic identity using Google's authoritative location database."
        >
          <SubSection title="Data Sources">
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
              <li><strong>Google Places API:</strong> Official business listings with verified addresses</li>
              <li><strong>Geocoding API:</strong> Coordinate validation and place ID assignment</li>
            </ul>
          </SubSection>

          <SubSection title="Fields Enriched">
            <FieldList fields={[
              { name: "place_id", description: "Google Places ID for canonical reference" },
              { name: "street_address", description: "Verified street address" },
              { name: "postal_code", description: "ZIP/postal code" },
              { name: "latitude, longitude", description: "Geocoded coordinates" },
              { name: "address_source", description: "Set to 'google_places'" },
              { name: "address_last_verified", description: "Timestamp of verification" },
            ]} />
          </SubSection>

          <QualityGate checks={[
            "Valid coordinates within expected geographic bounds",
            "Place ID format validated",
            "Address components complete (no TBD remaining)",
          ]} />
        </PipelineStage>

        {/* Phase 0.5 */}
        <PipelineStage
          phase="Phase 0.5"
          subtitle="Wikidata Structured Data"
          status="enrichment"
          description="Enriches records with structured knowledge from Wikidata, the world's largest open knowledge base."
        >
          <SubSection title="Data Sources">
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
              <li><strong>Wikidata API:</strong> Structured entity data with verified identifiers</li>
              <li><strong>SPARQL Queries:</strong> Precise data extraction using semantic queries</li>
            </ul>
          </SubSection>

          <SubSection title="Fields Enriched">
            <FieldList fields={[
              { name: "website", description: "Canonical website URL (if missing or incorrect)" },
              { name: "alternate_names", description: "Common abbreviations and historical names" },
              { name: "museum_type", description: "Structured classification (Art Museum, History Museum, etc.)" },
              { name: "latitude, longitude", description: "Cross-validation of coordinates" },
              { name: "postal_code", description: "Fill gaps from Phase 0" },
            ]} />
          </SubSection>

          <SubSection title="Matching Strategy">
            <p className="text-sm text-slate-700 mb-2">Museums matched using multiple strategies:</p>
            <ol className="list-decimal list-inside space-y-1 text-sm text-slate-700 ml-4">
              <li>Website URL exact match</li>
              <li>Official name + location (city, state)</li>
              <li>Alternate names + location</li>
              <li>Coordinate proximity (within 100m radius)</li>
            </ol>
          </SubSection>

          <QualityGate checks={[
            "Wikidata entity ID validated (Q-number format)",
            "Cross-reference coordinates within 500m of Phase 0 data",
            "Museum type from controlled vocabulary",
          ]} />
        </PipelineStage>

        {/* Phase 0.7 */}
        <PipelineStage
          phase="Phase 0.7"
          subtitle="Official Website Content Extraction"
          status="enrichment"
          description="Scrapes and parses official museum websites for visiting information and metadata."
        >
          <SubSection title="Extraction Targets">
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-bold text-slate-900 mb-2">Visitor Information</h4>
                <ul className="list-disc list-inside space-y-1 text-slate-700">
                  <li>Hours of operation</li>
                  <li>Admission prices and policies</li>
                  <li>Ticketing/reservation links</li>
                  <li>Accessibility information</li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold text-slate-900 mb-2">Technical Metadata</h4>
                <ul className="list-disc list-inside space-y-1 text-slate-700">
                  <li>Structured data (Schema.org)</li>
                  <li>Social media links</li>
                  <li>Contact information (phone, email)</li>
                  <li>Collections highlights</li>
                </ul>
              </div>
            </div>
          </SubSection>

          <SubSection title="Fields Enriched">
            <FieldList fields={[
              { name: "open_hours_url", description: "Direct link to hours/admission page" },
              { name: "tickets_url", description: "Direct link to ticketing system" },
              { name: "accessibility_url", description: "Accessibility services page" },
              { name: "phone", description: "Public contact number" },
              { name: "reservation_required", description: "Boolean flag for timed entry" },
              { name: "audience_focus", description: "Target audience (General, Family, Academic, etc.)" },
            ]} />
          </SubSection>

          <SubSection title="Technical Approach">
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm">
              <p className="text-slate-700 mb-3">
                <strong>Respectful Scraping:</strong> We follow robots.txt, use polite delays, and cache results.
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-700">
                <li><strong>Rate Limiting:</strong> Maximum 1 request per 2 seconds per domain</li>
                <li><strong>Caching:</strong> 30-day cache to minimize repeat requests</li>
                <li><strong>User Agent:</strong> Identifies as MuseumSpark with contact info</li>
                <li><strong>Timeout:</strong> 10-second timeout to avoid hanging</li>
              </ul>
            </div>
          </SubSection>

          <QualityGate checks={[
            "Website responds with HTTP 200 (or cached)",
            "Extracted URLs validated for correct format",
            "Phone numbers match expected patterns",
          ]} />
        </PipelineStage>

        {/* Phase 1 */}
        <PipelineStage
          phase="Phase 1"
          subtitle="Backbone Fields (Deterministic)"
          status="computation"
          description="Computes classification and logistical fields using deterministic algorithms—no AI involved."
        >
          <SubSection title="Computed Fields">
            <FieldList fields={[
              { name: "city_tier", description: "City size classification: 1=Major (1M+), 2=Medium (100K-1M), 3=Small (<100K)" },
              { name: "nearby_museum_count", description: "Number of other museums in the same city" },
              { name: "estimated_visit_minutes", description: "Heuristic visit duration based on museum type" },
              { name: "city_region", description: "Multi-city region grouping (e.g., 'Bay Area', 'DFW')" },
              { name: "timezone", description: "IANA timezone identifier by coordinates" },
            ]} />
          </SubSection>

          <SubSection title="City Tier Algorithm">
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-sm">
              <p className="text-slate-700 mb-2"><strong>Classification Logic:</strong></p>
              <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4">
                <li><strong>Tier 1 (Major Hub):</strong> Population ≥ 1,000,000 OR major metro area (NYC, LA, Chicago, etc.)</li>
                <li><strong>Tier 2 (Medium City):</strong> Population 100,000 - 999,999</li>
                <li><strong>Tier 3 (Small Town):</strong> Population &lt; 100,000</li>
              </ul>
              <p className="text-slate-600 mt-3 italic">
                Data source: US Census Bureau population estimates (latest available year)
              </p>
            </div>
          </SubSection>

          <QualityGate checks={[
            "City tier assigned (1, 2, or 3)",
            "Nearby museum count ≥ 0",
            "Timezone matches state/coordinates",
          ]} />
        </PipelineStage>

        {/* Phase 1.5 */}
        <PipelineStage
          phase="Phase 1.5"
          subtitle="Wikipedia Enrichment (Art Museums)"
          status="enrichment"
          description="Extracts detailed background information from Wikipedia articles for art museums."
        >
          <SubSection title="Scope">
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm">
              <p className="text-slate-700">
                <strong>⚠️ Art Museums Only:</strong> This phase processes museums where <code className="bg-amber-100 px-1">primary_domain = "Art"</code>. 
                Other museum types skip this phase as it focuses on art collection analysis.
              </p>
            </div>
          </SubSection>

          <SubSection title="Extraction Process">
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-700">
              <li><strong>Article Discovery:</strong> Match museum to Wikipedia article via Wikidata link or search API</li>
              <li><strong>Content Extraction:</strong> Parse article text, infoboxes, and structured data</li>
              <li><strong>Collections Analysis:</strong> Identify mentions of collection strengths (Impressionist, Modern, etc.)</li>
              <li><strong>Historical Context:</strong> Extract founding date, notable curators, major exhibitions</li>
              <li><strong>Evidence Caching:</strong> Store raw article text for Phase 2 LLM judgment</li>
            </ol>
          </SubSection>

          <SubSection title="Cached Data">
            <p className="text-sm text-slate-700 mb-2">Stored in: <code className="bg-slate-100 px-2 py-1 rounded text-xs">data/states/&#123;STATE&#125;/&#123;MUSEUM_ID&#125;/cache/wikipedia.json</code></p>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-700 ml-4">
              <li>Full article text (first 5,000 words)</li>
              <li>Extracted infobox data</li>
              <li>Article metadata (last edited, page ID)</li>
              <li>Collection mentions with context</li>
            </ul>
          </SubSection>

          <QualityGate checks={[
            "Wikipedia article found and validated",
            "Article matches museum (no false positives)",
            "Minimum article length (300 characters)",
          ]} />
        </PipelineStage>

        {/* Phase 1.8 */}
        <PipelineStage
          phase="Phase 1.8"
          subtitle="CSV Database Lookup (IRS 990 Data)"
          status="enrichment"
          description="Cross-references with IRS nonprofit database and other CSV data sources to fill gaps."
        >
          <SubSection title="Data Sources">
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
              <li><strong>IRS 990 Filings:</strong> Nonprofit tax returns with addresses and phone numbers</li>
              <li><strong>IMLS Database:</strong> Institute of Museum and Library Services registry</li>
              <li><strong>Local Datasets:</strong> State-specific museum databases</li>
            </ul>
          </SubSection>

          <SubSection title="Fields Enriched">
            <FieldList fields={[
              { name: "phone", description: "Contact phone (if missing from website scraping)" },
              { name: "museum_type", description: "Refine classification using IRS/IMLS categories" },
              { name: "latitude, longitude", description: "Additional coordinate sources for validation" },
            ]} />
          </SubSection>

          <SubSection title="Matching Strategy">
            <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-sm">
              <p className="text-slate-700 mb-2"><strong>Fuzzy Matching Algorithm:</strong></p>
              <ol className="list-decimal list-inside space-y-1 text-slate-700 ml-4">
                <li>Exact name match + state</li>
                <li>Normalized name (remove "The", "Museum of", etc.) + state</li>
                <li>Levenshtein distance &lt; 3 + city match</li>
                <li>Manual review for edge cases</li>
              </ol>
            </div>
          </SubSection>

          <QualityGate checks={[
            "Match confidence score ≥ 0.80 for automated matches",
            "No conflicting data (e.g., different addresses in same city)",
            "IRS EIN validated if available",
          ]} />
        </PipelineStage>

        {/* Phase 2 */}
        <PipelineStage
          phase="Phase 2"
          subtitle="LLM Scoring (Art Museums Only)"
          status="ai"
          description="AI-powered judgment of collection quality using curated evidence packets. This is the FIRST use of LLM in the pipeline."
        >
          <SubSection title="Eligibility Gate">
            <div className="rounded-lg bg-purple-50 border border-purple-200 p-4 text-sm">
              <p className="text-slate-700 mb-2">
                <strong>🎯 Strict Eligibility Criteria:</strong> Only museums meeting ALL requirements are scored:
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4">
                <li><code className="bg-purple-100 px-1">primary_domain = "Art"</code></li>
                <li>Valid Wikipedia article cached (Phase 1.5)</li>
                <li>Website content available (Phase 0.7)</li>
                <li><code className="bg-purple-100 px-1">is_scoreable = true</code> (set by Phase 0.5)</li>
              </ul>
            </div>
          </SubSection>

          <SubSection title="LLM Model">
            <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-sm">
              <p className="text-slate-700 mb-2"><strong>Current Model:</strong> Claude 3.5 Sonnet (Anthropic)</p>
              <p className="text-slate-700 mb-3">
                <strong>Why Claude?</strong> Superior reasoning for nuanced cultural judgments, strong instruction following, 
                and honest "I don't know" responses when evidence is insufficient.
              </p>
              <p className="text-slate-600 italic">
                Future: May use ensemble of models (Claude + GPT-4) with disagreement flagging.
              </p>
            </div>
          </SubSection>

          <SubSection title="Evidence Packets">
            <p className="text-sm text-slate-700 mb-3">
              The LLM receives <strong>curated evidence</strong>—not raw data dumps—to ensure high-quality judgments:
            </p>
            <div className="space-y-2 text-sm">
              <EvidenceItem 
                source="Wikipedia"
                content="Article text (5,000 words max) with collection descriptions"
              />
              <EvidenceItem 
                source="Museum Website"
                content="Collections page text, about page, exhibition highlights"
              />
              <EvidenceItem 
                source="Wikidata"
                content="Structured facts: founding date, notable works, building architect"
              />
              <EvidenceItem 
                source="Context"
                content="Museum name, location, type for inference"
              />
            </div>
          </SubSection>

          <SubSection title="Scoring Dimensions">
            <FieldList fields={[
              { name: "impressionist_strength", description: "1-5 scale: Impressionist collection quality" },
              { name: "modern_contemporary_strength", description: "1-5 scale: Modern/Contemporary collection quality" },
              { name: "historical_context_score", description: "1-5 scale: Curatorial and educational quality" },
              { name: "reputation", description: "0-3 scale: Cultural significance (0=International, 3=Local)" },
              { name: "collection_tier", description: "0-3 scale: Collection size/depth (0=Flagship, 3=Small)" },
              { name: "confidence", description: "1-5 scale: LLM self-assessed confidence" },
              { name: "score_notes", description: "2-3 sentence explanation of key scores" },
            ]} />
          </SubSection>

          <SubSection title="Judge Role Design">
            <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-sm">
              <p className="text-slate-700 mb-2">
                <strong>🎭 LLM as Judge, Not Researcher:</strong> The key insight that makes this work:
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4">
                <li><strong>No fact-finding:</strong> LLM doesn't search or discover information</li>
                <li><strong>Bounded judgment:</strong> All scores use defined scales with rubrics</li>
                <li><strong>Null when uncertain:</strong> LLM returns null rather than guessing</li>
                <li><strong>Explanation required:</strong> Must justify scores with specific evidence</li>
              </ul>
            </div>
          </SubSection>

          <QualityGate checks={[
            "Scores within defined ranges (1-5 or 0-3)",
            "Confidence score provided (1-5)",
            "score_notes contains specific evidence (not generic statements)",
            "No scores assigned without evidence mention",
          ]} />
        </PipelineStage>

        {/* Phase 2.5 */}
        <PipelineStage
          phase="Phase 2.5"
          subtitle="Content Generation (Premium Art Museums)"
          status="ai"
          description="LLM generates visitor-friendly descriptions and highlights for top museums."
        >
          <SubSection title="Scope">
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm">
              <p className="text-slate-700">
                <strong>📝 Selective Generation:</strong> Content created only for museums with:
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4 mt-2">
                <li><code className="bg-amber-100 px-1">overall_quality_score ≥ 14</code> (Very Good or better)</li>
                <li>Complete scoring data from Phase 2</li>
                <li>OR manually flagged for content generation</li>
              </ul>
            </div>
          </SubSection>

          <SubSection title="Generated Content">
            <FieldList fields={[
              { name: "content_summary", description: "50-100 word concise overview for list views" },
              { name: "content_description", description: "200-300 word detailed description with markdown formatting" },
              { name: "content_highlights", description: "5-8 bullet points of must-see items and key features" },
              { name: "content_model", description: "Model used (e.g., 'claude-3.5-sonnet')" },
              { name: "content_generated_at", description: "ISO timestamp of generation" },
            ]} />
          </SubSection>

          <QualityGate checks={[
            "Summary length 50-100 words",
            "Description length 200-300 words",
            "5-8 highlight points provided",
            "No hallucinated facts (verified against Phase 1.5 Wikipedia cache)",
          ]} />
        </PipelineStage>

        {/* Phase 1.75 */}
        <PipelineStage
          phase="Phase 1.75"
          subtitle="Heuristic Fallback (Non-Art Museums)"
          status="computation"
          description="Provides basic scoring for museums that don't qualify for LLM analysis."
        >
          <SubSection title="Purpose">
            <p className="text-sm text-slate-700 mb-3">
              Museums outside the art domain (Science, History, Specialty) receive heuristic estimates to enable 
              basic filtering and sorting in the browse interface.
            </p>
          </SubSection>

          <SubSection title="Heuristic Rules">
            <div className="space-y-3 text-sm">
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                <h4 className="font-bold text-slate-900 mb-2">Reputation (0-3)</h4>
                <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4">
                  <li>If museum_name contains "National": reputation = 1</li>
                  <li>If city_tier = 1 (major hub): reputation = 2</li>
                  <li>Otherwise: reputation = 3</li>
                </ul>
              </div>
              <div className="rounded-lg bg-slate-50 border border-slate-200 p-3">
                <h4 className="font-bold text-slate-900 mb-2">Collection Tier (0-3)</h4>
                <ul className="list-disc list-inside space-y-1 text-slate-700 ml-4">
                  <li>If museum_type contains "National" or "State": collection_tier = 1</li>
                  <li>If city_tier ≤ 2: collection_tier = 2</li>
                  <li>Otherwise: collection_tier = 3</li>
                </ul>
              </div>
            </div>
          </SubSection>

          <QualityGate checks={[
            "Heuristic scores clearly marked (scored_by = 'heuristic')",
            "No art strength scores assigned (remains null)",
            "confidence = 2 (low-to-medium confidence)",
          ]} />
        </PipelineStage>

        {/* Phase 3 */}
        <PipelineStage
          phase="Phase 3"
          subtitle="Priority Score Calculation (Deterministic)"
          status="computation"
          description="Computes final priority and quality scores using fixed formulas—fully transparent and auditable."
        >
          <SubSection title="Computed Metrics">
            <FieldList fields={[
              { name: "priority_score", description: "Hidden gem ranking: lower score = higher priority (0-25 range)" },
              { name: "overall_quality_score", description: "Absolute quality: higher score = better museum (5-25 range)" },
              { name: "primary_art", description: "Derived primary focus: 'Impressionist' or 'Modern/Contemporary'" },
            ]} />
          </SubSection>

          <SubSection title="Formulas">
            <div className="space-y-4">
              <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-4 text-sm">
                <h4 className="font-bold text-emerald-900 mb-2">Priority Score (Lower = Better)</h4>
                <pre className="bg-white p-3 rounded border border-emerald-300 overflow-x-auto text-xs font-mono">
{`Primary Art = max(Impressionist, Modern/Contemporary)

Priority Score = 
  (6 - Primary Art) × 3
  + (6 - Historical Context) × 2
  + Reputation (0-3)
  + Collection Tier (0-3)
  - Dual Strength Bonus (2 if both ≥ 4)
  - Nearby Cluster Bonus (1 if 3+ museums in city)`}
                </pre>
              </div>

              <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-sm">
                <h4 className="font-bold text-blue-900 mb-2">Quality Score (Higher = Better)</h4>
                <pre className="bg-white p-3 rounded border border-blue-300 overflow-x-auto text-xs font-mono">
{`Quality Score = 
  Primary Art × 3
  + Historical Context × 2
  + (3 - Reputation) × 1
  + (3 - Collection Tier) × 1
  + Dual Strength Bonus (2 if both ≥ 4)`}
                </pre>
              </div>
            </div>
          </SubSection>

          <SubSection title="Score Breakdown Logging">
            <p className="text-sm text-slate-700 mb-2">
              Every score calculation is logged with component breakdown for auditability:
            </p>
            <div className="rounded-lg bg-slate-100 border border-slate-200 p-3 text-xs font-mono overflow-x-auto">
{`{
  "museum_id": "usa-co-denver-denver-art-museum",
  "priority_score": 7.5,
  "overall_quality_score": 22,
  "breakdown": {
    "primary_art_strength": 5,
    "art_component": 3,
    "history_component": 8,
    "reputation_penalty": 0,
    "collection_penalty": 0,
    "dual_strength_bonus": 2,
    "nearby_cluster_bonus": 1
  }
}`}
            </div>
          </SubSection>

          <QualityGate checks={[
            "priority_score and overall_quality_score both assigned",
            "Scores mathematically consistent with input fields",
            "Breakdown components sum correctly",
          ]} />
        </PipelineStage>
      </div>

      {/* Output & Validation */}
      <div className="rounded-lg border border-green-200 bg-green-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-green-900">Final Output & Validation</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-bold text-green-900 mb-2">Master Index Build</h3>
            <p className="text-sm text-slate-700 mb-2">
              After pipeline completion, state files are aggregated into the master index:
            </p>
            <code className="block bg-white px-3 py-2 rounded border border-green-300 text-xs">
              data/index/all-museums.json
            </code>
          </div>

          <div>
            <h3 className="font-bold text-green-900 mb-2">Quality Metrics</h3>
            <div className="grid md:grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-white border border-green-200 p-3">
                <div className="font-semibold text-slate-900">Field Completeness</div>
                <div className="text-slate-600 text-xs mt-1">
                  % of required fields populated per museum
                </div>
              </div>
              <div className="rounded-lg bg-white border border-green-200 p-3">
                <div className="font-semibold text-slate-900">Source Attribution</div>
                <div className="text-slate-600 text-xs mt-1">
                  Every field tracked to authoritative source
                </div>
              </div>
              <div className="rounded-lg bg-white border border-green-200 p-3">
                <div className="font-semibold text-slate-900">Verification Dates</div>
                <div className="text-slate-600 text-xs mt-1">
                  Timestamp of last validation/update
                </div>
              </div>
              <div className="rounded-lg bg-white border border-green-200 p-3">
                <div className="font-semibold text-slate-900">Confidence Scores</div>
                <div className="text-slate-600 text-xs mt-1">
                  LLM self-assessment + data source reliability
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Why This Matters */}
      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-indigo-900">Why This Approach Works</h2>
        <div className="space-y-4 text-sm text-slate-700">
          <div className="flex gap-3">
            <span className="text-2xl flex-shrink-0">🎯</span>
            <div>
              <h3 className="font-bold text-slate-900 mb-1">No Hallucinations</h3>
              <p>LLM only sees verified facts from authoritative sources. Can't invent data because it doesn't do research—only judgment.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="text-2xl flex-shrink-0">🔍</span>
            <div>
              <h3 className="font-bold text-slate-900 mb-1">Full Transparency</h3>
              <p>Every score can be traced to source evidence. Pipeline runs logged with input/output snapshots.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="text-2xl flex-shrink-0">⚡</span>
            <div>
              <h3 className="font-bold text-slate-900 mb-1">Efficient Use of AI</h3>
              <p>LLM only processes ~15% of museums (art museums with sufficient evidence). Rest use deterministic methods.</p>
            </div>
          </div>
          <div className="flex gap-3">
            <span className="text-2xl flex-shrink-0">🔄</span>
            <div>
              <h3 className="font-bold text-slate-900 mb-1">Reproducible & Auditable</h3>
              <p>Deterministic phases produce identical results. LLM temperature = 0 for consistency. All runs logged with timestamps.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Future Enhancements */}
      <div className="rounded-lg bg-slate-100 p-6">
        <h2 className="mb-4 text-xl font-bold text-slate-900">Planned Enhancements</h2>
        <ul className="space-y-2 text-sm text-slate-700">
          <li className="flex items-start gap-2">
            <span className="text-blue-600">▪</span>
            <span><strong>Ensemble Scoring:</strong> Use multiple LLM models with disagreement flagging for human review</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">▪</span>
            <span><strong>Continuous Updates:</strong> Automated monthly pipeline runs to catch museum changes</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">▪</span>
            <span><strong>Crowdsourced Validation:</strong> Allow users to flag outdated info or suggest corrections</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">▪</span>
            <span><strong>Expand Domains:</strong> Extend LLM scoring to Science and History museums</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600">▪</span>
            <span><strong>International Expansion:</strong> Add European and Asian museums</span>
          </li>
        </ul>
      </div>

      {/* Version Info */}
      <div className="rounded-lg bg-slate-100 p-4 text-center text-sm text-slate-600">
        <div><strong>Pipeline Version:</strong> MRD v2.0 (January 2026)</div>
        <div className="mt-1"><strong>Total Phases:</strong> 10 (Ingestion + 9 enrichment phases)</div>
        <div className="mt-1"><strong>Typical Runtime:</strong> 2-4 hours per state (varies by museum count)</div>
      </div>
    </div>
  )
}

// Component Definitions

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="rounded-lg bg-slate-50 border border-slate-200 p-4 text-center">
      <div className="text-3xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-sm text-slate-600">{label}</div>
    </div>
  )
}

function Principle({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="flex gap-3">
      <span className="text-2xl flex-shrink-0">{icon}</span>
      <div>
        <h3 className="font-bold text-blue-900">{title}</h3>
        <p className="text-sm text-slate-700 mt-1">{description}</p>
      </div>
    </div>
  )
}

interface PipelineStageProps {
  phase: string
  subtitle: string
  status: 'seed' | 'enrichment' | 'computation' | 'ai'
  description: string
  children: React.ReactNode
}

function PipelineStage({ phase, subtitle, status, description, children }: PipelineStageProps) {
  const statusColors = {
    seed: { bg: 'bg-slate-50', border: 'border-slate-300', badge: 'bg-slate-200 text-slate-800' },
    enrichment: { bg: 'bg-blue-50', border: 'border-blue-300', badge: 'bg-blue-200 text-blue-900' },
    computation: { bg: 'bg-green-50', border: 'border-green-300', badge: 'bg-green-200 text-green-900' },
    ai: { bg: 'bg-purple-50', border: 'border-purple-300', badge: 'bg-purple-200 text-purple-900' },
  }

  const colors = statusColors[status]

  const statusLabels = {
    seed: 'Initial Data',
    enrichment: 'External Data',
    computation: 'Deterministic',
    ai: 'AI/LLM',
  }

  return (
    <div className={`rounded-lg border-2 ${colors.border} ${colors.bg} p-6 shadow-sm`}>
      <div className="mb-4 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-2xl font-bold text-slate-900">{phase}</h3>
            <span className={`rounded-full px-3 py-1 text-xs font-bold ${colors.badge}`}>
              {statusLabels[status]}
            </span>
          </div>
          <h4 className="text-lg font-semibold text-slate-700">{subtitle}</h4>
        </div>
      </div>
      <p className="text-slate-700 mb-6">{description}</p>
      <div className="space-y-6">
        {children}
      </div>
    </div>
  )
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="font-bold text-slate-900 mb-3">{title}</h4>
      {children}
    </div>
  )
}

function FieldList({ fields }: { fields: Array<{ name: string; description: string }> }) {
  return (
    <ul className="space-y-2">
      {fields.map((field) => (
        <li key={field.name} className="flex gap-2 text-sm">
          <code className="flex-shrink-0 rounded bg-slate-800 px-2 py-1 text-xs font-mono text-white">
            {field.name}
          </code>
          <span className="text-slate-700">{field.description}</span>
        </li>
      ))}
    </ul>
  )
}

function EvidenceItem({ source, content }: { source: string; content: string }) {
  return (
    <div className="rounded-lg bg-white border border-slate-200 p-3 flex gap-3">
      <span className="flex-shrink-0 rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-800">
        {source}
      </span>
      <span className="text-slate-700">{content}</span>
    </div>
  )
}

function QualityGate({ checks }: { checks: string[] }) {
  return (
    <div className="rounded-lg bg-green-50 border border-green-300 p-4 mt-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">✓</span>
        <h4 className="font-bold text-green-900">Quality Gates</h4>
      </div>
      <ul className="space-y-1.5">
        {checks.map((check, idx) => (
          <li key={idx} className="flex gap-2 text-sm text-slate-700">
            <span className="text-green-600 flex-shrink-0">✓</span>
            <span>{check}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
