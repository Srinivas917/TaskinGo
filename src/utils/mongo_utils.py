from datetime import datetime
from src.entities.mongo_model import ai_insights_collection


def save_goal_insight(user_id: int, goal_id: int, goal_title: str, insight_data: dict):
    
    # Get last insight order
    last_insight = ai_insights_collection.find_one(
        {
            "user_id": user_id,
            "goal_id": goal_id
        },
        sort=[("insight_order", -1)]
    )

    next_order = 1
    if last_insight and "insight_order" in last_insight:
        next_order = last_insight["insight_order"] + 1

    document = {
        "user_id": user_id,
        "goal_id": goal_id,
        "goal_title": goal_title,
        "insight": insight_data,
        "insight_order": next_order,
        "created_at": datetime.utcnow()
    }

    ai_insights_collection.insert_one(document)

    return next_order