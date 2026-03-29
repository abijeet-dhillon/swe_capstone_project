import { useCallback, useEffect, useMemo, useState } from 'react'
import { filterProjects, generateResumePdf, generatePortfolioSite, type FilteredProject, type ResumeEducationInput } from './api'
import { StatsCards } from './components/StatsCards'
import { UploadZone } from './components/UploadZone'
import { FilterTabs, type TabKey } from './components/FilterTabs'
import { ProjectTable } from './components/ProjectTable'
import { DetailPanel } from './components/DetailPanel'
import { ToastContainer, type ToastData } from './components/Toast'
import ProjectsView from './ProjectsView'
import SkillsTimeline from './components/SkillsTimeline'
import { ProfileView } from './components/ProfileView'

type AppView = 'dashboard' | 'upload' | 'projects' | 'timeline' | 'profile'
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
  // {
  //   id: 'heatmap',
  //   title: 'Project Activity Heatmap',
  //   category: 'heatmap',
  //   status: 'coming-soon',
  //   description: 'Visualize activity intensity and productivity trends.',
  //   icon: '🔥',
  // },
  // {
  //   id: 'showcase',
  //   title: 'Top 3 Project Showcase',
  //   category: 'showcase',
  //   status: 'coming-soon',
  //   description: 'Highlight top projects and evolution of key changes.',
  //   icon: '🏆',
  // },
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
    case 'profile':
      return <svg {...props}><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
    default:
      return null
  }
}

const NAV_ITEMS: { view: AppView; label: string }[] = [
  { view: 'dashboard', label: 'Dashboard' },
  { view: 'upload', label: 'Upload' },
  { view: 'projects', label: 'Projects' },
  { view: 'timeline', label: 'Timeline' },
  { view: 'profile', label: 'Profile' },
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
  profile: {
    title: 'Profile',
    subtitle: 'Manage your personal information and developer identity',
  },
}

let toastId = 0

const blankEducation = (): ResumeEducationInput => ({
  school: '',
  degree: '',
  location: '',
  start_date: '',
  end_date: '',
  is_current: false,
  expected_graduation: '',
})

function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    if (theme === 'dark') document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  }, [theme])

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
  const [resumeModalOpen, setResumeModalOpen] = useState(false)
  const [resumeProjectIds, setResumeProjectIds] = useState<number[]>([])
  const [resumeOwnerName, setResumeOwnerName] = useState('')
  const [resumePhone, setResumePhone] = useState('')
  const [resumeEmail, setResumeEmail] = useState('')
  const [resumeLinkedinUrl, setResumeLinkedinUrl] = useState('')
  const [resumeLinkedinLabel, setResumeLinkedinLabel] = useState('')
  const [resumeGithubUrl, setResumeGithubUrl] = useState('')
  const [resumeGithubLabel, setResumeGithubLabel] = useState('')
  const [resumeEducation, setResumeEducation] = useState<ResumeEducationInput[]>([blankEducation()])
  const [resumeDownloadUrl, setResumeDownloadUrl] = useState<string | null>(null)
  const [resumeFilename, setResumeFilename] = useState('resume.pdf')
  const [resumeGenerating, setResumeGenerating] = useState(false)
  const [resumeError, setResumeError] = useState('')
  const [timelineRefreshNonce, setTimelineRefreshNonce] = useState(0)
  const [timelineBusy, setTimelineBusy] = useState(false)

  const [portfolioModalOpen, setPortfolioModalOpen] = useState(false)
  const [portfolioProjectIds, setPortfolioProjectIds] = useState<number[]>([])
  const [portfolioName, setPortfolioName] = useState('')
  const [portfolioTitle, setPortfolioTitle] = useState('Full-Stack Developer')
  const [portfolioBio, setPortfolioBio] = useState('')
  const [portfolioEmail, setPortfolioEmail] = useState('')
  const [portfolioLocation, setPortfolioLocation] = useState('')
  const [portfolioGithubUrl, setPortfolioGithubUrl] = useState('')
  const [portfolioLinkedinUrl, setPortfolioLinkedinUrl] = useState('')
  const [portfolioYoe, setPortfolioYoe] = useState('')
  const [portfolioOss, setPortfolioOss] = useState('')
  const [portfolioGenerating, setPortfolioGenerating] = useState(false)
  const [portfolioError, setPortfolioError] = useState('')
  const [portfolioUrl, setPortfolioUrl] = useState<string | null>(null)

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

  const resetResumeModal = useCallback(() => {
    setResumeModalOpen(false)
    setResumeProjectIds([])
    setResumeOwnerName('')
    setResumePhone('')
    setResumeEmail('')
    setResumeLinkedinUrl('')
    setResumeLinkedinLabel('')
    setResumeGithubUrl('')
    setResumeGithubLabel('')
    setResumeEducation([blankEducation()])
    setResumeError('')
    setResumeGenerating(false)
    setResumeDownloadUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return null
    })
    setResumeFilename('resume.pdf')
  }, [])

  const handleUploadComplete = useCallback(
    (msg: string) => {
      const isError = msg.toLowerCase().includes('fail') || msg.toLowerCase().includes('error')
      addToast(isError ? 'Upload failed' : 'Upload queued!', isError ? 'error' : 'success', msg)
      if (!isError) loadProjects()
    },
    [addToast, loadProjects],
  )

  const handleResumeCardClick = useCallback(() => {
    setResumeError('')
    if (projects.length === 0) {
      addToast('No projects available', 'error', 'Upload and analyze a ZIP before generating a resume.')
      setView('upload')
      return
    }
    setResumeProjectIds((prev) => (prev.length > 0 ? prev : projects.slice(0, 1).map((project) => project.project_info_id)))
    setResumeModalOpen(true)
  }, [addToast, projects])

  const handleGenerateResumePdf = useCallback(async () => {
    if (resumeProjectIds.length === 0 || !resumeOwnerName.trim()) {
      setResumeError('Choose at least one project and enter the resume owner name.')
      return
    }
    setResumeGenerating(true)
    setResumeError('')
    try {
      const { blob, filename } = await generateResumePdf({
        resume_owner_name: resumeOwnerName.trim(),
        project_ids: resumeProjectIds,
        phone: resumePhone.trim(),
        email: resumeEmail.trim(),
        linkedin_url: resumeLinkedinUrl.trim(),
        linkedin_label: resumeLinkedinLabel.trim(),
        github_url: resumeGithubUrl.trim(),
        github_label: resumeGithubLabel.trim(),
        education: resumeEducation
          .map((entry) => ({
            school: entry.school?.trim() || '',
            degree: entry.degree?.trim() || '',
            location: entry.location?.trim() || '',
            start_date: entry.start_date?.trim() || '',
            end_date: entry.end_date?.trim() || '',
            is_current: Boolean(entry.is_current),
            expected_graduation: entry.expected_graduation?.trim() || '',
          }))
          .filter((entry) => entry.school),
      })
      setResumeDownloadUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return URL.createObjectURL(blob)
      })
      setResumeFilename(filename)
      addToast('Resume ready', 'success', 'Your PDF is ready to download.')
    } catch (e) {
      setResumeError(e instanceof Error ? e.message : 'Failed to generate resume PDF')
    } finally {
      setResumeGenerating(false)
    }
  }, [
    addToast,
    resumeEducation,
    resumeEmail,
    resumeGithubLabel,
    resumeGithubUrl,
    resumeLinkedinLabel,
    resumeLinkedinUrl,
    resumeOwnerName,
    resumePhone,
    resumeProjectIds,
  ])

  const toggleResumeProject = useCallback((projectId: number) => {
    setResumeProjectIds((prev) =>
      prev.includes(projectId)
        ? prev.filter((id) => id !== projectId)
        : [...prev, projectId],
    )
  }, [])

  const updateEducationField = useCallback(
    (index: number, field: keyof ResumeEducationInput, value: string | boolean) => {
      setResumeEducation((prev) =>
        prev.map((entry, currentIndex) =>
          currentIndex === index ? { ...entry, [field]: value } : entry,
        ),
      )
    },
    [],
  )

  const addEducationEntry = useCallback(() => {
    setResumeEducation((prev) => [...prev, blankEducation()])
  }, [])

  const removeEducationEntry = useCallback((index: number) => {
    setResumeEducation((prev) => (prev.length === 1 ? [blankEducation()] : prev.filter((_, currentIndex) => currentIndex !== index)))
  }, [])

  const resetPortfolioModal = useCallback(() => {
    setPortfolioModalOpen(false)
    setPortfolioProjectIds([])
    setPortfolioName('')
    setPortfolioTitle('Full-Stack Developer')
    setPortfolioBio('')
    setPortfolioEmail('')
    setPortfolioLocation('')
    setPortfolioGithubUrl('')
    setPortfolioLinkedinUrl('')
    setPortfolioYoe('')
    setPortfolioOss('')
    setPortfolioError('')
    setPortfolioGenerating(false)
    setPortfolioUrl(null)
  }, [])

  const handlePortfolioCardClick = useCallback(() => {
    setPortfolioError('')
    if (projects.length === 0) {
      addToast('No projects available', 'error', 'Upload and analyze a ZIP before generating a portfolio.')
      setView('upload')
      return
    }
    setPortfolioProjectIds((prev) => (prev.length > 0 ? prev : projects.slice(0, 2).map((p) => p.project_info_id)))
    setPortfolioModalOpen(true)
  }, [addToast, projects])

  const togglePortfolioProject = useCallback((projectId: number) => {
    setPortfolioProjectIds((prev) =>
      prev.includes(projectId)
        ? prev.filter((id) => id !== projectId)
        : prev.length >= 4 ? prev : [...prev, projectId],
    )
  }, [])

  const handleGeneratePortfolio = useCallback(async () => {
    if (portfolioProjectIds.length < 2) {
      setPortfolioError('Select at least 2 projects.')
      return
    }
    if (!portfolioName.trim()) {
      setPortfolioError('Enter your name.')
      return
    }
    setPortfolioGenerating(true)
    setPortfolioError('')
    try {
      const res = await generatePortfolioSite({
        name: portfolioName.trim(),
        title: portfolioTitle.trim() || 'Full-Stack Developer',
        bio: portfolioBio.trim(),
        email: portfolioEmail.trim(),
        location: portfolioLocation.trim(),
        github_url: portfolioGithubUrl.trim(),
        linkedin_url: portfolioLinkedinUrl.trim(),
        years_experience: portfolioYoe.trim(),
        projects_completed: String(projects.length),
        open_source_contributions: portfolioOss.trim(),
        project_ids: portfolioProjectIds,
      })
      setPortfolioUrl(res.url)
      addToast('Portfolio ready', 'success', res.message || 'Your portfolio is live at localhost:3000')
    } catch (e) {
      setPortfolioError(e instanceof Error ? e.message : 'Failed to generate portfolio')
    } finally {
      setPortfolioGenerating(false)
    }
  }, [addToast, portfolioBio, portfolioEmail, portfolioGithubUrl, portfolioLinkedinUrl, portfolioLocation, portfolioName, portfolioOss, portfolioProjectIds, portfolioTitle, portfolioYoe, projects.length])

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
  const resumeSelectedProjects = projects.filter((project) => resumeProjectIds.includes(project.project_info_id))
  const portfolioSelectedProjects = projects.filter((project) => portfolioProjectIds.includes(project.project_info_id))
  const canGenerateResume = resumeProjectIds.length > 0 && Boolean(resumeOwnerName.trim())
  const canGeneratePortfolio = portfolioProjectIds.length >= 2 && Boolean(portfolioName.trim())

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand__icon">RF</div>
          <div>
            <h1>ResumeForge</h1>
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

        <div className="sidebar-footer" style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center' }}>
          <button
            className="theme-toggle"
            onClick={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}
            title="Toggle theme"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
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
                      {/* <option value="heatmap">Heatmap</option> */}
                      {/* <option value="showcase">Showcase</option> */}
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
                          onClick={() => {
                            if (card.id === 'timeline') {
                              setView('timeline')
                              return
                            }
                            if (card.id === 'resume') {
                              handleResumeCardClick()
                              return
                            }
                            if (card.id === 'portfolio') {
                              handlePortfolioCardClick()
                              return
                            }
                          }}
                        >
                          {card.id === 'timeline' ? 'Open Timeline' : card.id === 'resume' ? 'Generate Resume' : card.id === 'portfolio' ? 'Generate Portfolio' : 'Customize'}
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
          ) : view === 'timeline' ? (
            <SkillsTimeline
              refreshNonce={timelineRefreshNonce}
              onBusyChange={setTimelineBusy}
            />
          ) : (
            <ProfileView onToast={addToast} />
          )}
        </div>

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

      {resumeModalOpen && (
        <div className="skill-modal" role="dialog" aria-modal="true" aria-labelledby="resume-modal-title" onClick={resetResumeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-header__copy">
                <span className="modal-category">Resume</span>
                <h2 id="resume-modal-title">Generate One-Page Resume</h2>
                <p className="modal-description">
                  Select the projects to include, fill in the details you want on the resume, then generate the PDF.
                </p>
              </div>
              <button className="close" type="button" onClick={resetResumeModal} aria-label="Close">
                ×
              </button>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Projects</h4>
                  <p className="modal-helper">Choose the work samples you want highlighted on this one-page resume.</p>
                </div>
                <span className="pill info">{resumeProjectIds.length} selected</span>
              </div>
              <div className="modal-project-list">
                {projects.map((project) => (
                  <label
                    key={project.project_info_id}
                    className={`modal-project-option ${resumeProjectIds.includes(project.project_info_id) ? 'is-selected' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={resumeProjectIds.includes(project.project_info_id)}
                      onChange={() => toggleResumeProject(project.project_info_id)}
                    />
                    <span>{project.project_name}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Owner</h4>
                  <p className="modal-helper">Use the exact name you want displayed in the PDF heading.</p>
                </div>
              </div>
              <div className="modal-form-grid modal-form-grid--two">
                <label className="modal-field">
                  <span>Resume owner name</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Jane Doe"
                    value={resumeOwnerName}
                    onChange={(e) => setResumeOwnerName(e.target.value)}
                  />
                </label>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Contact</h4>
                  <p className="modal-helper">Optional, but useful for a resume that is ready to share immediately.</p>
                </div>
              </div>
              <div className="modal-form-grid modal-form-grid--two">
                <label className="modal-field">
                  <span>Phone number</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="Phone number"
                    value={resumePhone}
                    onChange={(e) => setResumePhone(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>Email address</span>
                  <input
                    className="input"
                    type="email"
                    placeholder="Email address"
                    value={resumeEmail}
                    onChange={(e) => setResumeEmail(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>LinkedIn URL</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="LinkedIn URL"
                    value={resumeLinkedinUrl}
                    onChange={(e) => setResumeLinkedinUrl(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>LinkedIn label</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="LinkedIn label (optional)"
                    value={resumeLinkedinLabel}
                    onChange={(e) => setResumeLinkedinLabel(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>GitHub URL</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="GitHub URL"
                    value={resumeGithubUrl}
                    onChange={(e) => setResumeGithubUrl(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>GitHub label</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="GitHub label (optional)"
                    value={resumeGithubLabel}
                    onChange={(e) => setResumeGithubLabel(e.target.value)}
                  />
                </label>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Education</h4>
                  <p className="modal-helper">Add one or more schools exactly as you want them printed.</p>
                </div>
                <button className="action-btn" type="button" onClick={addEducationEntry}>
                  Add Education
                </button>
              </div>
              <div className="modal-education-list">
                {resumeEducation.map((entry, index) => (
                  <div key={index} className="modal-education-card">
                    <div className="modal-form-grid modal-form-grid--two">
                      <label className="modal-field">
                        <span>School</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="University or school"
                          value={entry.school ?? ''}
                          onChange={(e) => updateEducationField(index, 'school', e.target.value)}
                        />
                      </label>
                      <label className="modal-field">
                        <span>Degree or program</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="Degree or program"
                          value={entry.degree ?? ''}
                          onChange={(e) => updateEducationField(index, 'degree', e.target.value)}
                        />
                      </label>
                      <label className="modal-field">
                        <span>Location</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="Location"
                          value={entry.location ?? ''}
                          onChange={(e) => updateEducationField(index, 'location', e.target.value)}
                        />
                      </label>
                      <label className="modal-field">
                        <span>From</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="Sep 2022"
                          value={entry.start_date ?? ''}
                          onChange={(e) => updateEducationField(index, 'start_date', e.target.value)}
                        />
                      </label>
                      <label className="modal-field">
                        <span>To</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="May 2026"
                          value={entry.end_date ?? ''}
                          disabled={Boolean(entry.is_current)}
                          onChange={(e) => updateEducationField(index, 'end_date', e.target.value)}
                        />
                      </label>
                    </div>
                    <label className="modal-checkbox">
                      <input
                        type="checkbox"
                        checked={Boolean(entry.is_current)}
                        onChange={(e) => updateEducationField(index, 'is_current', e.target.checked)}
                      />
                      <span>I am still studying here</span>
                    </label>
                    {entry.is_current && (
                      <label className="modal-field">
                        <span>Expected graduation</span>
                        <input
                          className="input"
                          type="text"
                          placeholder="Expected graduation (e.g. May 2027)"
                          value={entry.expected_graduation ?? ''}
                          onChange={(e) => updateEducationField(index, 'expected_graduation', e.target.value)}
                        />
                      </label>
                    )}
                    <div className="modal-education-actions">
                      <button className="reset-btn" type="button" onClick={() => removeEducationEntry(index)}>
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {resumeError && (
              <p className="filter-error">{resumeError}</p>
            )}

            <div className="modal-footer">
              <div className="modal-footer__summary">
                <strong>{resumeSelectedProjects.length}</strong>
                <span>{resumeSelectedProjects.length === 1 ? 'project selected' : 'projects selected'}</span>
                {!canGenerateResume && <span className="modal-footer__hint">Select a project and enter the resume owner name.</span>}
              </div>
              <div className="modal-footer__actions">
                <button className="reset-btn" type="button" onClick={resetResumeModal}>
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  type="button"
                  onClick={handleGenerateResumePdf}
                  disabled={resumeGenerating}
                >
                  {resumeGenerating ? 'Generating…' : 'Generate PDF'}
                </button>
              </div>
              {resumeDownloadUrl && (
                <a
                  className="btn-primary"
                  href={resumeDownloadUrl}
                  download={resumeFilename}
                >
                  Download PDF
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {portfolioModalOpen && (
        <div className="skill-modal" role="dialog" aria-modal="true" aria-labelledby="portfolio-modal-title" onClick={resetPortfolioModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-header__copy">
                <span className="modal-category">Portfolio</span>
                <h2 id="portfolio-modal-title">Generate Web Portfolio</h2>
                <p className="modal-description">
                  Pick 2 to 4 projects, add the profile details you want displayed, then generate your portfolio website.
                </p>
              </div>
              <button className="close" type="button" onClick={resetPortfolioModal} aria-label="Close">
                ×
              </button>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Projects</h4>
                  <p className="modal-helper">Choose between two and four projects to feature on the portfolio page.</p>
                </div>
                <span className="pill info">{portfolioProjectIds.length}/4 selected</span>
              </div>
              <div className="modal-project-list">
                {projects.map((project) => (
                  <label
                    key={project.project_info_id}
                    className={`modal-project-option ${portfolioProjectIds.includes(project.project_info_id) ? 'is-selected' : ''}`}
                    style={{
                      opacity: !portfolioProjectIds.includes(project.project_info_id) && portfolioProjectIds.length >= 4 ? 0.55 : 1,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={portfolioProjectIds.includes(project.project_info_id)}
                      onChange={() => togglePortfolioProject(project.project_info_id)}
                      disabled={!portfolioProjectIds.includes(project.project_info_id) && portfolioProjectIds.length >= 4}
                    />
                    <span>{project.project_name}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Profile</h4>
                  <p className="modal-helper">These details become the hero section of your generated site.</p>
                </div>
              </div>
              <div className="modal-form-grid modal-form-grid--two">
                <label className="modal-field">
                  <span>Name</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Jane Doe"
                    value={portfolioName}
                    onChange={(e) => setPortfolioName(e.target.value)}
                  />
                </label>
                <label className="modal-field">
                  <span>Title</span>
                  <input
                    className="input"
                    type="text"
                    placeholder="e.g. Full-Stack Developer"
                    value={portfolioTitle}
                    onChange={(e) => setPortfolioTitle(e.target.value)}
                  />
                </label>
                <label className="modal-field modal-field--full">
                  <span>About me</span>
                  <textarea
                    className="input"
                    placeholder="Write a short bio about yourself..."
                    value={portfolioBio}
                    onChange={(e) => setPortfolioBio(e.target.value)}
                    rows={3}
                  />
                </label>
              </div>
            </div>

            <div className="modal-section">
              <div className="modal-section__heading">
                <div>
                  <h4>Links & highlights</h4>
                  <p className="modal-helper">These fields are optional and can make the generated portfolio feel more complete.</p>
                </div>
              </div>
              <div className="modal-form-grid modal-form-grid--two">
                <label className="modal-field">
                  <span>Email address</span>
                  <input className="input" type="email" placeholder="Email address" value={portfolioEmail} onChange={(e) => setPortfolioEmail(e.target.value)} />
                </label>
                <label className="modal-field">
                  <span>Location</span>
                  <input className="input" type="text" placeholder="Location (e.g. Vancouver, BC)" value={portfolioLocation} onChange={(e) => setPortfolioLocation(e.target.value)} />
                </label>
                <label className="modal-field">
                  <span>GitHub URL</span>
                  <input className="input" type="text" placeholder="GitHub URL" value={portfolioGithubUrl} onChange={(e) => setPortfolioGithubUrl(e.target.value)} />
                </label>
                <label className="modal-field">
                  <span>LinkedIn URL</span>
                  <input className="input" type="text" placeholder="LinkedIn URL" value={portfolioLinkedinUrl} onChange={(e) => setPortfolioLinkedinUrl(e.target.value)} />
                </label>
                <label className="modal-field">
                  <span>Years of experience</span>
                  <input className="input" type="text" placeholder="e.g. 4+" value={portfolioYoe} onChange={(e) => setPortfolioYoe(e.target.value)} />
                </label>
                <label className="modal-field">
                  <span>Open source contributions</span>
                  <input className="input" type="text" placeholder="e.g. 50+" value={portfolioOss} onChange={(e) => setPortfolioOss(e.target.value)} />
                </label>
              </div>
            </div>

            {portfolioError && (
              <p className="filter-error">{portfolioError}</p>
            )}

            <div className="modal-footer">
              <div className="modal-footer__summary">
                <strong>{portfolioSelectedProjects.length}</strong>
                <span>{portfolioSelectedProjects.length === 1 ? 'project selected' : 'projects selected'}</span>
                {!canGeneratePortfolio && <span className="modal-footer__hint">Select at least two projects and enter your name.</span>}
              </div>
              <div className="modal-footer__actions">
                <button className="reset-btn" type="button" onClick={resetPortfolioModal}>
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  type="button"
                  onClick={handleGeneratePortfolio}
                  disabled={portfolioGenerating}
                >
                  {portfolioGenerating ? 'Generating…' : 'Generate Portfolio'}
                </button>
              </div>
              {portfolioUrl && (
                <a
                  className="btn-primary"
                  href={portfolioUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View Portfolio
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
