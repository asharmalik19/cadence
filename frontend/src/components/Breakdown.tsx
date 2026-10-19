import { formatMinutes } from '../dates'
import type { Workstream } from '../types'

/** The kinds of ongoing work the goal needs, and how much time each gets. */
export function Breakdown({ workstreams }: { workstreams: Workstream[] }) {
  const total = workstreams.reduce((sum, w) => sum + w.minutes_per_week, 0) || 1
  return (
    <div className="breakdown">
      {workstreams.map((w) => (
        <div key={w.name} className="card workstream">
          <div className="workstream-hours">{formatMinutes(w.minutes_per_week)} / week</div>
          <h3>{w.name}</h3>
          <div className="bar">
            <div style={{ width: `${(100 * w.minutes_per_week) / total}%` }} />
          </div>
          <p className="muted" style={{ fontSize: 14 }}>
            {w.purpose}
          </p>
        </div>
      ))}
    </div>
  )
}
