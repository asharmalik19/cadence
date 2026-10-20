import { formatLong } from '../dates'
import type { Goal } from '../types'
import { Breakdown } from './Breakdown'
import { DayPlan } from './DayPlan'
import { LastChangeNote } from './LastChangeNote'
import { Milestones } from './Milestones'
import { UpdateBox } from './UpdateBox'

interface Props {
  goal: Goal
  currentDay: string
  onAddUpdate: (text: string) => Promise<void>
}

/** One goal's whole system: SMART goal, last change, what happened, milestones, breakdown, day-by-day plan. */
export function GoalView({ goal, currentDay, onAddUpdate }: Props) {
  return (
    <div className="goal-view">
      <header className="goal-head">
        <div className="label">Goal</div>
        <h1>{goal.text}</h1>
        <div className="goal-meta">
          <span>
            <span className="muted">Deadline </span>
            <span className="gold">{formatLong(goal.deadline)}</span>
          </span>
          {goal.feasibility && <span className="chip">{goal.feasibility}</span>}
        </div>
      </header>

      <section className="card section">
        <div className="label">SMART goal</div>
        <p className="smart">{goal.smart_goal}</p>
        {goal.clarifications.length > 0 && (
          <details>
            <summary>What you told the planner</summary>
            <div className="answers">
              {goal.clarifications.map((c) => (
                <div key={c.question}>
                  <p>{c.question}</p>
                  <p>{c.answer || '(no answer)'}</p>
                </div>
              ))}
            </div>
          </details>
        )}
      </section>

      <LastChangeNote note={goal.last_change} />

      <section className="section">
        <h2>What happened</h2>
        <UpdateBox key={goal.id} updates={goal.updates} onSubmit={onAddUpdate} />
      </section>

      <section className="section">
        <h2>Milestones</h2>
        <Milestones milestones={goal.milestones} currentDay={currentDay} />
      </section>

      <section className="section">
        <h2>The system</h2>
        <Breakdown workstreams={goal.breakdown} />
      </section>

      <section className="section">
        <h2>Day by day</h2>
        <DayPlan tasks={goal.tasks} currentDay={currentDay} />
        {goal.tasks.length > 0 && goal.tasks[goal.tasks.length - 1].day < goal.deadline && (
          <p className="muted day-horizon">
            Planned in detail for the next two weeks. After that, the milestones guide the plan, and the daily steps
            are filled in as you make decisions and share what happened.
          </p>
        )}
      </section>
    </div>
  )
}
