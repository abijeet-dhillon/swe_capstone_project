import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../src/renderer/src/App'

vi.mock('../src/renderer/src/api', () => ({
  filterProjects: vi.fn().mockResolvedValue({ total: 0, projects: [], filter_applied: {} }),
  getFilterOptions: vi.fn().mockResolvedValue({
    sort_options: [],
    project_types: [],
    complexity_levels: [],
  }),
  getProjectDetail: vi.fn().mockResolvedValue({}),
  getPortfolio: vi.fn().mockResolvedValue({}),
  getResume: vi.fn().mockResolvedValue({ bullets: [] }),
  getProjectSkills: vi.fn().mockResolvedValue([]),
  listSkillsCatalog: vi.fn().mockResolvedValue(['python']),
  getSkillsByYear: vi.fn().mockResolvedValue({ year: 2026, timeline: [] }),
  addProjectSkills: vi.fn().mockResolvedValue({ project_id: 1, skills: [] }),
  editProjectSkills: vi.fn().mockResolvedValue({ project_id: 1, skills: [] }),
  removeProjectSkills: vi.fn().mockResolvedValue({ project_id: 1, skills: [] }),
  getChronologicalSkills: vi.fn().mockResolvedValue({
    project_id: 1,
    project_name: 'Alpha',
    zip_hash: 'ziphash01',
    total_events: 0,
    categories: [],
    timeline: [],
  }),
  getChronologicalSkillsByProjectId: vi.fn().mockResolvedValue({
    project_id: 1,
    project_name: 'Alpha',
    zip_hash: 'ziphash01',
    total_events: 0,
    categories: [],
    timeline: [],
  }),
  getChronologicalProjects: vi.fn().mockResolvedValue({
    total_projects: 1,
    projects: [
      {
        project_name: 'Alpha',
        zip_hash: 'ziphash01',
        zip_path: '/tmp/a.zip',
        created_at: '2026-01-01T00:00:00',
        is_git_repo: true,
        languages: [],
        total_commits: 0,
        total_contributors: 0,
      },
    ],
  }),
  getProjectTimelineLookup: vi.fn().mockResolvedValue([
    { project_id: 1, project_name: 'Alpha', zip_hash: 'ziphash01' },
  ]),
}))

describe('App Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders sidebar brand and navigation', () => {
    render(<App />)
    expect(screen.getByText('ResumeForge')).toBeInTheDocument()
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Projects').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Timeline').length).toBeGreaterThan(0)
  })

  it('renders page header and footer', () => {
    render(<App />)
    expect(screen.getByText('Your workspace overview and quick actions')).toBeInTheDocument()
    expect(screen.getByText('COSC 499 — Digital Work Artifact Miner')).toBeInTheDocument()
  })

  it('renders upload zone and feature cards on dashboard', () => {
    render(<App />)
    expect(screen.getByText('Drop your .zip folder here')).toBeInTheDocument()
    expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    expect(screen.getByText('One-Page Resume')).toBeInTheDocument()
    expect(screen.getByText('Web Portfolio')).toBeInTheDocument()
  })

  it('defaults to private mode with customization enabled', () => {
    render(<App />)
    expect(screen.getByText('Customization controls are enabled.')).toBeInTheDocument()
    const customizeButtons = screen.getAllByRole('button', { name: 'Customize' })
    const enabled = customizeButtons.filter((b) => !b.hasAttribute('disabled'))
    expect(enabled.length).toBeGreaterThan(0)
  })

  it('switches to public mode and disables customize buttons', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Public' }))
    expect(screen.getByText('Customization controls are disabled in public mode.')).toBeInTheDocument()
    const customizeButtons = screen.getAllByRole('button', { name: 'Customize' })
    customizeButtons.forEach((b) => expect(b).toBeDisabled())
  })

  it('filters feature cards by search query', () => {
    render(<App />)
    fireEvent.change(screen.getByLabelText('Search sections'), {
      target: { value: 'heatmap' },
    })
    expect(screen.getByText('Project Activity Heatmap')).toBeInTheDocument()
    expect(screen.queryByText('One-Page Resume')).not.toBeInTheDocument()
  })

  it('filters feature cards by category', () => {
    render(<App />)
    fireEvent.change(screen.getByLabelText('Filter category'), {
      target: { value: 'timeline' },
    })
    expect(screen.getByText('Skills Timeline')).toBeInTheDocument()
    expect(screen.queryByText('Web Portfolio')).not.toBeInTheDocument()
  })

  it('switches to Projects view when nav clicked', () => {
    render(<App />)
    fireEvent.click(screen.getAllByText('Projects')[0])
    expect(screen.getByText('Search, filter, and explore your analyzed projects')).toBeInTheDocument()
  })

  it('switches to Timeline view when nav clicked', () => {
    render(<App />)
    fireEvent.click(screen.getAllByText('Timeline')[0])
    expect(screen.getByRole('button', { name: 'Load timeline' })).toBeInTheDocument()
  })

  it('renders header refresh action in timeline view', () => {
    render(<App />)
    fireEvent.click(screen.getAllByText('Timeline')[0])
    const refresh = screen.getByRole('button', { name: 'Refresh skill catalog' })
    expect(refresh).toBeInTheDocument()
    fireEvent.click(refresh)
  })
})
