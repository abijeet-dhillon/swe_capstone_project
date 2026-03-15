import type { FilteredProject } from '../api'

// TODO: Stats for Completed/Active/Failed — no backend processing status tracking found.
// The backend has no pipeline status field on projects. Only total count + type breakdown available.

export function StatsCards({ projects }: { projects: FilteredProject[] }) {
  const total = projects.length
  const collaborative = projects.filter((p) => p.is_collaborative).length
  const solo = total - collaborative
  const totalLines = projects.reduce((sum, p) => sum + (p.total_lines ?? 0), 0)

  const cards = [
    { label: 'Total Projects', value: total, accent: 'purple' },
    { label: 'Collaborative', value: collaborative, accent: 'blue' },
    { label: 'Solo Projects', value: solo, accent: 'green' },
    { label: 'Total Lines', value: totalLines.toLocaleString(), accent: 'pink' },
  ]

  return (
    <div className="stats-row">
      {cards.map((c) => (
        <div key={c.label} className={`stat-card stat-card--${c.accent}`}>
          <div className="stat-card__decoration" />
          <span className="stat-card__value">{c.value}</span>
          <span className="stat-card__label">{c.label}</span>
        </div>
      ))}
    </div>
  )
}
