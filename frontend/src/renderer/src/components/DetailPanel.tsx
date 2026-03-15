import { useEffect, useState } from 'react'
import {
  getProjectDetail,
  getPortfolio,
  getResume,
  getProjectSkills,
  type ProjectDetail,
  type PortfolioData,
  type ResumeData,
  type ProjectSkill,
} from '../api'

// TODO: Processing Pipeline stepper (6 steps) — no pipeline status tracking in backend.
// TODO: Resume Score card — no scoring/grading endpoint found.

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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
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

  return (
    <aside className="detail-panel">
      <div className="detail-panel__header">
        <h3>Task Details</h3>
        <button className="detail-panel__close" onClick={onClose}>
          ×
        </button>
      </div>

      {loading ? (
        <div className="detail-panel__loading">Loading...</div>
      ) : (
        <div className="detail-panel__body">
          {detail && (
            <>
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

          {/* TODO: Processing Pipeline stepper — no backend pipeline status tracking */}

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

          {/* TODO: Resume Score card — no scoring endpoint found */}
          {/* TODO: Download button for generated PDF — needs resume artifact endpoint */}
        </div>
      )}
    </aside>
  )
}
