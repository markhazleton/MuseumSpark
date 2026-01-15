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

const STRENGTH_MAP: Record<number, string> = {
  5: 'Flagship Collection',
  4: 'Strong Collection',
  3: 'Moderate Representation',
  2: 'Minor Works',
  1: 'None',
}

function Section({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm ${className}`}>
      <div className="border-b border-slate-100 bg-slate-50 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-900">{title}</h2>
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
}

function Field({ label, value, href }: { label: string; value: React.ReactNode; href?: string }) {
  let content = value
  if (content === null || content === undefined) return null
  if (href && typeof content === 'string') {
    content = (
      <a href={href} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
        {content}
      </a>
    )
  }
  return (
    <div className="mb-3 last:mb-0">
      <div className="text-xs font-medium text-slate-500 uppercase">{label}</div>
      <div className="text-sm text-slate-900">{content}</div>
    </div>
  )
}

function RatingBar({ label, value }: { label: string; value: number | null | undefined }) {
  if (!value) return null
  const pct = (value / 5) * 100
  const colorClass = value >= 4 ? 'bg-emerald-500' : value >= 3 ? 'bg-blue-500' : 'bg-slate-300'
  
  return (
    <div className="mb-4">
      <div className="mb-1 flex justify-between text-sm">
        <span className="font-medium text-slate-700">{label}</span>
        <span className="text-slate-500">{STRENGTH_MAP[value] || value}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function ExternalStepLink({ label, url, primary = false }: { label: string; url?: string | null; primary?: boolean }) {
  if (!url) return null
  return (
    <a
      href={url}
      target="_blank"
      rel="noreferrer"
      className={`inline-block w-full rounded-md px-4 py-2 text-center text-sm font-medium transition-colors ${
        primary
          ? 'bg-blue-600 text-white hover:bg-blue-700'
          : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
      }`}
    >
      {label}
    </a>
  )
}

export default function MuseumDetailPage() {
  const { museumId } = useParams()
  const id = museumId ? decodeURIComponent(museumId) : ''
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [museum, setMuseum] = useState<Museum | null>(null)
  const [source, setSource] = useState<'state' | 'index' | null>(null)

  const stateCode = useMemo(() => (id ? deriveStateCodeFromId(id) : null), [id])

  // Reset state when ID changes
  const [prevId, setPrevId] = useState(id)
  if (id !== prevId) {
    setPrevId(id)
    setLoading(true)
    setError(null)
    setMuseum(null)
    setSource(null)
  }

  // Load data
  useEffect(() => {
    let cancelled = false

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
      <div className="flex h-64 items-center justify-center rounded-lg border border-slate-200 bg-white p-6">
        <div className="text-lg text-slate-500 animate-pulse">Loading museum details...</div>
      </div>
    )
  }

  if (error || !museum) {
    return (
      <div className="mx-auto max-w-2xl rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <div className="mb-2 text-xl font-semibold text-red-700">Unable to load museum</div>
        <div className="text-sm text-red-600">{error || 'Museum not found'}</div>
        <div className="mt-6">
          <Link className="rounded-md bg-white px-4 py-2 text-sm font-medium text-slate-900 shadow-sm ring-1 ring-slate-300 hover:bg-slate-50" to="/">
            Back to Browse
          </Link>
        </div>
      </div>
    )
  }

  const isFull = isFullRecord(museum)
  const isArt = museum.primary_domain === 'Art' || museum.museum_type?.toLowerCase().includes('art')
  const hasScores = museum.is_scored || (museum.priority_score !== null && museum.priority_score !== undefined)

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-500">
              <span>{museum.city}, {museum.state_province}</span>
              {museum.country && <span>• {museum.country}</span>}
            </div>
            <h1 className="text-3xl font-bold text-slate-900 sm:text-4xl">{museum.museum_name}</h1>
            {museum.alternate_names && museum.alternate_names.length > 0 && (
              <p className="text-sm text-slate-500">Also known as: {museum.alternate_names.join(', ')}</p>
            )}
            
            <div className="mt-2 flex flex-wrap gap-2">
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${isFull ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>
                {isFull ? 'Complete Record' : 'Draft Record'}
              </span>
              {museum.museum_type && (
                <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-800">
                  {museum.museum_type}
                </span>
              )}
              {typeof museum.reputation === 'number' && (
                <span className="inline-flex items-center rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-800">
                  {REPUTATION_MAP[museum.reputation]} Reputation
                </span>
              )}
              {typeof museum.collection_tier === 'number' && (
                <span className="inline-flex items-center rounded-full bg-violet-100 px-2.5 py-0.5 text-xs font-medium text-violet-800">
                  {COLLECTION_TIER_MAP[museum.collection_tier]}
                </span>
              )}
            </div>
          </div>

          <div className="flex flex-shrink-0 flex-col items-end gap-3">
             {museum.priority_score !== undefined && museum.priority_score !== null && (
               <div className="flex flex-col items-center rounded-lg border border-slate-100 bg-slate-50 p-3 text-center">
                 <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Priority Score</span>
                 <span className="text-3xl font-bold text-slate-900">{museum.priority_score.toFixed(1)}</span>
               </div>
             )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column: 2/3 width */}
        <div className="space-y-6 lg:col-span-2">
          
          <Section title="Overview">
            {museum.notes ? (
              <p className="whitespace-pre-wrap text-slate-700 leading-relaxed">{museum.notes}</p>
            ) : (
              <p className="italic text-slate-400">No description available.</p>
            )}
            
            {museum.visit_priority_notes && (
               <div className="mt-4 rounded-md bg-sky-50 p-4">
                 <h3 className="mb-1 text-sm font-semibold text-sky-900">Why Visit?</h3>
                 <p className="text-sm text-sky-800">{museum.visit_priority_notes}</p>
               </div>
            )}
          </Section>

          {hasScores && isArt && (
            <Section title="Artistic Profile">
              <div className="grid gap-8 md:grid-cols-2">
                <div>
                   <h3 className="mb-3 text-sm font-semibold text-slate-900">Collection Strengths</h3>
                   <RatingBar label="Impressionist" value={museum.impressionist_strength} />
                   <RatingBar label="Modern & Contemporary" value={museum.modern_contemporary_strength} />
                </div>
                <div>
                  <h3 className="mb-3 text-sm font-semibold text-slate-900">Context & Focus</h3>
                  <RatingBar label="Historical Context" value={museum.historical_context_score} />
                  
                  {museum.primary_art && (
                    <div className="mt-4">
                      <div className="text-xs font-medium text-slate-500 uppercase">Primary Focus</div>
                      <div className="text-lg font-medium text-slate-900">{museum.primary_art}</div>
                    </div>
                  )}
                  
                  {museum.score_notes && (
                    <div className="mt-4 text-sm text-slate-600 bg-slate-50 p-3 rounded border border-slate-100">
                      {museum.score_notes}
                    </div>
                  )}
                </div>
              </div>
            </Section>
          )}

          <Section title="Details & Amenities">
            <div className="grid gap-4 sm:grid-cols-2">
               <Field label="Audience Focus" value={museum.audience_focus} />
               <Field label="Topics" value={museum.topics?.join(', ')} />
               <Field label="Best Season to Visit" value={museum.best_season} />
               <Field label="Time Needed" value={museum.time_needed} />
               {museum.estimated_visit_minutes && (
                 <Field label="Est. Minutes" value={`${museum.estimated_visit_minutes} min`} />
               )}
            </div>
            
            {(museum.parking_notes || museum.public_transit_notes) && (
              <div className="mt-4 border-t border-slate-100 pt-4">
                 <div className="grid gap-4 sm:grid-cols-2">
                    <Field label="Parking" value={museum.parking_notes} />
                    <Field label="Public Transit" value={museum.public_transit_notes} />
                 </div>
              </div>
            )}
          </Section>

        </div>

        {/* Right Column: 1/3 width - Sidebar */}
        <div className="space-y-6">
          <Section title="Action & Info">
            <div className="flex flex-col gap-2">
               <ExternalStepLink label="Official Website" url={museum.website} primary />
               <ExternalStepLink label="Tickets / Booking" url={museum.tickets_url} />
               <ExternalStepLink label="Google Maps" url={museum.place_id ? `https://www.google.com/maps/place/?q=place_id:${museum.place_id}` : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${museum.museum_name}, ${museum.city}, ${museum.state_province}`)}`} />
            </div>

            <div className="mt-6 space-y-4 border-t border-slate-100 pt-4">
              <Field label="Hours" value="View Opening Hours" href={museum.open_hours_url} />
              <Field label="Accessibility" value="View Accessibility Info" href={museum.accessibility_url} />
              <Field 
                label="Reservations" 
                value={museum.reservation_required === true ? 'Required' : museum.reservation_required === false ? 'Not Required' : null} 
              />
            </div>
          </Section>

          <Section title="Location">
             <Field label="Address" value={
               <div className="whitespace-pre-line">
                 {[museum.street_address, museum.address_line2, `${museum.city}, ${museum.state_province} ${museum.postal_code || ''}`].filter(Boolean).join('\n')}
               </div>
             } />
             <Field label="Neighborhood" value={museum.neighborhood} />
             <Field label="Region" value={museum.city_region} />
             {museum.nearby_museum_count !== null && museum.nearby_museum_count !== undefined && (
               <div className="mt-2 rounded bg-slate-50 p-2 text-center text-xs text-slate-500">
                 {museum.nearby_museum_count} other museums nearby
               </div>
             )}
          </Section>

          <Section title="Metadata">
             <Field label="Museum ID" value={museum.museum_id} />
             <Field label="Source" value={source === 'state' ? `State File (${stateCode})` : 'Master Index'} />
             <Field label="Confidence Score" value={
               museum.confidence ? (
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((s) => (
                      <div key={s} className={`h-1.5 w-1.5 rounded-full ${s <= (museum.confidence || 0) ? 'bg-slate-600' : 'bg-slate-200'}`} />
                    ))}
                    <span className="ml-1 text-xs text-slate-500">({museum.confidence}/5)</span>
                  </div>
               ) : null
             } />
             <Field label="Data Sources" value={
               museum.data_sources?.map((s, i) => (
                 <div key={i} className="truncate text-xs">{s}</div>
               ))
             } />
             {museum.updated_at && <Field label="Last Updated" value={museum.updated_at} />}
          </Section>

          <div className="text-center">
            <Link className="text-sm font-medium text-slate-600 hover:text-slate-900 hover:underline" to="/">
              &larr; Return to Master List
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
