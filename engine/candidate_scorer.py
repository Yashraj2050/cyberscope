"""
candidate_scorer.py — CyberScope CandidateScorer

Answers: "Given the observed evidence, which candidate is best supported?"

ARCHITECTURAL SEPARATION:
  CandidateGenerator  →  proposes candidates (WHAT)
  CandidateScorer     →  scores candidates   (HOW WELL SUPPORTED)

These two responsibilities are intentionally in separate classes.

SCORING PHILOSOPHY:
  The gap detector uses BINARY signals to answer: "Is this location suspicious?"
  The candidate scorer uses CONTINUOUS (0–1) dimension scores to answer:
  "Which candidate is most consistent with the surrounding observed evidence?"

  These are mathematically and conceptually distinct questions.
  Do not conflate gap_score with candidate_score.

DISCLAIMER:
  "Candidate score represents relative evidence support and is not a
  calibrated probability or accuracy measurement."
  Present scores as "Evidence Support Score" in the UI, not as percentages.
"""

from typing import List, Dict, Any, Optional
from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import ReconstructionGap
from candidate_model import ReconstructionCandidate
from gap_detector import TECHNIQUE_STAGE_MAP


# ---------------------------------------------------------------
# CANDIDATE SCORE WEIGHTS  (must sum to 1.0)
#
# Rationale:
#   technique_score (0.30): Stage bridging is the strongest indicator.
#     A candidate that correctly fills the technique stage gap has
#     the strongest structural support.
#   host_score (0.25): Host context directly constrains what is plausible.
#     An LSASS dump on HOST-B is irrelevant if the gap is on HOST-A.
#   user_score (0.20): User context is a strong filter — credential
#     operations are user-bound in most Windows environments.
#   process_score (0.15): Process lineage provides supporting structural
#     evidence but may be absent without breaking plausibility.
#   temporal_score (0.05): The time window is a weak constraint —
#     most techniques can execute within a wide range.
#   graph_score (0.05): Graph topology is useful context but secondary
#     to domain-knowledge signals in a sparse prototype graph.
# ---------------------------------------------------------------
CANDIDATE_SCORE_WEIGHTS: Dict[str, float] = {
    "technique_score": 0.30,
    "host_score":      0.25,
    "user_score":      0.20,
    "process_score":   0.15,
    "temporal_score":  0.05,
    "graph_score":     0.05,
}

_weight_total = sum(CANDIDATE_SCORE_WEIGHTS.values())
assert abs(_weight_total - 1.0) < 1e-9, (
    f"CANDIDATE_SCORE_WEIGHTS must sum to 1.0, got {_weight_total}"
)

# Minimum temporal window (seconds) for a technique to be plausible
MIN_TEMPORAL_WINDOW: float = 5.0   # < 5s is extremely tight
COMFORTABLE_WINDOW:  float = 30.0  # ≥ 30s gives full temporal score


class CandidateScorer:
    """
    Scores and ranks ReconstructionCandidate objects against observed evidence.

    Input:  Unscored candidates from CandidateGenerator.
    Output: New ReconstructionCandidate instances with all dimension scores,
            candidate_score, supporting_features, contradictory_features,
            and rank assigned.

    INVARIANT: Only observed CyberEvents and the observed AttackGraph are
    used for scoring. Ground truth is never provided or referenced.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        self.weights: Dict[str, float] = cfg.get(
            "weights", CANDIDATE_SCORE_WEIGHTS
        )

    def score_and_rank(
        self,
        candidates: List[ReconstructionCandidate],
        gap: ReconstructionGap,
        observed_events: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> List[ReconstructionCandidate]:
        """
        Score all candidates for a gap and return them ranked best-first.

        Args:
            candidates: Unscored candidates from CandidateGenerator.
            gap:        The ReconstructionGap these candidates address.
            observed_events: All observed CyberEvents.
            graph:      AttackGraphEngine built from observed events.

        Returns:
            New list of ReconstructionCandidate objects with scores filled
            and sorted by candidate_score descending (rank 1 = best).
        """
        if not candidates:
            return []

        event_map = {e.event_id: e for e in observed_events}
        prev_event = event_map.get(gap.previous_event_id)
        next_event = event_map.get(gap.next_event_id)

        if not prev_event or not next_event:
            return candidates  # Cannot score without boundary events

        scored: List[ReconstructionCandidate] = []
        for candidate in candidates:
            scored.append(
                self._score_one(
                    candidate, gap, prev_event, next_event, observed_events, graph
                )
            )

        # Sort by candidate_score descending
        scored.sort(key=lambda c: c.candidate_score, reverse=True)

        # Assign ranks (1-based, ties share the same rank)
        ranked = []
        current_rank = 1
        for i, c in enumerate(scored):
            if i > 0 and c.candidate_score < scored[i - 1].candidate_score:
                current_rank = i + 1
            ranked.append(c.model_copy(update={"rank": current_rank}))

        return ranked

    # ------------------------------------------------------------------
    # INTERNAL: score one candidate
    # ------------------------------------------------------------------

    def _score_one(
        self,
        candidate: ReconstructionCandidate,
        gap: ReconstructionGap,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        observed_events: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> ReconstructionCandidate:
        supporting: List[str] = []
        contradictory: List[str] = []

        t_score  = self._score_temporal(gap, supporting, contradictory)
        h_score  = self._score_host(candidate, prev_event, next_event, supporting, contradictory)
        u_score  = self._score_user(prev_event, next_event, supporting, contradictory)
        p_score  = self._score_process(prev_event, next_event, supporting, contradictory)
        te_score = self._score_technique(candidate, prev_event, next_event, supporting, contradictory)
        g_score  = self._score_graph(candidate, prev_event, next_event, graph, supporting, contradictory)

        weighted = (
            self.weights["temporal_score"]  * t_score  +
            self.weights["host_score"]      * h_score  +
            self.weights["user_score"]      * u_score  +
            self.weights["process_score"]   * p_score  +
            self.weights["technique_score"] * te_score +
            self.weights["graph_score"]     * g_score
        )
        candidate_score = round(min(max(weighted, 0.0), 1.0), 4)

        return candidate.model_copy(update={
            "temporal_score":        round(t_score,  4),
            "host_score":            round(h_score,  4),
            "user_score":            round(u_score,  4),
            "process_score":         round(p_score,  4),
            "technique_score":       round(te_score, 4),
            "graph_score":           round(g_score,  4),
            "candidate_score":       candidate_score,
            "supporting_features":   supporting,
            "contradictory_features": contradictory,
        })

    # ------------------------------------------------------------------
    # DIMENSION SCORERS
    # Each returns a float in [0.0, 1.0] and appends to evidence lists.
    # ------------------------------------------------------------------

    def _score_temporal(
        self,
        gap: ReconstructionGap,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score temporal feasibility.
        Most techniques require at least MIN_TEMPORAL_WINDOW seconds.
        A COMFORTABLE_WINDOW or more gives a full score.
        Intermediate windows are linearly interpolated.
        """
        w = gap.temporal_gap_seconds
        if w >= COMFORTABLE_WINDOW:
            supporting.append(
                f"Sufficient temporal window ({w:.0f}s ≥ {COMFORTABLE_WINDOW:.0f}s threshold)"
            )
            return 1.0
        elif w >= MIN_TEMPORAL_WINDOW:
            ratio = (w - MIN_TEMPORAL_WINDOW) / (COMFORTABLE_WINDOW - MIN_TEMPORAL_WINDOW)
            supporting.append(
                f"Narrow but feasible temporal window ({w:.1f}s)"
            )
            return round(0.5 + 0.5 * ratio, 4)
        else:
            contradictory.append(
                f"Very tight temporal window ({w:.1f}s < {MIN_TEMPORAL_WINDOW:.0f}s) "
                "— most techniques are unlikely in this interval"
            )
            return 0.2

    def _score_host(
        self,
        candidate: ReconstructionCandidate,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score host compatibility.
        - Same host on both sides: candidate is fully plausible on that host.
        - Host changes: the candidate may still be plausible (transition),
          but loses some evidence support.
        """
        if prev_event.host_id == next_event.host_id:
            supporting.append(
                f"Same host context on both sides of gap ({prev_event.host_id})"
            )
            return 1.0
        else:
            # Different hosts: candidate may bridge a host transition
            contradictory.append(
                f"Host context changes across gap "
                f"({prev_event.host_id} → {next_event.host_id}); "
                "candidate expected on source host"
            )
            return 0.55

    def _score_user(
        self,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score user context compatibility.
        Same user = full support. Missing user = neutral. Changed user = penalised.
        """
        if not prev_event.user_id:
            return 0.7  # Missing user context, neutral

        if prev_event.user_id == next_event.user_id:
            supporting.append(
                f"Consistent user context ({prev_event.user_id}) on both sides"
            )
            return 1.0

        if not next_event.user_id:
            return 0.7  # Missing next user, neutral

        contradictory.append(
            f"User context changes across gap "
            f"({prev_event.user_id} → {next_event.user_id}); "
            "candidate is associated with the prior user"
        )
        return 0.5

    def _score_process(
        self,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score process relationship.
        Same process or parent-child link between boundary events gives higher
        confidence that the candidate fits within the observed execution chain.
        """
        if not prev_event.process_id:
            contradictory.append("No process telemetry on preceding event")
            return 0.5

        if prev_event.process_id == next_event.process_id:
            supporting.append(
                f"Same process ({prev_event.process_name or prev_event.process_id}) "
                "active on both sides of gap"
            )
            return 0.9

        if next_event.parent_process_id == prev_event.process_id:
            supporting.append(
                f"Parent-child process relationship across gap "
                f"({prev_event.process_id} → {next_event.process_id})"
            )
            return 0.8

        # No direct relationship
        contradictory.append(
            f"No direct process lineage between "
            f"{prev_event.process_id} and {next_event.process_id}"
        )
        return 0.5

    def _score_technique(
        self,
        candidate: ReconstructionCandidate,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score how well the candidate bridges the MITRE technique transition.

        Perfect bridge: candidate stage is strictly between prev and next stages.
        Partial bridge: candidate is at one of the boundary stages.
        Off-range: candidate is outside the expected range.
        """
        if not candidate.technique_id:
            return 0.5

        prev_stage  = TECHNIQUE_STAGE_MAP.get(prev_event.technique_id  or "")
        next_stage  = TECHNIQUE_STAGE_MAP.get(next_event.technique_id  or "")
        cand_stage  = TECHNIQUE_STAGE_MAP.get(candidate.technique_id   or "")

        if any(s is None for s in (prev_stage, next_stage, cand_stage)):
            return 0.5  # Unmapped technique — neutral

        if prev_stage < cand_stage < next_stage:
            supporting.append(
                f"Technique stage ({cand_stage}) correctly bridges the gap "
                f"({prev_stage} → {cand_stage} → {next_stage})"
            )
            return 1.0

        if cand_stage == prev_stage or cand_stage == next_stage:
            contradictory.append(
                f"Technique stage ({cand_stage}) is at boundary rather than "
                "bridging the gap"
            )
            return 0.5

        # Outside expected range
        contradictory.append(
            f"Technique stage ({cand_stage}) is outside the expected "
            f"gap range ({prev_stage}–{next_stage})"
        )
        return 0.2

    def _score_graph(
        self,
        candidate: ReconstructionCandidate,
        prev_event: CyberEvent,
        next_event: CyberEvent,
        graph: AttackGraphEngine,
        supporting: List[str],
        contradictory: List[str],
    ) -> float:
        """
        Score graph topology compatibility.

        Checks whether the candidate would logically fit within the
        observed attack graph by examining existing node relationships.
        """
        prev_neighbors = set(graph.get_neighbors(prev_event.event_id))
        next_neighbors = set(graph.get_neighbors(next_event.event_id))
        shared = prev_neighbors & next_neighbors

        # Both events share a common context node (e.g., same process/host)
        if shared:
            supporting.append(
                f"Boundary events share {len(shared)} common graph node(s): "
                f"{list(shared)[:3]}"
            )
            base = 0.85
        else:
            contradictory.append(
                "No shared graph context between boundary events — "
                "candidate would need to bridge disconnected subgraphs"
            )
            base = 0.55

        # Check if the candidate's technique node already exists in the graph
        if candidate.technique_id and graph.graph.has_node(candidate.technique_id):
            supporting.append(
                f"Technique node {candidate.technique_id} already present in graph"
            )
            return min(base + 0.10, 1.0)

        return base
