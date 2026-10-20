import { useState } from 'react'
import { formatMinutes } from '../dates'
import type { Task } from '../types'

interface Props {
  task: Task
  /** Shown on Today, where tasks from all goals are mixed. */
  goalLabel?: string
  /** Given only where ticking is allowed (today's tasks). */
  onToggle?: (done: boolean) => Promise<void>
}

export function TaskCard({ task, goalLabel, onToggle }: Props) {
  const [busy, setBusy] = useState(false)
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
    <div className={`task ${task.status}${onToggle ? ' tickable' : ''}`}>
      {onToggle && (
        <button
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
          <span className="task-title">
            {task.kind === 'explore' && <span className="kind">Explore</span>}
            {task.title}
          </span>
          <span className="task-minutes">{formatMinutes(task.minutes)}</span>
        </div>
        <div className="task-body">
          <p>
            <span>{task.kind === 'explore' ? 'Progress when: ' : 'Done when: '}</span>
            {task.done_criterion}
          </p>
          <p>
            <span>Why: </span>
            {task.why}
          </p>
          {task.milestone && <p className="task-milestone">Toward: {task.milestone}</p>}
        </div>
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
