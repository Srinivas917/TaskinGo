from src.core.base import GoalState
from datetime import datetime, timezone
from src.utils.logging_utils import get_logger
from src.utils.goal_tasks import get_goal, get_tasks
from src.services.llm_service import call_llm_with_validation
from src.entities.tool_model import TaskRelevanceResponse,RecommandedStrategyResponse, RelevanceRecoveryResponse, StrategyResponse, InsightDetails
from src.constants.prompts import TASK_RELEVANCE_GATE_NODE_PROMPT, TASK_SUGGESTION_NODE_PROMPT, ROUTE_STRATEGY_NODE_PROMPT, CRITICAL_STRATEGY_NODE_PROMPT, OPTIMIZATION_STRATEGY_NODE_PROMPT, BALANCED_STRATEGY_NODE_PROMPT, INSIGHT_NODE_PROMPT

logger = get_logger(__name__, __file__, logging_level="DEBUG")


def fetch_goal_data_node(state: GoalState):
    try:
        goal = get_goal(state["goal_id"])
        tasks = get_tasks(state["goal_id"])
        task_list = []

        for task in tasks:
            if isinstance(task, dict):
                task_list.append(task)
            else:
                task_list.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "is_completed": task.is_completed,
                })
        logger.info(f"fetch_goal_data_node executed successfully")
        return {
            "goal_data": {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "deadline": goal.deadline,
            },
            "tasks_data": task_list
        }
    except Exception as e:
        logger.error(f"Error fetching goal data: {e}", exc_info=True)
        raise e

def task_relevance_gate_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        tasks = state["tasks_data"]

        all_tasks = '\n'.join([
        f"""
        Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Completed: {task.get('is_completed', False)}
        """
        for i, task in enumerate(tasks)
        ])

        prompt = TASK_RELEVANCE_GATE_NODE_PROMPT.format(goal_title=goal_title, goal_description=goal_description, all_tasks=all_tasks)
        parsed = call_llm_with_validation(
            prompt,
            TaskRelevanceResponse
        )

        relevant_tasks = [t.model_dump() for t in parsed.relevant_tasks]
        irrelevant_tasks = [t.model_dump() for t in parsed.irrelevant_tasks]

        if len(relevant_tasks) == 0:
            next_node = "task_suggestions"
        else:
            next_node = "analytics"

        logger.info(f"task_relevance_gate_node executed successfully")
        return {
            "relevant_tasks": relevant_tasks,
            "irrelevant_tasks": irrelevant_tasks,
            "next_node": next_node
        }
    except Exception as e:
        logger.error(f"Error in task relevance gate node: {e}", exc_info=True)
        raise e

def task_suggestions_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        irrelevant_tasks = state["irrelevant_tasks"]

        irrelevant_tasks_str = '\n'.join([
        f"""
        Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Completed: {task.get('is_completed', False)}
        """
        for i, task in enumerate(irrelevant_tasks)
        ])

        prompt = TASK_SUGGESTION_NODE_PROMPT.format(goal_title=goal_title, goal_description=goal_description, irrelevant_tasks_str=irrelevant_tasks_str)

        parsed = call_llm_with_validation(
            prompt,
            RelevanceRecoveryResponse
        )

        logger.info(f"task_suggestions_node executed successfully")
        return {
            "irrelevant_task_explanations": [e.model_dump() for e in parsed.explanation],
            "suggested_tasks": [t.model_dump() for t in parsed.suggested_tasks]
        }
    except Exception as e:
        logger.error(f"Error in task suggestions node: {e}", exc_info=True)
        raise e


def analytics_node(state: GoalState):
    try:
        tasks = state["tasks_data"]
        logger.info(f"Tasks Data: {tasks}")
        goal = state["goal_data"]

        total = len(tasks)
        logger.info(f"Total tasks: {total}")

        completed = [t for t in tasks if t.get("is_completed")]
        logger.info(f"Completed tasks: {len(completed)}")

        pending = [t for t in tasks if not t.get("is_completed")]
        logger.info(f"Pending tasks: {len(pending)}")

        completion_score = int((len(completed) / total) * 100) if total else 0

        # Deadline handling
        deadline = state.get("deadline") or goal.get("deadline")

        days_remaining = None
        risk_score = 0

        if deadline:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)

            deadline = deadline.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)

            days_remaining = (deadline - now).days

        risk_score = 0
        
        if completion_score < 25: risk_score += 40  # Critical: Low start
        elif completion_score < 50: risk_score += 20 # Warning: Behind mid-point
        
        if len(pending) > (len(completed) * 2): risk_score += 30 # Bottleneck risk
        
        # Deadline risk
        if days_remaining is not None:
            if days_remaining < 3:
                risk_score += 40
            elif days_remaining < 7:
                risk_score += 20

        if risk_score >= 70:
            priority = "High"
        elif risk_score >= 40:
            priority = "Medium"
        else:
            priority = "Low"

        logger.info(f"analytics_node executed successfully")
        return {
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "completion_score": completion_score,
            "priority": priority,
            "days_remaining": days_remaining
        }
    except Exception as e:
        logger.error(f"Error in analytics node: {e}", exc_info=True)
        raise e

def route_strategy_node(state: GoalState):
    try:
        completion_score = state["completion_score"]
        priority = state["priority"]
        days_remaining = state["days_remaining"]
        pending_count = state["pending_tasks"]
        completed_count = state["completed_tasks"]

        prompt = ROUTE_STRATEGY_NODE_PROMPT.format(
            completion_score=completion_score,
            priority=priority,
            days_remaining=days_remaining,
            pending_count=pending_count,
            completed_count=completed_count
        )

        parsed = call_llm_with_validation(
            prompt,
            RecommandedStrategyResponse
        )

        logger.info(f"route_strategy_node executed successfully")
        return {
            "execution_strategy": parsed.strategy,
            "next_node": parsed.strategy
        }
    except Exception as e:
        logger.error(f"Error in route strategy node: {e}", exc_info=True)
        raise e

def critical_strategy_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        tasks = state["relevant_tasks"]

        all_tasks = '\n'.join([
        f"""
        Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Status: {task.get('is_completed', False)}
        """
        for i, task in enumerate(tasks)
        ])
        priority = state["priority"]

        prompt = CRITICAL_STRATEGY_NODE_PROMPT.format(goal_title=goal_title, goal_description=goal_description, all_tasks=all_tasks, priority=priority)
        parsed = call_llm_with_validation(
            prompt,
            StrategyResponse
        )

        logger.info(f"critical_strategy_node executed successfully")
        return {"strategy_plan": parsed.model_dump()}
    except Exception as e:
        logger.error(f"Error in critical strategy node: {e}", exc_info=True)
        raise e

def optimization_strategy_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        tasks = state["relevant_tasks"]
        completion_score = state["completion_score"]
        all_tasks = '\n'.join([
        f"""
        Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Completed: {task.get('is_completed', False)}
        """
        for i, task in enumerate(tasks)
        ])

        prompt = OPTIMIZATION_STRATEGY_NODE_PROMPT.format(goal_title=goal_title, goal_description=goal_description, all_tasks=all_tasks, completion_score=completion_score)
        parsed = call_llm_with_validation(
            prompt,
            StrategyResponse
        )

        logger.info(f"optimization_strategy_node executed successfully")
        return {"strategy_plan": parsed.model_dump()}
    except Exception as e:
        logger.error(f"Error in optimization strategy node: {e}", exc_info=True)
        raise e

def balanced_strategy_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        tasks = state["relevant_tasks"]
        completion_score = state["completion_score"]
        priority = state["priority"]
        all_tasks = '\n'.join([
        f"""
        Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Completed: {task.get('is_completed', False)}
        """
        for i, task in enumerate(tasks)
        ])

        prompt = BALANCED_STRATEGY_NODE_PROMPT.format(goal_title=goal_title, goal_description=goal_description, all_tasks=all_tasks, priority=priority)
        parsed = call_llm_with_validation(
            prompt,
            StrategyResponse
        )

        logger.info(f"balanced_strategy_node executed successfully")
        return {"strategy_plan": parsed.model_dump()}
    except Exception as e:
        logger.error(f"Error in balanced strategy node: {e}", exc_info=True)
        raise e

def insight_node(state: GoalState):
    try:
        goal_title = state["goal_data"]["title"]
        goal_description = state["goal_data"]["description"]
        tasks = state["relevant_tasks"]

        all_tasks = '\n'.join([
            f"""
            Task {i+1}: {task['title']}. Description: {task.get('description', 'N/A')}. Status: {task.get('is_completed', False)}
            """
            for i, task in enumerate(tasks)
        ])
        
        prompt = INSIGHT_NODE_PROMPT.format(goal_title=goal_title, 
        goal_description=goal_description, 
        relevant_tasks=all_tasks,
        completion_score=state["completion_score"],
        priority=state["priority"],
        days_remaining=state["days_remaining"],
        pending_count=state["pending_tasks"],
        completed_count=state["completed_tasks"],
        execution_strategy=state["execution_strategy"]
        )
        parsed = call_llm_with_validation(
            prompt,
            InsightDetails
        )

        logger.info(f"insight_node executed successfully")
        return {"insights": parsed.model_dump()}
    except Exception as e:
        logger.error(f"Error in insight node: {e}", exc_info=True)
        raise e

def observation_tool_node(state: GoalState):

    try:

        observations = {}

        completion = state.get("completion_score", 0)
        priority = state.get("priority", "Low")
        relevant_count = len(state.get("relevant_tasks", []))
        irrelevant_count = len(state.get("irrelevant_tasks", []))
        deadline = state.get("days_remaining")

        # Completion observation
        if completion == 0:
            observations["progress_status"] = "No measurable progress on relevant tasks."
        elif completion < 40:
            observations["progress_status"] = "Low progress detected."
        elif completion < 75:
            observations["progress_status"] = "Moderate progress observed."
        else:
            observations["progress_status"] = "Strong progress observed."

        # Risk observation
        if priority == "High":
            observations["risk_level"] = "Take Immediate Action."
        elif priority == "Medium":
            observations["risk_level"] = "Take Action Soon."
        else:
            observations["risk_level"] = "You are on track."

        # Task quality observation
        if relevant_count == 0:
            observations["task_alignment"] = "No tasks align with the goal."
        else:
            ratio = round(relevant_count / (relevant_count + irrelevant_count), 2)
            observations["task_alignment"] = f"{ratio*100}% tasks aligned with goal."

        # Deadline observation
        if deadline is None:
            observations["deadline_status"] = "No deadline specified."
        elif deadline < 0:
            observations["deadline_status"] = "Deadline has passed."
        else:
            observations["deadline_status"] = f"{deadline} days remaining."

        logger.info(f"observation_tool_node executed successfully")
        return {"observations": observations}

    except Exception as e:
        logger.error(f"Error in observation tool node: {e}", exc_info=True)
        raise e

def answer_formatter_node(state: GoalState):

    try:
        if len(state.get("relevant_tasks", [])) == 0:

            logger.info(f"answer_formatter_node executed successfully")
            return {
                "final_output": {
                    "goal_id": state["goal_id"],
                "goal": state["goal_data"]["title"],
                "message": "No relevant tasks found.",
                "irrelevant_tasks_analysis": state["irrelevant_tasks"],
                "suggested_relevant_tasks": state.get("suggested_tasks", []),
                "observations": state["observations"]
            }
        }

        logger.info(f"answer_formatter_node executed successfully")
        return {
            "final_output": {
                "goal_id": state["goal_id"],
                "goal": state["goal_data"]["title"],
                "completion_score": state["completion_score"],
                "priority": state["priority"],
                "days_remaining": state["days_remaining"],
                "execution_strategy": state["execution_strategy"],
                "strategy_plan": state["strategy_plan"],
                "insights": state["insights"],
                "irrelevant_tasks": state["irrelevant_tasks"],
                "observations": state["observations"]
            }
        }
    except Exception as e:
        logger.error(f"Error in answer formatter node: {e}", exc_info=True)
        raise e