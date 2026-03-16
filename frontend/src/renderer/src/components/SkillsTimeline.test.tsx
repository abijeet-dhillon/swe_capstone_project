import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SkillsTimeline from './SkillsTimeline'

// Mock the hook
vi.mock('../hooks/useSkillsTimeline', () => ({
  useSkillsTimeline: vi.fn()
}))

import { useSkillsTimeline } from '../hooks/useSkillsTimeline'

const mockSkills = [
  {
    id: 1,
    name: 'JavaScript',
    category: 'language' as const,
    startDate: '2020-05',
    proficiency: 85,
    yearsExperience: 3.7,
    description: 'Deep understanding of closures, prototypes, async patterns, and functional programming.',
    milestones: [
      { date: '2020-05', level: 'beginner' as const, description: 'Variables, functions, and basic DOM manipulation' },
      { date: '2020-09', level: 'intermediate' as const, description: 'ES6+ features and array methods mastery' }
    ],
    projects: ['Interactive Web Apps', 'API Integrations'],
    depthLevel: 4
  },
  {
    id: 2,
    name: 'React',
    category: 'framework' as const,
    startDate: '2020-12',
    proficiency: 80,
    yearsExperience: 1.0,
    description: 'Expert in hooks, context, performance optimization, and custom component patterns.',
    milestones: [
      { date: '2020-12', level: 'beginner' as const, description: 'Components, props, and basic state' },
      { date: '2021-04', level: 'intermediate' as const, description: 'Hooks and functional components mastery' }
    ],
    projects: ['Task Manager App', 'Social Media Dashboard'],
    depthLevel: 4
  }
]

describe('SkillsTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders loading state', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: true,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('Loading skills data...')).toBeInTheDocument()
  })

  it('renders error state', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: false,
      error: 'Failed to fetch',
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('Error loading skills: Failed to fetch')).toBeInTheDocument()
    expect(screen.getByText('Retry')).toBeInTheDocument()
  })

  it('renders empty state when no skills', () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: [],
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    expect(screen.getByText('No skills data available. Upload a project to see your skills timeline.')).toBeInTheDocument()
  })

  it('renders timeline with skills', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      expect(screen.getByText('All Skills')).toBeInTheDocument()
      expect(screen.getByText('Languages')).toBeInTheDocument()
      expect(screen.getByText('Frameworks')).toBeInTheDocument()
      expect(screen.getByText('Backends')).toBeInTheDocument()
      expect(screen.getByText('Tools')).toBeInTheDocument()
    })
  })

  it('displays skill items', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      expect(screen.getByText('JavaScript')).toBeInTheDocument()
      expect(screen.getByText('React')).toBeInTheDocument()
    })
  })

  it('filters skills by category', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('Languages'))
      expect(screen.getByText('JavaScript')).toBeInTheDocument()
      expect(screen.queryByText('React')).not.toBeInTheDocument()
    })
  })

  it('opens modal when skill is clicked', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('JavaScript').closest('.timeline-content')!)
      expect(screen.getByText('Learning Progression')).toBeInTheDocument()
      expect(screen.getByText('Projects Built')).toBeInTheDocument()
    })
  })

  it('closes modal when close button is clicked', async () => {
    vi.mocked(useSkillsTimeline).mockReturnValue({
      skills: mockSkills,
      loading: false,
      error: null,
      refetch: vi.fn()
    })

    render(<SkillsTimeline />)
    
    await waitFor(() => {
      fireEvent.click(screen.getByText('JavaScript').closest('.timeline-content')!)
      fireEvent.click(screen.getByText('×'))
      expect(screen.queryByText('Learning Progression')).not.toBeInTheDocument()
    })
  })
})
