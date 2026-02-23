from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from bson import ObjectId
from src.entities.api_model import CreateNoteRequest, NoteUpdateRequest
from src.utils.auth_utils import get_current_user
from src.entities.db_model import User, SessionLocal, Goal
from src.entities.mongo_model import notes_collection
from src.utils.logging_utils import get_logger

router = APIRouter(tags=["Notes"], prefix="/notes")
logger = get_logger(__name__, __file__, logging_level="DEBUG")

from datetime import datetime

@router.post("/create-note")
def create_note(
    request: CreateNoteRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a new note for a specific goal.
    """
    db: Session = SessionLocal()

    try:
        # Validate goal ownership from SQL
        goal = (
            db.query(Goal)
            .filter(Goal.id == request.goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False)
            .first()
        )

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        note_data = {
            "user_id": current_user.id,
            "title": request.title,
            "content": request.content or "",
            "goal_id": request.goal_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = notes_collection.insert_one(note_data)

        return {
            "message": "Note created successfully",
            "note_id": str(result.inserted_id)
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while creating note")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    finally:
        db.close()

@router.get("/{goal_id}/get-notes")
def get_notes(
    goal_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get all notes for a specific goal.
    """
    db: Session = SessionLocal()

    try:
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False)
            .first()
        )

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        notes_cursor = notes_collection.find(
            {"goal_id": goal_id, "user_id": current_user.id}
            )

        notes = []
        for note in notes_cursor:
            notes.append({
                "_id": str(note["_id"]),
                "title": note.get("title"),
                "content": note.get("content"),
                "created_at": note.get("created_at"),
            })

        return {
            "message": "Notes fetched successfully",
            "notes": notes
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while fetching notes")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    finally:
        db.close()

@router.get("/{goal_id}/{note_id}/get-note")
def get_note(
    note_id: str,
    goal_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get a note by note_id for a specific goal by goal_id.
    """
    db: Session = SessionLocal()

    try:
        if not ObjectId.is_valid(note_id):
            raise HTTPException(status_code=400, detail="Invalid note ID")
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False)
            .first()
        )

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        note = notes_collection.find_one(
            {"_id": ObjectId(note_id), 
            "goal_id": goal_id, "user_id": current_user.id})

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        return {
            "message": "Note fetched successfully",
            "note": {
                "_id": str(note["_id"]),
                "title": note.get("title"),
                "content": note.get("content"),
                "created_at": note.get("created_at"),
            }
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while fetching note")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    finally:
        db.close()

@router.put("/update-note")
def update_note(
    request: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Update a note by note_id for a specific goal by goal_id.
    """
    db: Session = SessionLocal()

    try:
        if not ObjectId.is_valid(request.note_id):
            raise HTTPException(status_code=400, detail="Invalid note ID")

        goal = (
            db.query(Goal)
            .filter(Goal.id == request.goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False)
            .first()
        )

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

        update_data = {}

        if request.title is not None:
            update_data["title"] = request.title

        if request.content is not None:
            update_data["content"] = request.content

        update_data["updated_at"] = datetime.utcnow()

        result = notes_collection.update_one(
            {"_id": ObjectId(request.note_id), "goal_id": request.goal_id, "user_id": current_user.id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")

        return {"status": "success",
                "data": {
                    "note_id": str(request.note_id),
                    "title": update_data.get("title"),
                    "content": update_data.get("content"),
                    "updated_at": update_data.get("updated_at"),
                }
                }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while updating note")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    finally:
        db.close()

@router.delete("/{goal_id}/{note_id}/delete-note")
def delete_note(
    note_id: str,
    goal_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a note by note_id for a specific goal by goal_id.
    """
    db: Session = SessionLocal()

    try:
        if not ObjectId.is_valid(note_id):
            raise HTTPException(status_code=400, detail="Invalid note ID")
        goal = (
            db.query(Goal)
            .filter(Goal.id == goal_id, Goal.user_id == current_user.id, Goal.is_deleted == False)
            .first()
        )

        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        result = notes_collection.delete_one(
            {"_id": ObjectId(note_id), 
            "goal_id": goal_id, "user_id": current_user.id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")

        return {"status": "success",
                "note_id": str(note_id)
                }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Unexpected error while deleting note")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    finally:
        db.close()