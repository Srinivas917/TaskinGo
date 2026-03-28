from groq import Groq
from src.entities.tool_model import TaskPlannerResponse
from typing import Type
from pydantic import BaseModel, ValidationError
import json
from src.constants.properties import GROQ_API_KEY, LLM_MODEL_NAME
from src.constants.prompts import GENERATE_OR_ANALYZE_TASKS_PROMPT
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, __file__, logging_level="DEBUG")

client = Groq(api_key=GROQ_API_KEY)


def generate_or_analyze_tasks(goal_title: str, goal_description: str | None, tasks: list[dict]):
    """
    goal_title: str
    goal_description: str | None
    tasks: list[dict] -> [{"title": "...", "description": "..."}]
    """
    try:
        if tasks:
            existing_tasks_text = "\n".join(
                [
                    f"{i+1}. {t['title']} - {t.get('description', '')}"
                    for i, t in enumerate(tasks)
                ]
            )
        else:
            existing_tasks_text = "No existing tasks."

        prompt = GENERATE_OR_ANALYZE_TASKS_PROMPT.format(
            goal_title=goal_title,
            goal_description=goal_description,
            existing_tasks_text=existing_tasks_text
        )
        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            temperature=0.1,
            messages=[
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        # Validate strictly
        parsed = TaskPlannerResponse.model_validate_json(content)

        return parsed
    except Exception as e:
        logger.error(f"Error generating or analyzing tasks: {e}", exc_info=True)
        raise e


def call_llm_with_validation(
    prompt: str,
    response_model: Type[BaseModel],
    max_retries: int = 2
):
    try:
        parsed = None

        model_name = LLM_MODEL_NAME
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content

                parsed = response_model.model_validate_json(content)

            except ValidationError as e:
                logger.error(f"Validation error: {e}")
                raise
            
        return parsed
    except Exception as e:
        logger.error(f"Error calling LLM with validation: {e}", exc_info=True)
        raise e

        
