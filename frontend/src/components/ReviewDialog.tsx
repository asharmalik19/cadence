import { useState, type FormEvent } from 'react'
import type { ApiError } from '../api'
import { addDays, formatDay, formatLong } from '../dates'
import type { DayUpdate, Goal, TodayTask } from '../types'
import { ErrorNotice } from './ErrorNotice'
import { PlanningIndicator } from './PlanningIndicator'
import { TaskCard } from './TaskCard'

export interface CloseDays {
  updates: DayUpdate[]
  /** Fast forward only: the day to land on, and the tasks ticked on the days being closed. */
  toDay?: string
  doneTaskIds?: number[]
}

interface Props {
  tasks: TodayTask[]
  goals: Goal[]
  currentDay: string
  /** Set for Fast forward: the real date, which the date picker starts on. */
  realToday?: string
  onToggle: (taskId: number, done: boolean) => Promise<void>
  onConfirm: (close: CloseDays) => Promise<void>
  onClose: () => void
}

/**
 * End of the day (or of several days, for Fast forward): tick anything you did but forgot, say what happened
 * per goal (optional), then confirm. Whatever is still unticked counts as missed, and goals with a miss or an
 * update are re-planned once.
 */
export function ReviewDialog({ tasks, goals, currentDay, realToday, onToggle, onConfirm, onClose }: Props) {
  const forward = realToday !== undefined
  const [toDay, setToDay] = useState(() =>
    forward && realToday > currentDay ? realToday : addDays(currentDay, 1),
  )
  // Fast forward ticks stay here until Confirm: the skipped days aren't "today" yet, so they can't be ticked live.
  const [ticked, setTicked] = useState<Set<number>>(new Set())
  // The tasks unticked when the review opened stay listed, so ticking one doesn't make it jump away.
  const [reviewIds] = useState(() => {
    const all = forward ? goals.flatMap((g) => g.tasks) : tasks
    return new Set(all.filter((t) => t.status === 'planned').map((t) => t.id))
  })
  const [updates, setUpdates] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ message: string; retry?: boolean } | null>(null)

  const reviewTasks: TodayTask[] = forward
    ? goals
        .flatMap((g) => g.tasks.map((t) => ({ ...t, goal_text: g.text })))
        .filter((t) => reviewIds.has(t.id) && t.day >= currentDay && t.day < toDay)
        .map((t) => (ticked.has(t.id) ? { ...t, status: 'done' as const } : t))
        .sort((a, b) => a.day.localeCompare(b.day))
    : tasks.filter((t) => reviewIds.has(t.id))
  const days = [...new Set(reviewTasks.map((t) => t.day))]
  const stillUnticked = reviewTasks.filter((t) => t.status !== 'done').length
  const written = goals
    .map((g) => ({ goal_id: g.id, text: (updates[g.id] ?? '').trim() }))
    .filter((u) => u.text.length > 0)
  const willReplan = stillUnticked > 0 || written.length > 0
  const severalGoals = goals.length > 1

  const toggle = async (taskId: number, done: boolean) => {
    setError(null)
    if (forward) {
      setTicked((prev) => {
        const next = new Set(prev)
        if (done) next.add(taskId)
        else next.delete(taskId)
        return next
      })
      return
    }
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
      const doneTaskIds = reviewTasks.filter((t) => ticked.has(t.id)).map((t) => t.id)
      await onConfirm(forward ? { updates: written, toDay, doneTaskIds } : { updates: written })
    } catch (err) {
      const apiError = err as ApiError
      setError({ message: apiError.message, retry: apiError.status !== 409 && apiError.status !== 404 })
    } finally {
      setBusy(false)
    }
  }

  const card = (t: TodayTask) => (
    <TaskCard
      key={t.id}
      task={t}
      goalLabel={severalGoals ? t.goal_text : undefined}
      onToggle={(done) => toggle(t.id, done)}
      compact
    />
  )

  return (
    <div className="overlay">
      <form className="card dialog" onSubmit={confirm}>
        <div>
          <div className="label">
            {forward ? `Since ${formatLong(currentDay)}` : `End of ${formatLong(currentDay)}`}
          </div>
          <h2 style={{ marginTop: 6 }}>{forward ? 'Catch up to today' : 'Review your day'}</h2>
        </div>

        {forward && (
          <label className="field">
            <span className="muted">Fast forward to</span>
            <input
              type="date"
              value={toDay}
              min={addDays(currentDay, 1)}
              onChange={(e) => e.target.value && setToDay(e.target.value)}
              disabled={busy}
            />
          </label>
        )}

        {reviewTasks.length > 0 ? (
          <section className="section">
            <p className="muted">Tick what you did. The rest get re-planned.</p>
            {forward ? (
              days.map((day) => (
                <div key={day} className="review-day">
                  <h3>{formatDay(day)}</h3>
                  <div className="today-tasks">{reviewTasks.filter((t) => t.day === day).map(card)}</div>
                </div>
              ))
            ) : (
              <div className="today-tasks">{reviewTasks.map(card)}</div>
            )}
          </section>
        ) : (
          <p className="muted">
            {forward ? 'Nothing unticked on these days.' : 'Everything planned for today is ticked.'}
          </p>
        )}

        {goals.length > 0 && (
          <section className="section">
            <h3>
              Anything new? <span className="muted review-optional">Optional</span>
            </h3>
            {goals.map((g) => (
              <label key={g.id} className="field">
                {severalGoals && <span className="task-goal">{g.text}</span>}
                <textarea
                  value={updates[g.id] ?? ''}
                  onChange={(e) => setUpdates((prev) => ({ ...prev, [g.id]: e.target.value }))}
                  disabled={busy}
                  aria-label={`What's new for ${g.text}`}
                  placeholder={forward ? 'e.g. “was sick for three days”' : 'e.g. “the deadline moved to 30 Nov”'}
                />
              </label>
            ))}
          </section>
        )}

        {error && <ErrorNotice message={error.message} onRetry={error.retry ? () => confirm() : undefined} />}

        <div className="dialog-actions">
          {busy ? (
            <PlanningIndicator text={willReplan ? 'Re-planning…' : forward ? 'Moving ahead…' : 'Moving to tomorrow…'} />
          ) : (
            <>
              <button type="button" className="btn-text" onClick={onClose}>
                Not yet
              </button>
              <button type="submit" className="btn">
                {willReplan
                  ? 'Confirm and re-plan'
                  : forward
                    ? `Confirm and go to ${formatDay(toDay)}`
                    : 'Confirm and start tomorrow'}
              </button>
            </>
          )}
        </div>
      </form>
    </div>
  )
}
