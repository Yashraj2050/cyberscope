import pytest
from datetime import datetime, timezone
from ml.dataset_generator import DatasetGenerator
from ml.feature_extractor import FeatureExtractor
from candidate_model import ReconstructionCandidate
from gap_model import ReconstructionGap, DetectionSignals, GapStatus
from ml.predictor import CandidateRanker, RankingContext

def test_ground_truth_isolation():
    extractor = FeatureExtractor()
    cand = ReconstructionCandidate(
        candidate_id="TEST", gap_id="GAP", event_type="TEST", technique_id="T123", technique_name="TEST", description="",
        candidate_score=0.5, deterministic_score=0.5, final_ranking_score=0.5, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    gap = ReconstructionGap(gap_id="GAP", previous_event_id="E1", next_event_id="E2", start_timestamp="2026-08-20T10:00:00Z", end_timestamp="2026-08-20T10:05:00Z", temporal_gap_seconds=0, previous_event_type="", next_event_type="", detection_signals=DetectionSignals(), gap_score=0.5, status=GapStatus.OPEN)
    
    # Should work fine without GT
    feat = extractor.extract(cand, gap, [])
    assert feat.deterministic_score == 0.5
    
    # Should throw an explicit ValueError if GT is supplied
    with pytest.raises(ValueError, match="SECURITY VIOLATION: Ground truth events passed to feature extractor"):
        extractor.extract(cand, gap, [], ground_truth_events=["FAKE_EVENT"])

def test_deterministic_ranker():
    ranker = CandidateRanker()
    context = RankingContext(mode="DETERMINISTIC")
    
    c1 = ReconstructionCandidate(
        candidate_id="C1", gap_id="GAP", event_type="TEST", technique_id="T123", technique_name="TEST", description="",
        candidate_score=0.5, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    c2 = ReconstructionCandidate(
        candidate_id="C2", gap_id="GAP", event_type="TEST", technique_id="T124", technique_name="TEST", description="",
        candidate_score=0.8, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    
    ranked = ranker.rank([c1, c2], None, [], context)
    assert ranked[0].candidate_id == "C2"
    assert ranked[0].rank == 1
    assert ranked[0].rank_method == "DETERMINISTIC"
    assert ranked[0].final_ranking_score == 0.8
    
    assert ranked[1].candidate_id == "C1"
    assert ranked[1].rank == 2

def test_ml_ranker_fallback():
    # If the model file is not present or we simulate unavailability
    ranker = CandidateRanker()
    ranker.model_available = False # force fallback
    
    context = RankingContext(mode="ML")
    
    c1 = ReconstructionCandidate(
        candidate_id="C1", gap_id="GAP", event_type="TEST", technique_id="T123", technique_name="TEST", description="",
        candidate_score=0.5, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    c2 = ReconstructionCandidate(
        candidate_id="C2", gap_id="GAP", event_type="TEST", technique_id="T124", technique_name="TEST", description="",
        candidate_score=0.8, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    ranked = ranker.rank([c1, c2], None, [], context)
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2
    
    assert context.effective_mode == "DETERMINISTIC_FALLBACK"
    assert context.ml_status == "UNAVAILABLE"
    assert ranked[0].rank_method == "DETERMINISTIC_FALLBACK"

def test_hybrid_mode():
    ranker = CandidateRanker()
    if not ranker.model_available:
        pytest.skip("ML model not built, skipping hybrid logic test.")
        
    context = RankingContext(mode="HYBRID", alpha=0.5)
    
    c1 = ReconstructionCandidate(
        candidate_id="C1", gap_id="GAP", event_type="TEST", technique_id="T123", technique_name="TEST", description="",
        candidate_score=0.5, temporal_score=0.1, host_score=0.1, user_score=0.1, process_score=0.1, technique_score=0.1, graph_score=0.1, rank=1,
        supporting_features=[], contradictory_features=[]
    )
    gap = ReconstructionGap(gap_id="GAP", previous_event_id="E1", next_event_id="E2", start_timestamp=datetime.now(timezone.utc), end_timestamp=datetime.now(timezone.utc), temporal_gap_seconds=0, previous_event_type="", next_event_type="", detection_signals=DetectionSignals(), gap_score=0.5, status=GapStatus.OPEN)

    ranked = ranker.rank([c1], gap, [], context)
    assert ranked[0].rank_method == "HYBRID"
    assert ranked[0].final_ranking_score != ranked[0].deterministic_score
    assert context.effective_mode == "HYBRID"
