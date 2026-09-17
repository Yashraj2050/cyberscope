"""
baseline.py
Evaluates deterministic baseline metrics (Top-1, Top-3, MRR) for the ML dataset.
"""
from typing import List, Dict
from .dataset_schema import MLSample

class MetricsEvaluator:
    def evaluate(self, samples: List[MLSample], score_key: str = "deterministic_score") -> Dict[str, float]:
        """
        Evaluate metrics for a set of samples. 
        Samples must be grouped by gap_id to calculate ranking metrics correctly.
        """
        # Group by gap_id
        gaps: Dict[str, List[MLSample]] = {}
        for s in samples:
            if s.gap_id not in gaps:
                gaps[s.gap_id] = []
            gaps[s.gap_id].append(s)
            
        mrr_sum = 0.0
        top1_hits = 0
        top3_hits = 0
        total_gaps = len(gaps)
        
        if total_gaps == 0:
            return {"MRR": 0.0, "Top-1": 0.0, "Top-3": 0.0}
            
        for gap_id, cand_samples in gaps.items():
            # Sort descending by the requested score
            # In MLSample, the deterministic score is in features.deterministic_score
            # If score_key is "ml_score", we assume the caller appended it dynamically, or we use a lambda.
            # We'll just pass a lambda or property map.
            
            # To handle both static and dynamic scores:
            def get_score(s: MLSample):
                if score_key == "deterministic_score":
                    return s.features.deterministic_score
                return getattr(s, score_key, 0.0)
                
            sorted_cands = sorted(cand_samples, key=get_score, reverse=True)
            
            # Find the rank of the first positive candidate
            rank = 0
            for i, c in enumerate(sorted_cands):
                if c.is_positive:
                    rank = i + 1
                    break
                    
            if rank > 0:
                mrr_sum += 1.0 / rank
                if rank == 1:
                    top1_hits += 1
                if rank <= 3:
                    top3_hits += 1
                    
        return {
            "MRR": round(mrr_sum / total_gaps, 4),
            "Top-1": round(top1_hits / total_gaps, 4),
            "Top-3": round(top3_hits / total_gaps, 4)
        }

class BaselineEvaluator:
    def __init__(self):
        self.metrics_evaluator = MetricsEvaluator()
        
    def evaluate_baseline(self, samples: List[MLSample]) -> Dict[str, float]:
        return self.metrics_evaluator.evaluate(samples, score_key="deterministic_score")
