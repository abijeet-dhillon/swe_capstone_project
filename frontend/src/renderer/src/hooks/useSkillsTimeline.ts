import { useState, useEffect } from 'react'
import { getProjects, getProjectSkills, type ProjectListItem, type ProjectSkill } from '../api'

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

const categorizeSkill = (skillName: string): Skill['category'] => {
  const name = skillName.toLowerCase()
  if (name.includes('javascript') || name.includes('typescript') || name.includes('python') || name.includes('html') || name.includes('css')) return 'language'
  if (name.includes('react') || name.includes('vue') || name.includes('angular') || name.includes('django') || name.includes('flask')) return 'framework'
  if (name.includes('node') || name.includes('express') || name.includes('fastapi') || name.includes('django')) return 'backend'
  return 'tool'
}

const estimateProficiency = (skillName: string, projectDate: string): number => {
  const skillYears = new Date().getFullYear() - new Date(projectDate).getFullYear()
  return Math.min(95, Math.max(20, 20 + (skillYears * 15)))
}

const generateMilestones = (skillName: string, startDate: string): SkillMilestone[] => {
  const start = new Date(startDate)
  return [
    { date: startDate, level: 'beginner' as const, description: `Started learning ${skillName}` },
    { date: new Date(start.getTime() + 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 7), level: 'intermediate' as const, description: `Gained proficiency in ${skillName}` },
    { date: new Date(start.getTime() + 240 * 24 * 60 * 60 * 1000).toISOString().slice(0, 7), level: 'advanced' as const, description: `Mastered ${skillName}` }
  ]
}

export const useSkillsTimeline = () => {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSkillsData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const projects = await getProjects()
      const skillsMap = new Map<string, Skill>()
      
      for (const project of projects) {
        try {
          const projectSkills = await getProjectSkills(project.project_info_id)
          
          projectSkills.forEach((projectSkill) => {
            const skillName = projectSkill.skill_name
            
            if (!skillsMap.has(skillName)) {
              const skill: Skill = {
                id: skillsMap.size + 1,
                name: skillName,
                category: categorizeSkill(skillName),
                startDate: project.project_created_at.slice(0, 7),
                proficiency: estimateProficiency(skillName, project.project_created_at),
                yearsExperience: (new Date().getFullYear() - new Date(project.project_created_at).getFullYear()) / 12,
                description: `Experience with ${skillName}`,
                milestones: generateMilestones(skillName, project.project_created_at.slice(0, 7)),
                projects: [project.project_name],
                depthLevel: 3
              }
              skillsMap.set(skillName, skill)
            } else {
              const existingSkill = skillsMap.get(skillName)!
              if (!existingSkill.projects.includes(project.project_name)) {
                existingSkill.projects.push(project.project_name)
              }
            }
          })
        } catch (skillError) {
          console.warn(`Failed to fetch skills for project ${project.project_info_id}:`, skillError)
        }
      }
      
      setSkills(Array.from(skillsMap.values()).sort((a, b) => 
        new Date(a.startDate).getTime() - new Date(b.startDate).getTime()
      ))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch skills data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSkillsData()
  }, [])

  return { skills, loading, error, refetch: fetchSkillsData }
}
