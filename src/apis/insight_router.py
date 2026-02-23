from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from src.entities.api_model import AnalyzeGoalRequest
from src.utils.auth_utils import get_current_user
from src.entities.db_model import User, SessionLocal, Goal
from src.utils.logging_utils import get_logger
from src.core.graph_library import goal_orchestrator
from src.utils.mongo_utils import save_goal_insight

router = APIRouter(tags=["Insight"], prefix="/insight")
logger = get_logger(__name__, __file__, logging_level="DEBUG")

goal_graph = goal_orchestrator()


@router.post("/analyze-goal")
async def analyze_goal(payload: AnalyzeGoalRequest, current_user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == payload.goal_id, Goal.is_deleted == False).first()

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        if goal.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if not goal_graph:
            raise HTTPException(status_code=500, detail="Graph not initialized")

        try:
            result = goal_graph.invoke({
                "goal_id": payload.goal_id,
            })
        except Exception as e:
            logger.error(f"Error invoking graph: {e}")
            raise HTTPException(status_code=500, detail="something went wrong. Please try again later.")

        insight_order = save_goal_insight(
            user_id=current_user.id,
            goal_id=payload.goal_id,
            goal_title=goal.title,
            insight_data=result["final_output"]
        )
        logger.info(f"Insight saved successfully for user {current_user.id} and goal {payload.goal_id}")

        return {
            **result["final_output"],
            "insight_order": insight_order
        }

    except Exception as e:
        logger.error(f"Error analyzing goal: {e}")
        raise HTTPException(status_code=500, detail="something went wrong. Please try again later.")

    finally:
        db.close()