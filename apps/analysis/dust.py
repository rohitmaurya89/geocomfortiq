"""
apps/analysis/dust.py
Dust / Open Land % — tightened to avoid catching roads and buildings.
"""
import cv2
import numpy as np


def extract_dust_pct(image_bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # Dry soil / sandy tones — strict saturation and hue range
    lower1 = np.array([12, 30, 100])
    upper1 = np.array([28, 160, 210])

    # Light bare earth (dry fields)
    lower2 = np.array([18, 15, 160])
    upper2 = np.array([32, 70, 240])

    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower1, upper1),
        cv2.inRange(hsv, lower2, upper2)
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    total = image_bgr.shape[0] * image_bgr.shape[1]
    return round((int(np.sum(mask > 0)) / total) * 100, 2)
