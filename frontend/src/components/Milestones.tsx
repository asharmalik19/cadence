import { formatDay } from '../dates'
import type { Milestone } from '../types'

interface Props {
  milestones: Milestone[]
  currentDay: string
}

/** The backbone of the plan: dated checkpoints from now to the goal. */
export function Milestones({ milestones, currentDay }: Props) {
  if (milestones.length === 0) return <p className="muted">No milestones yet.</p>
  return (
    <ol className="milestones">
      {milestones.map((m) => (
        <li key={m.name} className={m.target_day < currentDay ? 'past' : undefined}>
          <span className="milestone-date">{formatDay(m.target_day, { day: 'numeric', month: 'short' })}</span>
          <div>
            <p className="milestone-name">{m.name}</p>
            <p className="muted" style={{ fontSize: 13.5 }}>
              {m.reached_when}
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}
