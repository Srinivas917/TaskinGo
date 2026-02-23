from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.utils.auth_utils import get_current_user

from src.entities.api_model import LoginRequest, RegisterRequest
from src.entities.db_model import User, SessionLocal, Goal, Task
from src.utils.auth_utils import create_access_token, create_refresh_token, decode_refresh_token, verify_password, hash_password
from src.utils.logging_utils import get_logger

router = APIRouter(tags=["Auth"], prefix="/auth")
logger = get_logger(__name__, __file__, logging_level="DEBUG")


async def check_cookie(request: Request):
    """
    Checks for refresh-Token in the request cookies and returns it if present.

    Args:
        request (Request): Incoming HTTP request containing cookies.

    Returns:
        The refresh token value if found, otherwise None.
    """
    cookie = request.cookies
    if not cookie:
        return None
    if cookie.get('refresh-Token'):
        return cookie.get('refresh-Token')

@router.post("/register")
async def register(request: RegisterRequest):
    db: Session = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.username == request.username, User.is_deleted == False)
            .first()
        )
        if user:
            raise HTTPException(status_code=400, detail="Username already exists")

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {"message": "User created successfully", "user_id": user.id, "username": user.username, "email": user.email}
    except Exception as e:
        db.rollback()
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error during registration")
    finally:
        db.close()

@router.post("/login")
async def login(request: LoginRequest):
    db: Session = SessionLocal()
    try:        
        user = (
            db.query(User)
            .filter(User.username == request.username, User.is_deleted == False)
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error during login")
    finally:
        db.close()

    claims = {"user_id": user.id, "username": user.username, "mail": user.email}
    token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)

    response = JSONResponse(
        {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
        },
        status_code=200,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        path="/auth",
        secure=True,
        samesite="none",
    )

    return response


@router.post("/refresh")
async def refresh(request: Request):
    """Refresh access token"""
    # Read refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    payload = decode_refresh_token(refresh_token)
    user_id = payload.get("user_id")
    if user_id is None:
        # optionally derive from sub
        sub = payload.get("sub")
        if sub and str(sub).isdigit():
            user_id = int(sub)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Ensure user still exists/active
    db: Session = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.id == user_id, User.is_deleted == False)
            .first()
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

    except Exception as e:
        logger.error(f"Error during generating refresh token: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error during generating refresh token")
    finally:
        db.close()


    # rotate refresh token
    claims = {"user_id": user.id, "username": user.username, "mail": user.email}
    new_access = create_access_token(claims)
    new_refresh = create_refresh_token(claims)  # rotate; or skip if not rotating

    response = JSONResponse(
        {"access_token": new_access, "token_type": "bearer", "user_id": user.id},
        status_code=200,
    )
    # Re-set rotated refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        path="/auth",
        secure=True, 
        samesite="none",
    )

    return response


@router.post("/logout")
async def logout():
    """Logout user and delete refresh token"""
    try:
        response = JSONResponse({"message": "Logged out"}, status_code=200)
        response.delete_cookie(key="refresh_token", path="/auth")
        return response
    except Exception as e:
        logger.error(f"Error during logout: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error during logout")

@router.get("/user-profile")
async def user_profile(current_user: User = Depends(get_current_user)):
    db: Session = SessionLocal()
    try:
        goals = (
            db.query(Goal)
            .filter(Goal.user_id == current_user.id, Goal.is_deleted == False)
            .all()
        )

        completed_goals = []
        pending_goals = []
        completed_tasks = []
        pending_tasks = []
        
        for goal in goals:
            if goal.is_completed:
                completed_goals.append(goal)
            else:
                pending_goals.append(goal)
            
            tasks = (
                db.query(Task)
                .filter(Task.goal_id == goal.id, Task.is_deleted == False)
                .all()
            )

            for task in tasks:
                if task.is_completed:
                    completed_tasks.append(task)
                else:
                    pending_tasks.append(task)
            
            

        return {"user_id": current_user.id, 
        "username": current_user.username, 
        "email": current_user.email,
        "total_goals": len(goals),
        "completed_goals": len(completed_goals),
        "pending_goals": len(pending_goals),
        "completed_tasks": len(completed_tasks),
        "pending_tasks": len(pending_tasks)
        }
    except Exception as e:
        logger.error(f"Error during fetching user profile: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Error during fetching user profile")
    finally:
        db.close()