import RoadmapNav from '../components/RoadmapNav'

export default function ScoringMethodologyPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-20">
      <RoadmapNav />
      {/* Header */}
      <div className="rounded-xl bg-gradient-to-br from-purple-600 to-blue-700 p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold">Scoring Methodology</h1>
        <p className="mt-3 text-xl text-purple-100">
          Transparent, data-driven museum quality assessment
        </p>
      </div>

      {/* Overview */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Overview</h2>
        <p className="text-slate-700 leading-relaxed">
          MuseumSpark uses a multi-dimensional scoring system to help art enthusiasts discover and prioritize museums. 
          Our methodology combines LLM-powered analysis of curated evidence with deterministic calculations to produce 
          two key metrics: <strong>Priority Score</strong> (finding hidden gems) and <strong>Quality Score</strong> (identifying 
          world-class museums).
        </p>
      </div>

      {/* Two-Phase Scoring System */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-blue-900">Two-Phase Scoring System</h2>
        <div className="space-y-4">
          <div className="rounded-lg bg-white p-4 border border-blue-100">
            <h3 className="font-bold text-blue-800 mb-2">Phase 1: LLM Judgment (Phase 2 Pipeline)</h3>
            <p className="text-slate-700 text-sm">
              An AI model (currently Claude 3.5 Sonnet) analyzes curated evidence packets including Wikipedia articles, 
              museum websites, and Wikidata to assign bounded scores for collection strength and reputation.
            </p>
          </div>
          <div className="rounded-lg bg-white p-4 border border-blue-100">
            <h3 className="font-bold text-blue-800 mb-2">Phase 2: Deterministic Calculation (Phase 3 Pipeline)</h3>
            <p className="text-slate-700 text-sm">
              Using the LLM-assigned base scores, we compute priority and quality scores using fixed mathematical formulas. 
              This ensures consistency and auditability.
            </p>
          </div>
        </div>
      </div>

      {/* Core Scoring Fields */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-6 text-2xl font-bold text-slate-900">Core Scoring Fields</h2>
        <p className="mb-6 text-slate-600">
          All art museums are scored on five dimensions. These scores are assigned by AI after analyzing curated evidence.
        </p>

        <div className="space-y-6">
          {/* Impressionist Strength */}
          <ScoreRubric
            title="Impressionist Strength"
            scale="1-5"
            description="Measures the depth and quality of Impressionist and Post-Impressionist collections (Monet, Renoir, Degas, Van Gogh, Cézanne, etc.)"
            rubric={[
              { value: 5, label: "Flagship", description: "World-class holdings with dedicated galleries, multiple masterworks, comprehensive representation" },
              { value: 4, label: "Strong", description: "Significant collection with several important works, depth in multiple artists" },
              { value: 3, label: "Moderate", description: "Notable Impressionist works, but limited breadth or depth" },
              { value: 2, label: "Minor", description: "Few Impressionist pieces, no dedicated focus or gallery space" },
              { value: 1, label: "None", description: "No significant Impressionist holdings" },
            ]}
          />

          {/* Modern/Contemporary Strength */}
          <ScoreRubric
            title="Modern/Contemporary Strength"
            scale="1-5"
            description="Measures the depth and quality of 20th-21st century art collections (Abstract Expressionism, Pop Art, Contemporary art)"
            rubric={[
              { value: 5, label: "Flagship", description: "Major holdings spanning multiple movements, influential artists, cutting-edge contemporary works" },
              { value: 4, label: "Strong", description: "Significant modern/contemporary collection with depth in key movements" },
              { value: 3, label: "Moderate", description: "Solid representation of modern art but limited contemporary depth" },
              { value: 2, label: "Minor", description: "Few modern/contemporary works, not a collection focus" },
              { value: 1, label: "None", description: "Little to no modern or contemporary art" },
            ]}
          />

          {/* Historical Context Score */}
          <ScoreRubric
            title="Historical Context Score"
            scale="1-5"
            description="Evaluates curatorial quality, educational programming, and interpretive materials"
            rubric={[
              { value: 5, label: "Outstanding", description: "Exceptional narrative flow, rich educational materials, chronological organization, deep interpretive content" },
              { value: 4, label: "Strong", description: "Clear organization, informative labels, good educational programming" },
              { value: 3, label: "Moderate", description: "Inconsistent context, surface-level interpretation in some areas" },
              { value: 2, label: "Minimal", description: "Basic labels only, limited educational depth" },
              { value: 1, label: "Poor", description: "Little to no historical framing or interpretive materials" },
            ]}
          />

          {/* Reputation */}
          <ScoreRubric
            title="Reputation"
            scale="0-3"
            description="Cultural significance and recognition level (lower number = higher reputation)"
            rubric={[
              { value: 0, label: "International", description: "World-renowned institution (MoMA, Met, Art Institute of Chicago, Getty)" },
              { value: 1, label: "National", description: "Major US destination, widely recognized across the country" },
              { value: 2, label: "Regional", description: "Well-known within a multi-state region, draws regional visitors" },
              { value: 3, label: "Local", description: "Primarily serves local community, limited regional draw" },
            ]}
          />

          {/* Collection Tier */}
          <ScoreRubric
            title="Collection Tier"
            scale="0-3"
            description="Overall collection size, depth, and breadth (lower number = larger collection)"
            rubric={[
              { value: 0, label: "Flagship", description: "Encyclopedic collection, world-class holdings across multiple periods and cultures" },
              { value: 1, label: "Strong", description: "Significant depth in multiple areas, substantial permanent collection" },
              { value: 2, label: "Moderate", description: "Respectable collection with clear focus, limited but quality holdings" },
              { value: 3, label: "Small", description: "Small or highly focused collection, niche specialty" },
            ]}
          />
        </div>
      </div>

      {/* Priority Score Formula */}
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-emerald-900">Priority Score Formula</h2>
        <p className="mb-4 text-slate-700">
          The <strong>Priority Score</strong> identifies "hidden gems" — museums with exceptional collections relative to their reputation. 
          Lower scores indicate higher priority for art enthusiasts seeking underrated destinations.
        </p>

        <div className="rounded-lg bg-white p-6 border border-emerald-200 font-mono text-sm overflow-x-auto">
          <div className="space-y-2">
            <div><span className="text-slate-600">Primary Art Strength =</span> <span className="text-blue-600">max(Impressionist, Modern/Contemporary)</span></div>
            <div className="mt-4 pt-4 border-t border-slate-200">
              <div className="text-slate-600 mb-2">Priority Score =</div>
              <div className="ml-4 space-y-1 text-slate-800">
                <div>(6 - Primary Art Strength) × 3</div>
                <div>+ (6 - Historical Context) × 2</div>
                <div>+ Reputation (0-3)</div>
                <div>+ Collection Tier (0-3)</div>
                <div>- Dual Strength Bonus (2 if both ≥ 4)</div>
                <div>- Nearby Cluster Bonus (1 if 3+ museums in city)</div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <h3 className="font-bold text-emerald-900">Component Weights</h3>
          <ul className="space-y-2 text-sm text-slate-700">
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">×3</span>
              <span><strong>Art Strength:</strong> Most important factor — museums with stronger collections score lower (higher priority)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">×2</span>
              <span><strong>Historical Context:</strong> Educational value and curatorial quality matters</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">+</span>
              <span><strong>Reputation Penalty:</strong> Lower reputation (local/regional) = lower score = higher priority</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">+</span>
              <span><strong>Collection Penalty:</strong> Smaller collections add to priority score</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">-2</span>
              <span><strong>Dual Strength Bonus:</strong> Museums strong in both Impressionist AND Modern/Contemporary get priority boost</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-600 font-bold">-1</span>
              <span><strong>Cluster Bonus:</strong> Museums in cities with many options get slight priority boost</span>
            </li>
          </ul>
        </div>

        <div className="mt-6 rounded-lg bg-emerald-100 border border-emerald-200 p-4">
          <h3 className="font-bold text-emerald-900 mb-2">Interpretation</h3>
          <ul className="space-y-1 text-sm text-slate-700">
            <li><strong>Score 0-5:</strong> Must-visit hidden gems — exceptional quality, lower recognition</li>
            <li><strong>Score 6-10:</strong> High-priority destinations with strong collections</li>
            <li><strong>Score 11-15:</strong> Worthwhile museums, plan if in the area</li>
            <li><strong>Score 16+:</strong> Known major museums or smaller regional institutions</li>
          </ul>
        </div>
      </div>

      {/* Quality Score Formula */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-blue-900">Overall Quality Score Formula</h2>
        <p className="mb-4 text-slate-700">
          The <strong>Quality Score</strong> ranks museums by absolute excellence. Higher scores indicate world-class collections 
          and curatorial standards. This metric helps identify the best museums regardless of reputation.
        </p>

        <div className="rounded-lg bg-white p-6 border border-blue-200 font-mono text-sm overflow-x-auto">
          <div className="space-y-2">
            <div><span className="text-slate-600">Primary Art Strength =</span> <span className="text-blue-600">max(Impressionist, Modern/Contemporary)</span></div>
            <div className="mt-4 pt-4 border-t border-slate-200">
              <div className="text-slate-600 mb-2">Quality Score =</div>
              <div className="ml-4 space-y-1 text-slate-800">
                <div>Primary Art Strength × 3</div>
                <div>+ Historical Context × 2</div>
                <div>+ (3 - Reputation) × 1</div>
                <div>+ (3 - Collection Tier) × 1</div>
                <div>+ Dual Strength Bonus (2 if both ≥ 4)</div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-blue-100 border border-blue-200 p-4">
          <h3 className="font-bold text-blue-900 mb-2">Interpretation</h3>
          <ul className="space-y-1 text-sm text-slate-700">
            <li><strong>Score 20+:</strong> World-class institutions (top-tier internationally)</li>
            <li><strong>Score 17-19:</strong> Excellent museums with outstanding collections</li>
            <li><strong>Score 14-16:</strong> Very good museums, strong regional destinations</li>
            <li><strong>Score 11-13:</strong> Good museums worth visiting</li>
            <li><strong>Score &lt;11:</strong> Modest or developing collections</li>
          </ul>
        </div>
      </div>

      {/* Design Principles */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Design Principles</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">🎯 Evidence-Based</h3>
            <p className="text-sm text-slate-700">
              LLM judges only see curated evidence from reliable sources (Wikipedia, museum websites, Wikidata). No hallucination-prone research tasks.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">🔢 Deterministic Calculation</h3>
            <p className="text-sm text-slate-700">
              Final scores computed using fixed formulas. Same inputs always produce same outputs. Fully auditable and reproducible.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">✅ Null Handling</h3>
            <p className="text-sm text-slate-700">
              If evidence is insufficient, scores remain null rather than guessed. Non-art museums are not scored.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">🔄 Transparent & Auditable</h3>
            <p className="text-sm text-slate-700">
              Score breakdowns logged with source references. Every calculation step is documented and verifiable.
            </p>
          </div>
        </div>
      </div>

      {/* Limitations */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-amber-900">Known Limitations</h2>
        <ul className="space-y-2 text-sm text-slate-700">
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Art Museum Focus:</strong> Currently only art museums are scored. Science, history, and specialty museums are included in the dataset but not scored.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>US/Canada Only:</strong> Scoring currently covers North American museums in the Walker Reciprocal Program.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Evidence Dependent:</strong> Museums with limited Wikipedia coverage or unclear websites may have null scores or lower confidence ratings.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Snapshot in Time:</strong> Scores reflect permanent collections and are updated periodically, but may not capture recent acquisitions or exhibitions.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Subjective Boundaries:</strong> The line between "Strong" (4) and "Flagship" (5) involves judgment. We strive for consistency but acknowledge scoring is not perfectly objective.</span>
          </li>
        </ul>
      </div>

      {/* Version Info */}
      <div className="rounded-lg bg-slate-100 p-4 text-center text-sm text-slate-600">
        <div><strong>Scoring Version:</strong> MRD v2.0 (January 2026)</div>
        <div className="mt-1"><strong>LLM Model:</strong> Claude 3.5 Sonnet (Anthropic)</div>
      </div>
    </div>
  )
}

interface ScoreRubricProps {
  title: string
  scale: string
  description: string
  rubric: Array<{
    value: number
    label: string
    description: string
  }>
}

function ScoreRubric({ title, scale, description, rubric }: ScoreRubricProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
      <div className="mb-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900">{title}</h3>
          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-800">Scale: {scale}</span>
        </div>
        <p className="mt-2 text-sm text-slate-600">{description}</p>
      </div>
      <div className="space-y-2">
        {rubric.map((item) => (
          <div key={item.value} className="flex gap-3 rounded-lg bg-white p-3 border border-slate-100">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
              {item.value}
            </div>
            <div className="flex-1">
              <div className="font-semibold text-slate-900">{item.label}</div>
              <div className="text-sm text-slate-600">{item.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
