import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { loadAllMuseums, loadStateFile } from '../lib/api'
import { isFullRecord } from '../lib/fullness'
import type { Museum } from '../lib/types'

function deriveStateCodeFromId(museumId: string): string | null {
  const parts = museumId.split('-')
  if (parts.length < 2) return null
  const candidate = parts[1]?.toUpperCase()
  if (!candidate || candidate.length !== 2) return null
  if (!/^[A-Z]{2}$/.test(candidate)) return null
  return candidate
}

function fieldValue(v: unknown): string {
  if (v === null || v === undefined) return 'Not available'
  if (Array.isArray(v)) return v.length ? v.join(', ') : 'Not available'
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  return String(v)
}

export default function MuseumDetailPage() {
  const { museumId } = useParams()
  const id = museumId ? decodeURIComponent(museumId) : ''
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [museum, setMuseum] = useState<Museum | null>(null)
  const [source, setSource] = useState<'state' | 'index' | null>(null)

  const stateCode = useMemo(() => (id ? deriveStateCodeFromId(id) : null), [id])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setMuseum(null)
    setSource(null)

    async function run() {
      if (!id) throw new Error('Missing museum id')

      // Prefer canonical state file.
      if (stateCode) {
        try {
          const sf = await loadStateFile(stateCode)
          const found = (sf.museums ?? []).find((m) => m.museum_id === id) ?? null
          if (found) {
            return { museum: found, source: 'state' as const }
          }
        } catch {
          // Fall through to index.
        }
      }

      const idx = await loadAllMuseums()
      const found = (idx.museums ?? []).find((m) => m.museum_id === id) ?? null
      if (!found) throw new Error('Museum not found in state file or index')
      return { museum: found, source: 'index' as const }
    }

    run()
      .then((res) => {
        if (cancelled) return
        setMuseum(res.museum)
        setSource(res.source)
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
  }, [id, stateCode])

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="text-slate-700">Loading museum…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-white p-6">
        <div className="font-semibold text-red-700">Unable to load museum</div>
        <div className="mt-2 text-sm text-slate-700">{error}</div>
        <div className="mt-4">
          <Link className="text-sm text-slate-900 underline" to="/">
            Back to Browse
          </Link>
        </div>
      </div>
    )
  }

  if (!museum) return null

  const full = isFullRecord(museum)
  const website = museum.website

  const fields: Array<[string, unknown]> = [
    ['museum_id', museum.museum_id],
    ['museum_name', museum.museum_name],
    ['alternate_names', museum.alternate_names],
    ['country', museum.country],
    ['state_province', museum.state_province],
    ['city', museum.city],
    ['street_address', museum.street_address],
    ['address_line2', museum.address_line2],
    ['postal_code', museum.postal_code],
    ['primary_domain', museum.primary_domain],
    ['museum_type', museum.museum_type],
    ['status', museum.status],
    ['reputation', museum.reputation],
    ['collection_tier', museum.collection_tier],
    ['time_needed', museum.time_needed],
    ['estimated_visit_minutes', museum.estimated_visit_minutes],
    ['priority_score', museum.priority_score],
    ['open_hours_url', museum.open_hours_url],
    ['tickets_url', museum.tickets_url],
    ['accessibility_url', museum.accessibility_url],
    ['reservation_required', museum.reservation_required],
    ['notes', museum.notes],
    ['confidence', museum.confidence],
    ['data_sources', museum.data_sources],
  ]

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h1 className="text-2xl font-semibold">{museum.museum_name}</h1>
            <div className="mt-1 text-sm text-slate-600">
              {museum.city}, {museum.state_province} • Source: {source ?? '—'}
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
            {website ? (
              <a
                href={website}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
                target="_blank"
                rel="noreferrer"
              >
                Website
              </a>
            ) : null}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-900">Record fields</h2>
        </div>
        <div className="divide-y divide-slate-200">
          {fields.map(([k, v]) => (
            <div key={k} className="grid gap-2 px-4 py-3 md:grid-cols-3">
              <div className="text-sm font-medium text-slate-700">{k}</div>
              <div className="md:col-span-2 text-sm text-slate-900 whitespace-pre-wrap">
                {k.endsWith('_url') && typeof v === 'string' && v ? (
                  <a className="underline" href={v} target="_blank" rel="noreferrer">
                    {v}
                  </a>
                ) : (
                  fieldValue(v)
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <Link className="text-sm text-slate-900 underline" to="/">
          Back to Browse
        </Link>
      </div>
    </div>
  )
}
