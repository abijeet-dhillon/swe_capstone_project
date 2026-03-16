import { useEffect, useState } from 'react'
import {
  filterProjects,
  getFilterOptions,
  getPortfolio,
  getProjectSkills,
  getResume,
  type FilteredProject,
  type FilterOptions,
  type ProjectFilter,
  type PortfolioData,
  type ResumeData,
  type ProjectSkill,
} from './api'

function parseCsv(s: string): string[] | undefined {
  const items = s.split(',').map((x) => x.trim()).filter(Boolean)
  return items.length ? items : undefined
}

const METRIC_NAMES = ['lines', 'commits', 'contributors', 'files'] as const

const FALLBACK_SORT = [
  { value: 'date_desc', label: 'Date Desc' },
  { value: 'date_asc', label: 'Date Asc' },
  { value: 'loc_desc', label: 'Loc Desc' },
  { value: 'importance', label: 'Importance' },
]

type ViewMode = 'list' | 'cards'

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch { return iso }
}

export default function ProjectsView() {
  const [searchText, setSearchText] = useState('')
  const [langInput, setLangInput] = useState('')
  const [fwInput, setFwInput] = useState('')
  const [skillInput, setSkillInput] = useState('')
  const [projectType, setProjectType] = useState('all')
  const [complexity, setComplexity] = useState('')
  const [sortBy, setSortBy] = useState('date_desc')
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [metrics, setMetrics] = useState<Record<string, number | undefined>>({})

  const [projects, setProjects] = useState<FilteredProject[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  useEffect(() => {
    getFilterOptions().then(setOptions).catch(() => {})
    handleApply()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const buildFilter = (): ProjectFilter => {
    const f: ProjectFilter = { sort_by: sortBy, project_type: projectType, limit: 50, offset: 0 }
    if (searchText) f.search_text = searchText
    const langs = parseCsv(langInput)
    if (langs) f.languages = langs
    const fws = parseCsv(fwInput)
    if (fws) f.frameworks = fws
    const sk = parseCsv(skillInput)
    if (sk) f.skills = sk
    if (complexity) f.complexity = complexity
    if (dateStart || dateEnd)
      f.date_range = { start: dateStart || undefined, end: dateEnd || undefined }
    const hasMetrics = Object.values(metrics).some((v) => v !== undefined)
    if (hasMetrics) f.metrics = metrics
    return f
  }

  const handleApply = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await filterProjects(buildFilter())
      setProjects(res.projects)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Filter failed')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setSearchText('')
    setLangInput('')
    setFwInput('')
    setSkillInput('')
    setProjectType('all')
    setComplexity('')
    setSortBy('date_desc')
    setDateStart('')
    setDateEnd('')
    setMetrics({})
    setShowAdvanced(false)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleApply()
  }

  const setMetric = (key: string, val: string) =>
    setMetrics((prev) => ({ ...prev, [key]: val ? Number(val) : undefined }))

  const activeFilterCount = [
    langInput, fwInput, skillInput, dateStart, dateEnd,
    complexity,
    ...Object.values(metrics).filter((v) => v !== undefined),
  ].filter(Boolean).length

  const toggleExpanded = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="projects-view" onKeyDown={onKeyDown}>
      {/* ── Toolbar ── */}
      <div className="pv-toolbar">
        <input
          className="input pv-toolbar__search"
          placeholder="Search projects..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <select className="select pv-toolbar__select" value={projectType} onChange={(e) => setProjectType(e.target.value)}>
          {(options?.project_types ?? [
            { value: 'all', label: 'All Types' },
            { value: 'individual', label: 'Individual' },
            { value: 'collaborative', label: 'Collaborative' },
          ]).map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select className="select pv-toolbar__select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          {(options?.sort_options ?? FALLBACK_SORT).map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          className={`pv-toolbar__toggle ${showAdvanced ? 'pv-toolbar__toggle--active' : ''}`}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          Filters
          {activeFilterCount > 0 && (
            <span className="pv-toolbar__badge">{activeFilterCount}</span>
          )}
        </button>
        <div className="pv-toolbar__view-toggle">
          <button
            className={`pv-view-btn ${viewMode === 'list' ? 'pv-view-btn--active' : ''}`}
            onClick={() => setViewMode('list')}
            title="List view"
          >
            ☰
          </button>
          <button
            className={`pv-view-btn ${viewMode === 'cards' ? 'pv-view-btn--active' : ''}`}
            onClick={() => setViewMode('cards')}
            title="Card view"
          >
            ⊞
          </button>
        </div>
        <button className="apply-btn" onClick={handleApply} disabled={loading}>
          {loading ? 'Loading…' : 'Apply'}
        </button>
        <span className="result-count">{total} found</span>
      </div>

      {/* ── Advanced Filters ── */}
      {showAdvanced && (
        <div className="pv-advanced">
          <div className="pv-advanced__row">
            <label className="pv-advanced__field">
              <span>Languages</span>
              <input className="input" placeholder="Python, JS..." value={langInput} onChange={(e) => setLangInput(e.target.value)} />
            </label>
            <label className="pv-advanced__field">
              <span>Frameworks</span>
              <input className="input" placeholder="React, FastAPI..." value={fwInput} onChange={(e) => setFwInput(e.target.value)} />
            </label>
            <label className="pv-advanced__field">
              <span>Skills</span>
              <input className="input" placeholder="REST API, Testing..." value={skillInput} onChange={(e) => setSkillInput(e.target.value)} />
            </label>
            <label className="pv-advanced__field">
              <span>Complexity</span>
              <select className="select" value={complexity} onChange={(e) => setComplexity(e.target.value)}>
                <option value="">Any</option>
                {(options?.complexity_levels ?? ['simple', 'moderate', 'complex']).map((c) => (
                  <option key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </label>
          </div>
          <div className="pv-advanced__row">
            <label className="pv-advanced__field pv-advanced__field--sm">
              <span>From</span>
              <input className="input" type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} />
            </label>
            <label className="pv-advanced__field pv-advanced__field--sm">
              <span>To</span>
              <input className="input" type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} />
            </label>
            {METRIC_NAMES.map((m) => (
              <label key={m} className="pv-advanced__field pv-advanced__field--sm">
                <span>{m} (min–max)</span>
                <div className="pv-advanced__pair">
                  <input className="input" type="number" min="0" placeholder="Min" value={metrics[`min_${m}`] ?? ''} onChange={(e) => setMetric(`min_${m}`, e.target.value)} />
                  <input className="input" type="number" min="0" placeholder="Max" value={metrics[`max_${m}`] ?? ''} onChange={(e) => setMetric(`max_${m}`, e.target.value)} />
                </div>
              </label>
            ))}
          </div>
          <button className="pv-advanced__reset" onClick={handleReset}>Clear all filters</button>
        </div>
      )}

      {error && <p className="filter-error">{error}</p>}

      {/* ── Results ── */}
      {projects.length === 0 && !loading ? (
        <p className="empty-state">No projects found. Adjust filters or ensure the backend is running on port 8000.</p>
      ) : viewMode === 'cards' ? (
        <section className="pv-cards-grid">
          {projects.map((p) => (
            <article
              key={p.project_info_id}
              className={`pv-card ${expandedId === p.project_info_id ? 'pv-card--expanded' : ''}`}
              onClick={() => toggleExpanded(p.project_info_id)}
            >
              <div className="pv-card__head">
                <h4>{p.project_name}</h4>
                <div className="project-pills">
                  {p.project_type && <span className="pill info">{p.project_type}</span>}
                  {p.complexity && (
                    <span className={`pill ${p.complexity === 'complex' ? 'highlight' : p.complexity === 'moderate' ? 'coming-soon' : 'ready'}`}>
                      {p.complexity}
                    </span>
                  )}
                </div>
              </div>
              {p.tagline && <p className="pv-card__tagline">{p.tagline}</p>}
              <div className="pv-card__stats">
                <span>{(p.total_lines ?? 0).toLocaleString()} lines</span>
                <span>{p.total_commits ?? 0} commits</span>
                <span>{p.total_contributors ?? 0} contributors</span>
                <span>{p.total_files ?? 0} files</span>
              </div>
              {p.description && <p className="pv-card__desc">{p.description}</p>}
              <span className="pv-card__date">{formatDate(p.project_created_at)}</span>
              {expandedId === p.project_info_id && (
                <ProjectExpandedDetail projectId={p.project_info_id} />
              )}
            </article>
          ))}
        </section>
      ) : (
        <section className="project-results">
          {projects.map((p) => (
            <article
              key={p.project_info_id}
              className={`project-card ${expandedId === p.project_info_id ? 'project-card--expanded' : ''}`}
              onClick={() => toggleExpanded(p.project_info_id)}
            >
              <div className="project-head">
                <h4>{p.project_name}</h4>
                <div className="project-pills">
                  {p.project_type && <span className="pill info">{p.project_type}</span>}
                  {p.complexity && (
                    <span className={`pill ${p.complexity === 'complex' ? 'highlight' : p.complexity === 'moderate' ? 'coming-soon' : 'ready'}`}>
                      {p.complexity}
                    </span>
                  )}
                </div>
              </div>
              {p.tagline && <p className="project-tagline">{p.tagline}</p>}
              <div className="project-stats">
                <span>{(p.total_lines ?? 0).toLocaleString()} lines</span>
                <span>{p.total_commits ?? 0} commits</span>
                <span>{p.total_contributors ?? 0} contributors</span>
                <span>{p.total_files ?? 0} files</span>
              </div>
              {p.description && <p className="project-desc">{p.description}</p>}
              {expandedId === p.project_info_id && (
                <ProjectExpandedDetail projectId={p.project_info_id} />
              )}
            </article>
          ))}
        </section>
      )}
    </div>
  )
}

function ProjectExpandedDetail({ projectId }: { projectId: number }) {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [resume, setResume] = useState<ResumeData | null>(null)
  const [skills, setSkills] = useState<ProjectSkill[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([
      getPortfolio(projectId),
      getResume(projectId),
      getProjectSkills(projectId),
    ]).then(([pRes, rRes, sRes]) => {
      if (pRes.status === 'fulfilled') setPortfolio(pRes.value)
      if (rRes.status === 'fulfilled') setResume(rRes.value)
      if (sRes.status === 'fulfilled') setSkills(sRes.value)
      setLoading(false)
    })
  }, [projectId])

  if (loading) {
    return <div className="pv-expanded__loading" onClick={(e) => e.stopPropagation()}>Loading details...</div>
  }

  return (
    <div className="pv-expanded" onClick={(e) => e.stopPropagation()}>
      {portfolio?.summary && (
        <div className="pv-expanded__section">
          <h5>Summary</h5>
          <p>{portfolio.summary}</p>
        </div>
      )}

      {portfolio?.key_features && portfolio.key_features.length > 0 && (
        <div className="pv-expanded__section">
          <h5>Key Features</h5>
          <ul>
            {portfolio.key_features.map((f, i) => <li key={i}>{f}</li>)}
          </ul>
        </div>
      )}

      {resume && resume.bullets.length > 0 && (
        <div className="pv-expanded__section">
          <h5>Resume Bullets</h5>
          <ul>
            {resume.bullets.map((b, i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
      )}

      {skills.length > 0 && (
        <div className="pv-expanded__section">
          <h5>Skills</h5>
          <div className="pv-expanded__skills">
            {skills.map((s, i) => (
              <span key={i} className="skill-pill">{s.skill_name}</span>
            ))}
          </div>
        </div>
      )}

      {portfolio?.evolution && (
        <div className="pv-expanded__section">
          <h5>Timeline</h5>
          <div className="pv-expanded__meta">
            {portfolio.evolution.first_commit && (
              <span>First commit: {portfolio.evolution.first_commit}</span>
            )}
            {portfolio.evolution.last_commit && (
              <span>Last commit: {portfolio.evolution.last_commit}</span>
            )}
            {portfolio.evolution.contributors && portfolio.evolution.contributors.length > 0 && (
              <span>{portfolio.evolution.contributors.length} contributor(s)</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
