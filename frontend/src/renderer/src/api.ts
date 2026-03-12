const API_BASE = 'http://localhost:8000'

export type ProjectFilter = {
  date_range?: { start?: string; end?: string }
  languages?: string[]
  frameworks?: string[]
  skills?: string[]
  project_type?: string
  complexity?: string
  metrics?: Record<string, number | undefined>
  search_text?: string
  sort_by?: string
  limit?: number
  offset?: number
}

export type FilteredProject = {
  project_info_id: number
  project_name: string
  slug: string
  project_created_at: string
  total_files: number
  total_lines: number
  total_commits: number
  total_contributors: number
  tagline?: string
  description?: string
  project_type?: string
  complexity?: string
  is_collaborative?: boolean
  summary?: string
}

export type FilterResponse = {
  total: number
  projects: FilteredProject[]
  filter_applied: Record<string, unknown>
}

export type FilterOptions = {
  sort_options: { value: string; label: string }[]
  project_types: { value: string; label: string }[]
  complexity_levels: string[]
}

export async function filterProjects(filter: ProjectFilter): Promise<FilterResponse> {
  const res = await fetch(`${API_BASE}/filter/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filter),
  })
  if (!res.ok) throw new Error(`Filter request failed: ${res.statusText}`)
  return res.json()
}

export async function getFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${API_BASE}/filter/options`)
  if (!res.ok) throw new Error(`Failed to load filter options: ${res.statusText}`)
  return res.json()
}
