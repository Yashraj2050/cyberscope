"""
gap_model.py — CyberScope ReconstructionGap Data Models

These models represent detected gaps in observed telemetry.

IMPORTANT:
- A ReconstructionGap does NOT assert that a missing event occurred.
- It identifies a location requiring investigation.
- gap_score is a prioritization score, NOT a validated accuracy metric.
- Status OPEN means the gap has been detected and not yet resolved.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class GapStatus(str, Enum):
    OPEN = "OPEN"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class DetectionSignals(BaseModel):
    """
    Boolean evidence signals that contributed to gap detection.

    Each signal is independently derived from observed telemetry only.
    No single signal is sufficient to declare a gap on its own.
    """
    temporal: bool = Field(
        False,
        description=(
            "The inter-event interval significantly exceeds the statistical baseline "
            "(median gap × TEMPORAL_OUTLIER_MULTIPLIER). "
            "Alone this is weak; combined with other signals it adds weight."
        )
    )
    host_continuity: bool = Field(
        False,
        description=(
            "The host changes unexpectedly between the two consecutive events "
            "without an observed connecting network event on the same process."
        )
    )
    user_continuity: bool = Field(
        False,
        description=(
            "The user context changes between events without an observed "
            "authentication or privilege event to explain it."
        )
    )
    process_relationship: bool = Field(
        False,
        description=(
            "No parent-child or same-process relationship exists between the "
            "processes in the two events, yet the events are adjacent in time."
        )
    )
    technique_transition: bool = Field(
        False,
        description=(
            "The MITRE ATT&CK technique stage jumps by more than the configured "
            "threshold (SUSPICIOUS_STAGE_JUMP), suggesting skipped attack phases."
        )
    )
    behavioral_prerequisite: bool = Field(
        False,
        description=(
            "The next event uses a technique that typically requires a "
            "precondition (e.g. credential access before lateral movement) "
            "not observed anywhere in the preceding telemetry."
        )
    )


class ReconstructionGap(BaseModel):
    """
    A detected location in observed telemetry where events may be missing.

    DISCLAIMER:
    This object identifies a location requiring investigation.
    It does NOT determine what actually happened.
    gap_score is a prioritization score, NOT validated accuracy.
    """
    gap_id: str = Field(..., description="Unique identifier for this gap")
    previous_event_id: str = Field(..., description="ID of the last observed event before the gap")
    next_event_id: str = Field(..., description="ID of the first observed event after the gap")
    start_timestamp: datetime = Field(..., description="Timestamp of the previous event")
    end_timestamp: datetime = Field(..., description="Timestamp of the next event")
    affected_host: Optional[str] = Field(None, description="Most relevant host (from previous event)")
    affected_user: Optional[str] = Field(None, description="Most relevant user (from previous event)")
    temporal_gap_seconds: float = Field(..., description="Wall-clock time between the two events in seconds")
    previous_event_type: str = Field(..., description="event_type of the preceding event")
    next_event_type: str = Field(..., description="event_type of the following event")
    graph_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual graph information about the two boundary events"
    )
    detection_signals: DetectionSignals = Field(
        ..., description="Boolean evidence signals that contributed to this detection"
    )
    gap_score: float = Field(
        ..., ge=0.0, le=1.0,
        description=(
            "Weighted prioritization score (0.0–1.0). "
            "Higher = more signals fired = higher investigative priority. "
            "This is NOT a validated accuracy or probability metric."
        )
    )
    status: GapStatus = Field(
        GapStatus.OPEN,
        description="Current status: OPEN (newly detected), REJECTED, or RESOLVED"
    )
