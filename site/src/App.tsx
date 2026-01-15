import { Link, NavLink, Route, Routes } from 'react-router-dom'
import BrowsePage from './pages/BrowsePage'
import MuseumDetailPage from './pages/MuseumDetailPage'
import ProgressPage from './pages/ProgressPage'
import HomePage from './pages/HomePage'
import RoadmapPage from './pages/RoadmapPage'

function Nav() {
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    [
      'rounded-md px-3 py-2 text-sm font-medium',
      isActive ? 'bg-slate-900 text-white' : 'text-slate-700 hover:bg-slate-100',
    ].join(' ')

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold text-slate-900 hover:text-blue-700">
          <span className="text-xl">🏛️</span> MuseumSpark
        </Link>
        <nav className="flex items-center gap-1 md:gap-2">
          <NavLink to="/" className={navLinkClass} end>
            Home
          </NavLink>
          <NavLink to="/browse" className={navLinkClass}>
            Browse
          </NavLink>
          <NavLink to="/roadmap" className={navLinkClass}>
            Roadmap
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
      <main className="mx-auto max-w-6xl px-4 py-6 md:py-10">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/browse" element={<BrowsePage />} />
          <Route path="/roadmap" element={<RoadmapPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/museums/:museumId" element={<MuseumDetailPage />} />
          <Route
            path="*"
            element={
              <div className="rounded-lg border border-slate-200 bg-white p-6 text-center">
                <h1 className="text-xl font-semibold">404 - Not found</h1>
                <p className="mt-2 text-slate-700">The page you are looking for doesn't exist.</p>
                <div className="mt-4">
                  <Link to="/" className="text-blue-600 hover:underline">Return Home</Link>
                </div>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  )
}
