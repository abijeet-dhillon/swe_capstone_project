import type { FilteredProject } from '../api'

// TODO: Filter by processing status (Queued/Processing/Complete/Failed) — no backend status field found.
// Using project_type as the available filter dimension instead.

export type TabKey = 'all' | 'solo' | 'collab'

const TAB_LABELS: { key: TabKey; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'solo', label: 'Solo' },
  { key: 'collab', label: 'Collaborative' },
]

export function FilterTabs({
  active,
  onChange,
  projects,
}: {
  active: TabKey
  onChange: (key: TabKey) => void
  projects: FilteredProject[]
}) {
  const counts: Record<TabKey, number> = {
    all: projects.length,
    solo: projects.filter((p) => !p.is_collaborative).length,
    collab: projects.filter((p) => p.is_collaborative).length,
  }

  return (
    <div className="filter-tabs">
      {TAB_LABELS.map((tab) => (
        <button
          key={tab.key}
          className={`filter-tab ${active === tab.key ? 'filter-tab--active' : ''}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.label}
          <span className="filter-tab__count">{counts[tab.key]}</span>
        </button>
      ))}
    </div>
  )
}
