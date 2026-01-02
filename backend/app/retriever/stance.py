# app/retriever/stance.py

import os
import json
from typing import Literal
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL_NAME = "llama-3.1-8b-instant"

STANCE_SYSTEM_PROMPT = """
You are a factual reasoning engine.

Your task is to determine whether a piece of evidence
SUPPORTS, CONTRADICTS, or is NEUTRAL toward a claim.

Rules:
- Use general world knowledge and common sense.
- Resolve geography, roles, numbers, dates, and death status yourself.
- Do NOT simulate rule-based logic or list steps.
- Do NOT ask for external data.
- If uncertain, choose "neutral".

Respond ONLY in valid JSON with:
{
  "stance": "support" | "contradict" | "neutral",
  "confidence": number between 0 and 1,
  "explanation": "one concise sentence"
}
""".strip()


class StanceResponse(BaseModel):
    stance: Literal["support", "contradict", "neutral"]
    confidence: float
    explanation: str


client = Groq()  # <-- KEY CHANGE (uses env automatically)


def detect_stance(claim: str, evidence: str) -> StanceResponse:
    if not claim or not evidence:
        return StanceResponse(
            stance="neutral",
            confidence=0.0,
            explanation="Missing claim or evidence."
        )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0,
            max_tokens=256,
            messages=[
                {"role": "system", "content": STANCE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Claim:\n{claim}\n\nEvidence:\n{evidence}"
                }
            ],
        )

        raw_text = response.choices[0].message.content.strip()
        data = json.loads(raw_text)

        return StanceResponse(**data)

    except (json.JSONDecodeError, ValidationError) as e:
        print("JSON / VALIDATION ERROR:", raw_text)
        return StanceResponse(
            stance="neutral",
            confidence=0.0,
            explanation="Invalid model response."
        )

    except Exception as e:
        print("GROQ ERROR:", repr(e))
        return StanceResponse(
            stance="neutral",
            confidence=0.0,
            explanation="Stance service unavailable."
        )
