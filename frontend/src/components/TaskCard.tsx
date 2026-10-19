import { formatMinutes } from '../dates'
import type { Task } from '../types'

export function TaskCard({ task }: { task: Task }) {
  return (
    <div className={`task ${task.status}`}>
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
  )
}
