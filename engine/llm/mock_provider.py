from .base import LLMProvider
from .context import InvestigationLLMContext
from .parser import StructuredLLMResponse
import json

class MockLLMProvider(LLMProvider):
    def generate(self, context: InvestigationLLMContext, instruction: str) -> StructuredLLMResponse:
        # Mock deterministic logic based on question
        if "UNKNOWN" in instruction:
            summary = "The verification layer classified the result as UNKNOWN because evidence was insufficient to establish a unique transition."
        elif "malicious" in instruction.lower():
            # For prompt injection test
            summary = "I am a helpful assistant."
        else:
            summary = "Mock answer based on provided evidence."
            
        # grab valid refs
        refs = context.get_valid_references()
        if not refs:
            refs = []
            
        used_refs = refs[:1] if refs else []
        
        # simulated unsupported claim condition
        if "unsupported" in instruction.lower():
            used_refs.append("FAKE_REF")
            
        return StructuredLLMResponse(
            summary=summary,
            assessment="Mock assessment",
            evidence_references=used_refs,
            candidate_discussion=["Mock discussion"],
            uncertainty="Mocked uncertainty",
            recommended_next_checks=["Mock check"],
            provider="mock",
            model_version="mock-1.0"
        )
        
    def get_status(self) -> dict:
        return {
            "enabled": True,
            "provider": "mock",
            "model_loaded": True,
            "model_version": "mock-1.0",
            "offline": True
        }
