"""
apps/analysis/shadow.py
Shade / Shadow % — darker threshold to avoid catching dark vegetation.
"""
import cv2
import numpy as np


def extract_shadow_pct(image_bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # True shadows — very low brightness only
    lower = np.array([0,   0,  0])
    upper = np.array([180, 255, 45])
    shadow_mask = cv2.inRange(hsv, lower, upper)

    # Exclude water (blue dominant)
    b, g, r = cv2.split(image_bgr)
    water_mask = ((b.astype(int) - r.astype(int)) > 25).astype(np.uint8) * 255
    shadow_mask = cv2.bitwise_and(shadow_mask, cv2.bitwise_not(water_mask))

    # Exclude green-toned dark areas (dark vegetation, not shadow)
    green_dark = cv2.inRange(hsv, np.array([36, 30, 20]), np.array([96, 255, 80]))
    shadow_mask = cv2.bitwise_and(shadow_mask, cv2.bitwise_not(green_dark))

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_OPEN,  kernel)
    shadow_mask = cv2.morphologyEx(shadow_mask, cv2.MORPH_CLOSE, kernel)

    total = image_bgr.shape[0] * image_bgr.shape[1]
    return round((int(np.sum(shadow_mask > 0)) / total) * 100, 2)
