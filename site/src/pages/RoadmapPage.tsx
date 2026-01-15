import { Link } from 'react-router-dom'

export default function RoadmapPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-12 pb-20">
      
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">Project Roadmap</h1>
        <p className="mt-4 text-lg text-slate-600">
          The evolution of MuseumSpark: From open data aggregation to a full-featured AI travel agent.
        </p>
      </div>

      {/* Phase 1 */}
      <Section status="current" title="Phase 1: Open Data Public Records">
        <p className="mb-4 text-slate-700">
          <strong>Focus:</strong> Establishing a comprehensive baseline using public data sources.
        </p>
        <ul className="list-inside list-disc space-y-2 text-sm text-slate-600">
          <li><strong>Foundation:</strong> Walker Art Reciprocal Program seed list.</li>
          <li><strong>Automated Enrichment:</strong> Using scripts to gather data from Wikidata, Wikipedia, and IMLS.</li>
          <li><strong>Structural Classification:</strong> Identifying "City Tiers" (Major Hub vs. Small Town) and inferring initial tiers for Reputation and Collections.</li>
          <li><strong>Web Interface:</strong> A static React browser to visualize the dataset as it grows.</li>
          <li className="font-semibold text-blue-600">Status: In Process (Open Data Enrichment)</li>
        </ul>
      </Section>

      {/* Phase 2 */}
      <Section status="planned" title="Phase 2: AI & LLM Enrichment">
        <p className="mb-4 text-slate-700">
          <strong>Focus:</strong> Deepening the dataset with qualitative insights using advanced AI models.
        </p>
        <ul className="list-inside list-disc space-y-2 text-sm text-slate-600">
          <li><strong>Targeted Processing:</strong> Selecting high-priority museums for deep-dive analysis.</li>
          <li><strong>Smart Scoring:</strong> Using Claude and OpenAI models to analyze collections and assign Master Requirement scores (Impressionist Strength, Historical Context).</li>
          <li><strong>Details Extraction:</strong> Automated gathering of detailed logistical info (hours, accessibility, precise location semantics).</li>
          <li><strong>Source Verification:</strong> Ensuring LLM outputs are cross-referenced with reliable web sources.</li>
        </ul>
      </Section>

      {/* Phase 3 */}
      <Section status="planned" title="Phase 3: Validation & Stakeholder Review">
         <p className="mb-4 text-slate-700">
          <strong>Focus:</strong> Ensuring data integrity and alignment with the project vision.
        </p>
        <ul className="list-inside list-disc space-y-2 text-sm text-slate-600">
          <li><strong>Full Dataset Audit:</strong> Algorithmic and manual checks for consistency and completeness.</li>
          <li><strong>Stakeholder Feedback:</strong> Reviewing the "Priority Scores" and categorization with art experts and primary users.</li>
          <li><strong>Direction Check:</strong> Validating the roadmap and feature set before backend development.</li>
        </ul>
      </Section>

      {/* Phase 4 */}
      <Section status="planned" title="Phase 4: Full Interactive Platform">
         <p className="mb-4 text-slate-700">
          <strong>Focus:</strong> A dynamic, personalized, and mobile-friendly application.
        </p>
        <ul className="list-inside list-disc space-y-2 text-sm text-slate-600">
          <li><strong>Backend API:</strong> Python-based API to handle complex logic and data persistence.</li>
          <li><strong>User Integration:</strong> Accounts for saving favorites, "Visited" lists, and custom notes.</li>
          <li><strong>Trip Planning Agent:</strong> Interactive AI agents to help plan trips, optimizing for routing and museum priorities.</li>
          <li><strong>Crowdsourced Enrichment:</strong> allowing users to contribute visit notes and background data to further enrich the dataset.</li>
          <li><strong>Mobile Optimized:</strong> A rich responsive design ensuring a great experience on phones and tablets.</li>
        </ul>
      </Section>

       {/* Vision */}
       <div className="rounded-xl bg-slate-100 p-8">
        <h2 className="mb-4 text-xl font-bold text-slate-900">Long-Term Vision</h2>
        <p className="text-slate-700">
          MuseumSpark aims to be the definitive tool for art lovers planning travel across North America. 
          By combining rigorous data curation with modern AI planning tools and community contributions, 
          we enable travelers to prioritize visits that match their specific cultural interests
          and logistical constraints.
        </p>
      </div>
     
      <div className="flex justify-center pt-8">
        <Link className="text-sm font-medium text-blue-600 hover:underline" to="/">
           &larr; Back to Home
        </Link>
      </div>

    </div>
  )
}

function Section({ title, children, status }: { title: string; children: React.ReactNode; status: 'completed' | 'current' | 'planned' }) {
  const borderColors = {
    completed: 'border-emerald-500',
    current: 'border-blue-500',
    planned: 'border-slate-300',
  }
  
  const bgColors = {
    completed: 'bg-emerald-50',
    current: 'bg-blue-50',
    planned: 'bg-white',
  }

  return (
    <div className={`relative border-l-4 ${borderColors[status]} ${bgColors[status]} rounded-r-lg p-6 shadow-sm`}>
      <div className="mb-4 flex items-center gap-3">
        <h2 className="text-xl font-bold text-slate-900">{title}</h2>
        {status === 'current' && <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-800">In Progress</span>}
        {status === 'completed' && <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">Done</span>}
        {status === 'planned' && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">Planned</span>}
      </div>
      <div>{children}</div>
    </div>
  )
}
