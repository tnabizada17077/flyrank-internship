from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Task API", version="1.0")

# Input validation model
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Build CRUD API", "done": False},
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def check_health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found"
    )

# POST /tasks - Create a task
@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task_input: TaskCreate):
    # Auto-generate next ID
    next_id = max((t["id"] for t in tasks), default=0) + 1
    
    new_task = {
        "id": next_id,
        "title": task_input.title.strip(),
        "done": False
    }
    
    # Extra check for whitespace-only strings
    if not new_task["title"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace"
        )
        
    tasks.append(new_task)
    return new_task