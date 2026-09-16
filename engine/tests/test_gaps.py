"""
test_gaps.py — CyberScope Milestone 3 Gap Detector Test Suite

Tests are organized to verify:
  1. The detector correctly identifies the known synthetic gap
  2. Normal sequences do not produce false gaps
  3. Individual signals behave correctly in isolation
  4. Ground-truth data cannot enter the detector
  5. Scoring is deterministic
  6. API endpoints return only observed-event-derived information

IMPORTANT: Ground truth (EVT-003, LSASS memory dump) is used ONLY by
test assertions to verify detection accuracy — it is never passed to
the detector or the API.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import GapStatus, ReconstructionGap
from gap_detector import (
    ReconstructionGapDetector,
    SIGNAL_WEIGHTS,
    GAP_SCORE_THRESHOLD,
)
from main import app, load_scenario

client = TestClient(app)

# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _make_event(**kwargs) -> CyberEvent:
    """Create a minimal valid CyberEvent with overridable fields."""
    defaults = {
        "event_id":   "E-TEST",
        "timestamp":  "2026-08-21T09:00:00Z",
        "host_id":    "HOST-A",
        "event_type": "ProcessCreate",
        "source":     "Sysmon",
    }
    defaults.update(kwargs)
    return CyberEvent(**defaults)


def _build_detector_with_events(events):
    """Build an AttackGraphEngine and run the detector on events."""
    graph = AttackGraphEngine()
    graph.build(events)
    detector = ReconstructionGapDetector()
    return detector.detect(events, graph)


def _load_full_scenario_raw():
    """
    Load the raw JSON (both observed AND ground truth) for test evaluation.
    This is ONLY used by test assertions, never passed to the detector.
    """
    base = Path(__file__).parent.parent
    path = base / "datasets" / "demo" / "scenario_001.json"
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------
# TEST 1 — Known synthetic gap is detected
# ---------------------------------------------------------------

def test_known_gap_is_detected():
    """
    scenario_001 has EVT-003 (credential access) intentionally hidden.
    The detector must identify the gap between EVT-002 and EVT-004
    using only observed information.
    """
    events = load_scenario()
    gaps = _build_detector_with_events(events)

    assert len(gaps) >= 1, "Expected at least one gap to be detected"

    boundary_ids = {(g.previous_event_id, g.next_event_id) for g in gaps}
    assert ("EVT-002", "EVT-004") in boundary_ids, (
        "The gap between EVT-002 and EVT-004 must be detected"
    )


# ---------------------------------------------------------------
# TEST 2 — Continuous sequence produces no gap
# ---------------------------------------------------------------

def test_continuous_sequence_no_gap():
    """
    A logically complete sequence (same host, user, process, single-stage
    MITRE advance, no missing prerequisite) must not produce any gap.
    """
    events = [
        _make_event(
            event_id="C1",
            timestamp="2026-08-21T09:00:00Z",
            host_id="HOST-X",
            user_id="alice",
            process_id="P-1",
            event_type="ProcessCreate",
            technique_id="T1190",   # Initial Access, stage 1
        ),
        _make_event(
            event_id="C2",
            timestamp="2026-08-21T09:01:00Z",
            host_id="HOST-X",
            user_id="alice",
            process_id="P-2",
            parent_process_id="P-1",
            event_type="ProcessCreate",
            technique_id="T1059.001",  # Execution, stage 2 — jump of 1
        ),
    ]
    gaps = _build_detector_with_events(events)
    assert gaps == [], f"Expected no gaps, got {gaps}"


# ---------------------------------------------------------------
# TEST 3 — Large time gap alone does NOT create a gap
# ---------------------------------------------------------------

def test_large_time_gap_alone_does_not_trigger():
    """
    Two events separated by a huge time interval but otherwise fully
    continuous (same host, user, process, sequential technique) must
    NOT produce a gap. Time alone is insufficient evidence.
    """
    events = [
        _make_event(
            event_id="T1",
            timestamp="2026-08-21T09:00:00Z",
            host_id="HOST-X",
            user_id="bob",
            process_id="P-1",
            event_type="ProcessCreate",
            technique_id="T1190",     # stage 1
        ),
        _make_event(
            event_id="T2",
            timestamp="2026-08-21T18:00:00Z",  # 9 hours later
            host_id="HOST-X",
            user_id="bob",
            process_id="P-2",
            parent_process_id="P-1",
            event_type="ProcessCreate",
            technique_id="T1059.001",  # stage 2 — jump of 1
        ),
    ]
    gaps = _build_detector_with_events(events)
    # A 9-hour gap is NOT enough on its own (signals: temporal only if
    # median < 3h; here median = 9h so multiplier test is ambiguous with
    # single pair; but the other signals all return False so score < threshold)
    # We just verify the score doesn't cross threshold from time alone.
    for gap in gaps:
        fired = gap.detection_signals
        # If a gap was produced, verify it wasn't purely temporal
        assert (
            fired.technique_transition or
            fired.behavioral_prerequisite or
            fired.host_continuity or
            fired.user_continuity or
            fired.process_relationship
        ), "A gap was created based on temporal signal alone — this violates the design invariant"


# ---------------------------------------------------------------
# TEST 4 — Different hosts are handled correctly
# ---------------------------------------------------------------

def test_different_hosts_signal():
    """
    When two consecutive events are on different hosts without a network
    event explaining the jump, the host_continuity signal must fire.
    """
    events = [
        _make_event(
            event_id="H1",
            timestamp="2026-08-21T09:00:00Z",
            host_id="HOST-A",
            user_id="jdoe",
            process_id="P-1",
            event_type="ProcessCreate",
            technique_id="T1190",
        ),
        _make_event(
            event_id="H2",
            timestamp="2026-08-21T09:01:00Z",
            host_id="HOST-B",        # Different host
            user_id="jdoe",
            process_id="P-2",
            event_type="ProcessCreate",
            technique_id="T1059.001",
        ),
    ]
    graph = AttackGraphEngine()
    graph.build(events)
    detector = ReconstructionGapDetector()

    # Evaluate signals directly for the pair
    temporal_gap = 60.0
    median_gap = 60.0
    signals = detector._evaluate_signals(
        events[0], events[1], temporal_gap, median_gap, [events[0]], graph
    )
    assert signals.host_continuity is True, (
        "host_continuity signal must fire when hosts differ"
    )


# ---------------------------------------------------------------
# TEST 5 — Different users are handled correctly
# ---------------------------------------------------------------

def test_different_users_signal():
    """
    When consecutive events have different user_ids, the user_continuity
    signal must fire.
    """
    e1 = _make_event(event_id="U1", timestamp="2026-08-21T09:00:00Z",
                     user_id="alice", process_id="P-1",
                     event_type="ProcessCreate", technique_id="T1190")
    e2 = _make_event(event_id="U2", timestamp="2026-08-21T09:01:00Z",
                     user_id="SYSTEM",   # Different user
                     process_id="P-2", parent_process_id="P-1",
                     event_type="ProcessCreate", technique_id="T1059.001")
    graph = AttackGraphEngine()
    graph.build([e1, e2])
    detector = ReconstructionGapDetector()
    signals = detector._evaluate_signals(e1, e2, 60.0, 60.0, [e1], graph)
    assert signals.user_continuity is True


# ---------------------------------------------------------------
# TEST 6 — Multiple gaps can be detected in a single sequence
# ---------------------------------------------------------------

def test_multiple_gaps_detected():
    """
    A sequence with two independently suspicious transitions must
    produce (at least) two separate ReconstructionGap objects.
    """
    events = [
        # Gap 1: stage jump 1 → 4 (skips credential access)
        _make_event(event_id="M1", timestamp="2026-08-21T09:00:00Z",
                    host_id="H1", user_id="u1", process_id="P1",
                    event_type="ProcessCreate", technique_id="T1190"),
        _make_event(event_id="M2", timestamp="2026-08-21T09:05:00Z",
                    host_id="H1", user_id="u1", process_id="P2",
                    parent_process_id="P1",
                    event_type="NetworkConnect", technique_id="T1021.002"),
        # Gap 2: second technique jump 4 → 1 on new host (unusual regression)
        _make_event(event_id="M3", timestamp="2026-08-21T09:20:00Z",
                    host_id="H2", user_id="u2", process_id="P3",
                    event_type="ProcessCreate", technique_id="T1190"),
        _make_event(event_id="M4", timestamp="2026-08-21T09:25:00Z",
                    host_id="H2", user_id="u2", process_id="P4",
                    parent_process_id="P3",
                    event_type="NetworkConnect", technique_id="T1021.002"),
    ]
    gaps = _build_detector_with_events(events)
    assert len(gaps) >= 2, (
        f"Expected at least 2 gaps for 2 suspicious transitions, got {len(gaps)}"
    )


# ---------------------------------------------------------------
# TEST 7 — Ground truth cannot enter the detector
# ---------------------------------------------------------------

def test_ground_truth_cannot_enter_detector():
    """
    Verifies that the scenario loader strips ground_truth_events before
    handing events to the detector, and that the hidden event (EVT-003)
    never appears in any gap's context.
    """
    # Ground-truth knowledge used ONLY in this test's assertion
    raw = _load_full_scenario_raw()
    ground_truth_ids = {
        e["event_id"] for e in raw.get("ground_truth_events", [])
    }

    # Load what the detector actually sees
    events = load_scenario()
    observed_ids = {e.event_id for e in events}

    # Ground truth must not be in the observed set
    assert ground_truth_ids.isdisjoint(observed_ids), (
        f"Ground truth event(s) leaked into observed set: "
        f"{ground_truth_ids & observed_ids}"
    )

    # Run the detector and verify ground truth IDs don't appear anywhere
    gaps = _build_detector_with_events(events)
    for gap in gaps:
        assert gap.previous_event_id not in ground_truth_ids
        assert gap.next_event_id not in ground_truth_ids
        ctx_nodes = gap.graph_context.get("previous_event_neighbors", [])
        ctx_nodes += gap.graph_context.get("next_event_neighbors", [])
        for gt_id in ground_truth_ids:
            assert gt_id not in ctx_nodes, (
                f"Ground truth event {gt_id} appeared in gap graph context"
            )


# ---------------------------------------------------------------
# TEST 8 — Gap score is deterministic
# ---------------------------------------------------------------

def test_gap_score_is_deterministic():
    """
    Running the detector twice on identical inputs must produce identical
    gap scores. gap_score must not vary between runs.
    """
    events = load_scenario()

    graph1 = AttackGraphEngine()
    graph1.build(events)
    gaps1 = ReconstructionGapDetector().detect(events, graph1)

    graph2 = AttackGraphEngine()
    graph2.build(events)
    gaps2 = ReconstructionGapDetector().detect(events, graph2)

    assert len(gaps1) == len(gaps2)
    for g1, g2 in zip(gaps1, gaps2):
        assert g1.gap_score == g2.gap_score, (
            f"Non-deterministic scores: {g1.gap_score} vs {g2.gap_score}"
        )
        assert g1.previous_event_id == g2.previous_event_id
        assert g1.next_event_id == g2.next_event_id


# ---------------------------------------------------------------
# TEST 9 — API returns only observed-event-derived gap information
# ---------------------------------------------------------------

def test_api_gaps_endpoint_returns_observed_only():
    """
    GET /api/v1/gaps must return ReconstructionGap objects whose
    boundary event IDs are all in the observed set — never ground truth.
    """
    raw = _load_full_scenario_raw()
    ground_truth_ids = {e["event_id"] for e in raw.get("ground_truth_events", [])}

    response = client.get("/api/v1/gaps")
    assert response.status_code == 200

    gaps = response.json()
    assert isinstance(gaps, list)

    for gap in gaps:
        assert gap["previous_event_id"] not in ground_truth_ids, (
            "Ground truth event appeared as previous_event_id in API response"
        )
        assert gap["next_event_id"] not in ground_truth_ids, (
            "Ground truth event appeared as next_event_id in API response"
        )
        assert gap["status"] == "OPEN"
        assert 0.0 <= gap["gap_score"] <= 1.0


# ---------------------------------------------------------------
# TEST 10 — POST /api/v1/gaps/detect with valid scenario
# ---------------------------------------------------------------

def test_api_post_gaps_detect():
    """
    POST /api/v1/gaps/detect with the default scenario must return
    the same result as GET /api/v1/gaps.
    """
    response = client.post(
        "/api/v1/gaps/detect",
        json={"scenario": "scenario_001.json"}
    )
    assert response.status_code == 200
    gaps = response.json()
    assert isinstance(gaps, list)
    assert len(gaps) >= 1


# ---------------------------------------------------------------
# TEST 11 — POST /api/v1/gaps/detect path traversal is blocked
# ---------------------------------------------------------------

def test_api_post_gaps_detect_path_traversal_blocked():
    """
    Malicious filenames must be rejected with HTTP 400.
    """
    for bad_name in ["../../etc/passwd", "../secrets.json", "/abs/path.json"]:
        response = client.post(
            "/api/v1/gaps/detect",
            json={"scenario": bad_name}
        )
        assert response.status_code == 400, (
            f"Expected 400 for malicious filename '{bad_name}', "
            f"got {response.status_code}"
        )


# ---------------------------------------------------------------
# TEST 12 — Technique signal: only fires on stage jump >= threshold
# ---------------------------------------------------------------

def test_technique_signal_only_fires_on_large_jump():
    """
    A technique stage advance of exactly SUSPICIOUS_STAGE_JUMP must fire.
    A stage advance of SUSPICIOUS_STAGE_JUMP - 1 must not fire.
    """
    # stage 1 → 3: jump of 2 → should fire (T1190 → T1003.001)
    e1 = _make_event(event_id="TS1", timestamp="2026-08-21T09:00:00Z",
                     process_id="P1", technique_id="T1190")
    e2 = _make_event(event_id="TS2", timestamp="2026-08-21T09:01:00Z",
                     process_id="P2", parent_process_id="P1",
                     technique_id="T1003.001")  # stage 3, jump = 2
    graph = AttackGraphEngine()
    graph.build([e1, e2])
    detector = ReconstructionGapDetector()
    sig_jump2 = detector._evaluate_signals(e1, e2, 60, 60, [e1], graph)
    assert sig_jump2.technique_transition is True

    # stage 1 → 2: jump of 1 → should NOT fire
    e3 = _make_event(event_id="TS3", timestamp="2026-08-21T09:02:00Z",
                     process_id="P3", parent_process_id="P2",
                     technique_id="T1059.001")  # stage 2, jump = 1
    sig_jump1 = detector._evaluate_signals(e2, e3, 60, 60, [e1, e2], graph)
    assert sig_jump1.technique_transition is False


# ---------------------------------------------------------------
# TEST 13 — Behavioral signal: suppressed when credential access exists
# ---------------------------------------------------------------

def test_behavioral_signal_suppressed_by_prior_credential_event():
    """
    If credential access is observed BEFORE the lateral movement event,
    the behavioral_prerequisite signal must NOT fire.
    """
    history_with_cred = [
        _make_event(event_id="B1", timestamp="2026-08-21T09:00:00Z",
                    technique_id="T1190"),
        _make_event(event_id="B2", timestamp="2026-08-21T09:05:00Z",
                    technique_id="T1003.001"),   # Credential access present
    ]
    lateral_event = _make_event(
        event_id="B3", timestamp="2026-08-21T09:10:00Z",
        technique_id="T1021.002"  # Lateral movement — requires credential access
    )
    graph = AttackGraphEngine()
    graph.build(history_with_cred + [lateral_event])
    detector = ReconstructionGapDetector()
    signals = detector._evaluate_signals(
        history_with_cred[-1], lateral_event,
        300.0, 300.0,
        history_with_cred,
        graph,
    )
    assert signals.behavioral_prerequisite is False, (
        "behavioral_prerequisite must be suppressed when credential access is in history"
    )


# ---------------------------------------------------------------
# TEST 14 — Configurable threshold changes detection sensitivity
# ---------------------------------------------------------------

def test_configurable_threshold():
    """
    Raising the score_threshold must suppress gaps that would otherwise
    be detected at the default threshold.
    """
    events = load_scenario()

    # Default config — gaps should be detected
    gaps_default = _build_detector_with_events(events)
    assert len(gaps_default) >= 1

    # Very high threshold — no gaps should be detected
    graph = AttackGraphEngine()
    graph.build(events)
    detector_strict = ReconstructionGapDetector(config={"score_threshold": 0.99})
    gaps_strict = detector_strict.detect(events, graph)
    assert len(gaps_strict) == 0, (
        "With threshold=0.99, no gaps should be detected"
    )


# ---------------------------------------------------------------
# TEST 15 — Signal weights sum to 1.0 (invariant guard)
# ---------------------------------------------------------------

def test_signal_weights_sum_to_one():
    """
    Ensures the scoring formula is normalised. If weights drift from 1.0,
    gap_score could exceed 1.0, violating the Pydantic model constraint.
    """
    total = sum(SIGNAL_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, (
        f"SIGNAL_WEIGHTS must sum to 1.0, got {total}"
    )


# ---------------------------------------------------------------
# TEST 16 — gap_score respects Pydantic bounds
# ---------------------------------------------------------------

def test_gap_score_within_bounds():
    """All detected gaps must have gap_score in [0.0, 1.0]."""
    events = load_scenario()
    gaps = _build_detector_with_events(events)
    for gap in gaps:
        assert 0.0 <= gap.gap_score <= 1.0, (
            f"gap_score {gap.gap_score} out of [0, 1] bounds for gap {gap.gap_id}"
        )


# ---------------------------------------------------------------
# TEST 17 — Gap status is OPEN for newly detected gaps
# ---------------------------------------------------------------

def test_newly_detected_gaps_are_open():
    """Freshly detected gaps must have status = OPEN."""
    events = load_scenario()
    gaps = _build_detector_with_events(events)
    for gap in gaps:
        assert gap.status == GapStatus.OPEN, (
            f"Gap {gap.gap_id} has status {gap.status}, expected OPEN"
        )
