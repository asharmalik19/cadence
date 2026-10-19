import { addDays, formatDay, formatMinutes, parseDay } from '../dates'
import type { Task } from '../types'
import { TaskCard } from './TaskCard'

interface Props {
  tasks: Task[]
  currentDay: string
}

/** Every day from the first task to the last: past days dimmed, today in gold, free days shown as free. */
export function DayPlan({ tasks, currentDay }: Props) {
  if (tasks.length === 0) return <p className="muted">No tasks planned.</p>
  const byDay = new Map<string, Task[]>()
  for (const t of tasks) byDay.set(t.day, [...(byDay.get(t.day) ?? []), t])
  const days: string[] = []
  for (let d = tasks[0].day; d <= tasks[tasks.length - 1].day; d = addDays(d, 1)) days.push(d)

  return (
    <div className="days">
      {days.map((day) => {
        const dayTasks = byDay.get(day) ?? []
        const minutes = dayTasks.reduce((sum, t) => sum + t.minutes, 0)
        const when = day < currentDay ? ' past' : day === currentDay ? ' today' : ''
        return (
          <div key={day}>
            {parseDay(day).getDay() === 1 && day !== days[0] && (
              <div className="label week-label">Week of {formatDay(day, { day: 'numeric', month: 'short' })}</div>
            )}
            <div className={`day-row${when}`}>
              <div className="day-date">
                <strong>{formatDay(day)}</strong>
                {day === currentDay ? 'Today' : dayTasks.length > 0 ? formatMinutes(minutes) : ''}
              </div>
              <div className="day-tasks">
                {dayTasks.length === 0 ? (
                  <div className="day-free">Free day: nothing planned for this goal</div>
                ) : (
                  dayTasks.map((t) => <TaskCard key={t.id} task={t} />)
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
