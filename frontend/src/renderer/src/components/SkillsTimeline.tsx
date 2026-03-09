import React, { useState } from 'react'

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
  const [skills] = useState<Skill[]>([
    {
      id: 1, name: "HTML/CSS", category: "language", startDate: "2019-12", proficiency: 90, yearsExperience: 4.2,
      description: "Mastered semantic markup, responsive design, CSS Grid, Flexbox, and modern animations.",
      milestones: [
        { date: "2019-12", level: "beginner", description: "Learned basic HTML tags and CSS selectors" },
        { date: "2020-03", level: "intermediate", description: "Built first responsive layouts with Flexbox" },
        { date: "2020-08", level: "advanced", description: "Mastered CSS Grid and complex animations" },
        { date: "2021-06", level: "expert", description: "Created design systems and component libraries" }
      ],
      projects: ["Portfolio Website", "E-commerce UI", "Dashboard Design System"],
      depthLevel: 4
    },
    {
      id: 2, name: "JavaScript", category: "language", startDate: "2020-05", proficiency: 85, yearsExperience: 3.7,
      description: "Deep understanding of closures, prototypes, async patterns, and functional programming.",
      milestones: [
        { date: "2020-05", level: "beginner", description: "Variables, functions, and basic DOM manipulation" },
        { date: "2020-09", level: "intermediate", description: "ES6+ features and array methods mastery" },
        { date: "2021-02", level: "advanced", description: "Async/await, Promises, and event loop deep dive" },
        { date: "2021-11", level: "expert", description: "Performance optimization and design patterns" }
      ],
      projects: ["Interactive Web Apps", "API Integrations", "Algorithm Solutions"],
      depthLevel: 4
    },
    {
      id: 3, name: "React", category: "framework", startDate: "2020-12", proficiency: 80, yearsExperience: 1.0,
      description: "Expert in hooks, context, performance optimization, and custom component patterns.",
      milestones: [
        { date: "2020-12", level: "beginner", description: "Components, props, and basic state" },
        { date: "2021-04", level: "intermediate", description: "Hooks and functional components mastery" },
        { date: "2021-10", level: "advanced", description: "Context API, custom hooks, and patterns" },
        { date: "2021-12", level: "expert", description: "Performance tuning and advanced patterns" }
      ],
      projects: ["Task Manager App", "Social Media Dashboard", "Real-time Chat App"],
      depthLevel: 4
    },
    {
      id: 4, name: "Node.js", category: "backend", startDate: "2021-05", proficiency: 75, yearsExperience: 0.6,
      description: "Built scalable APIs, authentication systems, and database integrations.",
      milestones: [
        { date: "2021-05", level: "beginner", description: "Basic Express server and routing" },
        { date: "2021-09", level: "intermediate", description: "RESTful APIs and middleware patterns" },
        { date: "2021-10", level: "advanced", description: "Authentication, JWT, and database design" },
        { date: "2021-12", level: "expert", description: "Scalability, performance optimization, and deployment" }
      ],
      projects: ["REST API Server", "Authentication System", "File Upload Service"],
      depthLevel: 3
    },
    {
      id: 5, name: "TypeScript", category: "language", startDate: "2021-12", proficiency: 70, yearsExperience: 0.1,
      description: "Type-safe development with generics, utility types, and advanced type patterns.",
      milestones: [
        { date: "2021-12", level: "beginner", description: "Basic types and interfaces" },
        { date: "2021-12", level: "intermediate", description: "Generics and type narrowing" },
        { date: "2021-12", level: "advanced", description: "Conditional types and mapped types" },
        { date: "2021-12", level: "expert", description: "Type-safe architecture patterns" }
      ],
      projects: ["Type-safe React Apps", "API Client Libraries", "Code Generation Tools"],
      depthLevel: 3
    }
  ])
  const [filter, setFilter] = useState<string>('all')
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null)

  const filteredSkills = filter === 'all' ? skills : skills.filter(skill => skill.category === filter)
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
  const getProficiencyColor = (proficiency: number) => proficiency >= 80 ? '#10b981' : proficiency >= 60 ? '#3b82f6' : '#f59e0b'
  const getLevelColor = (level: string) => ({ beginner: '#f59e0b', intermediate: '#3b82f6', advanced: '#8b5cf6', expert: '#10b981' }[level] || '#6b7280')

  return (
    <div className="timeline-container">
      <div className="timeline-controls">
        {['all', 'language', 'framework', 'backend'].map(cat => (
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
