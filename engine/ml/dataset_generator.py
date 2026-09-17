"""
dataset_generator.py
Generates a controlled synthetic dataset with variations in missing telemetry.
"""
import random
import uuid
import copy
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

from models import CyberEvent
from gap_detector import ReconstructionGapDetector, TECHNIQUE_STAGE_MAP
from candidate_generator import CandidateGenerator
from candidate_scorer import CandidateScorer
from candidate_model import ReconstructionCandidate
from graph_engine import AttackGraphEngine
from .config import SEED, TRAIN_RATIO, VAL_RATIO, TEST_RATIO
from .dataset_schema import MLDataset, MLSample, MLFeatureVector
from .feature_extractor import FeatureExtractor

# Some basic techniques for synthetic generation
TECHNIQUES = [
    "T1190", "T1059.001", "T1059.003", "T1078", "T1003", "T1003.001",
    "T1558.003", "T1021.002", "T1021.001", "T1569.002", "T1047", "T1484.001"
]

class DatasetGenerator:
    def __init__(self, seed: int = SEED):
        self.seed = seed
        random.seed(self.seed)
        self.extractor = FeatureExtractor()
        
    def generate_synthetic_attack_path(self, num_events: int = 5) -> List[CyberEvent]:
        events = []
        base_time = datetime(2026, 8, 20, 10, 0, 0)
        current_time = base_time
        
        host_id = f"HOST-{random.choice(['A', 'B', 'C'])}"
        user_id = f"USER-{random.randint(1, 5)}"
        process_id = f"PROC-{random.randint(1000, 9999)}"
        
        # Ensure the path makes logical stage transitions
        sorted_techniques = sorted(TECHNIQUES, key=lambda t: TECHNIQUE_STAGE_MAP.get(t, 5))
        path_techniques = random.sample(sorted_techniques, num_events)
        path_techniques.sort(key=lambda t: TECHNIQUE_STAGE_MAP.get(t, 5))
        
        for i in range(num_events):
            # Introduce small variations occasionally
            if random.random() < 0.2:
                host_id = f"HOST-{random.choice(['A', 'B', 'C'])}"
            if random.random() < 0.2:
                user_id = f"USER-{random.randint(1, 5)}"
            if random.random() < 0.2:
                process_id = f"PROC-{random.randint(1000, 9999)}"
                
            current_time += timedelta(minutes=random.randint(1, 15))
            
            ev = CyberEvent(
                event_id=f"EVT-SYN-{uuid.uuid4().hex[:8]}",
                timestamp=current_time.isoformat() + "Z",
                host_id=host_id,
                user_id=user_id,
                process_name="synthetic.exe",
                process_id=process_id,
                event_type="SyntheticEvent",
                source="SyntheticSource",
                technique_id=path_techniques[i],
                technique_name=f"Synthetic {path_techniques[i]}",
                raw_data={}
            )
            events.append(ev)
        return events

    def generate(self, num_scenarios: int = 100) -> MLDataset:
        random.seed(self.seed)
        
        all_samples = []
        
        # Generate scenarios
        for s_idx in range(num_scenarios):
            scenario_id = f"SCENARIO-{s_idx:04d}"
            
            # 1. Base path
            path_len = random.randint(4, 8)
            full_path = self.generate_synthetic_attack_path(path_len)
            
            # Create a sample for missing rates: 10%, 20%, 30%, 40%
            # For simplicity in this synthetic generator, we will just pick 1 event to hide per iteration
            # to simulate a gap, and label the missing rate abstractly or calculate it.
            
            for missing_rate in [0.0, 0.1, 0.2, 0.3, 0.4]:
                if missing_rate == 0.0:
                    continue # No gap to reconstruct from missing telemetry
                    
                # Hide one event (not first or last to ensure gap is bounded)
                hidden_idx = random.randint(1, len(full_path) - 2)
                hidden_event = full_path[hidden_idx]
                
                observed_events = full_path[:hidden_idx] + full_path[hidden_idx+1:]
                
                # Run deterministic engine on observed
                graph = AttackGraphEngine()
                graph.build(observed_events)
                gaps = ReconstructionGapDetector().detect(observed_events, graph)
                
                # Match the gap covering our hidden event
                target_gap = None
                for g in gaps:
                    if g.previous_event_id == full_path[hidden_idx-1].event_id and \
                       g.next_event_id == full_path[hidden_idx+1].event_id:
                        target_gap = g
                        break
                        
                if not target_gap:
                    continue
                    
                # Generate and score candidates
                generator = CandidateGenerator()
                scorer = CandidateScorer()
                
                raw_candidates = generator.generate(target_gap, observed_events, graph)
                
                # Inject the positive candidate if it wasn't generated (for dataset balance)
                has_positive = any(c.technique_id == hidden_event.technique_id for c in raw_candidates)
                if not has_positive:
                    # Create the positive candidate manually so the model has something to learn
                    pos_c = ReconstructionCandidate(
                        candidate_id=f"CAND-POS-{uuid.uuid4().hex[:8]}",
                        gap_id=target_gap.gap_id,
                        event_type="SyntheticAccess",
                        technique_id=hidden_event.technique_id,
                        technique_name=hidden_event.technique_name,
                        description="Synthetic positive candidate",
                        candidate_score=0.0,
                        temporal_score=0.0,
                        host_score=0.0,
                        user_score=0.0,
                        process_score=0.0,
                        technique_score=0.0,
                        graph_score=0.0,
                        rank=0,
                        supporting_features=[],
                        contradictory_features=[]
                    )
                    raw_candidates.append(pos_c)
                
                # Score them
                scored_candidates = scorer.score_and_rank(raw_candidates, target_gap, observed_events, graph)
                
                # Extract features for each candidate and build samples
                for cand in scored_candidates:
                    features = self.extractor.extract(cand, target_gap, observed_events)
                    is_positive = (cand.technique_id == hidden_event.technique_id)
                    
                    sample = MLSample(
                        scenario_id=scenario_id,
                        gap_id=target_gap.gap_id,
                        missing_rate=missing_rate,
                        hidden_event_id=hidden_event.event_id,
                        hidden_technique=hidden_event.technique_id,
                        candidate_id=cand.candidate_id,
                        candidate_technique=cand.technique_id,
                        features=features,
                        is_positive=is_positive
                    )
                    all_samples.append(sample)
                    
        # Strict Split by scenario_id
        scenario_ids = list(set(s.scenario_id for s in all_samples))
        scenario_ids.sort()
        random.shuffle(scenario_ids)
        
        train_end = int(len(scenario_ids) * TRAIN_RATIO)
        val_end = train_end + int(len(scenario_ids) * VAL_RATIO)
        
        train_scenarios = set(scenario_ids[:train_end])
        val_scenarios = set(scenario_ids[train_end:val_end])
        test_scenarios = set(scenario_ids[val_end:])
        
        train_samples = [s for s in all_samples if s.scenario_id in train_scenarios]
        val_samples = [s for s in all_samples if s.scenario_id in val_scenarios]
        test_samples = [s for s in all_samples if s.scenario_id in test_scenarios]
        
        return MLDataset(
            version="1.0",
            seed=self.seed,
            train=train_samples,
            val=val_samples,
            test=test_samples
        )
