from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.entities.api_model import CreateGoalRequest, GoalUpdateRequest
from src.services.reminder_service import send_goal_created_notification
from src.utils.auth_utils import get_current_user
from src.entities.db_model import User, SessionLocal, Goal
from src.utils.logging_utils import get_logger

router = APIRouter(tags=["Goal"], prefix="/goal")
logger = get_logger(__name__, __file__, logging_level="DEBUG")

@router.post("/create-goal")
def create_goal(request: CreateGoalRequest, background_tasks: BackgroundTasks,
                current_user: User = Depends(get_current_user)):
    """ Create a goal """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not request.description:
            request.description = ""
        goal_exists = db.query(Goal).filter(Goal.user_id == current_user.id, Goal.title == request.title, Goal.is_deleted == False).first()
        if goal_exists:
            raise HTTPException(status_code=400, detail="Goal already exists")
        goal = Goal(
            user_id=current_user.id,
            title=request.title,
            category=request.category,
            description=request.description,
            priority=request.priority,
            deadline=request.deadline
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        background_tasks.add_task(send_goal_created_notification, goal.id)
        logger.info(f"Goal created successfully for user {current_user.id}")
        return {"message":"Goal created successfully", 
                "goal_id":goal.id, 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while creating goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.get("/get-goals")
def get_goals(current_user: User = Depends(get_current_user)):
    """ Get all goals for the current user """
    db: Session = SessionLocal()
    try:
        goals = db.query(Goal).filter(Goal.user_id == current_user.id, Goal.is_deleted == False).all()
        goal_list = []
        for goal in goals:
            goal_list.append({
                "goal_id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": goal.priority
            })
        return {"message":"Goals fetched successfully", 
                "goals":goal_list, 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching goals")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.get("/{goal_id}/get-goal")
def get_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """ Get goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"message":"Goal fetched successfully", 
                "goal":{
                "goal_id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": goal.priority
            }, 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.put("/update-goal")
def update_goal(request: GoalUpdateRequest, current_user: User = Depends(get_current_user)):
    """ Update a goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == request.id, Goal.user_id == current_user.id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        if request.title:
            goal.title = request.title
        if request.description:
            goal.description = request.description
        if request.priority:
            goal.priority = request.priority
        db.commit()
        db.refresh(goal)
        return {"message":"Goal updated successfully", 
                "content":{
                "goal_id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "priority": goal.priority
            }, 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while updating goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.delete("/{goal_id}/delete-goal")
def delete_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """ Delete a goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal.is_deleted = True  
        db.commit()
        return {"message":f"{goal.title} Goal deleted successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while deleting goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()    

@router.patch("/{goal_id}/complete-goal")
def complete_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """ Complete a goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal.is_completed = True  
        db.commit()
        return {"message":f"{goal.title} Goal completed successfully",  
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while completing goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()    

@router.patch("/{goal_id}/uncomplete-goal")
def uncomplete_goal(goal_id: int, current_user: User = Depends(get_current_user)):
    """ Uncomplete a goal by goal id """
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        goal.is_completed = False  
        db.commit()
        return {"message":f"{goal.title} Goal uncompleted successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while uncompleting goal")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()
