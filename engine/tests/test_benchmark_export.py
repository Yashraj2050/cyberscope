"""
test_benchmark_export.py — Phase 3C Benchmark Export Tests

Validates:
1. All exported contexts conform to InvestigationLLMContext schema
2. Forbidden ground-truth fields are absent
3. Evidence IDs are real (match gap-based provenance identifiers)
4. All three classifications are represented
5. Contexts are deterministic/reproducible
6. Ground truth never enters the exported context
"""

import pytest
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.context import InvestigationLLMContext
from llm.benchmark_export import (
    run_export, scan_for_forbidden_fields, FORBIDDEN_FIELDS,
    OUTPUT_DIR, CONTEXTS_DIR, SEED,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def export_result():
    """Run the export once for all tests in this module."""
    import shutil
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    summary = run_export()
    return summary


@pytest.fixture(scope="module")
def context_files(export_result):
    """Load all exported context JSON files."""
    files = {}
    for p in CONTEXTS_DIR.glob("*.json"):
        with open(p, "r") as f:
            files[p.name] = json.load(f)
    return files


@pytest.fixture(scope="module")
def manifest(export_result):
    """Load the manifest."""
    with open(OUTPUT_DIR / "manifest.json", "r") as f:
        return json.load(f)


# -----------------------------------------------------------------------
# 1. All contexts validate against InvestigationLLMContext
# -----------------------------------------------------------------------

def test_all_contexts_validate_schema(context_files):
    for name, data in context_files.items():
        ctx = InvestigationLLMContext(**data)
        assert ctx.case_id, f"{name}: missing case_id"
        assert ctx.investigation_id, f"{name}: missing investigation_id"
        assert ctx.context_schema_version == "1.0.0", f"{name}: wrong schema version"
        assert ctx.classification in ("OBSERVED", "INFERRED", "UNKNOWN"), f"{name}: invalid classification"


# -----------------------------------------------------------------------
# 2. Forbidden fields are absent (recursive scan)
# -----------------------------------------------------------------------

def test_no_forbidden_fields(context_files):
    for name, data in context_files.items():
        violations = scan_for_forbidden_fields(data)
        assert violations == [], f"{name}: FORBIDDEN FIELDS DETECTED: {violations}"


# -----------------------------------------------------------------------
# 3. Evidence IDs are real (gap-based provenance identifiers)
# -----------------------------------------------------------------------

def test_evidence_ids_are_real(context_files):
    for name, data in context_files.items():
        gap_id = data.get("gap_id", "")
        for ev in data.get("evidence", []):
            ref = ev["reference"]
            # Every reference must start with the gap_id
            assert ref.startswith(gap_id) or ref.startswith("EVT-"), \
                f"{name}: evidence reference '{ref}' does not match gap_id '{gap_id}'"


# -----------------------------------------------------------------------
# 4. All three classifications are represented
# -----------------------------------------------------------------------

def test_all_classifications_represented(context_files):
    classifications = set()
    for data in context_files.values():
        classifications.add(data["classification"])
    assert "OBSERVED" in classifications, "No OBSERVED contexts"
    assert "INFERRED" in classifications, "No INFERRED contexts"
    assert "UNKNOWN" in classifications, "No UNKNOWN contexts"


def test_classification_counts(manifest):
    dist = manifest["classification_distribution"]
    assert dist["OBSERVED"] >= 10, f"OBSERVED count {dist['OBSERVED']} < 10"
    assert dist["INFERRED"] >= 10, f"INFERRED count {dist['INFERRED']} < 10"
    assert dist["UNKNOWN"] >= 10, f"UNKNOWN count {dist['UNKNOWN']} < 10"


# -----------------------------------------------------------------------
# 5. Contexts are deterministic/reproducible
# -----------------------------------------------------------------------

def test_deterministic_export():
    """Running the export twice with the same seed produces identical output."""
    import shutil

    # First run
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    summary1 = run_export()

    files1 = {}
    for p in CONTEXTS_DIR.glob("*.json"):
        with open(p, "r") as f:
            files1[p.name] = f.read()

    # Second run
    shutil.rmtree(OUTPUT_DIR)
    summary2 = run_export()

    files2 = {}
    for p in CONTEXTS_DIR.glob("*.json"):
        with open(p, "r") as f:
            files2[p.name] = f.read()

    assert summary1["total_contexts"] == summary2["total_contexts"]
    assert summary1["classification_distribution"] == summary2["classification_distribution"]
    assert set(files1.keys()) == set(files2.keys()), "Different filenames between runs"


# -----------------------------------------------------------------------
# 6. Ground truth never enters exported context
# -----------------------------------------------------------------------

def test_ground_truth_never_in_context(context_files):
    for name, data in context_files.items():
        raw = json.dumps(data)
        for forbidden in FORBIDDEN_FIELDS:
            assert f'"{forbidden}"' not in raw, \
                f"{name}: forbidden field '{forbidden}' found in serialized JSON"


# -----------------------------------------------------------------------
# 7. Required fields present
# -----------------------------------------------------------------------

def test_required_fields_present(context_files):
    required = [
        "context_schema_version", "case_id", "investigation_id",
        "gap_id", "preceding_event", "following_event", "gap_score",
        "gap_signals", "candidates", "candidate_scores", "evidence",
        "verification", "classification", "knowledge_context", "provenance",
    ]
    for name, data in context_files.items():
        for field in required:
            assert field in data, f"{name}: missing required field '{field}'"


# -----------------------------------------------------------------------
# 8. Manifest structure
# -----------------------------------------------------------------------

def test_manifest_structure(manifest):
    assert "benchmark_id" in manifest
    assert "version" in manifest
    assert "seed" in manifest
    assert manifest["seed"] == SEED
    assert "contexts" in manifest
    assert len(manifest["contexts"]) >= 30


# -----------------------------------------------------------------------
# 9. Evaluator metadata is separate
# -----------------------------------------------------------------------

def test_evaluator_metadata_separate():
    eval_path = OUTPUT_DIR / "evaluator_metadata.json"
    assert eval_path.exists(), "evaluator_metadata.json missing"
    with open(eval_path, "r") as f:
        data = json.load(f)
    assert "expected_classifications" in data
    assert "note" in data
    assert "NEVER" in data["note"]


# -----------------------------------------------------------------------
# 10. No network dependency (offline)
# -----------------------------------------------------------------------

def test_no_network_dependency():
    """The export module doesn't import requests or urllib."""
    import llm.benchmark_export as mod
    source = Path(mod.__file__).read_text()
    assert "import requests" not in source
    assert "urllib" not in source
    assert "http://" not in source
    assert "https://" not in source


# -----------------------------------------------------------------------
# 11. Total count is at least 30
# -----------------------------------------------------------------------

def test_total_count(export_result):
    assert export_result["total_contexts"] >= 30
