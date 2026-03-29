import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from '../src/renderer/src/App'

vi.mock('../src/renderer/src/api', () => ({
  filterProjects: vi.fn().mockResolvedValue({
    total: 3,
    projects: [
      {
        project_info_id: 1,
        project_name: 'docs',
        slug: 'docs',
        project_created_at: '2026-03-01T00:00:00',
        total_files: 5,
        total_lines: 120,
        total_commits: 7,
        total_contributors: 1,
        is_collaborative: false,
      },
      {
        project_info_id: 2,
        project_name: 'the-project-sunset',
        slug: 'the-project-sunset',
        project_created_at: '2026-03-02T00:00:00',
        total_files: 9,
        total_lines: 420,
        total_commits: 14,
        total_contributors: 2,
        is_collaborative: true,
      },
      {
        project_info_id: 3,
        project_name: 'kestrel-hft',
        slug: 'kestrel-hft',
        project_created_at: '2026-03-03T00:00:00',
        total_files: 11,
        total_lines: 820,
        total_commits: 20,
        total_contributors: 2,
        is_collaborative: true,
      },
    ],
    filter_applied: {},
  }),
  getFilterOptions: vi.fn().mockResolvedValue({
    sort_options: [],
    project_types: [],
    complexity_levels: [],
  }),
  generateResumePdf: vi.fn().mockResolvedValue({
    blob: new Blob(['resume'], { type: 'application/pdf' }),
    filename: 'resume.pdf',
  }),
  generatePortfolioSite: vi.fn().mockResolvedValue({
    status: 'ok',
    url: 'http://localhost:3000',
    server_started: true,
    message: 'Portfolio generated.',
  }),
  getProjectDetail: vi.fn().mockResolvedValue({}),
  getPortfolio: vi.fn().mockResolvedValue({}),
  getResume: vi.fn().mockResolvedValue({ bullets: [] }),
  getProjectSkills: vi.fn().mockResolvedValue([]),
  updateProject: vi.fn().mockResolvedValue({ status: 'ok', project_id: 1 }),
  removeProject: vi.fn().mockResolvedValue({ status: 'ok', project_id: 1 }),
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
  getProfile: vi.fn().mockResolvedValue({
    user_id: 'default',
    name: 'Jane Smith',
    contact: {
      phone_number: '555-0000',
      email: 'jane@example.com',
      linkedin_url: 'https://linkedin.com/in/jane',
      github_url: 'https://github.com/jane',
      linkedin_label: 'LinkedIn',
      github_label: 'GitHub',
    },
    education: [
      { school: 'UVic', location: 'Victoria', degree: 'BSc', from: '2022', to: '2026', still_studying: false },
    ],
    awards: [],
    portfolio: {
      title: 'Full-Stack Developer',
      about_me: 'Bio',
      years_of_experience: '3+',
      open_source_contribution: '10+',
    },
    git_identifier: 'jane@example.com',
  }),
  updateProfile: vi.fn().mockResolvedValue({ status: 'ok' }),
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
    expect(screen.getByRole('button', { name: 'Generate Resume' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Generate Portfolio' })).toBeEnabled()
  })

  it('switches to public mode and disables customize buttons', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Public' }))
    expect(screen.getByText('Customization controls are disabled in public mode.')).toBeInTheDocument()
    const customizeButtons = screen.getAllByRole('button', { name: 'Customize' })
    customizeButtons.forEach((b) => expect(b).toBeDisabled())
  })

  it('opens the resume modal with grouped sections and footer actions', async () => {
    render(<App />)
    await screen.findByText('3 projects')
    fireEvent.click(screen.getByRole('button', { name: 'Generate Resume' }))

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Generate One-Page Resume')).toBeInTheDocument()
    expect(screen.getByText('Choose the work samples you want highlighted on this one-page resume.')).toBeInTheDocument()
    expect(screen.getByText('Saved Profile Data')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generate PDF' })).toBeInTheDocument()
  })

  it('shows resume validation in the modal footer flow', async () => {
    render(<App />)
    await screen.findByText('3 projects')
    fireEvent.click(screen.getByRole('button', { name: 'Generate Resume' }))

    await screen.findByRole('dialog')
    const firstProject = await screen.findByRole('checkbox', { name: 'docs' })
    fireEvent.click(firstProject)
    fireEvent.click(screen.getByRole('button', { name: 'Generate PDF' }))

    expect(await screen.findByText('Choose at least one project.')).toBeInTheDocument()
  })

  it('opens the portfolio modal with grouped profile fields and clear selection state', async () => {
    render(<App />)
    await screen.findByText('3 projects')
    fireEvent.click(screen.getByRole('button', { name: 'Generate Portfolio' }))

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Generate Web Portfolio')).toBeInTheDocument()
    expect(screen.getByText('Choose between two and four projects to feature on the portfolio page.')).toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Title')).toBeInTheDocument()
    expect(screen.getByText('2/4 selected')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Generate Portfolio' }).length).toBeGreaterThan(1)
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

  it('switches to Timeline view when nav clicked', async () => {
    render(<App />)
    fireEvent.click(screen.getAllByText('Timeline')[0])
    await waitFor(() => expect(screen.getByRole('button', { name: 'Load timeline' })).toBeInTheDocument())
  })

  it('renders header refresh action in timeline view', () => {
    render(<App />)
    fireEvent.click(screen.getAllByText('Timeline')[0])
    const refresh = screen.getByRole('button', { name: 'Refresh skill catalog' })
    expect(refresh).toBeInTheDocument()
    fireEvent.click(refresh)
  })
})
