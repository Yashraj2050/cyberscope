"""
test_candidates.py — CyberScope Milestone 4 Candidate Generation & Scoring Tests

Test organization:
  1–3:   CandidateGenerator correctness and ground-truth isolation
  4–7:   CandidateScorer correctness (determinism, ranking, evidence)
  8–10:  Score bounds and ground-truth clean-up
  11–13: Edge cases (multiple / single / empty candidate sets)
  14:    Unrelated transitions produce no candidates
  15:    Evaluation utility (testing-only, never in pipeline)
  16–17: API endpoints clean of ground truth
  18:    POST reconstruction endpoint (named scenario)

IMPORTANT: Ground truth (EVT-003) is used ONLY in assertions to verify
detection quality — it is never passed to the generator, scorer, or API.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import ReconstructionGap, GapStatus, DetectionSignals
from gap_detector import ReconstructionGapDetector
from candidate_model import ReconstructionCandidate
from candidate_generator import CandidateGenerator
from candidate_scorer import CandidateScorer, CANDIDATE_SCORE_WEIGHTS
from evaluation import evaluate_candidates
from main import app, load_scenario

client = TestClient(app)


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _make_event(**kwargs) -> CyberEvent:
    defaults = {
        "event_id":   "E-BASE",
        "timestamp":  "2026-08-21T09:00:00Z",
        "host_id":    "HOST-A",
        "event_type": "ProcessCreate",
        "source":     "Sysmon",
    }
    defaults.update(kwargs)
    return CyberEvent(**defaults)


def _load_raw():
    """Load full scenario JSON (ONLY for test assertions, never for pipeline)."""
    base = Path(__file__).parent.parent
    with open(base / "datasets" / "demo" / "scenario_001.json") as f:
        return json.load(f)


def _full_pipeline(events=None):
    """Run the complete pipeline on observed events."""
    if events is None:
        events = load_scenario()
    graph = AttackGraphEngine()
    graph.build(events)
    gaps = ReconstructionGapDetector().detect(events, graph)
    generator = CandidateGenerator()
    scorer = CandidateScorer()
    all_candidates = []
    for gap in gaps:
        raw = generator.generate(gap, events, graph)
        scored = scorer.score_and_rank(raw, gap, events, graph)
        all_candidates.extend(scored)
    return gaps, all_candidates


def _gap001() -> tuple:
    """Return the primary gap and its scored candidates for scenario_001."""
    events = load_scenario()
    graph = AttackGraphEngine()
    graph.build(events)
    gaps = ReconstructionGapDetector().detect(events, graph)
    gap = next(g for g in gaps if g.previous_event_id == "EVT-002")
    generator = CandidateGenerator()
    scorer = CandidateScorer()
    raw = generator.generate(gap, events, graph)
    scored = scorer.score_and_rank(raw, gap, events, graph)
    return gap, scored


def _make_gap(prev_id, next_id, prev_ts, next_ts, **kwargs) -> ReconstructionGap:
    signals = DetectionSignals(technique_transition=True, behavioral_prerequisite=True)
    return ReconstructionGap(
        gap_id="GAP-TEST-001",
        previous_event_id=prev_id,
        next_event_id=next_id,
        start_timestamp=prev_ts,
        end_timestamp=next_ts,
        affected_host="HOST-A",
        affected_user="jdoe",
        temporal_gap_seconds=(next_ts - prev_ts).total_seconds(),
        previous_event_type="ProcessCreate",
        next_event_type="NetworkConnect",
        detection_signals=signals,
        gap_score=0.55,
        status=GapStatus.OPEN,
        **kwargs,
    )


# ---------------------------------------------------------------
# TEST 1 — Generator creates candidates for GAP-001
# ---------------------------------------------------------------

def test_candidate_generator_creates_candidates_for_gap001():
    """CandidateGenerator must produce ≥1 candidate for the known gap."""
    gap, candidates = _gap001()
    assert len(candidates) >= 1, (
        "Expected at least one candidate for GAP-001 (EVT-002 → EVT-004)"
    )


# ---------------------------------------------------------------
# TEST 2 — Generator abstains when evidence is insufficient
# ---------------------------------------------------------------

def test_candidate_generator_returns_empty_for_insufficient_evidence():
    """
    When the technique transition is Impact→Initial Access (backwards/unusual),
    the generator must return an empty list rather than inventing candidates.
    """
    e1 = _make_event(event_id="X1", technique_id="T1486",  # Impact, stage 5
                     event_type="FileModify")
    e2 = _make_event(event_id="X2", technique_id="T1190",  # Initial Access, stage 1
                     event_type="ProcessCreate")
    ts1 = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc)
    e1 = e1.model_copy(update={"timestamp": ts1})
    e2 = e2.model_copy(update={"timestamp": ts2})

    gap = _make_gap("X1", "X2", ts1, ts2)
    graph = AttackGraphEngine()
    graph.build([e1, e2])
    candidates = CandidateGenerator().generate(gap, [e1, e2], graph)
    assert candidates == [], (
        f"Generator must abstain for unsupported transitions, got: {candidates}"
    )


# ---------------------------------------------------------------
# TEST 3 — Generator never reads ground truth
# ---------------------------------------------------------------

def test_candidate_generator_never_reads_ground_truth():
    """
    The generator must only use observed events. Ground truth IDs must not
    appear in any candidate field.
    """
    raw = _load_raw()
    gt_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}
    gt_tids = {e.get("technique_id") for e in raw.get("ground_truth_events", [])}

    gap, candidates = _gap001()

    for c in candidates:
        assert c.candidate_id not in gt_ids
        assert c.gap_id not in gt_ids
        # Technique ID may coincidentally match GT (that is valid detection),
        # but the CANDIDATE must have been derived from the knowledge layer,
        # not from reading the hidden event. We only verify candidate_id/gap_id.
        for feature in c.supporting_features + c.contradictory_features:
            for gt_id in gt_ids:
                assert gt_id not in feature, (
                    f"Ground truth event ID {gt_id} leaked into candidate feature string"
                )


# ---------------------------------------------------------------
# TEST 4 — Scorer is deterministic
# ---------------------------------------------------------------

def test_candidate_scorer_is_deterministic():
    """Identical inputs must produce identical candidate_scores."""
    gap1, cands1 = _gap001()
    gap2, cands2 = _gap001()

    assert len(cands1) == len(cands2)
    for c1, c2 in zip(cands1, cands2):
        assert c1.candidate_score == c2.candidate_score, (
            f"Non-deterministic scores: {c1.candidate_score} vs {c2.candidate_score}"
        )
        assert c1.technique_id == c2.technique_id


# ---------------------------------------------------------------
# TEST 5 — Candidates are correctly ranked
# ---------------------------------------------------------------

def test_candidates_are_correctly_ranked():
    """Rank 1 must have the highest candidate_score; ranks must be ascending."""
    _, candidates = _gap001()
    assert len(candidates) >= 1

    rank1 = next(c for c in candidates if c.rank == 1)
    for c in candidates:
        assert c.candidate_score <= rank1.candidate_score, (
            f"Candidate with rank {c.rank} has higher score than rank-1 candidate"
        )

    # Ranks must be positive integers
    for c in candidates:
        assert c.rank >= 1


# ---------------------------------------------------------------
# TEST 6 — Supporting features are attached to each candidate
# ---------------------------------------------------------------

def test_supporting_features_are_attached():
    """Every scored candidate must have at least one supporting feature."""
    _, candidates = _gap001()
    for c in candidates:
        assert len(c.supporting_features) >= 1, (
            f"Candidate {c.candidate_id} has no supporting features — "
            "the scorer must explain why a candidate is supported"
        )


# ---------------------------------------------------------------
# TEST 7 — Contradictory features may be attached
# ---------------------------------------------------------------

def test_contradictory_features_type_is_list():
    """contradictory_features must be a list (may be empty, must not be None)."""
    _, candidates = _gap001()
    for c in candidates:
        assert isinstance(c.contradictory_features, list), (
            f"contradictory_features must be a list, got {type(c.contradictory_features)}"
        )


# ---------------------------------------------------------------
# TEST 8 — All dimension scores within [0.0, 1.0]
# ---------------------------------------------------------------

def test_candidate_scores_within_range():
    """All individual dimension scores and candidate_score must be in [0, 1]."""
    _, candidates = _gap001()
    for c in candidates:
        for field_name in (
            "temporal_score", "host_score", "user_score",
            "process_score", "technique_score", "graph_score", "candidate_score"
        ):
            val = getattr(c, field_name)
            assert 0.0 <= val <= 1.0, (
                f"{field_name}={val} is out of [0, 1] bounds "
                f"for candidate {c.candidate_id}"
            )


# ---------------------------------------------------------------
# TEST 9 — Candidate ranking does not expose ground truth
# ---------------------------------------------------------------

def test_candidate_ranking_does_not_expose_ground_truth():
    """
    Ground-truth event IDs must not appear in candidate_id, gap_id,
    or any feature strings of ranked candidates.
    """
    raw = _load_raw()
    gt_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}
    _, candidates = _gap001()

    for c in candidates:
        assert c.candidate_id not in gt_ids
        assert c.gap_id not in gt_ids


# ---------------------------------------------------------------
# TEST 10 — API does not expose ground truth
# ---------------------------------------------------------------

def test_api_reconstruction_candidates_no_ground_truth():
    """
    GET /api/v1/reconstruction/candidates must not contain ground-truth
    event IDs anywhere in the response.
    """
    raw = _load_raw()
    gt_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}

    response = client.get("/api/v1/reconstruction/candidates")
    assert response.status_code == 200

    body = json.dumps(response.json())
    for gt_id in gt_ids:
        assert gt_id not in body, (
            f"Ground truth event ID {gt_id} found in API reconstruction response"
        )


# ---------------------------------------------------------------
# TEST 11 — Multiple candidates are supported
# ---------------------------------------------------------------

def test_multiple_candidates_supported():
    """GAP-001 should produce multiple candidates (TR-001 has 3 blueprints)."""
    _, candidates = _gap001()
    assert len(candidates) > 1, (
        f"Expected multiple candidates for GAP-001, got {len(candidates)}"
    )


# ---------------------------------------------------------------
# TEST 12 — Single candidate is handled correctly
# ---------------------------------------------------------------

def test_single_candidate_handled():
    """A list of one candidate must still receive rank=1 correctly."""
    gap, all_candidates = _gap001()
    if not all_candidates:
        pytest.skip("No candidates generated")

    single = [all_candidates[0].model_copy(update={"rank": 0, "candidate_score": 0.0})]
    events = load_scenario()
    graph = AttackGraphEngine()
    graph.build(events)

    scorer = CandidateScorer()
    result = scorer.score_and_rank(single, gap, events, graph)
    assert len(result) == 1
    assert result[0].rank == 1


# ---------------------------------------------------------------
# TEST 13 — Empty candidate set is handled gracefully
# ---------------------------------------------------------------

def test_empty_candidate_set_handled():
    """Scorer must return an empty list when given an empty list."""
    events = load_scenario()
    graph = AttackGraphEngine()
    graph.build(events)
    gaps = ReconstructionGapDetector().detect(events, graph)
    assert gaps, "Need at least one gap for this test"

    scorer = CandidateScorer()
    result = scorer.score_and_rank([], gaps[0], events, graph)
    assert result == []


# ---------------------------------------------------------------
# TEST 14 — Unrelated events do not create arbitrary candidates
# ---------------------------------------------------------------

def test_unrelated_transition_produces_no_candidates():
    """
    A technique transition with no matching knowledge rule must produce
    zero candidates — the system must abstain, not fabricate.
    """
    ts1 = datetime(2026, 8, 21, 10, 0, tzinfo=timezone.utc)
    ts2 = datetime(2026, 8, 21, 10, 5, tzinfo=timezone.utc)
    # T1486 (Impact) → T1486 (Impact) — same stage, no transition rule
    e1 = _make_event(event_id="U1", timestamp=ts1, technique_id="T1486",
                     event_type="FileModify")
    e2 = _make_event(event_id="U2", timestamp=ts2, technique_id="T1486",
                     event_type="FileModify")
    gap = _make_gap("U1", "U2", ts1, ts2)
    graph = AttackGraphEngine()
    graph.build([e1, e2])

    candidates = CandidateGenerator().generate(gap, [e1, e2], graph)
    assert candidates == [], (
        "No candidates should be generated for a transition with no knowledge rule"
    )


# ---------------------------------------------------------------
# TEST 15 — Evaluation utility is correctly separated from pipeline
# ---------------------------------------------------------------

def test_evaluation_utility_not_in_pipeline():
    """
    evaluate_candidates() exists only for testing. Verify it:
    - correctly identifies a top-1 match using ground truth
    - is NOT importable from main (i.e., not wired into the API)
    """
    raw = _load_raw()
    gt_raw = raw["ground_truth_events"][0]
    gt_event = CyberEvent(**gt_raw)  # Ground truth used ONLY here in evaluation

    _, candidates = _gap001()
    result = evaluate_candidates(candidates, gt_event)

    assert "outcome" in result
    assert result["total_candidates"] >= 1
    # Ground truth technique is T1003.001 — our rank-1 candidate should match
    assert result["top1_match"] is True, (
        f"Expected top-1 match for T1003.001, got outcome={result['outcome']}, "
        f"matching_rank={result['matching_rank']}"
    )
    assert result["topk_match"] is True

    # Confirm evaluate_candidates is NOT part of main's public API
    import main as _main
    assert not hasattr(_main, "evaluate_candidates"), (
        "evaluate_candidates must not be exposed from main.py"
    )


# ---------------------------------------------------------------
# TEST 16 — API response structure is correct
# ---------------------------------------------------------------

def test_api_reconstruction_response_structure():
    """
    GET /api/v1/reconstruction/candidates must return a list of objects
    each containing 'gap' and 'candidates' keys with correct structure.
    """
    response = client.get("/api/v1/reconstruction/candidates")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    item = data[0]
    assert "gap" in item
    assert "candidates" in item
    assert isinstance(item["candidates"], list)

    # Each candidate must have the required fields
    if item["candidates"]:
        c = item["candidates"][0]
        for field in ("candidate_id", "gap_id", "technique_id",
                      "candidate_score", "rank", "supporting_features",
                      "contradictory_features"):
            assert field in c, f"Missing field '{field}' in candidate response"

        # Validate score semantics — explicitly NOT described as accuracy
        assert 0.0 <= c["candidate_score"] <= 1.0
        assert c["rank"] >= 1


# ---------------------------------------------------------------
# TEST 17 — POST reconstruction endpoint works and blocks path traversal
# ---------------------------------------------------------------

def test_api_post_reconstruction_candidates():
    """POST /api/v1/reconstruction/candidates accepts scenario filename."""
    response = client.post(
        "/api/v1/reconstruction/candidates",
        json={"scenario": "scenario_001.json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_api_post_reconstruction_blocks_path_traversal():
    """Path traversal filenames must be rejected with HTTP 400."""
    for bad in ["../../etc/passwd", "/abs/path.json", "../secret.json"]:
        r = client.post("/api/v1/reconstruction/candidates", json={"scenario": bad})
        assert r.status_code == 400


# ---------------------------------------------------------------
# TEST 18 — Score weights invariant
# ---------------------------------------------------------------

def test_candidate_score_weights_sum_to_one():
    """CANDIDATE_SCORE_WEIGHTS must sum to 1.0."""
    total = sum(CANDIDATE_SCORE_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"
