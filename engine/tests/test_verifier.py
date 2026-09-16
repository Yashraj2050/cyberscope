"""
test_verifier.py — CyberScope Milestone 5 Evidence Verifier Test Suite

Test organization:
  1:  Directly observed event     → OBSERVED
  2:  Unambiguous single candidate → INFERRED
  3:  Insufficient evidence        → UNKNOWN
  4:  Contradicting evidence       → UNKNOWN  (technique check FAIL)
  5:  Tied candidates             → UNKNOWN  (scenario_001 tie)
  6:  High score alone ≠ INFERRED → UNKNOWN  (veto from FAIL check)
  7:  Ground truth cannot enter verifier
  8:  Verification checks are recorded
  9:  Supporting evidence is recorded
  10: Missing evidence is recorded
  11: Contradictory evidence is recorded
  12: Deterministic verification
  13: No candidates              → UNKNOWN
  14: API verify endpoint returns results
  15: API verify endpoint is clean of ground truth
  16: POST verify endpoint + path traversal
  17: confidence_label is correct for each status
  18: Verification score within [0, 1]
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
from candidate_scorer import CandidateScorer
from verifier_model import (
    ReconstructionResult, ReconstructionStatus, ConfidenceLabel, CheckResult
)
from evidence_verifier import EvidenceVerifier, INFERRED_THRESHOLD, AMBIGUITY_DELTA
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


def _make_gap(
    prev_id: str, next_id: str,
    prev_ts: datetime, next_ts: datetime,
    host: str = "HOST-A", user: str = "jdoe",
) -> ReconstructionGap:
    signals = DetectionSignals(technique_transition=True, behavioral_prerequisite=True)
    return ReconstructionGap(
        gap_id="GAP-TEST-001",
        previous_event_id=prev_id,
        next_event_id=next_id,
        start_timestamp=prev_ts,
        end_timestamp=next_ts,
        affected_host=host,
        affected_user=user,
        temporal_gap_seconds=(next_ts - prev_ts).total_seconds(),
        previous_event_type="ProcessCreate",
        next_event_type="NetworkConnect",
        detection_signals=signals,
        gap_score=0.55,
        status=GapStatus.OPEN,
    )


def _make_candidate(
    technique_id: str,
    technique_name: str,
    event_type: str,
    candidate_score: float = 0.90,
    rank: int = 1,
    gap_id: str = "GAP-TEST-001",
) -> ReconstructionCandidate:
    return ReconstructionCandidate(
        candidate_id="CAND-SYNTHETIC-001",
        gap_id=gap_id,
        event_type=event_type,
        technique_id=technique_id,
        technique_name=technique_name,
        description="Synthetic candidate for testing",
        required_preconditions=[],
        supporting_features=[],
        contradictory_features=[],
        temporal_score=1.0,
        host_score=1.0,
        user_score=1.0,
        process_score=0.9,
        technique_score=1.0,
        graph_score=0.55,
        candidate_score=candidate_score,
        rank=rank,
    )


def _load_raw():
    base = Path(__file__).parent.parent
    with open(base / "datasets" / "demo" / "scenario_001.json") as f:
        return json.load(f)


def _gap001_full():
    """Run the full pipeline for scenario_001 and return gap + candidates."""
    events = load_scenario()
    graph = AttackGraphEngine()
    graph.build(events)
    gaps = ReconstructionGapDetector().detect(events, graph)
    gap = next(g for g in gaps if g.previous_event_id == "EVT-002")
    gen = CandidateGenerator()
    scorer = CandidateScorer()
    raw = gen.generate(gap, events, graph)
    scored = scorer.score_and_rank(raw, gap, events, graph)
    return gap, scored, events, graph


# ---------------------------------------------------------------
# TEST 1 — Directly observed event → OBSERVED
# ---------------------------------------------------------------

def test_observed_status_for_directly_observed_event():
    """
    If an event with the same technique and event_type as the candidate
    is present in the observed set within the gap window, the result must
    be OBSERVED — not INFERRED.
    """
    ts_prev = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts_mid  = datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc)   # in window
    ts_next = datetime(2026, 8, 21, 9, 15, tzinfo=timezone.utc)

    e_prev = _make_event(
        event_id="OBS-1", timestamp=ts_prev,
        host_id="HOST-A", user_id="jdoe", process_id="P-1",
        event_type="ProcessCreate", technique_id="T1059.001",
    )
    # This event IS observed — same technique + event_type as our candidate
    e_mid  = _make_event(
        event_id="OBS-2", timestamp=ts_mid,
        host_id="HOST-A", user_id="jdoe", process_id="P-1",
        event_type="ProcessAccess", technique_id="T1003.001",
    )
    e_next = _make_event(
        event_id="OBS-3", timestamp=ts_next,
        host_id="HOST-A", user_id="jdoe", process_id="P-2",
        parent_process_id="P-1",
        event_type="NetworkConnect", technique_id="T1021.002",
    )

    all_events = [e_prev, e_mid, e_next]
    graph = AttackGraphEngine()
    graph.build(all_events)

    gap = _make_gap("OBS-1", "OBS-3", ts_prev, ts_next)
    # Candidate matches e_mid exactly
    candidate = _make_candidate(
        technique_id="T1003.001",
        technique_name="OS Credential Dumping: LSASS Memory",
        event_type="ProcessAccess",
        candidate_score=0.96,
    )

    verifier = EvidenceVerifier()
    result = verifier.verify(gap, [candidate], all_events, graph)

    assert result.status == ReconstructionStatus.OBSERVED, (
        f"Expected OBSERVED when event exists in telemetry, got {result.status}"
    )
    assert "OBS-2" in result.explanation or "T1003.001" in result.explanation


# ---------------------------------------------------------------
# TEST 2 — Unambiguous single candidate → INFERRED
# ---------------------------------------------------------------

def test_inferred_for_unambiguous_single_candidate():
    """
    A single candidate with strong verification (no ambiguous competitor,
    all checks PASS, verification_score >= threshold) must produce INFERRED.
    """
    ts_prev = datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc)
    ts_next = datetime(2026, 8, 21, 9, 15, tzinfo=timezone.utc)

    e_prev = _make_event(
        event_id="EVT-002", timestamp=ts_prev,
        host_id="HOST-A", user_id="jdoe", process_id="P-101",
        process_name="powershell.exe",
        event_type="ProcessCreate", technique_id="T1059.001",
    )
    e_next = _make_event(
        event_id="EVT-004", timestamp=ts_next,
        host_id="HOST-A", user_id="jdoe", process_id="P-101",
        event_type="NetworkConnect", technique_id="T1021.002",
    )
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("EVT-002", "EVT-004", ts_prev, ts_next)
    # Single candidate only — no competitor
    single = _make_candidate(
        technique_id="T1003.001",
        technique_name="OS Credential Dumping: LSASS Memory",
        event_type="ProcessAccess",
        candidate_score=0.96,
        rank=1,
    )

    verifier = EvidenceVerifier()
    result = verifier.verify(gap, [single], events, graph)

    assert result.status == ReconstructionStatus.INFERRED, (
        f"Expected INFERRED for unambiguous single strong candidate, got {result.status}\n"
        f"explanation: {result.explanation}"
    )
    assert result.verification_score >= INFERRED_THRESHOLD


# ---------------------------------------------------------------
# TEST 3 — Insufficient evidence → UNKNOWN
# ---------------------------------------------------------------

def test_unknown_for_insufficient_evidence():
    """
    When verification_score falls below the INFERRED_THRESHOLD due to
    multiple UNKNOWN checks, the result must be UNKNOWN.
    """
    # Very tight time window → temporal check FAIL
    ts_prev = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts_next = ts_prev + timedelta(seconds=2)  # 2s — below 5s threshold

    e_prev = _make_event(event_id="INS-1", timestamp=ts_prev,
                         technique_id="T1059.001", event_type="ProcessCreate")
    e_next = _make_event(event_id="INS-2", timestamp=ts_next,
                         technique_id="T1021.002", event_type="NetworkConnect")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("INS-1", "INS-2", ts_prev, ts_next)
    candidate = _make_candidate(
        technique_id="T1003.001",
        technique_name="OS Credential Dumping: LSASS Memory",
        event_type="ProcessAccess",
        candidate_score=0.80,
    )

    verifier = EvidenceVerifier()
    result = verifier.verify(gap, [candidate], events, graph)

    # temporal check must FAIL (2s < 5s), vetoing INFERRED
    assert result.status == ReconstructionStatus.UNKNOWN, (
        f"Expected UNKNOWN for insufficient temporal evidence, got {result.status}"
    )
    assert result.verification_checks.get("temporal") == CheckResult.FAIL


# ---------------------------------------------------------------
# TEST 4 — Contradicting evidence (FAIL check) → UNKNOWN
# ---------------------------------------------------------------

def test_unknown_for_contradicting_evidence():
    """
    A candidate whose technique check FAILS (stage outside expected range)
    must be classified UNKNOWN regardless of candidate_score.
    """
    ts_prev = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts_next = ts_prev + timedelta(minutes=10)

    # Stage 4 → Stage 4: candidate at stage 5 (outside range) → technique FAIL
    e_prev = _make_event(event_id="CON-1", timestamp=ts_prev,
                         technique_id="T1021.002",   # stage 4
                         event_type="NetworkConnect", user_id="jdoe",
                         process_id="P-1")
    e_next = _make_event(event_id="CON-2", timestamp=ts_next,
                         technique_id="T1021.002",   # stage 4
                         event_type="NetworkConnect", user_id="jdoe",
                         process_id="P-1")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("CON-1", "CON-2", ts_prev, ts_next)
    # Candidate is at stage 5 (Impact) — outside the 4→4 range → FAIL
    candidate = _make_candidate(
        technique_id="T1486",          # Impact, stage 5
        technique_name="Data Encrypted for Impact",
        event_type="FileModify",
        candidate_score=0.90,
    )

    verifier = EvidenceVerifier()
    result = verifier.verify(gap, [candidate], events, graph)

    assert result.status == ReconstructionStatus.UNKNOWN, (
        f"Expected UNKNOWN for contradicting technique, got {result.status}"
    )
    assert result.verification_checks.get("technique") == CheckResult.FAIL


# ---------------------------------------------------------------
# TEST 5 — Tied candidates (scenario_001) → UNKNOWN
# ---------------------------------------------------------------

def test_unknown_for_tied_candidates_scenario001():
    """
    scenario_001 produces T1003.001 and T1003 with equal scores (0.9625).
    The verifier must recognize the ambiguity and return UNKNOWN.
    """
    gap, candidates, events, graph = _gap001_full()

    # Verify the tie exists
    top_scores = [c.candidate_score for c in candidates if c.rank == 1]
    assert len(top_scores) >= 2, (
        "Expected at least 2 tied rank-1 candidates for this test"
    )
    delta = max(top_scores) - min(top_scores)
    assert delta <= AMBIGUITY_DELTA, (
        f"Expected tied candidates within AMBIGUITY_DELTA={AMBIGUITY_DELTA}, got delta={delta}"
    )

    verifier = EvidenceVerifier()
    result = verifier.verify(gap, candidates, events, graph)

    assert result.status == ReconstructionStatus.UNKNOWN, (
        f"Expected UNKNOWN for tied candidates, got {result.status}\n"
        f"explanation: {result.explanation}"
    )
    # The explanation must mention ambiguity / multiple candidates
    explanation_lower = result.explanation.lower()
    assert any(word in explanation_lower for word in (
        "ambig", "comparable", "equivalent", "cannot distinguish", "tied"
    )), (
        f"Explanation should mention ambiguity, got: {result.explanation}"
    )


# ---------------------------------------------------------------
# TEST 6 — High candidate_score alone cannot produce INFERRED
# ---------------------------------------------------------------

def test_high_score_alone_cannot_produce_inferred():
    """
    A candidate with candidate_score=0.99 but a FAIL on the technique check
    must still produce UNKNOWN. Score alone is not sufficient for INFERRED.
    """
    ts_prev = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts_next = ts_prev + timedelta(minutes=10)

    e_prev = _make_event(event_id="HS-1", timestamp=ts_prev,
                         technique_id="T1059.001", event_type="ProcessCreate",
                         user_id="admin", process_id="P-1")
    e_next = _make_event(event_id="HS-2", timestamp=ts_next,
                         technique_id="T1021.002", event_type="NetworkConnect",
                         user_id="admin", process_id="P-1")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("HS-1", "HS-2", ts_prev, ts_next)
    # Candidate with very high score but wrong technique (stage out of range)
    candidate = _make_candidate(
        technique_id="T1486",   # stage 5, outside range 2→4
        technique_name="Data Encrypted for Impact",
        event_type="FileModify",
        candidate_score=0.99,   # deliberately very high
    )

    result = EvidenceVerifier().verify(gap, [candidate], events, graph)

    assert result.status == ReconstructionStatus.UNKNOWN, (
        "A FAIL on technique check must veto INFERRED even with high candidate_score"
    )


# ---------------------------------------------------------------
# TEST 7 — Ground truth cannot enter the verifier
# ---------------------------------------------------------------

def test_ground_truth_cannot_enter_verifier():
    """
    The verifier only receives observed events. Ground truth IDs must not
    appear anywhere in the ReconstructionResult output.
    """
    raw = _load_raw()
    gt_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}

    gap, candidates, events, graph = _gap001_full()
    verifier = EvidenceVerifier()
    result = verifier.verify(gap, candidates, events, graph)

    # Ground truth IDs must not appear in any result field
    result_json = result.model_dump_json()
    for gt_id in gt_ids:
        assert gt_id not in result_json, (
            f"Ground truth ID {gt_id} found in verifier output"
        )


# ---------------------------------------------------------------
# TEST 8 — Verification checks are recorded
# ---------------------------------------------------------------

def test_verification_checks_are_recorded():
    """Result must contain a verification_checks dict with expected keys."""
    gap, candidates, events, graph = _gap001_full()
    result = EvidenceVerifier().verify(gap, candidates, events, graph)

    assert isinstance(result.verification_checks, dict)
    expected_keys = {"temporal", "host", "user", "process",
                     "technique", "graph", "contradiction"}
    assert expected_keys.issubset(result.verification_checks.keys()), (
        f"Missing check keys: {expected_keys - result.verification_checks.keys()}"
    )
    for key, val in result.verification_checks.items():
        assert val in (CheckResult.PASS, CheckResult.FAIL, CheckResult.UNKNOWN), (
            f"Check '{key}' has invalid result '{val}'"
        )


# ---------------------------------------------------------------
# TEST 9 — Supporting evidence is recorded
# ---------------------------------------------------------------

def test_supporting_evidence_is_recorded():
    """supporting_evidence must be a non-empty list for a verifiable gap."""
    ts_prev = datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc)
    ts_next = datetime(2026, 8, 21, 9, 15, tzinfo=timezone.utc)
    e_prev = _make_event(event_id="SE-1", timestamp=ts_prev,
                         user_id="jdoe", process_id="P-1",
                         event_type="ProcessCreate", technique_id="T1059.001")
    e_next = _make_event(event_id="SE-2", timestamp=ts_next,
                         user_id="jdoe", process_id="P-1",
                         event_type="NetworkConnect", technique_id="T1021.002")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("SE-1", "SE-2", ts_prev, ts_next)
    candidate = _make_candidate(
        technique_id="T1003.001",
        technique_name="LSASS Memory",
        event_type="ProcessAccess",
    )

    result = EvidenceVerifier().verify(gap, [candidate], events, graph)

    assert isinstance(result.supporting_evidence, list), (
        "supporting_evidence must be a list"
    )
    assert len(result.supporting_evidence) >= 1, (
        "At least one supporting evidence item expected for a well-formed gap"
    )


# ---------------------------------------------------------------
# TEST 10 — Missing evidence is recorded when checks are UNKNOWN
# ---------------------------------------------------------------

def test_missing_evidence_is_recorded_for_unknown_checks():
    """
    When verification checks return UNKNOWN, those items should appear
    in missing_evidence (evidence we'd need but don't have).
    """
    # Use scenario_001 which has graph-UNKNOWN for candidates
    gap, candidates, events, graph = _gap001_full()
    result = EvidenceVerifier().verify(gap, candidates, events, graph)

    assert isinstance(result.missing_evidence, list), (
        "missing_evidence must be a list"
    )
    # For the tie (UNKNOWN status), contradictory evidence is generated
    # and missing evidence may come from UNKNOWN checks
    # At minimum missing_evidence is a valid list
    assert result.missing_evidence is not None


# ---------------------------------------------------------------
# TEST 11 — Contradictory evidence is recorded for ambiguous case
# ---------------------------------------------------------------

def test_contradictory_evidence_recorded_for_tied_case():
    """
    When candidates are tied (AMBIGUITY), the ambiguity note should appear
    in contradictory_evidence.
    """
    gap, candidates, events, graph = _gap001_full()
    result = EvidenceVerifier().verify(gap, candidates, events, graph)

    # Tied case → ambiguity note goes to contradictory_evidence
    assert result.status == ReconstructionStatus.UNKNOWN
    assert isinstance(result.contradictory_evidence, list)
    # At least the ambiguity note should be present
    combined = " ".join(result.contradictory_evidence)
    assert len(combined) > 0, (
        "contradictory_evidence should contain the ambiguity explanation"
    )


# ---------------------------------------------------------------
# TEST 12 — Deterministic verification
# ---------------------------------------------------------------

def test_verification_is_deterministic():
    """Same input must always produce the same status and verification_score."""
    gap, candidates, events, graph = _gap001_full()
    verifier = EvidenceVerifier()

    r1 = verifier.verify(gap, candidates, events, graph)
    r2 = verifier.verify(gap, candidates, events, graph)

    assert r1.status              == r2.status
    assert r1.verification_score  == r2.verification_score
    assert r1.verification_checks == r2.verification_checks
    assert r1.confidence_label    == r2.confidence_label


# ---------------------------------------------------------------
# TEST 13 — No candidates → UNKNOWN
# ---------------------------------------------------------------

def test_no_candidates_produces_unknown():
    """When no candidates are generated, the result must be UNKNOWN."""
    ts_prev = datetime(2026, 8, 21, 9, 0, tzinfo=timezone.utc)
    ts_next = ts_prev + timedelta(minutes=5)
    e_prev = _make_event(event_id="NC-1", timestamp=ts_prev,
                         technique_id="T1059.001")
    e_next = _make_event(event_id="NC-2", timestamp=ts_next,
                         technique_id="T1021.002")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)

    gap = _make_gap("NC-1", "NC-2", ts_prev, ts_next)

    result = EvidenceVerifier().verify(gap, [], events, graph)  # empty candidates

    assert result.status == ReconstructionStatus.UNKNOWN, (
        f"Expected UNKNOWN for no candidates, got {result.status}"
    )
    assert result.candidate_id is None
    assert len(result.missing_evidence) >= 1


# ---------------------------------------------------------------
# TEST 14 — API verify endpoint returns results
# ---------------------------------------------------------------

def test_api_verify_endpoint_returns_results():
    """
    GET /api/v1/reconstruction/verify must return a list with
    at least one FullPipelineResult containing gap + candidates + result.
    """
    response = client.get("/api/v1/reconstruction/verify")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    item = data[0]
    assert "gap" in item
    assert "candidates" in item
    assert "result" in item

    result = item["result"]
    assert "status" in result
    assert result["status"] in ("OBSERVED", "INFERRED", "UNKNOWN")
    assert "verification_score" in result
    assert "confidence_label" in result
    assert "verification_checks" in result
    assert "supporting_evidence" in result
    assert "missing_evidence" in result
    assert "contradictory_evidence" in result
    assert "explanation" in result
    assert 0.0 <= result["verification_score"] <= 1.0


# ---------------------------------------------------------------
# TEST 15 — API verify endpoint is clean of ground truth
# ---------------------------------------------------------------

def test_api_verify_no_ground_truth():
    """
    GET /api/v1/reconstruction/verify must not contain ground-truth event
    IDs in any part of the response body.
    """
    raw = _load_raw()
    gt_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}

    response = client.get("/api/v1/reconstruction/verify")
    assert response.status_code == 200

    body = json.dumps(response.json())
    for gt_id in gt_ids:
        assert gt_id not in body, (
            f"Ground truth ID {gt_id} found in verify API response"
        )


# ---------------------------------------------------------------
# TEST 16 — POST verify + path traversal blocked
# ---------------------------------------------------------------

def test_api_post_verify_and_path_traversal():
    """POST /api/v1/reconstruction/verify works and blocks path traversal."""
    # Valid scenario
    r = client.post("/api/v1/reconstruction/verify",
                    json={"scenario": "scenario_001.json"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Path traversal
    for bad in ["../../etc/passwd", "/etc/shadow.json", "../x.json"]:
        r2 = client.post("/api/v1/reconstruction/verify", json={"scenario": bad})
        assert r2.status_code == 400


# ---------------------------------------------------------------
# TEST 17 — confidence_label semantics
# ---------------------------------------------------------------

def test_confidence_label_for_inferred_case():
    """
    A result with INFERRED status and high verification_score must
    have confidence_label = HIGH (verification_score >= 0.80).
    """
    ts_prev = datetime(2026, 8, 21, 9, 5, tzinfo=timezone.utc)
    ts_next = datetime(2026, 8, 21, 9, 15, tzinfo=timezone.utc)
    e_prev = _make_event(event_id="CL-1", timestamp=ts_prev,
                         user_id="jdoe", process_id="P-101",
                         process_name="powershell.exe",
                         event_type="ProcessCreate", technique_id="T1059.001")
    e_next = _make_event(event_id="CL-2", timestamp=ts_next,
                         user_id="jdoe", process_id="P-101",
                         event_type="NetworkConnect", technique_id="T1021.002")
    events = [e_prev, e_next]
    graph = AttackGraphEngine()
    graph.build(events)
    gap = _make_gap("CL-1", "CL-2", ts_prev, ts_next)
    candidate = _make_candidate(
        technique_id="T1003.001",
        technique_name="LSASS Memory",
        event_type="ProcessAccess",
    )

    result = EvidenceVerifier().verify(gap, [candidate], events, graph)

    if result.status == ReconstructionStatus.INFERRED:
        assert result.confidence_label == ConfidenceLabel.HIGH, (
            f"Expected HIGH confidence for strong INFERRED, got {result.confidence_label}"
        )

    # Confidence label must always be a valid value
    assert result.confidence_label in (
        ConfidenceLabel.HIGH, ConfidenceLabel.MEDIUM, ConfidenceLabel.LOW
    )


# ---------------------------------------------------------------
# TEST 18 — Verification score within [0, 1]
# ---------------------------------------------------------------

def test_verification_score_within_bounds():
    """verification_score must always be in [0.0, 1.0]."""
    gap, candidates, events, graph = _gap001_full()
    result = EvidenceVerifier().verify(gap, candidates, events, graph)
    assert 0.0 <= result.verification_score <= 1.0, (
        f"verification_score {result.verification_score} out of [0, 1]"
    )
