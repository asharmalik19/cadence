// Mirrors the backend shapes in backend/app/models.py (API section). Dates are YYYY-MM-DD strings.

export type TaskStatus = 'planned' | 'done' | 'missed'
export type TaskKind = 'concrete' | 'explore'

export interface Task {
  id: number
  goal_id: number
  day: string
  kind: TaskKind
  milestone: string
  title: string
  done_criterion: string
  minutes: number
  why: string
  status: TaskStatus
}

export interface TodayTask extends Task {
  goal_text: string
}

export interface Workstream {
  name: string
  minutes_per_week: number
  purpose: string
}

export interface Milestone {
  name: string
  target_day: string
  reached_when: string
}

export interface Clarification {
  question: string
  answer: string
}

export interface Update {
  id: number
  goal_id: number
  day: string
  text: string
}

export interface Goal {
  id: number
  text: string
  deadline: string
  feasibility: string | null
  smart_goal: string
  clarifications: Clarification[]
  breakdown: Workstream[]
  milestones: Milestone[]
  last_change: string | null
  created_on: string
  updates: Update[]
  tasks: Task[]
}

export interface Settings {
  daily_hours: number
  current_day: string
}

export interface AppState {
  settings: Settings | null
  goals: Goal[]
  today: TodayTask[]
  max_goals: number
}

export interface DayUpdate {
  goal_id: number
  text: string
}

export interface GoalDraft {
  text: string
  deadline: string
}

export type AddGoalResult =
  | { status: 'impossible'; message: string; smart_goal: string; assumptions: string[] }
  | { status: 'added'; goal_id: number; state: AppState }
