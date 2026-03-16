import type { FilteredProject } from '../api'

// TODO: Priority indicator — no priority field in backend models.
// TODO: Score (circular progress ring) — no scoring/grading endpoint found.
// TODO: Status badge (Queued/Processing/Complete/Failed) — no pipeline status tracking.

const AVATAR_COLORS = [
  'linear-gradient(135deg, #7B68EE, #6C5CE7)',
  'linear-gradient(135deg, #00B894, #00CEC9)',
  'linear-gradient(135deg, #E84393, #FD79A8)',
  'linear-gradient(135deg, #0984E3, #74B9FF)',
  'linear-gradient(135deg, #FDCB6E, #F39C12)',
  'linear-gradient(135deg, #D63031, #FF7675)',
]

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return iso
  }
}

export function ProjectTable({
  projects,
  selectedId,
  onSelect,
}: {
  projects: FilteredProject[]
  selectedId: number | null
  onSelect: (id: number) => void
}) {
  if (projects.length === 0) {
    return <p className="empty-state">No projects found. Upload a .zip to get started.</p>
  }

  return (
    <div className="project-table">
      <div className="project-table__header">
        <span className="col-name">Project</span>
        <span className="col-type">Type</span>
        <span className="col-complexity">Complexity</span>
        <span className="col-date">Uploaded</span>
        <span className="col-stats">Lines</span>
        <span className="col-stats">Commits</span>
      </div>

      {projects.map((p, i) => (
        <div
          key={p.project_info_id}
          className={`project-table__row ${selectedId === p.project_info_id ? 'project-table__row--selected' : ''}`}
          onClick={() => onSelect(p.project_info_id)}
        >
          <div className="col-name">
            <span
              className="project-avatar"
              style={{ background: AVATAR_COLORS[i % AVATAR_COLORS.length] }}
            >
              {getInitials(p.project_name)}
            </span>
            <div className="project-name-group">
              <span className="project-name-text">{p.project_name}</span>
              {p.tagline && <span className="project-tagline-text">{p.tagline}</span>}
            </div>
          </div>
          <div className="col-type">
            {p.project_type && (
              <span className="pill info">{p.project_type}</span>
            )}
          </div>
          <div className="col-complexity">
            {p.complexity && (
              <span className={`pill ${p.complexity === 'complex' ? 'highlight' : p.complexity === 'moderate' ? 'coming-soon' : 'ready'}`}>
                {p.complexity}
              </span>
            )}
          </div>
          <div className="col-date">{formatDate(p.project_created_at)}</div>
          <div className="col-stats">{(p.total_lines ?? 0).toLocaleString()}</div>
          <div className="col-stats">{p.total_commits ?? 0}</div>
        </div>
      ))}
    </div>
  )
}
