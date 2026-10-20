import { useState, type FormEvent } from 'react'
import type { ApiError } from '../api'
import { formatDay } from '../dates'
import type { Update } from '../types'
import { ErrorNotice } from './ErrorNotice'
import { PlanningIndicator } from './PlanningIndicator'

interface Props {
  updates: Update[]
  onSubmit: (text: string) => Promise<void>
}

/** What happened or changed, in your words. Each one is kept and re-plans the goal right away. */
export function UpdateBox({ updates, onSubmit }: Props) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ message: string; retry: boolean } | null>(null)

  const submit = async (e?: FormEvent) => {
    e?.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      await onSubmit(text.trim())
      setText('')
    } catch (err) {
      const apiError = err as ApiError
      setError({ message: apiError.message, retry: apiError.status >= 500 || apiError.status === 0 })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="update-box">
      {updates.length > 0 && (
        <ul className="updates">
          {updates.map((u) => (
            <li key={u.id}>
              <span className="milestone-date">{formatDay(u.day, { day: 'numeric', month: 'short' })}</span>
              <span>{u.text}</span>
            </li>
          ))}
        </ul>
      )}
      <form className="card section" onSubmit={submit}>
        <label className="field">
          <span className="label">Anything new?</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={busy}
            placeholder="Something you found out or changed your mind about, e.g. “DAAD deadline is 30 Nov”"
          />
        </label>
        {error && <ErrorNotice message={error.message} onRetry={error.retry ? () => submit() : undefined} />}
        <div className="dialog-actions">
          {busy ? (
            <PlanningIndicator text="Re-planning around your update…" />
          ) : (
            <button type="submit" className="btn btn-quiet" disabled={!text.trim()}>
              Re-plan with this
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
