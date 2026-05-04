"""
apps/analysis/green.py
Green Cover % — tightened HSV ranges to reduce false positives.
"""
import cv2
import numpy as np


def extract_green_pct(image_bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # Strict green vegetation only (not yellow-green or dark shadows)
    lower1 = np.array([36, 50, 50])
    upper1 = np.array([82, 255, 200])

    # Dark forest green (dense canopy)
    lower2 = np.array([83, 40, 30])
    upper2 = np.array([96, 255, 160])

    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower1, upper1),
        cv2.inRange(hsv, lower2, upper2)
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    total = image_bgr.shape[0] * image_bgr.shape[1]
    return round((int(np.sum(mask > 0)) / total) * 100, 2)
