import { useEffect, useState } from 'react'
import {
  filterProjects,
  getFilterOptions,
  getPortfolio,
  getProjectSkills,
  getResume,
  removeProject,
  updateProject,
  type FilteredProject,
  type FilterOptions,
  type PortfolioData,
  type ProjectEditRequest,
  type ProjectFilter,
  type ProjectSkill,
  type ResumeData,
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

const EDITABLE_FIELDS: Array<keyof ProjectEditRequest> = [
  'project_name',
  'tagline',
  'description',
  'project_type',
  'complexity',
  'summary',
]

type ViewMode = 'list' | 'cards'
type ModalState =
  | { type: 'edit'; project: FilteredProject }
  | { type: 'remove'; project: FilteredProject }
  | null

type EditFormState = Record<keyof ProjectEditRequest, string>

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return iso
  }
}

function toEditForm(project: FilteredProject): EditFormState {
  return {
    project_name: project.project_name ?? '',
    tagline: project.tagline ?? '',
    description: project.description ?? '',
    project_type: project.project_type ?? '',
    complexity: project.complexity ?? '',
    summary: project.summary ?? '',
  }
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
  const [notice, setNotice] = useState('')
  const [options, setOptions] = useState<FilterOptions | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [modalState, setModalState] = useState<ModalState>(null)
  const [editForm, setEditForm] = useState<EditFormState>({
    project_name: '',
    tagline: '',
    description: '',
    project_type: '',
    complexity: '',
    summary: '',
  })
  const [mutating, setMutating] = useState(false)
  const [detailRefreshNonce, setDetailRefreshNonce] = useState(0)

  useEffect(() => {
    getFilterOptions().then(setOptions).catch(() => {})
    void handleApply()
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
    if (dateStart || dateEnd) f.date_range = { start: dateStart || undefined, end: dateEnd || undefined }
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
    if (e.key === 'Enter' && !modalState) void handleApply()
  }

  const setMetric = (key: string, val: string) =>
    setMetrics((prev) => ({ ...prev, [key]: val ? Number(val) : undefined }))

  const activeFilterCount = [
    langInput,
    fwInput,
    skillInput,
    dateStart,
    dateEnd,
    complexity,
    ...Object.values(metrics).filter((v) => v !== undefined),
  ].filter(Boolean).length

  const toggleExpanded = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const openEditModal = (project: FilteredProject, event: React.MouseEvent) => {
    event.stopPropagation()
    setEditForm(toEditForm(project))
    setModalState({ type: 'edit', project })
    setError('')
    setNotice('')
  }

  const openRemoveModal = (project: FilteredProject, event: React.MouseEvent) => {
    event.stopPropagation()
    setModalState({ type: 'remove', project })
    setError('')
    setNotice('')
  }

  const closeModal = () => {
    if (mutating) return
    setModalState(null)
  }

  const handleSaveProject = async () => {
    if (modalState?.type !== 'edit') return
    const original = modalState.project
    const payload: ProjectEditRequest = {}
    EDITABLE_FIELDS.forEach((field) => {
      const next = (editForm[field] ?? '').trim()
      const prevRaw = (original[field] ?? '') as string
      const prev = prevRaw.trim()
      if (next !== prev) {
        payload[field] = next
      }
    })

    if (Object.keys(payload).length === 0) {
      setNotice('No changes to save.')
      setModalState(null)
      return
    }

    setMutating(true)
    setError('')
    try {
      await updateProject(original.project_info_id, payload)
      setProjects((prev) =>
        prev.map((project) =>
          project.project_info_id === original.project_info_id
            ? {
                ...project,
                ...payload,
                project_name: payload.project_name ?? project.project_name,
              }
            : project,
        ),
      )
      setDetailRefreshNonce((prev) => prev + 1)
      setModalState(null)
      setNotice(`Updated "${payload.project_name ?? original.project_name}"`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update project')
    } finally {
      setMutating(false)
    }
  }

  const handleRemoveProject = async () => {
    if (modalState?.type !== 'remove') return
    const project = modalState.project
    setMutating(true)
    setError('')
    try {
      await removeProject(project.project_info_id)
      setProjects((prev) => prev.filter((item) => item.project_info_id !== project.project_info_id))
      setTotal((prev) => Math.max(0, prev - 1))
      setExpandedId((prev) => (prev === project.project_info_id ? null : prev))
      setModalState(null)
      setNotice(`Removed "${project.project_name}"`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to remove project')
    } finally {
      setMutating(false)
    }
  }

  return (
    <div className="projects-view" onKeyDown={onKeyDown}>
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
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select className="select pv-toolbar__select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          {(options?.sort_options ?? FALLBACK_SORT).map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          className={`pv-toolbar__toggle ${showAdvanced ? 'pv-toolbar__toggle--active' : ''}`}
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          Filters
          {activeFilterCount > 0 && <span className="pv-toolbar__badge">{activeFilterCount}</span>}
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
        <button className="apply-btn" onClick={() => void handleApply()} disabled={loading || mutating}>
          {loading ? 'Loading…' : 'Apply'}
        </button>
        <span className="result-count">{total} found</span>
      </div>

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
                  <option key={c} value={c}>
                    {c[0].toUpperCase() + c.slice(1)}
                  </option>
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
                <span>{m} (min-max)</span>
                <div className="pv-advanced__pair">
                  <input
                    className="input"
                    type="number"
                    min="0"
                    placeholder="Min"
                    value={metrics[`min_${m}`] ?? ''}
                    onChange={(e) => setMetric(`min_${m}`, e.target.value)}
                  />
                  <input
                    className="input"
                    type="number"
                    min="0"
                    placeholder="Max"
                    value={metrics[`max_${m}`] ?? ''}
                    onChange={(e) => setMetric(`max_${m}`, e.target.value)}
                  />
                </div>
              </label>
            ))}
          </div>
          <button className="pv-advanced__reset" onClick={handleReset}>
            Clear all filters
          </button>
        </div>
      )}

      {error && <p className="filter-error">{error}</p>}
      {!error && notice && <p className="timeline-notice">{notice}</p>}

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
              <div className="timeline-card-actions" onClick={(e) => e.stopPropagation()}>
                <button className="timeline-card-btn" onClick={(e) => openEditModal(p, e)} disabled={mutating || loading}>
                  Edit
                </button>
                <button
                  className="timeline-card-btn timeline-card-btn--danger"
                  onClick={(e) => openRemoveModal(p, e)}
                  disabled={mutating || loading}
                >
                  Remove
                </button>
              </div>
              {expandedId === p.project_info_id && (
                <ProjectExpandedDetail projectId={p.project_info_id} refreshNonce={detailRefreshNonce} />
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
              <div className="timeline-card-actions" onClick={(e) => e.stopPropagation()}>
                <button className="timeline-card-btn" onClick={(e) => openEditModal(p, e)} disabled={mutating || loading}>
                  Edit
                </button>
                <button
                  className="timeline-card-btn timeline-card-btn--danger"
                  onClick={(e) => openRemoveModal(p, e)}
                  disabled={mutating || loading}
                >
                  Remove
                </button>
              </div>
              {expandedId === p.project_info_id && (
                <ProjectExpandedDetail projectId={p.project_info_id} refreshNonce={detailRefreshNonce} />
              )}
            </article>
          ))}
        </section>
      )}

      {modalState?.type === 'edit' && (
        <div className="skill-modal" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={closeModal}>
              &times;
            </span>
            <div className="modal-header">
              <h2>Edit project</h2>
            </div>
            <label className="timeline-form-field">
              <span>Project Name</span>
              <input
                className="input"
                aria-label="Edit project name"
                value={editForm.project_name}
                onChange={(e) => setEditForm((prev) => ({ ...prev, project_name: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Tagline</span>
              <input
                className="input"
                aria-label="Edit project tagline"
                value={editForm.tagline}
                onChange={(e) => setEditForm((prev) => ({ ...prev, tagline: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Description</span>
              <textarea
                className="input"
                aria-label="Edit project description"
                value={editForm.description}
                onChange={(e) => setEditForm((prev) => ({ ...prev, description: e.target.value }))}
                rows={3}
                style={{ width: '100%', minWidth: 0 }}
              />
            </label>
            <label className="timeline-form-field">
              <span>Project Type</span>
              <input
                className="input"
                aria-label="Edit project type"
                value={editForm.project_type}
                onChange={(e) => setEditForm((prev) => ({ ...prev, project_type: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Complexity</span>
              <input
                className="input"
                aria-label="Edit project complexity"
                value={editForm.complexity}
                onChange={(e) => setEditForm((prev) => ({ ...prev, complexity: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Summary</span>
              <textarea
                className="input"
                aria-label="Edit project summary"
                value={editForm.summary}
                onChange={(e) => setEditForm((prev) => ({ ...prev, summary: e.target.value }))}
                rows={3}
                style={{ width: '100%', minWidth: 0 }}
              />
            </label>
            <div className="timeline-modal-actions">
              <button className="apply-btn" onClick={() => void handleSaveProject()} disabled={mutating}>
                {mutating ? 'Saving…' : 'Save'}
              </button>
              <button className="reset-btn" onClick={closeModal} disabled={mutating}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {modalState?.type === 'remove' && (
        <div className="skill-modal" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={closeModal}>
              &times;
            </span>
            <div className="modal-header">
              <h2>Remove project</h2>
            </div>
            <p className="modal-description">
              Remove <strong>{modalState.project.project_name}</strong> from this view?
            </p>
            <div className="timeline-modal-actions">
              <button className="apply-btn" onClick={() => void handleRemoveProject()} disabled={mutating}>
                {mutating ? 'Removing…' : 'Yes'}
              </button>
              <button className="reset-btn" onClick={closeModal} disabled={mutating}>
                No
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ProjectExpandedDetail({ projectId, refreshNonce = 0 }: { projectId: number; refreshNonce?: number }) {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [resume, setResume] = useState<ResumeData | null>(null)
  const [skills, setSkills] = useState<ProjectSkill[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([getPortfolio(projectId), getResume(projectId), getProjectSkills(projectId)]).then(
      ([pRes, rRes, sRes]) => {
        if (pRes.status === 'fulfilled') setPortfolio(pRes.value)
        if (rRes.status === 'fulfilled') setResume(rRes.value)
        if (sRes.status === 'fulfilled') setSkills(sRes.value)
        setLoading(false)
      },
    )
  }, [projectId, refreshNonce])

  if (loading) {
    return (
      <div className="pv-expanded__loading" onClick={(e) => e.stopPropagation()}>
        Loading details...
      </div>
    )
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
            {portfolio.key_features.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}

      {resume && resume.bullets.length > 0 && (
        <div className="pv-expanded__section">
          <h5>Resume Bullets</h5>
          <ul>
            {resume.bullets.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </div>
      )}

      {skills.length > 0 && (
        <div className="pv-expanded__section">
          <h5>Skills</h5>
          <div className="pv-expanded__skills">
            {skills.map((s, i) => (
              <span key={i} className="skill-pill">
                {s.skill_name}
              </span>
            ))}
          </div>
        </div>
      )}

      {portfolio?.evolution && (
        <div className="pv-expanded__section">
          <h5>Timeline</h5>
          <div className="pv-expanded__meta">
            {portfolio.evolution.first_commit && <span>First commit: {portfolio.evolution.first_commit}</span>}
            {portfolio.evolution.last_commit && <span>Last commit: {portfolio.evolution.last_commit}</span>}
            {portfolio.evolution.contributors && portfolio.evolution.contributors.length > 0 && (
              <span>{portfolio.evolution.contributors.length} contributor(s)</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
