"""
predictor.py
Unified CandidateRanker supporting DETERMINISTIC, ML, and HYBRID modes with robust fallback.
"""
import joblib
import warnings
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

from models import CyberEvent
from gap_model import ReconstructionGap
from candidate_model import ReconstructionCandidate
from .config import MODELS_DIR, MODEL_FILENAME, METADATA_FILENAME
from .feature_extractor import FeatureExtractor

logger = logging.getLogger("cyberscope.ml.predictor")

class RankingContext:
    def __init__(self, mode: str = "DETERMINISTIC", alpha: float = 0.70):
        self.requested_mode = mode.upper()
        self.hybrid_alpha = alpha
        
        self.effective_mode = self.requested_mode
        self.ml_status = "N/A"
        self.reason_code = None
        self.model_version = None
        self.feature_schema_version = None
        self.dataset_version = None
        self.ml_model_available = False
        self.inference_timestamp = None

class CandidateRanker:
    def __init__(self):
        self.model = None
        self.metadata = {}
        self.extractor = FeatureExtractor()
        self.model_available = False
        
        self._load_model()

    def _load_model(self):
        model_path = MODELS_DIR / MODEL_FILENAME
        meta_path = MODELS_DIR / METADATA_FILENAME
        
        if not model_path.exists() or not meta_path.exists():
            logger.warning(f"ML Model or metadata not found in {MODELS_DIR}. ML ranking unavailable.")
            return

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                self.model = joblib.load(model_path)
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
            self.model_available = True
            logger.info(f"Loaded ML model version {self.metadata.get('model_version')}")
        except Exception as e:
            logger.error(f"ML Ranker initialization failed, model unavailable: {e}")
            self.model = None
            self.model_available = False

    def rank(self, candidates: List[ReconstructionCandidate], gap: ReconstructionGap, observed_events: List[CyberEvent], context: RankingContext) -> List[ReconstructionCandidate]:
        # Handle Fallback
        if context.requested_mode in ["ML", "HYBRID"] and not self.model_available:
            logger.warning(f"Requested {context.requested_mode} but ML model is unavailable. Falling back to DETERMINISTIC.")
            context.effective_mode = "DETERMINISTIC_FALLBACK"
            context.ml_status = "UNAVAILABLE"
            context.reason_code = "MODEL_LOAD_FAILURE"
            context.ml_model_available = False
        elif context.requested_mode in ["ML", "HYBRID"]:
            context.ml_status = "AVAILABLE"
            context.ml_model_available = True
            context.model_version = self.metadata.get("model_version")
            context.feature_schema_version = self.metadata.get("feature_schema_version")
            context.dataset_version = self.metadata.get("dataset_version")
            context.inference_timestamp = datetime.now(timezone.utc)
            
        scored_candidates = []
        for cand in candidates:
            # Deterministic Score is assumed to be in candidate_score currently, or we map it to deterministic_score
            det_score = cand.candidate_score
            
            ml_score = None
            final_score = det_score
            
            if context.effective_mode in ["ML", "HYBRID"]:
                try:
                    features = self.extractor.extract(cand, gap, observed_events)
                    X = [[
                        features.temporal_score,
                        features.host_score,
                        features.user_score,
                        features.process_score,
                        features.technique_score,
                        features.graph_score,
                        features.deterministic_score
                    ]]
                    ml_score = float(self.model.predict_proba(X)[0][1])
                except Exception as e:
                    logger.error(f"Inference exception for candidate {cand.candidate_id}: {e}")
                    # Safe fallback for this candidate
                    context.effective_mode = "DETERMINISTIC_FALLBACK"
                    context.ml_status = "UNAVAILABLE"
                    context.reason_code = "INFERENCE_EXCEPTION"
                    ml_score = None
                    final_score = det_score
            
            if context.effective_mode == "ML" and ml_score is not None:
                final_score = ml_score
            elif context.effective_mode == "HYBRID" and ml_score is not None:
                final_score = context.hybrid_alpha * det_score + (1.0 - context.hybrid_alpha) * ml_score
                
            updated = cand.model_copy(update={
                "deterministic_score": det_score,
                "ml_ranking_score": ml_score,
                "final_ranking_score": final_score,
                "candidate_score": final_score,  # Preserve existing integration assumptions where applicable
                "rank_method": context.effective_mode,
                "model_version": context.model_version
            })
            scored_candidates.append(updated)
            
        # Sort and assign ranks
        ranked = sorted(scored_candidates, key=lambda c: c.final_ranking_score, reverse=True)
        final_ranked = []
        current_rank = 1
        for i, c in enumerate(ranked):
            if i > 0 and c.final_ranking_score < ranked[i - 1].final_ranking_score:
                current_rank = i + 1
            final_ranked.append(c.model_copy(update={"rank": current_rank}))
            
        return final_ranked
