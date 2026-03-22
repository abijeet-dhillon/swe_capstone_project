import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  addProjectSkills,
  editProjectSkills,
  getChronologicalSkills,
  getChronologicalSkillsByProjectId,
  getChronologicalProjects,
  getSkillsByYear,
  listSkillsCatalog,
  removeProjectSkills,
  removeProject,
  updateProject,
} from './api'

function ok(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response
}

describe('timeline api wrappers', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
  })

  it('loads global skill catalog', async () => {
    fetchMock.mockResolvedValue(ok(['python']))
    await listSkillsCatalog()
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/skills', undefined)
  })

  it('sends add/edit/remove payloads to skills mutation endpoints', async () => {
    fetchMock.mockResolvedValue(ok({ project_id: 1, skills: ['python'] }))
    await addProjectSkills({ project_id: 1, skills: ['python'] })
    await editProjectSkills({ project_id: 1, old: 'python', new: 'fastapi' })
    await removeProjectSkills({ project_id: 1, skills: ['fastapi'] })

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/skills/add',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/skills/edit',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ project_id: 1, old: 'python', new: 'fastapi' }),
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      'http://localhost:8000/skills/remove',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('builds year query for skills/year', async () => {
    fetchMock.mockResolvedValue(ok({ year: 2025, timeline: [] }))
    await getSkillsByYear(2025)
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/skills/year?year=2025', undefined)
  })

  it('builds chronological lookup routes', async () => {
    fetchMock.mockResolvedValue(ok({ timeline: [] }))
    await getChronologicalSkills({ zipHash: 'zip123', projectName: 'ProjectX' })
    await getChronologicalSkillsByProjectId(11)
    await getChronologicalProjects(25)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/chronological/skills?zip_hash=zip123&project_name=ProjectX',
      undefined,
    )
    expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/chronological/skills/11', undefined)
    expect(fetchMock).toHaveBeenNthCalledWith(3, 'http://localhost:8000/chronological/projects?limit=25', undefined)
  })

  it('sends patch/delete payloads to project mutation endpoints', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'ok', project_id: 9 }))
    await updateProject(9, { project_name: 'Renamed', summary: 'Updated summary' })
    await removeProject(9)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://localhost:8000/projects/9',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ project_name: 'Renamed', summary: 'Updated summary' }),
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://localhost:8000/projects/9',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })
})
