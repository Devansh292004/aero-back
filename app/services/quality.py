def compute_confidence(
    traversed_percent: float,
    visible_surface_percent: float,
    lighting_score: float,
    camera_stability_score: float,
):
    score = (
        0.35 * traversed_percent
        + 0.30 * visible_surface_percent
        + 0.20 * lighting_score
        + 0.15 * camera_stability_score
    )

    if score >= 85:
        label = "high"
    elif score >= 65:
        label = "medium"
    elif score >= 40:
        label = "low"
    else:
        label = "inconclusive"

    return round(score, 2), label
