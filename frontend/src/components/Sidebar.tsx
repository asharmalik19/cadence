import { useState } from 'react'
import type { ApiError } from '../api'
import { formatDay } from '../dates'
import type { Goal } from '../types'
import { ErrorNotice } from './ErrorNotice'

interface Props {
  goals: Goal[]
  maxGoals: number
  activeGoalId: number | null
  dailyHours: number
  onSelectGoal: (id: number) => void
  onAddGoal: () => void
  onDeleteGoal: (id: number) => Promise<void>
}

export function Sidebar({ goals, maxGoals, activeGoalId, dailyHours, onSelectGoal, onAddGoal, onDeleteGoal }: Props) {
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const atCap = goals.length >= maxGoals

  const remove = async (id: number) => {
    setDeleting(true)
    setError(null)
    try {
      await onDeleteGoal(id)
      setConfirmingId(null)
    } catch (err) {
      setError((err as ApiError).message)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        Sys<span>Planner</span>
      </div>
      <nav className="nav">
        <div className="label">
          <span>Active goals</span>
          <span>
            {goals.length}/{maxGoals}
          </span>
        </div>
        {goals.map((g) =>
          g.id === confirmingId ? (
            <div key={g.id} className="nav-row confirming">
              <p>Delete “{g.text}” and its plan? This can’t be undone.</p>
              <div className="nav-confirm">
                <button className="btn-text" onClick={() => setConfirmingId(null)} disabled={deleting}>
                  Keep
                </button>
                <button className="btn-text gold" onClick={() => remove(g.id)} disabled={deleting}>
                  {deleting ? 'Deleting…' : 'Delete'}
                </button>
              </div>
            </div>
          ) : (
            <div key={g.id} className={`nav-row${g.id === activeGoalId ? ' active' : ''}`}>
              <button className="nav-item" onClick={() => onSelectGoal(g.id)}>
                {g.text}
                <small>by {formatDay(g.deadline, { day: 'numeric', month: 'short', year: 'numeric' })}</small>
              </button>
              <button
                className="nav-delete"
                aria-label={`Delete goal: ${g.text}`}
                title="Delete goal"
                onClick={() => {
                  setError(null)
                  setConfirmingId(g.id)
                }}
              >
                <TrashIcon />
              </button>
            </div>
          ),
        )}
        {error && <ErrorNotice message={error} />}
      </nav>
      <div className="sidebar-add">
        <button className="btn btn-quiet" onClick={onAddGoal} disabled={atCap}>
          Add goal
        </button>
        {atCap && <p className="muted" style={{ fontSize: 13 }}>{maxGoals} goals is the limit. Focus on these first.</p>}
      </div>
      <div className="sidebar-foot muted">Planning {dailyHours} h a day</div>
    </aside>
  )
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
    </svg>
  )
}
