from groq import Groq
from src.entities.tool_model import TaskPlannerResponse
import json
from src.constants.properties import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def generate_or_analyze_tasks(goal_title: str, goal_description: str | None, tasks: list[dict]):
    """
    goal_title: str
    goal_description: str | None
    tasks: list[dict] -> [{"title": "...", "description": "..."}]
    """

    if tasks:
        existing_tasks_text = "\n".join(
            [
                f"{i+1}. {t['title']} - {t.get('description', '')}"
                for i, t in enumerate(tasks)
            ]
        )
    else:
        existing_tasks_text = "No existing tasks."

    system_prompt = """
    You are a precision-focused Task Decomposition Engine. Your sole purpose is to determine the logical gap between a Goal and the current state of Existing Tasks.

    **Operational Constraints:**
    1. ANALYZE: Compare "Goal Title" and "Goal Description" against "Existing Tasks".
    2. EVALUATE: Determine if the "Existing Tasks" fully satisfy every requirement of the Goal.
    3. OUTPUT RULES:
    - If the goal is fully met by existing tasks: set "goal_completed" to true and "tasks" to [].
    - If the goal is NOT met: set "goal_completed" to false and generate ONLY the missing, logically sequential tasks required to finish the goal.
    - If "Existing Tasks" is empty: generate a comprehensive, step-by-step task list to achieve the goal from scratch.
    4. ANTI-HALLUCINATION: Do not invent sub-goals. Do not include tasks already listed in "Existing Tasks". Do not provide conversational filler.

    **Response Format:**
    You must return a raw JSON object. No markdown blocks, no explanations.
    {
    "goal_completed": boolean,
    "tasks": ["string", "string"]
    }
    """
    user_prompt = f"""
    [GOAL DATA]
    Title: {goal_title}
    Description: {goal_description}

    [CURRENT STATE]
    Existing Tasks: 
    {existing_tasks_text}

    [INSTRUCTION]
    Analyze the gap and provide the JSON response.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    # Validate strictly
    parsed = TaskPlannerResponse.model_validate_json(content)

    return parsed
