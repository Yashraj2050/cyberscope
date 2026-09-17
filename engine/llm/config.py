"""
config.py
Configuration for Local LLM
"""

import os
from pathlib import Path

LLM_DIR = Path(__file__).parent
MODELS_DIR = LLM_DIR.parent.parent / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "llama-investigator-v1.gguf"

LLM_ENABLED = os.getenv("CYBERSCOPE_LLM_ENABLED", "true").lower() == "true"
LLM_PROVIDER = os.getenv("CYBERSCOPE_LLM_PROVIDER", "mock") # defaulting to mock for tests unless overridden
LLM_TEMPERATURE = 0.0 # Deterministic reasoning
LLM_MAX_TOKENS = 1024
