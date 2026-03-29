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
  projectName: string
}

type ModalState =
  | { type: 'add' }
  | { type: 'edit'; card: TimelineCard }
  | { type: 'remove'; card: TimelineCard }
  | { type: 'detail'; card: TimelineCard }
  | null

type SkillsTimelineProps = {
  refreshNonce?: number
  onBusyChange?: (busy: boolean) => void
}

const ALL_PROJECTS_KEY = '__all_projects__'
const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Category color map: each category gets a color scheme { accent, bg, text }
const CATEGORY_COLORS: Record<string, { accent: string; bg: string; text: string }> = {
  code: { accent: '#0984E3', bg: '#DBF0FF', text: '#0984E3' },
  text: { accent: '#00B894', bg: '#D4FAEF', text: '#00B894' },
  data: { accent: '#6C5CE7', bg: '#E8E4FF', text: '#6C5CE7' },
  config: { accent: '#F59E0B', bg: '#FEF3C7', text: '#D97706' },
  markup: { accent: '#EC4899', bg: '#FCE7F3', text: '#DB2777' },
  manual: { accent: '#7B68EE', bg: '#E8E4FF', text: '#6C5CE7' },
  uncategorized: { accent: '#B2BEC3', bg: '#F0F2F5', text: '#636E72' },
}

function getCategoryColor(category: string): { accent: string; bg: string; text: string } {
  const key = category.toLowerCase()
  return CATEGORY_COLORS[key] ?? { accent: '#7B68EE', bg: '#E8E4FF', text: '#6C5CE7' }
}

function getFileName(filePath: string): string {
  if (!filePath || filePath === 'unknown' || filePath === 'manual-entry') return filePath
  const parts = filePath.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || filePath
}

function optionKey(zipHash: string, projectName: string): string {
  return `${zipHash}::${projectName}`
}

function parseSkillInput(raw: string): string[] {
  return raw
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
}

/** Strip server-side temp extraction prefixes like /tmp/unzipped_abc123/ */
function stripTmpPrefix(filePath: string): string {
  return filePath.replace(/^\/tmp\/unzipped_[^/]+\//, '')
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

// Returns ALL cards (one per skill occurrence) — caller is responsible for dedup
function makeCardsFromEvents(events: ChronologicalSkillEvent[], projectName: string): TimelineCard[] {
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
        projectName,
      })
    })
  })
  return cards
}

function estimateProficiency(
  _skillName: string,
  firstSeenTimestamp: string,
): { level: string; percent: number } {
  const monthsAgo = Math.max(
    0,
    (Date.now() - new Date(firstSeenTimestamp).getTime()) / (1000 * 60 * 60 * 24 * 30),
  )
  if (monthsAgo >= 24) return { level: 'Advanced', percent: 85 }
  if (monthsAgo >= 12) return { level: 'Intermediate', percent: 60 }
  if (monthsAgo >= 3) return { level: 'Familiar', percent: 35 }
  return { level: 'Beginner', percent: 15 }
}

type TimelineGroup = {
  groupKey: string
  month: number
  year: number
  cards: TimelineCard[]
}

function groupCardsByMonthYear(cards: TimelineCard[]): TimelineGroup[] {
  const groupMap = new Map<string, TimelineGroup>()
  cards.forEach((card) => {
    const key = `${card.year}-${String(card.month).padStart(2, '0')}`
    if (!groupMap.has(key)) {
      groupMap.set(key, { groupKey: key, month: card.month, year: card.year, cards: [] })
    }
    groupMap.get(key)!.cards.push(card)
  })
  return Array.from(groupMap.values()).sort((a, b) => {
    if (b.year !== a.year) return b.year - a.year
    return b.month - a.month
  })
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
  const [allRawCards, setAllRawCards] = useState<TimelineCard[]>([])
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
  const [lastLoadedProjectKey, setLastLoadedProjectKey] = useState<string | null>(null)
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

  const groupedTimeline = useMemo(() => groupCardsByMonthYear(visibleCards), [visibleCards])

  const selectedProjectCount = useMemo(() => {
    if (selectedProjectKey === ALL_PROJECTS_KEY) return null
    if (hasLoadedTimeline && lastLoadedProjectKey === selectedProjectKey) {
      return cards.length
    }
    return projectCatalog.length
  }, [cards.length, hasLoadedTimeline, lastLoadedProjectKey, projectCatalog.length, selectedProjectKey])

  // Summary stats
  const summaryStats = useMemo(() => {
    if (visibleCards.length === 0) return null
    const categories = new Set(visibleCards.map((c) => c.category))
    const sorted = [...visibleCards].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    )
    const earliest = sorted[0]
    const latest = sorted[sorted.length - 1]
    const dateRange =
      earliest.year === latest.year && earliest.month === latest.month
        ? `${MONTH_NAMES[earliest.month - 1]} ${earliest.year}`
        : `${MONTH_NAMES[earliest.month - 1]} ${earliest.year} – ${MONTH_NAMES[latest.month - 1]} ${latest.year}`
    return { totalSkills: visibleCards.length, categoryCount: categories.size, dateRange }
  }, [visibleCards])

  // Skill detail data — computed from allRawCards when detail modal is open
  const skillDetail = useMemo(() => {
    if (modalState?.type !== 'detail') return null
    const skillKey = modalState.card.skill.toLowerCase()

    // All appearances of this skill across raw cards
    const appearances = allRawCards.filter((c) => c.skill.toLowerCase() === skillKey)

    // Unique projects
    const projects = [...new Set(appearances.map((c) => c.projectName))].filter(Boolean)

    // Unique source files
    const files = [...new Set(appearances.map((c) => c.file))].filter(
      (f) => f && f !== 'unknown' && f !== 'manual-entry',
    )

    // First and last seen
    const sorted = [...appearances].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    )
    const firstSeen = sorted[0]
    const lastSeen = sorted[sorted.length - 1]

    // Proficiency
    const proficiency = estimateProficiency(
      modalState.card.skill,
      firstSeen?.timestamp ?? modalState.card.timestamp,
    )

    // Is in global catalog
    const inCatalog = globalCatalog.some((s) => s.toLowerCase() === skillKey)

    return {
      skill: modalState.card,
      appearances: appearances.length,
      projects,
      files,
      firstSeen,
      lastSeen,
      proficiency,
      inCatalog,
      category: modalState.card.category,
    }
  }, [modalState, allRawCards, globalCatalog])

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
          const raw = makeCardsFromEvents(byYear.timeline, 'All projects')
          setAllRawCards(raw)
          const yearCards = keepMostRecentCardPerSkill(raw)
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
          const merged: TimelineCard[] = []
          results.forEach((result, idx) => {
            if (result.status === 'fulfilled') {
              const projName = projectOptions[idx].projectName
              const raw = makeCardsFromEvents(result.value.timeline, projName)
              merged.push(...raw)
            }
          })
          setAllRawCards(merged)
          const allCards = keepMostRecentCardPerSkill(merged)
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
        const raw = makeCardsFromEvents(response.timeline, selectedProject.projectName)
        setAllRawCards(raw)
        const loadedCards = keepMostRecentCardPerSkill(raw)
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
      setLastLoadedProjectKey(selectedProjectKey)
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
        projectName: selectedProject?.projectName ?? '',
      }))
      setAllRawCards((prev) => [...prev, ...nextCards])
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
      const updateCard = (card: TimelineCard): TimelineCard => {
        if (card.skill.toLowerCase() !== oldKey) return card
        if (card.id !== modalState.card.id) return { ...card, skill: nextSkill }
        return {
          ...card,
          skill: nextSkill,
          month,
          year,
          timestamp: targetTimestamp,
        }
      }
      setAllRawCards((prev) => prev.map(updateCard))
      setCards((prev) => keepMostRecentCardPerSkill(prev.map(updateCard)))
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
      setAllRawCards((prev) => prev.filter((card) => card.skill.toLowerCase() !== removedKey))
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
      {/* Controls card */}
      <div className="timeline-controls-card">
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
            <option value="all">All years</option>
            {yearOptions.map((year) => (
              <option key={year} value={String(year)}>
                {year}
              </option>
            ))}
          </select>
          <div className="timeline-pills-row">
            <span className="pill info">{globalCatalog.length} catalog skills</span>
            {selectedProjectKey !== ALL_PROJECTS_KEY && (
              <span className="pill ready">{selectedProjectCount ?? 0} in selected project</span>
            )}
            {error && <span className="pill error">{error}</span>}
            {!error && notice && <span className="pill timeline-notice-pill">{notice}</span>}
          </div>
        </div>
      </div>

      {/* Summary stats row */}
      {summaryStats && (
        <div className="timeline-stats-row">
          <div className="timeline-stat-pill">
            <span className="timeline-stat-value">{summaryStats.totalSkills}</span>
            <span className="timeline-stat-label">skills</span>
          </div>
          <div className="timeline-stat-pill">
            <span className="timeline-stat-value">{summaryStats.categoryCount}</span>
            <span className="timeline-stat-label">categories</span>
          </div>
          <div className="timeline-stat-pill timeline-stat-pill--range">
            <span className="timeline-stat-label">{summaryStats.dateRange}</span>
          </div>
        </div>
      )}

      {/* Timeline */}
      {groupedTimeline.length === 0 ? (
        <div className="timeline-empty-state">
          <div className="timeline-empty-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="20" fill="#E8E4FF" />
              <path d="M16 24h16M24 16v16" stroke="#7B68EE" strokeWidth="2.5" strokeLinecap="round"/>
            </svg>
          </div>
          <p className="timeline-empty-title">No skills to display</p>
          <p className="timeline-empty-sub">Select a project and click "Load timeline" to view your skill progression.</p>
        </div>
      ) : (
        <div className="timeline">
          {groupedTimeline.map((group, groupIndex) => (
            <div key={group.groupKey} className="timeline-item" style={{ animationDelay: `${groupIndex * 0.06}s` }}>
              <div className={`timeline-dot${groupIndex === 0 ? ' timeline-dot--latest' : ''}`}></div>
              <div className="timeline-content">
                <div className="timeline-group-header">
                  <span className="timeline-date">
                    {MONTH_NAMES[group.month - 1]} {group.year}
                  </span>
                  <span className="timeline-group-count">{group.cards.length} skill{group.cards.length !== 1 ? 's' : ''}</span>
                </div>

                {/* Skill chips */}
                <div className="timeline-skill-chips">
                  {group.cards.map((card) => {
                    const colors = getCategoryColor(card.category)
                    return (
                      <div
                        key={card.id}
                        className="timeline-skill-chip"
                        style={{ borderLeftColor: colors.accent }}
                        onClick={() => setModalState({ type: 'detail', card })}
                        role="button"
                        tabIndex={0}
                        aria-label={`View details for ${card.skill}`}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            setModalState({ type: 'detail', card })
                          }
                        }}
                      >
                        <div className="timeline-skill-chip-top">
                          <h3 className="timeline-skill-name">{card.skill}</h3>
                          <span
                            className="timeline-category-badge"
                            style={{ background: colors.bg, color: colors.text }}
                          >
                            {card.category}
                          </span>
                        </div>
                        {card.file !== 'manual-entry' && card.file !== 'unknown' && (
                          <span
                            className="timeline-file-path"
                            title={card.file}
                          >
                            {stripTmpPrefix(card.file)}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add modal */}
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

      {/* Edit modal */}
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

      {/* Remove modal */}
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

      {/* Detail modal */}
      {modalState?.type === 'detail' && skillDetail && (
        <div className="skill-modal" onClick={() => setModalState(null)}>
          <div className="modal-content skill-detail-modal" onClick={(e) => e.stopPropagation()}>
            <span className="close" onClick={() => setModalState(null)}>&times;</span>

            {/* Header */}
            <div className="skill-detail-header">
              <h2 className="skill-detail-title">{skillDetail.skill.skill}</h2>
              <span
                className="timeline-category-badge"
                style={{
                  background: getCategoryColor(skillDetail.category).bg,
                  color: getCategoryColor(skillDetail.category).text,
                }}
              >
                {skillDetail.category}
              </span>
            </div>

            {/* Proficiency */}
            <div className="skill-detail-proficiency">
              <div className="skill-detail-proficiency-header">
                <span className="skill-detail-proficiency-label">Estimated Proficiency</span>
                <span className="skill-detail-proficiency-level">{skillDetail.proficiency.level}</span>
              </div>
              <div className="proficiency-bar">
                <div
                  className="proficiency-fill"
                  style={{
                    width: `${skillDetail.proficiency.percent}%`,
                    background: `linear-gradient(90deg, ${getCategoryColor(skillDetail.category).accent}, ${getCategoryColor(skillDetail.category).accent}dd)`,
                  }}
                ></div>
              </div>
            </div>

            {/* Stats grid */}
            <div className="skill-detail-stats">
              <div className="skill-detail-stat">
                <span className="skill-detail-stat-value">{skillDetail.appearances}</span>
                <span className="skill-detail-stat-label">Appearances</span>
              </div>
              <div className="skill-detail-stat">
                <span className="skill-detail-stat-value">{skillDetail.projects.length}</span>
                <span className="skill-detail-stat-label">Projects</span>
              </div>
              <div className="skill-detail-stat">
                <span className="skill-detail-stat-value">{skillDetail.files.length}</span>
                <span className="skill-detail-stat-label">Files</span>
              </div>
              <div className="skill-detail-stat">
                <span className="skill-detail-stat-value">{skillDetail.inCatalog ? 'Yes' : 'No'}</span>
                <span className="skill-detail-stat-label">In Catalog</span>
              </div>
            </div>

            {/* Timeline info */}
            <div className="skill-detail-section">
              <h4>Timeline</h4>
              <div className="skill-detail-dates">
                <div className="skill-detail-date-item">
                  <span className="skill-detail-date-label">First seen</span>
                  <span className="skill-detail-date-value">
                    {skillDetail.firstSeen
                      ? `${MONTH_NAMES[skillDetail.firstSeen.month - 1]} ${skillDetail.firstSeen.year}`
                      : '—'}
                  </span>
                </div>
                <div className="skill-detail-date-item">
                  <span className="skill-detail-date-label">Last seen</span>
                  <span className="skill-detail-date-value">
                    {skillDetail.lastSeen
                      ? `${MONTH_NAMES[skillDetail.lastSeen.month - 1]} ${skillDetail.lastSeen.year}`
                      : '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Projects */}
            {skillDetail.projects.length > 0 && (
              <div className="skill-detail-section">
                <h4>Projects</h4>
                <div className="skill-detail-tags">
                  {skillDetail.projects.map((p) => (
                    <span key={p} className="skill-detail-tag">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Source Files */}
            {skillDetail.files.length > 0 && (
              <div className="skill-detail-section">
                <h4>Source Files</h4>
                <div className="skill-detail-files">
                  {skillDetail.files.map((f) => (
                    <span key={f} className="skill-detail-file" title={f}>
                      {getFileName(f)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {canMutate && (
              <div className="skill-detail-actions">
                <button
                  className="apply-btn"
                  onClick={() => setModalState({ type: 'edit', card: skillDetail.skill })}
                  disabled={isBusy}
                >
                  Edit
                </button>
                <button
                  className="reset-btn skill-detail-remove-btn"
                  onClick={() => setModalState({ type: 'remove', card: skillDetail.skill })}
                  disabled={isBusy}
                >
                  Remove
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SkillsTimeline
