import { useState } from 'react'
import { formatMinutes } from '../dates'
import type { Task } from '../types'

interface Props {
  task: Task
  /** Shown where tasks from several goals are mixed. Left out when there's only one goal. */
  goalLabel?: string
  /** Given only where ticking is allowed (today's tasks). */
  onToggle?: (done: boolean) => Promise<void>
  /** Title and time only, for the review, where the question is just "did you do it?". */
  compact?: boolean
}

export function TaskCard({ task, goalLabel, onToggle, compact }: Props) {
  const [busy, setBusy] = useState(false)
  const [open, setOpen] = useState(false)
  const done = task.status === 'done'

  const toggle = async () => {
    if (!onToggle || busy) return
    setBusy(true)
    try {
      await onToggle(!done)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`task ${task.status}${onToggle ? ' tickable' : ''}${compact ? ' compact' : ''}`}>
      {onToggle && (
        <button
          type="button"
          className={`tick${done ? ' on' : ''}`}
          role="checkbox"
          aria-checked={done}
          aria-label={done ? `Untick: ${task.title}` : `Tick as done: ${task.title}`}
          onClick={toggle}
          disabled={busy}
        >
          {done && <CheckIcon />}
        </button>
      )}
      <div className="task-main">
        {goalLabel && <div className="task-goal">{goalLabel}</div>}
        {/* Where there's no tick box, say plainly what happened to the task. */}
        {!onToggle && task.status === 'done' && (
          <div className="task-status done">
            <CheckIcon /> Done
          </div>
        )}
        {!onToggle && task.status === 'missed' && <div className="task-status missed">Not done · re-planned</div>}
        <div className="task-head">
          <span className="task-title">{task.title}</span>
          <span className="task-minutes">{formatMinutes(task.minutes)}</span>
        </div>
        {!compact && (
          <div className="task-body">
            <p>
              <span>{task.kind === 'explore' ? 'Progress when: ' : 'Done when: '}</span>
              {task.done_criterion}
            </p>
            {/* The why and the milestone are there when you want them, not in the way. */}
            {open && (
              <>
                <p>
                  <span>Why: </span>
                  {task.why}
                </p>
                {task.milestone && <p className="task-milestone">Toward: {task.milestone}</p>}
              </>
            )}
            <button type="button" className="btn-text task-more" onClick={() => setOpen(!open)} aria-expanded={open}>
              {open ? 'Hide details' : 'Details'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
  )
}
