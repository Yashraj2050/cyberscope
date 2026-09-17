from abc import ABC, abstractmethod
from .context import InvestigationLLMContext
from .parser import StructuredLLMResponse

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, context: InvestigationLLMContext, instruction: str) -> StructuredLLMResponse:
        pass
        
    @abstractmethod
    def get_status(self) -> dict:
        pass
