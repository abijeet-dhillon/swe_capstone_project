import { useEffect } from 'react'

export type ToastData = {
  id: number
  title: string
  subtitle?: string
  type: 'success' | 'error' | 'info'
}

export function Toast({
  toast,
  onDismiss,
}: {
  toast: ToastData
  onDismiss: (id: number) => void
}) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 3000)
    return () => clearTimeout(timer)
  }, [toast.id, onDismiss])

  const iconMap = { success: '✓', error: '✕', info: 'ℹ' }
  const colorMap = { success: 'toast-success', error: 'toast-error', info: 'toast-info' }

  return (
    <div className={`toast ${colorMap[toast.type]}`}>
      <span className="toast-icon">{iconMap[toast.type]}</span>
      <div className="toast-body">
        <span className="toast-title">{toast.title}</span>
        {toast.subtitle && <span className="toast-subtitle">{toast.subtitle}</span>}
      </div>
    </div>
  )
}

export function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: ToastData[]
  onDismiss: (id: number) => void
}) {
  if (toasts.length === 0) return null
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <Toast key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
