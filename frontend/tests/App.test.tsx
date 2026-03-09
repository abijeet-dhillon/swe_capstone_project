import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import App from '../src/renderer/src/App'

describe('App', () => {
  it('renders the application title', () => {
    render(<App />)
    expect(
      screen.getByText('Digital Work Artifact Miner')
    ).toBeInTheDocument()
  })

  it('renders the team subtitle', () => {
    render(<App />)
    expect(
      screen.getByText('Team 14 — Capstone Project')
    ).toBeInTheDocument()
  })

  it('renders the welcome card', () => {
    render(<App />)
    expect(screen.getByText('Welcome')).toBeInTheDocument()
    expect(
      screen.getByText(/privacy-first pipeline/i)
    ).toBeInTheDocument()
  })

  it('renders quick action buttons', () => {
    render(<App />)
    expect(screen.getByText('Upload Project')).toBeInTheDocument()
    expect(screen.getByText('View Projects')).toBeInTheDocument()
    expect(screen.getByText('Generate Report')).toBeInTheDocument()
  })

  it('has action buttons disabled initially', () => {
    render(<App />)
    const uploadBtn = screen.getByText('Upload Project')
    const viewBtn = screen.getByText('View Projects')
    const reportBtn = screen.getByText('Generate Report')

    expect(uploadBtn).toBeDisabled()
    expect(viewBtn).toBeDisabled()
    expect(reportBtn).toBeDisabled()
  })

  it('renders the footer', () => {
    render(<App />)
    expect(
      screen.getByText('COSC 499 — Digital Work Artifact Miner')
    ).toBeInTheDocument()
  })
})
