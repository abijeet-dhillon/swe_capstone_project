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

// ─── Consent Types ─────────────────────────────────────────────────

export type ConsentRequest = {
  user_id: string
  zip_path: string
  llm_consent: boolean
  data_access_consent: boolean
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

// Skills
export async function getProjectSkills(projectId: number): Promise<ProjectSkill[]> {
  const raw: Record<string, unknown> = await apiFetch(`/skills/${projectId}`)
  const skills = (raw.skills ?? []) as string[]
  return skills.map((s) => ({ skill_name: s }))
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
