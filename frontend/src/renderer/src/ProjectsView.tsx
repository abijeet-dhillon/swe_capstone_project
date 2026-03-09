import { useEffect, useState } from 'react'
import {
  filterProjects,
  getFilterOptions,
  type FilteredProject,
  type FilterOptions,
  type ProjectFilter,
} from './api'

function parseCsv(s: string): string[] | undefined {
  const items = s
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
  return items.length ? items : undefined
}

const METRIC_NAMES = ['lines', 'commits', 'contributors', 'files'] as const

const FALLBACK_SORT = [
  { value: 'date_desc', label: 'Date Desc' },
  { value: 'date_asc', label: 'Date Asc' },
  { value: 'loc_desc', label: 'Loc Desc' },
  { value: 'importance', label: 'Importance' },
]

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
  const [showMetrics, setShowMetrics] = useState(false)
  const [metrics, setMetrics] = useState<Record<string, number | undefined>>({})

  const [projects, setProjects] = useState<FilteredProject[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [options, setOptions] = useState<FilterOptions | null>(null)

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
    setShowMetrics(false)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleApply()
  }

  const setMetric = (key: string, val: string) =>
    setMetrics((prev) => ({ ...prev, [key]: val ? Number(val) : undefined }))

  return (
    <div className="projects-view">
      <section className="filter-panel" onKeyDown={onKeyDown}>
        <h3>Filter Projects</h3>

        <input
          className="input filter-search"
          placeholder="Search projects by name, description..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />

        <div className="filter-grid">
          <label>
            Languages
            <input className="input" placeholder="Python, JS..." value={langInput} onChange={(e) => setLangInput(e.target.value)} />
          </label>
          <label>
            Frameworks
            <input className="input" placeholder="React, FastAPI..." value={fwInput} onChange={(e) => setFwInput(e.target.value)} />
          </label>
          <label>
            Skills
            <input className="input" placeholder="REST API, Testing..." value={skillInput} onChange={(e) => setSkillInput(e.target.value)} />
          </label>
        </div>

        <div className="filter-grid">
          <label>
            Project Type
            <select className="select" value={projectType} onChange={(e) => setProjectType(e.target.value)}>
              {(options?.project_types ?? [{ value: 'all', label: 'All' }, { value: 'individual', label: 'Individual' }, { value: 'collaborative', label: 'Collaborative' }]).map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          <label>
            Complexity
            <select className="select" value={complexity} onChange={(e) => setComplexity(e.target.value)}>
              <option value="">Any</option>
              {(options?.complexity_levels ?? ['simple', 'moderate', 'complex']).map((c) => (
                <option key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
          </label>
          <label>
            Sort By
            <select className="select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              {(options?.sort_options ?? FALLBACK_SORT).map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="filter-grid filter-grid-2">
          <label>From<input className="input" type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} /></label>
          <label>To<input className="input" type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} /></label>
        </div>

        <button className="mode-btn metrics-toggle" onClick={() => setShowMetrics(!showMetrics)}>
          {showMetrics ? '▾ Hide' : '▸ Show'} Metrics Filters
        </button>

        {showMetrics && (
          <div className="filter-metrics">
            {METRIC_NAMES.map((m) => (
              <div key={m} className="metric-pair">
                <span>{m}</span>
                <input className="input" type="number" min="0" placeholder="Min" value={metrics[`min_${m}`] ?? ''} onChange={(e) => setMetric(`min_${m}`, e.target.value)} />
                <input className="input" type="number" min="0" placeholder="Max" value={metrics[`max_${m}`] ?? ''} onChange={(e) => setMetric(`max_${m}`, e.target.value)} />
              </div>
            ))}
          </div>
        )}

        <div className="filter-actions">
          <button className="action-btn apply-btn" onClick={handleApply} disabled={loading}>
            {loading ? 'Filtering…' : 'Apply Filters'}
          </button>
          <button className="action-btn" onClick={handleReset}>Reset</button>
          <span className="result-count">{total} project{total !== 1 ? 's' : ''} found</span>
        </div>
      </section>

      {error && <p className="filter-error">{error}</p>}

      <section className="project-results">
        {projects.length === 0 && !loading ? (
          <p className="empty-state">No projects found. Adjust filters or ensure the backend is running on port 8000.</p>
        ) : (
          projects.map((p) => (
            <article className="project-card" key={p.project_info_id}>
              <div className="project-head">
                <h4>{p.project_name}</h4>
                <div className="project-pills">
                  {p.project_type && <span className="pill ready">{p.project_type}</span>}
                  {p.complexity && <span className="pill coming-soon">{p.complexity}</span>}
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
            </article>
          ))
        )}
      </section>
    </div>
  )
}
