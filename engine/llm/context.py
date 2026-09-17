from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional
from .knowledge_retriever import LocalKnowledgeRetriever

class EvidenceFact(BaseModel):
    reference: str
    fact: str
    source_type: str
    source_id: str

class InvestigationLLMContext(BaseModel):
    context_schema_version: str = "1.0.0"
    case_id: str
    investigation_id: str
    gap_id: Optional[str] = None
    preceding_event: Optional[Dict[str, Any]] = None
    following_event: Optional[Dict[str, Any]] = None
    gap_score: Optional[float] = None
    gap_signals: Dict[str, Any] = Field(default_factory=dict)
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    candidate_scores: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[EvidenceFact] = Field(default_factory=list)
    verification: Dict[str, Any] = Field(default_factory=dict)
    classification: str
    knowledge_context: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def exclude_ground_truth(cls, values):
        if isinstance(values, dict):
            for k in ["ground_truth_events", "hidden_event_id", "correct_candidate", "expected_answer"]:
                if k in values:
                    raise ValueError(f"SECURITY VIOLATION: {k} must not be in InvestigationLLMContext")
            cls._check_dict_recursively(values)
        return values
        
    @classmethod
    def _check_dict_recursively(cls, d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in ["ground_truth_events", "hidden_event_id", "correct_candidate", "expected_answer"]:
                    raise ValueError(f"SECURITY VIOLATION: {k} must not be in InvestigationLLMContext")
                if isinstance(v, (dict, list)):
                    cls._check_dict_recursively(v)
        elif isinstance(d, list):
            for v in d:
                cls._check_dict_recursively(v)

    def get_valid_references(self) -> List[str]:
        return [f.reference for f in self.evidence]

class InvestigationContextBuilder:
    def __init__(self):
        self.retriever = LocalKnowledgeRetriever()

    def build(self, case_id: str, investigation_id: str, gap_result: Dict[str, Any], verification_result: Dict[str, Any], candidates: List[Dict[str, Any]]) -> InvestigationLLMContext:
        gap = gap_result.get("gap", {})
        preceding = gap.get("preceding_event")
        following = gap.get("following_event")
        
        knowledge = self.retriever.get_knowledge_context(preceding, following)

        evidence = []
        for check in verification_result.get("checks", []):
            if "evidence" in check:
                # We'll just generate synthetic IDs or use provided ones if they exist
                ref_id = f"EVT-{len(evidence)+1:03d}"
                evidence.append(EvidenceFact(
                    reference=ref_id,
                    fact=check["evidence"],
                    source_type=check.get("type", "unknown"),
                    source_id=check.get("source_id", "unknown")
                ))

        # Filter out ground truth from candidates explicitly just to be safe
        safe_candidates = []
        for c in candidates:
            sc = dict(c)
            sc.pop("is_correct", None)
            safe_candidates.append(sc)

        return InvestigationLLMContext(
            case_id=case_id,
            investigation_id=investigation_id,
            gap_id=gap.get("id"),
            preceding_event=preceding,
            following_event=following,
            gap_score=gap_result.get("score"),
            gap_signals=gap_result.get("signals", {}),
            candidates=safe_candidates,
            candidate_scores={c.get("id", "unk"): c.get("score", 0.0) for c in safe_candidates},
            evidence=evidence,
            verification=verification_result,
            classification=verification_result.get("classification", "UNKNOWN"),
            knowledge_context=knowledge,
            provenance={}
        )
