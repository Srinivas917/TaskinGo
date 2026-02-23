from sqlalchemy.orm import Session
from src.entities.db_model import User, SessionLocal, Goal, Task
from src.utils.logging_utils import get_logger

logger = get_logger(__name__, __file__, logging_level="DEBUG")

def get_goal(goal_id: int) -> Goal:
    """ Get goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal
    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

def get_tasks(goal_id: int) -> list[Task]:
    """ Get all tasks for the current user and goal """
    db: Session = SessionLocal()
    try:
        tasks = db.query(Task).filter(Task.goal_id == goal_id, Task.is_deleted == False).all()
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "is_completed": task.is_completed,
                "goal_id": task.goal_id
            })
        return task_list

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching tasks")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()
