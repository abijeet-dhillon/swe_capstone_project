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
import { LinkedInPostModal } from './LinkedInPostModal'

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
  const [showLinkedIn, setShowLinkedIn] = useState(false)

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

          {showLinkedIn && detail && (
            <LinkedInPostModal
              projectId={projectId}
              projectName={detail.project_name}
              onClose={() => setShowLinkedIn(false)}
            />
          )}
        </div>
      )}
    </aside>
  )
}
