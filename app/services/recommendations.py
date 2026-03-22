def get_condition_label(score: float) -> str:
    if score >= 90:
        return "Good"
    if score >= 75:
        return "Fair"
    if score >= 55:
        return "Poor"
    return "Critical"


def get_recommendation(
    score: float,
    confidence_label: str,
    urgent_flag: bool,
    findings: list[dict],
) -> str:
    if urgent_flag:
        return "Immediate maintenance review required"

    if confidence_label in {"low", "inconclusive"}:
        return "Re-inspect segment due to low inspection confidence"

    defect_types = {f["defect_type"] for f in findings}

    if "severe_blockage" in defect_types:
        return "Immediate blockage removal required"

    if "partial_blockage" in defect_types:
        return "Schedule maintenance inspection for airflow obstruction"

    if "heavy_dust" in defect_types or "debris" in defect_types:
        return "Schedule duct cleaning"

    if "moderate_dust" in defect_types:
        return "Monitor and schedule routine cleaning"

    if "corrosion" in defect_types or "crack" in defect_types:
        return "Schedule engineering inspection"

    if score >= 85:
        return "No immediate action needed"

    if score >= 70:
        return "Monitor in next scheduled inspection"

    return "Schedule maintenance within 30 days"