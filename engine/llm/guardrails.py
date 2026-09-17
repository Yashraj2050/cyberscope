from .context import InvestigationLLMContext
from .parser import StructuredLLMResponse

class GuardrailViolation(Exception):
    pass

class HallucinationGuardrail:
    def validate(self, response: StructuredLLMResponse, context: InvestigationLLMContext) -> StructuredLLMResponse:
        valid_refs = set(context.get_valid_references())
        
        for ref in response.evidence_references:
            if ref not in valid_refs:
                raise GuardrailViolation(f"LLM hallucinated evidence reference: {ref}")
            
        return response
