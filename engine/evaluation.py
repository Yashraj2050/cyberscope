"""
evaluation.py — CyberScope Evaluation Utility

FOR DEVELOPMENT AND TESTING ONLY.
This module is NOT part of the normal reconstruction pipeline.

It uses ground truth to evaluate the quality of generated candidates.
The results reported here are prototype evaluation metrics — they do NOT
constitute validated production accuracy claims.

USAGE:
  from evaluation import evaluate_candidates
  results = evaluate_candidates(candidates, ground_truth_event)

This function must NEVER be called from any API endpoint or the main
reconstruction pipeline.
"""

from typing import List, Dict, Any, Optional
from models import CyberEvent
from candidate_model import ReconstructionCandidate


def evaluate_candidates(
    candidates: List[ReconstructionCandidate],
    ground_truth_event: CyberEvent,
) -> Dict[str, Any]:
    """
    Evaluate reconstruction candidates against a known ground truth event.

    IMPORTANT:
    - This function is for development/testing evaluation only.
    - It must never be called from the API or the reconstruction pipeline.
    - Results are prototype metrics, not production accuracy measurements.

    Args:
        candidates:          Scored, ranked candidates from CandidateScorer.
        ground_truth_event:  The actual missing event (from test evaluation).

    Returns:
        Dict with evaluation metrics.
    """
    if not candidates:
        return {
            "outcome": "ABSTAINED",
            "top1_match": False,
            "topk_match": False,
            "k": 0,
            "matching_rank": None,
            "total_candidates": 0,
            "note": (
                "No candidates were generated. The system abstained — "
                "this is correct behaviour when evidence is insufficient."
            ),
        }

    gt_tid = ground_truth_event.technique_id or ""
    gt_etype = ground_truth_event.event_type or ""

    # Match criteria: technique_id exact match (primary), or event_type match (secondary)
    def is_match(c: ReconstructionCandidate) -> bool:
        if gt_tid and c.technique_id == gt_tid:
            return True
        if gt_etype and c.event_type == gt_etype:
            return True
        return False

    # Find the first matching candidate's rank
    matching_rank: Optional[int] = None
    for c in candidates:
        if is_match(c):
            matching_rank = c.rank
            break

    top1_match = matching_rank == 1
    k = len(candidates)
    topk_match = matching_rank is not None

    # False candidates: candidates that do NOT match the ground truth
    false_candidates = [
        {"candidate_id": c.candidate_id, "technique_id": c.technique_id, "rank": c.rank}
        for c in candidates if not is_match(c)
    ]

    outcome = "CORRECT_TOP1" if top1_match else (
        "CORRECT_TOPK" if topk_match else "INCORRECT"
    )

    return {
        "outcome": outcome,
        "top1_match": top1_match,
        "topk_match": topk_match,
        "k": k,
        "matching_rank": matching_rank,
        "total_candidates": len(candidates),
        "false_candidates": false_candidates,
        "ground_truth_technique": gt_tid,
        "ground_truth_event_type": gt_etype,
        "note": (
            "This is a prototype evaluation metric. "
            "It does NOT represent calibrated production accuracy."
        ),
    }
