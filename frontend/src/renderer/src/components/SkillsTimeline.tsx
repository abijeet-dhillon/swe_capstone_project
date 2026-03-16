import React, { useState } from 'react'
import { useSkillsTimeline } from '../hooks/useSkillsTimeline'

interface SkillMilestone {
  date: string
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  description: string
}

interface Skill {
  id: number
  name: string
  category: 'language' | 'framework' | 'backend' | 'tool'
  startDate: string
  proficiency: number
  yearsExperience: number
  description: string
  milestones: SkillMilestone[]
  projects: string[]
  depthLevel: number
}

const SkillsTimeline: React.FC = () => {
  const { skills, loading, error } = useSkillsTimeline()
  const [filter, setFilter] = useState<string>('all')
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const filteredSkills = filter === 'all' ? skills : skills.filter(skill => skill.category === filter)
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
  const getProficiencyColor = (proficiency: number) => proficiency >= 80 ? '#10b981' : proficiency >= 60 ? '#3b82f6' : '#f59e0b'
  const getLevelColor = (level: string) => ({ beginner: '#f59e0b', intermediate: '#3b82f6', advanced: '#8b5cf6', expert: '#10b981' }[level] || '#6b7280')

  if (loading) {
    return (
      <div className="timeline-container">
        <div className="timeline-loading">
          <div className="loading-spinner"></div>
          <p>Loading skills data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="timeline-container">
        <div className="timeline-error">
          <p>Error loading skills: {error}</p>
          <button onClick={() => window.location.reload()} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (skills.length === 0) {
    return (
      <div className="timeline-container">
        <div className="timeline-empty">
          <p>No skills data available. Upload a project to see your skills timeline.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="timeline-container">
      <div className="timeline-controls">
        {['all', 'language', 'framework', 'backend', 'tool'].map(cat => (
          <button key={cat} className={`filter-btn ${filter === cat ? 'active' : ''}`} onClick={() => setFilter(cat)}>
            {cat === 'all' ? 'All Skills' : cat.charAt(0).toUpperCase() + cat.slice(1) + 's'}
          </button>
        ))}
      </div>
      <div className="timeline">
        {filteredSkills.sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime()).map((skill, index) => (
          <div key={skill.id} className="timeline-item" style={{animationDelay: `${index * 0.1}s`}}>
            <div className="timeline-dot"></div>
            <div className="timeline-content" onClick={() => setSelectedSkill(skill)}>
              <div className="timeline-header">
                <div className="timeline-date">{formatDate(skill.startDate)}</div>
                <div className="depth-indicator">
                  {Array.from({ length: skill.depthLevel }).map((_, i) => (
                    <span key={i} className="depth-bar" style={{ backgroundColor: getProficiencyColor(skill.proficiency) }}></span>
                  ))}
                </div>
              </div>
              <h3 className="timeline-title">{skill.name}</h3>
              <span className="timeline-category">{skill.category}</span>
              <div className="timeline-proficiency">
                <div className="proficiency-header">
                  <span>Proficiency</span>
                  <span className="proficiency-value">{skill.proficiency}%</span>
                </div>
                <div className="proficiency-bar">
                  <div className="proficiency-fill" style={{width: `${skill.proficiency}%`, backgroundColor: getProficiencyColor(skill.proficiency)}}></div>
                </div>
              </div>
              <p className="timeline-description">{skill.description}</p>
              <div className="timeline-meta">
                <span className="years-badge">{skill.yearsExperience} years</span>
                <span className="projects-count">{skill.projects.length} projects</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      {selectedSkill && (
        <div className="skill-modal" onClick={() => setSelectedSkill(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <span className="close" onClick={() => setSelectedSkill(null)}>&times;</span>
            <div className="modal-header">
              <h2>{selectedSkill.name}</h2>
              <span className="modal-category">{selectedSkill.category}</span>
            </div>
            <div className="modal-stats">
              <div className="stat">
                <span className="stat-value">{selectedSkill.proficiency}%</span>
                <span className="stat-label">Proficiency</span>
              </div>
              <div className="stat">
                <span className="stat-value">{selectedSkill.yearsExperience}y</span>
                <span className="stat-label">Experience</span>
              </div>
              <div className="stat">
                <span className="stat-value">{selectedSkill.depthLevel}</span>
                <span className="stat-label">Depth Level</span>
              </div>
            </div>
            <p className="modal-description">{selectedSkill.description}</p>
            <div className="proficiency-bar modal-bar">
              <div className="proficiency-fill" style={{width: `${selectedSkill.proficiency}%`, backgroundColor: getProficiencyColor(selectedSkill.proficiency)}}></div>
            </div>
            <div className="modal-section">
              <h4>Learning Progression</h4>
              <div className="milestones">
                {selectedSkill.milestones.map((milestone, idx) => (
                  <div key={idx} className="milestone">
                    <div className="milestone-dot" style={{ backgroundColor: getLevelColor(milestone.level) }}></div>
                    <div className="milestone-content">
                      <div className="milestone-header">
                        <span className="milestone-level">{milestone.level}</span>
                        <span className="milestone-date">{formatDate(milestone.date)}</span>
                      </div>
                      <p className="milestone-desc">{milestone.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="modal-section">
              <h4>Projects Built</h4>
              <div className="projects-list">
                {selectedSkill.projects.map((project, idx) => (
                  <span key={idx} className="project-tag">{project}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SkillsTimeline
