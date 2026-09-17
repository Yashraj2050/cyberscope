"""
evidence_verifier.py — CyberScope EvidenceVerifier

Determines whether a candidate reconstruction should be classified as:
  OBSERVED  /  INFERRED  /  UNKNOWN

FUNDAMENTAL DESIGN PRINCIPLE:
  "CyberScope does not treat a model score as proof. A reconstruction must
  pass evidence verification before being classified as INFERRED."

  "When available evidence cannot distinguish between plausible candidates,
  CyberScope abstains and returns UNKNOWN."

ARCHITECTURAL ROLE:
  This is the TRUST BOUNDARY of CyberScope.

  CandidateScorer answers: "Which candidate is best supported numerically?"
  EvidenceVerifier answers: "Is the support sufficient and unambiguous to
                             produce a classification?"

  These are separate, distinct questions.

SECURITY INVARIANT:
  The verifier NEVER receives:
    - ground_truth_events
    - hidden events
    - evaluation labels
    - expected answers
  All decisions are derived exclusively from observed telemetry.

CLASSIFICATION RULES (explicit, not ML-derived):
  1. If direct telemetry already shows this event           → OBSERVED
  2. If verification_score >= INFERRED_THRESHOLD            → (candidate INFERRED)
     AND no check has status FAIL
     AND top candidate is clearly distinguishable from next
  3. Otherwise                                              → UNKNOWN

AMBIGUITY RULE:
  If the top-2 candidates have candidate_scores within AMBIGUITY_DELTA of
  each other, the evidence cannot distinguish between them.
  Classification is UNKNOWN regardless of verification_score.
  This is intentional conservative behaviour.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional, Any

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import ReconstructionGap
from candidate_model import ReconstructionCandidate
from verifier_model import (
    ReconstructionResult, ReconstructionStatus,
    ConfidenceLabel, CheckResult,
)
from gap_detector import TECHNIQUE_STAGE_MAP


# ---------------------------------------------------------------
# CLASSIFICATION THRESHOLDS  — documented rationale
# ---------------------------------------------------------------

# INFERRED_THRESHOLD = 0.70
# Rationale: At 0.70, at least 70% of the weighted verification checks
# must pass. In a 7-check system this means roughly 5 checks must be
# PASS (not just UNKNOWN) at full weight. This is conservative.
INFERRED_THRESHOLD: float = 0.70

# AMBIGUITY_DELTA = 0.05
# Rationale: Two candidates within 0.05 of each other have essentially
# equivalent evidence support. Distinguishing them would require
# additional telemetry not available. The system must abstain.
# 0.05 corresponds to half the weight of the smallest dimension score.
AMBIGUITY_DELTA: float = 0.05

# MIN_TEMPORAL_WINDOW_SECS = 5.0
# Below this, most techniques cannot execute. Check → FAIL.
MIN_TEMPORAL_WINDOW_SECS: float = 5.0


# ---------------------------------------------------------------
# VERIFICATION CHECK WEIGHTS  (must sum to 1.0)
#
# These weights are independent of CANDIDATE_SCORE_WEIGHTS in
# candidate_scorer.py. They answer a different question:
#   "Is the evidence sufficient for a classification?"
#
# technique (0.25): Correct stage bridging is the strongest
#   verification signal — it is an objective, domain-grounded test.
# host (0.15): Host context limits candidate plausibility spatially.
# user (0.15): User context limits candidate plausibility by identity.
# process (0.15): Process lineage provides structural corroboration.
# temporal (0.10): Time window feasibility is a weak but necessary gate.
# graph (0.10): Graph coherence is useful but sparse in prototype.
# contradiction (0.10): Contradicting evidence is a veto signal.
# ---------------------------------------------------------------
VERIFICATION_CHECK_WEIGHTS: Dict[str, float] = {
    "technique":     0.25,
    "host":          0.15,
    "user":          0.15,
    "process":       0.15,
    "temporal":      0.10,
    "graph":         0.10,
    "contradiction": 0.10,
}

_w_total = sum(VERIFICATION_CHECK_WEIGHTS.values())
assert abs(_w_total - 1.0) < 1e-9, (
    f"VERIFICATION_CHECK_WEIGHTS must sum to 1.0, got {_w_total}"
)

# Score value per check result
_CHECK_SCORES: Dict[str, float] = {
    CheckResult.PASS:    1.0,
    CheckResult.UNKNOWN: 0.5,
    CheckResult.FAIL:    0.0,
}


class EvidenceVerifier:
    """
    Produces a ReconstructionResult for a gap given its ranked candidates.

    Input:
      - ReconstructionGap        (from ReconstructionGapDetector)
      - List[ReconstructionCandidate]  (ranked by CandidateScorer)
      - List[CyberEvent]         (OBSERVED events ONLY — no ground truth)
      - AttackGraphEngine        (built from observed events ONLY)

    Output:
      - ReconstructionResult with status OBSERVED / INFERRED / UNKNOWN

    INVARIANT: Ground truth is never an accepted parameter of this class.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.inferred_threshold: float = cfg.get(
            "inferred_threshold", INFERRED_THRESHOLD
        )
        self.ambiguity_delta: float = cfg.get(
            "ambiguity_delta", AMBIGUITY_DELTA
        )

    def verify(
        self,
        gap: ReconstructionGap,
        candidates: List[ReconstructionCandidate],
        observed_events: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> ReconstructionResult:
        """
        Produce a classification for the given gap.

        Args:
            gap:              The detected ReconstructionGap.
            candidates:       Ranked candidates from CandidateScorer.
                              Must be derived from observed data ONLY.
            observed_events:  All observed CyberEvents (no ground truth).
            graph:            AttackGraphEngine from observed events only.

        Returns:
            ReconstructionResult with OBSERVED / INFERRED / UNKNOWN.
        """
        event_map = {e.event_id: e for e in observed_events}
        prev_event = event_map.get(gap.previous_event_id)
        next_event = event_map.get(gap.next_event_id)

        # ── Case 1: No candidates → immediate UNKNOWN ───────────────────
        if not candidates:
            return self._build_result(
                gap=gap,
                status=ReconstructionStatus.UNKNOWN,
                candidate=None,
                checks={},
                verification_score=0.0,
                supporting=[],
                missing=["No reconstruction candidates could be generated from "
                         "the observed telemetry for this gap"],
                contradictory=[],
                explanation=(
                    "No candidates were generated. The knowledge base contained "
                    "no matching transition rule for the observed technique pair. "
                    "The system abstains: insufficient evidence to reconstruct this gap."
                ),
            )

        top = candidates[0]

        # ── Case 2: Direct telemetry check → may be OBSERVED ────────────
        direct_match = self._find_direct_telemetry(
            top, gap, observed_events, prev_event, next_event
        )
        if direct_match:
            return self._build_result(
                gap=gap,
                status=ReconstructionStatus.OBSERVED,
                candidate=top,
                checks={"direct_telemetry": CheckResult.PASS},
                verification_score=1.0,
                supporting=[
                    f"Direct telemetry match found: event {direct_match.event_id} "
                    f"({direct_match.technique_id}, {direct_match.event_type}) "
                    f"exists in observed data within the gap window"
                ],
                missing=[],
                contradictory=[],
                explanation=(
                    f"Event with technique {top.technique_id} and type "
                    f"{top.event_type} was directly observed within the gap "
                    f"window on {gap.affected_host}. Classification: OBSERVED."
                ),
            )

        # ── Cases 3+: Run full verification ─────────────────────────────
        if not prev_event or not next_event:
            return self._build_result(
                gap=gap, status=ReconstructionStatus.UNKNOWN,
                candidate=top, checks={}, verification_score=0.0,
                supporting=[], missing=["Boundary events not found in observed set"],
                contradictory=[],
                explanation="Boundary events for the gap could not be located.",
            )

        checks, evidence = self._run_checks(
            top, gap, prev_event, next_event, observed_events, graph
        )
        verification_score = self._compute_verification_score(checks)

        # ── Ambiguity: top-2 candidates within AMBIGUITY_DELTA ──────────
        is_ambiguous = False
        ambiguity_note = ""
        if len(candidates) > 1:
            second_best = candidates[1]
            delta = abs(top.candidate_score - second_best.candidate_score)
            if delta <= self.ambiguity_delta:
                is_ambiguous = True
                ambiguity_note = (
                    f"Top-2 candidates ({top.technique_id}: "
                    f"{top.candidate_score:.4f}, {second_best.technique_id}: "
                    f"{second_best.candidate_score:.4f}) have "
                    f"equivalent evidence support (delta={delta:.4f} ≤ "
                    f"{self.ambiguity_delta}). Direct telemetry is unavailable. "
                    "The available evidence cannot distinguish between these "
                    "candidates."
                )

        # ── Classification ───────────────────────────────────────────────
        status = self._classify(
            checks=checks,
            verification_score=verification_score,
            is_ambiguous=is_ambiguous,
        )

        explanation = self._build_explanation(
            status=status,
            top=top,
            checks=checks,
            verification_score=verification_score,
            is_ambiguous=is_ambiguous,
            ambiguity_note=ambiguity_note,
        )

        supporting = evidence["supporting"]
        missing    = evidence["missing"]
        contradictory = evidence["contradictory"]

        if is_ambiguous:
            contradictory.append(ambiguity_note)

        return self._build_result(
            gap=gap,
            status=status,
            candidate=top,
            checks=checks,
            verification_score=verification_score,
            supporting=supporting,
            missing=missing,
            contradictory=contradictory,
            explanation=explanation,
        )

    # ------------------------------------------------------------------
    # CLASSIFICATION
    # ------------------------------------------------------------------

    def _classify(
        self,
        checks: Dict[str, str],
        verification_score: float,
        is_ambiguous: bool,
    ) -> ReconstructionStatus:
        """
        Apply explicit conservative classification rules.

        Order of evaluation matters:
          1. Any FAIL check → UNKNOWN (veto)
          2. Ambiguous candidates → UNKNOWN
          3. verification_score below threshold → UNKNOWN
          4. Otherwise → INFERRED
        """
        # Rule 1: any FAIL is a veto — cannot classify as INFERRED
        if CheckResult.FAIL in checks.values():
            return ReconstructionStatus.UNKNOWN

        # Rule 2: ambiguous candidates
        if is_ambiguous:
            return ReconstructionStatus.UNKNOWN

        # Rule 3: verification threshold
        if verification_score < self.inferred_threshold:
            return ReconstructionStatus.UNKNOWN

        return ReconstructionStatus.INFERRED

    # ------------------------------------------------------------------
    # VERIFICATION CHECKS  (7 independent checks)
    # Each returns (CheckResult, explanation_string)
    # ------------------------------------------------------------------

    def _run_checks(
        self,
        candidate: ReconstructionCandidate,
        gap: ReconstructionGap,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        observed_events: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """
        Run all 7 verification checks. Returns check results dict and
        accumulated evidence lists.
        """
        supporting:    List[str] = []
        missing:       List[str] = []
        contradictory: List[str] = []

        def record(result: str, message: str) -> None:
            if result == CheckResult.PASS:
                supporting.append(message)
            elif result == CheckResult.FAIL:
                contradictory.append(message)
            else:
                missing.append(message)

        checks: Dict[str, str] = {}

        # A. Temporal consistency
        r, msg = self._check_temporal(gap)
        checks["temporal"] = r
        record(r, f"[temporal] {msg}")

        # B. Host consistency
        r, msg = self._check_host(prev_event, next_event)
        checks["host"] = r
        record(r, f"[host] {msg}")

        # C. User consistency
        r, msg = self._check_user(prev_event, next_event)
        checks["user"] = r
        record(r, f"[user] {msg}")

        # D. Process consistency
        r, msg = self._check_process(prev_event, next_event)
        checks["process"] = r
        record(r, f"[process] {msg}")

        # E. Technique compatibility
        r, msg = self._check_technique(candidate, prev_event, next_event)
        checks["technique"] = r
        record(r, f"[technique] {msg}")

        # F. Graph consistency
        r, msg = self._check_graph(prev_event, next_event, graph)
        checks["graph"] = r
        record(r, f"[graph] {msg}")

        # G. Contradiction detection
        r, msg = self._check_contradiction(
            candidate, gap, prev_event, next_event, observed_events
        )
        checks["contradiction"] = r
        record(r, f"[contradiction] {msg}")

        evidence = {
            "supporting":    supporting,
            "missing":       missing,
            "contradictory": contradictory,
        }
        return checks, evidence

    # ------------------------------------------------------------------
    # Individual check implementations
    # ------------------------------------------------------------------

    def _check_temporal(
        self, gap: ReconstructionGap
    ) -> Tuple[str, str]:
        """
        A. Temporal consistency
        Is the gap window large enough for the candidate technique to execute?
        Below MIN_TEMPORAL_WINDOW_SECS the candidate is almost certainly impossible.
        """
        w = gap.temporal_gap_seconds
        if w >= MIN_TEMPORAL_WINDOW_SECS:
            return (
                CheckResult.PASS,
                f"Gap window ({w:.1f}s) is sufficient for candidate execution"
            )
        return (
            CheckResult.FAIL,
            f"Gap window ({w:.1f}s) is too narrow — "
            f"below minimum {MIN_TEMPORAL_WINDOW_SECS}s threshold"
        )

    def _check_host(
        self, prev_event: CyberEvent, next_event: CyberEvent
    ) -> Tuple[str, str]:
        """
        B. Host consistency
        Candidate is expected to execute on the same host as the previous event.
        A host change without a network event is suspicious but not a hard FAIL —
        it reduces certainty without conclusively refuting the candidate.
        """
        if prev_event.host_id == next_event.host_id:
            return (
                CheckResult.PASS,
                f"Host context consistent across gap ({prev_event.host_id})"
            )
        return (
            CheckResult.UNKNOWN,
            f"Host changes across gap ({prev_event.host_id} → {next_event.host_id}); "
            "candidate origin host is uncertain"
        )

    def _check_user(
        self, prev_event: CyberEvent, next_event: CyberEvent
    ) -> Tuple[str, str]:
        """
        C. User consistency
        Candidate is expected to execute under the same user account.
        Missing user_id is treated as inconclusive.
        """
        if not prev_event.user_id:
            return (
                CheckResult.UNKNOWN,
                "User context unavailable on preceding event"
            )
        if not next_event.user_id:
            return (
                CheckResult.UNKNOWN,
                "User context unavailable on following event"
            )
        if prev_event.user_id == next_event.user_id:
            return (
                CheckResult.PASS,
                f"User context consistent across gap ({prev_event.user_id})"
            )
        return (
            CheckResult.UNKNOWN,
            f"User context changes ({prev_event.user_id} → {next_event.user_id}); "
            "candidate may run under either user account"
        )

    def _check_process(
        self, prev_event: CyberEvent, next_event: CyberEvent
    ) -> Tuple[str, str]:
        """
        D. Process consistency
        Same process or direct parent-child link provides structural corroboration.
        No process data at all is treated as UNKNOWN (inconclusive, not contradictory).
        """
        if not prev_event.process_id:
            return (
                CheckResult.UNKNOWN,
                "No process telemetry on preceding event"
            )
        if prev_event.process_id == next_event.process_id:
            return (
                CheckResult.PASS,
                f"Same process ({prev_event.process_name or prev_event.process_id}) "
                "active across gap"
            )
        if next_event.parent_process_id == prev_event.process_id:
            return (
                CheckResult.PASS,
                f"Parent-child process relationship: "
                f"{prev_event.process_id} → {next_event.process_id}"
            )
        return (
            CheckResult.UNKNOWN,
            f"No direct process lineage between "
            f"{prev_event.process_id} and {next_event.process_id}"
        )

    def _check_technique(
        self,
        candidate: ReconstructionCandidate,
        prev_event: CyberEvent,
        next_event: CyberEvent,
    ) -> Tuple[str, str]:
        """
        E. Technique compatibility
        Candidate must occupy a stage strictly between prev and next event stages.
        This is the strongest verification signal.
        Not-mapped techniques produce UNKNOWN (inconclusive, not refuting).
        A candidate outside the expected range produces FAIL.
        """
        if not candidate.technique_id:
            return CheckResult.UNKNOWN, "Candidate has no technique ID"

        prev_stage = TECHNIQUE_STAGE_MAP.get(prev_event.technique_id or "")
        next_stage = TECHNIQUE_STAGE_MAP.get(next_event.technique_id or "")
        cand_stage = TECHNIQUE_STAGE_MAP.get(candidate.technique_id or "")

        if any(s is None for s in (prev_stage, next_stage, cand_stage)):
            unmapped = [
                t for t, s in [
                    (prev_event.technique_id, prev_stage),
                    (next_event.technique_id, next_stage),
                    (candidate.technique_id,  cand_stage),
                ] if s is None and t
            ]
            return (
                CheckResult.UNKNOWN,
                f"Technique stage not mapped for: {unmapped}. "
                "Cannot verify stage bridging."
            )

        if prev_stage < cand_stage < next_stage:
            return (
                CheckResult.PASS,
                f"Candidate technique stage ({cand_stage}) correctly bridges "
                f"gap ({prev_stage} → {cand_stage} → {next_stage})"
            )

        if cand_stage <= prev_stage or cand_stage >= next_stage:
            return (
                CheckResult.FAIL,
                f"Candidate technique stage ({cand_stage}) does not bridge "
                f"the gap ({prev_stage} → {next_stage}); "
                "this technique cannot explain the observed transition"
            )

        return (
            CheckResult.UNKNOWN,
            "Technique stage relationship is ambiguous"
        )

    def _check_graph(
        self,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        graph: AttackGraphEngine,
    ) -> Tuple[str, str]:
        """
        F. Graph consistency
        Checks whether the boundary events share graph context that a
        candidate could plausibly connect through.
        """
        prev_neighbors = set(graph.get_neighbors(prev_event.event_id))
        next_neighbors = set(graph.get_neighbors(next_event.event_id))
        shared = prev_neighbors & next_neighbors

        if shared:
            return (
                CheckResult.PASS,
                f"Boundary events share {len(shared)} graph node(s) "
                f"({list(shared)[:3]}); candidate fits within observed context"
            )
        return (
            CheckResult.UNKNOWN,
            "No shared graph context between boundary events; "
            "candidate would bridge disconnected subgraphs"
        )

    def _check_contradiction(
        self,
        candidate: ReconstructionCandidate,
        gap: ReconstructionGap,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        observed_events: List[CyberEvent],
    ) -> Tuple[str, str]:
        """
        G. Contradiction detection
        Searches for observed events within the gap window that would make
        the candidate unlikely or impossible.

        FAIL: An observed event inside the window on the same host is at a
              HIGHER technique stage than the candidate, suggesting the
              candidate's stage would be redundant or out of sequence.
        UNKNOWN: An event inside the window exists but its relationship to
                 the candidate is unclear.
        PASS: No contradicting events found in the gap window.
        """
        cand_stage = TECHNIQUE_STAGE_MAP.get(candidate.technique_id or "")

        # Events strictly inside the gap window on the same host
        window_events = [
            e for e in observed_events
            if (
                e.event_id != prev_event.event_id
                and e.event_id != next_event.event_id
                and e.host_id == prev_event.host_id
                and prev_event.timestamp < e.timestamp < next_event.timestamp
            )
        ]

        if not window_events:
            return (
                CheckResult.PASS,
                "No contradicting events observed within the gap window"
            )

        # Check if any window event is at a stage that contradicts the candidate
        next_stage = TECHNIQUE_STAGE_MAP.get(next_event.technique_id or "")
        for we in window_events:
            we_stage = TECHNIQUE_STAGE_MAP.get(we.technique_id or "")
            if (
                cand_stage is not None
                and we_stage is not None
                and next_stage is not None
                and we_stage >= next_stage  # proxy: advanced stage
            ):
                # More conservative: if stage is ahead of the candidate
                if we_stage > cand_stage:
                    return (
                        CheckResult.FAIL,
                        f"Observed event {we.event_id} (stage {we_stage}) "
                        f"within gap window is at a later stage than candidate "
                        f"(stage {cand_stage}), suggesting out-of-sequence activity"
                    )

        # Events exist in window but can't determine relationship definitively
        ids = [e.event_id for e in window_events]
        return (
            CheckResult.UNKNOWN,
            f"Observed event(s) {ids} exist within gap window; "
            "relationship to candidate is uncertain"
        )

    # ------------------------------------------------------------------
    # SCORING + CONFIDENCE
    # ------------------------------------------------------------------

    def _compute_verification_score(self, checks: Dict[str, str]) -> float:
        """
        Weighted verification score.

        score = Σ (weight_i × check_value_i)
        where check_value: PASS=1.0, UNKNOWN=0.5, FAIL=0.0

        Bounded [0, 1] by construction (weights sum to 1.0, values in [0,1]).
        """
        if not checks:
            return 0.0
        return round(
            sum(
                VERIFICATION_CHECK_WEIGHTS.get(k, 0.0) * _CHECK_SCORES.get(v, 0.0)
                for k, v in checks.items()
            ),
            4,
        )

    def _confidence_label(self, verification_score: float) -> ConfidenceLabel:
        """
        Map verification_score to qualitative confidence label.

        HIGH   ≥ 0.80 — Most checks passed; strong evidence base.
        MEDIUM ≥ 0.60 — Mixed checks; moderate evidence base.
        LOW    < 0.60 — Many unknown/failed checks; weak evidence base.

        IMPORTANT: These labels are NOT calibrated probabilities.
        """
        if verification_score >= 0.80:
            return ConfidenceLabel.HIGH
        if verification_score >= 0.60:
            return ConfidenceLabel.MEDIUM
        return ConfidenceLabel.LOW

    # ------------------------------------------------------------------
    # DIRECT TELEMETRY CHECK
    # ------------------------------------------------------------------

    def _find_direct_telemetry(
        self,
        candidate: ReconstructionCandidate,
        gap: ReconstructionGap,
        observed_events: List[CyberEvent],
        prev_event: Optional[CyberEvent],
        next_event: Optional[CyberEvent],
    ) -> Optional[CyberEvent]:
        """
        Check whether an observed event DIRECTLY corresponds to the candidate.

        Criteria:
          - Same technique_id as candidate
          - Same event_type as candidate
          - Strictly within the gap's temporal window
          - On the same host as the gap

        Returns the matching event if found, else None.
        """
        if not prev_event or not next_event:
            return None

        for e in observed_events:
            if (
                e.event_id != prev_event.event_id
                and e.event_id != next_event.event_id
                and e.technique_id == candidate.technique_id
                and e.event_type == candidate.event_type
                and e.host_id == gap.affected_host
                and prev_event.timestamp < e.timestamp < next_event.timestamp
            ):
                return e
        return None

    # ------------------------------------------------------------------
    # RESULT BUILDER
    # ------------------------------------------------------------------

    def _build_explanation(
        self,
        status: ReconstructionStatus,
        top: Optional[ReconstructionCandidate],
        checks: Dict[str, str],
        verification_score: float,
        is_ambiguous: bool,
        ambiguity_note: str,
    ) -> str:
        if status == ReconstructionStatus.OBSERVED:
            return (
                f"Event of type {top.event_type} with technique {top.technique_id} "
                "was directly observed in telemetry within the gap window. "
                "Classification: OBSERVED."
            )

        if not top:
            return (
                "No reconstruction candidates could be generated. "
                "The system abstains: UNKNOWN."
            )

        if is_ambiguous:
            return (
                f"Multiple candidates have comparable evidence support. "
                f"{ambiguity_note} "
                f"Classification withheld: UNKNOWN."
            )

        fail_checks = [k for k, v in checks.items() if v == CheckResult.FAIL]
        if fail_checks:
            return (
                f"Candidate {top.technique_id} failed {len(fail_checks)} "
                f"verification check(s): {', '.join(fail_checks)}. "
                f"A FAIL check vetoes INFERRED classification. Result: UNKNOWN."
            )

        passed  = [k for k, v in checks.items() if v == CheckResult.PASS]
        unknown = [k for k, v in checks.items() if v == CheckResult.UNKNOWN]

        if status == ReconstructionStatus.INFERRED:
            return (
                f"Candidate {top.technique_name or top.technique_id} "
                f"(Evidence Support Score: {top.candidate_score:.4f}) passed "
                f"{len(passed)}/{len(checks)} verification checks "
                f"(verification score: {verification_score:.4f} ≥ "
                f"{self.inferred_threshold}). "
                f"{len(unknown)} check(s) had insufficient evidence but no "
                "contradictions were found. Classification: INFERRED. "
                "Note: INFERRED does not mean the event definitely occurred."
            )

        return (
            f"Candidate {top.technique_id} achieved verification score "
            f"{verification_score:.4f}, below the INFERRED threshold "
            f"({self.inferred_threshold}). "
            f"{len(passed)} checks PASS, {len(unknown)} checks UNKNOWN. "
            "Classification: UNKNOWN."
        )

    def _build_result(
        self,
        gap: ReconstructionGap,
        status: ReconstructionStatus,
        candidate: Optional[ReconstructionCandidate],
        checks: Dict[str, str],
        verification_score: float,
        supporting: List[str],
        missing: List[str],
        contradictory: List[str],
        explanation: str,
    ) -> ReconstructionResult:
        return ReconstructionResult(
            reconstruction_id=f"REC-{str(uuid.uuid4())[:8].upper()}",
            gap_id=gap.gap_id,
            status=status,
            candidate_id=candidate.candidate_id if candidate else None,
            event_type=candidate.event_type if candidate else None,
            technique_id=candidate.technique_id if candidate else None,
            technique_name=candidate.technique_name if candidate else None,
            candidate_score=candidate.candidate_score if candidate else None,
            verification_score=verification_score,
            confidence_label=self._confidence_label(verification_score),
            supporting_evidence=supporting,
            missing_evidence=missing,
            contradictory_evidence=contradictory,
            verification_checks=checks,
            explanation=explanation,
            created_at=datetime.now(timezone.utc),
        )
