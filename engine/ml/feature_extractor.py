"""
feature_extractor.py
Feature extractor for ML training and inference.
Takes observed events, gap, and a candidate, and returns a numeric feature vector.
"""
from typing import List, Optional
from models import CyberEvent
from gap_model import ReconstructionGap
from candidate_model import ReconstructionCandidate
from .dataset_schema import MLFeatureVector

class FeatureExtractor:
    def extract(self, 
                candidate: ReconstructionCandidate, 
                gap: ReconstructionGap, 
                observed_events: List[CyberEvent],
                ground_truth_events: Optional[List[CyberEvent]] = None) -> MLFeatureVector:
        """
        Extract features from candidate and observed evidence.
        CRITICAL SECURITY INVARIANT: ground_truth_events MUST NEVER be passed during extraction.
        """
        if ground_truth_events is not None:
            raise ValueError("SECURITY VIOLATION: Ground truth events passed to feature extractor. Leakage prevented.")
            
        # For our baseline ML, we will use the existing dimension scores calculated by CandidateScorer
        # as our raw features, because they encapsulate the graph/temporal distance logic already.
        
        return MLFeatureVector(
            temporal_score=candidate.temporal_score,
            host_score=candidate.host_score,
            user_score=candidate.user_score,
            process_score=candidate.process_score,
            technique_score=candidate.technique_score,
            graph_score=candidate.graph_score,
            deterministic_score=candidate.candidate_score
        )
