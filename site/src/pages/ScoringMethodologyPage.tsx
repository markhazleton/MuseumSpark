import RoadmapNav from '../components/RoadmapNav'

export default function ScoringMethodologyPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-8 pb-20">
      <RoadmapNav />
      {/* Header */}
      <div className="rounded-xl bg-gradient-to-br from-purple-600 to-blue-700 p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold">Scoring Methodology</h1>
        <p className="mt-3 text-xl text-purple-100">
          Transparent, data-driven museum quality assessment — v3.1.T
        </p>
      </div>

      {/* Overview */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Overview</h2>
        <p className="text-slate-700 leading-relaxed">
          MuseumSpark uses a multi-dimensional scoring system to help art enthusiasts discover and prioritize museums.
          The methodology combines LLM-powered analysis of curated evidence with deterministic calculations to produce
          a <strong>Priority Score</strong> (lower = higher priority) and an <strong>Outcome Tier</strong> that reflects
          predicted visitor travel gravity — from Must-See anchors to Background institutions.
        </p>
      </div>

      {/* Two-Phase Scoring System */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-blue-900">Two-Phase Scoring System</h2>
        <div className="space-y-4">
          <div className="rounded-lg bg-white p-4 border border-blue-100">
            <h3 className="font-bold text-blue-800 mb-2">Phase 1: LLM Judgment (Pipeline Phase 2)</h3>
            <p className="text-slate-700 text-sm">
              An AI model analyzes curated evidence packets (Wikipedia articles, museum websites, Wikidata) to assign
              bounded scores for each collection axis and institutional signals. LLM is a judge, not a researcher —
              it only evaluates provided evidence and returns null when evidence is insufficient.
            </p>
          </div>
          <div className="rounded-lg bg-white p-4 border border-blue-100">
            <h3 className="font-bold text-blue-800 mb-2">Phase 2: Deterministic Calculation (Pipeline Phase 3)</h3>
            <p className="text-slate-700 text-sm">
              Priority Score and Outcome Tier are computed using fixed formulas from MRD v3.1.T.
              Same inputs always produce the same outputs. Fully auditable and reproducible. No LLM involved.
            </p>
          </div>
        </div>
      </div>

      {/* Core Scoring Fields */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-6 text-2xl font-bold text-slate-900">Core Scoring Fields (MRD v3.1.T)</h2>
        <p className="mb-6 text-slate-600">
          Art museums are scored on six dimensions using a 0–5 scale (higher = stronger attribute).
          Three dimensions measure collection axes; one measures historical interpretation depth;
          one measures exhibition/curatorial authority; one measures overall collection authority.
        </p>

        <div className="space-y-6">
          <ScoreRubric
            title="Impressionist / Post-Impressionist Strength"
            scale="0-5"
            description="Measures the depth, authority, and scholarly importance of permanent Impressionist and Post-Impressionist holdings. Core period: c. 1860s–1905 (Monet, Renoir, Degas, Cézanne, Van Gogh, Gauguin, Seurat, etc.). Does NOT include modern works 'in the spirit of' Impressionism or exhibition programming alone."
            rubric={[
              { value: 5, label: "Canon-Defining", description: "Field-defining at national/international level. Canonical works, reference institution for Impressionist scholarship." },
              { value: 4, label: "Major Scholarly", description: "Deep, high-quality holdings with clear scholarly value and national significance." },
              { value: 3, label: "Strong Regional", description: "Coherent, well-curated holdings with recognized strength within a region or theme." },
              { value: 2, label: "Modest/Supporting", description: "Contextual or educational value; lacks depth, rarity, or sustained curatorial impact." },
              { value: 1, label: "Limited", description: "Small or inconsistent holdings with minimal curatorial or scholarly relevance." },
              { value: 0, label: "None", description: "No meaningful Impressionist works of significance." },
            ]}
          />

          <ScoreRubric
            title="Modern / Contemporary Strength"
            scale="0-5"
            description="Measures the depth, authority, and scholarly importance of permanent Modern and Contemporary art holdings. Scope: Late Modern (1920s–1960s) and Contemporary (1970s–present). Defined by modernist rupture, experimentation, abstraction, or conceptual critique."
            rubric={[
              { value: 5, label: "Canon-Defining", description: "Field-defining at national/international level. Canonical works, reference institution for Modern/Contemporary scholarship." },
              { value: 4, label: "Major Scholarly", description: "Deep, high-quality holdings with clear scholarly value and national significance." },
              { value: 3, label: "Strong Regional", description: "Coherent, well-curated holdings with recognized strength within a region or theme." },
              { value: 2, label: "Modest/Supporting", description: "Contextual or educational value; lacks depth or sustained impact." },
              { value: 1, label: "Limited", description: "Small or inconsistent holdings with minimal relevance." },
              { value: 0, label: "None", description: "No meaningful Modern/Contemporary works of significance." },
            ]}
          />

          <ScoreRubric
            title="Historical Art Traditions (HAT) Strength"
            scale="0-5"
            description="New in v3.1.T. Measures depth, authority, and coherence of tradition-based artistic production — art grounded in sustained cultural, academic, workshop, ceremonial, courtly, or lineage-based systems. Includes non-Western canons, Indigenous lineage art, decorative arts, and court traditions. Critical rule: works belonging to the Impressionist movement or defined by modernist rupture belong in those categories, not here."
            rubric={[
              { value: 5, label: "Canon-Defining", description: "Field-defining tradition-based collection. Institution is a reference point within its tradition." },
              { value: 4, label: "Major Scholarly", description: "Deep, high-quality tradition-based holdings with clear scholarly value." },
              { value: 3, label: "Strong Regional", description: "Coherent, well-curated tradition-based holdings with recognized regional strength." },
              { value: 2, label: "Modest/Supporting", description: "Tradition-based works provide contextual value; lacks depth or sustained impact." },
              { value: 1, label: "Limited", description: "Small or inconsistent tradition-based holdings." },
              { value: 0, label: "None", description: "No tradition-based works of significance." },
            ]}
          />

          <ScoreRubric
            title="Historical Context Score"
            scale="0-5"
            description="Measures the quality and depth of historical interpretation — how clearly, rigorously, and insightfully the museum constructs historical understanding. Evaluates interpretive strength, NOT collection size, reputation, or attendance. Applies to art, science, cultural, or social history."
            rubric={[
              { value: 5, label: "Canon-Defining Interpretation", description: "Field-shaping; defines or reshapes understanding of a major historical subject. Multi-layered, analytical, grounded in strong primary material. ★ Must-See qualifier." },
              { value: 4, label: "Deep, Integrated Interpretation", description: "Substantial depth and coherence; integrates multiple layers of context; goes beyond explanation into analysis and synthesis." },
              { value: 3, label: "Intentional Historical Framing", description: "Clear intent and solid explanatory structure; explains what happened and why it matters; limited in depth or layering." },
              { value: 2, label: "Descriptive / Place-Based", description: "Primarily descriptive or documentary; focuses on facts, chronology, or preservation; primarily local relevance." },
              { value: 1, label: "Minimal", description: "Limited or incidental historical content; does not meaningfully construct a narrative." },
              { value: 0, label: "None", description: "Not historically oriented; history is absent or incidental." },
            ]}
          />

          <ScoreRubric
            title="Exhibitions & Curatorial Authority (ECA)"
            scale="0-5"
            description="Measures curatorial influence outside permanent collections: exhibition authorship, commissioning power, and intellectual leadership. ECA evaluates programmatic authority only. In the Priority Score formula, ECA can elevate Effective PAS — allowing exhibition-powerhouse institutions to score well even with weaker permanent holdings."
            rubric={[
              { value: 5, label: "Field-Shaping", description: "Produces exhibitions, research, or commissions shaping discourse nationally or internationally." },
              { value: 4, label: "Nationally Recognized", description: "Sustained record of original, influential exhibitions with national reach. Also qualifies for High Priority tier." },
              { value: 3, label: "Strong Regional", description: "Original and respected exhibitions with regional influence." },
              { value: 2, label: "Competent", description: "Professionally executed but largely derivative or touring exhibitions." },
              { value: 1, label: "Minimal", description: "Limited scope or intellectual contribution." },
              { value: 0, label: "None", description: "No meaningful exhibition programming or curatorial presence." },
            ]}
          />

          <ScoreRubric
            title="Collection-Based Strength"
            scale="0-5"
            description="Measures the depth, authority, and scholarly importance of permanent holdings across ALL art categories. Art-first evaluation; does not evaluate popularity, attendance, branding, or reputation."
            rubric={[
              { value: 5, label: "Canon-Defining", description: "Field-defining at national/international level. Encyclopedic breadth or unquestioned domain authority. Reference institution. ★ Must-See qualifier." },
              { value: 4, label: "Major Scholarly", description: "Deep, high-quality collection with national significance. Important works and artists, supports sustained research." },
              { value: 3, label: "Strong Regional", description: "Coherent, well-curated collection with strength within a region, medium, movement, or theme." },
              { value: 2, label: "Modest/Supporting", description: "Contextual or educational value; lacks depth, rarity, or sustained impact." },
              { value: 1, label: "Limited", description: "Small or inconsistent permanent collection with minimal scholarly relevance." },
              { value: 0, label: "None", description: "No meaningful permanent collection (exhibition-only spaces, archives without objects)." },
            ]}
          />
        </div>
      </div>

      {/* Reputation & Collection Level */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-6 text-2xl font-bold text-slate-900">Institutional Classification Fields</h2>
        <p className="mb-4 text-slate-600 text-sm">
          These fields use structural evidence only. Media praise, awards, visitor numbers, and building size are
          explicitly excluded from classification evidence.
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-bold text-slate-800 mb-3">Reputation Level</h3>
            <p className="text-sm text-slate-600 mb-3">
              Structural scope of institutional recognition and role — not collection strength, interpretive quality,
              or media visibility. Defaults to Local.
            </p>
            <div className="space-y-2 text-sm">
              {[
                { level: "International", penalty: "+0", desc: "Sustained cross-border institutional role; originating exhibitions with ongoing international circulation." },
                { level: "National", penalty: "+0", desc: "National governance, funding, or sustained multi-state exhibition/research reach." },
                { level: "Regional", penalty: "+2", desc: "Functions as a recognized anchor across a broader region (multi-metro or multi-state)." },
                { level: "Supra-Local", penalty: "+3", desc: "Meaningfully outward-facing beyond one city, but not a recognized regional anchor." },
                { level: "Local", penalty: "+4", desc: "Recognition confined primarily to the immediate city or locality. Default." },
              ].map(({ level, penalty, desc }) => (
                <div key={level} className="flex gap-3 rounded-lg bg-slate-50 p-3 border border-slate-100">
                  <div className="flex-shrink-0 w-32 font-semibold text-slate-800">{level} <span className="text-orange-600 font-mono text-xs">{penalty}</span></div>
                  <div className="text-slate-600">{desc}</div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-bold text-slate-800 mb-3">Collection Level</h3>
            <p className="text-sm text-slate-600 mb-3">
              Scale and structural role of permanent holdings. Requires explicit, documentable evidence.
              Defaults to Small.
            </p>
            <div className="space-y-2 text-sm">
              {[
                { level: "Flagship", penalty: "+0", desc: "Field-shaping depth or breadth; active scholarly reference; substantial primary evidence whose loss would materially reduce the field's research base." },
                { level: "Strong", penalty: "+0", desc: "Clearly documented central institutional asset; coherent scope; used in sustained curatorial or research contexts." },
                { level: "Moderate", penalty: "+2", desc: "Documented, identifiable discrete collection with some internal structure; supports interpretation in a recurring way." },
                { level: "Small", penalty: "+4", desc: "Minimal, fragmented, or incidental holdings; exhibition-driven or insufficient evidence for Moderate. Default." },
              ].map(({ level, penalty, desc }) => (
                <div key={level} className="flex gap-3 rounded-lg bg-slate-50 p-3 border border-slate-100">
                  <div className="flex-shrink-0 w-24 font-semibold text-slate-800">{level} <span className="text-orange-600 font-mono text-xs">{penalty}</span></div>
                  <div className="text-slate-600">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Priority Score Formula */}
      <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-emerald-900">Priority Score Formula (MRD v3.1.T)</h2>
        <p className="mb-4 text-slate-700">
          The <strong>Priority Score</strong> identifies museums with strong collections relative to their
          institutional profile. Lower scores = higher priority. Score has a <strong>floor of 1</strong>.
        </p>

        <div className="rounded-lg bg-white p-6 border border-emerald-200 font-mono text-sm overflow-x-auto space-y-4">
          <div>
            <div className="text-slate-500 text-xs mb-1">Step 1 — Collection-Based PAS</div>
            <div className="text-blue-700">Collection-Based PAS = MAX(Impressionist, Modern/Contemporary, HAT)</div>
          </div>
          <div>
            <div className="text-slate-500 text-xs mb-1">Step 2 — Effective PAS (ECA may elevate)</div>
            <div className="text-blue-700">Effective PAS = MAX(Collection-Based PAS, ECA)</div>
          </div>
          <div>
            <div className="text-slate-500 text-xs mb-1">Step 3 — Dual-Strength Bonus</div>
            <div className="text-violet-700">Dual-Strength Bonus = −2 if Impressionist ≥ 3 AND Modern/Contemporary ≥ 3</div>
            <div className="text-slate-500 text-xs mt-1">HAT does not qualify. Threshold is ≥3 (not ≥4).</div>
          </div>
          <div className="pt-4 border-t border-slate-200">
            <div className="text-slate-600 mb-2">Priority Score =</div>
            <div className="ml-4 space-y-1 text-slate-800">
              <div className="font-bold">MAX(1,</div>
              <div className="ml-4">(6 − Effective PAS) × 2</div>
              <div className="ml-4">+ (6 − Historical Context Score)</div>
              <div className="ml-4">+ Reputation Penalty</div>
              <div className="ml-4">+ Collection Penalty</div>
              <div className="ml-4">+ Dual-Strength Bonus</div>
              <div className="font-bold">)</div>
            </div>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <h3 className="font-bold text-emerald-900">Penalty Reference</h3>
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div>
              <div className="font-semibold text-slate-700 mb-1">Reputation Penalty</div>
              <div className="space-y-1 text-slate-600 font-mono">
                <div>International / National = +0</div>
                <div>Regional               = +2</div>
                <div>Supra-Local            = +3</div>
                <div>Local                  = +4</div>
              </div>
            </div>
            <div>
              <div className="font-semibold text-slate-700 mb-1">Collection Penalty</div>
              <div className="space-y-1 text-slate-600 font-mono">
                <div>Flagship / Strong = +0</div>
                <div>Moderate          = +2</div>
                <div>Small             = +4</div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg bg-emerald-100 border border-emerald-200 p-4">
          <h3 className="font-bold text-emerald-900 mb-2">Score Interpretation</h3>
          <ul className="space-y-1 text-sm text-slate-700">
            <li><strong>Score 1–5:</strong> Must-Visit destinations — exceptional quality</li>
            <li><strong>Score 6–9:</strong> High-priority with strong collections</li>
            <li><strong>Score 10–15:</strong> Worthwhile, plan if in the area</li>
            <li><strong>Score 16+:</strong> Community-oriented or lower institutional gravity</li>
            <li className="mt-2 pt-2 border-t border-emerald-200"><strong>★ Must-See:</strong> Collection-Based PAS = 5 or Historical Context = 5</li>
          </ul>
        </div>
      </div>

      {/* Outcome Tiers */}
      <div className="rounded-lg border border-violet-200 bg-violet-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-violet-900">Outcome Tiers (MRD v3.1.T — Behavioral Gravity Framework)</h2>
        <p className="mb-4 text-slate-700">
          Outcome Tiers reflect predicted visitor routing behavior and institutional merit. Tiers are assigned
          deterministically using the Priority Score and institutional signals.
        </p>

        <div className="space-y-3">
          {[
            {
              tier: "Must-See",
              icon: "★",
              color: "bg-emerald-100 border-emerald-300",
              headerColor: "text-emerald-800",
              rule: "Collection-Based PAS = 5 OR Historical Context = 5",
              desc: "Canon-defining collection or historical interpretation. A trip anchor. Worth a dedicated journey regardless of other plans.",
            },
            {
              tier: "High Priority",
              icon: "▲",
              color: "bg-blue-100 border-blue-300",
              headerColor: "text-blue-800",
              rule: "Priority Score ≤ 9; OR Flagship Collection + PAS = 4; OR ECA ≥ 4; OR HC = 4 + National/International rep",
              desc: "Exceptional collection or curatorial authority. Worth a dedicated visit. Priority Score ≤ 9 alone is sufficient.",
            },
            {
              tier: "Regionally Important",
              icon: "◆",
              color: "bg-violet-100 border-violet-300",
              headerColor: "text-violet-800",
              rule: "Score 10–15 AND Regional reputation AND functions as a primary regional art or history reference",
              desc: "Primary regional art or history reference. Plan around it when visiting the region.",
            },
            {
              tier: "Detour",
              icon: "↗",
              color: "bg-orange-100 border-orange-300",
              headerColor: "text-orange-800",
              rule: "Specialization signal (Specialized Art Site, Specialized Cultural Site, or You Won't See This Again) AND (Effective PAS ≥ 3 OR HC ≥ 3)",
              desc: "A culturally motivated traveler would plausibly alter their route. Specialization alone is insufficient — institutional strength must also be present.",
            },
            {
              tier: "Consider",
              icon: "●",
              color: "bg-amber-100 border-amber-300",
              headerColor: "text-amber-800",
              rule: "Worth visiting when already in the area. No routing pull.",
              desc: "Proximity-dependent value. Subtypes: Generalized Collection Museum, Locally Historic, Quirky / Memorable, Kunsthalle.",
            },
            {
              tier: "Background",
              icon: "○",
              color: "bg-slate-100 border-slate-300",
              headerColor: "text-slate-700",
              rule: "Default classification. Limited travel gravity.",
              desc: "May provide local value but typically does not influence visitor routing decisions. Default for community-oriented institutions.",
            },
          ].map(({ tier, icon, color, headerColor, rule, desc }) => (
            <div key={tier} className={`rounded-lg border p-4 ${color}`}>
              <div className="flex items-start gap-3">
                <div className={`text-2xl font-bold flex-shrink-0 ${headerColor}`}>{icon}</div>
                <div>
                  <div className={`font-bold text-lg ${headerColor}`}>{tier}</div>
                  <div className="text-xs font-mono text-slate-600 mt-1 mb-2">{rule}</div>
                  <div className="text-sm text-slate-700">{desc}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Design Principles */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-slate-900">Design Principles</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Evidence-Based</h3>
            <p className="text-sm text-slate-700">
              LLM judges only see curated evidence from reliable sources. Absence of evidence constrains scores
              downward. Null is preferred over a hallucinated score.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Deterministic Calculation</h3>
            <p className="text-sm text-slate-700">
              Priority Score and Outcome Tier computed using fixed formulas. Same inputs always produce same outputs.
              Fully auditable and reproducible.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Behavioral Gravity</h3>
            <p className="text-sm text-slate-700">
              Outcome Tiers reflect how a museum affects visitor routing decisions — not just institutional quality.
              Detour, Consider, and Background distinguish between route-altering, proximity-based, and low-gravity visits.
            </p>
          </div>
          <div className="rounded-lg bg-slate-50 p-4 border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Conservative by Default</h3>
            <p className="text-sm text-slate-700">
              Reputation defaults to Local. Collection Level defaults to Small. Borderline cases are classified
              downward, never upward. Strict evidentiary standards prevent inflation.
            </p>
          </div>
        </div>
      </div>

      {/* Known Limitations */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold text-amber-900">Known Limitations</h2>
        <ul className="space-y-2 text-sm text-slate-700">
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Art Museum Focus:</strong> Currently only art museums are scored. Science, history, and specialty museums are included but not scored.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Walker Reciprocal Scope:</strong> Dataset covers Walker Art Reciprocal Program members only. Not a comprehensive museum directory.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Evidence Dependent:</strong> Museums with limited Wikipedia coverage or unclear websites may have null scores or lower confidence ratings.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Snapshot in Time:</strong> Scores reflect permanent collections and are updated periodically but may not capture recent acquisitions.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span><strong>Subjective Boundaries:</strong> The line between score levels (e.g., Strong vs. Flagship) involves judgment. We strive for consistency and document reasoning in score_notes.</span>
          </li>
        </ul>
      </div>

      {/* Version Info */}
      <div className="rounded-lg bg-slate-100 p-4 text-center text-sm text-slate-600">
        <div><strong>Scoring Version:</strong> MRD v3.1.T (March 2026)</div>
        <div className="mt-1 text-xs text-slate-500">
          Key changes from v3.0: HAT (Historical Art Traditions) third scoring axis; Supra-Local reputation tier;
          Dual-Strength bonus threshold lowered to ≥3; new Priority Score formula with Effective PAS; Outcome Tier system;
          Kunsthalle Museum and Community Art Center institution types added.
        </div>
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
