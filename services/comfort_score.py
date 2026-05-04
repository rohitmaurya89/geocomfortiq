"""
services/comfort_score.py

Phase 3 upgrade:
  - compute_comfort_score()  : weighted formula (unchanged, already good)
  - classify_and_score()     : full pipeline — score + KMeans risk category
  - explain_score()          : human-readable explanation for AI assistant
"""

from config.settings_config import COMFORT_WEIGHTS, RISK_THRESHOLDS


def compute_comfort_score(params: dict) -> float:
    """
    Comfort Score (0-100) via weighted combination of parameters.
    Formula: score = 50 + sum( weight_i * (param_i - 50) )
    Clamped to [0, 100].
    """
    score = 50.0
    for param_key, weight in COMFORT_WEIGHTS.items():
        value = params.get(param_key, 50.0)
        score += weight * (value - 50.0)
    return round(max(0.0, min(100.0, score)), 2)


def classify_and_score(params: dict) -> dict:
    """
    Full Phase 3 pipeline:
      1. Compute weighted comfort score.
      2. Run KMeans to get ML-based risk category.
    Returns dict: { comfort_score, risk_category, kmeans_cluster }
    """
    from services.kmeans_classifier import classify_zone

    score = compute_comfort_score(params)
    kmeans_result = classify_zone(params)

    return {
        'comfort_score':  score,
        'risk_category':  kmeans_result['risk_category'],
        'kmeans_cluster': kmeans_result['cluster_id'],
    }


def explain_score(params: dict, score: float) -> list:
    """Returns human-readable explanation list for the AI assistant."""
    reasons = []
    g  = params.get('green_pct',      0)
    d  = params.get('dust_pct',       0)
    b  = params.get('builtup_pct',    0)
    sh = params.get('shade_pct',      0)
    co = params.get('congestion_pct', 0)

    if g >= 30:
        reasons.append(f"Good green cover ({g:.1f}%) — cooler air, better microclimate.")
    elif g >= 15:
        reasons.append(f"Moderate green cover ({g:.1f}%) — some vegetation present.")
    else:
        reasons.append(f"Low green cover ({g:.1f}%) — high heat exposure risk.")

    if d >= 35:
        reasons.append(f"High dust/open land ({d:.1f}%) — elevated PM10, poor air quality.")
    elif d >= 20:
        reasons.append(f"Moderate dust ({d:.1f}%) — carry a mask if sensitive.")

    if sh >= 20:
        reasons.append(f"Good shade coverage ({sh:.1f}%) — UV exposure reduced.")
    elif sh < 10:
        reasons.append(f"Low shade ({sh:.1f}%) — direct sunlight exposure likely.")

    if co >= 40:
        reasons.append(f"High structural congestion ({co:.1f}%) — poor airflow, heat trap.")
    elif co >= 25:
        reasons.append(f"Moderate congestion ({co:.1f}%) — limited wind circulation.")

    if b >= 45:
        reasons.append(f"High built-up area ({b:.1f}%) — urban heat island effect likely.")

    if score >= 70:
        reasons.append("Overall: Safe and comfortable route.")
    elif score >= 40:
        reasons.append("Overall: Moderate — travel early morning or evening.")
    else:
        reasons.append("Overall: Risky — avoid midday, carry water and mask.")

    return reasons
