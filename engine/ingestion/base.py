from abc import ABC, abstractmethod
from typing import List
from models.domain import CyberEvent

class BaseAdapter(ABC):
    """
    Abstract base class for all telemetry ingestion adapters.
    """
    @abstractmethod
    def ingest(self, source_path: str) -> List[CyberEvent]:
        """Reads raw data, normalizes it, and returns CyberEvents."""
        pass
