from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.schemas import (
    SegmentInspectionIn,
    SegmentConditionOut,
    SegmentConditionDBOut,
    SegmentConditionDetailOut,
    InspectionResultsOut,
    InspectionSummaryOut,
    SegmentComparisonOut,
)
from app.services.scoring import evaluate_segment
from app.database import get_db
from app.models import SegmentCondition, InspectionEvidence, InspectionFinding

router = APIRouter()


@router.post("/evaluate-segment", response_model=SegmentConditionOut)
def evaluate_segment_route(payload: SegmentInspectionIn):
    try:
        result = evaluate_segment(payload)

        return {
            "segment_id": payload.segment_id,
            "traversed_percent": payload.traversed_percent,
            "visible_surface_percent": payload.visible_surface_percent,
            "lighting_score": payload.lighting_score,
            "camera_stability_score": payload.camera_stability_score,
            "cleanliness_score": result["cleanliness_score"],
            "mechanical_score": result["mechanical_score"],
            "obstruction_score": result["obstruction_score"],
            "moisture_score": result["moisture_score"],
            "confidence_score": result["confidence_score"],
            "confidence_label": result["confidence_label"],
            "overall_score": result["overall_score"],
            "condition_label": result["condition_label"],
            "recommendation": result["recommendation"],
            "urgent_flag": result["urgent_flag"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/evaluate-and-save", response_model=SegmentConditionDetailOut)
def evaluate_and_save_route(payload: SegmentInspectionIn, db: Session = Depends(get_db)):
    try:
        result = evaluate_segment(payload)

        max_version = (
            db.query(func.max(SegmentCondition.version))
            .filter(
                SegmentCondition.segment_id == payload.segment_id,
                SegmentCondition.inspection_id == payload.inspection_id,
            )
            .scalar()
        )

        next_version = 1 if max_version is None else max_version + 1

        row = SegmentCondition(
            segment_id=payload.segment_id,
            inspection_id=payload.inspection_id,
            version=next_version,
            traversed_percent=payload.traversed_percent,
            visible_surface_percent=payload.visible_surface_percent,
            lighting_score=payload.lighting_score,
            camera_stability_score=payload.camera_stability_score,
            cleanliness_score=result["cleanliness_score"],
            mechanical_score=result["mechanical_score"],
            obstruction_score=result["obstruction_score"],
            moisture_score=result["moisture_score"],
            confidence_score=result["confidence_score"],
            confidence_label=result["confidence_label"],
            overall_score=result["overall_score"],
            condition_label=result["condition_label"],
            recommendation=result["recommendation"],
            urgent_flag=result["urgent_flag"],
        )

        db.add(row)
        db.flush()

        for ev in payload.evidence:
            db.add(
                InspectionEvidence(
                    segment_condition_id=row.id,
                    file_url=ev.file_url,
                    file_type=ev.file_type,
                    timestamp=ev.timestamp,
                    quality_score=ev.quality_score,
                )
            )

        for fd in payload.findings:
            db.add(
                InspectionFinding(
                    segment_condition_id=row.id,
                    defect_type=fd.defect_type,
                    severity=fd.severity,
                    confidence=fd.confidence,
                    evidence_index=fd.evidence_index,
                )
            )

        db.commit()

        saved_row = (
            db.query(SegmentCondition)
            .options(
                selectinload(SegmentCondition.evidence_items),
                selectinload(SegmentCondition.findings),
            )
            .filter(SegmentCondition.id == row.id)
            .first()
        )

        return saved_row

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/segments/{segment_id}", response_model=list[SegmentConditionDBOut])
def get_segment_results(segment_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(SegmentCondition)
        .filter(SegmentCondition.segment_id == segment_id)
        .order_by(SegmentCondition.created_at.desc(), SegmentCondition.version.desc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No results found for this segment")

    return rows


@router.get("/segments/{segment_id}/latest", response_model=SegmentConditionDBOut)
def get_segment_latest(segment_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(SegmentCondition)
        .filter(SegmentCondition.segment_id == segment_id)
        .order_by(SegmentCondition.created_at.desc(), SegmentCondition.version.desc())
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="No latest result found for this segment")

    return row


@router.get("/segments/{segment_id}/versions/{version}", response_model=SegmentConditionDetailOut)
def get_segment_version_detail(segment_id: str, version: int, db: Session = Depends(get_db)):
    row = (
        db.query(SegmentCondition)
        .options(
            selectinload(SegmentCondition.evidence_items),
            selectinload(SegmentCondition.findings),
        )
        .filter(
            SegmentCondition.segment_id == segment_id,
            SegmentCondition.version == version,
        )
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="No result found for this segment/version")

    return row


@router.get("/segments/{segment_id}/compare", response_model=SegmentComparisonOut)
def compare_segment_versions(
    segment_id: str,
    version_a: int = Query(...),
    version_b: int = Query(...),
    db: Session = Depends(get_db),
):
    row_a = (
        db.query(SegmentCondition)
        .filter(
            SegmentCondition.segment_id == segment_id,
            SegmentCondition.version == version_a,
        )
        .first()
    )

    row_b = (
        db.query(SegmentCondition)
        .filter(
            SegmentCondition.segment_id == segment_id,
            SegmentCondition.version == version_b,
        )
        .first()
    )

    if not row_a or not row_b:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    delta = round(row_b.overall_score - row_a.overall_score, 2)

    if delta > 0:
        trend = "improved"
    elif delta < 0:
        trend = "declined"
    else:
        trend = "unchanged"

    return {
        "segment_id": segment_id,
        "inspection_id_a": row_a.inspection_id,
        "version_a": row_a.version,
        "score_a": row_a.overall_score,
        "label_a": row_a.condition_label,
        "created_at_a": row_a.created_at,
        "inspection_id_b": row_b.inspection_id,
        "version_b": row_b.version,
        "score_b": row_b.overall_score,
        "label_b": row_b.condition_label,
        "created_at_b": row_b.created_at,
        "score_delta": delta,
        "trend": trend,
    }


@router.get("/inspections/{inspection_id}", response_model=InspectionResultsOut)
def get_inspection_results(inspection_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(SegmentCondition)
        .filter(SegmentCondition.inspection_id == inspection_id)
        .order_by(
            SegmentCondition.segment_id.asc(),
            SegmentCondition.version.desc(),
        )
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No results found for this inspection")

    return {
        "inspection_id": inspection_id,
        "results": rows,
    }


@router.get("/inspections/{inspection_id}/latest", response_model=InspectionResultsOut)
def get_inspection_latest(inspection_id: str, db: Session = Depends(get_db)):
    subq = (
        db.query(
            SegmentCondition.segment_id,
            func.max(SegmentCondition.version).label("max_version"),
        )
        .filter(SegmentCondition.inspection_id == inspection_id)
        .group_by(SegmentCondition.segment_id)
        .subquery()
    )

    rows = (
        db.query(SegmentCondition)
        .join(
            subq,
            (SegmentCondition.segment_id == subq.c.segment_id)
            & (SegmentCondition.version == subq.c.max_version),
        )
        .filter(SegmentCondition.inspection_id == inspection_id)
        .order_by(SegmentCondition.segment_id.asc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No latest results found for this inspection")

    return {
        "inspection_id": inspection_id,
        "results": rows,
    }


@router.get("/inspections/{inspection_id}/details", response_model=list[SegmentConditionDetailOut])
def get_inspection_details(inspection_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(SegmentCondition)
        .options(
            selectinload(SegmentCondition.evidence_items),
            selectinload(SegmentCondition.findings),
        )
        .filter(SegmentCondition.inspection_id == inspection_id)
        .order_by(
            SegmentCondition.segment_id.asc(),
            SegmentCondition.version.desc(),
        )
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No detailed results found for this inspection")

    return rows


@router.get("/inspections/{inspection_id}/summary", response_model=InspectionSummaryOut)
def get_inspection_summary(inspection_id: str, db: Session = Depends(get_db)):
    subq = (
        db.query(
            SegmentCondition.segment_id,
            func.max(SegmentCondition.version).label("max_version"),
        )
        .filter(SegmentCondition.inspection_id == inspection_id)
        .group_by(SegmentCondition.segment_id)
        .subquery()
    )

    rows = (
        db.query(SegmentCondition)
        .join(
            subq,
            (SegmentCondition.segment_id == subq.c.segment_id)
            & (SegmentCondition.version == subq.c.max_version),
        )
        .filter(SegmentCondition.inspection_id == inspection_id)
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No summary data found for this inspection")

    total_results = len(rows)
    unique_segments = len({r.segment_id for r in rows})
    average_overall_score = round(sum(r.overall_score for r in rows) / total_results, 2)
    urgent_count = sum(1 for r in rows if r.urgent_flag)
    good_count = sum(1 for r in rows if r.condition_label == "Good")
    fair_count = sum(1 for r in rows if r.condition_label == "Fair")
    poor_count = sum(1 for r in rows if r.condition_label == "Poor")
    critical_count = sum(1 for r in rows if r.condition_label == "Critical")

    return {
        "inspection_id": inspection_id,
        "total_results": total_results,
        "unique_segments": unique_segments,
        "average_overall_score": average_overall_score,
        "urgent_count": urgent_count,
        "good_count": good_count,
        "fair_count": fair_count,
        "poor_count": poor_count,
        "critical_count": critical_count,
    }