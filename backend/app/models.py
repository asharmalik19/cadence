"""Pydantic shapes: what the AI must reply with, and what we send it."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# AI reply shapes. Their JSON schema is sent to Gemini as the required format.
# ---------------------------------------------------------------------------


TaskKind = Literal["concrete", "explore"]

DETAIL_DAYS = 14  # daily tasks are planned this far ahead; beyond it, only milestones


class TaskPlan(BaseModel):
    day: date = Field(description="Day the task is done, YYYY-MM-DD.")
    kind: TaskKind = Field(
        description='"concrete": a clear output in a predictable time. "explore": one session on an open '
        "question (research, deciding, reflecting) that spans several days."
    )
    title: str = Field(description="What to do, short and concrete.")
    done_criterion: str = Field(
        description="concrete: the finished output. explore: the progress this session leaves behind "
        "(notes, a comparison, a conversation), never that the question is settled."
    )
    minutes: int = Field(description="Time estimate in minutes.")
    why: str = Field(description="One sentence on how this task moves the goal forward.")
    milestone: str = Field(description="Name of the milestone this task works toward, exactly as in milestones.")


class Milestone(BaseModel):
    name: str = Field(description='A checkpoint on the way to the goal, e.g. "Choose 2-3 countries".')
    target_day: date = Field(description="Day it should be reached by, YYYY-MM-DD.")
    reached_when: str = Field(description="What is true once it's reached.")


class Workstream(BaseModel):
    name: str = Field(description="A kind of ongoing work the goal needs.")
    minutes_per_week: int = Field(description="Time this workstream gets per week.")
    purpose: str = Field(description="Why the goal needs this workstream.")


class GoalPlan(BaseModel):
    goal_id: int = Field(description="Id of the goal. Use 0 for the goal being added.")
    smart_goal: str = Field(
        default="",
        description="For an existing goal: its SMART goal, rewritten only if an update changed the goal itself, "
        "otherwise repeated unchanged. Empty for the goal being added."
    )
    breakdown: list[Workstream]
    milestones: list[Milestone] = Field(description="Every milestone from now to the goal, in date order.")
    tasks: list[TaskPlan] = Field(
        description=f"Daily tasks for the next {DETAIL_DAYS} days only (or until completion if sooner)."
    )
    change_note: str = Field(
        description="For a changed existing goal: what changed and whether the deadline is still met. "
        "Empty for the goal being added."
    )


class Clarify(BaseModel):
    questions: list[str] = Field(
        description="Only what you must know to plan this goal well. Empty if the goal is already specific."
    )


class NewGoalPlan(BaseModel):
    smart_goal: str = Field(
        description="The goal restated as one SMART sentence: specific, measurable, achievable, time-bound."
    )
    assumptions: list[str] = Field(description="Assumptions you still had to make, in plain words.")
    verdict: Literal["impossible", "stretch", "comfortable"]
    message: str = Field(
        description="If impossible: why the deadline is too short. Otherwise a one-line summary of the plan."
    )
    new_goal: GoalPlan | None = Field(description="The new goal's system. Null when impossible.")
    rework: list[GoalPlan] = Field(description="Only existing goals whose plans change. Empty if none.")


class Replan(BaseModel):
    goals: list[GoalPlan] = Field(description="Exactly the goals listed in replan_goal_ids.")


# ---------------------------------------------------------------------------
# What we send the AI: the full picture.
# ---------------------------------------------------------------------------


class TaskContext(BaseModel):
    id: int
    day: date
    kind: TaskKind
    milestone: str
    title: str
    minutes: int
    status: Literal["planned", "done", "missed"]


class Clarification(BaseModel):
    question: str
    answer: str


class UpdateContext(BaseModel):
    day: date = Field(description="Day the user wrote it.")
    text: str = Field(description="Something that happened or changed, in the user's words. Treat it as fact.")


class GoalContext(BaseModel):
    id: int
    text: str
    smart_goal: str
    clarifications: list[Clarification]
    deadline: date
    breakdown: list[Workstream]
    milestones: list[Milestone]
    updates: list[UpdateContext] = Field(default_factory=list, description="Oldest first.")
    tasks: list[TaskContext]


class NewGoalRequest(BaseModel):
    text: str
    deadline: date
    clarifications: list[Clarification] = Field(default_factory=list)


class PlanContext(BaseModel):
    daily_hours: int = Field(description="Hours the user plans for each day, weekends included.")
    today: date
    start_day: date = Field(description="First day the reply may plan tasks on.")
    goals: list[GoalContext] = Field(default_factory=list, description="Existing active goals.")
    new_goal: NewGoalRequest | None = None
    replan_goal_ids: list[int] = Field(default_factory=list, description="Goals to re-plan.")
    replan_reasons: dict[int, list[str]] = Field(
        default_factory=dict, description="Why each goal in replan_goal_ids is being re-planned."
    )


# ---------------------------------------------------------------------------
# API shapes: what the frontend sends and gets back. types.ts mirrors these.
# ---------------------------------------------------------------------------


class Settings(BaseModel):
    daily_hours: int
    current_day: date


class TaskOut(BaseModel):
    id: int
    goal_id: int
    day: date
    kind: TaskKind
    milestone: str
    title: str
    done_criterion: str
    minutes: int
    why: str
    status: Literal["planned", "done", "missed"]


class UpdateOut(BaseModel):
    id: int
    goal_id: int
    day: date
    text: str


class TodayTask(TaskOut):
    goal_text: str


class GoalOut(BaseModel):
    id: int
    text: str
    deadline: date
    feasibility: str | None
    smart_goal: str
    clarifications: list[Clarification]
    breakdown: list[Workstream]
    milestones: list[Milestone]
    last_change: str | None
    created_on: date
    updates: list[UpdateOut]
    tasks: list[TaskOut]


class AppState(BaseModel):
    settings: Settings | None
    goals: list[GoalOut]
    today: list[TodayTask]
    max_goals: int


class SettingsIn(BaseModel):
    daily_hours: int = Field(ge=1, le=16)


class ClarifyIn(BaseModel):
    text: str = Field(min_length=1)
    deadline: date


class ClarifyOut(BaseModel):
    questions: list[str]


class AddGoalIn(ClarifyIn):
    clarifications: list[Clarification] = Field(default_factory=list)


class AddGoalImpossible(BaseModel):
    status: Literal["impossible"] = "impossible"
    message: str
    smart_goal: str
    assumptions: list[str]


class AddGoalAdded(BaseModel):
    status: Literal["added"] = "added"
    goal_id: int
    state: AppState


class ToggleIn(BaseModel):
    done: bool


class UpdateIn(BaseModel):
    text: str = Field(min_length=1)


class DayUpdate(UpdateIn):
    goal_id: int


class NextDayIn(BaseModel):
    updates: list[DayUpdate] = Field(default_factory=list)
