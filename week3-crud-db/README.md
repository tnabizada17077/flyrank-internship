Markdown
# Week 3 Assignment A2: Connecting CRUD to SQLite

## Overview
This project replaces the in-memory storage layer from Assignment 1 with a persistent SQLite database (`tasks.db`). All CRUD endpoints behave identically to the client while storing data permanently on disk.

## Why SQLite?
* **Zero Configuration:** Operates as a single local file (`tasks.db`) without requiring a separate database server.
* **Data Persistence:** Ensures tasks survive application restarts.
* **Serverless Execution:** Embedded directly into Python's standard library via `sqlite3`.

## Startup Command
Run the application using Uvicorn:
```bash
uvicorn main:app --reload
Stage 4: SQL Query Verification
Executed directly against tasks.db to inspect completed tasks:

SQL
SELECT * FROM tasks WHERE done = 1;
Database Screenshot