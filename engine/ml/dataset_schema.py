"""
dataset_schema.py
Defines the schema for the ML dataset and evaluation records.
"""
from pydantic import BaseModel
from typing import List

class MLFeatureVector(BaseModel):
    temporal_score: float
    host_score: float
    user_score: float
    process_score: float
    technique_score: float
    graph_score: float
    deterministic_score: float
    
class MLSample(BaseModel):
    scenario_id: str
    gap_id: str
    missing_rate: float
    hidden_event_id: str
    hidden_technique: str
    candidate_id: str
    candidate_technique: str
    features: MLFeatureVector
    is_positive: bool
    ml_score: float = 0.0

class MLDataset(BaseModel):
    version: str
    seed: int
    train: List[MLSample]
    val: List[MLSample]
    test: List[MLSample]
