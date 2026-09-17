"""
candidate_generator.py — CyberScope CandidateGenerator

Answers: "What events/techniques could plausibly connect this gap?"

ARCHITECTURAL SEPARATION:
  CandidateGenerator  →  proposes candidates (WHAT)
  CandidateScorer     →  scores candidates   (HOW WELL SUPPORTED)

These two responsibilities are kept in separate classes intentionally.

SECURITY INVARIANT:
  This module ONLY operates on observed CyberEvents.
  It NEVER receives, reads, or uses ground_truth_events.
  The knowledge layer is built from domain knowledge, NOT from the
  hidden event or any evaluation label.

KNOWLEDGE LAYER LIMITATION:
  The transition rules below are a demonstration knowledge base for the
  prototype. They cover a small set of common attack patterns.
  They are NOT a comprehensive claim about all possible attack sequences.
  Coverage should be extended for production use.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

from models import CyberEvent
from graph_engine import AttackGraphEngine
from gap_model import ReconstructionGap
from candidate_model import ReconstructionCandidate


# ---------------------------------------------------------------
# CANDIDATE BLUEPRINT
# Internal structure used by the generator to describe a candidate
# before it has been scored. The scorer creates the final
# ReconstructionCandidate from this.
# ---------------------------------------------------------------

@dataclass
class CandidateBlueprint:
    technique_id: str
    technique_name: str
    event_type: str
    description: str
    required_preconditions: List[str] = field(default_factory=list)
    # Rough expected host context: "same" = same host, "any" = host agnostic
    expected_host_context: str = "same"
    # Rough expected user context
    expected_user_context: str = "same"
    # Knowledge rule that produced this candidate
    source_rule_id: str = ""


# ---------------------------------------------------------------
# TRANSITION KNOWLEDGE BASE
#
# Each rule maps a set of (prev_technique_ids, next_technique_ids)
# to a list of CandidateBlueprints.
#
# Rules are matched by exact technique ID first, then by technique
# stage range if no exact match is found.
#
# LIMITATION: This is demonstration knowledge for the prototype.
# It covers common Windows-centric lateral movement patterns.
# It is NOT universally valid for all environments or attack variants.
# ---------------------------------------------------------------

import json
import os
from dataclasses import dataclass, field

@dataclass
class CandidateBlueprint:
    technique_id: str
    technique_name: str
    event_type: str
    description: str
    required_preconditions: List[str] = field(default_factory=list)
    expected_host_context: str = "same"
    expected_user_context: str = "same"
    source_rule_id: str = ""

@dataclass
class TransitionRule:
    rule_id: str
    description: str
    prev_technique_ids: Set[str]
    next_technique_ids: Set[str]
    blueprints: List[CandidateBlueprint]

def load_knowledge_base():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(base_dir, "knowledge", "transitions.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rules = []
    for r in data.get("transition_rules", []):
        bps = []
        for bp in r.get("blueprints", []):
            bps.append(CandidateBlueprint(
                source_rule_id=bp.get("source_rule_id", ""),
                technique_id=bp["technique_id"],
                technique_name=bp["technique_name"],
                event_type=bp["event_type"],
                description=bp["description"],
                required_preconditions=bp.get("required_preconditions", []),
                expected_host_context=bp.get("expected_host_context", "same"),
                expected_user_context=bp.get("expected_user_context", "same")
            ))
        rules.append(TransitionRule(
            rule_id=r["rule_id"],
            description=r.get("description", ""),
            prev_technique_ids=set(r.get("prev_technique_ids", [])),
            next_technique_ids=set(r.get("next_technique_ids", [])),
            blueprints=bps
        ))
        
    fallbacks = {}
    for k, bp_list in data.get("stage_fallback_rules", {}).items():
        parts = k.split("_")
        stage_key = (int(parts[0]), int(parts[1]))
        bps = []
        for bp in bp_list:
            bps.append(CandidateBlueprint(
                source_rule_id=bp.get("source_rule_id", ""),
                technique_id=bp["technique_id"],
                technique_name=bp["technique_name"],
                event_type=bp["event_type"],
                description=bp["description"],
                required_preconditions=bp.get("required_preconditions", []),
                expected_host_context=bp.get("expected_host_context", "same"),
                expected_user_context=bp.get("expected_user_context", "same")
            ))
        fallbacks[stage_key] = bps
        
    return rules, fallbacks

TRANSITION_RULES, STAGE_FALLBACK_RULES = load_knowledge_base()

# Import stage map to compute stage-based fallback
from gap_detector import TECHNIQUE_STAGE_MAP


class CandidateGenerator:
    """
    Proposes plausible candidate events for a detected ReconstructionGap.

    SECURITY INVARIANT: Only observed CyberEvents and AttackGraph are
    accepted as input. Ground truth is never passed to this class.

    ABSTENTION: If no matching rule exists in the knowledge base for the
    observed transition, the generator returns an empty list. This is the
    correct behaviour — the system must be capable of abstaining rather
    than fabricating unsupported candidates.
    """

    def generate(
        self,
        gap: ReconstructionGap,
        observed_events: List[CyberEvent],
        graph: AttackGraphEngine,
    ) -> List[ReconstructionCandidate]:
        """
        Generate candidate blueprints for the gap and return unscored
        ReconstructionCandidate objects (all scores = 0.0, rank = 0).
        CandidateScorer must be called subsequently to fill in scores.

        Args:
            gap: The detected ReconstructionGap (OBSERVED data only).
            observed_events: All observed CyberEvents for the scenario.
            graph: AttackGraphEngine built from observed events only.

        Returns:
            List of unscored ReconstructionCandidate objects,
            or an empty list if evidence is insufficient.
        """
        # Locate boundary events by ID
        event_map = {e.event_id: e for e in observed_events}
        prev_event = event_map.get(gap.previous_event_id)
        next_event = event_map.get(gap.next_event_id)

        if not prev_event or not next_event:
            return []

        blueprints = self._lookup_blueprints(prev_event, next_event)

        if not blueprints:
            return []

        candidates = []
        for bp in blueprints:
            candidates.append(
                ReconstructionCandidate(
                    candidate_id=f"CAND-{str(uuid.uuid4())[:8].upper()}",
                    gap_id=gap.gap_id,
                    event_type=bp.event_type,
                    technique_id=bp.technique_id,
                    technique_name=bp.technique_name,
                    description=bp.description,
                    required_preconditions=bp.required_preconditions,
                    # Supporting/contradictory features populated by scorer
                    supporting_features=[],
                    contradictory_features=[],
                    # All scores start at 0.0 — scorer fills these in
                    temporal_score=0.0,
                    host_score=0.0,
                    user_score=0.0,
                    process_score=0.0,
                    technique_score=0.0,
                    graph_score=0.0,
                    candidate_score=0.0,
                    rank=0,
                )
            )
        return candidates

    def _lookup_blueprints(
        self,
        prev_event: CyberEvent,
        next_event: CyberEvent,
    ) -> List[CandidateBlueprint]:
        """
        Find matching blueprints from the knowledge base.
        Tries exact technique match first, then stage-based fallback.
        """
        prev_tid = prev_event.technique_id or ""
        next_tid = next_event.technique_id or ""

        # 1. Exact technique-to-technique match
        for rule in TRANSITION_RULES:
            if prev_tid in rule.prev_technique_ids and next_tid in rule.next_technique_ids:
                return list(rule.blueprints)

        # 2. Stage-based fallback
        prev_stage = TECHNIQUE_STAGE_MAP.get(prev_tid)
        next_stage = TECHNIQUE_STAGE_MAP.get(next_tid)

        if prev_stage is not None and next_stage is not None:
            key = (prev_stage, next_stage)
            if key in STAGE_FALLBACK_RULES:
                return list(STAGE_FALLBACK_RULES[key])

        # 3. No match — abstain
        return []
