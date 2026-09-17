"""
evaluator.py
Provides manual evaluation utilities without retraining.
"""
import joblib
import json
from .config import MODELS_DIR, MODEL_FILENAME, METADATA_FILENAME

class ModelEvaluator:
    def load_model(self):
        try:
            model = joblib.load(MODELS_DIR / MODEL_FILENAME)
            with open(MODELS_DIR / METADATA_FILENAME, "r") as f:
                metadata = json.load(f)
            return model, metadata
        except Exception as e:
            print(f"Error loading model: {e}")
            return None, None
            
if __name__ == "__main__":
    evaluator = ModelEvaluator()
    model, meta = evaluator.load_model()
    if meta:
        print("Model loaded successfully.")
        print(f"Metadata: {json.dumps(meta, indent=2)}")
