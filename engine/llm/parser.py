import json
from pydantic import BaseModel, Field
from typing import List

class StructuredLLMResponse(BaseModel):
    summary: str
    assessment: str
    evidence_references: List[str] = Field(default_factory=list)
    candidate_discussion: List[str] = Field(default_factory=list)
    uncertainty: str = ""
    recommended_next_checks: List[str] = Field(default_factory=list)
    provider: str = ""
    model_version: str = ""

def parse_llm_response(raw_text: str) -> StructuredLLMResponse:
    try:
        # attempt to extract json if wrapped in markdown blocks
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        return StructuredLLMResponse(**data)
    except Exception as e:
        raise ValueError("LLM_RESPONSE_INVALID")
