# Local LLM Integration (Phase 3)

This module provides the local LLM Assistant for CyberScope.

## Core Philosophy
The local LLM is an **investigation assistant**. It **does not determine** whether a security event occurred. The final verdict is determined solely by the deterministic Evidence Verifier. The LLM simply provides an evidence-grounded explanation of the deterministic results.

## Architecture
- `provider.py`: Factory handling configuration logic.
- `local_provider.py`: The `llama.cpp` integration. We intentionally avoid downloading weights on the fly or contacting OpenAI/Anthropic/Gemini APIs to maintain absolute air-gapped security.
- `mock_provider.py`: Used exclusively for deterministic unit testing.
- `context.py`: Strictly typed extraction of `InvestigationContext` that forcefully validates against ground-truth leakage.
- `guardrails.py`: Validates structured JSON responses. Any claim made by the assistant must map to an evidence reference (e.g., `[E1]`, `[GAP-1]`).

## Context Schema
The prompt uses strict delimiters to prevent prompt injection from untrusted telemetry:

```
--- SYSTEM INSTRUCTIONS ---
You must...

--- INVESTIGATION EVIDENCE ---
Case ID: ...
Facts:
[GAP-1] gap_detector: Gap detected...
[VERIFY-host_continuity] verification_check: host_continuity check resulted in PASS

--- USER QUESTION ---
Why was the gap detected?
```

## Structured Output & Hallucination Controls
The `StructuredLLMResponse` Pydantic model requires the LLM to separate prose (`answer`) from exact claims (`claims`). The `HallucinationGuardrail` module verifies every `evidence_refs` against the context list. If unsupported claims exceed `max_unsupported_claims`, the response is immediately discarded.

## Offline Behavior
If the LLM feature is disabled in `config.py` or the `llama-cpp-python` package is missing, the backend gracefully recovers and exposes a `model_loaded: False` status to the frontend. The main investigation pipeline remains entirely unblocked.

## Model Provenance
Every generated explanation attaches the provider name and model version into its response, ensuring full chain of custody across the analysis lifecycle.
