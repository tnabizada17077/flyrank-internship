from fastapi import FastAPI, HTTPException, status

app = FastAPI(title="Task API", version="1.0")

# In-memory "database" pre-filled with 3 example tasks
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

# GET /tasks - returns all tasks
@app.get("/tasks")
def get_tasks():
    return tasks

# GET /tasks/{id} - returns a single task by ID
@app.get("/tasks/{id}")
def get_task(id: int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found"
    )