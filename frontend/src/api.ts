// One typed function per backend route.
import type { AddGoalResult, AppState, Clarification, DayUpdate, GoalDraft } from './types'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function call<T>(path: string, body?: unknown, method = body === undefined ? 'GET' : 'POST'): Promise<T> {
  let res: Response
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, "Can't reach the app's backend. Is it running?")
  }
  if (!res.ok) {
    const detail = await res.json().then((d) => d.detail, () => null)
    throw new ApiError(res.status, typeof detail === 'string' ? detail : 'Something went wrong. Nothing was changed.')
  }
  return res.json() as Promise<T>
}

export const getState = () => call<AppState>('/state')

export const setDailyHours = (daily_hours: number) => call<AppState>('/settings', { daily_hours })

export const clarifyGoal = (draft: GoalDraft) => call<{ questions: string[] }>('/goals/clarify', draft)

export const addGoal = (draft: GoalDraft, clarifications: Clarification[]) =>
  call<AddGoalResult>('/goals', { ...draft, clarifications })

export const deleteGoal = (goalId: number) => call<AppState>(`/goals/${goalId}`, undefined, 'DELETE')

export const addUpdate = (goalId: number, text: string) => call<AppState>(`/goals/${goalId}/updates`, { text })

export const toggleTask = (taskId: number, done: boolean) => call<AppState>(`/tasks/${taskId}/toggle`, { done })

export const nextDay = (updates: DayUpdate[]) => call<AppState>('/day/next', { updates })
