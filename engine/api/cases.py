from fastapi import APIRouter, HTTPException
from typing import List
from models.domain import InvestigationCase
from persistence.local_storage import LocalCaseRepository

router = APIRouter()
repo = LocalCaseRepository()

@router.get("", response_model=List[InvestigationCase])
def list_cases():
    return repo.list_cases()

@router.post("", response_model=InvestigationCase)
def create_case(case: InvestigationCase):
    try:
        return repo.create_case(case)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{case_id}", response_model=InvestigationCase)
def get_case(case_id: str):
    case = repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/{case_id}", response_model=InvestigationCase)
def update_case(case_id: str, case: InvestigationCase):
    if case.case_id != case_id:
        raise HTTPException(status_code=400, detail="Case ID mismatch")
    try:
        return repo.update_case(case)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{case_id}")
def delete_case(case_id: str):
    if repo.delete_case(case_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Case not found")
