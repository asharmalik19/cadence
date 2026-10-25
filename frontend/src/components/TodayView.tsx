import { useState } from 'react'
import type { ApiError } from '../api'
import { formatLong, formatMinutes } from '../dates'
import type { TodayTask } from '../types'
import { ErrorNotice } from './ErrorNotice'
import { FastForwardBanner } from './FastForwardBanner'
import { TaskCard } from './TaskCard'

interface Props {
  tasks: TodayTask[]
  currentDay: string
  realToday: string
  onToggle: (taskId: number, done: boolean) => Promise<void>
  onNextDay: () => void
  onFastForward: () => void
}

/** Today's tasks across all goals. You only ever tick wins; Next day handles the rest. */
export function TodayView({ tasks, currentDay, realToday, onToggle, onNextDay, onFastForward }: Props) {
  const [error, setError] = useState<string | null>(null)
  const done = tasks.filter((t) => t.status === 'done')
  const minutesLeft = tasks.filter((t) => t.status !== 'done').reduce((sum, t) => sum + t.minutes, 0)

  const toggle = async (taskId: number, isDone: boolean) => {
    setError(null)
    try {
      await onToggle(taskId, isDone)
    } catch (err) {
      setError((err as ApiError).message)
    }
  }

  return (
    <div className="today-view">
      <FastForwardBanner currentDay={currentDay} realToday={realToday} onFastForward={onFastForward} />
      <header className="today-head">
        <div>
          <div className="label">Today</div>
          <h1>{formatLong(currentDay)}</h1>
          <p className="muted" style={{ marginTop: 8 }}>
            {tasks.length === 0
              ? 'Nothing planned for today. A free day.'
              : done.length === tasks.length
                ? 'Nothing left for today.'
                : `${done.length} of ${tasks.length} done · ${formatMinutes(minutesLeft)} left`}
          </p>
        </div>
        <button className="btn" onClick={onNextDay}>
          Next day
        </button>
      </header>

      {error && <ErrorNotice message={error} />}

      <div className="today-tasks">
        {tasks.map((t) => (
          <TaskCard key={t.id} task={t} goalLabel={t.goal_text} onToggle={(isDone) => toggle(t.id, isDone)} />
        ))}
      </div>
    </div>
  )
}
