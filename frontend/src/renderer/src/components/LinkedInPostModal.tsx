import { useEffect, useState } from 'react'
import { getLinkedInPreview, type LinkedInPreview } from '../api'

export function LinkedInPostModal({
  projectId,
  projectName,
  onClose,
}: {
  projectId: number
  projectName: string
  onClose: () => void
}) {
  const [preview, setPreview] = useState<LinkedInPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [includeHashtags, setIncludeHashtags] = useState(true)
  const [includeEmojis, setIncludeEmojis] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getLinkedInPreview(projectId, { includeHashtags, includeEmojis })
      .then((data) => {
        setPreview(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || 'Failed to generate LinkedIn post')
        setLoading(false)
      })
  }, [projectId, includeHashtags, includeEmojis])

  const handleCopy = async () => {
    if (!preview) return
    try {
      await navigator.clipboard.writeText(preview.text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      const textarea = document.createElement('textarea')
      textarea.value = preview.text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="linkedin-modal-overlay" onClick={onClose}>
      <div className="linkedin-modal" onClick={(e) => e.stopPropagation()}>
        <div className="linkedin-modal__header">
          <div className="linkedin-modal__header-left">
            <span className="linkedin-modal__icon">in</span>
            <h3>LinkedIn Post</h3>
          </div>
          <button className="linkedin-modal__close" onClick={onClose}>
            &times;
          </button>
        </div>

        <p className="linkedin-modal__subtitle">
          Generated for <strong>{projectName}</strong>
        </p>

        <div className="linkedin-modal__options">
          <label className="linkedin-modal__toggle">
            <input
              type="checkbox"
              checked={includeHashtags}
              onChange={(e) => setIncludeHashtags(e.target.checked)}
            />
            <span>Hashtags</span>
          </label>
          <label className="linkedin-modal__toggle">
            <input
              type="checkbox"
              checked={includeEmojis}
              onChange={(e) => setIncludeEmojis(e.target.checked)}
            />
            <span>Emojis</span>
          </label>
        </div>

        {loading ? (
          <div className="linkedin-modal__loading">
            <div className="linkedin-modal__spinner" />
            <span>Generating post...</span>
          </div>
        ) : error ? (
          <div className="linkedin-modal__error">
            <span className="linkedin-modal__error-icon">!</span>
            <p>{error}</p>
          </div>
        ) : preview ? (
          <>
            <div className="linkedin-modal__preview">
              <pre className="linkedin-modal__text">{preview.text}</pre>
            </div>

            <div className="linkedin-modal__footer">
              <span className="linkedin-modal__char-count">
                {preview.char_count} / 3,000 chars
                {preview.exceeds_limit && (
                  <span className="linkedin-modal__char-warn"> — over limit</span>
                )}
              </span>
              <button
                className={`linkedin-modal__copy ${copied ? 'linkedin-modal__copy--success' : ''}`}
                onClick={handleCopy}
              >
                {copied ? 'Copied!' : 'Copy to Clipboard'}
              </button>
            </div>

            {preview.hashtags.length > 0 && (
              <div className="linkedin-modal__hashtags">
                {preview.hashtags.map((tag, i) => (
                  <span key={i} className="linkedin-modal__tag">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  )
}
