import pytest
import json
from pathlib import Path
from pydantic import ValidationError
from fastapi.testclient import TestClient

from models import CyberEvent
from graph_engine import AttackGraphEngine
from main import app, load_scenario

client = TestClient(app)

# 1 & 2. Valid and Invalid CyberEvent
def test_valid_cyberevent():
    event = CyberEvent(
        event_id="E1",
        timestamp="2026-08-21T09:00:00Z",
        host_id="H1",
        event_type="ProcessCreate",
        source="Sysmon"
    )
    assert event.event_id == "E1"
    assert event.timestamp.isoformat() == "2026-08-21T09:00:00+00:00"

def test_invalid_cyberevent_missing_required():
    with pytest.raises(ValidationError):
        # Missing timestamp and host_id
        CyberEvent(
            event_id="E2",
            event_type="Network",
            source="Sysmon"
        )

# 3. Event Normalization / Loading Scenario
def test_load_scenario():
    events = load_scenario("scenario_001.json")
    assert len(events) == 4 # Only observed events
    
    # Proof that hidden ground truth is NOT inserted
    event_ids = [e.event_id for e in events]
    assert "EVT-001" in event_ids
    assert "EVT-002" in event_ids
    assert "EVT-004" in event_ids
    assert "EVT-005" in event_ids
    assert "EVT-003" not in event_ids # EVT-003 is the hidden ground truth!

# 4, 5, 6. Graph Creation, Node Creation, Edge Creation
def test_graph_creation():
    events = load_scenario("scenario_001.json")
    engine = AttackGraphEngine()
    engine.build(events)
    
    nodes = engine.get_nodes()
    edges = engine.get_edges()
    
    # We should have nodes for HOST-A, HOST-B, P-100, P-101, P-200, jdoe, SYSTEM, techniques, events
    node_ids = [n["id"] for n in nodes]
    assert "HOST-A" in node_ids
    assert "P-101" in node_ids
    assert "jdoe" in node_ids
    assert "EVT-001" in node_ids
    
    # Ground truth event should NOT be in the graph
    assert "EVT-003" not in node_ids

    # Edge creation (executes, runs_on, generates, etc.)
    edge_rels = [e["relationship"] for e in edges]
    assert "executes" in edge_rels
    assert "runs_on" in edge_rels
    assert "generates" in edge_rels
    
# 7. Graph Serialization
def test_graph_serialization():
    events = load_scenario("scenario_001.json")
    engine = AttackGraphEngine()
    engine.build(events)
    
    serialized = engine.serialize()
    assert "nodes" in serialized
    assert "edges" in serialized
    assert isinstance(serialized["nodes"], list)
    assert isinstance(serialized["edges"], list)

# 8. API Endpoints testing
def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "CyberScope Engine is running"}

def test_api_events():
    response = client.get("/api/v1/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    
def test_api_graph():
    response = client.get("/api/v1/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0
