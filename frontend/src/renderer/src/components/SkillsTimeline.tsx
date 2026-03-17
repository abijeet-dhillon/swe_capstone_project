import React, { useEffect, useMemo, useRef, useState } from 'react'
import {
  addProjectSkills,
  editProjectSkills,
  getChronologicalProjects,
  getChronologicalSkills,
  getChronologicalSkillsByProjectId,
  getProjectSkills,
  getProjectTimelineLookup,
  getSkillsByYear,
  listSkillsCatalog,
  removeProjectSkills,
  type ChronologicalSkillEvent,
} from '../api'

type LookupMode = 'project-id' | 'zip-name'
type YearFilter = 'all' | `${number}`

type TimelineProjectOption = {
  key: string
  projectName: string
  zipHash: string
  projectId: number | null
}

type TimelineCard = {
  id: string
  skill: string
  category: string
  file: string
  timestamp: string
  month: number
  year: number
}

type ModalState =
  | { type: 'add' }
  | { type: 'edit'; card: TimelineCard }
  | { type: 'remove'; card: TimelineCard }
  | null

type SkillsTimelineProps = {
  refreshNonce?: number
  onBusyChange?: (busy: boolean) => void
}

const ALL_PROJECTS_KEY = '__all_projects__'
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function optionKey(zipHash: string, projectName: string): string {
  return `${zipHash}::${projectName}`
}

function parseSkillInput(raw: string): string[] {
  return raw
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
}

function splitTimestamp(timestamp: string): { month: number; year: number; normalized: string } {
  const parsed = new Date(timestamp)
  if (Number.isNaN(parsed.getTime())) {
    const now = new Date()
    return {
      month: now.getMonth() + 1,
      year: now.getFullYear(),
      normalized: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01T00:00:00`,
    }
  }
  return {
    month: parsed.getMonth() + 1,
    year: parsed.getFullYear(),
    normalized: parsed.toISOString(),
  }
}

function makeTimestamp(year: number, month: number): string {
  return `${year}-${String(month).padStart(2, '0')}-01T00:00:00`
}

function keepMostRecentCardPerSkill(cards: TimelineCard[]): TimelineCard[] {
  const latestBySkill = new Map<string, TimelineCard>()
  cards.forEach((card) => {
    const skillKey = card.skill.trim().toLowerCase()
    if (!skillKey) return
    const existing = latestBySkill.get(skillKey)
    if (!existing) {
      latestBySkill.set(skillKey, card)
      return
    }
    const currentMs = new Date(card.timestamp).getTime()
    const existingMs = new Date(existing.timestamp).getTime()
    if (currentMs >= existingMs) {
      latestBySkill.set(skillKey, card)
    }
  })
  return Array.from(latestBySkill.values()).sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  )
}

function makeCardsFromEvents(events: ChronologicalSkillEvent[]): TimelineCard[] {
  const cards: TimelineCard[] = []
  events.forEach((event) => {
    const values = splitTimestamp(event.timestamp)
    ;(event.skills ?? []).forEach((skill, idx) => {
      const cleaned = String(skill ?? '').trim()
      if (!cleaned) return
      cards.push({
        id: `${event.file}|${event.timestamp}|${cleaned}|${idx}`,
        skill: cleaned,
        category: event.category || 'uncategorized',
        file: event.file || 'unknown',
        timestamp: values.normalized,
        month: values.month,
        year: values.year,
      })
    })
  })
  return keepMostRecentCardPerSkill(cards)
}

const currentDate = new Date()
const defaultAddForm = {
  skills: '',
  month: String(currentDate.getMonth() + 1),
  year: String(currentDate.getFullYear()),
}

const SkillsTimeline: React.FC<SkillsTimelineProps> = ({ refreshNonce = 0, onBusyChange }) => {
  const [lookupMode, setLookupMode] = useState<LookupMode>('project-id')
  const [projectOptions, setProjectOptions] = useState<TimelineProjectOption[]>([])
  const [selectedProjectKey, setSelectedProjectKey] = useState<string>(ALL_PROJECTS_KEY)
  const [yearFilter, setYearFilter] = useState<YearFilter>('all')
  const [cards, setCards] = useState<TimelineCard[]>([])
  const [globalCatalog, setGlobalCatalog] = useState<string[]>([])
  const [projectCatalog, setProjectCatalog] = useState<string[]>([])
  const [modalState, setModalState] = useState<ModalState>(null)
  const [addForm, setAddForm] = useState(defaultAddForm)
  const [editForm, setEditForm] = useState({ skill: '', month: '1', year: String(currentDate.getFullYear()) })
  const [loadingOptions, setLoadingOptions] = useState(true)
  const [loadingTimeline, setLoadingTimeline] = useState(false)
  const [refreshingCatalog, setRefreshingCatalog] = useState(false)
  const [mutating, setMutating] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [hasLoadedTimeline, setHasLoadedTimeline] = useState(false)
  const firstRefreshHandled = useRef(false)

  const selectedProject = useMemo(
    () => projectOptions.find((project) => project.key === selectedProjectKey) ?? null,
    [projectOptions, selectedProjectKey],
  )
  const activeProjectId = selectedProject?.projectId ?? null
  const canMutate = Boolean(selectedProject && selectedProjectKey !== ALL_PROJECTS_KEY && activeProjectId)
  const isBusy = loadingOptions || loadingTimeline || refreshingCatalog || mutating

  const yearOptions = useMemo(() => {
    const years = new Set<number>([currentDate.getFullYear()])
    cards.forEach((card) => years.add(card.year))
    return Array.from(years).sort((a, b) => b - a)
  }, [cards])

  const visibleCards = useMemo(() => {
    if (yearFilter === 'all') return cards
    return cards.filter((card) => String(card.year) === yearFilter)
  }, [cards, yearFilter])

  useEffect(() => {
    onBusyChange?.(isBusy)
  }, [isBusy, onBusyChange])

  async function refreshGlobalCatalog(showNotice = false): Promise<void> {
    setRefreshingCatalog(true)
    try {
      const catalog = await listSkillsCatalog()
      setGlobalCatalog(catalog)
      if (showNotice) {
        setNotice(`Skill catalog refreshed (${catalog.length})`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh skill catalog')
    } finally {
      setRefreshingCatalog(false)
    }
  }

  async function refreshProjectCatalog(projectId: number): Promise<void> {
    const response = await getProjectSkills(projectId)
    setProjectCatalog(response.map((item) => item.skill_name))
  }

  async function loadProjectOptions(): Promise<void> {
    setLoadingOptions(true)
    setError('')
    try {
      const [chronological, lookup] = await Promise.all([
        getChronologicalProjects(50),
        getProjectTimelineLookup(),
      ])
      const idByProject = new Map<string, number>()
      lookup.forEach((project) => {
        idByProject.set(optionKey(project.zip_hash, project.project_name), project.project_id)
      })
      const seen = new Set<string>()
      const options: TimelineProjectOption[] = []
      chronological.projects.forEach((project) => {
        const key = optionKey(project.zip_hash, project.project_name)
        if (seen.has(key)) return
        seen.add(key)
        options.push({
          key,
          projectName: project.project_name,
          zipHash: project.zip_hash,
          projectId: idByProject.get(key) ?? null,
        })
      })
      setProjectOptions(options)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects')
      setProjectOptions([])
    } finally {
      setLoadingOptions(false)
    }
  }

  async function handleLoadTimeline(): Promise<void> {
    if (loadingTimeline) return
    setLoadingTimeline(true)
    setError('')
    setNotice('')
    try {
      if (selectedProjectKey === ALL_PROJECTS_KEY) {
        setProjectCatalog([])
        if (yearFilter !== 'all') {
          const byYear = await getSkillsByYear(Number(yearFilter))
          const yearCards = makeCardsFromEvents(byYear.timeline)
          setCards(yearCards)
          setNotice(`Loaded ${yearCards.length} items for ${yearFilter}`)
        } else {
          const results = await Promise.allSettled(
            projectOptions.map((project) =>
              getChronologicalSkills({
                zipHash: project.zipHash,
                projectName: project.projectName,
              }),
            ),
          )
          const merged: ChronologicalSkillEvent[] = []
          results.forEach((result) => {
            if (result.status === 'fulfilled') {
              merged.push(...result.value.timeline)
            }
          })
          const allCards = makeCardsFromEvents(merged)
          setCards(allCards)
          setNotice(`Loaded ${allCards.length} items across all projects`)
        }
      } else {
        if (!selectedProject) throw new Error('Select a project first')
        const response =
          lookupMode === 'project-id' && selectedProject.projectId
            ? await getChronologicalSkillsByProjectId(selectedProject.projectId)
            : await getChronologicalSkills({
                zipHash: selectedProject.zipHash,
                projectName: selectedProject.projectName,
              })
        const responseProjectId = response.project_id ?? selectedProject.projectId
        if (responseProjectId && responseProjectId !== selectedProject.projectId) {
          setProjectOptions((prev) =>
            prev.map((project) =>
              project.key === selectedProject.key ? { ...project, projectId: responseProjectId } : project,
            ),
          )
        }
        const loadedCards = makeCardsFromEvents(response.timeline)
        setCards(loadedCards)
        if (responseProjectId) {
          await refreshProjectCatalog(responseProjectId)
        } else {
          setProjectCatalog([])
          setNotice('Timeline loaded without project ID; add/edit/remove is disabled.')
        }
        if (!notice) {
          setNotice(`Loaded ${loadedCards.length} items for ${selectedProject.projectName}`)
        }
      }
      setHasLoadedTimeline(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline')
    } finally {
      setLoadingTimeline(false)
    }
  }

  useEffect(() => {
    void Promise.all([loadProjectOptions(), refreshGlobalCatalog(false)])
  }, [])

  useEffect(() => {
    if (!firstRefreshHandled.current) {
      firstRefreshHandled.current = true
      return
    }
    void refreshGlobalCatalog(true)
    if (hasLoadedTimeline) {
      void handleLoadTimeline()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshNonce])

  useEffect(() => {
    if (modalState?.type === 'edit') {
      setEditForm({
        skill: modalState.card.skill,
        month: String(modalState.card.month),
        year: String(modalState.card.year),
      })
    }
  }, [modalState])

  async function handleAddSkill(): Promise<void> {
    if (!activeProjectId) return
    const skills = parseSkillInput(addForm.skills)
    const month = Number(addForm.month)
    const year = Number(addForm.year)
    if (skills.length === 0 || Number.isNaN(month) || Number.isNaN(year)) {
      setError('Provide month, year, and at least one skill.')
      return
    }
    setMutating(true)
    setError('')
    try {
      await addProjectSkills({ project_id: activeProjectId, skills, month, year })
      const timestamp = makeTimestamp(year, month)
      const nextCards = skills.map((skill, idx) => ({
        id: `manual|${timestamp}|${skill}|${Date.now()}|${idx}`,
        skill,
        category: 'manual',
        file: 'manual-entry',
        timestamp,
        month,
        year,
      }))
      setCards((prev) => keepMostRecentCardPerSkill([...prev, ...nextCards]))
      await refreshProjectCatalog(activeProjectId)
      setModalState(null)
      setAddForm(defaultAddForm)
      setNotice(`Added ${skills.length} skill${skills.length === 1 ? '' : 's'}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add skill')
    } finally {
      setMutating(false)
    }
  }

  async function handleEditSkill(): Promise<void> {
    if (modalState?.type !== 'edit' || !activeProjectId) return
    const nextSkill = editForm.skill.trim()
    const month = Number(editForm.month)
    const year = Number(editForm.year)
    if (!nextSkill || Number.isNaN(month) || Number.isNaN(year)) {
      setError('Provide valid skill, month, and year.')
      return
    }
    setMutating(true)
    setError('')
    try {
      const oldSkill = modalState.card.skill
      await editProjectSkills({ project_id: activeProjectId, old: oldSkill, new: nextSkill, month, year })
      const targetTimestamp = makeTimestamp(year, month)
      const oldKey = oldSkill.toLowerCase()
      setCards((prev) =>
        keepMostRecentCardPerSkill(
          prev.map((card) => {
            if (card.skill.toLowerCase() !== oldKey) return card
            if (card.id !== modalState.card.id) return { ...card, skill: nextSkill }
            return {
              ...card,
              skill: nextSkill,
              month,
              year,
              timestamp: targetTimestamp,
            }
          }),
        ),
      )
      await refreshProjectCatalog(activeProjectId)
      setModalState(null)
      setNotice(`Updated "${oldSkill}" to "${nextSkill}"`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to edit skill')
    } finally {
      setMutating(false)
    }
  }

  async function handleRemoveSkill(): Promise<void> {
    if (modalState?.type !== 'remove' || !activeProjectId) return
    setMutating(true)
    setError('')
    try {
      await removeProjectSkills({ project_id: activeProjectId, skills: [modalState.card.skill] })
      const removedKey = modalState.card.skill.toLowerCase()
      setCards((prev) => prev.filter((card) => card.skill.toLowerCase() !== removedKey))
      await refreshProjectCatalog(activeProjectId)
      setModalState(null)
      setNotice(`Removed "${modalState.card.skill}"`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove skill')
    } finally {
      setMutating(false)
    }
  }

  if (loadingOptions && projectOptions.length === 0) {
    return (
      <div className="timeline-container">
        <div className="timeline-loading">
          <div className="loading-spinner"></div>
          <p>Loading skills data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="timeline-container">
      <div className="timeline-controls timeline-controls--load">
        <select
          className="select timeline-select timeline-select--project"
          aria-label="Project selector"
          value={selectedProjectKey}
          onChange={(e) => setSelectedProjectKey(e.target.value)}
          disabled={isBusy}
        >
          <option value={ALL_PROJECTS_KEY}>All projects</option>
          {projectOptions.map((project) => (
            <option key={project.key} value={project.key}>
              {project.projectName} ({project.zipHash.slice(0, 8)})
            </option>
          ))}
        </select>
        <select
          className="select timeline-select timeline-select--mode"
          aria-label="Lookup mode"
          value={lookupMode}
          onChange={(e) => setLookupMode(e.target.value as LookupMode)}
          disabled={isBusy}
        >
          <option value="project-id">Project ID</option>
          <option value="zip-name">ZIP + Name</option>
        </select>
        <button className="apply-btn" onClick={() => void handleLoadTimeline()} disabled={isBusy || loadingOptions}>
          {loadingTimeline ? 'Loading…' : 'Load timeline'}
        </button>
        <button className="reset-btn" onClick={() => setModalState({ type: 'add' })} disabled={isBusy || !canMutate}>
          Add skill
        </button>
      </div>

      <div className="timeline-controls timeline-controls--year">
        <select
          className="select timeline-select timeline-select--year"
          aria-label="Year filter"
          value={yearFilter}
          onChange={(e) => setYearFilter(e.target.value as YearFilter)}
          disabled={isBusy}
        >
          <option value="all">All</option>
          {yearOptions.map((year) => (
            <option key={year} value={String(year)}>
              {year}
            </option>
          ))}
        </select>
        <span className="pill info">{globalCatalog.length} catalog skills</span>
        {selectedProjectKey !== ALL_PROJECTS_KEY && (
          <span className="pill ready">{projectCatalog.length} in selected project</span>
        )}
      </div>

      {error && <p className="filter-error">{error}</p>}
      {!error && notice && <p className="timeline-notice">{notice}</p>}

      {visibleCards.length === 0 ? (
        <p className="empty-state">Load a timeline to view skill cards.</p>
      ) : (
        <div className="timeline">
          {visibleCards.map((card, index) => (
            <div key={card.id} className="timeline-item" style={{ animationDelay: `${index * 0.05}s` }}>
              <div className="timeline-dot"></div>
              <div className="timeline-content">
                <div className="timeline-header">
                  <div className="timeline-date">
                    {MONTH_NAMES[card.month - 1]} {card.year}
                  </div>
                  <span className="timeline-category">{card.category}</span>
                </div>
                <h3 className="timeline-title">{card.skill}</h3>
                <p className="timeline-description">{card.file}</p>
                <div className="timeline-card-actions">
                  <button
                    className="timeline-card-btn"
                    onClick={() => setModalState({ type: 'edit', card })}
                    disabled={!canMutate || isBusy}
                  >
                    Edit
                  </button>
                  <button
                    className="timeline-card-btn timeline-card-btn--danger"
                    onClick={() => setModalState({ type: 'remove', card })}
                    disabled={!canMutate || isBusy}
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {modalState?.type === 'add' && (
        <div className="skill-modal" onClick={() => (mutating ? null : setModalState(null))}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => (mutating ? null : setModalState(null))}>&times;</span>
            <div className="modal-header">
              <h2>Add skill</h2>
            </div>
            <label className="timeline-form-field">
              <span>Skill(s)</span>
              <input
                className="input"
                aria-label="Add skills input"
                placeholder="python, fastapi"
                value={addForm.skills}
                onChange={(e) => setAddForm((prev) => ({ ...prev, skills: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Month</span>
              <select
                className="select"
                aria-label="Add month"
                value={addForm.month}
                onChange={(e) => setAddForm((prev) => ({ ...prev, month: e.target.value }))}
              >
                {MONTH_NAMES.map((month, idx) => (
                  <option key={month} value={String(idx + 1)}>
                    {month}
                  </option>
                ))}
              </select>
            </label>
            <label className="timeline-form-field">
              <span>Year</span>
              <input
                className="input"
                aria-label="Add year"
                type="number"
                min="1000"
                max="9999"
                value={addForm.year}
                onChange={(e) => setAddForm((prev) => ({ ...prev, year: e.target.value }))}
              />
            </label>
            <div className="timeline-modal-actions">
              <button className="apply-btn" onClick={() => void handleAddSkill()} disabled={mutating}>
                {mutating ? 'Adding…' : 'Add'}
              </button>
              <button className="reset-btn" onClick={() => setModalState(null)} disabled={mutating}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {modalState?.type === 'edit' && (
        <div className="skill-modal" onClick={() => (mutating ? null : setModalState(null))}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => (mutating ? null : setModalState(null))}>&times;</span>
            <div className="modal-header">
              <h2>Edit skill</h2>
            </div>
            <label className="timeline-form-field">
              <span>Skill</span>
              <input
                className="input"
                aria-label="Edit skill input"
                value={editForm.skill}
                onChange={(e) => setEditForm((prev) => ({ ...prev, skill: e.target.value }))}
              />
            </label>
            <label className="timeline-form-field">
              <span>Month</span>
              <select
                className="select"
                aria-label="Edit month"
                value={editForm.month}
                onChange={(e) => setEditForm((prev) => ({ ...prev, month: e.target.value }))}
              >
                {MONTH_NAMES.map((month, idx) => (
                  <option key={month} value={String(idx + 1)}>
                    {month}
                  </option>
                ))}
              </select>
            </label>
            <label className="timeline-form-field">
              <span>Year</span>
              <input
                className="input"
                aria-label="Edit year"
                type="number"
                min="1000"
                max="9999"
                value={editForm.year}
                onChange={(e) => setEditForm((prev) => ({ ...prev, year: e.target.value }))}
              />
            </label>
            <div className="timeline-modal-actions">
              <button className="apply-btn" onClick={() => void handleEditSkill()} disabled={mutating}>
                {mutating ? 'Saving…' : 'Save'}
              </button>
              <button className="reset-btn" onClick={() => setModalState(null)} disabled={mutating}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {modalState?.type === 'remove' && (
        <div className="skill-modal" onClick={() => (mutating ? null : setModalState(null))}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => (mutating ? null : setModalState(null))}>&times;</span>
            <div className="modal-header">
              <h2>Remove skill</h2>
            </div>
            <p className="modal-description">
              Remove <strong>{modalState.card.skill}</strong> from this project?
            </p>
            <div className="timeline-modal-actions">
              <button className="apply-btn" onClick={() => void handleRemoveSkill()} disabled={mutating}>
                {mutating ? 'Removing…' : 'Yes'}
              </button>
              <button className="reset-btn" onClick={() => setModalState(null)} disabled={mutating}>
                No
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SkillsTimeline
