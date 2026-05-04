"""
services/mock_analysis.py

Phase 1 stub: generates realistic-looking parameters per city.
Phase 2 replaces this entirely with real OpenCV pixel analysis.

Each city has slightly different environmental profiles to make
the app feel realistic during UI development/demo.
"""

import random

# City-specific environmental profiles (base values + noise range)
CITY_PROFILES = {
    "lucknow": {
        "green_pct":      (22, 5),
        "dust_pct":       (28, 6),
        "builtup_pct":    (35, 5),
        "shade_pct":      (10, 3),
        "congestion_pct": (30, 8),
        "water_pct":      (5,  2),
    },
    "delhi": {
        "green_pct":      (15, 4),
        "dust_pct":       (35, 7),
        "builtup_pct":    (40, 5),
        "shade_pct":      (8,  3),
        "congestion_pct": (38, 7),
        "water_pct":      (2,  1),
    },
    "mumbai": {
        "green_pct":      (18, 4),
        "dust_pct":       (20, 5),
        "builtup_pct":    (50, 6),
        "shade_pct":      (12, 3),
        "congestion_pct": (42, 8),
        "water_pct":      (8,  3),
    },
    "bengaluru": {
        "green_pct":      (30, 6),
        "dust_pct":       (18, 4),
        "builtup_pct":    (38, 5),
        "shade_pct":      (15, 4),
        "congestion_pct": (32, 7),
        "water_pct":      (4,  2),
    },
    "hyderabad": {
        "green_pct":      (20, 5),
        "dust_pct":       (25, 6),
        "builtup_pct":    (40, 6),
        "shade_pct":      (10, 3),
        "congestion_pct": (28, 7),
        "water_pct":      (5,  2),
    },
    "chennai": {
        "green_pct":      (18, 4),
        "dust_pct":       (22, 5),
        "builtup_pct":    (42, 6),
        "shade_pct":      (11, 3),
        "congestion_pct": (30, 7),
        "water_pct":      (7,  3),
    },
    "kolkata": {
        "green_pct":      (20, 5),
        "dust_pct":       (28, 6),
        "builtup_pct":    (38, 5),
        "shade_pct":      (12, 3),
        "congestion_pct": (35, 8),
        "water_pct":      (7,  3),
    },
    "jaipur": {
        "green_pct":      (12, 4),
        "dust_pct":       (40, 7),
        "builtup_pct":    (35, 6),
        "shade_pct":      (7,  3),
        "congestion_pct": (25, 6),
        "water_pct":      (1,  1),
    },
}

DEFAULT_PROFILE = {
    "green_pct":      (20, 5),
    "dust_pct":       (28, 6),
    "builtup_pct":    (38, 5),
    "shade_pct":      (10, 3),
    "congestion_pct": (30, 7),
    "water_pct":      (4,  2),
}


def generate_mock_parameters(city_slug: str) -> dict:
    """
    Returns a dict of environmental parameters (0–100 floats).
    Values are seeded from city profile + small random noise.
    Phase 2 replaces this with real OpenCV extraction.
    """
    profile = CITY_PROFILES.get(city_slug, DEFAULT_PROFILE)
    params = {}
    total = 0

    for key, (base, noise) in profile.items():
        if key == "water_pct":
            continue
        val = max(0.0, min(100.0, base + random.uniform(-noise, noise)))
        params[key] = round(val, 2)
        total += val

    # Normalize so non-water values loosely sum to ~100
    if total > 100:
        factor = 100 / total
        params = {k: round(v * factor, 2) for k, v in params.items()}

    # Water
    w_base, w_noise = profile.get("water_pct", (4, 2))
    params["water_pct"] = round(max(0, w_base + random.uniform(-w_noise, w_noise)), 2)

    return params
