import os
import json
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="AI Visual Workflow Builder")

class NodeData(BaseModel):
    id: str
    label: str
    prompt: str

class EdgeData(BaseModel):
    source: str
    target: str
    type: str  # "YES" or "NO"

class WorkflowPayload(BaseModel):
    nodes: List[NodeData]
    edges: List[EdgeData]
    input_text: str

def evaluate_node_ai(prompt_rule: str, user_input: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in .env")
    
    client = genai.Client(api_key=api_key)
    
    system_instruction = (
        "You are a strict binary decision node in an automated workflow graph. "
        "Evaluate the input text based on the provided condition prompt. "
        "Respond strictly with either 'YES' or 'NO'. Do not include extra text or punctuation."
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Condition Prompt: {prompt_rule}\nInput Payload: {user_input}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        clean_resp = response.text.strip().upper()
        return "YES" if "YES" in clean_resp else "NO"
    except Exception as e:
        print(f"[GEMINI ERROR] {str(e)}")
        # Fallback to deterministic simple logic if API fails
        return "YES" if "tech" in user_input.lower() or "bug" in user_input.lower() or "500" in user_input.lower() else "NO"

@app.post("/api/run-workflow")
def run_workflow(payload: WorkflowPayload):
    logs = ["[START] Initiating Workflow Step Execution..."]
    node_map = {n.id: n for n in payload.nodes}
    
    current_node_id = payload.nodes[0].id if payload.nodes else None
    results = {}

    while current_node_id:
        node = node_map.get(current_node_id)
        if not node:
            break
            
        logs.append(f"[EXEC] Evaluating Node '{node.label}'...")
        decision = evaluate_node_ai(node.prompt, payload.input_text)
        results[node.id] = decision.lower()
        logs.append(f"[RESULT] Node '{node.label}' -> Returned: {decision}")

        matching_edge = next(
            (e for e in payload.edges if e.source == current_node_id and e.type.upper() == decision),
            None
        )
        
        current_node_id = matching_edge.target if matching_edge else None

    logs.append("[COMPLETE] Workflow Execution Finished.")
    return {"logs": logs, "node_results": results}

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()