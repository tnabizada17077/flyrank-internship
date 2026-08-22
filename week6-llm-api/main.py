import os
import json
import time
from enum import Enum
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="FlyRank LLM Triage API")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class CategoryEnum(str, Enum):
    billing = "billing"
    bug = "bug"
    feature_request = "feature_request"
    general = "general"

class UrgencyEnum(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"

class TriageInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)

class TriageOutput(BaseModel):
    category: CategoryEnum
    urgency: UrgencyEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_action: str
    reason: str

def load_prompt() -> str:
    with open("prompts/triage-v1.md", "r") as f:
        return f.read()

SYSTEM_PROMPT = load_prompt()

def log_quarantine(raw_output: str, error_msg: str, user_input: str):
    os.makedirs("logs", exist_ok=True)
    with open("logs/quarantine.jsonl", "a") as f:
        log_entry = {
            "timestamp": time.time(),
            "input": user_input,
            "raw_output": raw_output,
            "error": error_msg,
            "prompt_version": "triage-v1"
        }
        f.write(json.dumps(log_entry) + "\n")

@app.post("/triage", response_model=TriageOutput)
def triage_message(payload: TriageInput):
    # Kill switch
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        return TriageOutput(
            category=CategoryEnum.general,
            urgency=UrgencyEnum.normal,
            confidence=0.0,
            suggested_action="Kill switch active: Manual triage required",
            reason="LLM feature disabled via kill switch"
        )

    # Stub mode
    if os.getenv("LLM_STUB", "0") == "1":
        return TriageOutput(
            category=CategoryEnum.bug,
            urgency=UrgencyEnum.normal,
            confidence=0.99,
            suggested_action="Stub response: Issue logged",
            reason="Stub mode active"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in .env file")

    client = genai.Client(api_key=api_key)
    start_time = time.time()
    raw_response_text = ""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"User Message: {payload.text}",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=TriageOutput,
            )
        )
        raw_response_text = response.text
        duration_ms = (time.time() - start_time) * 1000
        print(f"[COST LOG] Prompt v1 | Model: gemini-2.5-flash | Duration: {duration_ms:.2f}ms")

        return TriageOutput.model_validate_json(raw_response_text)

    except (ValidationError, json.JSONDecodeError) as err:
        print(f"[REPAIR TRIGGERED] Validation error: {str(err)}")
        try:
            repair_prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Your previous output failed validation: {str(err)}.\n"
                f"Raw response: {raw_response_text}\n"
                f"Fix the error and return JSON strictly matching the schema."
            )
            repair_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"User Message: {payload.text}",
                config=types.GenerateContentConfig(
                    system_instruction=repair_prompt,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=TriageOutput,
                )
            )
            return TriageOutput.model_validate_json(repair_response.text)
        except Exception as repair_err:
            log_quarantine(raw_response_text, str(repair_err), payload.text)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Model output failed schema validation after repair retry: {str(repair_err)}"
            )
    except Exception as e:
        print(f"[LLM ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")