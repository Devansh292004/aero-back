from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import InspectionReportOut
from app.services.reporting import build_inspection_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/inspections/{inspection_id}", response_model=InspectionReportOut)
def get_inspection_report(inspection_id: str, db: Session = Depends(get_db)):
    report = build_inspection_report(db, inspection_id)
    if not report:
        raise HTTPException(status_code=404, detail="No report data found for this inspection")
    return report