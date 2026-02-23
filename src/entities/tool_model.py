from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal


class TaskPlannerResponse(BaseModel):
    goal_completed: bool = Field(
        description="True if goal is fully achieved with current tasks."
    )
    tasks: List[str] = Field(
        description="List of new or missing tasks required to achieve the goal. Empty if goal_completed is true."
    )

class TaskClassification(BaseModel):
    relevant_tasks: List[Dict] = Field(
        description="List of tasks that are directly aligned with the goal."
    )
    irrelevant_tasks: List[Dict] = Field(
        description="List of tasks that are not aligned with the goal, along with reasoning."
    )

class RelevantTask(BaseModel):
    title: str = Field(
        description="Task title that is directly aligned with the goal."
    )
    description: str = Field(
        description="Task description that is directly aligned with the goal."
    )
    is_completed: bool = Field(
        description="Current execution status of the task."
    )
class IrrelevantTask(BaseModel):
    title: str = Field(
        description="Task title that is not aligned with the goal."
    )
    description: str = Field(
        description="Task description that is not aligned with the goal."
    )
    is_completed: bool = Field(
        description="Current execution status of the task."
    )
    reason: str = Field(
        description="Clear explanation why this task is irrelevant to the goal."
    )
class TaskRelevanceResponse(BaseModel):
    relevant_tasks: List[RelevantTask] = Field(
        description="List of tasks that are directly aligned with the goal."
    )
    irrelevant_tasks: List[IrrelevantTask] = Field(
        description="List of tasks that are not aligned with the goal, along with reasoning."
    )

class TaskExplanation(BaseModel):
    title: str = Field(
        description="Task that was identified as irrelevant."
    )
    description: str = Field(
        description="Detailed explanation for why the task does not support the goal."
    )

class TaskSuggestionModel(BaseModel):
    suggested_tasks: List[str] = Field(
        description="List of newly suggested tasks that align with the goal."
    )
    explanation: List[TaskExplanation] = Field(
        description="Task-wise explanation for why each existing task was irrelevant."
    )
class SuggestedTask(BaseModel):
    title: str = Field(
        description="Task title that is directly aligned with the goal."
    )
    description: str | None = Field(
        description="Task description that is directly aligned with the goal."
    )
    is_completed: bool = Field(
        description="Current execution status of the task."
    )

class RelevanceRecoveryResponse(BaseModel):
    explanation: List[TaskExplanation] = Field(
        description="Detailed explanation of why each existing task is irrelevant."
    )
    suggested_tasks: List[SuggestedTask] = Field(
        description="List of recommended new tasks aligned with the goal."
    )

class StrategyResponse(BaseModel):
    execution_strategy: str = Field(
        description="Structured execution strategy tailored to the goal, completion score, and risk level."
    )

class RecommandedStrategyResponse(BaseModel):
    strategy: Literal[
        "critical_strategy",
        "balanced_strategy",
        "optimization_strategy"
    ] = Field(
        description="Selected execution strategy."
    )

class InsightDetails(BaseModel):
    appreciation: str = Field(
        description="Positive reinforcement based on user's progress."
    )
    improvement_tip: List[str] = Field(
        description="Actionable suggestion to improve performance."
    )
    focus_area: str = Field(
        description="Primary area where the user should focus next."
    )
    task_suggestions: List[str] = Field(
        description="List of recommended new tasks aligned with the goal."
    )
class InsightsResponse(BaseModel):
    completion_score: int = Field(
        description="Percentage of relevant tasks completed."
    )
    risk_score: int = Field(
        description="Calculated risk score based on progress and deadline."
    )
    days_remaining: Optional[int] = Field(
        description="Number of days remaining until deadline. Null if no deadline is provided."
    )
    insights: InsightDetails = Field(
        description="Structured performance insights derived from analytics."
    )
