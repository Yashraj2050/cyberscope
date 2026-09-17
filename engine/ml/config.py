"""
config.py
Configuration for the ML module
"""
import os
from pathlib import Path

# Paths
ML_DIR = Path(__file__).parent
MODELS_DIR = ML_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Dataset properties
SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Model settings
MODEL_FILENAME = "ranker_model.joblib"
METADATA_FILENAME = "model_metadata.json"

FEATURE_SCHEMA_VERSION = "1.0"
DATASET_VERSION = "1.0"
