"""
apps/analysis/builtup.py
Built-up / Concrete % — stricter grey detection, avoid shadows and vegetation.
"""
import cv2
import numpy as np


def extract_builtup_pct(image_bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # True concrete grey — low saturation, medium-high brightness
    lower1 = np.array([0,   0,  90])
    upper1 = np.array([180, 30, 190])

    # Bright white rooftops
    lower2 = np.array([0,   0,  210])
    upper2 = np.array([180, 20, 255])

    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower1, upper1),
        cv2.inRange(hsv, lower2, upper2)
    )

    # Exclude very dark pixels (shadows, not concrete)
    dark_mask = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60]))
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(dark_mask))

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    total = image_bgr.shape[0] * image_bgr.shape[1]
    return round((int(np.sum(mask > 0)) / total) * 100, 2)
