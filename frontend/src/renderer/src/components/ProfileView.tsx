import { useCallback, useEffect, useState } from 'react'
import { getProfile, updateProfile, type ProfileUpdateRequest } from '../api'

const USER_ID = 'default'
type FormState = { first_name: string; last_name: string; email: string; github_username: string; git_identifier: string }
type SaveStatus = 'idle' | 'saving' | 'success' | 'error'
const EMPTY: FormState = { first_name: '', last_name: '', email: '', github_username: '', git_identifier: '' }

function Field({ id, label, value, onChange, type = 'text', placeholder, hint, full, badge }: {
  id: keyof FormState; label: string; value: string; onChange: (f: keyof FormState) => React.ChangeEventHandler<HTMLInputElement>
  type?: string; placeholder?: string; hint?: string; full?: boolean; badge?: string
}) {
  return (
    <div className={`profile-field${full ? ' profile-field--full' : ''}`}>
      <label className="profile-label" htmlFor={id}>
        {label}
        {badge && <span className="pill info" style={{ marginLeft: '0.5rem', fontSize: '0.7rem', verticalAlign: 'middle' }}>{badge}</span>}
      </label>
      <input id={id} className="input" type={type} placeholder={placeholder} value={value} onChange={onChange(id)} />
      {hint && <span style={{ display: 'block', marginTop: '0.35rem', fontSize: '0.78rem', color: 'var(--text-muted, #888)' }}>{hint}</span>}
    </div>
  )
}

export function ProfileView({ onToast }: { onToast: (title: string, type: 'success' | 'error', subtitle?: string) => void }) {
  const [form, setForm] = useState<FormState>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [notFound, setNotFound] = useState(false)

  const loadProfile = useCallback(async () => {
    setLoading(true)
    try {
      const p = await getProfile(USER_ID)
      setForm({ first_name: p.first_name ?? '', last_name: p.last_name ?? '', email: p.email ?? '', github_username: p.github_username ?? '', git_identifier: p.git_identifier ?? '' })
      setNotFound(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) setNotFound(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadProfile() }, [loadProfile])

  const handleChange = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }))
    if (saveStatus !== 'idle') setSaveStatus('idle')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaveStatus('saving')
    const payload: ProfileUpdateRequest = {}
    for (const k of Object.keys(form) as (keyof FormState)[]) {
      if (form[k].trim()) payload[k] = form[k].trim()
    }
    try {
      await updateProfile(USER_ID, payload)
      setSaveStatus('success')
      onToast('Profile saved', 'success', 'Your profile has been updated.')
    } catch (err: unknown) {
      setSaveStatus('error')
      onToast('Save failed', 'error', err instanceof Error ? err.message : 'Unknown error')
    }
  }

  if (loading) return <div className="card" style={{ padding: '2rem', textAlign: 'center' }}><p style={{ color: 'var(--text-muted, #888)' }}>Loading profile…</p></div>
  if (notFound) return <div className="card" style={{ padding: '2rem' }}><p style={{ color: 'var(--text-muted, #888)' }}>No user configuration found. Upload a project first to create a user record, then return here to fill in your profile.</p></div>

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Personal Information</h3>
          <p style={{ margin: 0, color: 'var(--text-muted, #888)', fontSize: '0.875rem' }}>Used when generating your resume and portfolio.</p>
        </div>
        <div className="profile-fields">
          <Field id="first_name" label="First Name" value={form.first_name} onChange={handleChange} placeholder="e.g. Jane" />
          <Field id="last_name" label="Last Name" value={form.last_name} onChange={handleChange} placeholder="e.g. Smith" />
          <Field id="email" label="Email" type="email" value={form.email} onChange={handleChange} placeholder="e.g. jane@example.com" full />
        </div>
      </div>
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Developer Identity</h3>
          <p style={{ margin: 0, color: 'var(--text-muted, #888)', fontSize: '0.875rem' }}>Helps attribute commits and link your GitHub account.</p>
        </div>
        <div className="profile-fields">
          <Field id="github_username" label="GitHub Username" value={form.github_username} onChange={handleChange} placeholder="e.g. janesmith" />
          <Field id="git_identifier" label="Git Identifier" value={form.git_identifier} onChange={handleChange} placeholder="e.g. jane@example.com or janesmith" badge="commit filter" hint="Used to filter git commits to your own contributions during analysis." />
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <button type="submit" className="action-btn" disabled={saveStatus === 'saving'} style={{ minWidth: '9rem' }}>
          {saveStatus === 'saving' ? 'Saving…' : 'Save Profile'}
        </button>
        {saveStatus === 'success' && <span className="pill ready" style={{ fontSize: '0.8rem' }}>Saved</span>}
        {saveStatus === 'error' && <span className="pill coming-soon" style={{ fontSize: '0.8rem' }}>Save failed</span>}
      </div>
    </form>
  )
}
