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
  first_name: 'Jane',
  last_name: 'Smith',
  email: 'jane@example.com',
  github_username: 'janesmith',
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
      expect(screen.getByDisplayValue('Jane')).toBeInTheDocument()
    })
    expect(screen.getByDisplayValue('Smith')).toBeInTheDocument()
    // email and git_identifier both hold 'jane@example.com' — confirm both are present
    expect(screen.getAllByDisplayValue('jane@example.com').length).toBeGreaterThanOrEqual(2)
    expect(screen.getByDisplayValue('janesmith')).toBeInTheDocument()
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
    mockUpdateProfile.mockResolvedValue({ ...baseProfile, first_name: 'Alice' })

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => screen.getByDisplayValue('Jane'))

    fireEvent.change(screen.getByLabelText('First Name'), { target: { value: 'Alice' } })
    fireEvent.click(screen.getByRole('button', { name: /save profile/i }))

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith(
        'default',
        expect.objectContaining({ first_name: 'Alice' }),
      )
    })
    expect(onToast).toHaveBeenCalledWith('Profile saved', 'success', expect.any(String))
  })

  it('fires error toast when updateProfile rejects', async () => {
    mockGetProfile.mockResolvedValue(baseProfile)
    mockUpdateProfile.mockRejectedValue(new Error('Network error'))

    render(<ProfileView onToast={onToast} />)

    await waitFor(() => screen.getByDisplayValue('Jane'))

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
