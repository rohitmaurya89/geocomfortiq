"""
apps/analysis/congestion.py
Structural Congestion % via Canny edge density.
Fixed: multiplier reduced from 4.0 to 2.5 — was producing 90%+ values.
Urban areas typically have 10-20% raw edge density → maps to 25-50% congestion.
"""
import cv2
import numpy as np


def extract_congestion_pct(image_bgr: np.ndarray) -> float:
    gray    = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny edge detection
    edges = cv2.Canny(blurred, threshold1=60, threshold2=160)

    total      = image_bgr.shape[0] * image_bgr.shape[1]
    edge_pixels = int(np.sum(edges > 0))

    # Raw edge density (urban areas: 5-30%)
    raw_density = (edge_pixels / total) * 100

    # Scale to 0-100: multiplier 2.5 instead of 4.0
    # This means 20% raw density → 50% congestion (more realistic)
    congestion = min(raw_density * 2.5, 100.0)
    return round(congestion, 2)
