import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-slate-900 px-6 py-16 text-center text-white shadow-xl sm:px-12 sm:py-24">
        <div className="relative z-10 mx-auto max-w-4xl space-y-6">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Discover Art with <span className="text-blue-400">Precision</span>
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-slate-300 sm:text-xl">
            MuseumSpark is a travel prioritization system designed to help you plan the perfect museum visit. 
            Rank collections by artistic strength, historical context, and travel efficiency.
          </p>
          <div className="pt-4">
            <Link
              to="/browse"
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-8 py-3 text-base font-medium text-white shadow-lg transition-colors hover:bg-blue-700"
            >
              Browse the Collection
            </Link>
          </div>
        </div>
        
        {/* Abstract Background Element */}
        <div className="absolute top-0 left-0 h-full w-full opacity-20">
            <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-blue-500 blur-3xl"></div>
            <div className="absolute top-1/2 right-10 h-64 w-64 rounded-full bg-purple-500 blur-3xl"></div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="mx-auto max-w-5xl px-4">
        <h2 className="mb-10 text-center text-3xl font-bold text-slate-900">Why MuseumSpark?</h2>
        <div className="grid gap-8 md:grid-cols-3">
          <FeatureCard 
            title="Curated Scoring" 
            description="Our comprehensive MRD v3 scoring evaluates 6 dimensions: Impressionist & Modern/Contemporary collections, Historical Context, Exhibitions & Curatorial Authority, Collection-Based Strength, and Reputation. Find Must-See museums with field-defining collections."
            icon="🏆"
          />
          <FeatureCard 
            title="Smart Planning" 
            description="Filter by City Tier, Time Needed, and Historical Context. Optimize your itinerary whether you have a full day or just a quick stop."
            icon="📍"
          />
          <FeatureCard 
            title="Data Enriched" 
            description="Built on the Walker Art Reciprocal Program and enriched with open data from Wikidata and IMLS for comprehensive, verified details."
            icon="📊"
          />
        </div>
      </section>

      {/* Quick Stats or Callout */}
      <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="mb-4 text-lg font-medium text-slate-700">
          Currently tracking museums across the United States.
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/progress" className="text-sm font-medium text-blue-600 hover:underline">
            View Data Progress →
          </Link>
          <Link to="/roadmap" className="text-sm font-medium text-blue-600 hover:underline">
            See the Roadmap →
          </Link>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="mb-4 text-4xl">{icon}</div>
      <h3 className="mb-2 text-xl font-semibold text-slate-900">{title}</h3>
      <p className="text-slate-600">{description}</p>
    </div>
  )
}
