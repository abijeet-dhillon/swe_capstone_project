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

export type ProjectEditRequest = {
  project_name?: string
  tagline?: string
  description?: string
  project_type?: string
  complexity?: string
  summary?: string
}

export type ProjectMutationResponse = {
  status: string
  project_id: number
  project?: Record<string, unknown>
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

// ─── AI Analysis Types ────────────────────────────────────────────

export type TopSummary = {
  rank: number
  name: string
  score: number
  criteria: string
  summary: string
  user_contrib_score: number | null
  metrics: {
    commits: number
    loc: number
    recency_days: number
    languages: string[]
    duration_days: number
  }
}

export type AIAnalysisData = {
  portfolio_summary: string | null
  portfolio_description: string | null
  portfolio_tagline: string | null
  key_features: string[]
  resume_bullets: string[]
  top_summary: TopSummary | null
  languages: string[]
  frameworks: string[]
  skills: string[]
  has_documentation: boolean
  has_tests: boolean
  total_files: number
  total_lines: number
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
  user_id?: string
  resume_owner_name?: string
  project_ids: number[]
  phone?: string
  email?: string
  linkedin_url?: string
  linkedin_label?: string
  github_url?: string
  github_label?: string
  education?: ResumeEducationInput[]
  awards?: string[]
}

export type PortfolioSiteRequest = {
  user_id?: string
  name?: string
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
  hidden_sections?: string[]
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
    let parsed: unknown = null
    try {
      parsed = text ? JSON.parse(text) : null
    } catch {
      parsed = null
    }
    const detail = typeof parsed === 'object' && parsed !== null && 'detail' in parsed
      ? (parsed as { detail: unknown }).detail
      : null
    if (typeof detail === 'string' && detail.trim()) {
      throw new Error(detail)
    }
    if (typeof detail === 'object' && detail !== null) {
      const detailMessage = 'message' in detail && typeof (detail as { message?: unknown }).message === 'string'
        ? (detail as { message: string }).message
        : ''
      if (detailMessage) {
        const missing = 'missing_fields' in detail && Array.isArray((detail as { missing_fields?: unknown }).missing_fields)
          ? (detail as { missing_fields: unknown[] }).missing_fields
            .map((item) => String(item))
            .filter(Boolean)
          : []
        const suffix = missing.length > 0 ? ` Missing: ${missing.join(', ')}` : ''
        throw new Error(`${detailMessage}${suffix}`)
      }
    }
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

export function updateProject(projectId: number, payload: ProjectEditRequest): Promise<ProjectMutationResponse> {
  return apiFetch(`/projects/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function removeProject(projectId: number): Promise<ProjectMutationResponse> {
  return apiFetch(`/projects/${projectId}`, {
    method: 'DELETE',
  })
}

export function uploadProject(req: UploadRequest): Promise<UploadResponse> {
  return apiFetch('/projects/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// AI Analysis
export async function getAIAnalysis(projectId: number): Promise<AIAnalysisData> {
  const raw: Record<string, unknown> = await apiFetch(`/projects/${projectId}`)
  const portfolio = (raw.portfolio_item ?? {}) as Record<string, unknown>
  const resume = (raw.resume_item ?? {}) as Record<string, unknown>
  const globalInsights = (raw.global_insights ?? {}) as Record<string, unknown>
  const ranking = (globalInsights.project_ranking ?? {}) as Record<string, unknown>
  const topSummaries = (ranking.top_summaries ?? []) as Record<string, unknown>[]
  const projectName = (raw.project_name ?? '') as string

  const matchingSummary = topSummaries.find((s) => s.name === projectName) ?? topSummaries[0] ?? null

  return {
    portfolio_summary: (portfolio.summary ?? null) as string | null,
    portfolio_description: (portfolio.description ?? null) as string | null,
    portfolio_tagline: (portfolio.tagline ?? null) as string | null,
    key_features: (portfolio.key_features ?? []) as string[],
    resume_bullets: (resume.bullets ?? []) as string[],
    top_summary: matchingSummary
      ? {
          rank: (matchingSummary.rank ?? 0) as number,
          name: (matchingSummary.name ?? '') as string,
          score: (matchingSummary.score ?? 0) as number,
          criteria: (matchingSummary.criteria ?? '') as string,
          summary: (matchingSummary.summary ?? '') as string,
          user_contrib_score: (matchingSummary.user_contrib_score ?? null) as number | null,
          metrics: (matchingSummary.metrics ?? {}) as TopSummary['metrics'],
        }
      : null,
    languages: (portfolio.languages ?? []) as string[],
    frameworks: (portfolio.frameworks ?? []) as string[],
    skills: (portfolio.skills ?? []) as string[],
    has_documentation: (portfolio.has_documentation ?? false) as boolean,
    has_tests: (portfolio.has_tests ?? false) as boolean,
    total_files: (portfolio.total_lines !== undefined ? 0 : 0) as number,
    total_lines: (portfolio.total_lines ?? 0) as number,
  }
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
    let parsed: unknown = null
    try {
      parsed = text ? JSON.parse(text) : null
    } catch {
      parsed = null
    }
    const detail = typeof parsed === 'object' && parsed !== null && 'detail' in parsed
      ? (parsed as { detail: unknown }).detail
      : null
    if (typeof detail === 'string' && detail.trim()) {
      throw new Error(detail)
    }
    if (typeof detail === 'object' && detail !== null) {
      const detailMessage = 'message' in detail && typeof (detail as { message?: unknown }).message === 'string'
        ? (detail as { message: string }).message
        : ''
      if (detailMessage) {
        const missing = 'missing_fields' in detail && Array.isArray((detail as { missing_fields?: unknown }).missing_fields)
          ? (detail as { missing_fields: unknown[] }).missing_fields
            .map((item) => String(item))
            .filter(Boolean)
          : []
        const suffix = missing.length > 0 ? ` Missing: ${missing.join(', ')}` : ''
        throw new Error(`${detailMessage}${suffix}`)
      }
    }
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
  name: string | null
  contact: {
    phone_number: string | null
    email: string | null
    linkedin_url: string | null
    github_url: string | null
    linkedin_label: string | null
    github_label: string | null
  }
  education: Array<{
    school: string
    location: string
    degree: string
    from: string
    to: string
    still_studying: boolean
  }>
  awards: string[]
  portfolio: {
    title: string | null
    about_me: string | null
    years_of_experience: string | null
    open_source_contribution: string | null
  }
  git_identifier: string | null
  // Backward-compatible fields still returned by backend
  first_name?: string | null
  last_name?: string | null
  email?: string | null
  github_username?: string | null
}

export type ProfileUpdateRequest = {
  name?: string
  contact?: {
    phone_number?: string
    email?: string
    linkedin_url?: string
    github_url?: string
    linkedin_label?: string
    github_label?: string
  }
  education?: Array<{
    school?: string
    location?: string
    degree?: string
    from?: string
    to?: string
    still_studying?: boolean
  }>
  awards?: string[]
  portfolio?: {
    title?: string
    about_me?: string
    years_of_experience?: string
    open_source_contribution?: string
  }
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

// ─── LinkedIn Types ─────────────────────────────────────────────────

export type LinkedInPreview = {
  project_id: number
  project_name: string
  text: string
  char_count: number
  exceeds_limit: boolean
  hashtags: string[]
  preview: string
}

// ─── Thumbnail Types ────────────────────────────────────────────────

export type ThumbnailUploadResponse = {
  status: string
  project_id: number
  thumbnail_url: string
  mime_type: string
  size_bytes: number
}

// LinkedIn
export function getLinkedInPreview(
  projectId: number,
  opts: { includeHashtags?: boolean; includeEmojis?: boolean } = {},
): Promise<LinkedInPreview> {
  const params = new URLSearchParams()
  if (opts.includeHashtags !== undefined) params.set('include_hashtags', String(opts.includeHashtags))
  if (opts.includeEmojis !== undefined) params.set('include_emojis', String(opts.includeEmojis))
  const qs = params.toString()
  return apiFetch(`/linkedin/preview/${projectId}${qs ? `?${qs}` : ''}`)
}

// Thumbnails
export async function hasProjectThumbnail(projectId: number): Promise<boolean> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/thumbnail`)
  return res.ok
}

export async function uploadProjectThumbnail(
  projectId: number,
  file: File,
): Promise<ThumbnailUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/projects/${projectId}/thumbnail`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || `Upload failed (${res.status})`)
  }
  return res.json() as Promise<ThumbnailUploadResponse>
}
