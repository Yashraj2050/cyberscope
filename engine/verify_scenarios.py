import json
import requests
import sys

for i in range(1, 6):
    scenario = f"scenario_00{i}.json"
    print(f"\n================ {scenario} ================")
    try:
        r = requests.post("http://localhost:8000/api/v1/reconstruction/verify", json={"scenario": scenario})
        if r.status_code != 200:
            print(f"ERROR: {r.status_code} - {r.text}")
            continue
            
        data = r.json()
        print(f"Gap Count: {len(data)}")
        
        with open(f"datasets/demo/{scenario}") as f:
            scen_data = json.load(f)
            print(f"Scenario Name: {scen_data.get('scenario_name')}")
            print(f"Observed Events: {len(scen_data.get('observed_events', []))}")
            print(f"Ground Truth Events: {len(scen_data.get('ground_truth_events', []))}")
            
        if not data:
            print("No gaps detected.")
            continue
            
        for idx, item in enumerate(data):
            print(f"\n--- GAP {idx+1} ---")
            gap = item["gap"]
            print(f"Gap Score: {gap['gap_score']}")
            print(f"Gap Signals: {json.dumps(gap['detection_signals'])}")
            
            cands = item["candidates"]
            print(f"Candidate Count: {len(cands)}")
            for c in cands:
                print(f"  Rank {c['rank']}: {c['technique_id']} ({c['technique_name']}) - Score: {c['candidate_score']}")
                
            res = item["result"]
            print(f"Verification Score: {res['verification_score']}")
            print(f"Verification Checks: {json.dumps(res['verification_checks'])}")
            print(f"Final Classification: {res['status']}")
            print(f"Explanation: {res['explanation']}")
            
    except Exception as e:
        print(f"Exception: {e}")
