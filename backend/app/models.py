"""Pydantic shapes: what the AI must reply with, and what we send it."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# AI reply shapes. Their JSON schema is sent to Gemini as the required format.
# ---------------------------------------------------------------------------


class TaskPlan(BaseModel):
    day: date = Field(description="Day the task is done, YYYY-MM-DD.")
    title: str = Field(description="What to do, short and concrete.")
    done_criterion: str = Field(description="How the user knows the task is done.")
    minutes: int = Field(description="Time estimate in minutes.")
    why: str = Field(description="One sentence on how this task moves the goal forward.")


class Workstream(BaseModel):
    name: str = Field(description="A kind of ongoing work the goal needs.")
    minutes_per_week: int = Field(description="Time this workstream gets per week.")
    purpose: str = Field(description="Why the goal needs this workstream.")


class GoalPlan(BaseModel):
    goal_id: int = Field(description="Id of the goal. Use 0 for the goal being added.")
    breakdown: list[Workstream]
    tasks: list[TaskPlan] = Field(description="Every task from the plan's start day to completion.")
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
    goals: list[GoalPlan] = Field(description="Only goals that had missed tasks.")


# ---------------------------------------------------------------------------
# What we send the AI: the full picture.
# ---------------------------------------------------------------------------


class TaskContext(BaseModel):
    id: int
    day: date
    title: str
    minutes: int
    status: Literal["planned", "done", "missed"]


class Clarification(BaseModel):
    question: str
    answer: str


class GoalContext(BaseModel):
    id: int
    text: str
    smart_goal: str
    clarifications: list[Clarification]
    deadline: date
    breakdown: list[Workstream]
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
    replan_goal_ids: list[int] = Field(default_factory=list, description="Goals with misses to re-plan.")
