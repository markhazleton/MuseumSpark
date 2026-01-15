import { useEffect, useState } from 'react'
import { loadProgress } from '../lib/api'
import type { ProgressIndex } from '../lib/types'

export default function ProgressPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<ProgressIndex | null>(null)

  useEffect(() => {
    let cancelled = false
    loadProgress()
      .then((p) => {
        if (cancelled) return
        setProgress(p)
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

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <div className="text-slate-700">Loading progress…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-white p-6">
        <div className="font-semibold text-red-700">Failed to load progress</div>
        <div className="mt-2 text-sm text-slate-700">{error}</div>
      </div>
    )
  }

  if (!progress) {
    return null
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h1 className="text-xl font-semibold">Dataset progress</h1>
        <div className="mt-2 text-sm text-slate-600">Generated at {progress.generated_at}</div>

        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="text-xs font-semibold text-slate-600">Total</div>
            <div className="mt-1 text-2xl font-semibold">{progress.total_museums.toLocaleString()}</div>
          </div>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
            <div className="text-xs font-semibold text-emerald-700">FULL</div>
            <div className="mt-1 text-2xl font-semibold text-emerald-900">{progress.full.toLocaleString()}</div>
          </div>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
            <div className="text-xs font-semibold text-amber-700">Placeholder</div>
            <div className="mt-1 text-2xl font-semibold text-amber-900">
              {progress.placeholder.toLocaleString()}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <div className="text-xs font-semibold text-slate-600">FULL %</div>
            <div className="mt-1 text-2xl font-semibold">{progress.full_pct}%</div>
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-900">By state/province</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left font-semibold text-slate-700">State</th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700">Total</th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700">FULL</th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700">Placeholder</th>
                <th className="px-4 py-2 text-right font-semibold text-slate-700">FULL %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {Object.entries(progress.by_state).map(([state, row]) => {
                const pct = row.total ? Math.round((row.full / row.total) * 10000) / 100 : 0
                return (
                  <tr key={state} className="hover:bg-slate-50">
                    <td className="px-4 py-2 font-medium text-slate-900">{state}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{row.total}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{row.full}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{row.placeholder}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{pct}%</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
