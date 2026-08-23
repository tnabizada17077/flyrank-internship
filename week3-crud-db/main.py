import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DB_NAME = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Stage 0: Create tasks table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        );
    """)
    
    # Stage 0: Seed initial 3 tasks ONLY if table is empty
    cursor.execute("SELECT COUNT(*) as count FROM tasks;")
    row_count = cursor.fetchone()["count"]
    
    if row_count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?);",
            [
                ("Learn SQLite with FastAPI", 1),
                ("Build parameterized queries", 0),
                ("Verify persistence across restarts", 0)
            ]
        )
    
    conn.commit()
    conn.close()

# Initialize database on application start
init_db()

app = FastAPI(title="Task CRUD API with SQLite Persistence")

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    done: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool

# Stage 1: Read all tasks
@app.get("/tasks", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
def get_all_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks;")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

# Stage 1: Read single task
@app.get("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task_by_id(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

# Stage 2: Insert new task
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0);", (title,))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {"id": new_id, "title": title, "done": False}

# Stage 3: Update task
@app.put("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(task_id: int, payload: TaskUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (task_id,))
    existing = cursor.fetchone()
    
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
        
    new_title = existing["title"]
    if payload.title is not None:
        cleaned_title = payload.title.strip()
        if not cleaned_title:
            conn.close()
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        new_title = cleaned_title
        
    new_done = existing["done"] if payload.done is None else (1 if payload.done else 0)
    
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?;",
        (new_title, new_done, task_id)
    )
    conn.commit()
    conn.close()
    
    return {"id": task_id, "title": new_title, "done": bool(new_done)}

# Stage 3: Delete task
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tasks WHERE id = ?;", (task_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
        
    cursor.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
    conn.commit()
    conn.close()
    return None