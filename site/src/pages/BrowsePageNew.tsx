import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadAllMuseums } from '../lib/api'
import { isFullRecord } from '../lib/fullness'
import { getScoreBadgeColor, getScoreLabel, getTopScores, hasAnyScore } from '../lib/scoring'
import type { Museum } from '../lib/types'

type SortKey = 'priority_score' | 'museum_name' | 'collection_quality' | 'family_friendly' | 'educational'

export default function BrowsePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [museums, setMuseums] = useState<Museum[]>([])

  const [q, setQ] = useState('')
  const [stateFilter, setStateFilter] = useState<string>('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [minQuality, setMinQuality] = useState<number>(0)
  const [minFamily, setMinFamily] = useState<number>(0)
  const [minEducational, setMinEducational] = useState<number>(0)
  const [showScoredOnly, setShowScoredOnly] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('collection_quality')
  const [page, setPage] = useState(1)
  const pageSize = 50

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
    return museums.filter(m => m.tour_planning_scores && hasAnyScore(m.tour_planning_scores)).length
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
        const hay = [m.museum_name, ...(m.alternate_names ?? [])].filter(Boolean).map(s => String(s).toLowerCase()).join(' | ')
        if (!hay.includes(qn)) continue
      }

      // Filters
      if (stateFilter && String(m.state_province).toLowerCase() !== stateFilter.toLowerCase()) continue
      if (domainFilter && String(m.primary_domain ?? '').toLowerCase() !== domainFilter.toLowerCase()) continue
      
      // Scoring filters
      const scores = m.tour_planning_scores
      if (showScoredOnly && !hasAnyScore(scores)) continue
      if (minQuality > 0 && (!scores?.collection_quality || scores.collection_quality < minQuality)) continue
      if (minFamily > 0 && (!scores?.family_friendly_score || scores.family_friendly_score < minFamily)) continue
      if (minEducational > 0 && (!scores?.educational_value_score || scores.educational_value_score < minEducational)) continue

      out.push(m)
    }
    return out
  }, [museums, q, stateFilter, domainFilter, minQuality, minFamily, minEducational, showScoredOnly])

  const sorted = useMemo(() => {
    const arr = [...filtered]
    arr.sort((a, b) => {
      if (sortKey === 'museum_name') {
        return String(a.museum_name || '').localeCompare(String(b.museum_name || ''))
      }

      if (sortKey === 'collection_quality') {
        const av = a.tour_planning_scores?.collection_quality ?? -1
        const bv = b.tour_planning_scores?.collection_quality ?? -1
        if (av !== bv) return bv - av
        return String(a.museum_name).localeCompare(String(b.museum_name))
      }

      if (sortKey === 'family_friendly') {
        const av = a.tour_planning_scores?.family_friendly_score ?? -1
        const bv = b.tour_planning_scores?.family_friendly_score ?? -1
        if (av !== bv) return bv - av
        return String(a.museum_name).localeCompare(String(b.museum_name))
      }

      if (sortKey === 'educational') {
        const av = a.tour_planning_scores?.educational_value_score ?? -1
        const bv = b.tour_planning_scores?.educational_value_score ?? -1
        if (av !== bv) return bv - av
        return String(a.museum_name).localeCompare(String(b.museum_name))
      }

      if (sortKey === 'priority_score') {
        const av = a.priority_score ?? 999999
        const bv = b.priority_score ?? 999999
        if (av !== bv) return av - bv
        return String(a.museum_name).localeCompare(String(b.museum_name))
      }

      return 0
    })
    return arr
  }, [filtered, sortKey])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paged = useMemo(() => {
    const start = (page - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, page, pageSize])

  useEffect(() => {
    setPage(1)
  }, [q, stateFilter, domainFilter, minQuality, minFamily, minEducational, showScoredOnly])

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
        <h1 className="text-4xl font-bold">Discover Museums</h1>
        <p className="mt-3 text-xl text-blue-100">
          {museums.length.toLocaleString()} museums • {scoredCount} with AI-powered tour planning scores
        </p>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg bg-white/10 p-4 backdrop-blur">
            <div className="text-3xl font-bold">{museums.length.toLocaleString()}</div>
            <div className="text-sm text-blue-100">Total Museums</div>
          </div>
          <div className="rounded-lg bg-white/10 p-4 backdrop-blur">
            <div className="text-3xl font-bold">{scoredCount}</div>
            <div className="text-sm text-blue-100">AI-Scored Museums</div>
          </div>
          <div className="rounded-lg bg-white/10 p-4 backdrop-blur">
            <div className="text-3xl font-bold">{facets.states.length}</div>
            <div className="text-sm text-blue-100">States Covered</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-slate-900">Filters</h2>
        
        {/* Search */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-2">Search</label>
          <input
            type="text"
            placeholder="Search by museum name..."
            className="w-full rounded-md border border-slate-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>

        {/* Basic Filters */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 mb-4">
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

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Sort By</label>
            <select
              className="w-full rounded-md border border-slate-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
            >
              <option value="collection_quality">Collection Quality</option>
              <option value="family_friendly">Family-Friendly</option>
              <option value="educational">Educational Value</option>
              <option value="museum_name">Name (A-Z)</option>
              <option value="priority_score">Priority Score</option>
            </select>
          </div>
        </div>

        {/* Score Filters */}
        <div className="border-t border-slate-200 pt-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-sm font-medium text-slate-700">AI Tour Planning Scores</span>
            <span className="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
              {scoredCount} museums scored
            </span>
          </div>
          
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-500/20"
                checked={showScoredOnly}
                onChange={(e) => setShowScoredOnly(e.target.checked)}
              />
              <span className="text-sm text-slate-700">Scored Only</span>
            </label>

            <div>
              <label className="block text-sm text-slate-700 mb-1">Min Quality</label>
              <select
                className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                value={minQuality}
                onChange={(e) => setMinQuality(Number(e.target.value))}
              >
                <option value="0">Any</option>
                <option value="5">5+ Good</option>
                <option value="7">7+ Excellent</option>
                <option value="8">8+ Outstanding</option>
                <option value="9">9+ World-Class</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-700 mb-1">Min Family-Friendly</label>
              <select
                className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                value={minFamily}
                onChange={(e) => setMinFamily(Number(e.target.value))}
              >
                <option value="0">Any</option>
                <option value="7">7+</option>
                <option value="8">8+</option>
                <option value="9">9+</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-700 mb-1">Min Educational</label>
              <select
                className="w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                value={minEducational}
                onChange={(e) => setMinEducational(Number(e.target.value))}
              >
                <option value="0">Any</option>
                <option value="7">7+</option>
                <option value="8">8+</option>
                <option value="9">9+</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">
          Showing {((page - 1) * pageSize) + 1}–{Math.min(page * pageSize, sorted.length)} of {sorted.length.toLocaleString()} museums
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-slate-600">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Museum Cards */}
      <div className="space-y-4">
        {paged.map((museum) => {
          const scores = museum.tour_planning_scores
          const hasScores = hasAnyScore(scores)
          const topScores = getTopScores(scores)

          return (
            <Link
              key={museum.museum_id}
              to={`/museums/${museum.museum_id}`}
              className="block rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition-all hover:border-blue-400 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3">
                    <h3 className="text-xl font-semibold text-slate-900 hover:text-blue-600">
                      {museum.museum_name}
                    </h3>
                    {hasScores && (
                      <span className="flex-shrink-0 rounded-full bg-purple-100 px-2 py-1 text-xs font-medium text-purple-700">
                        AI Scored
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-1 flex items-center gap-2 text-sm text-slate-600">
                    <span>{museum.city}, {museum.state_province}</span>
                    {museum.primary_domain && (
                      <>
                        <span>•</span>
                        <span>{museum.primary_domain}</span>
                      </>
                    )}
                  </div>

                  {museum.summary_short && (
                    <p className="mt-3 text-sm text-slate-700 line-clamp-2">
                      {museum.summary_short}
                    </p>
                  )}

                  {hasScores && scores && (
                    <div className="mt-4 space-y-3">
                      {/* Core Scores */}
                      <div className="flex flex-wrap gap-2">
                        {scores.collection_quality && (
                          <div className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${getScoreBadgeColor(scores.collection_quality)}`}>
                            <span className="text-xs">🏛️</span>
                            <span>Quality: {scores.collection_quality}/10</span>
                            <span className="text-xs opacity-75">({getScoreLabel(scores.collection_quality)})</span>
                          </div>
                        )}
                        {scores.family_friendly_score && scores.family_friendly_score >= 7 && (
                          <div className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${getScoreBadgeColor(scores.family_friendly_score)}`}>
                            <span className="text-xs">👨‍👩‍👧‍👦</span>
                            <span>Family: {scores.family_friendly_score}/10</span>
                          </div>
                        )}
                        {scores.educational_value_score && scores.educational_value_score >= 7 && (
                          <div className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${getScoreBadgeColor(scores.educational_value_score)}`}>
                            <span className="text-xs">📚</span>
                            <span>Educational: {scores.educational_value_score}/10</span>
                          </div>
                        )}
                        {scores.architecture_score && scores.architecture_score >= 7 && (
                          <div className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${getScoreBadgeColor(scores.architecture_score)}`}>
                            <span className="text-xs">🏛️</span>
                            <span>Architecture: {scores.architecture_score}/10</span>
                          </div>
                        )}
                      </div>

                      {/* Top Specialties */}
                      {topScores.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          <span className="text-xs font-medium text-slate-500">Specialties:</span>
                          {topScores.map((s) => (
                            <span
                              key={s.label}
                              className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                            >
                              {s.label} <span className="font-bold">{s.score}</span>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="text-right">
                  <div className="text-sm font-medium text-blue-600">View Details →</div>
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 border-t border-slate-200 pt-6">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-slate-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
