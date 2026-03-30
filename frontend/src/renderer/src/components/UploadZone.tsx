import { useCallback, useRef, useState } from 'react'
import {
  setPrivacyConsent,
  setGitIdentifier,
  uploadProject,
  type UploadResponse,
} from '../api'

declare global {
  interface Window {
    electronAPI?: {
      selectZipFile: () => Promise<{ containerPath: string; fileName: string } | null>
      prepareZipForUpload: (
        filePath: string,
      ) => Promise<{ containerPath: string; fileName: string } | null>
      prepareDroppedZipForUpload: (
        fileName: string,
        bytes: Uint8Array,
      ) => Promise<{ containerPath: string; fileName: string } | null>
      platform: string
    }
  }
}

type UploadStep = 'idle' | 'consent' | 'processing' | 'done' | 'error'

const isElectron = !!window.electronAPI

export function UploadZone({
  onUploadComplete,
}: {
  onUploadComplete: (msg: string) => void
}) {
  const [step, setStep] = useState<UploadStep>('idle')
  const [dragging, setDragging] = useState(false)
  const [containerPath, setContainerPath] = useState<string | null>(null)
  const [fileName, setFileName] = useState('')
  const [manualPath, setManualPath] = useState('')

  // consent
  const [dataConsent, setDataConsent] = useState(true)
  const [llmConsent, setLlmConsent] = useState(false)
  const [gitId, setGitId] = useState('')

  // results
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState('')

  const inputRef = useRef<HTMLInputElement>(null)

  const pickFile = useCallback((cPath: string, name: string) => {
    setContainerPath(cPath)
    setFileName(name)
    setStep('consent')
    setResult(null)
    setErrorMsg('')
  }, [])

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const file = e.dataTransfer.files[0]
      if (!file) return
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setErrorMsg('Only .zip files are accepted.')
        setStep('error')
        return
      }
      const filePath = (file as File & { path?: string }).path
      try {
        if (filePath && window.electronAPI?.prepareZipForUpload) {
          const res = await window.electronAPI.prepareZipForUpload(filePath)
          if (res) pickFile(res.containerPath, res.fileName)
          else {
            setErrorMsg('Failed to prepare file for upload. The file may not exist or is inaccessible.')
            setStep('error')
          }
        } else if (window.electronAPI?.prepareDroppedZipForUpload) {
          const buf = await file.arrayBuffer()
          const res = await window.electronAPI.prepareDroppedZipForUpload(
            file.name,
            new Uint8Array(buf),
          )
          if (res) pickFile(res.containerPath, res.fileName)
          else {
            setErrorMsg('Failed to prepare dropped file for upload.')
            setStep('error')
          }
        } else if (filePath) {
          pickFile(filePath, file.name)
        } else {
          setErrorMsg('File upload requires the desktop app. Please run the Electron application.')
          setStep('error')
        }
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : 'Failed to prepare file')
        setStep('error')
      }
    },
    [pickFile],
  )

  const handleBrowse = useCallback(async () => {
    try {
      if (window.electronAPI?.selectZipFile) {
        const res = await window.electronAPI.selectZipFile()
        if (res) pickFile(res.containerPath, res.fileName)
        // null means user cancelled — that's fine, do nothing
      } else {
        // Browser fallback
        inputRef.current?.click()
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to open file picker')
      setStep('error')
    }
  }, [pickFile])

  const handleFileInput = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setErrorMsg('Only .zip files are accepted.')
        setStep('error')
        e.target.value = ''
        return
      }
      const filePath = (file as File & { path?: string }).path
      try {
        if (filePath && window.electronAPI?.prepareZipForUpload) {
          const res = await window.electronAPI.prepareZipForUpload(filePath)
          if (res) pickFile(res.containerPath, res.fileName)
          else {
            setErrorMsg('Failed to prepare file for upload.')
            setStep('error')
          }
        } else if (filePath) {
          pickFile(filePath, file.name)
        } else {
          // Browser mode — no Electron path access
          setErrorMsg('File upload requires the desktop app. Please run the Electron application.')
          setStep('error')
        }
      } catch (err) {
        setErrorMsg(err instanceof Error ? err.message : 'Failed to prepare file')
        setStep('error')
      }
      e.target.value = ''
    },
    [pickFile],
  )

  const handleSubmit = useCallback(async () => {
    if (!containerPath) return
    setStep('processing')
    setErrorMsg('')

    const userId = 'default'

    try {
      // Step 1: Set consent
      await setPrivacyConsent({
        user_id: userId,
        zip_path: containerPath,
        llm_consent: llmConsent,
        data_access_consent: dataConsent,
      })

      // Step 2: Set git identifier (optional)
      if (gitId.trim()) {
        await setGitIdentifier({ user_id: userId, git_identifier: gitId.trim() })
      }

      // Step 3: Run pipeline
      const res = await uploadProject({ zip_path: containerPath, user_id: userId })
      setResult(res)
      setStep('done')
      onUploadComplete(
        `Analysis complete! Found ${res.projects?.length ?? 0} project(s).`,
      )
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Upload failed'
      setErrorMsg(msg)
      setStep('error')
      onUploadComplete(msg)
    }
  }, [containerPath, llmConsent, dataConsent, gitId, onUploadComplete])

  const handleReset = useCallback(() => {
    setStep('idle')
    setContainerPath(null)
    setFileName('')
    setDataConsent(true)
    setLlmConsent(false)
    setGitId('')
    setResult(null)
    setErrorMsg('')
  }, [])

  const handleManualSubmit = useCallback(() => {
    const p = manualPath.trim()
    if (!p) return
    const name = p.split('/').pop() || p
    pickFile(p, name)
  }, [manualPath, pickFile])

  // ── Step: Select file ──
  if (step === 'idle') {
    return (
      <div
        className={`upload-zone ${dragging ? 'upload-zone--active' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".zip"
          onChange={handleFileInput}
          style={{ display: 'none' }}
        />
        <div className="upload-zone__icon">📦</div>
        <h3 className="upload-zone__title">Drop your .zip folder here</h3>
        <p className="upload-zone__subtitle">or click to browse</p>
        <button className="btn-primary upload-zone__btn" onClick={handleBrowse}>
          Select ZIP File
        </button>
        {!isElectron && (
          <div className="upload-zone__manual">
            <p className="upload-zone__note" style={{ marginBottom: 8 }}>
              Browser mode — enter the path to your ZIP on the server:
            </p>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                className="input"
                type="text"
                placeholder="/uploads/my-project.zip"
                value={manualPath}
                onChange={(e) => setManualPath(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleManualSubmit() }}
                style={{ flex: 1 }}
              />
              <button
                className="btn-primary"
                onClick={handleManualSubmit}
                disabled={!manualPath.trim()}
              >
                Use Path
              </button>
            </div>
          </div>
        )}
        <p className="upload-zone__note">Accepts .zip files only</p>
      </div>
    )
  }

  // ── Step: Consent ──
  if (step === 'consent') {
    return (
      <div className="upload-zone upload-zone--form">
        <div className="upload-consent">
          <div className="upload-consent__file">
            <span className="upload-consent__file-icon">📁</span>
            <div>
              <span className="upload-consent__file-name">{fileName}</span>
              <button className="upload-consent__change" onClick={handleReset}>
                Change file
              </button>
            </div>
          </div>

          <h3 className="upload-consent__title">Before we analyze</h3>
          <p className="upload-consent__desc">
            Please review the permissions below. Your data is processed locally and
            stored encrypted.
          </p>

          <label className="upload-consent__check">
            <input
              type="checkbox"
              checked={dataConsent}
              onChange={(e) => setDataConsent(e.target.checked)}
            />
            <div>
              <span className="upload-consent__check-label">Data Access Consent</span>
              <span className="upload-consent__check-hint">
                Allow the system to read and analyze the contents of your ZIP file
              </span>
            </div>
          </label>

          <label className="upload-consent__check">
            <input
              type="checkbox"
              checked={llmConsent}
              onChange={(e) => setLlmConsent(e.target.checked)}
            />
            <div>
              <span className="upload-consent__check-label">
                AI-Enhanced Analysis (Optional)
              </span>
              <span className="upload-consent__check-hint">
                Use an external LLM for richer summaries and resume bullets
              </span>
            </div>
          </label>

          <label className="upload-consent__field">
            <span>Git Identifier (optional)</span>
            <input
              className="input"
              type="text"
              placeholder="e.g. your-github@users.noreply.github.com"
              value={gitId}
              onChange={(e) => setGitId(e.target.value)}
            />
            <span className="upload-consent__check-hint">
              Helps identify your contributions in collaborative projects
            </span>
          </label>

          <div className="upload-consent__actions">
            <button
              className="btn-primary"
              onClick={handleSubmit}
              disabled={!dataConsent}
            >
              Start Analysis
            </button>
            <button className="reset-btn" onClick={handleReset}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ── Step: Processing ──
  if (step === 'processing') {
    return (
      <div className="upload-zone upload-zone--processing">
        <div className="upload-progress">
          <div className="upload-progress__spinner" />
          <h3 className="upload-progress__title">Analyzing your projects...</h3>
          <p className="upload-progress__subtitle">
            Extracting files, parsing code, building resume — this may take a moment.
          </p>
          <div className="upload-progress__steps">
            {[
              'Upload received',
              'Extracting files',
              'Parsing content',
              'Building resume',
              'Quality check',
            ].map((s, i) => (
              <div key={i} className="upload-progress__step">
                <span className="upload-progress__step-dot" />
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  // ── Step: Done ──
  if (step === 'done' && result) {
    return (
      <div className="upload-zone upload-zone--done">
        <div className="upload-result">
          <div className="upload-result__icon">✓</div>
          <h3 className="upload-result__title">Analysis Complete</h3>
          <div className="upload-result__stats">
            <div className="upload-result__stat">
              <span className="upload-result__stat-value">
                {result.projects?.length ?? 0}
              </span>
              <span className="upload-result__stat-label">Projects Found</span>
            </div>
            {result.zip_hash && (
              <div className="upload-result__stat">
                <span className="upload-result__stat-value">
                  {result.zip_hash.slice(0, 8)}...
                </span>
                <span className="upload-result__stat-label">ZIP Hash</span>
              </div>
            )}
            {result.resume_pdf_path && (
              <div className="upload-result__stat">
                <span className="upload-result__stat-value">✓</span>
                <span className="upload-result__stat-label">Resume PDF</span>
              </div>
            )}
          </div>
          {result.projects && result.projects.length > 0 && (
            <div className="upload-result__projects">
              {result.projects.map((name) => (
                <span key={name} className="skill-pill">{name}</span>
              ))}
            </div>
          )}
          <button className="btn-primary" onClick={handleReset}>
            Upload Another
          </button>
        </div>
      </div>
    )
  }

  // ── Step: Error ──
  return (
    <div className="upload-zone upload-zone--error">
      <div className="upload-result">
        <div className="upload-result__icon upload-result__icon--error">✕</div>
        <h3 className="upload-result__title">Analysis Failed</h3>
        <p className="upload-result__error">{errorMsg}</p>
        <button className="btn-primary" onClick={handleReset}>
          Try Again
        </button>
      </div>
    </div>
  )
}
