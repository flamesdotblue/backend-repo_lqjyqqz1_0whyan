"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Task -> "task" collection
- Assignment -> "assignment" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: str = Field("annotator", description="user role: admin | annotator")
    is_active: bool = Field(True, description="Whether user is active")

class Task(BaseModel):
    """
    Tasks collection schema
    Collection name: "task"
    """
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    instructions: Optional[str] = Field(None, description="Detailed instructions")
    due_date: Optional[datetime] = Field(None, description="Optional deadline")
    priority: str = Field("normal", description="low | normal | high")

class Assignment(BaseModel):
    """
    Assignments link tasks to users
    Collection name: "assignment"
    """
    user_email: str = Field(..., description="User email this task is assigned to")
    task_id: str = Field(..., description="ID of the task document as string")
    status: str = Field("pending", description="pending | in_progress | completed")
    notes: Optional[str] = Field(None, description="Optional notes or feedback")
