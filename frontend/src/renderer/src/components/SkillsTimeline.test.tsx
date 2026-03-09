import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SkillsTimeline from './SkillsTimeline'

describe('SkillsTimeline', () => {
  it('renders timeline with skills', () => {
    render(<SkillsTimeline />)
    expect(screen.getByText('All Skills')).toBeInTheDocument()
    expect(screen.getByText('Languages')).toBeInTheDocument()
    expect(screen.getByText('Frameworks')).toBeInTheDocument()
    expect(screen.getByText('Backends')).toBeInTheDocument()
  })

  it('displays skill items', () => {
    render(<SkillsTimeline />)
    expect(screen.getByText('HTML/CSS')).toBeInTheDocument()
    expect(screen.getByText('JavaScript')).toBeInTheDocument()
    expect(screen.getByText('React')).toBeInTheDocument()
  })

  it('filters skills by category', () => {
    render(<SkillsTimeline />)
    fireEvent.click(screen.getByText('Languages'))
    expect(screen.getByText('HTML/CSS')).toBeInTheDocument()
  })

  it('opens modal when skill is clicked', () => {
    render(<SkillsTimeline />)
    fireEvent.click(screen.getByText('HTML/CSS').closest('.timeline-content')!)
    expect(screen.getByText('Learning Progression')).toBeInTheDocument()
    expect(screen.getByText('Projects Built')).toBeInTheDocument()
  })

  it('closes modal when close button is clicked', () => {
    render(<SkillsTimeline />)
    fireEvent.click(screen.getByText('HTML/CSS').closest('.timeline-content')!)
    fireEvent.click(screen.getByText('×'))
    expect(screen.queryByText('Learning Progression')).not.toBeInTheDocument()
  })
})
