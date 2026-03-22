from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.models import SegmentCondition
from app.schemas import InspectionReportOut


def build_inspection_report(db: Session, inspection_id: str) -> dict:
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
        .options(
            selectinload(SegmentCondition.evidence_items),
            selectinload(SegmentCondition.findings),
        )
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
        return None

    total_segments = len(rows)
    avg_score = round(sum(r.overall_score for r in rows) / total_segments, 2)
    urgent_count = sum(1 for r in rows if r.urgent_flag)
    good_count = sum(1 for r in rows if r.condition_label == "Good")
    fair_count = sum(1 for r in rows if r.condition_label == "Fair")
    poor_count = sum(1 for r in rows if r.condition_label == "Poor")
    critical_count = sum(1 for r in rows if r.condition_label == "Critical")

    segments = []
    urgent_segments = []

    for r in rows:
        seg = {
            "segment_id": r.segment_id,
            "version": r.version,
            "created_at": r.created_at,
            "traversed_percent": r.traversed_percent,
            "visible_surface_percent": r.visible_surface_percent,
            "lighting_score": r.lighting_score,
            "camera_stability_score": r.camera_stability_score,
            "cleanliness_score": r.cleanliness_score,
            "mechanical_score": r.mechanical_score,
            "obstruction_score": r.obstruction_score,
            "moisture_score": r.moisture_score,
            "confidence_score": r.confidence_score,
            "confidence_label": r.confidence_label,
            "overall_score": r.overall_score,
            "condition_label": r.condition_label,
            "recommendation": r.recommendation,
            "urgent_flag": r.urgent_flag,
            "findings": [
                {
                    "defect_type": f.defect_type,
                    "severity": f.severity,
                    "confidence": f.confidence,
                    "evidence_index": f.evidence_index,
                }
                for f in r.findings
            ],
            "evidence_items": [
                {
                    "file_url": e.file_url,
                    "file_type": e.file_type,
                    "timestamp": e.timestamp,
                    "quality_score": e.quality_score,
                }
                for e in r.evidence_items
            ],
        }
        segments.append(seg)

        if r.urgent_flag:
            urgent_segments.append(seg)

    return {
        "inspection_id": inspection_id,
        "generated_at": datetime.utcnow(),
        "summary": {
            "inspection_id": inspection_id,
            "total_segments": total_segments,
            "average_overall_score": avg_score,
            "urgent_count": urgent_count,
            "good_count": good_count,
            "fair_count": fair_count,
            "poor_count": poor_count,
            "critical_count": critical_count,
        },
        "urgent_segments": urgent_segments,
        "segments": segments,
    }