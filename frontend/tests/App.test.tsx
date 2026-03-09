import { fireEvent, render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../src/renderer/src/App'

describe('App Dashboard', () => {
  it('renders title and footer', () => {
    render(<App />)
    expect(screen.getByText('Digital Work Artifact Miner')).toBeInTheDocument()
    expect(screen.getByText('COSC 499 — Digital Work Artifact Miner')).toBeInTheDocument()
  })

  it('defaults to private mode with customization enabled for ready cards', () => {
    render(<App />)
    expect(screen.getByText('Customization controls are enabled.')).toBeInTheDocument()

    const customizeButtons = screen.getAllByRole('button', { name: 'Customize' })
    const enabledButtons = customizeButtons.filter((button) => !button.hasAttribute('disabled'))
    expect(enabledButtons.length).toBeGreaterThan(0)
  })

  it('switches to public mode and disables all customize buttons', () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Public' }))

    expect(screen.getByText('Customization controls are disabled in public mode.')).toBeInTheDocument()

    const customizeButtons = screen.getAllByRole('button', { name: 'Customize' })
    customizeButtons.forEach((button) => expect(button).toBeDisabled())
  })

  it('filters dashboard cards by search query', () => {
    render(<App />)

    fireEvent.change(screen.getByLabelText('Search sections'), {
      target: { value: 'heatmap' },
    })

    expect(screen.getByText('Project Activity Heatmap')).toBeInTheDocument()
    expect(screen.queryByText('One-Page Resume')).not.toBeInTheDocument()
  })

  it('filters dashboard cards by category select', () => {
    render(<App />)

    fireEvent.change(screen.getByLabelText('Filter category'), {
      target: { value: 'timeline' },
    })

    expect(screen.getByText('Skills Timeline')).toBeInTheDocument()
    expect(screen.queryByText('Web Portfolio')).not.toBeInTheDocument()
  })
})
