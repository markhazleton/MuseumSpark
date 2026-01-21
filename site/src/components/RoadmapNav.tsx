import { NavLink } from 'react-router-dom'

export default function RoadmapNav() {
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    [
      'rounded-md px-4 py-2 text-sm font-medium transition-colors',
      isActive 
        ? 'bg-blue-600 text-white shadow-sm' 
        : 'text-slate-700 hover:bg-blue-50 hover:text-blue-700',
    ].join(' ')

  return (
    <nav className="mb-8 rounded-lg border border-slate-200 bg-white p-2 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <NavLink to="/roadmap" className={navLinkClass} end>
          📍 Roadmap
        </NavLink>
        <NavLink to="/roadmap/pipeline" className={navLinkClass}>
          🔄 Data Pipeline
        </NavLink>
        <NavLink to="/roadmap/scoring" className={navLinkClass}>
          ⭐ Scoring
        </NavLink>
        <NavLink to="/roadmap/data-model" className={navLinkClass}>
          🗂️ Data Model
        </NavLink>
      </div>
    </nav>
  )
}
