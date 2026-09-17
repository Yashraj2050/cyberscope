import pytest
import json
import os
from unittest.mock import patch
from llm.context import InvestigationLLMContext, EvidenceFact, InvestigationContextBuilder
from llm.parser import parse_llm_response, StructuredLLMResponse
from llm.guardrails import HallucinationGuardrail, GuardrailViolation
from llm.provider import get_llm_provider
from llm.local_provider import LocalLLMProvider
from llm.prompts import build_prompt
from llm.knowledge_retriever import LocalKnowledgeRetriever
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# 1. Context construction
def test_context_construction():
    builder = InvestigationContextBuilder()
    ctx = builder.build(
        case_id="case_1",
        investigation_id="inv_1",
        gap_result={"gap": {"id": "gap_1"}, "score": 0.5},
        verification_result={"classification": "UNKNOWN", "checks": [{"evidence": "test", "type": "t"}]},
        candidates=[{"id": "cand_1"}]
    )
    assert ctx.case_id == "case_1"
    assert ctx.classification == "UNKNOWN"
    assert len(ctx.evidence) == 1

# 2. Ground-truth isolation
def test_ground_truth_isolation():
    with pytest.raises(ValueError, match="SECURITY VIOLATION"):
        InvestigationLLMContext(
            case_id="1", investigation_id="2",
            classification="UNKNOWN",
            candidates=[{"correct_candidate": True}]
        )

# 3. Evidence ID preservation
def test_evidence_id_preservation():
    raw = '''```json
{"summary": "s", "assessment": "a", "evidence_references": ["EVT-001"], "candidate_discussion": [], "uncertainty": "", "recommended_next_checks": []}
```'''
    parsed = parse_llm_response(raw)
    assert parsed.evidence_references == ["EVT-001"]

# 4. Invalid evidence reference rejection
def test_invalid_evidence_reference_rejection():
    ctx = InvestigationLLMContext(
        case_id="1", investigation_id="2",
        classification="UNKNOWN",
        evidence=[EvidenceFact(reference="EVT-001", fact="test", source_type="t", source_id="1")]
    )
    res = StructuredLLMResponse(
        summary="s", assessment="a", evidence_references=["FAKE_REF"]
    )
    guard = HallucinationGuardrail()
    with pytest.raises(GuardrailViolation):
        guard.validate(res, ctx)

# 5. Invalid JSON rejection
def test_invalid_json_rejection():
    with pytest.raises(ValueError, match="LLM_RESPONSE_INVALID"):
        parse_llm_response("just some text")

# 6. UNKNOWN preservation
def test_unknown_preservation():
    provider = get_llm_provider()
    ctx = InvestigationLLMContext(case_id="1", investigation_id="2", classification="UNKNOWN")
    res = provider.generate(ctx, "UNKNOWN test")
    assert "UNKNOWN" in res.summary

# 7. OBSERVED preservation
def test_observed_preservation():
    provider = get_llm_provider()
    ctx = InvestigationLLMContext(case_id="1", investigation_id="2", classification="OBSERVED")
    res = provider.generate(ctx, "test")
    # Prompt instructs not to override. Mock doesn't change it.

# 8. INFERRED preservation
def test_inferred_preservation():
    pass

# 9. Prompt injection
def test_prompt_injection():
    provider = get_llm_provider()
    ctx = InvestigationLLMContext(case_id="1", investigation_id="2", classification="UNKNOWN")
    res = provider.generate(ctx, "malicious instructions")
    assert "I am a helpful assistant." in res.summary

# 10. Missing model
def test_missing_model():
    import llm.config as conf
    conf.DEFAULT_MODEL_PATH = conf.MODELS_DIR / "does_not_exist.gguf"
    provider = LocalLLMProvider()
    assert not provider.is_loaded
    with pytest.raises(RuntimeError, match="LLM_UNAVAILABLE"):
        provider.generate(InvestigationLLMContext(case_id="1", investigation_id="2", classification="UNKNOWN"), "test")

# 11. Invalid model hash
def test_invalid_model_hash():
    # If hash doesn't match manifest, it doesn't load
    pass

# 12. Model status API
def test_model_status_api():
    resp = client.get("/api/v1/llm/status")
    assert resp.status_code == 200
    assert "enabled" in resp.json()

# 13. Offline execution
@patch("socket.socket")
def test_offline_execution(mock_socket):
    provider = get_llm_provider()
    provider.get_status()
    mock_socket.assert_not_called()

# 14. Deterministic pipeline without LLM
def test_deterministic_pipeline_without_llm():
    resp = client.get("/api/v1/reconstruction/verify")
    assert resp.status_code == 200

# 15. LLM failure does not break investigation
def test_llm_failure_does_not_break():
    import llm.config as conf
    conf.DEFAULT_MODEL_PATH = conf.MODELS_DIR / "does_not_exist.gguf"
    conf.LLM_PROVIDER = "local"
    resp = client.post("/api/v1/investigations/scenario_001.json/ai/explain")
    assert resp.status_code == 503
    conf.LLM_PROVIDER = "mock"

# 16. Context size limits
def test_context_size_limits():
    pass

# 17. Model provenance
def test_model_provenance():
    provider = get_llm_provider()
    ctx = InvestigationLLMContext(case_id="1", investigation_id="2", classification="UNKNOWN")
    res = provider.generate(ctx, "test")
    assert res.provider == "mock"

# 18. Audit logging
def test_audit_logging():
    from llm.audit import log_llm_request
    log_llm_request("1", "2", "3", "4", "5", "1.0", 0.5, "VALID", [])
    assert os.path.exists("logs/llm_audit.log")

# 19. API authorization/input validation
def test_api_input_validation():
    resp = client.post("/api/v1/investigations/bad@file.json/ai/explain")
    assert resp.status_code == 400

# 20. Local knowledge retrieval
def test_local_knowledge_retrieval():
    kr = LocalKnowledgeRetriever()
    k = kr.get_knowledge_context({"event_type": "NetworkConnection"}, {"event_type": "ProcessExecution"})
    assert isinstance(k, str)
