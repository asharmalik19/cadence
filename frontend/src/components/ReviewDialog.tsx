import { useState, type FormEvent } from 'react'
import type { ApiError } from '../api'
import { formatLong } from '../dates'
import type { DayUpdate, Goal, TodayTask } from '../types'
import { ErrorNotice } from './ErrorNotice'
import { PlanningIndicator } from './PlanningIndicator'
import { TaskCard } from './TaskCard'

interface Props {
  tasks: TodayTask[]
  goals: Goal[]
  currentDay: string
  onToggle: (taskId: number, done: boolean) => Promise<void>
  onConfirm: (updates: DayUpdate[]) => Promise<void>
  onClose: () => void
}

/**
 * End of the day: tick anything you did but forgot, say what happened per goal (optional), then confirm.
 * Whatever is still unticked counts as missed, and goals with a miss or an update are re-planned.
 */
export function ReviewDialog({ tasks, goals, currentDay, onToggle, onConfirm, onClose }: Props) {
  // The tasks unticked when the review opened stay listed, so ticking one doesn't make it jump away.
  const [reviewIds] = useState(() => new Set(tasks.filter((t) => t.status !== 'done').map((t) => t.id)))
  const [updates, setUpdates] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ message: string; retry?: boolean } | null>(null)

  const reviewTasks = tasks.filter((t) => reviewIds.has(t.id))
  const stillUnticked = reviewTasks.filter((t) => t.status !== 'done').length
  const written = goals
    .map((g) => ({ goal_id: g.id, text: (updates[g.id] ?? '').trim() }))
    .filter((u) => u.text.length > 0)
  const willReplan = stillUnticked > 0 || written.length > 0

  const toggle = async (taskId: number, done: boolean) => {
    setError(null)
    try {
      await onToggle(taskId, done)
    } catch (err) {
      setError({ message: (err as ApiError).message })
    }
  }

  const confirm = async (e?: FormEvent) => {
    e?.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onConfirm(written)
    } catch (err) {
      const apiError = err as ApiError
      setError({ message: apiError.message, retry: apiError.status !== 409 && apiError.status !== 404 })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="overlay">
      <form className="card dialog" onSubmit={confirm}>
        <div>
          <div className="label">End of {formatLong(currentDay)}</div>
          <h2 style={{ marginTop: 6 }}>Review your day</h2>
        </div>

        {reviewTasks.length > 0 ? (
          <section className="section">
            <p className="muted">Tick any you actually did. The rest are re-planned, nothing more.</p>
            <div className="today-tasks">
              {reviewTasks.map((t) => (
                <TaskCard key={t.id} task={t} goalLabel={t.goal_text} onToggle={(done) => toggle(t.id, done)} />
              ))}
            </div>
          </section>
        ) : (
          <p className="muted">Everything planned for today is ticked.</p>
        )}

        {goals.length > 0 && (
          <section className="section">
            <div>
              <h3>Anything new?</h3>
              <p className="muted" style={{ marginTop: 4, fontSize: 14 }}>
                Optional. Something you found out or changed your mind about, e.g. “DAAD deadline is 30 Nov” or
                “dropping Dubai”. The plan follows it.
              </p>
            </div>
            {goals.map((g) => (
              <label key={g.id} className="field">
                <span className="label">{g.text}</span>
                <textarea
                  value={updates[g.id] ?? ''}
                  onChange={(e) => setUpdates((prev) => ({ ...prev, [g.id]: e.target.value }))}
                  disabled={busy}
                  placeholder="Nothing new"
                />
              </label>
            ))}
          </section>
        )}

        {error && <ErrorNotice message={error.message} onRetry={error.retry ? () => confirm() : undefined} />}

        <div className="dialog-actions">
          {busy ? (
            <PlanningIndicator text={willReplan ? 'Re-planning…' : 'Moving to tomorrow…'} />
          ) : (
            <>
              <button type="button" className="btn-text" onClick={onClose}>
                Not yet
              </button>
              <button type="submit" className="btn">
                {willReplan ? 'Confirm and re-plan' : 'Confirm and start tomorrow'}
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  )
}
