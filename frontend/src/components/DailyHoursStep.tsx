import { useState, type FormEvent } from 'react'
import { ErrorNotice } from './ErrorNotice'

interface Props {
  onSubmit: (hours: number) => Promise<void>
}

/** First open: the one time budget all goals share. */
export function DailyHoursStep({ onSubmit }: Props) {
  const [hours, setHours] = useState('8')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const value = Number(hours)
  const valid = Number.isInteger(value) && value >= 1 && value <= 16

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!valid) return
    setSaving(true)
    setError(null)
    try {
      await onSubmit(value)
    } catch (err) {
      setError((err as Error).message)
      setSaving(false)
    }
  }

  return (
    <div className="centered">
      <form className="welcome" onSubmit={submit}>
        <div className="label">Before your first goal</div>
        <h1>How many hours a day do you want to plan for?</h1>
        <p className="muted">
          Count every day, weekends included. Plan for less than you really have: the gap is your buffer, and a tight
          limit makes the plan focus on what matters. One day each week stays free for everything else.
        </p>
        <div className="field">
          <span className="label">Hours per day</span>
          <div className="hours-input">
            <input
              type="number"
              min={1}
              max={16}
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              aria-label="Hours per day"
              autoFocus
            />
            <span className="muted">hours</span>
          </div>
        </div>
        <div>
          <button className="btn" type="submit" disabled={!valid || saving}>
            Continue
          </button>
        </div>
        {error && <ErrorNotice message={error} />}
      </form>
    </div>
  )
}
