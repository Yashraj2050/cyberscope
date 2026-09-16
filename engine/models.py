from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class CyberEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    timestamp: datetime = Field(..., description="When the event occurred")
    host_id: str = Field(..., description="The host where the event occurred")
    user_id: Optional[str] = None
    process_id: Optional[str] = None
    parent_process_id: Optional[str] = None
    event_type: str = Field(..., description="Category of the event (e.g., ProcessCreate, NetworkConnect)")
    process_name: Optional[str] = None
    source: str = Field(..., description="Sensor or log source (e.g., Sysmon, Windows Event Log)")
    source_event_id: Optional[str] = Field(None, description="Original event ID from the source system")
    technique_id: Optional[str] = Field(None, description="MITRE ATT&CK Technique ID")
    technique_name: Optional[str] = Field(None, description="MITRE ATT&CK Technique Name")
    destination_host: Optional[str] = None
    destination_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional structured context")
    raw_reference: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Original raw event payload")
