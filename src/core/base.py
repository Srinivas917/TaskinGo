from langgraph.graph import MessagesState
from typing import TypedDict, List, Dict, Optional
from datetime import datetime

class GoalState(MessagesState):
    next_node: str
    goal_id: int
    deadline: Optional[datetime]

    goal_data: Dict
    tasks_data: List[Dict]

    relevant_tasks: List[Dict]
    completed_tasks: int
    pending_tasks: int
    irrelevant_tasks: List[Dict]
    irrelevant_task_explanations: List[Dict]
    suggested_tasks: List[Dict]

    completion_score: int
    risk_score: int
    days_remaining: Optional[int]

    execution_strategy: str
    strategy_plan: Dict
    insights: Dict
    observations: Dict
    final_output: Dict

