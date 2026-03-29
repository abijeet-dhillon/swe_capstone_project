import { useEffect, useState } from 'react'
import {
  getProjectDetail,
  getPortfolio,
  getResume,
  getProjectSkills,
  getAIAnalysis,
  type ProjectDetail,
  type PortfolioData,
  type ResumeData,
  type ProjectSkill,
  type AIAnalysisData,
} from '../api'
import { LinkedInPostModal } from './LinkedInPostModal'

type DetailTab = 'overview' | 'ai-analysis'

export function DetailPanel({
  projectId,
  onClose,
}: {
  projectId: number
  onClose: () => void
}) {
  const [detail, setDetail] = useState<ProjectDetail | null>(null)
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [resume, setResume] = useState<ResumeData | null>(null)
  const [skills, setSkills] = useState<ProjectSkill[]>([])
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [aiLoading, setAiLoading] = useState(false)
  const [showLinkedIn, setShowLinkedIn] = useState(false)
  const [activeTab, setActiveTab] = useState<DetailTab>('overview')

  useEffect(() => {
    setLoading(true)
    setActiveTab('overview')
    setAiAnalysis(null)
    Promise.allSettled([
      getProjectDetail(projectId),
      getPortfolio(projectId),
      getResume(projectId),
      getProjectSkills(projectId),
    ]).then(([detailRes, portfolioRes, resumeRes, skillsRes]) => {
      if (detailRes.status === 'fulfilled') setDetail(detailRes.value)
      if (portfolioRes.status === 'fulfilled') setPortfolio(portfolioRes.value)
      if (resumeRes.status === 'fulfilled') setResume(resumeRes.value)
      if (skillsRes.status === 'fulfilled') setSkills(skillsRes.value)
      setLoading(false)
    })
  }, [projectId])

  useEffect(() => {
    if (activeTab === 'ai-analysis' && !aiAnalysis && !aiLoading) {
      setAiLoading(true)
      getAIAnalysis(projectId)
        .then(setAiAnalysis)
        .catch(() => setAiAnalysis(null))
        .finally(() => setAiLoading(false))
    }
  }, [activeTab, projectId, aiAnalysis, aiLoading])

  return (
    <aside className="detail-panel">
      <div className="detail-panel__header">
        <h3>Project Details</h3>
        <button className="detail-panel__close" onClick={onClose}>
          ×
        </button>
      </div>

      {loading ? (
        <div className="detail-panel__loading">Loading...</div>
      ) : (
        <>
          {detail && (
            <div className="detail-panel__top">
              <h2 className="detail-panel__title">{detail.project_name}</h2>
              <div className="detail-panel__badges">
                {detail.project_type && (
                  <span className="pill info">{detail.project_type}</span>
                )}
                {detail.complexity && (
                  <span className="pill coming-soon">{detail.complexity}</span>
                )}
                {detail.is_collaborative && (
                  <span className="pill highlight">Collaborative</span>
                )}
              </div>
            </div>
          )}

          <div className="detail-panel__tabs">
            <button
              className={`detail-panel__tab ${activeTab === 'overview' ? 'detail-panel__tab--active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={`detail-panel__tab ${activeTab === 'ai-analysis' ? 'detail-panel__tab--active' : ''}`}
              onClick={() => setActiveTab('ai-analysis')}
            >
              AI Analysis
            </button>
          </div>

          <div className="detail-panel__body">
            {activeTab === 'overview' && (
              <>
                {detail && (
                  <>
                    {detail.user_role && (
                      <p className="detail-panel__role">Role: {detail.user_role}</p>
                    )}

                    <div className="detail-panel__meta-grid">
                      <div className="meta-item">
                        <span className="meta-item__label">Files</span>
                        <span className="meta-item__value">{detail.total_files}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-item__label">Lines</span>
                        <span className="meta-item__value">
                          {(detail.total_lines ?? 0).toLocaleString()}
                        </span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-item__label">Commits</span>
                        <span className="meta-item__value">{detail.total_commits}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-item__label">Contributors</span>
                        <span className="meta-item__value">{detail.total_contributors}</span>
                      </div>
                    </div>
                  </>
                )}

                {portfolio?.description && (
                  <div className="detail-panel__section">
                    <h4>Description</h4>
                    <p>{portfolio.description}</p>
                  </div>
                )}

                {portfolio?.summary && (
                  <div className="detail-panel__section">
                    <h4>Summary</h4>
                    <p>{portfolio.summary}</p>
                  </div>
                )}

                {portfolio?.key_features && portfolio.key_features.length > 0 && (
                  <div className="detail-panel__section">
                    <h4>Key Features</h4>
                    <ul className="detail-panel__features">
                      {portfolio.key_features.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {resume && resume.bullets.length > 0 && (
                  <div className="detail-panel__section">
                    <h4>Resume Bullets</h4>
                    <ul className="detail-panel__bullets">
                      {resume.bullets.map((b, i) => (
                        <li key={i}>{b}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {skills.length > 0 && (
                  <div className="detail-panel__section">
                    <h4>Skills</h4>
                    <div className="detail-panel__skills">
                      {skills.map((s, i) => (
                        <span key={i} className="skill-pill">
                          {s.skill_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="detail-panel__section">
                  <button
                    className="detail-panel__linkedin-btn"
                    onClick={() => setShowLinkedIn(true)}
                  >
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                    </svg>
                    Generate LinkedIn Post
                  </button>
                </div>
              </>
            )}

            {activeTab === 'ai-analysis' && (
              <>
                {aiLoading ? (
                  <div className="detail-panel__loading">Loading AI Analysis...</div>
                ) : aiAnalysis ? (
                  <>
                    {aiAnalysis.top_summary && (
                      <div className="detail-panel__section">
                        <h4>Project Score</h4>
                        <div className="ai-analysis__score-card">
                          <div className="ai-analysis__score">
                            {aiAnalysis.top_summary.score.toFixed(1)}
                          </div>
                          <div className="ai-analysis__score-details">
                            <span className="ai-analysis__rank">
                              Rank #{aiAnalysis.top_summary.rank}
                            </span>
                            <span className="ai-analysis__criteria">
                              by {aiAnalysis.top_summary.criteria}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {aiAnalysis.portfolio_summary && (
                      <div className="detail-panel__section">
                        <h4>AI Summary</h4>
                        <p>{aiAnalysis.portfolio_summary}</p>
                      </div>
                    )}

                    {aiAnalysis.top_summary?.summary && (
                      <div className="detail-panel__section">
                        <h4>Analysis Overview</h4>
                        <p className="ai-analysis__overview">{aiAnalysis.top_summary.summary}</p>
                      </div>
                    )}

                    {aiAnalysis.portfolio_description && (
                      <div className="detail-panel__section">
                        <h4>Generated Description</h4>
                        <p>{aiAnalysis.portfolio_description}</p>
                      </div>
                    )}

                    {aiAnalysis.key_features.length > 0 && (
                      <div className="detail-panel__section">
                        <h4>Identified Features</h4>
                        <ul className="detail-panel__features">
                          {aiAnalysis.key_features.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {aiAnalysis.resume_bullets.length > 0 && (
                      <div className="detail-panel__section">
                        <h4>Generated Resume Bullets</h4>
                        <ul className="detail-panel__bullets">
                          {aiAnalysis.resume_bullets.map((b, i) => (
                            <li key={i}>{b}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {aiAnalysis.languages.length > 0 && (
                      <div className="detail-panel__section">
                        <h4>Languages</h4>
                        <div className="detail-panel__skills">
                          {aiAnalysis.languages.map((l, i) => (
                            <span key={i} className="skill-pill skill-pill--lang">
                              {l}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {aiAnalysis.frameworks.length > 0 && (
                      <div className="detail-panel__section">
                        <h4>Frameworks</h4>
                        <div className="detail-panel__skills">
                          {aiAnalysis.frameworks.map((f, i) => (
                            <span key={i} className="skill-pill skill-pill--framework">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {aiAnalysis.skills.length > 0 && (
                      <div className="detail-panel__section">
                        <h4>Detected Skills</h4>
                        <div className="detail-panel__skills">
                          {aiAnalysis.skills.map((s, i) => (
                            <span key={i} className="skill-pill">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="detail-panel__section">
                      <h4>Project Attributes</h4>
                      <div className="ai-analysis__attributes">
                        <span className={`pill ${aiAnalysis.has_documentation ? 'highlight' : 'muted'}`}>
                          {aiAnalysis.has_documentation ? 'Documented' : 'No Docs'}
                        </span>
                        <span className={`pill ${aiAnalysis.has_tests ? 'highlight' : 'muted'}`}>
                          {aiAnalysis.has_tests ? 'Has Tests' : 'No Tests'}
                        </span>
                      </div>
                    </div>

                    {aiAnalysis.top_summary?.metrics && (
                      <div className="detail-panel__section">
                        <h4>Metrics</h4>
                        <div className="detail-panel__meta-grid">
                          <div className="meta-item">
                            <span className="meta-item__label">Lines of Code</span>
                            <span className="meta-item__value">
                              {aiAnalysis.top_summary.metrics.loc.toLocaleString()}
                            </span>
                          </div>
                          <div className="meta-item">
                            <span className="meta-item__label">Commits</span>
                            <span className="meta-item__value">
                              {aiAnalysis.top_summary.metrics.commits}
                            </span>
                          </div>
                          <div className="meta-item">
                            <span className="meta-item__label">Duration</span>
                            <span className="meta-item__value">
                              {aiAnalysis.top_summary.metrics.duration_days} days
                            </span>
                          </div>
                          <div className="meta-item">
                            <span className="meta-item__label">Recency</span>
                            <span className="meta-item__value">
                              {aiAnalysis.top_summary.metrics.recency_days} days ago
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="ai-analysis__empty">
                    <div className="ai-analysis__empty-icon">
                      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M12 2a7 7 0 0 1 7 7c0 2.38-1.19 4.47-3 5.74V17a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-2.26C6.19 13.47 5 11.38 5 9a7 7 0 0 1 7-7z" />
                        <path d="M10 21h4" />
                        <path d="M12 6v4" />
                        <path d="M10 10h4" />
                      </svg>
                    </div>
                    <p>No AI analysis available for this project.</p>
                    <p className="ai-analysis__empty-hint">
                      Enable AI-Enhanced Analysis when uploading a project to get detailed insights.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {showLinkedIn && detail && (
            <LinkedInPostModal
              projectId={projectId}
              projectName={detail.project_name}
              onClose={() => setShowLinkedIn(false)}
            />
          )}
        </>
      )}
    </aside>
  )
}
