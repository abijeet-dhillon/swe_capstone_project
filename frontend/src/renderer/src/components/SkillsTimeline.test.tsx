import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SkillsTimeline from './SkillsTimeline'
import * as api from '../api'

vi.mock('../api', () => ({
  addProjectSkills: vi.fn(),
  editProjectSkills: vi.fn(),
  getChronologicalProjects: vi.fn(),
  getChronologicalSkills: vi.fn(),
  getChronologicalSkillsByProjectId: vi.fn(),
  getProjectSkills: vi.fn(),
  getProjectTimelineLookup: vi.fn(),
  getSkillsByYear: vi.fn(),
  listSkillsCatalog: vi.fn(),
  removeProjectSkills: vi.fn(),
}))

const mocked = vi.mocked(api)

function seedMocks() {
  mocked.getChronologicalProjects.mockResolvedValue({
    total_projects: 1,
    projects: [
      {
        project_name: 'Alpha',
        zip_hash: 'ziphash01',
        zip_path: '/tmp/alpha.zip',
        created_at: '2026-01-01T00:00:00',
        is_git_repo: true,
        languages: ['Python'],
        total_commits: 12,
        total_contributors: 1,
      },
    ],
  })
  mocked.getProjectTimelineLookup.mockResolvedValue([
    { project_id: 7, project_name: 'Alpha', zip_hash: 'ziphash01' },
  ])
  mocked.listSkillsCatalog.mockResolvedValue(['python', 'fastapi'])
  mocked.getChronologicalSkillsByProjectId.mockResolvedValue({
    project_id: 7,
    project_name: 'Alpha',
    zip_hash: 'ziphash01',
    total_events: 1,
    categories: ['code'],
    timeline: [
      {
        file: 'alpha/main.py',
        timestamp: '2026-02-02T10:00:00',
        category: 'code',
        skills: ['python'],
        metadata: {},
      },
    ],
  })
  mocked.getChronologicalSkills.mockResolvedValue({
    project_id: 7,
    project_name: 'Alpha',
    zip_hash: 'ziphash01',
    total_events: 1,
    categories: ['code'],
    timeline: [
      {
        file: 'alpha/main.py',
        timestamp: '2026-02-02T10:00:00',
        category: 'code',
        skills: ['python'],
        metadata: {},
      },
    ],
  })
  const currentYear = new Date().getFullYear()
  mocked.getSkillsByYear.mockResolvedValue({
    year: currentYear,
    timeline: [
      {
        file: 'global/event.txt',
        timestamp: `${currentYear}-03-03T11:00:00`,
        category: 'text',
        skills: ['writing'],
        metadata: {},
      },
    ],
  })
  mocked.getProjectSkills.mockResolvedValue([{ skill_name: 'python' }])
  mocked.addProjectSkills.mockResolvedValue({ project_id: 7, skills: ['python', 'graphql'] })
  mocked.editProjectSkills.mockResolvedValue({ project_id: 7, skills: ['golang'] })
  mocked.removeProjectSkills.mockResolvedValue({ project_id: 7, skills: [] })
}

async function selectAlphaAndLoad(): Promise<void> {
  fireEvent.change(screen.getByLabelText('Project selector'), { target: { value: 'ziphash01::Alpha' } })
  fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))
  await waitFor(() => expect(mocked.getChronologicalSkillsByProjectId).toHaveBeenCalledWith(7))
}

// Mock the hook
vi.mock('../hooks/useSkillsTimeline', () => ({
  useSkillsTimeline: vi.fn()
}))

import { useSkillsTimeline } from '../hooks/useSkillsTimeline'

const mockSkills = [
  {
    id: 1,
    name: 'JavaScript',
    category: 'language' as const,
    startDate: '2020-05',
    proficiency: 85,
    yearsExperience: 3.7,
    description: 'Deep understanding of closures, prototypes, async patterns, and functional programming.',
    milestones: [
      { date: '2020-05', level: 'beginner' as const, description: 'Variables, functions, and basic DOM manipulation' },
      { date: '2020-09', level: 'intermediate' as const, description: 'ES6+ features and array methods mastery' }
    ],
    projects: ['Interactive Web Apps', 'API Integrations'],
    depthLevel: 4
  },
  {
    id: 2,
    name: 'React',
    category: 'framework' as const,
    startDate: '2020-12',
    proficiency: 80,
    yearsExperience: 1.0,
    description: 'Expert in hooks, context, performance optimization, and custom component patterns.',
    milestones: [
      { date: '2020-12', level: 'beginner' as const, description: 'Components, props, and basic state' },
      { date: '2021-04', level: 'intermediate' as const, description: 'Hooks and functional components mastery' }
    ],
    projects: ['Task Manager App', 'Social Media Dashboard'],
    depthLevel: 4
  }
]

describe('SkillsTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: true,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('Loading skills data...')).toBeInTheDocument()
  })

  it('renders error state', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: false,
      error: 'Failed to fetch',
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('Error loading skills: Failed to fetch')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('renders empty state when no skills', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('No skills data available. Upload a project to see your skills timeline.')).toBeInTheDocument()
  })

  it('renders timeline with skills', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      expect(screen.getByText('All Skills')).toBeInTheDocument()
      expect(screen.getByText('Languages')).toBeInTheDocument()
      expect(screen.getByText('Frameworks')).toBeInTheDocument()
      expect(screen.getByText('Backends')).toBeInTheDocument()
      expect(screen.getByText('Tools')).toBeInTheDocument()
    })
  })

  it('displays skill items', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      expect(screen.getByText('JavaScript')).toBeInTheDocument()
      expect(screen.getByText('React')).toBeInTheDocument()
    })
  })

  it('filters skills by category', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Languages'))
      expect(screen.getByText('JavaScript')).toBeInTheDocument()
      expect(screen.queryByText('React')).not.toBeInTheDocument()
    })
  })

  it('opens modal when skill is clicked', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('JavaScript').closest('.timeline-content')!)
      expect(screen.getByText('Learning Progression')).toBeInTheDocument()
      expect(screen.getByText('Projects Built')).toBeInTheDocument()
    })
  })

  it('closes modal when close button is clicked', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('JavaScript').closest('.timeline-content')!)
      fireEvent.click(screen.getByText('×'))
      expect(screen.queryByText('Learning Progression')).not.toBeInTheDocument()
    })
    seedMocks()
  })

  it('loads timeline using project-id lookup mode', async () => {
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    await selectAlphaAndLoad()
    expect(screen.getByText('python')).toBeInTheDocument()
  })

  it('deduplicates repeated skills and keeps the most recent event', async () => {
    mocked.getChronologicalSkillsByProjectId.mockResolvedValueOnce({
      project_id: 7,
      project_name: 'Alpha',
      zip_hash: 'ziphash01',
      total_events: 2,
      categories: ['code'],
      timeline: [
        {
          file: 'alpha/old.py',
          timestamp: '2025-01-01T10:00:00',
          category: 'code',
          skills: ['python'],
          metadata: {},
        },
        {
          file: 'alpha/new.py',
          timestamp: '2026-01-01T10:00:00',
          category: 'code',
          skills: ['python'],
          metadata: {},
        },
      ],
    })
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    await selectAlphaAndLoad()
    expect(screen.getAllByRole('heading', { name: 'python' })).toHaveLength(1)
    expect(screen.getByText('alpha/new.py')).toBeInTheDocument()
    expect(screen.queryByText('alpha/old.py')).not.toBeInTheDocument()
  })

  it('uses skills/year when All projects + specific year is selected', async () => {
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    const currentYear = String(new Date().getFullYear())
    fireEvent.change(screen.getByLabelText('Year filter'), { target: { value: currentYear } })
    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))
    await waitFor(() => expect(mocked.getSkillsByYear).toHaveBeenCalledWith(Number(currentYear)))
    expect(screen.getByText('writing')).toBeInTheDocument()
  })

  it('handles add skill modal flow', async () => {
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    await selectAlphaAndLoad()

    fireEvent.click(screen.getByRole('button', { name: 'Add skill' }))
    fireEvent.change(screen.getByLabelText('Add skills input'), { target: { value: 'graphql' } })
    fireEvent.change(screen.getByLabelText('Add month'), { target: { value: '4' } })
    fireEvent.change(screen.getByLabelText('Add year'), { target: { value: '2026' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))

    await waitFor(() =>
      expect(mocked.addProjectSkills).toHaveBeenCalledWith({
        project_id: 7,
        skills: ['graphql'],
        month: 4,
        year: 2026,
      }),
    )
    expect(screen.getByText('graphql')).toBeInTheDocument()
  })

  it('handles edit skill modal flow', async () => {
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    await selectAlphaAndLoad()

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByLabelText('Edit skill input'), { target: { value: 'golang' } })
    fireEvent.change(screen.getByLabelText('Edit month'), { target: { value: '5' } })
    fireEvent.change(screen.getByLabelText('Edit year'), { target: { value: '2026' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(mocked.editProjectSkills).toHaveBeenCalledWith({
        project_id: 7,
        old: 'python',
        new: 'golang',
        month: 5,
        year: 2026,
      }),
    )
    expect(screen.getByText('golang')).toBeInTheDocument()
  })

  it('handles remove confirmation flow with Yes/No', async () => {
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    await selectAlphaAndLoad()

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    fireEvent.click(screen.getByRole('button', { name: 'No' }))
    expect(mocked.removeProjectSkills).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    fireEvent.click(screen.getByRole('button', { name: 'Yes' }))
    await waitFor(() =>
      expect(mocked.removeProjectSkills).toHaveBeenCalledWith({ project_id: 7, skills: ['python'] }),
    )
  })

  it('shows loading error when timeline request fails', async () => {
    mocked.getChronologicalSkillsByProjectId.mockRejectedValueOnce(new Error('boom'))
    render(<SkillsTimeline />)
    await waitFor(() => expect(mocked.getChronologicalProjects).toHaveBeenCalled())
    fireEvent.change(screen.getByLabelText('Project selector'), { target: { value: 'ziphash01::Alpha' } })
    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))
    await waitFor(() => expect(screen.getByText('boom')).toBeInTheDocument())
  })

  it('refreshes global catalog when refresh nonce changes', async () => {
    const { rerender } = render(<SkillsTimeline refreshNonce={0} />)
    await waitFor(() => expect(mocked.listSkillsCatalog).toHaveBeenCalledTimes(1))
    rerender(<SkillsTimeline refreshNonce={1} />)
    await waitFor(() => expect(mocked.listSkillsCatalog).toHaveBeenCalledTimes(2))
  })
})