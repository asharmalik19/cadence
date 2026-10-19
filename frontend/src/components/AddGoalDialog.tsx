import { useState, type FormEvent } from 'react'
import { addGoal, ApiError, clarifyGoal } from '../api'
import { addDays } from '../dates'
import type { AppState, Clarification } from '../types'
import { ErrorNotice } from './ErrorNotice'
import { PlanningIndicator } from './PlanningIndicator'

interface Props {
  currentDay: string
  onClose: () => void
  onAdded: (goalId: number, state: AppState) => void
}

type Step = 'goal' | 'deadline' | 'questions' | 'impossible'
type Impossible = { message: string; smart_goal: string; assumptions: string[] }

/**
 * Adding a goal, in the PRD's order: the goal in plain words → "By when?" → the AI's clarifying questions
 * (asked knowing the deadline) → SMART goal and verdict. An impossible verdict keeps the deadline and
 * answers editable for another try.
 */
export function AddGoalDialog({ currentDay, onClose, onAdded }: Props) {
  const [step, setStep] = useState<Step>('goal')
  const [text, setText] = useState('')
  const [deadline, setDeadline] = useState('')
  const [answers, setAnswers] = useState<Clarification[]>([])
  const [impossible, setImpossible] = useState<Impossible | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<{ message: string; retry?: () => void } | null>(null)

  const draft = { text: text.trim(), deadline }
  const hasGoal = draft.text.length > 0
  const canAsk = hasGoal && deadline > currentDay

  const run = async (label: string, action: () => Promise<void>) => {
    setBusy(label)
    setError(null)
    try {
      await action()
    } catch (err) {
      const e = err as ApiError
      // 409 is a plain refusal (nothing to retry); anything else is a planning failure you can retry.
      setError({ message: e.message, retry: e.status === 409 ? undefined : () => run(label, action) })
    } finally {
      setBusy(null)
    }
  }

  const askQuestions = (e: FormEvent) => {
    e.preventDefault()
    if (!canAsk) return
    run('Reading your goal…', async () => {
      const { questions } = await clarifyGoal(draft)
      const previous = new Map(answers.map((a) => [a.question, a.answer]))
      const next = questions.map((q) => ({ question: q, answer: previous.get(q) ?? '' }))
      setAnswers(next)
      if (next.length === 0) await plan(next)
      else setStep('questions')
    })
  }

  const plan = async (clarifications: Clarification[]) => {
    const result = await addGoal(draft, clarifications)
    if (result.status === 'added') {
      onAdded(result.goal_id, result.state)
    } else {
      setImpossible(result)
      setStep('impossible')
    }
  }

  const submitAnswers = (e: FormEvent) => {
    e.preventDefault()
    run('Planning your system…', () => plan(answers))
  }

  const setAnswer = (i: number, answer: string) =>
    setAnswers((prev) => prev.map((a, j) => (j === i ? { ...a, answer } : a)))

  const answerFields = answers.map((a, i) => (
    <label key={a.question} className="question">
      <p>{a.question}</p>
      <div className="field">
        <textarea value={a.answer} onChange={(e) => setAnswer(i, e.target.value)} rows={2} />
      </div>
    </label>
  ))

  return (
    <div className="overlay">
      <div className="card dialog" role="dialog" aria-modal="true">
        <div>
          <div className="label">Add goal</div>
          <h2 style={{ marginTop: 6 }}>
            {
              {
                goal: 'What do you want to achieve?',
                deadline: 'By when?',
                questions: 'A few more questions',
                impossible: 'Not possible by this deadline',
              }[step]
            }
          </h2>
        </div>

        {step === 'goal' && (
          <form
            className="section"
            onSubmit={(e) => {
              e.preventDefault()
              if (hasGoal) setStep('deadline')
            }}
          >
            <label className="field">
              <span className="label">Your goal, in plain words</span>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="e.g. Get a scholarship to study abroad for a master's"
                autoFocus
              />
            </label>
            <p className="muted" style={{ fontSize: 14 }}>
              A plain sentence is enough. The planner asks what it needs before it plans.
            </p>
            <div className="dialog-actions">
              <button type="button" className="btn-text" onClick={onClose}>
                Cancel
              </button>
              <button className="btn" type="submit" disabled={!hasGoal}>
                Continue
              </button>
            </div>
          </form>
        )}

        {step === 'deadline' && (
          <form className="section" onSubmit={askQuestions}>
            <p className="muted">
              The date you want <em>{draft.text}</em> done by. The planner uses it to decide what to ask you next.
            </p>
            <label className="field">
              <span className="label">Deadline</span>
              <input
                type="date"
                value={deadline}
                min={addDays(currentDay, 1)}
                onChange={(e) => setDeadline(e.target.value)}
                autoFocus
              />
            </label>
            <div className="dialog-actions">
              <button type="button" className="btn-text" onClick={() => setStep('goal')} disabled={!!busy}>
                Back
              </button>
              <button className="btn" type="submit" disabled={!canAsk || !!busy}>
                Continue
              </button>
            </div>
          </form>
        )}

        {step === 'questions' && (
          <form className="section" onSubmit={submitAnswers}>
            <p className="muted">
              So the plan fits <em>your</em> goal instead of a guess. Answer what you can; “not decided yet” is a fine
              answer, and the plan will include deciding it.
            </p>
            {answerFields}
            <div className="dialog-actions">
              <button type="button" className="btn-text" onClick={() => setStep('deadline')} disabled={!!busy}>
                Back
              </button>
              <button className="btn" type="submit" disabled={!!busy}>
                Build my system
              </button>
            </div>
          </form>
        )}

        {step === 'impossible' && impossible && (
          <form className="section" onSubmit={submitAnswers}>
            <div className="verdict-box">
              <p>{impossible.message}</p>
              {impossible.assumptions.length > 0 && (
                <div>
                  <div className="label">What the planner assumed</div>
                  <ul style={{ margin: '6px 0 0', paddingLeft: 20 }}>
                    {impossible.assumptions.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <p className="muted">Change the deadline, or correct your answers if it misunderstood, and try again.</p>
            <label className="field">
              <span className="label">Deadline</span>
              <input type="date" value={deadline} min={addDays(currentDay, 1)} onChange={(e) => setDeadline(e.target.value)} />
            </label>
            {answerFields}
            <div className="dialog-actions">
              <button type="button" className="btn-text" onClick={onClose} disabled={!!busy}>
                Cancel
              </button>
              <button className="btn" type="submit" disabled={!canAsk || !!busy}>
                Try again
              </button>
            </div>
          </form>
        )}

        {busy && <PlanningIndicator text={busy} />}
        {error && <ErrorNotice message={error.message} onRetry={error.retry} />}
      </div>
    </div>
  )
}
