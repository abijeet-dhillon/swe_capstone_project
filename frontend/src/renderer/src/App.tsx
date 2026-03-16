import { useCallback, useEffect, useMemo, useState } from 'react'
import { filterProjects, type FilteredProject } from './api'
import { StatsCards } from './components/StatsCards'
import { UploadZone } from './components/UploadZone'
import { FilterTabs, type TabKey } from './components/FilterTabs'
import { ProjectTable } from './components/ProjectTable'
import { DetailPanel } from './components/DetailPanel'
import { ToastContainer, type ToastData } from './components/Toast'
import ProjectsView from './ProjectsView'
import SkillsTimeline from './components/SkillsTimeline'

type AppView = 'dashboard' | 'upload' | 'projects' | 'timeline'
type DashboardMode = 'private' | 'public'
type DashboardCategory = 'all' | 'resume' | 'portfolio' | 'timeline' | 'heatmap' | 'showcase'

type DashboardCard = {
  id: string
  title: string
  category: Exclude<DashboardCategory, 'all'>
  status: 'ready' | 'coming-soon'
  description: string
  icon: string
}

const dashboardCards: DashboardCard[] = [
  {
    id: 'resume',
    title: 'One-Page Resume',
    category: 'resume',
    status: 'ready',
    description: 'Generate and review a concise one-page resume from analyzed projects.',
    icon: '📄',
  },
  {
    id: 'portfolio',
    title: 'Web Portfolio',
    category: 'portfolio',
    status: 'ready',
    description: 'Assemble project summaries and evidence into portfolio-ready sections.',
    icon: '🌐',
  },
  {
    id: 'timeline',
    title: 'Skills Timeline',
    category: 'timeline',
    status: 'ready',
    description: 'Track learning progression and depth across projects over time.',
    icon: '📈',
  },
  {
    id: 'heatmap',
    title: 'Project Activity Heatmap',
    category: 'heatmap',
    status: 'coming-soon',
    description: 'Visualize activity intensity and productivity trends.',
    icon: '🔥',
  },
  {
    id: 'showcase',
    title: 'Top 3 Project Showcase',
    category: 'showcase',
    status: 'coming-soon',
    description: 'Highlight top projects and evolution of key changes.',
    icon: '🏆',
  },
]

function NavIcon({ name }: { name: string }) {
  const size = 18
  const props = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }
  switch (name) {
    case 'dashboard':
      return <svg {...props}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
    case 'upload':
      return <svg {...props}><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    case 'projects':
      return <svg {...props}><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
    case 'timeline':
      return <svg {...props}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
    default:
      return null
  }
}

const NAV_ITEMS: { view: AppView; label: string }[] = [
  { view: 'dashboard', label: 'Dashboard' },
  { view: 'upload', label: 'Upload' },
  { view: 'projects', label: 'Projects' },
  { view: 'timeline', label: 'Timeline' },
]

const PAGE_META: Record<AppView, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Dashboard',
    subtitle: 'Your workspace overview and quick actions',
  },
  upload: {
    title: 'Upload & Analyze',
    subtitle: 'Upload a .zip file to analyze your projects',
  },
  projects: {
    title: 'Projects',
    subtitle: 'Search, filter, and explore your analyzed projects',
  },
  timeline: {
    title: 'Skills Timeline',
    subtitle: 'Track your learning progression over time',
  },
}

let toastId = 0

function App() {
  const [view, setView] = useState<AppView>('dashboard')
  const [projects, setProjects] = useState<FilteredProject[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<TabKey>('all')
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
  const [toasts, setToasts] = useState<ToastData[]>([])
  const [mode, setMode] = useState<DashboardMode>('private')
  const [cardQuery, setCardQuery] = useState('')
  const [cardCategory, setCardCategory] = useState<DashboardCategory>('all')
  const [timelineRefreshNonce, setTimelineRefreshNonce] = useState(0)
  const [timelineBusy, setTimelineBusy] = useState(false)

  const loadProjects = useCallback(async () => {
    setLoading(true)
    try {
      const res = await filterProjects({ limit: 100, offset: 0 })
      setProjects(res.projects)
    } catch {
      setProjects([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  const addToast = useCallback((title: string, type: ToastData['type'] = 'success', subtitle?: string) => {
    setToasts((prev) => [...prev, { id: ++toastId, title, type, subtitle }])
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const handleUploadComplete = useCallback(
    (msg: string) => {
      const isError = msg.toLowerCase().includes('fail') || msg.toLowerCase().includes('error')
      addToast(isError ? 'Upload failed' : 'Upload queued!', isError ? 'error' : 'success', msg)
      if (!isError) loadProjects()
    },
    [addToast, loadProjects],
  )

  const filteredProjects = useMemo(() => {
    let list = projects
    if (activeTab === 'solo') list = list.filter((p) => !p.is_collaborative)
    if (activeTab === 'collab') list = list.filter((p) => p.is_collaborative)
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase()
      list = list.filter(
        (p) =>
          p.project_name.toLowerCase().includes(q) ||
          p.tagline?.toLowerCase().includes(q) ||
          p.description?.toLowerCase().includes(q),
      )
    }
    return list
  }, [projects, activeTab, searchQuery])

  const filteredCards = useMemo(() => {
    const lowered = cardQuery.trim().toLowerCase()
    return dashboardCards.filter((card) => {
      const matchesCategory = cardCategory === 'all' || card.category === cardCategory
      const matchesQuery =
        lowered.length === 0 ||
        card.title.toLowerCase().includes(lowered) ||
        card.description.toLowerCase().includes(lowered)
      return matchesCategory && matchesQuery
    })
  }, [cardCategory, cardQuery])

  const meta = PAGE_META[view]

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand__icon">RF</div>
          <div>
            <h1>ResumeForge</h1>
            <span>Artifact Miner</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.view}
              className={`nav-item ${view === item.view ? 'is-active' : ''}`}
              onClick={() => {
                setView(item.view)
                setSelectedProjectId(null)
              }}
            >
              <span className="nav-icon"><NavIcon name={item.view} /></span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p>Team 14 — COSC 499</p>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className={`main-content ${selectedProjectId !== null ? 'main-content--with-panel' : ''}`}>
        <div className="page-header">
          <div className="page-header__left">
            <h2>{meta.title}</h2>
            <p>{meta.subtitle}</p>
          </div>
          {view === 'dashboard' && (
            <div className="page-header__right">
              <input
                className="input page-header__search"
                type="text"
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <span className="pill info">{projects.length} projects</span>
            </div>
          )}
          {view === 'timeline' && (
            <div className="page-header__right">
              <button
                className="pv-view-btn"
                type="button"
                aria-label="Refresh skill catalog"
                title="Refresh skill catalog"
                onClick={() => setTimelineRefreshNonce((prev) => prev + 1)}
                disabled={timelineBusy}
              >
                ↻
              </button>
            </div>
          )}
        </div>

        <div className="page-body">
          {view === 'dashboard' ? (
            <>
              <StatsCards projects={projects} />

              {/* ── Quick Actions — Feature Cards ── */}
              <div className="card">
                <div className="features-header">
                  <div className="features-header__left">
                    <h3>Quick Actions</h3>
                    <div className="mode-toggle" role="group" aria-label="Mode Toggle">
                      <button
                        className={`mode-btn ${mode === 'private' ? 'is-active' : ''}`}
                        onClick={() => setMode('private')}
                        aria-pressed={mode === 'private'}
                      >
                        Private
                      </button>
                      <button
                        className={`mode-btn ${mode === 'public' ? 'is-active' : ''}`}
                        onClick={() => setMode('public')}
                        aria-pressed={mode === 'public'}
                      >
                        Public
                      </button>
                    </div>
                    <span className="mode-hint">
                      {mode === 'private'
                        ? 'Customization controls are enabled.'
                        : 'Customization controls are disabled in public mode.'}
                    </span>
                  </div>
                  <div className="features-header__right">
                    <input
                      className="input"
                      type="text"
                      placeholder="Search sections..."
                      value={cardQuery}
                      onChange={(e) => setCardQuery(e.target.value)}
                      aria-label="Search sections"
                    />
                    <select
                      className="select"
                      value={cardCategory}
                      onChange={(e) => setCardCategory(e.target.value as DashboardCategory)}
                      aria-label="Filter category"
                    >
                      <option value="all">All Categories</option>
                      <option value="resume">Resume</option>
                      <option value="portfolio">Portfolio</option>
                      <option value="timeline">Timeline</option>
                      <option value="heatmap">Heatmap</option>
                      <option value="showcase">Showcase</option>
                    </select>
                  </div>
                </div>

                <section className="cards-grid" aria-label="dashboard-cards">
                  {filteredCards.length === 0 ? (
                    <p className="empty-state">No sections match your search or filter.</p>
                  ) : (
                    filteredCards.map((card) => (
                      <article className="feature-card" key={card.id}>
                        <div className="feature-head">
                          <h4>
                            <span style={{ marginRight: 8 }}>{card.icon}</span>
                            {card.title}
                          </h4>
                          <span className={`pill ${card.status}`}>
                            {card.status === 'ready' ? 'Ready' : 'Coming Soon'}
                          </span>
                        </div>
                        <p>{card.description}</p>
                        <button
                          className="action-btn"
                          disabled={mode === 'public' || card.status === 'coming-soon'}
                          onClick={() => (card.id === 'timeline' ? setView('timeline') : undefined)}
                        >
                          {card.id === 'timeline' ? 'Open Timeline' : 'Customize'}
                        </button>
                      </article>
                    ))
                  )}
                </section>
              </div>

              {/* ── Upload ── */}
              <UploadZone onUploadComplete={handleUploadComplete} />

              {/* ── Project List ── */}
              <FilterTabs
                active={activeTab}
                onChange={setActiveTab}
                projects={projects}
              />
              {loading ? (
                <p className="empty-state">Loading projects...</p>
              ) : (
                <ProjectTable
                  projects={filteredProjects}
                  selectedId={selectedProjectId}
                  onSelect={setSelectedProjectId}
                />
              )}
            </>
          ) : view === 'upload' ? (
            <UploadZone onUploadComplete={handleUploadComplete} />
          ) : view === 'projects' ? (
            <ProjectsView />
          ) : (
            <SkillsTimeline
              refreshNonce={timelineRefreshNonce}
              onBusyChange={setTimelineBusy}
            />
          )}
        </div>

        <footer className="app-footer">
          <p>COSC 499 — Digital Work Artifact Miner</p>
        </footer>
      </main>

      {/* ── Detail Panel ── */}
      {selectedProjectId !== null && (
        <DetailPanel
          projectId={selectedProjectId}
          onClose={() => setSelectedProjectId(null)}
        />
      )}

      {/* ── Toasts ── */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}

export default App
