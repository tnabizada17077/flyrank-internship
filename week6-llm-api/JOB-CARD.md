# Job Card: Support Message Triage API

- **What it does:** Classifies incoming user support messages into actionable categories and urgency levels.
- **Input:** `{ "text": "string, 1-2000 characters" }`
- **Output:** `{ "category": "billing" | "bug" | "feature_request" | "general", "urgency": "low" | "normal" | "high" | "critical", "confidence": float 0.0-1.0, "suggested_action": "string", "reason": "string" }`
- **It must never:** Invent categories outside the permitted list, return markdown text fences around JSON, or return conversational prose.
- **When unsure:** Return category `"general"`, urgency `"normal"`, and set confidence below `0.5`.