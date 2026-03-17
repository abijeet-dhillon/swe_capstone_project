const API_BASE = 'http://localhost:8000'

// ─── Filter Types (existing) ───────────────────────────────────────

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

// ─── Project Types ─────────────────────────────────────────────────

export type ProjectListItem = {
  project_info_id: number
  project_name: string
  zip_hash: string
  project_created_at: string
  total_files: number
  total_lines: number
  total_commits: number
  total_contributors: number
  slug?: string
  tagline?: string
  description?: string
  project_type?: string
  complexity?: string
  is_collaborative?: boolean
  summary?: string
}

export type ProjectDetail = {
  project_info_id: number
  project_name: string
  zip_hash: string
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
  user_role?: string
  thumbnail?: { image_path: string; mime_type: string } | null
}

// ─── Portfolio Types ───────────────────────────────────────────────

export type PortfolioTemplate = {
  id: string
  name: string
  description: string
  emphasis: string[]
}

export type PortfolioData = {
  project_name: string
  tagline?: string
  description?: string
  summary?: string
  key_features?: string[]
  project_type?: string
  complexity?: string
  is_collaborative?: boolean
  skills?: string[]
  metrics?: {
    total_files: number
    total_lines: number
    total_commits: number
    total_contributors: number
  }
  evolution?: {
    first_commit?: string
    last_commit?: string
    contributors?: string[]
  }
}

// ─── Resume Types ──────────────────────────────────────────────────

export type ResumeData = {
  project_name: string
  bullets: string[]
  user_role?: string
}

// ─── Skills Types ──────────────────────────────────────────────────

export type ProjectSkill = {
  skill_name: string
  category?: string
  evidence?: string
}

export type SkillCatalogResponse = {
  project_id: number
  skills: string[]
}

export type SkillsAddRequest = {
  project_id: number
  skills: string[]
  month?: number
  year?: number
  timestamp?: string
}

export type SkillsRemoveRequest = {
  project_id: number
  skills: string[]
}

export type SkillsEditRequest = {
  project_id: number
  old?: string
  new?: string
  skills?: string[]
  month?: number
  year?: number
  timestamp?: string
}

export type ChronologicalSkillEvent = {
  file: string
  timestamp: string
  category: string
  skills: string[]
  metadata: Record<string, unknown>
}

export type ChronologicalSkillsResponse = {
  project_id?: number
  project_name?: string
  zip_hash: string
  total_events: number
  categories: string[]
  timeline: ChronologicalSkillEvent[]
}

export type ChronologicalProject = {
  project_name: string
  zip_hash: string
  zip_path: string
  created_at: string
  is_git_repo: boolean
  languages: string[]
  total_commits: number
  total_contributors: number
}

export type ChronologicalProjectsResponse = {
  total_projects: number
  projects: ChronologicalProject[]
}

export type ProjectTimelineLookup = {
  project_id: number
  project_name: string
  zip_hash: string
}

// ─── Consent Types ─────────────────────────────────────────────────

export type ConsentRequest = {
  user_id: string
  zip_path: string
  llm_consent: boolean
  data_access_consent: boolean
  resume_owner_name?: string
}

export type GitIdentifierRequest = {
  user_id: string
  git_identifier: string
}

// ─── Upload Types ──────────────────────────────────────────────────

export type UploadRequest = {
  zip_path: string
  user_id: string
}

export type UploadResponse = {
  status: string
  zip_hash?: string
  ingest_id?: number
  projects?: string[]
  resume_pdf_path?: string | null
  representation?: Record<string, unknown>
  represented_output?: Record<string, unknown>
}

export type ResumeEducationInput = {
  school: string
  degree?: string
  location?: string
  start_date?: string
  end_date?: string
  is_current?: boolean
  expected_graduation?: string
}

export type ResumePdfRequest = {
  resume_owner_name: string
  project_ids: number[]
  phone?: string
  email?: string
  linkedin_url?: string
  linkedin_label?: string
  github_url?: string
  github_label?: string
  education?: ResumeEducationInput[]
}

export type PortfolioSiteRequest = {
  name: string
  title?: string
  bio?: string
  email?: string
  location?: string
  github_url?: string
  linkedin_url?: string
  years_experience?: string
  projects_completed?: string
  open_source_contributions?: string
  project_ids: number[]
}

export type PortfolioSiteResponse = {
  status: string
  url: string
  server_started: boolean
  message: string
}

// ─── API Functions ─────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || res.statusText)
  }
  return res.json()
}

// Filter
export function filterProjects(filter: ProjectFilter): Promise<FilterResponse> {
  return apiFetch('/filter/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filter),
  })
}

export function getFilterOptions(): Promise<FilterOptions> {
  return apiFetch('/filter/options')
}

// Projects
export function getProjects(): Promise<ProjectListItem[]> {
  return apiFetch('/projects')
}

export async function getProjectDetail(projectId: number): Promise<ProjectDetail> {
  const raw: Record<string, unknown> = await apiFetch(`/projects/${projectId}`)
  const metrics = (raw.project_metrics ?? {}) as Record<string, unknown>
  const portfolio = (raw.portfolio_item ?? {}) as Record<string, unknown>
  const git = (raw.git_analysis ?? {}) as Record<string, unknown>
  return {
    project_info_id: (raw.project_id ?? projectId) as number,
    project_name: (raw.project_name ?? '') as string,
    zip_hash: (raw.zip_hash ?? '') as string,
    project_created_at: (git.first_commit_at ?? metrics.duration_start ?? '') as string,
    total_files: (metrics.total_files ?? 0) as number,
    total_lines: (metrics.total_lines ?? 0) as number,
    total_commits: (git.total_commits ?? metrics.total_commits ?? 0) as number,
    total_contributors: (git.total_contributors ?? metrics.total_contributors ?? 0) as number,
    tagline: (portfolio.tagline ?? undefined) as string | undefined,
    description: (portfolio.description ?? undefined) as string | undefined,
    project_type: (portfolio.project_type ?? undefined) as string | undefined,
    complexity: (portfolio.complexity ?? undefined) as string | undefined,
    is_collaborative: (portfolio.is_collaborative ?? undefined) as boolean | undefined,
    summary: (portfolio.summary ?? undefined) as string | undefined,
    user_role: (raw.user_role ?? undefined) as string | undefined,
  }
}

export function uploadProject(req: UploadRequest): Promise<UploadResponse> {
  return apiFetch('/projects/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// Portfolio
export function getPortfolioTemplates(): Promise<PortfolioTemplate[]> {
  return apiFetch('/portfolio/templates')
}

export async function getPortfolio(projectId: number): Promise<PortfolioData> {
  const raw: Record<string, unknown> = await apiFetch(`/portfolio/${projectId}`)
  const keyMetrics = (raw.key_metrics ?? {}) as Record<string, number>
  return {
    project_name: (raw.project_title ?? '') as string,
    tagline: raw.tagline as string | undefined,
    description: raw.description as string | undefined,
    summary: raw.summary as string | undefined,
    key_features: (raw.key_features ?? raw.deliverables ?? raw.artifacts ?? []) as string[],
    project_type: raw.project_type as string | undefined,
    complexity: raw.complexity as string | undefined,
    is_collaborative: raw.is_collaborative as boolean | undefined,
    skills: (raw.key_skills ?? []) as string[],
    metrics: {
      total_files: keyMetrics.total_files ?? 0,
      total_lines: keyMetrics.total_lines ?? 0,
      total_commits: keyMetrics.total_commits ?? 0,
      total_contributors: keyMetrics.total_contributors ?? 0,
    },
    evolution: raw.evolution as PortfolioData['evolution'],
  }
}

export function generatePortfolioSite(payload: PortfolioSiteRequest): Promise<PortfolioSiteResponse> {
  return apiFetch('/portfolio/generate-site', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// Resume
export async function getResume(projectId: number): Promise<ResumeData> {
  const raw: Record<string, unknown> = await apiFetch(`/resume/${projectId}`)
  const resumeItem = (raw.resume_item ?? {}) as Record<string, unknown>
  return {
    project_name: (resumeItem.project_name ?? '') as string,
    bullets: (resumeItem.bullets ?? []) as string[],
    user_role: (raw.user_role ?? resumeItem.user_role) as string | undefined,
  }
}

export function generateResume(): Promise<{ message: string }> {
  return apiFetch('/resume/generate', { method: 'POST' })
}

export async function generateResumePdf(
  payload: ResumePdfRequest,
): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${API_BASE}/resume/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || res.statusText)
  }
  const blob = await res.blob()
  const disposition = res.headers.get('content-disposition') || ''
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
  return {
    blob,
    filename: filenameMatch?.[1] || 'resume.pdf',
  }
}

// Skills
export async function getProjectSkills(projectId: number): Promise<ProjectSkill[]> {
  const raw: Record<string, unknown> = await apiFetch(`/skills/${projectId}`)
  const skills = (raw.skills ?? []) as string[]
  return skills.map((s) => ({ skill_name: s }))
}

export function listSkillsCatalog(): Promise<string[]> {
  return apiFetch('/skills')
}

export function getSkillsByYear(year: number): Promise<{ year: number; timeline: ChronologicalSkillEvent[] }> {
  return apiFetch(`/skills/year?year=${encodeURIComponent(String(year))}`)
}

export function addProjectSkills(req: SkillsAddRequest): Promise<SkillCatalogResponse> {
  return apiFetch('/skills/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function removeProjectSkills(req: SkillsRemoveRequest): Promise<SkillCatalogResponse> {
  return apiFetch('/skills/remove', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function editProjectSkills(req: SkillsEditRequest): Promise<SkillCatalogResponse> {
  return apiFetch('/skills/edit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getChronologicalSkills(params: {
  zipHash?: string
  projectName?: string
} = {}): Promise<ChronologicalSkillsResponse> {
  const query = new URLSearchParams()
  if (params.zipHash) query.set('zip_hash', params.zipHash)
  if (params.projectName) query.set('project_name', params.projectName)
  const suffix = query.toString()
  return apiFetch(`/chronological/skills${suffix ? `?${suffix}` : ''}`)
}

export function getChronologicalSkillsByProjectId(projectId: number): Promise<ChronologicalSkillsResponse> {
  return apiFetch(`/chronological/skills/${projectId}`)
}

export function getChronologicalProjects(limit = 50): Promise<ChronologicalProjectsResponse> {
  return apiFetch(`/chronological/projects?limit=${encodeURIComponent(String(limit))}`)
}

export async function getProjectTimelineLookup(): Promise<ProjectTimelineLookup[]> {
  const raw = await apiFetch<Record<string, unknown>[]>('/projects')
  return raw
    .map((item) => ({
      project_id: Number(item.project_id ?? 0),
      project_name: String(item.project_name ?? ''),
      zip_hash: String(item.zip_hash ?? ''),
    }))
    .filter((item) => item.project_id > 0 && item.project_name.length > 0 && item.zip_hash.length > 0)
}

// ─── Profile Types ─────────────────────────────────────────────────

export type UserProfile = {
  user_id: string
  first_name: string | null
  last_name: string | null
  email: string | null
  github_username: string | null
  git_identifier: string | null
}

export type ProfileUpdateRequest = {
  first_name?: string
  last_name?: string
  email?: string
  github_username?: string
  git_identifier?: string
}

// Consent & Privacy
export function setPrivacyConsent(req: ConsentRequest): Promise<{ message: string }> {
  return apiFetch('/privacy-consent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function setGitIdentifier(req: GitIdentifierRequest): Promise<{ message: string }> {
  return apiFetch('/git-identifier', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export function getProfile(userId: string): Promise<UserProfile> {
  return apiFetch(`/profile/${encodeURIComponent(userId)}`)
}

export function updateProfile(userId: string, data: ProfileUpdateRequest): Promise<UserProfile> {
  return apiFetch(`/profile/${encodeURIComponent(userId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}
