import os
import json
import re
from typing import List, Optional
from datetime import datetime
from models.domain import InvestigationCase

class LocalCaseRepository:
    def __init__(self, storage_dir: str = "cases"):
        self.storage_dir = storage_dir
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def _get_case_path(self, case_id: str) -> str:
        # Prevent path traversal
        if not re.match(r'^[a-zA-Z0-9_\-]+$', case_id):
            raise ValueError(f"Invalid case_id format: {case_id}")
        return os.path.join(self.storage_dir, f"{case_id}.json")

    def create_case(self, case: InvestigationCase) -> InvestigationCase:
        path = self._get_case_path(case.case_id)
        if os.path.exists(path):
            raise ValueError(f"Case {case.case_id} already exists.")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(case.json())
        return case

    def get_case(self, case_id: str) -> Optional[InvestigationCase]:
        path = self._get_case_path(case_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return InvestigationCase(**data)

    def update_case(self, case: InvestigationCase) -> InvestigationCase:
        path = self._get_case_path(case.case_id)
        if not os.path.exists(path):
            raise ValueError(f"Case {case.case_id} not found.")
        
        # Ensure updated_at is refreshed
        case.updated_at = datetime.utcnow()
        with open(path, 'w', encoding='utf-8') as f:
            f.write(case.json())
        return case

    def list_cases(self) -> List[InvestigationCase]:
        cases = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                case_id = filename[:-5]
                try:
                    c = self.get_case(case_id)
                    if c:
                        cases.append(c)
                except Exception:
                    # Ignore malformed files
                    pass
        # Sort by updated_at descending
        cases.sort(key=lambda x: x.updated_at, reverse=True)
        return cases

    def delete_case(self, case_id: str) -> bool:
        path = self._get_case_path(case_id)
        if os.path.exists(path):
            os.remove(path)
            # Also attempt to remove analysis results if stored separately
            result_path = os.path.join(self.storage_dir, f"{case_id}_result.json")
            if os.path.exists(result_path):
                os.remove(result_path)
            return True
        return False

    def save_investigation_result(self, case_id: str, result_json: str) -> None:
        """Saves the raw JSON dump of an InvestigationResult."""
        self._get_case_path(case_id) # validate ID
        path = os.path.join(self.storage_dir, f"{case_id}_result.json")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(result_json)
        
        # Update case metadata
        case = self.get_case(case_id)
        if case:
            case.has_analysis = True
            self.update_case(case)

    def load_investigation_result(self, case_id: str) -> Optional[str]:
        self._get_case_path(case_id) # validate ID
        path = os.path.join(self.storage_dir, f"{case_id}_result.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

