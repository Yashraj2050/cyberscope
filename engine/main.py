from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import json
import os
from pathlib import Path
from typing import List

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import ReconstructionGap
from gap_detector import ReconstructionGapDetector
from candidate_model import ReconstructionCandidate
from candidate_generator import CandidateGenerator
from candidate_scorer import CandidateScorer
from verifier_model import ReconstructionResult
from evidence_verifier import EvidenceVerifier

app = FastAPI(title="CyberScope Engine")

# Allow frontend to communicate with it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_scenario(filename: str = "scenario_001.json"):
    import sys
    import os
    # Resolve relative to main.py or PyInstaller MEIPASS
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    
    scenario_path = base_dir / "datasets" / "demo" / filename
    
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario not found at {scenario_path}")
        
    with open(scenario_path, "r") as f:
        data = json.load(f)
        
    # ONLY load observed events. NEVER load ground truth into the operational endpoints.
    raw_observed = data.get("observed_events", [])
    
    events = []
    for raw in raw_observed:
        try:
            events.append(CyberEvent(**raw))
        except Exception as e:
            print(f"Validation error for event {raw.get('event_id')}: {e}")
            # Skip invalid events for now or raise
            raise ValueError(f"Invalid event {raw.get('event_id')}: {e}")
            
    return events

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "CyberScope Engine is running"}

@app.get("/api/v1/events", response_model=List[CyberEvent])
def get_events():
    try:
        events = load_scenario()
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel as _BaseModel

class ScenarioRequest(_BaseModel):
    scenario: str = "scenario_001.json"

@app.post("/api/v1/events", response_model=List[CyberEvent])
def post_events(body: ScenarioRequest):
    import re
    if not re.match(r'^[\w\-\.]+\.json$', body.scenario):
        raise HTTPException(status_code=400, detail="Invalid scenario filename.")
    try:
        return load_scenario(body.scenario)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{body.scenario}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class ScenarioMetadata(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    category: str
    synthetic: bool
    event_count: int

@app.get("/api/v1/scenarios", response_model=List[ScenarioMetadata])
def get_scenarios():
    import sys
    import os
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent
    
    demo_dir = base_dir / "datasets" / "demo"
    scenarios = []
    
    if demo_dir.exists():
        for file_path in demo_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    
                meta = ScenarioMetadata(
                    scenario_id=file_path.name,
                    scenario_name=data.get("scenario_name", "Unknown Scenario"),
                    description=data.get("description", "No description available."),
                    category=data.get("category", "Uncategorized"),
                    synthetic=data.get("synthetic", True),
                    event_count=len(data.get("observed_events", []))
                )
                scenarios.append(meta)
            except Exception as e:
                print(f"Error loading metadata for {file_path}: {e}")
                
    scenarios.sort(key=lambda s: s.scenario_id)
    return scenarios


@app.get("/api/v1/graph")
def get_graph():
    try:
        events = load_scenario()
        engine = AttackGraphEngine()
        engine.build(events)
        return engine.serialize()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/graph")
def post_graph(body: ScenarioRequest):
    import re
    if not re.match(r'^[\w\-\.]+\.json$', body.scenario):
        raise HTTPException(status_code=400, detail="Invalid scenario filename.")
    try:
        events = load_scenario(body.scenario)
        engine = AttackGraphEngine()
        engine.build(events)
        return engine.serialize()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{body.scenario}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/api/v1/gaps",
    response_model=List[ReconstructionGap],
    summary="Detect reconstruction gaps in the default scenario",
)
def get_gaps():
    """
    Loads the default observed telemetry scenario, builds the attack graph,
    and runs the ReconstructionGapDetector.

    SECURITY NOTE: Only observed_events are loaded. Ground truth is never
    accessible through this endpoint.

    gap_score is a PRIORITIZATION SCORE, not a validated accuracy metric.
    """
    try:
        events = load_scenario()
        graph = AttackGraphEngine()
        graph.build(events)
        detector = ReconstructionGapDetector()
        gaps = detector.detect(events, graph)
        return gaps
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DetectRequest(dict):
    """Optional: scenario filename override for POST endpoint."""
    pass


@app.post(
    "/api/v1/gaps/detect",
    response_model=List[ReconstructionGap],
    summary="Detect reconstruction gaps for a named scenario",
)
def detect_gaps(body: ScenarioRequest):
    """
    Runs gap detection for a specific scenario file.
    Accepts only the filename; path traversal is blocked.

    SECURITY NOTE: Only observed_events are loaded. Ground truth is never
    accessible through this endpoint.
    """
    import re
    # Block path traversal — only allow safe filenames
    if not re.match(r'^[\w\-\.]+\.json$', body.scenario):
        raise HTTPException(status_code=400, detail="Invalid scenario filename.")
    try:
        events = load_scenario(body.scenario)
        graph = AttackGraphEngine()
        graph.build(events)
        detector = ReconstructionGapDetector()
        gaps = detector.detect(events, graph)
        return gaps
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{body.scenario}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------
# Reconstruction candidate response schema
# -----------------------------------------------------------------------

from pydantic import BaseModel as _CandBase
from typing import Any as _Any

class GapWithCandidates(_CandBase):
    gap: ReconstructionGap
    candidates: List[ReconstructionCandidate]


def _run_full_pipeline(scenario_filename: str) -> List[GapWithCandidates]:
    """
    Shared helper: load observed events → build graph → detect gaps
    → generate candidates → score candidates.

    SECURITY NOTE: Only observed_events are ever loaded.
    Ground truth is never accessible through this pipeline.
    """
    events = load_scenario(scenario_filename)
    graph = AttackGraphEngine()
    graph.build(events)

    gaps = ReconstructionGapDetector().detect(events, graph)
    generator = CandidateGenerator()
    scorer = CandidateScorer()

    results: List[GapWithCandidates] = []
    for gap in gaps:
        raw_candidates = generator.generate(gap, events, graph)
        scored = scorer.score_and_rank(raw_candidates, gap, events, graph)
        results.append(GapWithCandidates(gap=gap, candidates=scored))

    return results


@app.get(
    "/api/v1/reconstruction/candidates",
    response_model=List[GapWithCandidates],
    summary="Full reconstruction pipeline for default scenario",
)
def get_reconstruction_candidates():
    """
    Runs the complete reconstruction pipeline for the default scenario:
    Observed events → Gap detection → Candidate generation → Scoring → Ranking.

    SECURITY NOTE: Only observed_events are loaded. Ground truth is never
    returned by this endpoint.

    candidate_score is an EVIDENCE SUPPORT SCORE, not a probability or
    accuracy metric.
    """
    try:
        return _run_full_pipeline("scenario_001.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/reconstruction/candidates",
    response_model=List[GapWithCandidates],
    summary="Full reconstruction pipeline for a named scenario",
)
def post_reconstruction_candidates(body: ScenarioRequest):
    """
    Runs the complete reconstruction pipeline for a specific scenario file.
    Path traversal is blocked; only safe filenames are accepted.

    SECURITY NOTE: Only observed_events are loaded. Ground truth is never
    returned by this endpoint.
    """
    import re
    if not re.match(r'^[\w\-\.]+\.json$', body.scenario):
        raise HTTPException(status_code=400, detail="Invalid scenario filename.")
    try:
        return _run_full_pipeline(body.scenario)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{body.scenario}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------
# Full end-to-end pipeline (Observed → Gap → Candidates → Verification)
# -----------------------------------------------------------------------

from pydantic import BaseModel as _PipeBase

class FullPipelineResult(_PipeBase):
    """
    Combines gap + candidates + verification result for one gap.
    Used by the verify endpoints.
    """
    gap: ReconstructionGap
    candidates: List[ReconstructionCandidate]
    result: ReconstructionResult


def _run_full_pipeline_with_verification(
    scenario_filename: str,
) -> List[FullPipelineResult]:
    """
    Complete reconstruction pipeline:
      Observed Telemetry
        → Normalization
        → Attack Graph
        → Gap Detection
        → Candidate Generation
        → Candidate Scoring
        → Evidence Verification
        → OBSERVED / INFERRED / UNKNOWN

    SECURITY NOTE: Only observed_events are loaded at any stage.
    Ground truth is never accessible through this pipeline.
    """
    events = load_scenario(scenario_filename)
    graph  = AttackGraphEngine()
    graph.build(events)

    gaps      = ReconstructionGapDetector().detect(events, graph)
    generator = CandidateGenerator()
    scorer    = CandidateScorer()
    verifier  = EvidenceVerifier()

    output: List[FullPipelineResult] = []
    for gap in gaps:
        candidates = generator.generate(gap, events, graph)
        scored     = scorer.score_and_rank(candidates, gap, events, graph)
        rec_result = verifier.verify(gap, scored, events, graph)
        output.append(FullPipelineResult(
            gap=gap,
            candidates=scored,
            result=rec_result,
        ))
    return output


@app.get(
    "/api/v1/reconstruction/verify",
    response_model=List[FullPipelineResult],
    summary="Full end-to-end reconstruction pipeline for default scenario",
)
def get_reconstruction_verify():
    """
    Runs the complete pipeline for the default scenario:
      Observed Telemetry → Gap → Candidates → Evidence Verification
      → OBSERVED / INFERRED / UNKNOWN

    SECURITY NOTE: Ground truth is NEVER loaded or returned.
    confidence_label and candidate_score are EVIDENCE STRENGTH indicators,
    not calibrated probabilities.
    """
    try:
        return _run_full_pipeline_with_verification("scenario_001.json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/v1/reconstruction/verify",
    response_model=List[FullPipelineResult],
    summary="Full end-to-end reconstruction pipeline for a named scenario",
)
def post_reconstruction_verify(body: ScenarioRequest):
    """
    Same as GET but accepts a scenario filename.
    Path traversal is blocked.

    SECURITY NOTE: Ground truth is NEVER loaded or returned.
    """
    import re
    if not re.match(r'^[\w\-\.]+\.json$', body.scenario):
        raise HTTPException(status_code=400, detail="Invalid scenario filename.")
    try:
        return _run_full_pipeline_with_verification(body.scenario)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{body.scenario}' not found."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="127.0.0.1", port=port)
