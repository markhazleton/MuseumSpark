import { Link, NavLink, Route, Routes } from 'react-router-dom'
import BrowsePage from './pages/BrowsePage'
import MuseumDetailPage from './pages/MuseumDetailPage'
import ProgressPage from './pages/ProgressPage'

function Nav() {
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    [
      'rounded-md px-3 py-2 text-sm font-medium',
      isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100',
    ].join(' ')

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-semibold text-slate-900">
          MuseumSpark
        </Link>
        <nav className="flex items-center gap-2">
          <NavLink to="/" className={navLinkClass} end>
            Browse
          </NavLink>
          <NavLink to="/progress" className={navLinkClass}>
            Progress
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <div className="min-h-dvh bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<BrowsePage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/museums/:museumId" element={<MuseumDetailPage />} />
          <Route
            path="*"
            element={
              <div className="rounded-lg border border-slate-200 bg-white p-6">
                <h1 className="text-xl font-semibold">Not found</h1>
                <p className="mt-2 text-slate-700">That page doesn’t exist.</p>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  )
}
