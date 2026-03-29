import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ProfileView } from '../src/renderer/src/components/ProfileView'
import * as api from '../src/renderer/src/api'

vi.mock('../src/renderer/src/api', () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
}))

const mockGetProfile = vi.mocked(api.getProfile)
const mockUpdateProfile = vi.mocked(api.updateProfile)

const baseProfile: api.UserProfile = {
  user_id: 'default',
  name: 'Jane Smith',
  contact: {
    phone_number: '555-0000',
    email: 'jane@example.com',
    linkedin_url: 'https://linkedin.com/in/jane',
    github_url: 'https://github.com/jane',
    linkedin_label: 'LinkedIn',
    github_label: 'GitHub',
  },
  education: [
    {
      school: 'UVic',
      location: 'Victoria',
      degree: 'BSc',
      from: 'Sep 2022',
      to: 'May 2026',
      still_studying: false,
    },
  ],
  awards: ["Dean's List"],
  portfolio: {
    title: 'Full-Stack Developer',
    about_me: 'Building practical systems.',
    years_of_experience: '3+',
    open_source_contribution: '10+ PRs',
  },
  git_identifier: 'jane@example.com',
}

describe('ProfileView', () => {
  const onToast = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and displays profile fields on mount', async () => {
    mockGetProfile.mockResolvedValue(baseProfile)

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => {
      expect(screen.getByDisplayValue('Jane Smith')).toBeInTheDocument()
    })
    expect(screen.getAllByDisplayValue('jane@example.com').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByDisplayValue('UVic')).toBeInTheDocument()
    expect(screen.getByDisplayValue("Dean's List")).toBeInTheDocument()
  })

  it('shows not-found message when user config is absent', async () => {
    mockGetProfile.mockRejectedValue(new Error('404 Not Found'))

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => {
      expect(screen.getByText(/No user configuration found/i)).toBeInTheDocument()
    })
  })

  it('calls updateProfile and fires success toast on save', async () => {
    mockGetProfile.mockResolvedValue(baseProfile)
    mockUpdateProfile.mockResolvedValue(baseProfile)

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => screen.getByDisplayValue('Jane Smith'))

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Alice Cooper' } })
    fireEvent.click(screen.getByRole('button', { name: /save profile/i }))

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith(
        'default',
        expect.objectContaining({ name: 'Alice Cooper' }),
      )
    })
    expect(onToast).toHaveBeenCalledWith('Profile saved', 'success', expect.any(String))
  })

  it('fires error toast when updateProfile rejects', async () => {
    mockGetProfile.mockResolvedValue(baseProfile)
    mockUpdateProfile.mockRejectedValue(new Error('Network error'))

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => screen.getByDisplayValue('Jane Smith'))

    fireEvent.click(screen.getByRole('button', { name: /save profile/i }))

    await waitFor(() => {
      expect(onToast).toHaveBeenCalledWith('Save failed', 'error', 'Network error')
    })
  })

  it('shows loading state before profile resolves', () => {
    mockGetProfile.mockReturnValue(new Promise(() => {}))

    render(<ProfileView onToast={onToast} />)

    expect(screen.getByText(/loading profile/i)).toBeInTheDocument()
  })
})
