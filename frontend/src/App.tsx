import { useCallback, useEffect, useState } from 'react'
import { addUpdate, deleteGoal, getState, nextDay, setDailyHours, toggleTask } from './api'
import { AddGoalDialog } from './components/AddGoalDialog'
import { DailyHoursStep } from './components/DailyHoursStep'
import { ErrorNotice } from './components/ErrorNotice'
import { GoalView } from './components/GoalView'
import { PlanningIndicator } from './components/PlanningIndicator'
import { ReviewDialog } from './components/ReviewDialog'
import { Sidebar } from './components/Sidebar'
import { TodayView } from './components/TodayView'
import { toDay } from './dates'
import type { AppState } from './types'

/** Holds the app state from the backend and picks which screen to show. Decides nothing itself. */
export default function App() {
  const [state, setState] = useState<AppState | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  // null = Today
  const [activeGoalId, setActiveGoalId] = useState<number | null>(null)
  const [adding, setAdding] = useState(false)
  // 'day' = Next day's review; 'forward' = Fast forward over several days
  const [reviewing, setReviewing] = useState<'day' | 'forward' | null>(null)

  const load = useCallback(async () => {
    setLoadError(null)
    try {
      setState(await getState())
    } catch (err) {
      setLoadError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  // The calendar date, for the Fast forward banner. Refreshed on focus so a tab left open overnight notices.
  const [realToday, setRealToday] = useState(() => toDay(new Date()))
  useEffect(() => {
    const refresh = () => setRealToday(toDay(new Date()))
    window.addEventListener('focus', refresh)
    return () => window.removeEventListener('focus', refresh)
  }, [])

  if (loadError) {
    return (
      <div className="centered">
        <ErrorNotice message={loadError} onRetry={load} />
      </div>
    )
  }
  if (!state) {
    return (
      <div className="centered">
        <PlanningIndicator text="Opening…" />
      </div>
    )
  }
  if (!state.settings) {
    return <DailyHoursStep onSubmit={async (hours) => setState(await setDailyHours(hours))} />
  }

  const { settings, goals } = state
  const activeGoal = goals.find((g) => g.id === activeGoalId)
  const toggle = async (taskId: number, done: boolean) => setState(await toggleTask(taskId, done))

  return (
    <div className="shell">
      <Sidebar
        goals={goals}
        maxGoals={state.max_goals}
        activeGoalId={activeGoal?.id ?? null}
        dailyHours={settings.daily_hours}
        currentDay={settings.current_day}
        todayLeft={state.today.filter((t) => t.status !== 'done').length}
        onSelectToday={() => setActiveGoalId(null)}
        onSelectGoal={setActiveGoalId}
        onAddGoal={() => setAdding(true)}
        onDeleteGoal={async (id) => {
          setState(await deleteGoal(id))
          if (id === activeGoalId) setActiveGoalId(null)
        }}
      />
      <main className="main">
        {activeGoal ? (
          <GoalView
            goal={activeGoal}
            currentDay={settings.current_day}
            onAddUpdate={async (text) => setState(await addUpdate(activeGoal.id, text))}
          />
        ) : goals.length > 0 ? (
          <TodayView
            tasks={state.today}
            currentDay={settings.current_day}
            realToday={realToday}
            onToggle={toggle}
            onNextDay={() => setReviewing('day')}
            onFastForward={() => setReviewing('forward')}
          />
        ) : (
          <div className="welcome" style={{ marginTop: 64 }}>
            <div className="label">No goals yet</div>
            <h1>Start with one goal you care about.</h1>
            <p className="muted">
              Give it a deadline. The planner asks a few questions, then builds the system: the kinds of work it
              needs and what to do each day.
            </p>
            <div>
              <button className="btn" onClick={() => setAdding(true)}>
                Add your first goal
              </button>
            </div>
          </div>
        )}
      </main>
      {reviewing && (
        <ReviewDialog
          tasks={state.today}
          goals={goals}
          currentDay={settings.current_day}
          realToday={reviewing === 'forward' ? realToday : undefined}
          onToggle={toggle}
          onConfirm={async ({ updates, toDay, doneTaskIds }) => {
            setState(await nextDay(updates, toDay, doneTaskIds))
            setReviewing(null)
          }}
          onClose={() => setReviewing(null)}
        />
      )}
      {adding && (
        <AddGoalDialog
          currentDay={settings.current_day}
          onClose={() => setAdding(false)}
          onAdded={(goalId, next) => {
            setState(next)
            setActiveGoalId(goalId)
            setAdding(false)
          }}
        />
      )}
    </div>
  )
}
