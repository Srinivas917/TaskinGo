from pydantic import BaseModel, Field
from typing import List


class TaskPlannerResponse(BaseModel):
    goal_completed: bool = Field(
        description="True if goal is fully achieved with current tasks."
    )
    tasks: List[str] = Field(
        description="List of new or missing tasks required to achieve the goal. Empty if goal_completed is true."
    )
