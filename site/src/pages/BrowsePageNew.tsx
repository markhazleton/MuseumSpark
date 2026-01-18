import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadAllMuseums } from '../lib/api'
import type { Museum } from '../lib/types'

type SortKey = 'state_province' | 'city' | 'museum_name' | 'museum_type' | 'time_needed' | 'reputation' | 'collection_tier' | 'overall_quality_score' | 'priority_score' | 'nearby_museum_count'

const REPUTATION_MAP: Record<number, string> = {
  0: 'International',
  1: 'National',
  2: 'Regional',
  3: 'Local',
}

const COLLECTION_TIER_MAP: Record<number, string> = {
  0: 'Flagship',
  1: 'Strong',
  2: 'Moderate',
  3: 'Small',
}

export default function BrowsePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [museums, setMuseums] = useState<Museum[]>([])

  const [q, setQ] = useState('')
  const [stateFilter, setStateFilter] = useState<string>('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [showScoredOnly, setShowScoredOnly] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('overall_quality_score')
  const [sortDesc, setSortDesc] = useState(true)
  const [page, setPage] = useState(1)
  const pageSize = 100

  useEffect(() => {
    let cancelled = false
    loadAllMuseums()
      .then((data) => {
        if (cancelled) return
        setMuseums(data.museums ?? [])
        setLoading(false)
      })
      .catch((e: unknown) => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : String(e))
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const scoredCount = useMemo(() => {
    return museums.filter(m => m.is_scoreable && (m.impressionist_strength || m.modern_contemporary_strength)).length
  }, [museums])

  const facets = useMemo(() => {
    const states = new Set<string>()
    const domains = new Set<string>()
    for (const m of museums) {
      if (m.state_province) states.add(String(m.state_province))
      if (m.primary_domain) domains.add(String(m.primary_domain))
    }
    const sortAlpha = (a: string, b: string) => String(a).localeCompare(String(b))
    return {
      states: Array.from(states).sort(sortAlpha),
      domains: Array.from(domains).sort(sortAlpha),
    }
  }, [museums])

  const filtered = useMemo(() => {
    const qn = q.trim().toLowerCase()

    const out: Museum[] = []
    for (const m of museums) {
      // Text search
      if (qn) {
        const hay = [m.museum_name, m.city, ...(m.alternate_names ?? [])].filter(Boolean).map(s => String(s).toLowerCase()).join(' | ')
        if (!hay.includes(qn)) continue
      }

      // Filters
      if (stateFilter && String(m.state_province).toLowerCase() !== stateFilter.toLowerCase()) continue
      if (domainFilter && String(m.primary_domain ?? '').toLowerCase() !== domainFilter.toLowerCase()) continue
      
      // Scoring filters
      if (showScoredOnly && (!m.is_scoreable || (!m.impressionist_strength && !m.modern_contemporary_strength))) continue

      out.push(m)
    }
    return out
  }, [museums, q, stateFilter, domainFilter, showScoredOnly])

  const sorted = useMemo(() => {
    const arr = [...filtered]
    arr.sort((a, b) => {
      let comparison = 0

      if (sortKey === 'museum_name') {
        comparison = String(a.museum_name || '').localeCompare(String(b.museum_name || ''))
      } else if (sortKey === 'state_province') {
        comparison = String(a.state_province || '').localeCompare(String(b.state_province || ''))
      } else if (sortKey === 'city') {
        comparison = String(a.city || '').localeCompare(String(b.city || ''))
      } else if (sortKey === 'museum_type') {
        comparison = String(a.museum_type || '').localeCompare(String(b.museum_type || ''))
      } else if (sortKey === 'time_needed') {
        comparison = String(a.time_needed || '').localeCompare(String(b.time_needed || ''))
      } else if (sortKey === 'reputation') {
        comparison = (a.reputation ?? 999) - (b.reputation ?? 999)
      } else if (sortKey === 'collection_tier') {
        comparison = (a.collection_tier ?? 999) - (b.collection_tier ?? 999)
      } else if (sortKey === 'overall_quality_score') {
        comparison = (a.overall_quality_score ?? -1) - (b.overall_quality_score ?? -1)
      } else if (sortKey === 'priority_score') {
        comparison = (a.priority_score ?? 999) - (b.priority_score ?? 999)
      } else if (sortKey === 'nearby_museum_count') {
        comparison = (a.nearby_museum_count ?? 0) - (b.nearby_museum_count ?? 0)
      }

      if (sortDesc) comparison = -comparison
      if (comparison === 0) {
        comparison = String(a.museum_name).localeCompare(String(b.museum_name))
      }
      return comparison
    })
    return arr
  }, [filtered, sortKey, sortDesc])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paged = useMemo(() => {
    const start = (page - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, page, pageSize])

  useEffect(() => {
    setPage(1)
  }, [q, stateFilter, domainFilter, showScoredOnly])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-slate-600">Loading museums...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <h2 className="text-lg font-semibold text-red-900">Error Loading Data</h2>
        <p className="mt-2 text-red-700">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="rounded-xl bg-gradient-to-br from-blue-600 to-purple-700 p-8 text-white shadow-xl">
        <h1 className="text-4xl font-bold">Museum Master Data</h1>
        <p className="mt-3 text-xl text-blue-100">
          {museums.length.toLocaleString()} museums • {scoredCount} with AI-powered art scoring
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Filters & Search</h2>
        
        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by museum name or city..."
            className="w-full rounded-md border border-slate-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        {/* Filters Row */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">State</label>
            <select
              className="w-full rounded-md border border-slate-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
            >
              <option value="">All States</option>
              {facets.states.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Type</label>
            <select
              className="w-full rounded-md border border-slate-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
            >
              <option value="">All Types</option>
              {facets.domains.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
                checked={showScoredOnly}
                onChange={(e) => setShowScoredOnly(e.target.checked)}
              />
              <span className="text-sm font-medium text-slate-700">AI-Scored Only ({scoredCount})</span>
            </label>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-slate-600">
        <div>
          Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, sorted.length)} of {sorted.length.toLocaleString()} museums
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <span>Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <SortableHeader label="State" sortKey="state_province" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="City" sortKey="city" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Museum Name" sortKey="museum_name" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Type" sortKey="museum_type" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Time Needed" sortKey="time_needed" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Reputation" sortKey="reputation" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Collection" sortKey="collection_tier" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Quality ↑" sortKey="overall_quality_score" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Priority ↓" sortKey="priority_score" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <SortableHeader label="Nearby" sortKey="nearby_museum_count" currentSort={sortKey} desc={sortDesc} onSort={setSortKey} onToggleDesc={() => setSortDesc(!sortDesc)} />
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Notes</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((museum, idx) => (
              <tr key={museum.museum_id} className={`border-b border-slate-100 hover:bg-slate-50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/30'}`}>
                <td className="px-4 py-3 text-slate-700">{museum.state_province}</td>
                <td className="px-4 py-3 text-slate-700">{museum.city}</td>
                <td className="px-4 py-3">
                  <Link
                    to={`/museums/${museum.museum_id}`}
                    className="font-medium text-blue-600 hover:underline"
                  >
                    {museum.museum_name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{museum.museum_type || '—'}</td>
                <td className="px-4 py-3 text-slate-600">{museum.time_needed || '—'}</td>
                <td className="px-4 py-3 text-slate-600">
                  {museum.reputation !== null && museum.reputation !== undefined ? REPUTATION_MAP[museum.reputation] : '—'}
                </td>
                <td className="px-4 py-3 text-slate-600">
                  {museum.collection_tier !== null && museum.collection_tier !== undefined ? COLLECTION_TIER_MAP[museum.collection_tier] : '—'}
                </td>
                <td className="px-4 py-3 text-center font-medium text-emerald-700">
                  {museum.overall_quality_score !== null && museum.overall_quality_score !== undefined ? museum.overall_quality_score : '—'}
                </td>
                <td className="px-4 py-3 text-center font-medium text-blue-700">
                  {museum.priority_score !== null && museum.priority_score !== undefined ? museum.priority_score.toFixed(1) : '—'}
                </td>
                <td className="px-4 py-3 text-center text-slate-600">
                  {museum.nearby_museum_count || '—'}
                </td>
                <td className="px-4 py-3 text-slate-600 max-w-xs truncate">
                  {museum.content_summary ? (
                    <span className="text-xs" title={museum.content_summary}>
                      {museum.content_summary.slice(0, 80)}...
                    </span>
                  ) : museum.notes ? (
                    <span className="text-xs" title={museum.notes}>
                      {museum.notes.slice(0, 80)}...
                    </span>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Bottom */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 border-t border-slate-200 pt-6">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="px-4 py-2 text-sm text-slate-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}

function SortableHeader({ 
  label, 
  sortKey, 
  currentSort, 
  desc, 
  onSort, 
  onToggleDesc 
}: { 
  label: string
  sortKey: SortKey
  currentSort: SortKey
  desc: boolean
  onSort: (key: SortKey) => void
  onToggleDesc: () => void
}) {
  const isActive = currentSort === sortKey
  return (
    <th 
      className="px-4 py-3 text-left font-semibold text-slate-700 cursor-pointer hover:bg-slate-100 select-none"
      onClick={() => {
        if (isActive) {
          onToggleDesc()
        } else {
          onSort(sortKey)
        }
      }}
    >
      <div className="flex items-center gap-1">
        {label}
        {isActive && (
          <span className="text-blue-600">{desc ? '↓' : '↑'}</span>
        )}
      </div>
    </th>
  )
}
}
