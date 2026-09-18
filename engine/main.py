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

from api import health_router, cases_router

app.include_router(health_router, prefix="/api")
app.include_router(cases_router, prefix="/api/v1/cases")

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
    ranker_mode: str = "DETERMINISTIC"
    hybrid_alpha: float = 0.70

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
from typing import Any as _Any, Optional

from models.domain import AnalysisMetadata

class GapWithCandidates(_CandBase):
    gap: ReconstructionGap
    candidates: List[ReconstructionCandidate]
    analysis_metadata: Optional[AnalysisMetadata] = None


def _run_full_pipeline(scenario_filename: str, ranker_mode: str = "DETERMINISTIC", hybrid_alpha: float = 0.70) -> List[GapWithCandidates]:
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
    
    from ml.predictor import CandidateRanker, RankingContext
    ranker = CandidateRanker()
    rank_ctx = RankingContext(mode=ranker_mode, alpha=hybrid_alpha)

    results: List[GapWithCandidates] = []
    
    meta = AnalysisMetadata(
        ranker_mode=rank_ctx.effective_mode,
        hybrid_alpha=rank_ctx.hybrid_alpha,
        ml_model_available=rank_ctx.ml_model_available,
        ml_model_version=rank_ctx.model_version,
        ml_feature_schema_version=rank_ctx.feature_schema_version,
        ml_dataset_version=rank_ctx.dataset_version,
        ml_inference_timestamp=rank_ctx.inference_timestamp,
        ml_status=rank_ctx.ml_status,
        ml_reason_code=rank_ctx.reason_code
    )

    for gap in gaps:
        raw_candidates = generator.generate(gap, events, graph)
        scored = scorer.score_and_rank(raw_candidates, gap, events, graph)
        ranked = ranker.rank(scored, gap, events, rank_ctx)
        results.append(GapWithCandidates(gap=gap, candidates=ranked, analysis_metadata=meta))

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
        return _run_full_pipeline("scenario_001.json", ranker_mode="DETERMINISTIC", hybrid_alpha=0.70)
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
        return _run_full_pipeline(body.scenario, ranker_mode=body.ranker_mode, hybrid_alpha=body.hybrid_alpha)
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
    analysis_metadata: Optional[AnalysisMetadata] = None


def _run_full_pipeline_with_verification(
    scenario_filename: str,
    ranker_mode: str = "DETERMINISTIC",
    hybrid_alpha: float = 0.70
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
    
    from ml.predictor import CandidateRanker, RankingContext
    ranker = CandidateRanker()
    rank_ctx = RankingContext(mode=ranker_mode, alpha=hybrid_alpha)

    output: List[FullPipelineResult] = []
    
    meta = AnalysisMetadata(
        ranker_mode=rank_ctx.effective_mode,
        hybrid_alpha=rank_ctx.hybrid_alpha,
        ml_model_available=rank_ctx.ml_model_available,
        ml_model_version=rank_ctx.model_version,
        ml_feature_schema_version=rank_ctx.feature_schema_version,
        ml_dataset_version=rank_ctx.dataset_version,
        ml_inference_timestamp=rank_ctx.inference_timestamp,
        ml_status=rank_ctx.ml_status,
        ml_reason_code=rank_ctx.reason_code
    )

    for gap in gaps:
        candidates = generator.generate(gap, events, graph)
        scored     = scorer.score_and_rank(candidates, gap, events, graph)
        ranked     = ranker.rank(scored, gap, events, rank_ctx)
        rec_result = verifier.verify(gap, ranked, events, graph)
        output.append(FullPipelineResult(
            gap=gap,
            candidates=ranked,
            result=rec_result,
            analysis_metadata=meta
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
        return _run_full_pipeline_with_verification("scenario_001.json", ranker_mode="DETERMINISTIC", hybrid_alpha=0.70)
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
        return _run_full_pipeline_with_verification(body.scenario, ranker_mode=body.ranker_mode, hybrid_alpha=body.hybrid_alpha)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{body.scenario}' not found."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------
# Local LLM Integration
# -----------------------------------------------------------------------

from llm import get_llm_provider, InvestigationLLMContext, EvidenceFact, InvestigationContextBuilder, HallucinationGuardrail
from llm.audit import log_llm_request
import time

@app.get("/api/v1/llm/status", summary="Get Local LLM status")
def get_llm_status():
    try:
        provider = get_llm_provider()
        return provider.get_status()
    except Exception as e:
        return {
            "enabled": False,
            "provider": None,
            "model_loaded": False,
            "model_version": None,
            "offline": True,
            "error": str(e)
        }

class ExplainRequest(BaseModel):
    question: Optional[str] = None

@app.post("/api/v1/investigations/{case_id}/ai/explain", summary="Generate advisory explanation using Local LLM")
def explain_investigation(case_id: str, request: ExplainRequest = None):
    """
    Given a case_id (treated as scenario filename for now), run deterministic pipeline,
    build the evidence context, and query the local LLM for a structured advisory explanation.
    """
    import re
    safe_scenario = case_id if case_id.endswith(".json") else f"{case_id}.json"
    if not re.match(r'^[\w\-\.]+\.json$', safe_scenario):
        raise HTTPException(status_code=400, detail="Invalid case/scenario ID.")
        
    start_time = time.time()
    try:
        results = _run_full_pipeline_with_verification(safe_scenario)
        if not results:
            raise HTTPException(status_code=404, detail="No investigation results found.")
            
        result = results[0]
        
        # Build strict context
        builder = InvestigationContextBuilder()
        ctx = builder.build(
            case_id=case_id,
            investigation_id=f"INV-{case_id}",
            gap_result=result.gap.model_dump(),
            verification_result=result.result.model_dump(),
            candidates=[c.model_dump() for c in result.candidates]
        )
        
        provider = get_llm_provider()
        status = provider.get_status()
        if not status.get("available", False):
            raise HTTPException(status_code=503, detail="LLM_UNAVAILABLE: Configured model is missing or invalid.")
            
        question = request.question if (request and request.question) else "Explain the investigation outcome based solely on the provided context."
        llm_response = provider.generate(ctx, question)
        
        guardrail = HallucinationGuardrail()
        validated_response = guardrail.validate(llm_response, ctx)
        
        latency = time.time() - start_time
        
        # Audit logging
        log_llm_request(
            case_id=ctx.case_id,
            investigation_id=ctx.investigation_id,
            gap_id=ctx.gap_id,
            model_id=status.get("model_id", "unknown"),
            model_hash=status.get("model_hash", "unknown"),
            context_schema_version=ctx.context_schema_version,
            latency=latency,
            output_validation_status="VALID",
            evidence_references=validated_response.evidence_references
        )
        
        return validated_response.model_dump()
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Scenario '{safe_scenario}' not found.")
    except Exception as e:
        latency = time.time() - start_time
        try:
            status = get_llm_provider().get_status()
        except:
            status = {}
            
        log_llm_request(
            case_id=case_id,
            investigation_id=f"INV-{case_id}",
            gap_id="unknown",
            model_id=status.get("model_id", "unknown"),
            model_hash=status.get("model_hash", "unknown"),
            context_schema_version="1.0.0",
            latency=latency,
            output_validation_status=f"INVALID: {e}",
            evidence_references=[]
        )
        
        if "LLM_UNAVAILABLE" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        if "LLM hallucinated evidence reference" in str(e) or "LLM_RESPONSE_INVALID" in str(e):
            raise HTTPException(status_code=422, detail=f"LLM Parsing/Guardrail Failure: {e}")
        
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="127.0.0.1", port=port)
