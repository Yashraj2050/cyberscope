from .base import LLMProvider
from .mock_provider import MockLLMProvider
from .local_provider import LocalLLMProvider
from . import config

def get_llm_provider() -> LLMProvider:
    if not config.LLM_ENABLED:
        raise RuntimeError("LLM feature is disabled in configuration.")
        
    if config.LLM_PROVIDER == "mock":
        return MockLLMProvider()
    elif config.LLM_PROVIDER == "local":
        return LocalLLMProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")
