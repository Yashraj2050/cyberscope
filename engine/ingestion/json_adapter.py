import json
from typing import List
from models.domain import CyberEvent
from ingestion.base import BaseAdapter

class DemoJsonAdapter(BaseAdapter):
    """
    Adapter for the existing demo JSON files.
    CRITICAL: Strips ground_truth_events completely before returning.
    """
    def ingest(self, source_path: str) -> List[CyberEvent]:
        with open(source_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            
        # ONLY load observed events. NEVER load ground truth into the operational endpoints.
        raw_observed = data.get("observed_events", [])
        
        events = []
        for raw in raw_observed:
            try:
                events.append(CyberEvent(**raw))
            except Exception as e:
                # Log or handle validation error
                raise ValueError(f"Invalid event {raw.get('event_id')}: {e}")
                
        return events
