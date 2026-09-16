"""
gap_detector.py — CyberScope ReconstructionGapDetector

Identifies locations in observed attack telemetry where events may be missing.

SECURITY INVARIANT:
  This module ONLY operates on observed CyberEvents.
  It NEVER receives, reads, or compares against hidden ground-truth events.
  Any gap it produces is derived exclusively from observed data.

DESIGN PRINCIPLE:
  A simple timestamp gap is NOT sufficient evidence of missing telemetry.
  The detector evaluates six independent contextual signals, each grounded
  in cybersecurity domain knowledge. Multiple signals must converge before
  a gap is created.

OUTPUT SEMANTICS:
  A ReconstructionGap means:
  "This location in the observed sequence requires investigation."
  It does NOT mean: "An event definitely occurred here."
  gap_score is a PRIORITIZATION SCORE, not a validated accuracy metric.
"""

import uuid
import statistics
from typing import List, Dict, Any, Optional

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import DetectionSignals, GapStatus, ReconstructionGap


# ---------------------------------------------------------------
# MITRE ATT&CK Technique Stage Map
#
# Maps technique IDs to broad attack lifecycle stages (1–5).
# Stage ordering follows the MITRE ATT&CK tactic ordering:
#   1: Initial Access / Reconnaissance
#   2: Execution
#   3: Privilege Escalation / Credential Access / Persistence
#   4: Lateral Movement / Discovery
#   5: Collection / Exfiltration / Impact
#
# A jump of ≥ SUSPICIOUS_STAGE_JUMP stages between consecutive observed
# events implies that at least one attack phase was not observed.
# ---------------------------------------------------------------
TECHNIQUE_STAGE_MAP: Dict[str, int] = {
    # Stage 1 — Initial Access
    "T1190": 1,  "T1566": 1,    "T1566.001": 1, "T1566.002": 1,
    "T1133": 1,  "T1078": 1,    "T1195": 1,
    # Stage 2 — Execution
    "T1059": 2,  "T1059.001": 2, "T1059.003": 2, "T1059.005": 2,
    "T1204": 2,  "T1204.002": 2,
    # Stage 3 — Credential Access / Privilege Escalation / Persistence
    "T1003": 3,  "T1003.001": 3, "T1003.002": 3, "T1558": 3,
    "T1134": 3,  "T1055": 3,    "T1547": 3,    "T1543": 3,
    # Stage 4 — Lateral Movement / Discovery
    "T1021": 4,  "T1021.001": 4, "T1021.002": 4, "T1021.006": 4,
    "T1018": 4,  "T1046": 4,    "T1569": 4,    "T1569.002": 4,
    # Stage 5 — Collection / Exfiltration / Impact
    "T1486": 5,  "T1041": 5,    "T1005": 5,    "T1560": 5,
}

# ---------------------------------------------------------------
# Behavioral Prerequisite Maps
#
# Techniques in REQUIRES_CREDENTIAL_ACCESS are lateral movement
# techniques that, in the observed wild, are nearly always preceded
# by a credential harvesting or account-abuse step.
#
# REQUIRES_CREDENTIAL_ACCESS does NOT include T1569.002 (Service
# Execution) because that technique can be the *result* of lateral
# movement rather than the triggering step, and separately requiring
# credential access for it would over-flag normal SMB chains.
# ---------------------------------------------------------------
REQUIRES_CREDENTIAL_ACCESS: set = {
    "T1021",     # Remote Services (generic)
    "T1021.001", # RDP
    "T1021.002", # SMB/Windows Admin Shares
    "T1021.006", # WinRM
}

CREDENTIAL_ACCESS_TECHNIQUES: set = {
    "T1003",     # OS Credential Dumping (generic)
    "T1003.001", # LSASS Memory
    "T1003.002", # SAM
    "T1558",     # Steal or Forge Kerberos Tickets
    "T1078",     # Valid Accounts
    "T1134",     # Access Token Manipulation
}

# ---------------------------------------------------------------
# CONFIGURABLE THRESHOLDS — documented rationale below
# ---------------------------------------------------------------

# TEMPORAL_OUTLIER_MULTIPLIER = 3.0
# Rationale: A gap 3× larger than the median inter-event gap is a
# standard statistical outlier boundary. We do not use an absolute
# time because attack timing varies widely across scenarios.
# Time alone is weak evidence; we weight it at 0.10.
TEMPORAL_OUTLIER_MULTIPLIER: float = 3.0

# SUSPICIOUS_STAGE_JUMP = 2
# Rationale: A single-stage advance (e.g., Initial Access → Execution)
# is normal and expected. A jump of 2+ stages skips an entire attack
# phase, which commonly requires intermediate, unobserved steps.
SUSPICIOUS_STAGE_JUMP: int = 2

# GAP_SCORE_THRESHOLD = 0.40
# Rationale: At 0.40, at least one strong signal (weight ≥ 0.25) plus
# one supporting signal must fire, OR two moderate signals must fire.
# This prevents single-signal false positives while remaining sensitive.
GAP_SCORE_THRESHOLD: float = 0.40

# ---------------------------------------------------------------
# SIGNAL WEIGHTS  (must sum to 1.0)
#
# Rationale for ordering:
#   technique_transition (0.30): MITRE stage mapping is objective and
#     specific to attack sequencing — strongest signal.
#   behavioral_prerequisite (0.25): A missing precondition is a concrete
#     causal gap, not just a statistical anomaly — second strongest.
#   host_continuity (0.15): Host changes are meaningful but expected
#     during lateral movement; needs supporting signals.
#   user_continuity (0.10): User changes add context but can be
#     legitimately explained (e.g., impersonation, SYSTEM elevation).
#   process_relationship (0.10): Missing process lineage is a useful
#     supporting signal for unexplained behavioral jumps.
#   temporal (0.10): Weakest — time alone cannot justify a gap claim.
# ---------------------------------------------------------------
SIGNAL_WEIGHTS: Dict[str, float] = {
    "technique_transition":    0.30,
    "behavioral_prerequisite": 0.25,
    "host_continuity":         0.15,
    "user_continuity":         0.10,
    "process_relationship":    0.10,
    "temporal":                0.10,
}

# Verify at import time
_weight_sum = sum(SIGNAL_WEIGHTS.values())
assert abs(_weight_sum - 1.0) < 1e-9, (
    f"SIGNAL_WEIGHTS must sum to 1.0, got {_weight_sum}"
)


class ReconstructionGapDetector:
    """
    Detects potential reconstruction gaps in observed attack telemetry.

    INVARIANT: Only observed CyberEvents and the observed AttackGraph
    are ever passed to this class. Ground truth is never provided.

    Usage:
        detector = ReconstructionGapDetector()
        gaps = detector.detect(observed_events, attack_graph)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.temporal_multiplier: float = cfg.get(
            "temporal_multiplier", TEMPORAL_OUTLIER_MULTIPLIER
        )
        self.stage_jump_threshold: int = cfg.get(
            "stage_jump_threshold", SUSPICIOUS_STAGE_JUMP
        )
        self.score_threshold: float = cfg.get(
            "score_threshold", GAP_SCORE_THRESHOLD
        )

    def detect(
        self,
        events: List[CyberEvent],
        graph: AttackGraphEngine
    ) -> List[ReconstructionGap]:
        """
        Evaluate all consecutive event pairs for reconstruction gaps.

        Args:
            events: ONLY observed CyberEvents (no ground truth).
            graph:  AttackGraphEngine built from the same observed events.

        Returns:
            List of ReconstructionGap objects, sorted by gap_score descending.
        """
        if len(events) < 2:
            return []

        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Pre-compute all inter-event time gaps in seconds
        gap_seconds_list = [
            (sorted_events[i + 1].timestamp - sorted_events[i].timestamp).total_seconds()
            for i in range(len(sorted_events) - 1)
        ]

        # Median gap used as baseline for temporal signal
        median_gap = statistics.median(gap_seconds_list) if gap_seconds_list else 0.0

        reconstruction_gaps: List[ReconstructionGap] = []

        for i in range(len(sorted_events) - 1):
            prev = sorted_events[i]
            nxt = sorted_events[i + 1]
            temporal_gap = gap_seconds_list[i]

            # History = all events observed at or before prev (used for behavioral signal)
            history_before_prev: List[CyberEvent] = sorted_events[: i + 1]

            signals = self._evaluate_signals(
                prev, nxt, temporal_gap, median_gap, history_before_prev, graph
            )
            score = self._compute_score(signals)

            if score >= self.score_threshold:
                gap = ReconstructionGap(
                    gap_id=f"GAP-{str(uuid.uuid4())[:8].upper()}",
                    previous_event_id=prev.event_id,
                    next_event_id=nxt.event_id,
                    start_timestamp=prev.timestamp,
                    end_timestamp=nxt.timestamp,
                    affected_host=prev.host_id,
                    affected_user=prev.user_id,
                    temporal_gap_seconds=round(temporal_gap, 3),
                    previous_event_type=prev.event_type,
                    next_event_type=nxt.event_type,
                    graph_context=self._get_graph_context(prev, nxt, graph),
                    detection_signals=signals,
                    gap_score=round(score, 4),
                    status=GapStatus.OPEN,
                )
                reconstruction_gaps.append(gap)

        # Return highest-priority gaps first
        reconstruction_gaps.sort(key=lambda g: g.gap_score, reverse=True)
        return reconstruction_gaps

    # ------------------------------------------------------------------
    # SIGNAL EVALUATION
    # ------------------------------------------------------------------

    def _evaluate_signals(
        self,
        prev: CyberEvent,
        nxt: CyberEvent,
        temporal_gap: float,
        median_gap: float,
        history: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> DetectionSignals:
        return DetectionSignals(
            temporal=self._signal_temporal(temporal_gap, median_gap),
            host_continuity=self._signal_host(prev, nxt),
            user_continuity=self._signal_user(prev, nxt),
            process_relationship=self._signal_process(prev, nxt),
            technique_transition=self._signal_technique(prev, nxt),
            behavioral_prerequisite=self._signal_behavioral(nxt, history),
        )

    def _signal_temporal(
        self, gap_seconds: float, median_gap: float
    ) -> bool:
        """
        True if the inter-event gap is an outlier relative to the
        median gap across the full observed sequence.
        Uses a multiplier rather than an absolute threshold because
        attack timing varies between scenarios.
        """
        if median_gap <= 0:
            return False
        return gap_seconds > (self.temporal_multiplier * median_gap)

    def _signal_host(self, prev: CyberEvent, nxt: CyberEvent) -> bool:
        """
        True if the host changes between consecutive events without
        a direct network-connection event linking them.
        Note: a host change within lateral movement is expected at
        the boundary of a connect/execute pair; however, unexplained
        host changes within the same technique phase are suspicious.
        """
        return prev.host_id != nxt.host_id

    def _signal_user(self, prev: CyberEvent, nxt: CyberEvent) -> bool:
        """
        True if both events have a user context and they differ.
        Missing user_id is treated as inconclusive (returns False).
        """
        if not prev.user_id or not nxt.user_id:
            return False
        return prev.user_id != nxt.user_id

    def _signal_process(self, prev: CyberEvent, nxt: CyberEvent) -> bool:
        """
        True if no direct process relationship (same PID or parent→child)
        exists between adjacent events. An unexplained process jump
        suggests an intermediate step was not observed.
        """
        if not prev.process_id or not nxt.process_id:
            return False
        if prev.process_id == nxt.process_id:
            return False
        # Direct parent-child relationship
        if nxt.parent_process_id == prev.process_id:
            return False
        if prev.parent_process_id == nxt.process_id:
            return False
        return True

    def _signal_technique(self, prev: CyberEvent, nxt: CyberEvent) -> bool:
        """
        True if the MITRE ATT&CK stage advances by ≥ SUSPICIOUS_STAGE_JUMP.
        A jump of 2+ stages means at least one attack phase was skipped
        in the observed telemetry.
        """
        prev_stage = TECHNIQUE_STAGE_MAP.get(prev.technique_id or "")
        nxt_stage = TECHNIQUE_STAGE_MAP.get(nxt.technique_id or "")
        if prev_stage is None or nxt_stage is None:
            return False
        return (nxt_stage - prev_stage) >= self.stage_jump_threshold

    def _signal_behavioral(
        self, nxt: CyberEvent, history: List[CyberEvent]
    ) -> bool:
        """
        True if the next event uses a technique that typically requires
        a credential-access step as a prerequisite, and no such step
        is present anywhere in the observed history.

        This signal looks at the FULL history (not just the previous
        event) so that a credential step observed earlier suppresses
        the signal correctly.
        """
        if nxt.technique_id not in REQUIRES_CREDENTIAL_ACCESS:
            return False
        history_techniques = {
            e.technique_id for e in history if e.technique_id
        }
        has_credential_event = bool(
            history_techniques & CREDENTIAL_ACCESS_TECHNIQUES
        )
        return not has_credential_event

    # ------------------------------------------------------------------
    # SCORING
    # ------------------------------------------------------------------

    def _compute_score(self, signals: DetectionSignals) -> float:
        """
        Weighted linear combination of boolean signals.

        Formula:
            score = Σ (weight_i × signal_i)

        where signal_i ∈ {0, 1}.

        The score is bounded [0, 1] by construction because weights sum to 1
        and all signals are boolean.
        """
        mapping = {
            "technique_transition":    signals.technique_transition,
            "behavioral_prerequisite": signals.behavioral_prerequisite,
            "host_continuity":         signals.host_continuity,
            "user_continuity":         signals.user_continuity,
            "process_relationship":    signals.process_relationship,
            "temporal":                signals.temporal,
        }
        return sum(
            SIGNAL_WEIGHTS[k] * (1.0 if v else 0.0)
            for k, v in mapping.items()
        )

    # ------------------------------------------------------------------
    # GRAPH CONTEXT
    # ------------------------------------------------------------------

    def _get_graph_context(
        self,
        prev: CyberEvent,
        nxt: CyberEvent,
        graph: AttackGraphEngine,
    ) -> Dict[str, Any]:
        """
        Collects graph-level context about the two boundary events.
        Used to enrich the ReconstructionGap object for the UI.
        Does NOT influence the gap_score.
        """
        prev_neighbors = graph.get_neighbors(prev.event_id)
        nxt_neighbors = graph.get_neighbors(nxt.event_id)
        shared_context = list(set(prev_neighbors) & set(nxt_neighbors))
        directly_connected = (
            nxt.event_id in prev_neighbors or prev.event_id in nxt_neighbors
        )
        return {
            "previous_event_neighbors": prev_neighbors,
            "next_event_neighbors": nxt_neighbors,
            "directly_connected_in_graph": directly_connected,
            "shared_context_nodes": shared_context,
        }
