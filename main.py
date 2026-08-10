from typing import Optional
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

app = FastAPI(title="Task API", version="1.0")

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title cannot be empty")

# Input validation model for updating tasks
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

tasks =[
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Build CRUD API", "done": False},]

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

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task_input: TaskCreate):
    next_id = max((t["id"] for t in tasks), default=0) + 1
    new_task = {
        "id": next_id,
        "title": task_input.title.strip(),
        "done": False
    }
    if not new_task["title"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace"
        )
    tasks.append(new_task)
    return new_task

# PUT /tasks/{id} - Update a task
@app.put("/tasks/{id}")
def update_task(id: int, task_input: TaskUpdate):
    for task in tasks:
        if task["id"] == id:
            if task_input.title is not None:
                cleaned_title = task_input.title.strip()
                if not cleaned_title:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Title cannot be empty"
                    )
                task["title"] = cleaned_title
            if task_input.done is not None:
                task["done"] = task_input.done
            return task
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found"
    )

# DELETE /tasks/{id} - Remove a task
@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(id: int):
    for index, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(index)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found"
    )