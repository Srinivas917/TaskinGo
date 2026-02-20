from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.entities.api_model import CreateTaskRequest, TaskUpdateRequest, GenerateTasksRequest
from src.utils.auth_utils import get_current_user
from src.services.llm_service import generate_or_analyze_tasks
from src.entities.db_model import User, SessionLocal, Goal, Task
from src.utils.logging_utils import get_logger

router = APIRouter(tags=["Task"], prefix="/task")
logger = get_logger(__name__, __file__, logging_level="DEBUG")

@router.post("/create-task")
def create_task(request: CreateTaskRequest, current_user: User = Depends(get_current_user)):
    """ Create a task """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not request.description:
            request.description = ""
        task = Task(
            title=request.title,
            description=request.description,
            priority=request.priority,
            goal_id=request.goal_id
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"message":f"{task.title} Task for goal id {task.goal_id} created successfully", 
                 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while creating task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.get("/get-tasks")
def get_tasks(goal_id: int, current_user: User = Depends(get_current_user)):
    """ Get all tasks for the current user and goal """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        tasks = db.query(Task).filter(Task.goal_id == goal_id, Task.is_deleted == False).all()
        task_list = []
        for task in tasks:
            task_list.append({
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "goal_id": task.goal_id
            })
        return {"message":"Tasks fetched successfully", 
                "tasks":task_list, 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching tasks")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.get("/get-task")
def get_task(task_id: int, goal_id: int, current_user: User = Depends(get_current_user)):
    """ Get task by task id and goal id """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        task = db.query(Task).filter(Task.id == task_id, Task.goal_id == goal_id, Task.is_deleted == False).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message":"Task fetched successfully", 
                "task":{
                    "goal_id": task.goal_id,
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,  
                }
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while fetching task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.post("/generate-tasks")
async def process_goal(request: GenerateTasksRequest, current_user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        goal = db.query(Goal).filter(Goal.id == request.goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False).first()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        goal_title = goal.title
        goal_description = goal.description
        tasks = db.query(Task).filter(Task.goal_id == goal.id, Task.is_deleted == False).all()

        if not tasks:
            tasks = []
        tasks = [{"title": task.title, "description": task.description} for task in tasks]

        llm_response = generate_or_analyze_tasks(
            goal_title,
            goal_description,
            tasks
        )

        if llm_response.goal_completed:
            return {
                "status": "completed",
                "message": "Goal achieved successfully.",
                "tasks": []
            }

        return {
            "status": "in_progress",
            "message": "Additional tasks required.",
            "tasks": llm_response.tasks
        }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while generating tasks")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.put("/update-task")
def update_task(request: TaskUpdateRequest, current_user: User = Depends(get_current_user)):
    """ Update a task by task id """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        task = db.query(Task).filter(Task.id == request.id,Task.goal_id == request.goal_id, Task.is_deleted == False).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        if request.title:
            task.title = request.title
        if request.description:
            task.description = request.description
        if request.priority:
            task.priority = request.priority
        db.commit()
        return {"message":f"{task.title} Task updated successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while updating task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.delete("/delete-task")
def delete_task(task_id: int, goal_id: int, current_user: User = Depends(get_current_user)):
    """ Delete a task by task id """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        task = db.query(Task).filter(Task.id == task_id,Task.goal_id == goal_id, Task.is_deleted == False).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.is_deleted = True
        db.commit()
        return {"message":f"{task.title} Task deleted successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while deleting task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.put("/complete-task")
def complete_task(task_id: int, goal_id: int, current_user: User = Depends(get_current_user)):
    """ Complete a task by task id """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        task = db.query(Task).filter(Task.id == task_id,Task.goal_id == goal_id, Task.is_deleted == False).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.is_completed = True
        db.commit()
        return {"message":f"{task.title} Task completed successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while completing task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()

@router.put("/uncomplete-task")
def uncomplete_task(task_id: int, goal_id: int, current_user: User = Depends(get_current_user)):
    """ Uncomplete a task by task id """
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        task = db.query(Task).filter(Task.id == task_id,Task.goal_id == goal_id, Task.is_deleted == False).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.is_completed = False
        db.commit()
        return {"message":f"{task.title} Task uncompleted successfully", 
                }
    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        logger.exception("Unexpected error while uncompleting task")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )
    finally:
        db.close()



