import sys
import json
sys.path.append('engine')
from ingestion.json_adapter import DemoJsonAdapter

adapter = DemoJsonAdapter()
events = adapter.ingest("engine/datasets/demo/scenario_001.json")

print(f"Total events ingested: {len(events)}")

# Double check the original file
with open("engine/datasets/demo/scenario_001.json", "r") as f:
    data = json.load(f)
    print(f"Original file has {len(data.get('observed_events', []))} observed events")
    print(f"Original file has {len(data.get('ground_truth_events', []))} ground truth events")

# Check if any ground truth IDs slipped into the ingested events
gt_ids = [e['event_id'] for e in data.get('ground_truth_events', [])]
leaked = [e for e in events if e.event_id in gt_ids and e.event_id not in [o['event_id'] for o in data.get('observed_events', [])]]
print(f"Leaked ground truth events: {len(leaked)}")
if len(leaked) > 0:
    print("FAILED: Ground truth isolation compromised")
    sys.exit(1)
print("PASS: Ground truth isolation maintained")
