from collections import defaultdict
from app.taxonomy import CLEANLINESS, MECHANICAL, MOISTURE, OBSTRUCTION, URGENT_DEFECTS
from app.services.quality import compute_confidence
from app.services.recommendations import get_condition_label, get_recommendation


def clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))

def apply_business_rules(overall: float, findings: list[dict]) -> float:
    defect_types = {f["defect_type"] for f in findings}

    if "partial_blockage" in defect_types and overall > 89:
        overall = 89

    if "moderate_dust" in defect_types and "partial_blockage" in defect_types and overall > 85:
        overall = 85

    return overall

def validate_findings(findings: list[dict]):
    for f in findings:
        if "defect_type" not in f:
            raise ValueError("Each finding must include defect_type")
        if "severity" not in f:
            raise ValueError("Each finding must include severity")
        if "confidence" not in f:
            raise ValueError("Each finding must include confidence")


def get_penalty_multiplier(defect: str) -> float:
    if defect in {"heavy_dust", "debris", "foreign_object"}:
        return 14
    if defect in {"moderate_dust"}:
        return 12
    if defect in {"corrosion", "crack", "loose_lining", "damaged_joint"}:
        return 15
    if defect in {"partial_blockage", "narrowing"}:
        return 16
    if defect in {"severe_blockage"}:
        return 25
    if defect in {"moisture_presence", "suspected_microbial_growth"}:
        return 18
    if defect in {"staining", "condensation_signs"}:
        return 12
    return 10


def score_from_findings(findings: list[dict]) -> dict:
    penalties = defaultdict(float)

    for f in findings:
        defect = f["defect_type"]
        severity = f["severity"]
        confidence = f["confidence"] / 100.0

        multiplier = get_penalty_multiplier(defect)
        weight = severity * confidence * multiplier

        if defect in CLEANLINESS:
            penalties["cleanliness"] += weight
        elif defect in MECHANICAL:
            penalties["mechanical"] += weight
        elif defect in MOISTURE:
            penalties["moisture"] += weight
        elif defect in OBSTRUCTION:
            penalties["obstruction"] += weight

    cleanliness_score = clamp(100 - penalties["cleanliness"])
    mechanical_score = clamp(100 - penalties["mechanical"])
    moisture_score = clamp(100 - penalties["moisture"])
    obstruction_score = clamp(100 - penalties["obstruction"])

    overall_score = (
        0.35 * cleanliness_score
        + 0.20 * mechanical_score
        + 0.20 * moisture_score
        + 0.25 * obstruction_score
    )

    return {
        "cleanliness_score": round(cleanliness_score, 2),
        "mechanical_score": round(mechanical_score, 2),
        "moisture_score": round(moisture_score, 2),
        "obstruction_score": round(obstruction_score, 2),
        "overall_score": round(overall_score, 2),
    }


def has_urgent_flag(findings: list[dict]) -> bool:
    for f in findings:
        if f["defect_type"] in URGENT_DEFECTS and f["severity"] >= 2:
            return True
    return False


def evaluate_segment(payload) -> dict:
    findings = [f.model_dump() if hasattr(f, "model_dump") else f for f in payload.findings]

    validate_findings(findings)

    confidence_score, confidence_label = compute_confidence(
        payload.traversed_percent,
        payload.visible_surface_percent,
        payload.lighting_score,
        payload.camera_stability_score,
    )

    scores = score_from_findings(findings)
    urgent_flag = has_urgent_flag(findings)

    overall = scores["overall_score"]

    if confidence_label == "low":
        overall *= 0.90
    elif confidence_label == "inconclusive":
        overall *= 0.75

    overall = apply_business_rules(overall, findings)
    condition_label = get_condition_label(overall)

    recommendation = get_recommendation(
        overall,
        confidence_label,
        urgent_flag,
        findings,
    )

    return {
        "segment_id": payload.segment_id,
        "cleanliness_score": scores["cleanliness_score"],
        "mechanical_score": scores["mechanical_score"],
        "obstruction_score": scores["obstruction_score"],
        "moisture_score": scores["moisture_score"],
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "overall_score": overall,
        "condition_label": condition_label,
        "recommendation": recommendation,
        "urgent_flag": urgent_flag,
    }