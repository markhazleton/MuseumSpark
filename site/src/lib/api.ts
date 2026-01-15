import type { AllMuseumsIndex, ProgressIndex, StateFile } from './types'

function assetUrl(pathname: string): string {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
  const path = pathname.replace(/^\//, '')
  return `${base}${path}`
}

async function fetchJson<T>(pathname: string): Promise<T> {
  const url = assetUrl(pathname)
  const resp = await fetch(url)
  if (!resp.ok) {
    throw new Error(`Fetch failed (${resp.status}) for ${pathname}`)
  }
  return (await resp.json()) as T
}

export function loadAllMuseums(): Promise<AllMuseumsIndex> {
  return fetchJson<AllMuseumsIndex>('data/index/all-museums.json')
}

export function loadProgress(): Promise<ProgressIndex> {
  return fetchJson<ProgressIndex>('data/index/progress.json')
}

export function loadStateFile(stateCode: string): Promise<StateFile> {
  const code = stateCode.toUpperCase()
  return fetchJson<StateFile>(`data/states/${code}.json`)
}
