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

@dataclass
class TransitionRule:
    rule_id: str
    description: str
    prev_technique_ids: Set[str]
    next_technique_ids: Set[str]
    blueprints: List[CandidateBlueprint]


TRANSITION_RULES: List[TransitionRule] = [
    # -------------------------------------------------------
    # TR-001: Execution → Lateral Movement (Remote Services)
    # The most common pattern: execution capability (e.g., PowerShell)
    # is used to dump credentials, which are then used for SMB/WinRM/RDP.
    # -------------------------------------------------------
    TransitionRule(
        rule_id="TR-001",
        description="Execution to Remote-Service Lateral Movement via Credential Access",
        prev_technique_ids={
            "T1059", "T1059.001", "T1059.003", "T1059.005",
        },
        next_technique_ids={
            "T1021", "T1021.001", "T1021.002", "T1021.006",
            "T1569", "T1569.002",
        },
        blueprints=[
            CandidateBlueprint(
                source_rule_id="TR-001",
                technique_id="T1003.001",
                technique_name="OS Credential Dumping: LSASS Memory",
                event_type="ProcessAccess",
                description=(
                    "A process (e.g., PowerShell or spawned tool) accesses LSASS "
                    "memory to extract plaintext credentials or NTLM hashes. "
                    "These credentials are subsequently used to authenticate on "
                    "remote systems via SMB or WinRM."
                ),
                required_preconditions=[
                    "Execution capability on the host (PowerShell or similar)",
                    "Administrator or SYSTEM privilege to access LSASS process memory",
                    "SeDebugPrivilege or equivalent enabled for the calling process",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
            CandidateBlueprint(
                source_rule_id="TR-001",
                technique_id="T1003",
                technique_name="OS Credential Dumping",
                event_type="ProcessAccess",
                description=(
                    "Generic OS credential dumping activity. The attacker uses an "
                    "execution foothold to access stored credentials (registry, "
                    "memory, or files) before authenticating to a remote host."
                ),
                required_preconditions=[
                    "Execution capability on the host",
                    "Elevated privileges sufficient to access credential stores",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
            CandidateBlueprint(
                source_rule_id="TR-001",
                technique_id="T1558.003",
                technique_name="Steal or Forge Kerberos Tickets: Kerberoasting",
                event_type="NetworkAccess",
                description=(
                    "The attacker requests Kerberos service tickets for domain "
                    "accounts and extracts them for offline cracking. Cracked "
                    "credentials are then used for lateral movement."
                ),
                required_preconditions=[
                    "Active domain user session on a domain-joined host",
                    "Network access to a domain controller",
                    "Target service accounts must have SPNs registered",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
        ],
    ),

    # -------------------------------------------------------
    # TR-002: Initial Access → Lateral Movement (large jump)
    # Attacker pivots to lateral movement without explicit execution events.
    # Multiple intermediate stages may be missing.
    # -------------------------------------------------------
    TransitionRule(
        rule_id="TR-002",
        description="Initial Access directly to Lateral Movement — missing execution and credential stages",
        prev_technique_ids={
            "T1190", "T1566", "T1566.001", "T1566.002", "T1133",
        },
        next_technique_ids={
            "T1021", "T1021.001", "T1021.002", "T1021.006",
        },
        blueprints=[
            CandidateBlueprint(
                source_rule_id="TR-002",
                technique_id="T1059.001",
                technique_name="Command and Scripting Interpreter: PowerShell",
                event_type="ProcessCreate",
                description=(
                    "A command interpreter (e.g., PowerShell, cmd.exe) was likely "
                    "executed as an intermediate step to run staging or credential "
                    "harvesting commands before lateral movement."
                ),
                required_preconditions=[
                    "Initial access established on the host",
                    "Ability to execute commands (e.g., via exploit or phishing payload)",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
            CandidateBlueprint(
                source_rule_id="TR-002",
                technique_id="T1003.001",
                technique_name="OS Credential Dumping: LSASS Memory",
                event_type="ProcessAccess",
                description=(
                    "Credential dumping likely occurred between initial access and "
                    "lateral movement. LSASS is a common target after an initial "
                    "foothold is established."
                ),
                required_preconditions=[
                    "Execution capability established via initial access vector",
                    "Elevated privileges",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
        ],
    ),

    # -------------------------------------------------------
    # TR-003: Execution → Collection/Exfiltration
    # After code execution, attacker collects data before exfiltration.
    # -------------------------------------------------------
    TransitionRule(
        rule_id="TR-003",
        description="Execution to Data Exfiltration — missing data staging/collection",
        prev_technique_ids={
            "T1059", "T1059.001", "T1059.003",
        },
        next_technique_ids={
            "T1041", "T1486",
        },
        blueprints=[
            CandidateBlueprint(
                source_rule_id="TR-003",
                technique_id="T1005",
                technique_name="Data from Local System",
                event_type="FileAccess",
                description=(
                    "The attacker accesses and stages files from the local system "
                    "before exfiltration or encryption."
                ),
                required_preconditions=[
                    "Execution capability on the host",
                    "Read access to target files or directories",
                ],
                expected_host_context="same",
                expected_user_context="same",
            ),
        ],
    ),
]


# ---------------------------------------------------------------
# STAGE-BASED FALLBACK RULES
#
# When no exact technique match exists in TRANSITION_RULES,
# these stage-range rules provide coarser-grained candidates.
# They are less precise and should be clearly marked as such.
# ---------------------------------------------------------------

STAGE_FALLBACK_RULES: Dict[tuple, List[CandidateBlueprint]] = {
    # Stage jump: Execution (2) → Lateral Movement (4)
    (2, 4): [
        CandidateBlueprint(
            source_rule_id="FALLBACK-2-4",
            technique_id="T1003",
            technique_name="OS Credential Dumping",
            event_type="ProcessAccess",
            description=(
                "Generic credential access activity inferred from a technique "
                "stage jump of 2 (Execution → Lateral Movement). "
                "[Fallback rule — lower confidence than specific match.]"
            ),
            required_preconditions=[
                "Execution capability on the host",
                "Elevated privileges",
            ],
        ),
    ],
    # Stage jump: Initial Access (1) → Lateral Movement (4)
    (1, 4): [
        CandidateBlueprint(
            source_rule_id="FALLBACK-1-4",
            technique_id="T1059.001",
            technique_name="Command and Scripting Interpreter: PowerShell",
            event_type="ProcessCreate",
            description=(
                "Execution activity inferred from a large technique stage jump "
                "(Initial Access → Lateral Movement). "
                "[Fallback rule — lower confidence than specific match.]"
            ),
            required_preconditions=[
                "Initial access established",
            ],
        ),
    ],
}

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
