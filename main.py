from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")

@app.get("/")
def read_root():
    return {"message": "Hello, server!"}