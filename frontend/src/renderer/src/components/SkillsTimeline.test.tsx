import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
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

function seedMocks(): void {
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
  mocked.addProjectSkills.mockResolvedValue({ project_id: 7, skills: ['graphql'] })
  mocked.editProjectSkills.mockResolvedValue({ project_id: 7, skills: ['golang'] })
  mocked.removeProjectSkills.mockResolvedValue({ project_id: 7, skills: [] })
}

async function waitForTimelineControls(): Promise<void> {
  await waitFor(() => expect(screen.getByLabelText('Project selector')).toBeInTheDocument())
  await waitFor(() => expect(screen.getByRole('button', { name: 'Load timeline' })).toBeEnabled())
}

async function selectAlphaAndLoad(): Promise<void> {
  await waitForTimelineControls()
  fireEvent.change(screen.getByLabelText('Project selector'), { target: { value: 'ziphash01::Alpha' } })
  fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))
  await waitFor(() => expect(mocked.getChronologicalSkillsByProjectId).toHaveBeenCalledWith(7))
}

describe('SkillsTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    seedMocks()
  })

  it('renders without crashing and shows timeline controls', async () => {
    expect(() => render(<SkillsTimeline />)).not.toThrow()

    await waitForTimelineControls()
    expect(screen.getByRole('button', { name: 'Load timeline' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'All projects' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Project ID' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'ZIP + Name' })).toBeInTheDocument()
  })

  it('shows loading state while project options are being fetched', () => {
    mocked.getChronologicalProjects.mockImplementation(() => new Promise(() => undefined))
    mocked.getProjectTimelineLookup.mockImplementation(() => new Promise(() => undefined))
    mocked.listSkillsCatalog.mockImplementation(() => new Promise(() => undefined))

    render(<SkillsTimeline />)
    expect(screen.getByText('Loading skills data...')).toBeInTheDocument()
  })

  it('loads timeline using project-id lookup mode', async () => {
    render(<SkillsTimeline />)
    await selectAlphaAndLoad()

    expect(screen.getByText('python')).toBeInTheDocument()
    expect(mocked.getChronologicalSkillsByProjectId).toHaveBeenCalledWith(7)
  })

  it('loads timeline using zip-name lookup mode', async () => {
    render(<SkillsTimeline />)
    await waitForTimelineControls()

    fireEvent.change(screen.getByLabelText('Project selector'), { target: { value: 'ziphash01::Alpha' } })
    fireEvent.change(screen.getByLabelText('Lookup mode'), { target: { value: 'zip-name' } })
    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))

    await waitFor(() =>
      expect(mocked.getChronologicalSkills).toHaveBeenCalledWith({
        zipHash: 'ziphash01',
        projectName: 'Alpha',
      }),
    )
    expect(mocked.getChronologicalSkillsByProjectId).not.toHaveBeenCalled()
  })

  it('loads all projects when All projects is selected', async () => {
    render(<SkillsTimeline />)
    await waitForTimelineControls()

    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))

    await waitFor(() =>
      expect(mocked.getChronologicalSkills).toHaveBeenCalledWith({
        zipHash: 'ziphash01',
        projectName: 'Alpha',
      }),
    )
    expect(screen.getByText('python')).toBeInTheDocument()
  })

  it('uses skills/year when All projects + specific year is selected', async () => {
    render(<SkillsTimeline />)
    await waitForTimelineControls()

    const currentYear = String(new Date().getFullYear())
    fireEvent.change(screen.getByLabelText('Year filter'), { target: { value: currentYear } })
    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))

    await waitFor(() => expect(mocked.getSkillsByYear).toHaveBeenCalledWith(Number(currentYear)))
    expect(screen.getByText('writing')).toBeInTheDocument()
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
    await selectAlphaAndLoad()

    expect(screen.getAllByRole('heading', { name: 'python' })).toHaveLength(1)
    expect(screen.getByText('alpha/new.py')).toBeInTheDocument()
    expect(screen.queryByText('alpha/old.py')).not.toBeInTheDocument()
  })

  it('handles add skill modal flow', async () => {
    render(<SkillsTimeline />)
    await selectAlphaAndLoad()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Add skill' })).toBeEnabled())

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
    await selectAlphaAndLoad()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Edit' })).toBeEnabled())

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
    await selectAlphaAndLoad()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Remove' })).toBeEnabled())

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    fireEvent.click(screen.getByRole('button', { name: 'No' }))
    expect(mocked.removeProjectSkills).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    fireEvent.click(screen.getByRole('button', { name: 'Yes' }))

    await waitFor(() =>
      expect(mocked.removeProjectSkills).toHaveBeenCalledWith({
        project_id: 7,
        skills: ['python'],
      }),
    )
  })

  it('shows inline error and keeps controls available when timeline request fails', async () => {
    mocked.getChronologicalSkillsByProjectId.mockRejectedValueOnce(new Error('boom'))

    render(<SkillsTimeline />)
    await waitForTimelineControls()

    fireEvent.change(screen.getByLabelText('Project selector'), { target: { value: 'ziphash01::Alpha' } })
    fireEvent.click(screen.getByRole('button', { name: 'Load timeline' }))

    await waitFor(() => expect(screen.getByText('boom')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Load timeline' })).toBeInTheDocument()
  })

  it('refreshes global catalog when refresh nonce changes', async () => {
    const { rerender } = render(<SkillsTimeline refreshNonce={0} />)
    await waitFor(() => expect(mocked.listSkillsCatalog).toHaveBeenCalledTimes(1))

    rerender(<SkillsTimeline refreshNonce={1} />)
    await waitFor(() => expect(mocked.listSkillsCatalog).toHaveBeenCalledTimes(2))
  })
})
