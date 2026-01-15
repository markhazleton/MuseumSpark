import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadAllMuseums } from '../lib/api'
import { isFullRecord } from '../lib/fullness'
import type { Museum } from '../lib/types'

const reputationOrder: Record<string, number> = {
  Local: 1,
  Regional: 2,
  National: 3,
  International: 4,
}

const collectionTierOrder: Record<string, number> = {
  Small: 1,
  Moderate: 2,
  Strong: 3,
  Flagship: 4,
}

type SortKey = 'priority_score' | 'museum_name' | 'reputation' | 'collection_tier'

function normalize(s: unknown): string {
  return String(s || '').trim().toLowerCase()
}

export default function BrowsePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [museums, setMuseums] = useState<Museum[]>([])

  const [q, setQ] = useState('')
  const [stateFilter, setStateFilter] = useState<string>('')
  const [cityFilter, setCityFilter] = useState<string>('')
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [reputationFilter, setReputationFilter] = useState<string>('')
  const [tierFilter, setTierFilter] = useState<string>('')
  const [timeFilter, setTimeFilter] = useState<string>('')
  const [onlyFull, setOnlyFull] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('priority_score')
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

  const facets = useMemo(() => {
    const states = new Set<string>()
    const domains = new Set<string>()
    const reputations = new Set<string>()
    const tiers = new Set<string>()
    const times = new Set<string>()
    for (const m of museums) {
      if (m.state_province) states.add(String(m.state_province))
      if (m.primary_domain) domains.add(String(m.primary_domain))
      if (m.reputation) reputations.add(String(m.reputation))
      if (m.collection_tier) tiers.add(String(m.collection_tier))
      if (m.time_needed) times.add(String(m.time_needed))
    }
    const sortAlpha = (a: string, b: string) => String(a).localeCompare(String(b))
    return {
      states: Array.from(states).sort(sortAlpha),
      domains: Array.from(domains).sort(sortAlpha),
      reputations: Array.from(reputations).sort(sortAlpha),
      tiers: Array.from(tiers).sort(sortAlpha),
      times: Array.from(times).sort(sortAlpha),
    }
  }, [museums])

  const filtered = useMemo(() => {
    const qn = normalize(q)
    const cityN = normalize(cityFilter)

    const matchesText = (m: Museum) => {
      if (!qn) return true
      const hay = [m.museum_name, ...(m.alternate_names ?? [])].filter(Boolean).map(normalize).join(' | ')
      return hay.includes(qn)
    }

    const out: Museum[] = []
    for (const m of museums) {
      if (!matchesText(m)) continue
      if (stateFilter && normalize(m.state_province) !== normalize(stateFilter)) continue
      if (cityN && normalize(m.city ?? '') !== cityN) continue
      if (domainFilter && normalize(m.primary_domain ?? '') !== normalize(domainFilter)) continue
      if (reputationFilter && normalize(m.reputation ?? '') !== normalize(reputationFilter)) continue
      if (tierFilter && normalize(m.collection_tier ?? '') !== normalize(tierFilter)) continue
      if (timeFilter && normalize(m.time_needed ?? '') !== normalize(timeFilter)) continue
      if (onlyFull && !isFullRecord(m)) continue
      out.push(m)
    }
    return out
  }, [museums, q, stateFilter, cityFilter, domainFilter, reputationFilter, tierFilter, timeFilter, onlyFull])

  const sorted = useMemo(() => {
    const arr = [...filtered]
    arr.sort((a, b) => {
      if (sortKey === 'museum_name') {
        return String(a.museum_name || '').localeCompare(String(b.museum_name || ''))
      }

      if (sortKey === 'priority_score') {
        const av = a.priority_score
        const bv = b.priority_score
        const aNull = av === null || av === undefined
        const bNull = bv === null || bv === undefined
        if (aNull && bNull) return a.museum_name.localeCompare(b.museum_name)
        if (aNull) return 1
        if (bNull) return -1
        if (av !== bv) return (av as number) - (bv as number)
        return a.museum_name.localeCompare(b.museum_name)
      }

      if (sortKey === 'reputation') {
        const ao = reputationOrder[a.reputation ?? ''] ?? 999
        const bo = reputationOrder[b.reputation ?? ''] ?? 999
        if (ao !== bo) return ao - bo
        return a.museum_name.localeCompare(b.museum_name)
      }

      if (sortKey === 'collection_tier') {
        const ao = collectionTierOrder[a.collection_tier ?? ''] ?? 999
        const bo = collectionTierOrder[b.collection_tier ?? ''] ?? 999
        if (ao !== bo) return ao - bo
        return a.museum_name.localeCompare(b.museum_name)
      }

      return 0
    })
    return arr
  }, [filtered, sortKey])

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize))
  const paged = useMemo(() => {
    const start = (page - 1) * pageSize
    return sorted.slice(start, start + pageSize)
  }, [sorted, page])

  // Reset page when filters change
  const [prevFilters, setPrevFilters] = useState({
    q,
    stateFilter,
    cityFilter,
    domainFilter,
    reputationFilter,
    tierFilter,
    timeFilter,
    onlyFull,
    sortKey,
  })

  // Check if filters changed
  const filtersChanged =
    q !== prevFilters.q ||
    stateFilter !== prevFilters.stateFilter ||
    cityFilter !== prevFilters.cityFilter ||
    domainFilter !== prevFilters.domainFilter ||
    reputationFilter !== prevFilters.reputationFilter ||
    tierFilter !== prevFilters.tierFilter ||
    timeFilter !== prevFilters.timeFilter ||
    onlyFull !== prevFilters.onlyFull ||
    sortKey !== prevFilters.sortKey

  if (filtersChanged) {
    setPrevFilters({
      q,
      stateFilter,
      cityFilter,
      domainFilter,
      reputationFilter,
      tierFilter,
      timeFilter,
      onlyFull,
      sortKey,
    })
    setPage(1)
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="text-slate-700">Loading museum index…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-white p-6">
        <div className="font-semibold text-red-700">Failed to load data</div>
        <div className="mt-2 text-sm text-slate-700">{error}</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="grid gap-3 md:grid-cols-6">
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Search</label>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Museum name…"
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">State/Province</label>
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {facets.states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">City</label>
            <input
              value={cityFilter}
              onChange={(e) => setCityFilter(e.target.value)}
              placeholder="Exact city"
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">Domain</label>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {facets.domains.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">Sort</label>
            <select
              value={sortKey}
              onChange={(e) => setSortKey(e.target.value as SortKey)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="priority_score">Priority score</option>
              <option value="museum_name">Name</option>
              <option value="reputation">Reputation</option>
              <option value="collection_tier">Collection tier</option>
            </select>
          </div>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-6">
          <div>
            <label className="text-sm font-medium text-slate-700">Reputation</label>
            <select
              value={reputationFilter}
              onChange={(e) => setReputationFilter(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {facets.reputations.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">Collection tier</label>
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {facets.tiers.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">Time needed</label>
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {facets.times.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Show</label>
            <div className="mt-1 flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input type="checkbox" checked={onlyFull} onChange={(e) => setOnlyFull(e.target.checked)} />
                FULL only
              </label>
              <div className="text-sm text-slate-600">{sorted.length.toLocaleString()} results</div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div className="text-sm text-slate-600">
            Page {page} of {totalPages}
          </div>
          <div className="flex items-center gap-2">
            <button
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm disabled:opacity-50"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              Prev
            </button>
            <button
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm disabled:opacity-50"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next
            </button>
          </div>
        </div>

        <ul className="divide-y divide-slate-200">
          {paged.map((m) => {
            const full = isFullRecord(m)
            return (
              <li key={m.museum_id} className="px-4 py-3 hover:bg-slate-50">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <Link
                      className="font-medium text-slate-900 hover:underline"
                      to={`/museums/${encodeURIComponent(m.museum_id)}`}
                    >
                      {m.museum_name}
                    </Link>
                    <div className="mt-1 text-sm text-slate-600">
                      {m.city}, {m.state_province} • {m.primary_domain ?? 'Unknown domain'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={[
                        'rounded-full px-2 py-1 text-xs font-semibold',
                        full ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800',
                      ].join(' ')}
                    >
                      {full ? 'FULL' : 'Placeholder'}
                    </span>
                    <span className="text-xs text-slate-600">
                      {m.time_needed ?? (m.estimated_visit_minutes ? `${m.estimated_visit_minutes} min` : '—')}
                    </span>
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
