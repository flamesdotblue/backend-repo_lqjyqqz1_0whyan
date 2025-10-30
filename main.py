import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User as UserSchema, Task as TaskSchema, Assignment as AssignmentSchema

app = FastAPI(title="Outlier-like Task Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Utility to convert ObjectId to string for responses

def _stringify_ids(docs: List[dict]):
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["_id"] = str(d["_id"])
    return docs

# User endpoints
@app.post("/users", response_model=dict)
def create_user(user: UserSchema):
    # enforce unique email
    existing = list(db["user"].find({"email": user.email}).limit(1)) if db else []
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    inserted_id = create_document("user", user)
    return {"id": inserted_id}

@app.get("/users", response_model=List[dict])
def list_users(active: Optional[bool] = None):
    filt = {}
    if active is not None:
        filt["is_active"] = active
    users = get_documents("user", filt)
    return _stringify_ids(users)

# Task endpoints
@app.post("/admin/tasks", response_model=dict)
def create_task(task: TaskSchema):
    inserted_id = create_document("task", task)
    return {"id": inserted_id}

@app.get("/tasks", response_model=List[dict])
def list_tasks():
    tasks = get_documents("task")
    return _stringify_ids(tasks)

# Assignment endpoints
class AssignRequest(BaseModel):
    task_id: str
    user_emails: Optional[List[str]] = None  # if None, assign to all active users

@app.post("/admin/assignments/auto", response_model=dict)
def auto_assign(assign: AssignRequest):
    # Validate task exists
    try:
        task_obj = db["task"].find_one({"_id": ObjectId(assign.task_id)})
    except Exception:
        task_obj = None
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")

    # Determine target users
    if assign.user_emails:
        users = list(db["user"].find({"email": {"$in": assign.user_emails}, "is_active": True}))
    else:
        users = list(db["user"].find({"is_active": True}))

    created = 0
    for u in users:
        existing = db["assignment"].find_one({"user_email": u["email"], "task_id": assign.task_id})
        if existing:
            continue
        create_document("assignment", AssignmentSchema(user_email=u["email"], task_id=assign.task_id))
        created += 1

    return {"assigned": created, "users_considered": len(users)}

@app.get("/assignments", response_model=List[dict])
def list_assignments(user_email: Optional[str] = None):
    filt = {}
    if user_email:
        filt["user_email"] = user_email
    assigns = get_documents("assignment", filt)
    return _stringify_ids(assigns)

@app.post("/assignments/{assignment_id}/complete", response_model=dict)
def complete_assignment(assignment_id: str):
    try:
        oid = ObjectId(assignment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid assignment id")
    res = db["assignment"].update_one({"_id": oid}, {"$set": {"status": "completed"}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"status": "completed"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
