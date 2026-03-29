import { useCallback, useEffect, useState } from 'react'
import { getProfile, updateProfile, type ProfileUpdateRequest } from '../api'

const USER_ID = 'default'

type EducationEntry = {
  school: string
  location: string
  degree: string
  from: string
  to: string
  still_studying: boolean
}

type FormState = {
  name: string
  phone_number: string
  email: string
  linkedin_url: string
  github_url: string
  linkedin_label: string
  github_label: string
  git_identifier: string
  education: EducationEntry[]
  awards_text: string
  portfolio_title: string
  portfolio_about_me: string
  portfolio_years_of_experience: string
  portfolio_open_source_contribution: string
}

type SaveStatus = 'idle' | 'saving' | 'success' | 'error'

const blankEducation = (): EducationEntry => ({
  school: '',
  location: '',
  degree: '',
  from: '',
  to: '',
  still_studying: false,
})

const EMPTY: FormState = {
  name: '',
  phone_number: '',
  email: '',
  linkedin_url: '',
  github_url: '',
  linkedin_label: '',
  github_label: '',
  git_identifier: '',
  education: [blankEducation()],
  awards_text: '',
  portfolio_title: '',
  portfolio_about_me: '',
  portfolio_years_of_experience: '',
  portfolio_open_source_contribution: '',
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  full,
}: {
  label: string
  value: string
  onChange: React.ChangeEventHandler<HTMLInputElement>
  type?: string
  placeholder?: string
  full?: boolean
}) {
  return (
    <label className={`modal-field${full ? ' modal-field--full' : ''}`}>
      <span>{label}</span>
      <input className="input" type={type} value={value} onChange={onChange} placeholder={placeholder} />
    </label>
  )
}

export function ProfileView({
  onToast,
  onProfileSaved,
}: {
  onToast: (title: string, type: 'success' | 'error', subtitle?: string) => void
  onProfileSaved?: () => void
}) {
  const [form, setForm] = useState<FormState>(EMPTY)
  const [loading, setLoading] = useState(true)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [notFound, setNotFound] = useState(false)

  const loadProfile = useCallback(async () => {
    setLoading(true)
    try {
      const profile = await getProfile(USER_ID)
      setForm({
        name: profile.name ?? '',
        phone_number: profile.contact?.phone_number ?? '',
        email: profile.contact?.email ?? profile.email ?? '',
        linkedin_url: profile.contact?.linkedin_url ?? '',
        github_url: profile.contact?.github_url ?? '',
        linkedin_label: profile.contact?.linkedin_label ?? '',
        github_label: profile.contact?.github_label ?? '',
        git_identifier: profile.git_identifier ?? '',
        education: profile.education.length > 0
          ? profile.education.map((entry) => ({
            school: entry.school ?? '',
            location: entry.location ?? '',
            degree: entry.degree ?? '',
            from: entry.from ?? '',
            to: entry.to ?? '',
            still_studying: Boolean(entry.still_studying),
          }))
          : [blankEducation()],
        awards_text: Array.isArray(profile.awards) ? profile.awards.join('\n') : '',
        portfolio_title: profile.portfolio?.title ?? '',
        portfolio_about_me: profile.portfolio?.about_me ?? '',
        portfolio_years_of_experience: profile.portfolio?.years_of_experience ?? '',
        portfolio_open_source_contribution: profile.portfolio?.open_source_contribution ?? '',
      })
      setNotFound(false)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('404') || msg.toLowerCase().includes('not found')) setNotFound(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProfile()
  }, [loadProfile])

  const handleFieldChange = <K extends keyof Omit<FormState, 'education' | 'awards_text'>>(key: K) =>
    (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [key]: event.target.value }))
      if (saveStatus !== 'idle') setSaveStatus('idle')
    }

  const handleEducationChange = (
    index: number,
    field: keyof EducationEntry,
    value: string | boolean,
  ) => {
    setForm((prev) => ({
      ...prev,
      education: prev.education.map((entry, currentIndex) => (
        currentIndex === index ? { ...entry, [field]: value } : entry
      )),
    }))
    if (saveStatus !== 'idle') setSaveStatus('idle')
  }

  const addEducationEntry = () => {
    setForm((prev) => ({ ...prev, education: [...prev.education, blankEducation()] }))
  }

  const removeEducationEntry = (index: number) => {
    setForm((prev) => ({
      ...prev,
      education: prev.education.length === 1
        ? [blankEducation()]
        : prev.education.filter((_, currentIndex) => currentIndex !== index),
    }))
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaveStatus('saving')

    const awards = form.awards_text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)

    const payload: ProfileUpdateRequest = {
      name: form.name,
      git_identifier: form.git_identifier,
      contact: {
        phone_number: form.phone_number,
        email: form.email,
        linkedin_url: form.linkedin_url,
        github_url: form.github_url,
        linkedin_label: form.linkedin_label,
        github_label: form.github_label,
      },
      education: form.education
        .map((entry) => ({
          school: entry.school.trim(),
          location: entry.location.trim(),
          degree: entry.degree.trim(),
          from: entry.from.trim(),
          to: entry.to.trim(),
          still_studying: Boolean(entry.still_studying),
        }))
        .filter((entry) => Object.values(entry).some((value) => value === true || (typeof value === 'string' && value.length > 0))),
      awards,
      portfolio: {
        title: form.portfolio_title,
        about_me: form.portfolio_about_me,
        years_of_experience: form.portfolio_years_of_experience,
        open_source_contribution: form.portfolio_open_source_contribution,
      },
    }

    try {
      await updateProfile(USER_ID, payload)
      setSaveStatus('success')
      onToast('Profile saved', 'success', 'Your profile has been updated.')
      onProfileSaved?.()
    } catch (err: unknown) {
      setSaveStatus('error')
      onToast('Save failed', 'error', err instanceof Error ? err.message : 'Unknown error')
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted, #888)' }}>Loading profile…</p>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="card" style={{ padding: '2rem' }}>
        <p style={{ color: 'var(--text-muted, #888)' }}>
          No user configuration found. Upload a project first to create a user record, then return here to fill out your profile.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Basic Info</h3>
          <p style={{ margin: 0, color: 'var(--text-muted, #888)', fontSize: '0.875rem' }}>
            This information is reused for resume and portfolio generation.
          </p>
        </div>
        <div className="modal-form-grid modal-form-grid--two">
          <Field label="Name" value={form.name} onChange={handleFieldChange('name')} placeholder="e.g. Jane Smith" full />
          <Field label="Git Identifier" value={form.git_identifier} onChange={handleFieldChange('git_identifier')} placeholder="Email or username used in commits" />
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Contact</h3>
        </div>
        <div className="modal-form-grid modal-form-grid--two">
          <Field label="Phone Number" value={form.phone_number} onChange={handleFieldChange('phone_number')} placeholder="Phone number" />
          <Field label="Email" type="email" value={form.email} onChange={handleFieldChange('email')} placeholder="Email address" />
          <Field label="LinkedIn URL" value={form.linkedin_url} onChange={handleFieldChange('linkedin_url')} placeholder="LinkedIn URL" />
          <Field label="LinkedIn Label" value={form.linkedin_label} onChange={handleFieldChange('linkedin_label')} placeholder="e.g. LinkedIn" />
          <Field label="GitHub URL" value={form.github_url} onChange={handleFieldChange('github_url')} placeholder="GitHub URL" />
          <Field label="GitHub Label" value={form.github_label} onChange={handleFieldChange('github_label')} placeholder="e.g. GitHub" />
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div className="modal-section__heading" style={{ marginBottom: '1rem' }}>
          <div>
            <h3 style={{ margin: '0 0 0.25rem' }}>Education</h3>
            <p className="modal-helper">Add one or more education entries used in resume generation.</p>
          </div>
          <button className="action-btn" type="button" onClick={addEducationEntry}>
            Add Education
          </button>
        </div>
        <div className="modal-education-list">
          {form.education.map((entry, index) => (
            <div key={index} className="modal-education-card">
              <div className="modal-form-grid modal-form-grid--two">
                <Field label="School" value={entry.school} onChange={(event) => handleEducationChange(index, 'school', event.target.value)} placeholder="University or school" />
                <Field label="Location" value={entry.location} onChange={(event) => handleEducationChange(index, 'location', event.target.value)} placeholder="Location" />
                <Field label="Degree" value={entry.degree} onChange={(event) => handleEducationChange(index, 'degree', event.target.value)} placeholder="Degree or program" />
                <Field label="From" value={entry.from} onChange={(event) => handleEducationChange(index, 'from', event.target.value)} placeholder="Sep 2022" />
                <Field label="To" value={entry.to} onChange={(event) => handleEducationChange(index, 'to', event.target.value)} placeholder="May 2026" />
              </div>
              <label className="modal-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(entry.still_studying)}
                  onChange={(event) => handleEducationChange(index, 'still_studying', event.target.checked)}
                />
                <span>Still studying</span>
              </label>
              <div className="modal-education-actions">
                <button className="reset-btn" type="button" onClick={() => removeEducationEntry(index)}>
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Awards</h3>
          <p className="modal-helper">One award per line.</p>
        </div>
        <label className="modal-field modal-field--full">
          <span>Awards</span>
          <textarea
            className="input"
            rows={4}
            value={form.awards_text}
            onChange={(event) => {
              setForm((prev) => ({ ...prev, awards_text: event.target.value }))
              if (saveStatus !== 'idle') setSaveStatus('idle')
            }}
            placeholder="Dean's List&#10;Hackathon Winner"
          />
        </label>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ margin: '0 0 0.25rem' }}>Portfolio</h3>
        </div>
        <div className="modal-form-grid modal-form-grid--two">
          <Field label="Portfolio Title" value={form.portfolio_title} onChange={handleFieldChange('portfolio_title')} placeholder="e.g. Full-Stack Developer" />
          <Field label="Years of Experience" value={form.portfolio_years_of_experience} onChange={handleFieldChange('portfolio_years_of_experience')} placeholder="e.g. 3+" />
          <Field label="Open Source Contribution" value={form.portfolio_open_source_contribution} onChange={handleFieldChange('portfolio_open_source_contribution')} placeholder="e.g. 25+ PRs" />
          <label className="modal-field modal-field--full">
            <span>About Me</span>
            <textarea
              className="input"
              rows={4}
              value={form.portfolio_about_me}
              onChange={handleFieldChange('portfolio_about_me')}
              placeholder="Short summary for your portfolio hero section."
            />
          </label>
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
