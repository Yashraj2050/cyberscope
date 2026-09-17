import json
import logging
from datetime import datetime
from pathlib import Path

audit_logger = logging.getLogger("llm_audit")
audit_logger.setLevel(logging.INFO)

log_path = Path(__file__).parent.parent / "logs" / "llm_audit.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

handler = logging.FileHandler(log_path)
handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(handler)

def log_llm_request(
    case_id: str,
    investigation_id: str,
    gap_id: str,
    model_id: str,
    model_hash: str,
    context_schema_version: str,
    latency: float,
    output_validation_status: str,
    evidence_references: list
):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "case_id": case_id,
        "investigation_id": investigation_id,
        "gap_id": gap_id,
        "model_id": model_id,
        "model_hash": model_hash,
        "context_schema_version": context_schema_version,
        "latency_seconds": round(latency, 3),
        "output_validation_status": output_validation_status,
        "evidence_references": evidence_references
    }
    audit_logger.info(json.dumps(log_entry))
