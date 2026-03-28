from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateGoalRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    deadline: Optional[str] = None
    priority: str   

class GoalUpdateRequest(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None   
    category: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None

class CreateTaskRequest(BaseModel):
    goal_id: int
    title: str
    description: Optional[str] = None
    priority: str

class TaskUpdateRequest(BaseModel):
    id: int
    goal_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None

class CreateNoteRequest(BaseModel):
    goal_id: int
    title: str
    content: Optional[str] = None

class NoteUpdateRequest(BaseModel):
    note_id: str
    goal_id: int
    title: Optional[str] = None
    content: Optional[str] = None

class GenerateTasksRequest(BaseModel):
    goal_id: int

class AnalyzeGoalRequest(BaseModel):
    goal_id: int